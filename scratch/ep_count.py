#!/usr/bin/env python3
import os, glob

base = "/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_12"

print("=" * 60)
print("EPISODE COUNTS (out of 100)")
print("=" * 60)
total = 0
for s in [42, 43, 44, 45, 46]:
    runs_dir = f"{base}/seed_{s}/runs"
    ep_csv = f"{base}/seed_{s}/episode_metrics.csv"
    n = len(os.listdir(runs_dir)) if os.path.exists(runs_dir) else 0
    done = "✅ COMPLETE" if os.path.exists(ep_csv) else "🔄 running"
    print(f"  Seed {s}: {n:>3}/100  {done}")
    total += n

print(f"\n  Total episodes across all seeds: {total}/500")
pct = (total / 500) * 100
bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
print(f"  Progress: [{bar}] {pct:.1f}%")

print("\n" + "=" * 60)
print("CHECKPOINTS")
print("=" * 60)
ckpt_dir = f"{base}/checkpoints"
if os.path.exists(ckpt_dir):
    ckpts = os.listdir(ckpt_dir)
    for c in sorted(ckpts):
        path = f"{ckpt_dir}/{c}"
        size_kb = os.path.getsize(path) / 1024
        print(f"  {c}  ({size_kb:.1f} KB)")
else:
    print("  No checkpoints yet")
