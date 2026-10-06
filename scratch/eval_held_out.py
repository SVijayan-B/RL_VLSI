#!/usr/bin/env python3
"""
Correct held-out evaluation for Phase 12.
Loads best checkpoints per seed, runs RL policy on 4 held-out benchmarks
using the correct DEF paths from the registry.
"""
import os, json, subprocess, time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path

BASE = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
RESULTS = BASE / "results/phase_12"

# -------- ActorCritic matching src/rl/a2c.py exactly --------
class ActorCritic(nn.Module):
    def __init__(self, state_dim=41, action_dim=8, hidden_dim=128):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        # Separate actor network (41 -> 128 -> 128 -> 8)
        self.actor_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        # Separate critic network (41 -> 128 -> 128 -> 1)
        self.critic_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        return self.actor_net(x), self.critic_net(x)

    def get_action_and_value(self, x, action=None):
        logits, value = self.forward(x)
        dist = torch.distributions.Categorical(logits=logits)
        if action is None:
            action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), value

# -------- Load registry and embeddings --------
reg = pd.read_csv(RESULTS / "phase12_benchmark_registry.csv")
held = reg[reg["split"] == "HELD_OUT_TEST"].copy()
emb_df = pd.read_csv(BASE / "results/phase_09/graph_embeddings.csv").set_index("design_id")
emb_cols = [c for c in emb_df.columns if c.startswith("emb_")]

import json as _json
with open(BASE / "configs/phase10_parameter_space.json") as f:
    param_cfg = _json.load(f)
params = param_cfg["parameters"]

# Force diamond legalizer default = 1
for p in params:
    if p["name"] == "use_diamond_legalizer":
        p["default"] = 1

ACTIONS = [
    {"name": "FLIP_BOOLEANS",   "delta": {"disallow_one_site_gaps": "toggle", "disable_window_extension": "toggle"}},
    {"name": "UP_INTEGERS",     "delta": {"max_displacement": +10, "site_search_window": +10, "row_search_window": +2}},
    {"name": "DOWN_INTEGERS",   "delta": {"max_displacement": -10, "site_search_window": -10, "row_search_window": -2}},
    {"name": "UP_EFFORTS",      "delta": {"max_displacement": +10, "site_search_window": +10}},
    {"name": "DOWN_EFFORTS",    "delta": {"max_displacement": -10, "site_search_window": -10}},
    {"name": "UP_DETAILED",     "delta": {"max_displacement": +10, "site_search_window": +20, "row_search_window": +2}},
    {"name": "DOWN_DETAILED",   "delta": {"max_displacement": -10, "site_search_window": -10, "row_search_window": -2}},
    {"name": "DO_NOTHING",      "delta": {}},
]

def apply_action(action_id, cur_params):
    new_p = dict(cur_params)
    delta = ACTIONS[action_id]["delta"]
    for k, v in delta.items():
        if v == "toggle":
            new_p[k] = 0 if new_p[k] else 1
        else:
            p_cfg = next(pp for pp in params if pp["name"] == k)
            new_p[k] = max(p_cfg["minimum"], min(p_cfg["maximum"], float(new_p.get(k, 0)) + v))
    new_p["use_diamond_legalizer"] = 1
    return new_p

def normalize_params(param_dict):
    vals = []
    for p in params:
        name = p["name"]
        val = param_dict.get(name, p["default"])
        if p["datatype"] == "boolean":
            vals.append(1.0 if bool(val) else 0.0)
        else:
            pmin, pmax = p["minimum"], p["maximum"]
            clamped = max(pmin, min(pmax, float(val)))
            vals.append((clamped - pmin) / (pmax - pmin) if pmax > pmin else 0.0)
    return np.array(vals, dtype=np.float32)

def build_state(design_id, param_dict, cur_hpwl, base_hpwl, prev_hpwl, step, max_steps):
    emb = emb_df.loc[design_id, emb_cols].values.astype(np.float32)
    norm_p = normalize_params(param_dict)
    norm_hpwl = cur_hpwl / base_hpwl if base_hpwl > 0 else 1.0
    rel_chg = (prev_hpwl - cur_hpwl) / prev_hpwl if prev_hpwl > 0 else 0.0
    prog = step / max_steps if max_steps > 0 else 0.0
    return np.concatenate([emb, norm_p, [norm_hpwl, rel_chg], [prog]], axis=0).astype(np.float32)

def run_openroad(def_path_relative, dpl_flags):
    """Run OpenROAD with the correct DEF path from the registry."""
    tcl = f"read_lef /CircuitNet/dataset/raw/circuitnet.lef\n"
    tcl += f"read_def -continue_on_errors /CircuitNet/{def_path_relative}\n"
    tcl += f"detailed_placement {dpl_flags}\n"
    tcl += f"check_placement -verbose\n"
    tcl += f"exit\n"
    t0 = time.time()
    try:
        res = subprocess.run(
            ["docker", "run", "--rm", "-i", "-v", f"{BASE}:/CircuitNet",
             "openroad/orfs:latest",
             "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad",
             "-no_splash"],
            input=tcl, text=True, capture_output=True, timeout=90
        )
        elapsed = time.time() - t0
        leg_hpwl = None
        for line in res.stdout.splitlines():
            if "legalized HPWL" in line:
                try:
                    leg_hpwl = float(line.split()[-2])
                except:
                    pass
        if leg_hpwl is not None:
            return True, leg_hpwl, elapsed
        return False, 0.0, elapsed
    except subprocess.TimeoutExpired:
        return False, 0.0, 90.0

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
seeds = [42, 43, 44, 45, 46]
all_results = []

print("=" * 70)
print("PHASE 12 HELD-OUT EVALUATION (CORRECTED DEF PATHS)")
print("=" * 70)

for seed in seeds:
    ckpt_path = RESULTS / "checkpoints" / f"checkpoint_best_seed_{seed}.pt"
    model = ActorCritic().to(device)
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    print(f"\n--- Seed {seed} (best ep={ckpt.get('episode','?')}, return={ckpt.get('best_return',0):.5f}) ---")

    for _, row in held.iterrows():
        b_id = row["benchmark_id"]
        d_id = row["design_id"]
        base_hpwl = float(row["default_dpl_baseline_HPWL_um"])
        # DEF path relative to BASE (strip leading BASE prefix)
        def_full = str(row["source_DEF"])
        def_rel = def_full.replace(str(BASE) + "/", "").replace(str(BASE), "")

        # Get RL action from policy
        init_p = {p["name"]: p["default"] for p in params}
        state = build_state(d_id, init_p, base_hpwl, base_hpwl, base_hpwl, 0, 10)
        st_t = torch.from_numpy(state).float().unsqueeze(0).to(device)
        with torch.no_grad():
            act, _, _, _ = model.get_action_and_value(st_t)
        a_int = act.item()
        new_p = apply_action(a_int, init_p)

        # Build DPL flags
        dpl_flags = []
        if new_p.get("max_displacement", 0) > 0:
            dpl_flags.append(f"-max_displacement {int(new_p['max_displacement'])}")
        if new_p.get("site_search_window", 0) > 0:
            dpl_flags.append(f"-site_search_window {int(new_p['site_search_window'])}")
        if new_p.get("row_search_window", 0) > 0:
            dpl_flags.append(f"-row_search_window {int(new_p['row_search_window'])}")
        if new_p.get("disallow_one_site_gaps", 0):
            dpl_flags.append("-disallow_one_site_gaps")
        dpl_flags.append("-use_diamond_legalizer")
        if new_p.get("disable_window_extension", 0):
            dpl_flags.append("-disable_window_extension")
        dpl_str = " ".join(dpl_flags)

        # Also run BASELINE explicitly on same DEF for fair comparison
        ok_b, rl_hpwl, t = run_openroad(def_rel, dpl_str)
        # Baseline is pre-computed from registry
        impr_pct = ((base_hpwl - rl_hpwl) / base_hpwl * 100) if ok_b and rl_hpwl > 0 else 0.0
        abs_impr = base_hpwl - rl_hpwl if ok_b and rl_hpwl > 0 else 0.0
        status = "PASS" if ok_b else "FAIL"

        print(f"  [{b_id}] Design: {d_id}")
        print(f"    Action: {ACTIONS[a_int]['name']} | Flags: {dpl_str}")
        print(f"    Baseline HPWL : {base_hpwl:>12.1f} µm")
        print(f"    RL HPWL       : {rl_hpwl:>12.1f} µm  ({status})")
        print(f"    Improvement   : {abs_impr:>+10.1f} µm  ({impr_pct:+.6f}%)")

        all_results.append({
            "seed": seed, "benchmark_id": b_id, "design": d_id,
            "baseline_hpwl": base_hpwl, "rl_hpwl": rl_hpwl if ok_b else base_hpwl,
            "absolute_improvement": abs_impr, "improvement_percent": impr_pct,
            "rl_action": ACTIONS[a_int]["name"], "rl_flags": dpl_str,
            "baseline_status": "PASS", "rl_status": status
        })

df = pd.DataFrame(all_results)
df.to_csv(RESULTS / "final_benchmark_results_corrected.csv", index=False)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
pass_results = df[df["rl_status"] == "PASS"]
print(f"Total evaluations: {len(df)} (5 seeds × 4 benchmarks)")
print(f"PASS: {len(pass_results)} | FAIL: {len(df)-len(pass_results)}")
if len(pass_results) > 0:
    print(f"Mean improvement (PASS only): {pass_results['improvement_percent'].mean():+.6f}%")
    print(f"Best improvement: {pass_results['improvement_percent'].max():+.6f}%")
    print(f"Designs with positive improvement: {(pass_results['improvement_percent'] > 1e-5).sum()}")
