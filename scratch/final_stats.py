#!/usr/bin/env python3
import pandas as pd
import json

BASE = "/home/b_siddarth_vijayan/CircuitNet_28nm"

print("=" * 70)
print("PHASE 12 FINAL TRAINING STATISTICS")
print("=" * 70)

seed_summary = []
for s in [42, 43, 44, 45, 46]:
    df = pd.read_csv(f"{BASE}/results/phase_12/seed_{s}/episode_metrics.csv")
    best_return = df["episode_return"].max()
    final_return = df["episode_return"].iloc[-1]
    mean_return = df["episode_return"].mean()
    impr_eps = (df["best_hpwl"] < df["initial_hpwl"]).sum()
    fail_rate = (df["failed_steps"] / (df["successful_steps"] + df["failed_steps"])).mean() * 100
    best_hpwl_pct = ((df["initial_hpwl"] - df["best_hpwl"]) / df["initial_hpwl"] * 100).max()
    unique_designs = df["design_id"].nunique()
    
    print(f"\nSeed {s}:")
    print(f"  Best return       : {best_return:+.6f}")
    print(f"  Final return      : {final_return:+.6f}")
    print(f"  Mean return       : {mean_return:+.6f}")
    print(f"  Episodes with impr: {impr_eps}/100")
    print(f"  Avg DPL fail rate : {fail_rate:.1f}%")
    print(f"  Best HPWL impr    : {best_hpwl_pct:+.6f}%")
    print(f"  Unique designs    : {unique_designs}/48")
    
    seed_summary.append({
        "seed": s,
        "best_return": best_return,
        "final_return": final_return,
        "mean_return": mean_return,
        "episodes_with_improvement": int(impr_eps),
        "avg_fail_rate_pct": round(fail_rate, 2),
        "best_hpwl_improvement_pct": round(best_hpwl_pct, 6),
        "unique_designs_sampled": unique_designs
    })

print("\n" + "=" * 70)
print("AGGREGATE ACROSS ALL SEEDS")
print("=" * 70)
df_s = pd.DataFrame(seed_summary)
print(f"  Mean best return      : {df_s['best_return'].mean():+.6f} ± {df_s['best_return'].std():.6f}")
print(f"  Mean final return     : {df_s['final_return'].mean():+.6f} ± {df_s['final_return'].std():.6f}")
print(f"  Mean fail rate        : {df_s['avg_fail_rate_pct'].mean():.1f}%")
print(f"  Mean HPWL impr        : {df_s['best_hpwl_improvement_pct'].mean():+.6f}%")
print(f"  Best HPWL impr (any)  : {df_s['best_hpwl_improvement_pct'].max():+.6f}%")
print(f"  Seeds with impr > 0   : {(df_s['episodes_with_improvement'] > 0).sum()}/5")

# Design sampling audit
print("\n" + "=" * 70)
print("DESIGN SAMPLING AUDIT")
print("=" * 70)
audit = pd.read_csv(f"{BASE}/results/phase_12/design_sampling_audit.csv")
per_seed = audit.groupby("seed")["design_id"].nunique()
print(f"  Unique designs per seed: {per_seed.to_dict()}")
print(f"  Avg unique designs: {per_seed.mean():.1f}")

# Check leakage
with open(f"{BASE}/results/phase_12/leakage_audit.json") as f:
    leakage = json.load(f)
print(f"\nLeakage audit status: {leakage['status']}")
