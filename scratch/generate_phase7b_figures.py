import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

root = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
res_dir = root / "results/phase_07"
fig_dir = res_dir / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)

df_sweep = pd.read_csv(res_dir / "parameter_sweep_final.csv")
df_sens = pd.read_csv(res_dir / "parameter_sensitivity_final.csv")
df_inter = pd.read_csv(res_dir / "parameter_interactions_final.csv")
df_rep_sum = pd.read_csv(res_dir / "runtime_repeat_summary.csv")

# -------------------------------------------------------------
# 1. parameter_sensitivity_final.png
# -------------------------------------------------------------
plt.figure(figsize=(10, 5), dpi=300)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
bars = plt.barh(df_sens['parameter'], df_sens['delta_high_pct'], color=colors[:len(df_sens)])
plt.axvline(0, color='gray', linestyle='--', linewidth=0.8)
plt.xlabel('HPWL Delta (%) at High Parameter Setting vs Baseline')
plt.title('Phase 7B: OpenROAD Placement Parameter Sensitivity (BENCH_01_RISCY_C2_U70)')
for bar, val in zip(bars, df_sens['delta_high_pct']):
    plt.text(val, bar.get_y() + bar.get_height()/2, f" {val:+.4f}%", va='center', fontsize=9)
plt.grid(axis='x', linestyle=':', alpha=0.6)
plt.tight_layout()
for fname in ["parameter_sensitivity_final.png", "parameter_sensitivity.png"]:
    plt.savefig(fig_dir / fname)
plt.close()

# -------------------------------------------------------------
# 2. hpwl_parameter_effects_final.png
# -------------------------------------------------------------
plt.figure(figsize=(12, 6), dpi=300)
sub1 = df_sweep[df_sweep['benchmark'] == 'BENCH_01_RISCY_C2_U70']
plot_params = [p for p in sub1['parameter'].unique() if p != 'baseline_all']
for p in plot_params:
    p_sub = sub1[sub1['parameter'] == p].copy()
    if len(p_sub) >= 2:
        x_vals = range(len(p_sub))
        plt.plot(x_vals, p_sub['hpwl_um'], marker='o', label=p)
        plt.xticks(x_vals, [str(v) for v in p_sub['tested_value']])
plt.xlabel('Tested Parameter Value')
plt.ylabel('Legalized HPWL (um)')
plt.title('Legalized HPWL Across Placement Parameters (BENCH_01_RISCY_C2_U70)')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
for fname in ["hpwl_parameter_effects_final.png", "hpwl_parameter_effects.png"]:
    plt.savefig(fig_dir / fname)
plt.close()

# -------------------------------------------------------------
# 3. runtime_parameter_effects_final.png
# -------------------------------------------------------------
plt.figure(figsize=(10, 5), dpi=300)
x = np.arange(len(df_sens))
width = 0.35
plt.bar(x - width/2, df_sens['runtime_baseline'], width, label='Baseline Setting', color='#3498db')
plt.bar(x + width/2, df_sens['runtime_high'], width, label='High Setting', color='#e74c3c')
plt.xlabel('Parameter')
plt.ylabel('Detailed Placement Runtime (sec)')
plt.title('Detailed Placement Runtime Impact Across Parameters (BENCH_01_RISCY_C2_U70)')
plt.xticks(x, df_sens['parameter'], rotation=25, ha='right')
plt.legend()
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
for fname in ["runtime_parameter_effects_final.png", "runtime_parameter_effects.png"]:
    plt.savefig(fig_dir / fname)
plt.close()

# -------------------------------------------------------------
# 4. density_parameter_effects_final.png
# -------------------------------------------------------------
plt.figure(figsize=(10, 5), dpi=300)
sub_u70 = df_sweep[(df_sweep['benchmark'] == 'BENCH_01_RISCY_C2_U70') & (df_sweep['parameter'] == 'max_displacement')]
sub_u90 = df_sweep[(df_sweep['benchmark'] == 'BENCH_02_RISCY_C2_U90') & (df_sweep['parameter'] == 'max_displacement')]
plt.plot(sub_u70['tested_value'], sub_u70['hpwl_um'], marker='s', linewidth=2, label='U70 (Density 0.70)')
plt.plot(sub_u90['tested_value'], sub_u90['hpwl_um'], marker='^', linewidth=2, label='U90 (Density 0.90)')
plt.xlabel('max_displacement (sites)')
plt.ylabel('Legalized HPWL (um)')
plt.title('Placement Density Sensitivity: U70 vs U90 under max_displacement Variation')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
for fname in ["density_parameter_effects_final.png", "density_parameter_effects.png"]:
    plt.savefig(fig_dir / fname)
plt.close()

# -------------------------------------------------------------
# 5. parameter_interaction_heatmap_final.png
# -------------------------------------------------------------
plt.figure(figsize=(7, 6), dpi=300)
pivot = df_inter.pivot(index='value_a', columns='value_b', values='hpwl_delta_pct')
im = plt.imshow(pivot.values, cmap='Blues', interpolation='nearest', vmin=-0.05, vmax=0.05)
plt.colorbar(im, label='HPWL Delta (%) vs Baseline')
plt.xticks(range(len(pivot.columns)), pivot.columns)
plt.yticks(range(len(pivot.index)), pivot.index)
plt.xlabel('site_search_window (sites)')
plt.ylabel('max_displacement (sites)')
plt.title('Pairwise HPWL Interaction Heatmap (BENCH_01_RISCY_C2_U70)\nAll Delts = 0.00% (No Measurable HPWL Interaction)')
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        plt.text(j, i, f"{pivot.values[i, j]:+.2f}%", ha='center', va='center', color='black', fontsize=10)
plt.tight_layout()
for fname in ["parameter_interaction_heatmap_final.png", "parameter_interaction_heatmap.png"]:
    plt.savefig(fig_dir / fname)
plt.close()

# -------------------------------------------------------------
# 6. runtime_repeat_validation.png
# -------------------------------------------------------------
plt.figure(figsize=(10, 5), dpi=300)
labels = [f"{row['benchmark'].split('_')[1]}\n{row['parameter']}={row['value']}" for _, row in df_rep_sum.iterrows()]
medians = df_rep_sum['median_runtime_sec'].values
stds = df_rep_sum['sample_std_runtime_sec'].values
bars = plt.bar(range(len(labels)), medians, yerr=stds, capsize=5, color='#2980b9', alpha=0.85, edgecolor='black')
plt.xticks(range(len(labels)), labels, rotation=0, fontsize=8)
plt.ylabel('Runtime (sec) [Median ± Std]')
plt.title('Phase 7B Runtime Repeat Validation (3 Repeated Executions per Config)')
for idx, (m, s) in enumerate(zip(medians, stds)):
    plt.text(idx, m + s + 1.0, f"{m:.2f}s", ha='center', va='bottom', fontsize=8, fontweight='bold')
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig(fig_dir / "runtime_repeat_validation.png")
plt.close()

print("✓ All 6 figures generated successfully in results/phase_07/figures/!")
