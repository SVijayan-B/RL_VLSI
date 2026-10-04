import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

TRAIN_LOG_CSV = "results/phase_10/training/training_log.csv"
AUDIT_CSV = "results/phase_10/smoke/manual_transition_audit.csv"
PLOTS_DIR = "results/phase_10/plots"

def generate_plots():
    os.makedirs(PLOTS_DIR, exist_ok=True)
    df_train = pd.read_csv(TRAIN_LOG_CSV)
    df_audit = pd.read_csv(AUDIT_CSV)

    # 1. Reward & Loss per episode
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.plot(df_train['episode'], df_train['cumulative_reward'], marker='o', color='#1f77b4', linewidth=2)
    ax1.set_title("SMOKE TEST - Reward per Episode\n(NOT PERFORMANCE EVALUATION)", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Episode")
    ax1.set_ylabel("Cumulative Return")
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2.plot(df_train['episode'], df_train['total_loss'], marker='s', color='#d62728', linewidth=2)
    ax2.set_title("SMOKE TEST - Total A2C Loss per Episode\n(NOT PERFORMANCE EVALUATION)", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Episode")
    ax2.set_ylabel("A2C Loss")
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "smoke_reward_and_loss.png"), dpi=200)
    plt.close()

    # 2. HPWL Trajectory across Transitions
    plt.figure(figsize=(8, 5))
    steps = range(1, len(df_audit) + 1)
    plt.plot(steps, df_audit['measured_HPWL'], marker='.', color='#2ca02c', linewidth=1.5)
    plt.axhline(df_audit['measured_HPWL'].iloc[0], color='black', linestyle='--', label='Initial Baseline')
    plt.title("SMOKE TEST - HPWL Transition Trajectory\n(NOT PERFORMANCE EVALUATION)", fontsize=11, fontweight='bold')
    plt.xlabel("Global Step")
    plt.ylabel("Legalized HPWL (um)")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "smoke_hpwl_trajectory.png"), dpi=200)
    plt.close()

    # 3. Action Frequency
    plt.figure(figsize=(8, 4))
    act_counts = df_audit['selected_action_name'].value_counts()
    act_counts.plot(kind='bar', color='#ff7f0e', edgecolor='black')
    plt.title("SMOKE TEST - Action Selection Frequency\n(NOT PERFORMANCE EVALUATION)", fontsize=11, fontweight='bold')
    plt.xlabel("Action Name")
    plt.ylabel("Execution Count")
    plt.xticks(rotation=30, ha='right')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "smoke_action_frequency.png"), dpi=200)
    plt.close()

    print(f"[+] Saved all smoke test plots to {PLOTS_DIR}")

if __name__ == "__main__":
    generate_plots()
