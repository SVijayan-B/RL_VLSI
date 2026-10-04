"""
Phase 10: RL State Representation & Construction.
State formulation strictly obeying Agnesina et al. (IEEE TCAD 2023) adaptation:
STATE = graph_embedding (32) + normalized_parameters (6) + placement_metrics (2) + episode_progress (1)
Total Programmatic Dimension: 41
"""

import json
import os
from typing import Dict, Any, List, Optional
import numpy as np
import torch

PARAM_CONFIG_PATH = "configs/phase10_parameter_space.json"

class PlacementStateSpace:
    """
    Programmatic State Space Encoder for VLSI Placement RL.
    """
    def __init__(self, param_config_path: str = PARAM_CONFIG_PATH):
        with open(param_config_path, "r") as f:
            self.param_config = json.load(f)

        self.params = self.param_config["parameters"]
        self.num_params = len(self.params) # 6
        self.graph_emb_dim = 32
        
        # Placement metrics:
        # [0]: normalized_hpwl (hpwl_current / hpwl_baseline)
        # [1]: relative_hpwl_change ((hpwl_prev - hpwl_curr) / hpwl_prev)
        self.num_placement_metrics = 2
        
        # Progress metric:
        # [0]: step_fraction (step_idx / max_steps)
        self.num_progress_metrics = 1

        self.total_dim = (
            self.graph_emb_dim +
            self.num_params +
            self.num_placement_metrics +
            self.num_progress_metrics
        )

        self.provenance = {
            "graph_embedding": {"dim": 32, "provenance": "Phase 9 Frozen GraphSAGE (DIRECT)"},
            "parameters": {"dim": 6, "provenance": "OpenROAD Verified Placement Space (DIRECT)"},
            "placement_metrics": {"dim": 2, "provenance": "Canonical DEF HPWL Extractor (DERIVED)"},
            "episode_progress": {"dim": 1, "provenance": "Environment Progression (DERIVED)"}
        }

    def normalize_parameters(self, param_dict: Dict[str, Any]) -> np.ndarray:
        """
        Normalizes raw parameter dictionary into [0, 1] range using declared bounds.
        """
        norm_vals = []
        for p in self.params:
            name = p["name"]
            val = param_dict.get(name, p["default"])
            p_min = p["minimum"]
            p_max = p["maximum"]

            if p["datatype"] == "boolean":
                norm_val = 1.0 if bool(val) else 0.0
            else:
                # Clamp within declared bounds
                clamped = max(p_min, min(p_max, float(val)))
                norm_val = (clamped - p_min) / (p_max - p_min) if p_max > p_min else 0.0

            norm_vals.append(norm_val)

        return np.array(norm_vals, dtype=np.float32)

    def construct_state(
        self,
        graph_embedding: np.ndarray,
        param_dict: Dict[str, Any],
        current_hpwl: float,
        baseline_hpwl: float,
        previous_hpwl: float,
        step_idx: int,
        max_steps: int
    ) -> np.ndarray:
        """
        Constructs complete 41-dimensional state vector.
        """
        assert graph_embedding.shape == (32,), f"Expected graph emb shape (32,), got {graph_embedding.shape}"
        assert not np.isnan(graph_embedding).any(), "Graph embedding contains NaN"
        assert not np.isinf(graph_embedding).any(), "Graph embedding contains Inf"

        # 1. Graph embedding: [32]
        emb = graph_embedding.astype(np.float32)

        # 2. Normalized parameters: [6]
        norm_params = self.normalize_parameters(param_dict)

        # 3. Placement metrics: [2]
        norm_hpwl = float(current_hpwl / baseline_hpwl) if baseline_hpwl > 0 else 1.0
        rel_change = float((previous_hpwl - current_hpwl) / previous_hpwl) if previous_hpwl > 0 else 0.0
        metrics = np.array([norm_hpwl, rel_change], dtype=np.float32)

        # 4. Episode progress: [1]
        prog = np.array([float(step_idx) / float(max_steps) if max_steps > 0 else 0.0], dtype=np.float32)

        state_vec = np.concatenate([emb, norm_params, metrics, prog], axis=0)
        assert state_vec.shape == (self.total_dim,), f"Expected total state dim {self.total_dim}, got {state_vec.shape}"
        assert not np.isnan(state_vec).any(), "State vector contains NaN"
        assert not np.isinf(state_vec).any(), "State vector contains Inf"

        return state_vec
