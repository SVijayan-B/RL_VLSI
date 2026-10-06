#!/usr/bin/env python3
"""
Fix: Build a corrected benchmark registry that uses Phase 11E/11D validated
legalized_hpwl values as the correct baseline for RL training.
Also identifies and excludes RISCY-FPU-a-3-c2 (training physical failure).
"""
import pandas as pd
import os

BASE = "/home/b_siddarth_vijayan/CircuitNet_28nm"

# Load existing benchmark registry
reg = pd.read_csv(f"{BASE}/results/phase_10/benchmark_registry.csv")
print(f"Benchmark registry: {len(reg)} rows")
print(f"Columns: {list(reg.columns)}")
print()
print("Sample HPWL values from registry:")
print(reg[['design_id', 'split', 'default_dpl_baseline_HPWL_um']].to_string())
print()

# Load Phase 11D validated baselines (actual OpenROAD legalized HPWL)
p11d = pd.read_csv(f"{BASE}/results/phase_11d/training_baselines.csv")
print(f"\nPhase 11D baselines: {len(p11d)} rows")
print("Columns:", list(p11d.columns))
print()
print("Sample Phase 11D HPWL values:")
print(p11d[['design_id', 'legalized_hpwl', 'status']].to_string())
