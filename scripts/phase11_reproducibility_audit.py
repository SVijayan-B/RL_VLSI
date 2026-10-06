"""
Phase 11: Reproducibility Audit.
Runs a dual-pass training experiment under seed 42 to verify deterministic execution.
Generates results/phase_11/reproducibility.csv.
"""

import json
import os
import time
import numpy as np
import pandas as pd
import torch

from src.rl.train_a2c_multiseed import train_single_seed

CONFIG_PATH = "configs/phase11_a2c_training_protocol.json"
OUT_CSV = "results/phase_11/reproducibility.csv"

def run_reproducibility_audit():
    print("="*80)
    print("PHASE 11: REPRODUCIBILITY AUDIT")
    print("="*80)

    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    # Temporary config with compact 5 episodes for audit comparison
    cfg_audit = cfg.copy()
    cfg_audit["hyperparameters"] = cfg["hyperparameters"].copy()
    cfg_audit["hyperparameters"]["num_episodes"] = 5

    # Run Pass 1
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
    res1 = train_single_seed(seed=42, config=cfg_audit)
    df1 = pd.read_csv("results/phase_11/seed_42/transitions.csv")
    hpwl1 = df1["current_hpwl_um"].values

    # Run Pass 2
    res2 = train_single_seed(seed=42, config=cfg_audit)
    df2 = pd.read_csv("results/phase_11/seed_42/transitions.csv")
    hpwl2 = df2["current_hpwl_um"].values

    diff = np.abs(hpwl1 - hpwl2)
    max_diff = float(np.max(diff))
    mean_diff = float(np.mean(diff))

    is_exact = bool(max_diff < 1e-4)

    audit_records = [{
        "seed": 42,
        "test_episodes": 5,
        "total_transitions_checked": len(hpwl1),
        "max_absolute_difference": max_diff,
        "mean_absolute_difference": mean_diff,
        "reproducibility_level": "BIT_EXACT" if max_diff == 0.0 else "NUMERICALLY_EQUIVALENT",
        "status": "PASS" if is_exact else "FAIL"
    }]

    df_out = pd.DataFrame(audit_records)
    df_out.to_csv(OUT_CSV, index=False)
    print(f"\n[+] Saved reproducibility audit to {OUT_CSV}")
    print(f"[+] Status: {audit_records[0]['status']} | Max Diff: {max_diff}")

if __name__ == "__main__":
    run_reproducibility_audit()
