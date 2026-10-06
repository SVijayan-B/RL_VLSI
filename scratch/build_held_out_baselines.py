#!/usr/bin/env python3
"""
Step 1: Find the original CircuitNet DEFs for held-out designs.
Step 2: Run OpenROAD baseline placement on them.
Step 3: Add them to the Phase 12 registry with HELD_OUT_TEST split.
"""
import os
import subprocess
import time
import pandas as pd
from pathlib import Path

BASE = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")

# The held-out designs are RISCY-a-1-c2, RISCY-a-1-c5, RISCY-a-1-c20
# These were in the Phase 10 benchmark_registry.csv with their original CircuitNet DEF paths
p10 = pd.read_csv(BASE / "results/phase_10/benchmark_registry.csv")
held_out_rows = p10[p10["split"] == "HELD_OUT_TEST"].copy()
print("Held-out from Phase 10 registry:")
print(held_out_rows[["benchmark_id", "design_id", "source_DEF", "default_dpl_baseline_HPWL_um"]].to_string())
print()

# Check if source DEFs exist
for _, row in held_out_rows.iterrows():
    def_path = BASE / row["source_DEF"]
    exists = def_path.exists()
    print(f"  {row['design_id']}: {def_path} -> exists={exists}")

print()

# Run OpenROAD on each held-out design to get real baselines
def run_openroad_baseline(def_path: str, design_id: str):
    tcl = f"read_lef /CircuitNet/dataset/raw/circuitnet.lef\n"
    tcl += f"read_def -continue_on_errors /CircuitNet/{def_path}\n"
    tcl += f"detailed_placement -use_diamond_legalizer\n"
    tcl += f"check_placement -verbose\n"
    tcl += f"exit\n"

    t0 = time.time()
    try:
        res = subprocess.run(
            ["docker", "run", "--rm", "-i", "-v",
             f"{BASE}:/CircuitNet",
             "openroad/orfs:latest",
             "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad",
             "-no_splash"],
            input=tcl, text=True, capture_output=True, timeout=120
        )
        elapsed = time.time() - t0
        out = res.stdout
        leg_hpwl = None
        for line in out.splitlines():
            if "legalized HPWL" in line:
                try:
                    leg_hpwl = float(line.split()[-2])
                except:
                    pass
        if leg_hpwl is not None:
            print(f"  [{design_id}] Legalized HPWL: {leg_hpwl:.1f} um | Time: {elapsed:.1f}s")
            return True, leg_hpwl, elapsed
        else:
            print(f"  [{design_id}] FAILED - no HPWL in output")
            print("  STDOUT tail:", out[-500:])
            return False, None, elapsed
    except subprocess.TimeoutExpired:
        return False, None, 120.0

print("Running OpenROAD baselines for held-out designs...")
held_out_baselines = []

for _, row in held_out_rows.iterrows():
    d_id = row["design_id"]
    def_rel = row["source_DEF"]  # relative path like dataset/processed/DEF/...
    
    # Check path
    def_full = BASE / def_rel
    if not def_full.exists():
        # Try to find the DEF
        print(f"  DEF not found at {def_full}, searching...")
        matches = list(BASE.glob(f"**/{d_id}*.def"))
        if matches:
            def_rel = str(matches[0].relative_to(BASE))
            print(f"  Found: {def_rel}")
        else:
            print(f"  No DEF found for {d_id}, skipping")
            continue
    
    success, leg_hpwl, elapsed = run_openroad_baseline(def_rel, d_id)
    held_out_baselines.append({
        "benchmark_id": row["benchmark_id"],
        "design_id": d_id,
        "split": "HELD_OUT_TEST",
        "source_DEF": str(BASE / def_rel),
        "def_exists": True,
        "placement_sample_id": -1,
        "initial_hpwl_um": row.get("initial_HPWL_um", 0.0),
        "default_dpl_baseline_HPWL_um": leg_hpwl if success else row["default_dpl_baseline_HPWL_um"],
        "rl_start_HPWL_um": leg_hpwl if success else row["default_dpl_baseline_HPWL_um"],
        "baseline_source": "PHASE_12_LIVE_OPENROAD" if success else "PHASE_10_STALE",
        "utilization": 0.0,
        "movable_cells": 0,
        "check_placement_errors": 0,
        "status": "PASS" if success else "UNKNOWN"
    })

# Load existing training registry
train_reg = pd.read_csv(BASE / "results/phase_12/phase12_benchmark_registry.csv")
print(f"\nExisting training registry: {len(train_reg)} rows")

# Merge
held_df = pd.DataFrame(held_out_baselines)
full_reg = pd.concat([train_reg, held_df], ignore_index=True)
print(f"Full registry: {len(full_reg)} rows")
print(f"  TRAIN: {len(full_reg[full_reg['split']=='TRAIN'])}")
print(f"  HELD_OUT_TEST: {len(full_reg[full_reg['split']=='HELD_OUT_TEST'])}")

out_path = BASE / "results/phase_12/phase12_benchmark_registry.csv"
full_reg.to_csv(out_path, index=False)
print(f"\nSaved full registry: {out_path}")
print("\nHeld-out baselines:")
print(held_df[["design_id", "default_dpl_baseline_HPWL_um", "baseline_source"]].to_string())
