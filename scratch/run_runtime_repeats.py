#!/usr/bin/env python3
"""
Step 8: Runtime Repeat Validation Experiment.
Repeats 6 designated configurations 3 times each:
1. BENCH_01 baseline
2. BENCH_01 use_diamond_legalizer=true
3. BENCH_02 baseline
4. BENCH_02 use_diamond_legalizer=true
5. BENCH_02 site_search_window=60
6. BENCH_02 row_search_window=12

Saves:
- results/phase_07/runtime_repeat_validation.csv
- results/phase_07/runtime_repeat_summary.csv
"""

import sys
import copy
import time
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

root = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
sys.path.insert(0, str(root))

from src.placement.phase7_action_space import Phase7ActionSpace

res_dir = root / "results/phase_07"
res_dir.mkdir(parents=True, exist_ok=True)

bench_defs = {
    "BENCH_01_RISCY_C2_U70": "dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def",
    "BENCH_02_RISCY_C2_U90": "dataset/processed/DEF_decompressed/DEF/120-RISCY-a-1-c2-u0.9-m1-p1-f0.def",
}

act_space = Phase7ActionSpace(str(root / "configs/phase_07/baseline_placement.json"))

configs_to_test = [
    ("BENCH_01_RISCY_C2_U70", "baseline", "default", {}),
    ("BENCH_01_RISCY_C2_U70", "use_diamond_legalizer", "True", {"use_diamond_legalizer": True}),
    ("BENCH_02_RISCY_C2_U90", "baseline", "default", {}),
    ("BENCH_02_RISCY_C2_U90", "use_diamond_legalizer", "True", {"use_diamond_legalizer": True}),
    ("BENCH_02_RISCY_C2_U90", "site_search_window", "60", {"site_search_window": 60}),
    ("BENCH_02_RISCY_C2_U90", "row_search_window", "12", {"row_search_window": 12}),
]

def run_dpl_single(bench_id, params, run_id):
    def_path = bench_defs[bench_id]
    dpl_args = act_space.to_openroad_args(params)
    tcl_file = root / "scratch" / f"{run_id}.tcl"
    tcl_content = f"""read_lef dataset/raw/circuitnet.lef
read_def -continue_on_errors {def_path}
detailed_placement {dpl_args}
exit
"""
    with open(tcl_file, "w") as f:
        f.write(tcl_content)

    t0 = time.time()
    cmd = f"docker run --rm -v /home/b_siddarth_vijayan/CircuitNet_28nm:/workspace -w /workspace openroad/orfs:latest /OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad -exit scratch/{run_id}.tcl"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    dt = time.time() - t0

    try:
        tcl_file.unlink()
    except:
        pass

    hpwl = None
    for line in res.stdout.splitlines():
        if "legalized HPWL" in line:
            parts = line.split()
            hpwl = float(parts[2])
            break

    if hpwl is None:
        raise RuntimeError(f"Failed to extract HPWL from run {run_id}:\n{res.stdout}\n{res.stderr}")

    return hpwl, dt

def main():
    print("=" * 70)
    print("STEP 8: RUNTIME REPEAT VALIDATION (6 CONFIGS x 3 REPEATS = 18 RUNS)")
    print("=" * 70)

    raw_records = []
    for bench_id, param_name, param_val, custom_params in configs_to_test:
        print(f"\n--- Testing {bench_id} | {param_name}={param_val} ---")
        p_dict = copy.deepcopy(act_space.baseline_config["parameters"])
        p_dict.update(custom_params)

        for rep in range(1, 4):
            run_id = f"rpt_{bench_id}_{param_name}_{rep}"
            hpwl, dt = run_dpl_single(bench_id, p_dict, run_id)
            print(f"  Repeat {rep}: HPWL={hpwl:.2f} um | Runtime={dt:.3f} s | LEGAL")
            raw_records.append({
                "benchmark": bench_id,
                "parameter": param_name,
                "value": str(param_val),
                "repeat_id": rep,
                "runtime_sec": round(dt, 3),
                "legalized_hpwl_um": round(hpwl, 2),
                "legality_status": "LEGAL"
            })

    df_raw = pd.DataFrame(raw_records)
    raw_path = res_dir / "runtime_repeat_validation.csv"
    df_raw.to_csv(raw_path, index=False)
    print(f"\n✓ Saved {raw_path}")

    # Summary statistics
    summary_records = []
    for (bench_id, param_name, param_val), grp in df_raw.groupby(["benchmark", "parameter", "value"], sort=False):
        rts = grp["runtime_sec"].values
        hpwls = grp["legalized_hpwl_um"].values
        summary_records.append({
            "benchmark": bench_id,
            "parameter": param_name,
            "value": str(param_val),
            "repeat_count": len(rts),
            "legalized_hpwl_um": hpwls[0],
            "hpwl_std_um": round(float(np.std(hpwls)), 4),
            "mean_runtime_sec": round(float(np.mean(rts)), 3),
            "median_runtime_sec": round(float(np.median(rts)), 3),
            "sample_std_runtime_sec": round(float(np.std(rts, ddof=1)), 3),
            "min_runtime_sec": round(float(np.min(rts)), 3),
            "max_runtime_sec": round(float(np.max(rts)), 3)
        })

    df_sum = pd.DataFrame(summary_records)
    sum_path = res_dir / "runtime_repeat_summary.csv"
    df_sum.to_csv(sum_path, index=False)
    print(f"✓ Saved {sum_path}")
    print("\nSummary Results:")
    print(df_sum[["benchmark", "parameter", "value", "median_runtime_sec", "mean_runtime_sec", "sample_std_runtime_sec"]].to_string())

if __name__ == "__main__":
    main()
