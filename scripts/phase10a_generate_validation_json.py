import json
import os
import pandas as pd

SUMMARY_JSON = "results/phase_10/phase10a_validation.json"

def generate_summary():
    # 1. Baseline validation
    df_base = pd.read_csv("results/phase_10/baseline_validation.csv")
    base_pass = (df_base["pass_fail"] == "PASS").all() and len(df_base) == 4

    # 2. State validation
    from src.rl.state import PlacementStateSpace
    st_space = PlacementStateSpace()
    state_pass = (st_space.total_dim == 41)

    # 3. Action validation
    from src.rl.action_space import PlacementActionRegistry
    act_reg = PlacementActionRegistry()
    _, valid_avail = act_reg.apply_action(0, {"max_displacement": 10})
    _, valid_unavail = act_reg.apply_action(8, {"max_displacement": 10})
    action_pass = valid_avail and not valid_unavail and act_reg.num_actions == 8

    # 4. Reward validation
    from src.rl.reward import PlacementRewardEngine
    r_eng = PlacementRewardEngine()
    r_pos, _ = r_eng.compute_reward(1000.0, 900.0, 1000.0, True)
    r_neg, _ = r_eng.compute_reward(1000.0, 1100.0, 1000.0, True)
    reward_pass = (r_pos > 0.0) and (r_neg < 0.0)

    # 5. Leakage validation
    from src.rl.environment import VLSIPlacementEnv
    env = VLSIPlacementEnv(quarantine_test_designs=True)
    test_set = {"RISCY-a-1-c20", "RISCY-a-1-c2", "RISCY-a-1-c5"}
    active_designs = set(env.active_benchmarks["design_id"])
    leakage_pass = len(active_designs.intersection(test_set)) == 0

    # 6. Determinism validation
    env1 = VLSIPlacementEnv(max_steps=2, quarantine_test_designs=False)
    env2 = VLSIPlacementEnv(max_steps=2, quarantine_test_designs=False)
    o1, _ = env1.reset(benchmark_id="BENCH_01_RISCY_C2_U70", seed=42)
    o2, _ = env2.reset(benchmark_id="BENCH_01_RISCY_C2_U70", seed=42)
    import numpy as np
    det_pass = bool(np.allclose(o1, o2))

    # 7. Checkpoint validation
    ckpt_pass = os.path.exists("results/phase_10/checkpoints/a2c_smoke_checkpoint.pt")

    # 8. Protocol validation
    proto_pass = os.path.exists("configs/phase11_a2c_training_protocol.json") and os.path.exists("results/phase_11/seed_42/transitions.csv")

    overall = "PASS" if all([base_pass, state_pass, action_pass, reward_pass, leakage_pass, det_pass, ckpt_pass, proto_pass]) else "FAIL"

    record = {
        "phase": "10A",
        "status": overall,
        "baseline_validation": "PASS" if base_pass else "FAIL",
        "state_validation": "PASS" if state_pass else "FAIL",
        "action_validation": "PASS" if action_pass else "FAIL",
        "reward_validation": "PASS" if reward_pass else "FAIL",
        "leakage_validation": "PASS" if leakage_pass else "FAIL",
        "determinism_validation": "PASS" if det_pass else "FAIL",
        "checkpoint_validation": "PASS" if ckpt_pass else "FAIL",
        "protocol_validation": "PASS" if proto_pass else "FAIL"
    }

    with open(SUMMARY_JSON, "w") as f:
        json.dump(record, f, indent=2)
    print(f"[+] Saved Phase 10A validation summary to {SUMMARY_JSON}")
    print(json.dumps(record, indent=2))

if __name__ == "__main__":
    generate_summary()
