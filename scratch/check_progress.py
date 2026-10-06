#!/usr/bin/env python3
import os
import json
import glob

base = "/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_12"
seeds = [42, 43, 44, 45, 46]

print("=" * 80)
print("PHASE 12 LIVE TRAINING PROGRESS")
print("=" * 80)

total_improved = 0
total_failed = 0
total_unchanged = 0

for s in seeds:
    runs_dir = os.path.join(base, f"seed_{s}", "runs")
    ep_metrics = os.path.join(base, f"seed_{s}", "episode_metrics.csv")
    
    # Count episodes
    if os.path.exists(runs_dir):
        episodes_done = len(os.listdir(runs_dir))
    else:
        episodes_done = 0
    
    # Check latest transition logs for HPWL
    all_transitions = glob.glob(os.path.join(base, f"seed_{s}", "runs", "**", "transition_log.json"), recursive=True)
    all_transitions.sort(key=os.path.getmtime)
    
    hpwl_deltas = []
    fails = 0
    improved = 0
    unchanged = 0
    
    for tpath in all_transitions:
        try:
            with open(tpath) as f:
                t = json.load(f)
            prev = t.get("previous_hpwl", 0)
            curr = t.get("current_hpwl", 0)
            exit_code = t.get("openroad_exit_code", 1)
            if exit_code == 0 and curr > 0 and prev > 0:
                delta = prev - curr
                delta_pct = (delta / prev) * 100
                hpwl_deltas.append(delta_pct)
                if delta_pct < -1e-5:
                    unchanged += 1
                elif delta_pct > 1e-5:
                    improved += 1
                else:
                    unchanged += 1
            else:
                fails += 1
        except:
            pass
    
    best_impr = max(hpwl_deltas) if hpwl_deltas else 0.0
    worst_degr = min(hpwl_deltas) if hpwl_deltas else 0.0
    fail_rate = (fails / max(len(all_transitions), 1)) * 100
    
    print(f"\nSeed {s}:")
    print(f"  Episodes: {episodes_done}/100")
    print(f"  Total transitions: {len(all_transitions)}")
    print(f"  PASS: {len(hpwl_deltas)} | FAIL: {fails} | Fail rate: {fail_rate:.1f}%")
    print(f"  HPWL Improved steps: {improved}")
    print(f"  HPWL Unchanged steps: {unchanged}")
    print(f"  Best improvement: {best_impr:+.6f}%")
    print(f"  Worst degradation: {worst_degr:+.6f}%")
    
    # Check if episode_metrics.csv exists (training completed for this seed)
    if os.path.exists(ep_metrics):
        import pandas as pd
        df = pd.read_csv(ep_metrics)
        print(f"  [DONE] Episode metrics saved: {len(df)} episodes")
        print(f"  Best training return: {df['episode_return'].max():.6f}")
        print(f"  Final training return: {df['episode_return'].iloc[-1]:.6f}")
    else:
        print(f"  [RUNNING] episode_metrics.csv not yet saved")
    
    total_improved += improved
    total_failed += fails
    total_unchanged += unchanged

print("\n" + "=" * 80)
print("AGGREGATE (ALL SEEDS)")
print(f"  Total HPWL-improved steps: {total_improved}")
print(f"  Total HPWL-unchanged steps: {total_unchanged}")
print(f"  Total FAILED steps: {total_failed}")
print("=" * 80)
