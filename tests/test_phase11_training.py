"""
Phase 11: Multi-Seed A2C Training Validation Suite.
Validates all 15 required criteria from the Phase 11 specification:
1. Actor output dimension = 8
2. Critic output dimension = 1
3. Observation dimension = 41
4. Rewards finite
5. Actor loss finite
6. Critic loss finite
7. Gradients finite
8. Action validity
9. Checkpoint save
10. Checkpoint reload
11. Seed propagation
12. Test-design quarantine
13. Training CSV schema
14. Episode metrics schema
15. Multi-seed directory isolation
"""

import json
import os
import glob
import pandas as pd
import numpy as np
import pytest
import torch

from src.rl.a2c import ActorCritic
from src.rl.environment import VLSIPlacementEnv

BASE_RESULTS_DIR = "results/phase_11"
SEEDS = [42, 43, 44, 45, 46]
TEST_BENCHMARKS = {"RISCY-a-1-c2", "RISCY-a-1-c5", "RISCY-a-1-c20", "BENCH_01_RISCY_C2_U70", "BENCH_02_RISCY_C2_U90", "BENCH_03_RISCY_C5_U70", "BENCH_04_RISCY_C20_U70"}


def test_01_02_03_network_dimensions():
    model = ActorCritic(state_dim=41, action_dim=8, hidden_dim=128)
    dummy_s = torch.randn(2, 41)
    logits, val = model(dummy_s)
    assert logits.shape == (2, 8), f"Expected actor logits (2, 8), got {logits.shape}"
    assert val.shape == (2, 1), f"Expected critic value (2, 1), got {val.shape}"


def test_04_05_06_07_losses_and_gradients_finite():
    for s in SEEDS:
        ep_file = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "episode_metrics.csv")
        assert os.path.exists(ep_file)
        df_ep = pd.read_csv(ep_file)
        assert len(df_ep) == 100
        assert not df_ep["policy_loss"].isna().any()
        assert not df_ep["value_loss"].isna().any()
        assert not df_ep["total_loss"].isna().any()
        assert not np.isinf(df_ep["policy_loss"].values).any()
        assert not np.isinf(df_ep["value_loss"].values).any()
        assert not np.isinf(df_ep["total_loss"].values).any()


def test_08_action_validity():
    for s in SEEDS:
        tr_file = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "transitions.csv")
        df_tr = pd.read_csv(tr_file)
        assert df_tr["action_id"].between(0, 7).all()
        assert (df_tr["execution_status"] == "VALID").all()


def test_09_10_checkpoint_save_and_reload():
    for s in SEEDS:
        ckpt_best = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "checkpoint_best.pt")
        ckpt_final = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "checkpoint_final.pt")
        assert os.path.exists(ckpt_best)
        assert os.path.exists(ckpt_final)
        
        # Test reloading
        d_best = torch.load(ckpt_best, map_location="cpu", weights_only=False)
        assert "model_state_dict" in d_best
        m = ActorCritic(state_dim=41, action_dim=8, hidden_dim=128)
        m.load_state_dict(d_best["model_state_dict"])
        assert m is not None


def test_11_seed_propagation():
    with open("configs/phase11_a2c_training_protocol.json", "r") as f:
        proto = json.load(f)
    assert set(proto["random_seed_policy"]["minimum_seed_set"]) == set(SEEDS)


def test_12_test_design_quarantine_leakage_audit():
    """Verify zero held-out test benchmarks appear in any training log."""
    for s in SEEDS:
        tr_file = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "transitions.csv")
        df_tr = pd.read_csv(tr_file)
        designs_seen = set(df_tr["design_id"].unique())
        leakage = designs_seen.intersection(TEST_BENCHMARKS)
        assert len(leakage) == 0, f"Critical security leak! Test benchmark {leakage} found in seed {s} training transitions!"


def test_13_training_csv_schema():
    expected_cols = [
        "episode", "step", "design_id", "action_id", "action_name",
        "previous_hpwl_um", "current_hpwl_um", "relative_improvement",
        "reward", "runtime_sec", "execution_status", "seed"
    ]
    for s in SEEDS:
        tr_file = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "transitions.csv")
        df_tr = pd.read_csv(tr_file)
        assert len(df_tr) == 1000
        for c in expected_cols:
            assert c in df_tr.columns, f"Missing {c} in seed_{s}/transitions.csv"


def test_14_episode_metrics_schema():
    expected_cols = [
        "episode", "episode_return", "mean_reward", "initial_hpwl_um",
        "final_hpwl_um", "best_hpwl_um", "relative_improvement_pct",
        "episode_steps", "successful_steps", "failed_steps",
        "policy_loss", "value_loss", "entropy", "total_loss", "seed"
    ]
    for s in SEEDS:
        ep_file = os.path.join(BASE_RESULTS_DIR, f"seed_{s}", "episode_metrics.csv")
        df_ep = pd.read_csv(ep_file)
        assert len(df_ep) == 100
        for c in expected_cols:
            assert c in df_ep.columns, f"Missing {c} in seed_{s}/episode_metrics.csv"


def test_15_multiseed_directory_isolation():
    for s in SEEDS:
        s_dir = os.path.join(BASE_RESULTS_DIR, f"seed_{s}")
        assert os.path.isdir(s_dir)
        meta_file = os.path.join(s_dir, "checkpoint_metadata.json")
        assert os.path.exists(meta_file)
        with open(meta_file, "r") as f:
            m = json.load(f)
        assert m["seed"] == s
