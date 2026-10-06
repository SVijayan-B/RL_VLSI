"""
Phase 11: Multi-Seed Training Diagnostics & Figures Generator.
Generates all 8 required training diagnostic plots:
01_episode_return.png
02_training_hpwl_improvement.png
03_policy_loss.png
04_value_loss.png
05_entropy.png
06_action_frequency.png
07_failed_steps.png
08_seed_comparison.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BASE_RESULTS_DIR = "results/phase_11"
PLOTS_DIR = os.path.join(BASE_RESULTS_DIR, "figures")
SEEDS = [42, 43, 44, 45, 46]

def generate_all_figures():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    dfs_ep = {s: pd.read_csv(os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "episode_metrics.csv")) for s in SEEDS}
    dfs_tr = {s: pd.read_csv(os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "transitions.csv")) for s in SEEDS}

    colors = {42: "#1f77b4", 43: "#ff7f0e", 44: "#2ca02c", 45: "#d62728", 46: "#9467bd"}

    # 1. Episode Return vs Episode
    plt.figure(figsize=(9, 5))
    for s in SEEDS:
        df = dfs_ep[s]
        plt.plot(df["episode"], df["episode_return"], label=f"Seed {s}", color=colors[s], alpha=0.7, linewidth=1.5)
    plt.title("Phase 11 Training Diagnostic — Episode Return vs Episode\n(TRAINING PARTITION ONLY — NOT EVALUATION)", fontsize=11, fontweight="bold")
    plt.xlabel("Training Episode")
    plt.ylabel("Episode Cumulative Return (Reward Sum)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "01_episode_return.png"), dpi=200)
    plt.close()

    # 2. Training HPWL Improvement vs Episode
    plt.figure(figsize=(9, 5))
    for s in SEEDS:
        df = dfs_ep[s]
        # Rolling average for readability
        roll = df["relative_improvement_pct"].rolling(5, min_periods=1).mean()
        plt.plot(df["episode"], roll, label=f"Seed {s} (5-ep ma)", color=colors[s], linewidth=1.5)
    plt.title("Phase 11 Training Diagnostic — HPWL Improvement (%) vs Episode\n(TRAINING PARTITION ONLY — NOT EVALUATION)", fontsize=11, fontweight="bold")
    plt.xlabel("Training Episode")
    plt.ylabel("Relative HPWL Improvement (%)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "02_training_hpwl_improvement.png"), dpi=200)
    plt.close()

    # 3. Policy Loss vs Episode
    plt.figure(figsize=(9, 5))
    for s in SEEDS:
        df = dfs_ep[s]
        plt.plot(df["episode"], df["policy_loss"], label=f"Seed {s}", color=colors[s], alpha=0.7)
    plt.title("Phase 11 Training Diagnostic — Actor Policy Loss\n(TRAINING PARTITION ONLY)", fontsize=11, fontweight="bold")
    plt.xlabel("Training Episode")
    plt.ylabel("Policy Loss")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "03_policy_loss.png"), dpi=200)
    plt.close()

    # 4. Value Loss vs Episode
    plt.figure(figsize=(9, 5))
    for s in SEEDS:
        df = dfs_ep[s]
        plt.plot(df["episode"], df["value_loss"], label=f"Seed {s}", color=colors[s], alpha=0.7)
    plt.title("Phase 11 Training Diagnostic — Critic Value Loss\n(TRAINING PARTITION ONLY)", fontsize=11, fontweight="bold")
    plt.xlabel("Training Episode")
    plt.ylabel("Value Loss (MSE)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "04_value_loss.png"), dpi=200)
    plt.close()

    # 5. Entropy vs Episode
    plt.figure(figsize=(9, 5))
    for s in SEEDS:
        df = dfs_ep[s]
        plt.plot(df["episode"], df["entropy"], label=f"Seed {s}", color=colors[s], alpha=0.7)
    plt.title("Phase 11 Training Diagnostic — Policy Entropy vs Episode\n(TRAINING PARTITION ONLY)", fontsize=11, fontweight="bold")
    plt.xlabel("Training Episode")
    plt.ylabel("Entropy")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "05_entropy.png"), dpi=200)
    plt.close()

    # 6. Action Frequency across all seeds
    plt.figure(figsize=(10, 5))
    all_actions = []
    for s in SEEDS:
        all_actions.extend(dfs_tr[s]["action_name"].tolist())
    pd.Series(all_actions).value_counts().plot(kind="bar", color="#3470a3", edgecolor="black")
    plt.title("Phase 11 Training Diagnostic — Action Frequency Across All 5 Seeds\n(5,000 Total Transitions)", fontsize=11, fontweight="bold")
    plt.xlabel("Action Name")
    plt.ylabel("Execution Count")
    plt.xticks(rotation=30, ha="right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "06_action_frequency.png"), dpi=200)
    plt.close()

    # 7. Failed Steps
    plt.figure(figsize=(8, 4))
    failed_counts = [dfs_ep[s]["failed_steps"].sum() for s in SEEDS]
    plt.bar([f"Seed {s}" for s in SEEDS], failed_counts, color="#2ca02c", edgecolor="black")
    plt.title("Phase 11 Training Diagnostic — Failed Placement Transitions Count", fontsize=11, fontweight="bold")
    plt.ylabel("Failures Count")
    plt.ylim(0, 5)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "07_failed_steps.png"), dpi=200)
    plt.close()

    # 8. Seed Comparison Summary
    plt.figure(figsize=(9, 5))
    df_summary = pd.read_csv(os.path.join(BASE_RESULTS_DIR, "multi_seed_summary.csv"))
    x = np.arange(len(SEEDS))
    plt.bar(x, df_summary["best_training_improvement_pct"], color="#e377c2", edgecolor="black", width=0.5)
    plt.xticks(x, [f"Seed {s}" for s in SEEDS])
    plt.title("Phase 11 Multi-Seed Comparison — Best Training HPWL Improvement (%)\n(TRAINING PARTITION ONLY)", fontsize=11, fontweight="bold")
    plt.ylabel("Best HPWL Improvement (%)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "08_seed_comparison.png"), dpi=200)
    plt.close()

    print(f"[+] Successfully generated all 8 training diagnostic figures in {PLOTS_DIR}")

if __name__ == "__main__":
    generate_all_figures()
