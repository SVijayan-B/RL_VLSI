import pytest
import json
import pandas as pd
from pathlib import Path
from src.placement.phase7_action_space import Phase7ActionSpace

root = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
res_dir = root / "results/phase_07"

def test_01_timing_effort_cardinality():
    df = pd.read_csv(res_dir / "paper_parameter_reference.csv")
    row = df[df["paper_parameter"] == "timing effort"]
    assert len(row) == 1
    assert int(row["number_of_values"].iloc[0]) == 2

def test_02_clock_power_driven_cardinality():
    df = pd.read_csv(res_dir / "paper_parameter_reference.csv")
    row = df[df["paper_parameter"] == "clock power driven"]
    assert len(row) == 1
    assert int(row["number_of_values"].iloc[0]) == 3

def test_03_paper_action_names():
    df = pd.read_csv(res_dir / "paper_action_reference.csv")
    names = dict(zip(df["action_id"], df["action_name"]))
    assert names[8] == "UP Global"
    assert names[9] == "DOWN Global"
    assert names[10] == "INVERT-MIX"

def test_04_unavailable_action_classification():
    df = pd.read_csv(res_dir / "action_validation.csv")
    status_map = dict(zip(df["action_id"], df["openroad_action_status"]))
    assert status_map[8] == "UNAVAILABLE"
    assert status_map[9] == "UNAVAILABLE"
    assert status_map[10] == "UNAVAILABLE"
    assert status_map[1] == "VERIFIED"
    assert status_map[11] == "VERIFIED"

def test_05_sensitivity_direction_threshold():
    df = pd.read_csv(res_dir / "parameter_sensitivity_final.csv")
    tol = 0.001
    for _, row in df.iterrows():
        dh = row["delta_high_pct"]
        if dh > tol:
            assert row["effect_direction"] == "DEGRADATION"
        elif dh < -tol:
            assert row["effect_direction"] == "IMPROVEMENT"
        else:
            assert row["effect_direction"] == "NEUTRAL"

def test_06_hpwl_interaction_calculation():
    df = pd.read_csv(res_dir / "parameter_interactions_final.csv")
    for _, row in df.iterrows():
        obs = row["observed_delta_hpwl_um"]
        exp = row["expected_additive_hpwl_delta_um"]
        diff = obs - exp
        assert abs(row["hpwl_interaction_um"] - diff) < 1e-4
        assert row["hpwl_interaction_detected"] == (abs(diff) > 1.0)
    # On BENCH_01 all HPWL values are equal to baseline
    assert (df["hpwl_interaction_um"] == 0.0).all()
    assert not df["hpwl_interaction_detected"].any()

def test_07_runtime_interaction_calculation():
    df = pd.read_csv(res_dir / "parameter_interactions_final.csv")
    assert "runtime_interaction_sec" in df.columns
    assert "runtime_interaction_detected" in df.columns
    for _, row in df.iterrows():
        obs = row["observed_delta_runtime_sec"]
        exp = row["expected_additive_runtime_delta_sec"]
        inter = obs - exp
        assert abs(row["runtime_interaction_sec"] - inter) < 1e-3

def test_08_baseline_hpwl_lock():
    with open(res_dir / "integrity/baseline_lock.json") as f:
        lock = json.load(f)
    assert abs(lock["phase4_reference_hpwl"] - 731162.90) < 1e-4
    assert abs(lock["validated_hpwl"] - 731162.90) < 1e-4
