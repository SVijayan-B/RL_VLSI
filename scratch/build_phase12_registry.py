#!/usr/bin/env python3
"""
Build corrected Phase 12 benchmark registry.
- Sources Phase 11D validated legalized_hpwl for all 48 PASS training designs
- Excludes RISCY-FPU-a-3-c2 (TRAINING_PHYSICAL_FAILURE)
- Marks held-out designs correctly
- Links source_DEF to Phase 11D reconstructed DEFs
- Links graph embeddings from Phase 9
"""
import pandas as pd
import os
from pathlib import Path

BASE = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
OUT = BASE / "results/phase_12"
OUT.mkdir(parents=True, exist_ok=True)

# Load Phase 11D validated baselines
p11d = pd.read_csv(BASE / "results/phase_11d/training_baselines.csv")

# Filter to PASS only (excludes RISCY-FPU-a-3-c2 which is NaN/FAIL)
p11d_pass = p11d[p11d["status"] == "PASS"].copy()
print(f"Phase 11D PASS designs: {len(p11d_pass)}")

# Load Phase 9 graph embeddings to get list of available embeddings
emb_path = BASE / "results/phase_09/graph_embeddings.csv"
emb_df = pd.read_csv(emb_path)
available_emb_designs = set(emb_df["design_id"].tolist())
print(f"Designs with Phase 9 graph embeddings: {len(available_emb_designs)}")

# Held-out benchmark designs (must NOT appear in training)
HELD_OUT_DESIGNS = ["RISCY-a-1-c2", "RISCY-a-1-c5", "RISCY-a-1-c20"]

# Build the registry rows
rows = []

for _, r in p11d_pass.iterrows():
    d_id = r["design_id"]
    
    # Skip designs not in embeddings
    if d_id not in available_emb_designs:
        print(f"  SKIP (no embedding): {d_id}")
        continue
    
    # Determine split
    if d_id in HELD_OUT_DESIGNS:
        split = "HELD_OUT_TEST"
    else:
        split = "TRAIN"
    
    # DEF path
    def_path = str(BASE / f"results/phase_11d/reconstructed_defs/{d_id}.def")
    def_exists = os.path.exists(def_path)
    
    # Embedding file path (from Phase 9)
    emb_row = emb_df[emb_df["design_id"] == d_id].iloc[0]
    
    rows.append({
        "benchmark_id": f"P12_{d_id.replace('-','_').replace(' ','_')}",
        "design_id": d_id,
        "split": split,
        "source_DEF": def_path,
        "def_exists": def_exists,
        "placement_sample_id": r["placement_sample_id"],
        "initial_hpwl_um": r["initial_hpwl"],
        "default_dpl_baseline_HPWL_um": r["legalized_hpwl"],  # ← CORRECT Phase 11E value
        "rl_start_HPWL_um": r["legalized_hpwl"],
        "baseline_source": "PHASE_11D_VALIDATED_OPENROAD_LEGALIZED",
        "utilization": r["utilization"],
        "movable_cells": r["movable_cells"],
        "check_placement_errors": r["check_placement_errors"],
        "status": r["status"]
    })

df = pd.DataFrame(rows)

# Summary
train_df = df[df["split"] == "TRAIN"]
held_df = df[df["split"] == "HELD_OUT_TEST"]
missing_defs = df[~df["def_exists"]]

print(f"\nRegistry summary:")
print(f"  Total rows: {len(df)}")
print(f"  TRAIN: {len(train_df)}")
print(f"  HELD_OUT_TEST: {len(held_df)}")
print(f"  Missing DEFs: {len(missing_defs)}")
print(f"\n  TRAIN HPWL range: {train_df['default_dpl_baseline_HPWL_um'].min():.1f} – {train_df['default_dpl_baseline_HPWL_um'].max():.1f} µm")
print(f"  TRAIN mean HPWL: {train_df['default_dpl_baseline_HPWL_um'].mean():.1f} µm")

if len(missing_defs) > 0:
    print(f"\n  WARNING — missing DEFs:")
    print(missing_defs[["design_id", "source_DEF"]].to_string())

# Save
out_path = OUT / "phase12_benchmark_registry.csv"
df.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")

# Also save training-only subset for quick reference
train_df.to_csv(OUT / "phase12_train_pool.csv", index=False)
print(f"Saved: {OUT / 'phase12_train_pool.csv'}")

# Print held-out designs
print("\nHeld-out designs:")
print(held_df[["design_id", "benchmark_id", "default_dpl_baseline_HPWL_um"]].to_string())

print("\nFirst 5 training designs:")
print(train_df[["design_id", "default_dpl_baseline_HPWL_um"]].head().to_string())
