#!/usr/bin/env python3
"""Find all HPWL-improved transitions across all seeds and show details."""
import os, json, glob

base = "/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_12"
seeds = [42, 43, 44, 45, 46]

improved = []
degraded = []

for s in seeds:
    logs = glob.glob(os.path.join(base, f"seed_{s}", "runs", "**", "transition_log.json"), recursive=True)
    for lpath in sorted(logs):
        try:
            with open(lpath) as f:
                t = json.load(f)
            prev = t.get("previous_hpwl", 0)
            curr = t.get("current_hpwl", 0)
            base_hpwl = t.get("baseline_hpwl", 0)
            exit_code = t.get("openroad_exit_code", 1)
            if exit_code == 0 and curr > 0 and prev > 0:
                delta_pct = ((prev - curr) / prev) * 100
                abs_delta = prev - curr
                if delta_pct > 1e-5:
                    improved.append({
                        "seed": s,
                        "design_id": t.get("design_id"),
                        "action": t.get("action_name"),
                        "params": t.get("new_parameters"),
                        "baseline_hpwl": base_hpwl,
                        "prev_hpwl": prev,
                        "curr_hpwl": curr,
                        "abs_improvement_um": abs_delta,
                        "improvement_pct": delta_pct,
                        "path": lpath
                    })
                elif delta_pct < -1e-5:
                    degraded.append({
                        "seed": s,
                        "design_id": t.get("design_id"),
                        "action": t.get("action_name"),
                        "delta_pct": delta_pct
                    })
        except:
            pass

print(f"{'='*70}")
print(f"VALID HPWL IMPROVEMENTS FOUND: {len(improved)}")
print(f"{'='*70}")

if improved:
    for r in sorted(improved, key=lambda x: -x["improvement_pct"]):
        print(f"\n  Seed {r['seed']} | Design: {r['design_id']}")
        print(f"  Action: {r['action']}")
        print(f"  Params: {r['params']}")
        print(f"  Baseline HPWL : {r['baseline_hpwl']:>12.1f} µm")
        print(f"  Previous HPWL : {r['prev_hpwl']:>12.1f} µm")
        print(f"  Current HPWL  : {r['curr_hpwl']:>12.1f} µm")
        print(f"  Improvement   : {r['abs_improvement_um']:>+10.1f} µm  ({r['improvement_pct']:+.6f}%)")
else:
    print("  None yet.")

print(f"\n{'='*70}")
print(f"HPWL DEGRADATIONS: {len(degraded)}")
print(f"{'='*70}")
for r in degraded[:5]:
    print(f"  Seed {r['seed']} | {r['design_id']} | {r['action']} | {r['delta_pct']:+.6f}%")
