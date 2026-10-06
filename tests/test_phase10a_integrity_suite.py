"""
Phase 10A: Final Integrity Cleanup & Protocol Verification Suite.
Validates:
1. Benchmark registry terminology & exact numerical lock (Initial vs Legalized DPL)
2. All 4 authoritative benchmarks (BENCH_01 through BENCH_04)
3. Exactly six active parameters and strict bounds
4. Paper action space adaptation (8 active verified vs 3 unavailable)
5. Exactly 41-D programmatic state shape & finite values
6. Frozen GraphSAGE 32-D embeddings across all 54 designs
7. Strict data split isolation (no leakage of held-out test benchmarks)
8. Relative HPWL reward mathematical behavior & failure handling
9. Multi-seed training policy configuration in configs/phase11_a2c_training_protocol.json
10. A2C model gradient and loss finiteness
11. Checkpoint reload determinism
"""

import json
import os
import pandas as pd
import numpy as np
import pytest
import torch

from src.rl.state import PlacementStateSpace
from src.rl.action_space import PlacementActionRegistry
from src.rl.reward import PlacementRewardEngine
from src.rl.environment import VLSIPlacementEnv
from src.rl.a2c import ActorCritic
from metrics.hpwl import compute_canonical_hpwl

BENCH_REG_PATH = "results/phase_10/benchmark_registry.csv"
PROTOCOL_PATH = "configs/phase11_a2c_training_protocol.json"
PARAM_SPACE_PATH = "configs/phase10_parameter_space.json"
EMB_PATH = "results/phase_09/graph_embeddings.csv"

TEST_BENCHMARKS = {
    "BENCH_01_RISCY_C2_U70": {"init": 730968.99, "legal": 731162.90, "design": "RISCY-a-1-c2"},
    "BENCH_02_RISCY_C2_U90": {"init": 585708.96, "legal": 708651.30, "design": "RISCY-a-1-c2"},
    "BENCH_03_RISCY_C5_U70": {"init": 699223.74, "legal": 701234.80, "design": "RISCY-a-1-c5"},
    "BENCH_04_RISCY_C20_U70": {"init": 699355.68, "legal": 700395.90, "design": "RISCY-a-1-c20"}
}


def test_01_benchmark_registry_terminology():
    assert os.path.exists(BENCH_REG_PATH)
    df = pd.read_csv(BENCH_REG_PATH)
    expected_cols = [
        "benchmark_id", "design_id", "split", "source_netlist", "source_DEF",
        "graph_file", "embedding_file", "initial_HPWL_um", "default_dpl_baseline_HPWL_um",
        "rl_start_HPWL_um", "baseline_source", "seed"
    ]
    for c in expected_cols:
        assert c in df.columns, f"Missing column {c} in benchmark_registry.csv"


def test_02_all_four_authoritative_benchmarks():
    df = pd.read_csv(BENCH_REG_PATH).set_index("benchmark_id")
    for b_id, vals in TEST_BENCHMARKS.items():
        assert b_id in df.index
        row = df.loc[b_id]
        assert row["design_id"] == vals["design"]
        assert row["split"] == "HELD_OUT_TEST"
        assert row["initial_HPWL_um"] == pytest.approx(vals["init"], abs=0.01)
        assert row["default_dpl_baseline_HPWL_um"] == pytest.approx(vals["legal"], abs=0.01)
        assert row["rl_start_HPWL_um"] == pytest.approx(vals["legal"], abs=0.01)


def test_03_six_active_parameters():
    with open(PARAM_SPACE_PATH, "r") as f:
        cfg = json.load(f)
    params = cfg["parameters"]
    assert len(params) == 6
    names = [p["name"] for p in params]
    expected_names = [
        "max_displacement", "site_search_window", "row_search_window",
        "disallow_one_site_gaps", "use_diamond_legalizer", "disable_window_extension"
    ]
    assert names == expected_names
    for p in params:
        assert p["verification_status"] == "VERIFIED"


def test_04_action_space_adaptation():
    act_reg = PlacementActionRegistry()
    assert act_reg.num_actions == 8
    # Test unavailable actions are guarded
    for unavail_id in [8, 9, 10]:
        act_info = act_reg.ACTIONS[unavail_id]
        assert act_info["status"] == "UNAVAILABLE"
        _, valid = act_reg.apply_action(unavail_id, {"max_displacement": 10})
        assert not valid


def test_05_state_space_dimension_41():
    st_space = PlacementStateSpace()
    assert st_space.total_dim == 41
    dummy_emb = np.zeros(32, dtype=np.float32)
    dummy_params = {"max_displacement": 0, "site_search_window": 0, "row_search_window": 0, "disallow_one_site_gaps": False, "use_diamond_legalizer": False, "disable_window_extension": False}
    st = st_space.construct_state(dummy_emb, dummy_params, 731162.9, 731162.9, 731162.9, 0, 10)
    assert st.shape == (41,)
    assert not np.isnan(st).any()


def test_06_frozen_graphsage_embeddings():
    assert os.path.exists(EMB_PATH)
    df = pd.read_csv(EMB_PATH)
    assert len(df) == 54
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    assert len(emb_cols) == 32
    assert not df[emb_cols].isna().any().any()


def test_07_strict_data_split_isolation():
    env = VLSIPlacementEnv(quarantine_test_designs=True)
    held_out_designs = {"RISCY-a-1-c2", "RISCY-a-1-c5", "RISCY-a-1-c20"}
    for _, r in env.active_benchmarks.iterrows():
        assert r["split"] == "TRAIN"
        assert r["design_id"] not in held_out_designs


def test_08_reward_mathematical_behavior():
    r_engine = PlacementRewardEngine()
    # Positive for wirelength decrease
    r_imp, _ = r_engine.compute_reward(previous_hpwl=1000.0, current_hpwl=900.0, baseline_hpwl=1000.0, openroad_success=True)
    assert r_imp > 0.0
    # Negative for wirelength increase
    r_deg, _ = r_engine.compute_reward(previous_hpwl=1000.0, current_hpwl=1100.0, baseline_hpwl=1000.0, openroad_success=True)
    assert r_deg < 0.0
    # Failure penalty
    r_fail, m_fail = r_engine.compute_reward(previous_hpwl=1000.0, current_hpwl=np.nan, baseline_hpwl=1000.0, openroad_success=False)
    assert r_fail == -1.0
    assert m_fail["status"] == "FAILED"


def test_09_multi_seed_protocol_config():
    assert os.path.exists(PROTOCOL_PATH)
    with open(PROTOCOL_PATH, "r") as f:
        proto = json.load(f)
    seeds = proto["random_seed_policy"]["minimum_seed_set"]
    assert len(seeds) >= 5
    assert set(seeds) == {42, 43, 44, 45, 46}
    assert proto["representation_freeze"]["status"] == "FROZEN"


def test_10_a2c_loss_and_gradient_finiteness():
    model = ActorCritic(state_dim=41, action_dim=8, hidden_dim=64)
    st = torch.randn(5, 41)
    act = torch.tensor([0, 1, 2, 3, 4], dtype=torch.long)
    _, log_probs, entropy, values = model.get_action_and_value(st, act)
    returns = torch.tensor([[0.1], [0.2], [-0.1], [0.0], [0.05]], dtype=torch.float32)
    adv = returns - values
    loss = -(log_probs.unsqueeze(1) * adv.detach()).mean() + 0.5 * torch.nn.functional.mse_loss(values, returns)
    loss.backward()
    assert torch.isfinite(loss)
    for p in model.parameters():
        assert p.grad is not None
        assert torch.isfinite(p.grad).all()


def test_11_checkpoint_reload_determinisim():
    ckpt_path = "results/phase_10/checkpoints/a2c_smoke_checkpoint.pt"
    assert os.path.exists(ckpt_path)
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    model1 = ActorCritic(state_dim=41, action_dim=8, hidden_dim=64)
    model2 = ActorCritic(state_dim=41, action_dim=8, hidden_dim=64)
    model1.load_state_dict(ckpt["model_state_dict"])
    model2.load_state_dict(ckpt["model_state_dict"])
    st = torch.randn(1, 41)
    with torch.no_grad():
        l1, v1 = model1(st)
        l2, v2 = model2(st)
    assert torch.equal(l1, l2)
    assert torch.equal(v1, v2)
