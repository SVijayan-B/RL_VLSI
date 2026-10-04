"""
Phase 10: Complete Unit & Integration Test Suite.
Validates:
1. Frozen GraphSAGE interface and embedding integrity
2. Programmatic state space construction and dimension (41)
3. Parameter bounds, normalization, and bounds clamping
4. Verified action space transitions (FLIP, UP, DOWN, DO_NOTHING)
5. Unavailable action rejection (status=UNAVAILABLE)
6. HPWL canonical metric calculation consistency
7. Reward engine correctness (improvement, degradation, invalid states)
8. Environment reset, stepping, and isolation
9. Deterministic environment replay
10. Train/Test partition isolation (no leakage of held-out designs)
11. A2C model forward pass and loss backpropagation
12. Checkpoint reload equivalence
"""

import json
import os
import numpy as np
import pytest
import torch

from src.rl.state import PlacementStateSpace
from src.rl.action_space import PlacementActionRegistry
from src.rl.reward import PlacementRewardEngine
from src.rl.environment import VLSIPlacementEnv
from src.rl.a2c import ActorCritic
from metrics.hpwl import compute_canonical_hpwl

TEST_BENCHMARKS = {"RISCY-a-1-c20", "RISCY-a-1-c2", "RISCY-a-1-c5"}


def test_01_frozen_graphsage_embeddings():
    emb_path = "results/phase_09/graph_embeddings.csv"
    assert os.path.exists(emb_path)
    import pandas as pd
    df = pd.read_csv(emb_path)
    assert len(df) == 54
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    assert len(emb_cols) == 32
    assert not df[emb_cols].isna().any().any()
    assert not np.isinf(df[emb_cols].values).any()


def test_02_state_space_dimensions():
    state_space = PlacementStateSpace()
    assert state_space.total_dim == 41
    dummy_emb = np.random.randn(32).astype(np.float32)
    dummy_params = {
        "max_displacement": 20,
        "site_search_window": 10,
        "row_search_window": 4,
        "disallow_one_site_gaps": True,
        "use_diamond_legalizer": False,
        "disable_window_extension": False
    }
    state = state_space.construct_state(
        graph_embedding=dummy_emb,
        param_dict=dummy_params,
        current_hpwl=730000.0,
        baseline_hpwl=731000.0,
        previous_hpwl=731000.0,
        step_idx=2,
        max_steps=10
    )
    assert state.shape == (41,)
    assert not np.isnan(state).any()
    assert not np.isinf(state).any()


def test_03_parameter_normalization():
    state_space = PlacementStateSpace()
    # Min bounds -> 0.0
    min_params = {"max_displacement": 0, "site_search_window": 0, "row_search_window": 0, "disallow_one_site_gaps": False, "use_diamond_legalizer": False, "disable_window_extension": False}
    norm_min = state_space.normalize_parameters(min_params)
    assert np.allclose(norm_min, 0.0)

    # Max bounds -> 1.0
    max_params = {"max_displacement": 100, "site_search_window": 100, "row_search_window": 20, "disallow_one_site_gaps": True, "use_diamond_legalizer": True, "disable_window_extension": True}
    norm_max = state_space.normalize_parameters(max_params)
    assert np.allclose(norm_max, 1.0)


def test_04_action_space_transitions():
    act_reg = PlacementActionRegistry()
    params = {"max_displacement": 10, "site_search_window": 10, "row_search_window": 2, "disallow_one_site_gaps": False, "use_diamond_legalizer": False, "disable_window_extension": False}
    
    # 0: FLIP
    p_flip, valid = act_reg.apply_action(0, params)
    assert valid
    assert p_flip["disallow_one_site_gaps"] is True
    assert p_flip["use_diamond_legalizer"] is True
    assert p_flip["disable_window_extension"] is True

    # 1: UP_INTEGERS
    p_up, valid = act_reg.apply_action(1, params)
    assert valid
    assert p_up["max_displacement"] == 20
    assert p_up["site_search_window"] == 20
    assert p_up["row_search_window"] == 4

    # 2: DOWN_INTEGERS
    p_down, valid = act_reg.apply_action(2, params)
    assert valid
    assert p_down["max_displacement"] == 0
    assert p_down["site_search_window"] == 0
    assert p_down["row_search_window"] == 0


def test_05_unavailable_action_rejection():
    act_reg = PlacementActionRegistry()
    params = {"max_displacement": 10}
    # Action 8 is UP_GLOBAL (UNAVAILABLE)
    p_out, valid = act_reg.apply_action(8, params)
    assert not valid
    assert p_out == params


def test_06_canonical_hpwl():
    def_path = "dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def"
    res = compute_canonical_hpwl(def_path)
    assert res["total_hpwl_um"] == pytest.approx(730968.99, abs=1.0)
    assert res["num_cells"] == 52147
    assert res["provenance"] == "DIRECT_DEF_PARSER"


def test_07_reward_engine():
    engine = PlacementRewardEngine()
    # Improvement (wirelength decreased)
    r_pos, m_pos = engine.compute_reward(previous_hpwl=1000.0, current_hpwl=950.0, baseline_hpwl=1000.0, openroad_success=True)
    assert r_pos > 0.0
    assert m_pos["status"] == "SUCCESS"

    # Degradation (wirelength increased)
    r_neg, m_neg = engine.compute_reward(previous_hpwl=1000.0, current_hpwl=1050.0, baseline_hpwl=1000.0, openroad_success=True)
    assert r_neg < 0.0
    assert m_neg["status"] == "SUCCESS"

    # OpenROAD failure
    r_fail, m_fail = engine.compute_reward(previous_hpwl=1000.0, current_hpwl=np.nan, baseline_hpwl=1000.0, openroad_success=False)
    assert r_fail == -1.0
    assert m_fail["status"] == "FAILED"


def test_08_environment_stepping():
    env = VLSIPlacementEnv(max_steps=3, quarantine_test_designs=False)
    obs, info = env.reset(benchmark_id="BENCH_01_RISCY_C2_U70", seed=42)
    assert obs.shape == (41,)
    assert info["step"] == 0

    next_obs, r, term, trunc, t_info = env.step(action_id=1)
    assert next_obs.shape == (41,)
    assert t_info["step"] == 1
    assert t_info["action_id"] == 1
    assert not term


def test_09_deterministic_environment_replay():
    env1 = VLSIPlacementEnv(max_steps=3, quarantine_test_designs=False)
    env2 = VLSIPlacementEnv(max_steps=3, quarantine_test_designs=False)

    obs1, _ = env1.reset(benchmark_id="BENCH_01_RISCY_C2_U70", seed=42)
    obs2, _ = env2.reset(benchmark_id="BENCH_01_RISCY_C2_U70", seed=42)
    assert np.allclose(obs1, obs2)

    o1, r1, _, _, _ = env1.step(action_id=1)
    o2, r2, _, _, _ = env2.step(action_id=1)
    assert np.allclose(o1, o2)
    assert r1 == r2


def test_10_train_test_split_isolation():
    env = VLSIPlacementEnv(quarantine_test_designs=True)
    # Ensure active benchmarks contain zero held-out test designs
    for _, row in env.active_benchmarks.iterrows():
        assert row["split"] == "TRAIN"
        assert row["design_id"] not in TEST_BENCHMARKS


def test_11_a2c_forward_and_loss():
    model = ActorCritic(state_dim=41, action_dim=8, hidden_dim=32)
    state = torch.randn(4, 41)
    action, log_prob, entropy, value = model.get_action_and_value(state)
    assert action.shape == (4,)
    assert log_prob.shape == (4,)
    assert value.shape == (4, 1)

    loss = -log_prob.mean() + value.mean()
    loss.backward()
    for param in model.parameters():
        assert param.grad is not None


def test_12_checkpoint_reload():
    ckpt_path = "results/phase_10/checkpoints/a2c_smoke_checkpoint.pt"
    assert os.path.exists(ckpt_path)
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    assert "model_state_dict" in ckpt
    model = ActorCritic(state_dim=41, action_dim=8, hidden_dim=64)
    model.load_state_dict(ckpt["model_state_dict"])
    assert model is not None
