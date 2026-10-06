import copy
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from src.rl.state import PlacementStateSpace
from src.rl.action_space import PlacementActionRegistry
from src.rl.reward import PlacementRewardEngine

class VLSIPlacementEnvPhase12:
    def __init__(self, benchmark_registry_path: str = "results/phase_12/phase12_benchmark_registry.csv",
                 graph_embeddings_path: str = "results/phase_09/graph_embeddings.csv",
                 runs_dir: str = "results/phase_12/runs",
                 max_steps: int = 10,
                 quarantine_test_designs: bool = True):
        self.runs_dir = Path(runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.max_steps = max_steps
        self.quarantine_test_designs = quarantine_test_designs

        self.df_embs = pd.read_csv(graph_embeddings_path).set_index("design_id")
        self.emb_cols = [c for c in self.df_embs.columns if c.startswith("emb_")]

        self.df_bench = pd.read_csv(benchmark_registry_path)
        if self.quarantine_test_designs:
            # Strictly filter to TRAIN designs — uses Phase 11D validated HPWL
            self.active_benchmarks = self.df_bench[self.df_bench["split"] == "TRAIN"].copy()
        else:
            # For held-out evaluation, expose all including HELD_OUT_TEST
            self.active_benchmarks = self.df_bench.copy()

        self.state_space = PlacementStateSpace()
        self.action_registry = PlacementActionRegistry()
        self.reward_engine = PlacementRewardEngine()

        self.observation_dim = self.state_space.total_dim
        self.action_dim = self.action_registry.num_actions

        # Enforce diamond legalizer as per Phase 11E baseline contract
        for p in self.state_space.params:
            if p["name"] == "use_diamond_legalizer":
                p["default"] = 1

    def reset(self, benchmark_id: Optional[str] = None, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        if seed is not None:
            np.random.seed(seed)

        if benchmark_id is not None:
            matches = self.active_benchmarks[self.active_benchmarks["benchmark_id"] == benchmark_id]
            if len(matches) == 0:
                matches = self.df_bench[self.df_bench["benchmark_id"] == benchmark_id]
            assert len(matches) > 0, f"Benchmark {benchmark_id} not found in registry!"
            self.current_benchmark = matches.iloc[0].to_dict()
        else:
            idx = np.random.randint(0, len(self.active_benchmarks))
            self.current_benchmark = self.active_benchmarks.iloc[idx].to_dict()

        self.episode_id = f"ep_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.current_step = 0

        self.current_params = {p["name"]: p["default"] for p in self.state_space.params}
        # Use Phase 11D validated legalized HPWL — the authoritative baseline
        baseline_raw = self.current_benchmark.get("default_dpl_baseline_HPWL_um", None)
        if baseline_raw is None or float(baseline_raw) <= 0:
            baseline_raw = self.current_benchmark.get("rl_start_HPWL_um", 0.0)
        self.baseline_hpwl = float(baseline_raw)
        assert self.baseline_hpwl > 0, (
            f"Invalid baseline HPWL={self.baseline_hpwl} for {self.current_benchmark.get('design_id')}. "
            f"Check phase12_benchmark_registry.csv."
        )
        self.current_hpwl = self.baseline_hpwl
        self.previous_hpwl = self.baseline_hpwl
        
        d_id = self.current_benchmark["design_id"]
        graph_emb = self.df_embs.loc[d_id, self.emb_cols].values.astype(np.float32)

        obs = self.state_space.construct_state(
            graph_embedding=graph_emb,
            param_dict=self.current_params,
            current_hpwl=self.current_hpwl,
            baseline_hpwl=self.baseline_hpwl,
            previous_hpwl=self.previous_hpwl,
            step_idx=self.current_step,
            max_steps=self.max_steps
        )

        info = {
            "episode_id": self.episode_id,
            "benchmark_id": self.current_benchmark["benchmark_id"],
            "design_id": d_id,
            "split": self.current_benchmark["split"],
            "step": self.current_step,
            "baseline_hpwl": self.baseline_hpwl,
            "current_params": copy.deepcopy(self.current_params)
        }

        return obs, info

    def run_openroad_eval(self, design_id: str, dpl_cmd_str: str) -> Tuple[bool, float, float]:
        tcl = f"read_lef /CircuitNet/dataset/raw/circuitnet.lef\n"
        tcl += f"read_def -continue_on_errors /CircuitNet/results/phase_11d/reconstructed_defs/{design_id}.def\n"
        tcl += f"detailed_placement {dpl_cmd_str}\n"
        tcl += f"check_placement -verbose\n"
        tcl += f"exit\n"
        
        start_t = time.time()
        try:
            res = subprocess.run(
                ["docker", "run", "--rm", "-i", "-v", "/home/b_siddarth_vijayan/CircuitNet_28nm:/CircuitNet", "openroad/orfs:latest", "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad", "-no_splash"],
                input=tcl, text=True, capture_output=True, timeout=60
            )
            end_t = time.time()
            out = res.stdout
            
            if "Placement Failures:" in out:
                fail_line = [l for l in out.splitlines() if "Total Placement Failures:" in l]
                if fail_line:
                    try:
                        failures = int(fail_line[0].split(":")[-1].strip())
                        if failures > 0:
                            return False, 0.0, end_t - start_t
                    except ValueError:
                        return False, 0.0, end_t - start_t
            
            leg_hpwl = None
            for line in out.splitlines():
                if "legalized HPWL" in line:
                    leg_hpwl = float(line.split()[-2])
            
            if leg_hpwl is not None:
                return True, leg_hpwl, end_t - start_t
            else:
                return False, 0.0, end_t - start_t
                
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", "$(docker ps -q)"], capture_output=True, shell=True)
            return False, 0.0, 60.0
            
    def step(self, action_id: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.current_step += 1
        prev_params = copy.deepcopy(self.current_params)
        self.previous_hpwl = self.current_hpwl

        new_params, is_valid = self.action_registry.apply_action(action_id, self.current_params)
        self.current_params = new_params
        
        # Enforce diamond legalizer
        self.current_params["use_diamond_legalizer"] = 1

        step_dir = self.runs_dir / self.episode_id / f"step_{self.current_step:03d}"
        step_dir.mkdir(parents=True, exist_ok=True)

        dpl_flags = []
        if self.current_params.get("max_displacement", 0) > 0:
            dpl_flags.append(f"-max_displacement {self.current_params['max_displacement']}")
        if self.current_params.get("site_search_window", 0) > 0:
            dpl_flags.append(f"-site_search_window {self.current_params['site_search_window']}")
        if self.current_params.get("row_search_window", 0) > 0:
            dpl_flags.append(f"-row_search_window {self.current_params['row_search_window']}")
        if self.current_params.get("disallow_one_site_gaps", 0):
            dpl_flags.append("-disallow_one_site_gaps")
        if self.current_params.get("use_diamond_legalizer", 0):
            dpl_flags.append("-use_diamond_legalizer")
        if self.current_params.get("disable_window_extension", 0):
            dpl_flags.append("-disable_window_extension")
        
        dpl_cmd_str = " ".join(dpl_flags)

        d_id = self.current_benchmark["design_id"]
        
        # Execute Real OpenROAD
        openroad_success, new_hpwl, runtime_sec = self.run_openroad_eval(d_id, dpl_cmd_str)
        
        if openroad_success:
            self.current_hpwl = new_hpwl

        reward, reward_meta = self.reward_engine.compute_reward(
            previous_hpwl=self.previous_hpwl,
            current_hpwl=self.current_hpwl,
            baseline_hpwl=self.baseline_hpwl,
            openroad_success=openroad_success
        )

        terminated = bool(self.current_step >= self.max_steps)
        truncated = False

        graph_emb = self.df_embs.loc[d_id, self.emb_cols].values.astype(np.float32)

        obs = self.state_space.construct_state(
            graph_embedding=graph_emb,
            param_dict=self.current_params,
            current_hpwl=self.current_hpwl,
            baseline_hpwl=self.baseline_hpwl,
            previous_hpwl=self.previous_hpwl,
            step_idx=self.current_step,
            max_steps=self.max_steps
        )

        transition_info = {
            "run_id": f"{self.episode_id}_s{self.current_step}",
            "benchmark_id": self.current_benchmark["benchmark_id"],
            "design_id": d_id,
            "split": self.current_benchmark["split"],
            "step": self.current_step,
            "action_id": action_id,
            "action_name": self.action_registry.ACTIONS[action_id]["name"],
            "previous_parameters": prev_params,
            "new_parameters": copy.deepcopy(self.current_params),
            "openroad_flags": dpl_cmd_str,
            "previous_hpwl": self.previous_hpwl,
            "current_hpwl": self.current_hpwl,
            "baseline_hpwl": self.baseline_hpwl,
            "reward": reward,
            "reward_meta": reward_meta,
            "openroad_exit_code": 0 if openroad_success else 1,
            "runtime_sec": round(runtime_sec, 4),
            "metric_status": "VALID",
            "metric_provenance": "CANONICAL_HPWL"
        }

        with open(step_dir / "transition_log.json", "w") as f:
            json.dump(transition_info, f, indent=2)

        return obs, reward, terminated, truncated, transition_info
