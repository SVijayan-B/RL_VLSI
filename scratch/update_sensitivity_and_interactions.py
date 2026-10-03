import pandas as pd
import numpy as np
from pathlib import Path

root = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
res_dir = root / "results/phase_07"

# 1. Parameter Sensitivity Final
df_sens = pd.read_csv(res_dir / "parameter_sensitivity_corrected.csv")
TOLERANCE_PCT = 0.001

for idx, row in df_sens.iterrows():
    d_high = row["delta_high_pct"]
    d_low = row["delta_low_pct"]
    
    # HPWL effect detected if high or low delta exceeds tolerance
    hpwl_effect = (abs(d_high) > TOLERANCE_PCT) or (abs(d_low) > TOLERANCE_PCT)
    df_sens.at[idx, "hpwl_effect_detected"] = hpwl_effect
    
    # Direction
    if d_high > TOLERANCE_PCT:
        direction = "DEGRADATION"
    elif d_high < -TOLERANCE_PCT:
        direction = "IMPROVEMENT"
    else:
        direction = "NEUTRAL"
    df_sens.at[idx, "effect_direction"] = direction

# Save both final and update corrected
df_sens.to_csv(res_dir / "parameter_sensitivity_final.csv", index=False)
df_sens.to_csv(res_dir / "parameter_sensitivity_corrected.csv", index=False)
df_sens.to_csv(res_dir / "parameter_sensitivity.csv", index=False)
print("✓ Successfully updated parameter sensitivity with strict tolerance classification:")
print(df_sens[["parameter", "delta_high_pct", "hpwl_effect_detected", "effect_direction", "runtime_effect_detected"]].to_string())

# 2. Parameter Sweep Final
df_swp = pd.read_csv(res_dir / "parameter_sweep_corrected.csv")
df_swp.to_csv(res_dir / "parameter_sweep_final.csv", index=False)
print(f"✓ Saved parameter_sweep_final.csv ({len(df_swp)} rows)")

# 3. Parameter Interactions Final
df_inter = pd.read_csv(res_dir / "parameter_interactions_corrected.csv")
# Calculate formal runtime interaction:
# observed_delta_rt - (delta_rt_a + delta_rt_b)
base_rt = df_inter[(df_inter["value_a"] == 0) & (df_inter["value_b"] == 0)]["runtime_sec"].iloc[0]

# Single factor runtime deltas
delta_rt_a = {}
for va in [0, 20, 50]:
    rt = df_inter[(df_inter["value_a"] == va) & (df_inter["value_b"] == 0)]["runtime_sec"].iloc[0]
    delta_rt_a[va] = rt - base_rt

delta_rt_b = {}
for vb in [0, 20, 50]:
    rt = df_inter[(df_inter["value_a"] == 0) & (df_inter["value_b"] == vb)]["runtime_sec"].iloc[0]
    delta_rt_b[vb] = rt - base_rt

for idx, row in df_inter.iterrows():
    va = row["value_a"]
    vb = row["value_b"]
    obs_rt = row["runtime_sec"]
    obs_delta_rt = obs_rt - base_rt
    exp_delta_rt = delta_rt_a[va] + delta_rt_b[vb]
    inter_rt = obs_delta_rt - exp_delta_rt
    
    df_inter.at[idx, "observed_delta_runtime_sec"] = round(obs_delta_rt, 3)
    df_inter.at[idx, "expected_additive_runtime_delta_sec"] = round(exp_delta_rt, 3)
    df_inter.at[idx, "runtime_interaction_sec"] = round(inter_rt, 3)
    # Significant interaction if > 0.5s deviation from pure additivity
    df_inter.at[idx, "runtime_interaction_detected"] = abs(inter_rt) > 0.50

df_inter.to_csv(res_dir / "parameter_interactions_final.csv", index=False)
df_inter.to_csv(res_dir / "parameter_interactions_corrected.csv", index=False)
df_inter.to_csv(res_dir / "parameter_interactions.csv", index=False)
print("✓ Successfully updated parameter interactions with formal runtime interaction metric:")
print(df_inter[["value_a", "value_b", "hpwl_um", "hpwl_interaction_um", "hpwl_interaction_detected", "runtime_sec", "runtime_interaction_sec", "runtime_interaction_detected"]].to_string())
