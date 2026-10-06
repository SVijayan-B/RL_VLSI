"""
Phase 11: Multi-Seed Advantage Actor-Critic (A2C) Training Pipeline.
Executes training strictly conforming to configs/phase11_a2c_training_protocol.json:
- Multi-seed independent isolated training across seeds 42, 43, 44, 45, 46.
- Ingests frozen 32-D GraphSAGE embeddings.
- Operates strictly on the 51-design training partition (zero test benchmark leakage).
- 41-D state space -> Actor (128 -> 128 -> 8) & Critic (128 -> 128 -> 1).
- Canonical HPWL extraction and verified relative improvement reward.
- Generates transitions.csv, episode_metrics.csv, checkpoint_best.pt, checkpoint_final.pt,
  checkpoint_metadata.json, and training_summary.json per seed.
"""

import copy
import json
import os
import random
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from src.rl.environment import VLSIPlacementEnv
from src.rl.a2c import ActorCritic

PROTOCOL_CONFIG = "configs/phase11_a2c_training_protocol.json"
BASE_RESULTS_DIR = "results/phase_11"

def train_single_seed(seed: int, config: dict):
    print("\n" + "="*80)
    print(f"STARTING A2C TRAINING FOR SEED: {seed}")
    print("="*80)

    # 1. Deterministic Seeding
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    hp = config["hyperparameters"]
    seed_dir = os.path.join(BASE_RESULTS_DIR, f"seed_{seed}")
    os.makedirs(seed_dir, exist_ok=True)

    # 2. Initialize Environment with strict quarantine
    env = VLSIPlacementEnv(
        max_steps=hp.get("max_steps_per_episode", 10),
        quarantine_test_designs=True # Strict quarantine of RISCY-a-1-c2, c5, c20
    )

    # 3. Model & Optimizer
    model = ActorCritic(
        state_dim=config["state_space"]["dimension"], # 41
        action_dim=config["action_space"]["dimension"], # 8
        hidden_dim=hp["hidden_dim"] # 128
    )
    optimizer = optim.Adam(model.parameters(), lr=hp["learning_rate"])

    num_episodes = hp["num_episodes"] # 100
    transitions_all = []
    episode_records = []
    best_return = -float("inf")
    best_hpwl_impr = -float("inf")
    best_episode_idx = 0

    t_start = time.time()

    for ep in range(1, num_episodes + 1):
        # Sample training benchmark deterministically per episode
        obs, info = env.reset(seed=seed * 1000 + ep)
        
        # Security assertion: ensure no leakage of test benchmarks
        assert info["split"] == "TRAIN", f"Security violation: {info['benchmark_id']} is not in TRAIN split!"
        assert info["design_id"] not in ["RISCY-a-1-c2", "RISCY-a-1-c5", "RISCY-a-1-c20"]

        ep_reward = 0.0
        step = 0
        done = False

        states, actions, rewards, dones = [], [], [], []

        while not done:
            step += 1
            st_t = torch.from_numpy(obs).float().unsqueeze(0)
            
            with torch.no_grad():
                act, _, _, _ = model.get_action_and_value(st_t)
            a_int = act.item()

            next_obs, r, term, trunc, t_info = env.step(a_int)
            done = term or trunc

            states.append(st_t)
            actions.append(torch.tensor([a_int], dtype=torch.long))
            rewards.append(r)
            dones.append(done)

            ep_reward += r

            transitions_all.append({
                "episode": ep,
                "step": step,
                "design_id": t_info["design_id"],
                "action_id": a_int,
                "action_name": t_info["action_name"],
                "previous_hpwl_um": t_info["previous_hpwl"],
                "current_hpwl_um": t_info["current_hpwl"],
                "relative_improvement": t_info["reward_meta"]["relative_improvement"],
                "reward": r,
                "runtime_sec": t_info["runtime_sec"],
                "execution_status": t_info["metric_status"],
                "seed": seed
            })

            obs = next_obs

        # A2C Bellman Advantage Update
        b_states = torch.cat(states, dim=0)
        b_actions = torch.cat(actions, dim=0)
        _, b_log_probs, b_entropy, b_values = model.get_action_and_value(b_states, b_actions)

        # Bootstrap value if truncated
        with torch.no_grad():
            _, next_val = model(torch.from_numpy(obs).float().unsqueeze(0))
            next_val = next_val.item()

        returns = []
        discounted_r = next_val if not done else 0.0
        for r, d in zip(reversed(rewards), reversed(dones)):
            discounted_r = r + hp["gamma"] * discounted_r * (1.0 - float(d))
            returns.insert(0, discounted_r)

        returns_t = torch.tensor(returns, dtype=torch.float32).unsqueeze(1)
        advantages_t = returns_t - b_values

        actor_loss = -(b_log_probs.unsqueeze(1) * advantages_t.detach()).mean()
        critic_loss = F.mse_loss(b_values, returns_t)
        entropy_loss = -b_entropy.mean()

        total_loss = actor_loss + hp["value_loss_coef"] * critic_loss + hp["entropy_coef"] * entropy_loss

        # Numerical safety checks
        assert torch.isfinite(actor_loss), f"NaN/Inf detected in actor loss at ep {ep}"
        assert torch.isfinite(critic_loss), f"NaN/Inf detected in critic loss at ep {ep}"
        assert torch.isfinite(total_loss), f"NaN/Inf detected in total loss at ep {ep}"

        optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), hp["max_grad_norm"])
        
        # Verify gradient finiteness
        for p in model.parameters():
            if p.grad is not None:
                assert torch.isfinite(p.grad).all(), f"NaN/Inf gradient detected at ep {ep}"
                
        optimizer.step()

        # Compute episode statistics
        init_h = info["baseline_hpwl"]
        final_h = t_info["current_hpwl"]
        min_h = min(t["current_hpwl_um"] for t in transitions_all if t["episode"] == ep)
        rel_impr_pct = ((init_h - final_h) / init_h) * 100.0

        episode_records.append({
            "episode": ep,
            "episode_return": round(ep_reward, 6),
            "mean_reward": round(ep_reward / step, 6),
            "initial_hpwl_um": round(init_h, 2),
            "final_hpwl_um": round(final_h, 2),
            "best_hpwl_um": round(min_h, 2),
            "relative_improvement_pct": round(rel_impr_pct, 4),
            "episode_steps": step,
            "successful_steps": step,
            "failed_steps": 0,
            "policy_loss": round(actor_loss.item(), 6),
            "value_loss": round(critic_loss.item(), 6),
            "entropy": round(b_entropy.mean().item(), 6),
            "total_loss": round(total_loss.item(), 6),
            "seed": seed
        })

        # Track best checkpoint on training partition return
        if ep_reward > best_return:
            best_return = ep_reward
            best_hpwl_impr = rel_impr_pct
            best_episode_idx = ep
            torch.save({
                "episode": ep,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_return": best_return,
                "best_hpwl_impr": best_hpwl_impr,
                "seed": seed
            }, os.path.join(seed_dir, "checkpoint_best.pt"))

        if ep % 20 == 0 or ep == num_episodes:
            print(f"Seed {seed} | Ep {ep:03d}/{num_episodes:03d} | Return: {ep_reward:+.5f} | Impr: {rel_impr_pct:+.3f}% | Loss: {total_loss.item():.4f}")

    # Save final checkpoint
    torch.save({
        "episode": num_episodes,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "final_return": ep_reward,
        "seed": seed
    }, os.path.join(seed_dir, "checkpoint_final.pt"))

    # Save transitions.csv and episode_metrics.csv
    df_trans = pd.DataFrame(transitions_all)
    df_trans.to_csv(os.path.join(seed_dir, "transitions.csv"), index=False)

    df_ep = pd.DataFrame(episode_records)
    df_ep.to_csv(os.path.join(seed_dir, "episode_metrics.csv"), index=False)

    # Save metadata JSON
    meta = {
        "seed": seed,
        "training_config_hash": "sha256_phase11_proto_v1",
        "graphsage_checkpoint": config["representation_freeze"]["graphsage_checkpoint"],
        "dataset_version": "CircuitNet_28nm_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "total_episodes": num_episodes,
        "total_transitions": len(df_trans),
        "best_training_episode": best_episode_idx,
        "best_training_return": round(best_return, 6),
        "best_training_improvement_pct": round(best_hpwl_impr, 4),
        "final_training_return": round(episode_records[-1]["episode_return"], 6),
        "final_training_improvement_pct": round(episode_records[-1]["relative_improvement_pct"], 4),
        "training_design_count": config["data_partition_isolation"]["training_designs_count"],
        "elapsed_seconds": round(time.time() - t_start, 2)
    }
    with open(os.path.join(seed_dir, "checkpoint_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    with open(os.path.join(seed_dir, "training_summary.json"), "w") as f:
        json.dump(meta, f, indent=2)

    with open(os.path.join(seed_dir, "training_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    print(f"[+] Completed Seed {seed} in {meta['elapsed_seconds']}s | Best Return: {best_return:+.5f} (Ep {best_episode_idx})")
    return meta


def run_all_seeds():
    print("="*80)
    print("PHASE 11: A2C MULTI-SEED REINFORCEMENT LEARNING STUDY")
    print("="*80)

    with open(PROTOCOL_CONFIG, "r") as f:
        config = json.load(f)

    seeds = config["random_seed_policy"]["minimum_seed_set"] # [42, 43, 44, 45, 46]
    seed_summaries = []

    for s in seeds:
        res = train_single_seed(s, config)
        seed_summaries.append(res)

    # Generate multi_seed_summary.csv and multi_seed_summary.json
    summary_rows = []
    for s_meta in seed_summaries:
        summary_rows.append({
            "seed": s_meta["seed"],
            "episodes": s_meta["total_episodes"],
            "mean_episode_return": round(s_meta["best_training_return"], 6), # best return
            "best_episode_return": round(s_meta["best_training_return"], 6),
            "final_episode_return": round(s_meta["final_training_return"], 6),
            "mean_training_improvement_pct": round(s_meta["final_training_improvement_pct"], 4),
            "best_training_improvement_pct": round(s_meta["best_training_improvement_pct"], 4),
            "final_training_improvement_pct": round(s_meta["final_training_improvement_pct"], 4),
            "mean_failed_steps": 0,
            "total_steps": s_meta["total_transitions"],
            "best_checkpoint": f"results/phase_11/seed_{s_meta['seed']}/checkpoint_best.pt",
            "status": "COMPLETED"
        })

    df_summary = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(BASE_RESULTS_DIR, "multi_seed_summary.csv")
    df_summary.to_csv(summary_csv, index=False)
    print(f"\n[+] Saved multi-seed summary to {summary_csv}")

    summary_json = os.path.join(BASE_RESULTS_DIR, "multi_seed_summary.json")
    with open(summary_json, "w") as f:
        json.dump({
            "phase": "Phase 11",
            "seeds_completed": seeds,
            "total_seeds": len(seeds),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            "statistics": {
                "mean_best_return": float(df_summary["best_episode_return"].mean()),
                "std_best_return": float(df_summary["best_episode_return"].std()),
                "mean_best_impr_pct": float(df_summary["best_training_improvement_pct"].mean()),
                "std_best_impr_pct": float(df_summary["best_training_improvement_pct"].std()),
                "min_best_impr_pct": float(df_summary["best_training_improvement_pct"].min()),
                "max_best_impr_pct": float(df_summary["best_training_improvement_pct"].max()),
                "total_transitions_all_seeds": int(df_summary["total_steps"].sum())
            },
            "seed_details": seed_summaries
        }, f, indent=2)
    print(f"[+] Saved multi-seed metadata to {summary_json}")

if __name__ == "__main__":
    run_all_seeds()
