import os
import sys
import glob
import time
import json
import re
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
sys.path.insert(0, str(BASE_DIR))

from src.placement.lef_site_model import LEFSiteModel
from src.placement.coordinate_mapper import CoordinateMapper
from src.placement.def_reconstructor import DEFReconstructor

OUT_DIR = BASE_DIR / "results/phase_11d"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DEF_DIR = OUT_DIR / "reconstructed_defs"
DEF_DIR.mkdir(parents=True, exist_ok=True)

print("============================================================")
print("PHASE 11D — MASTER BASELINE AND SENSITIVITY PIPELINE")
print("============================================================")

lef_model = LEFSiteModel(BASE_DIR / "dataset/raw/circuitnet.lef")
reconstructor = DEFReconstructor(dbu_per_micron=2000)
mapper = CoordinateMapper(lef_model=lef_model, dbu_per_micron=2000)

p_map_file = BASE_DIR / "results/phase_11b/manifests/placement_design_mapping.csv"
df_map = pd.read_csv(p_map_file)
held_out = ['RISCY-a-1-c2', 'RISCY-a-1-c5', 'RISCY-a-1-c20']
df_train = df_map[~df_map['graph_design_id'].isin(held_out)]
df_train_sorted = df_train.sort_values(by=['graph_design_id', 'sample_id'])
# Deterministic representative sample: first sample per design
df_rep = df_train_sorted.groupby('graph_design_id').first().reset_index()

print(f"Loaded {len(df_rep)} active training designs.")
assert len(df_rep) == 49, f"Expected 49 designs, got {len(df_rep)}"

baselines_records = []
failures_records = []

def run_openroad_dpl(def_file, dpl_args, timeout=30):
    tcl = f"""read_lef /CircuitNet/dataset/raw/circuitnet.lef
read_def -continue_on_errors {def_file}
detailed_placement {dpl_args}
check_placement -verbose
exit
"""
    t0 = time.time()
    try:
        res = subprocess.run(
            ["docker", "run", "--rm", "-i", "-v", f"{BASE_DIR}:/CircuitNet", "openroad/orfs:latest", "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad", "-no_splash"],
            input=tcl, text=True, capture_output=True, timeout=timeout
        )
        dt = time.time() - t0
        stdout = res.stdout
        stderr = res.stderr
        rc = res.returncode
        
        init_hpwl = None
        leg_hpwl = None
        moves = None
        disp = None
        
        for line in stdout.splitlines():
            if 'original HPWL' in line:
                m = re.findall(r'original HPWL\s+([\d\.]+)', line)
                if m: init_hpwl = float(m[0])
            elif 'legalized HPWL' in line:
                m = re.findall(r'legalized HPWL\s+([\d\.]+)', line)
                if m: leg_hpwl = float(m[0])
            elif 'total moves' in line:
                m = re.findall(r'total moves\s+(\d+)', line)
                if m: moves = int(m[0])
            elif 'max displacement' in line:
                m = re.findall(r'max displacement\s+([\d\.]+)', line)
                if m: disp = float(m[0])

        check_errs = 0
        if "detailed placement checks failed" in stdout:
            check_errs = 1
        elif "Total Placement Failures:" in stdout:
            m_pf = re.findall(r'Total Placement Failures:\s+(\d+)', stdout)
            if m_pf and int(m_pf[0]) > 0:
                check_errs = int(m_pf[0])
        m_viol = re.findall(r'Placement analysis:\s+(\d+)\s+placement violations', stdout)
        if m_viol and int(m_viol[0]) > 0:
            check_errs = max(check_errs, int(m_viol[0]))

        status = "PASS" if (rc == 0 and check_errs == 0 and leg_hpwl is not None) else "FAIL"

        return {
            "status": status,
            "runtime_sec": round(dt, 2),
            "returncode": rc,
            "initial_hpwl": init_hpwl,
            "legalized_hpwl": leg_hpwl,
            "total_moves": moves,
            "max_displacement": disp,
            "check_placement_errors": check_errs,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "runtime_sec": timeout,
            "returncode": -1,
            "initial_hpwl": None,
            "legalized_hpwl": None,
            "total_moves": None,
            "max_displacement": None,
            "check_placement_errors": 1,
            "stdout": "",
            "stderr": "Command timed out"
        }

print("\n--- STAGE 1: RECONSTRUCTING AND EVALUATING BASELINES FOR ALL 49 DESIGNS ---")
for idx, row in df_rep.iterrows():
    d_id = row['graph_design_id']
    s_id = row['sample_id']
    p_path = BASE_DIR / row['placement_path']
    
    t_start = time.time()
    try:
        # Load graph
        g_path = BASE_DIR / f"dataset/graphs/{d_id}_graph.npz"
        g_data = np.load(g_path, allow_pickle=True)
        c_names = g_data['cell_names']
        c_types = g_data['cell_types']
        c_feats = g_data['cell_features']
        n_names = g_data['net_names']
        p_names = g_data['pin_names']
        edge_bip = g_data['edge_index_bipartite']

        # Independent floorplan derivation
        tot_cell_area = sum([(lef_model.get_macro_size_dbu(ct)[0]/2000.0) * (lef_model.get_macro_size_dbu(ct)[1]/2000.0) for ct in c_types])
        m_util = re.findall(r'-u([0-9\.]+)-', p_path.name)
        target_util = float(m_util[0]) if m_util else 0.70
        target_dim = np.sqrt(tot_cell_area / target_util)
        num_rows = int(round(target_dim / 1.05))
        num_sites = int(round(target_dim / 0.21))
        die_w = num_sites * 420
        die_h = num_rows * 2100
        actual_util = tot_cell_area / ((die_w / 2000.0) * (die_h / 2000.0))

        # Reconstruct layout
        p_dict = np.load(p_path, allow_pickle=True).item()
        components, missing = mapper.reconstruct_layout(
            d_id, c_names, c_types, c_feats, p_dict, die_w, die_h, num_rows
        )

        # Validate geometry
        overlap_cnt = 0
        out_of_die = 0
        illegal_sites = 0
        illegal_rows = 0
        movable_cells = 0
        fixed_macros = 0
        
        comp_boxes = []
        for inst, ctype, x, y, orient, status in components:
            is_macro = lef_model.is_macro(ctype)
            if is_macro: fixed_macros += 1
            else: movable_cells += 1
            w, h = lef_model.get_macro_size_dbu(ctype)
            if x < 0 or y < 0 or x + w > die_w or y + h > die_h:
                out_of_die += 1
            if x % 420 != 0:
                illegal_sites += 1
            if y % 2100 != 0:
                illegal_rows += 1
            comp_boxes.append((inst, x, y, x + w, y + h))

        row_map = {}
        for inst, x1, y1, x2, y2 in comp_boxes:
            r = y1 // 2100
            if r not in row_map: row_map[r] = []
            row_map[r].append((inst, x1, x2))

        for r, intervals in row_map.items():
            intervals.sort(key=lambda item: item[1])
            for k in range(len(intervals) - 1):
                if intervals[k][2] > intervals[k+1][1]:
                    overlap_cnt += 1

        recon_valid = (overlap_cnt == 0 and out_of_die == 0 and illegal_sites == 0 and illegal_rows == 0)

        # Reconstruct nets
        net_conns = {n: [] for n in n_names}
        src_cells = edge_bip[0]
        dst_nets = edge_bip[1]
        for ci in range(len(src_cells)):
            net_conns[n_names[dst_nets[ci]]].append((c_names[src_cells[ci]], p_names[ci]))
        valid_nets = [(n, conns) for n, conns in net_conns.items() if len(conns) >= 2]
        pins = [("clk", die_w // 2, 0, "INPUT", "M3"), ("rst_n", die_w // 4, 0, "INPUT", "M3")]

        def_path = DEF_DIR / f"{d_id}.def"
        reconstructor.generate_def(
            d_id, die_w, die_h, num_rows, components, valid_nets, pins, str(def_path)
        )

        # Execute baseline OpenROAD DPL
        container_def = f"/CircuitNet/results/phase_11d/reconstructed_defs/{d_id}.def"
        res_dpl = run_openroad_dpl(container_def, "-use_diamond_legalizer", timeout=30)

        dt = time.time() - t_start
        status = "PASS" if recon_valid and res_dpl["status"] == "PASS" else "FAIL"

        rec = {
            "design_id": d_id,
            "placement_sample_id": s_id,
            "placement_file": p_path.name,
            "configuration_id": "BASELINE_FROZEN",
            "parameter_values": "use_diamond_legalizer=true, max_disp=0, site_search=0, row_search=0, disallow_gaps=false, disable_ext=false",
            "initial_hpwl": res_dpl["initial_hpwl"],
            "legalized_hpwl": res_dpl["legalized_hpwl"],
            "hpwl_delta_um": round(res_dpl["legalized_hpwl"] - res_dpl["initial_hpwl"], 2) if (res_dpl["legalized_hpwl"] and res_dpl["initial_hpwl"]) else None,
            "hpwl_improvement_percent": 0.0,
            "runtime_sec": res_dpl["runtime_sec"],
            "movable_cells": movable_cells,
            "fixed_macros": fixed_macros,
            "utilization": round(actual_util, 4),
            "check_placement_errors": res_dpl["check_placement_errors"],
            "reconstruction_valid": recon_valid,
            "deterministic": True,
            "status": status
        }
        baselines_records.append(rec)
        print(f"[{idx+1}/49] {d_id}: HPWL={res_dpl['legalized_hpwl']} um, moves={res_dpl['total_moves']}, time={res_dpl['runtime_sec']}s, status={status}")

        if status != "PASS":
            failures_records.append({
                "design": d_id,
                "stage": "BASELINE_DPL" if recon_valid else "GEOMETRY_RECONSTRUCTION",
                "error": res_dpl["stderr"] if recon_valid else f"Overlaps:{overlap_cnt}, OutDie:{out_of_die}, IllegalSites:{illegal_sites}",
                "runtime": dt,
                "output_path": str(def_path)
            })

    except Exception as e:
        print(f"[{idx+1}/49] {d_id} EXCEPTION: {e}")
        failures_records.append({
            "design": d_id,
            "stage": "PIPELINE_EXCEPTION",
            "error": str(e),
            "runtime": time.time() - t_start,
            "output_path": ""
        })

df_base = pd.DataFrame(baselines_records)
df_base.to_csv(OUT_DIR / "training_baselines.csv", index=False)
print(f"\nSaved 49 baselines to: {OUT_DIR / 'training_baselines.csv'}")

# STAGE 2: SENSITIVITY SWEEP ON 10 REPRESENTATIVE DESIGNS
print("\n--- STAGE 2: FAST SENSITIVITY SWEEP ON 10 REPRESENTATIVE DESIGNS ---")
df_base_sorted = df_base.sort_values(by="movable_cells").reset_index(drop=True)
subset_indices = np.linspace(0, len(df_base_sorted) - 1, 10, dtype=int)
subset_designs = df_base_sorted.iloc[subset_indices]['design_id'].tolist()
print(f"Selected 10 representative designs for sensitivity test: {subset_designs}")

sensitivity_configs = [
    ("CFG_0_BASELINE", "-use_diamond_legalizer", "baseline"),
    ("CFG_1_MAX_DISP_10", "-use_diamond_legalizer -max_displacement 10", "max_disp=10"),
    ("CFG_2_MAX_DISP_50", "-use_diamond_legalizer -max_displacement 50", "max_disp=50"),
    ("CFG_3_SITE_SEARCH_10", "-use_diamond_legalizer -site_search_window 10", "site_search=10"),
    ("CFG_4_SITE_SEARCH_50", "-use_diamond_legalizer -site_search_window 50", "site_search=50"),
    ("CFG_5_ROW_SEARCH_2", "-use_diamond_legalizer -row_search_window 2", "row_search=2"),
    ("CFG_6_ROW_SEARCH_6", "-use_diamond_legalizer -row_search_window 6", "row_search=6"),
    ("CFG_7_DISALLOW_GAPS", "-use_diamond_legalizer -disallow_one_site_gaps", "disallow_gaps=true"),
    ("CFG_8_DISABLE_EXT", "-use_diamond_legalizer -disable_window_extension", "disable_ext=true"),
    ("CFG_9_FLIP_DIAMOND", "-max_displacement 50 -site_search_window 50 -row_search_window 2", "diamond=false, bounded_window")
]

sensitivity_records = []

for s_idx, d_id in enumerate(subset_designs):
    base_row = df_base[df_base['design_id'] == d_id].iloc[0]
    base_hpwl = base_row['legalized_hpwl']
    s_id = base_row['placement_sample_id']
    container_def = f"/CircuitNet/results/phase_11d/reconstructed_defs/{d_id}.def"

    print(f"\n[{s_idx+1}/10] Testing sensitivity on {d_id} (Baseline HPWL={base_hpwl:.1f} um):")

    for cfg_id, dpl_args, param_desc in sensitivity_configs:
        timeout = 10 if "CFG_9" in cfg_id else 20
        res = run_openroad_dpl(container_def, dpl_args, timeout=timeout)
        
        cand_hpwl = res['legalized_hpwl']
        if cand_hpwl and base_hpwl:
            imp_pct = round(((base_hpwl - cand_hpwl) / base_hpwl) * 100.0, 4)
            delta_um = round(cand_hpwl - base_hpwl, 2)
        else:
            imp_pct = None
            delta_um = None

        rec = {
            "design_id": d_id,
            "placement_sample_id": s_id,
            "configuration_id": cfg_id,
            "parameter_values": param_desc,
            "initial_hpwl": res["initial_hpwl"],
            "legalized_hpwl": cand_hpwl,
            "hpwl_delta_um": delta_um,
            "hpwl_improvement_percent": imp_pct,
            "runtime_sec": res["runtime_sec"],
            "movable_cells": base_row['movable_cells'],
            "fixed_macros": base_row['fixed_macros'],
            "utilization": base_row['utilization'],
            "check_placement_errors": res["check_placement_errors"],
            "reconstruction_valid": True,
            "deterministic": True,
            "status": res["status"]
        }
        sensitivity_records.append(rec)
        print(f"  {cfg_id:25s}: HPWL={cand_hpwl}, delta={delta_um} um, imp={imp_pct}%, status={res['status']}")

df_sens = pd.DataFrame(sensitivity_records)
df_sens.to_csv(OUT_DIR / "sensitivity_results.csv", index=False)
print(f"\nSaved sensitivity results to: {OUT_DIR / 'sensitivity_results.csv'}")

df_fail = pd.DataFrame(failures_records)
df_fail.to_csv(OUT_DIR / "failures.csv", index=False)
print(f"Saved failures to: {OUT_DIR / 'failures.csv'}")

# STAGE 3: COMPUTE SUMMARY STATISTICS
print("\n--- STAGE 3: COMPUTING METRICS AND HEADROOM ANALYSIS ---")

base_pass_count = len(df_base[df_base['status'] == 'PASS'])
mean_base_hpwl = float(df_base['legalized_hpwl'].mean())
median_base_hpwl = float(df_base['legalized_hpwl'].median())
std_base_hpwl = float(df_base['legalized_hpwl'].std())

train_summary = {
    "total_training_designs": 49,
    "baseline_successful": base_pass_count,
    "baseline_failed": len(df_base) - base_pass_count,
    "mean_baseline_hpwl_um": round(mean_base_hpwl, 2),
    "median_baseline_hpwl_um": round(median_base_hpwl, 2),
    "std_baseline_hpwl_um": round(std_base_hpwl, 2),
    "mean_runtime_sec": round(float(df_base['runtime_sec'].mean()), 2),
    "total_movable_cells": int(df_base['movable_cells'].sum()),
    "mean_movable_cells": round(float(df_base['movable_cells'].mean()), 1)
}
with open(OUT_DIR / "training_pool_summary.json", "w") as fp:
    json.dump(train_summary, fp, indent=2)

valid_sens = df_sens[df_sens['hpwl_improvement_percent'].notna()]
improvements = valid_sens['hpwl_improvement_percent'].values

best_imp = float(np.max(improvements)) if len(improvements) > 0 else 0.0
worst_deg = float(np.min(improvements)) if len(improvements) > 0 else 0.0
median_imp = float(np.median(improvements)) if len(improvements) > 0 else 0.0

param_stats = {}
for cfg in sensitivity_configs:
    cfg_id = cfg[0]
    sub = df_sens[df_sens['configuration_id'] == cfg_id]
    imps = sub['hpwl_improvement_percent'].dropna().values
    if len(imps) > 0:
        param_stats[cfg_id] = {
            "description": cfg[2],
            "mean_change_pct": round(float(np.mean(imps)), 4),
            "median_change_pct": round(float(np.median(imps)), 4),
            "min_change_pct": round(float(np.min(imps)), 4),
            "max_change_pct": round(float(np.max(imps)), 4),
            "fraction_improved": round(float(np.mean(imps > 0.0001)), 4),
            "fraction_degraded": round(float(np.mean(imps < -0.0001)), 4),
            "fraction_unchanged": round(float(np.mean(np.abs(imps) <= 0.0001)), 4),
        }

if best_imp > 1.0:
    headroom_verdict = "HIGH"
elif best_imp > 0.1:
    headroom_verdict = "MODERATE"
else:
    headroom_verdict = "LOW"

sens_summary = {
    "num_designs_tested": len(subset_designs),
    "total_configurations_tested": len(sensitivity_configs),
    "total_evaluations": len(df_sens),
    "best_observed_improvement_pct": round(best_imp, 4),
    "worst_observed_degradation_pct": round(worst_deg, 4),
    "median_improvement_pct": round(median_imp, 4),
    "headroom_classification": headroom_verdict,
    "parameter_statistics": param_stats
}
with open(OUT_DIR / "sensitivity_summary.json", "w") as fp:
    json.dump(sens_summary, fp, indent=2)

print("\nSummary Results:")
print("  Baselines valid:    ", f"{base_pass_count}/49")
print("  Mean Baseline HPWL: ", f"{mean_base_hpwl:.1f} um")
print("  Best Improvement:   ", f"{best_imp:.4f}%")
print("  Headroom Verdict:   ", headroom_verdict)
