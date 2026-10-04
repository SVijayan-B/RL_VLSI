"""
Phase 10: Mathematically Explicit Placement Reward Engine.
Computes primary relative HPWL improvement reward:
reward_hpwl = (HPWL_prev - HPWL_curr) / max(abs(HPWL_prev), epsilon)
Positive for wirelength reduction, negative for wirelength expansion.
Rejects invalid states and OpenROAD failures.
"""

from typing import Dict, Any, Tuple
import numpy as np

class PlacementRewardEngine:
    """
    Computes placement RL rewards with complete provenance tagging.
    """
    def __init__(self, epsilon: float = 1e-6):
        self.epsilon = epsilon
        self.w_hpwl = 1.0 # Primary normalized weight

    def compute_reward(
        self,
        previous_hpwl: float,
        current_hpwl: float,
        baseline_hpwl: float,
        openroad_success: bool
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates step reward.
        Returns:
            (reward_scalar, metadata_dict)
        """
        if not openroad_success or np.isnan(current_hpwl) or np.isinf(current_hpwl) or current_hpwl <= 0:
            # Failure penalty without masking the failed state
            meta = {
                "status": "FAILED",
                "reward_raw": -1.0,
                "reward_hpwl": -1.0,
                "relative_improvement": -1.0,
                "notes": "OpenROAD execution failure or invalid HPWL metric"
            }
            return -1.0, meta

        if previous_hpwl <= 0:
            previous_hpwl = baseline_hpwl

        # Relative HPWL improvement
        # delta > 0 indicates wirelength reduction (improvement)
        delta_hpwl = previous_hpwl - current_hpwl
        denom = max(abs(previous_hpwl), self.epsilon)
        rel_improvement = delta_hpwl / denom

        reward = float(self.w_hpwl * rel_improvement)

        # Sanity check
        if np.isnan(reward) or np.isinf(reward):
            reward = 0.0

        meta = {
            "status": "SUCCESS",
            "reward_raw": round(reward, 6),
            "reward_hpwl": round(reward, 6),
            "relative_improvement": round(rel_improvement, 6),
            "delta_hpwl_um": round(delta_hpwl, 2),
            "previous_hpwl_um": round(previous_hpwl, 2),
            "current_hpwl_um": round(current_hpwl, 2),
            "baseline_hpwl_um": round(baseline_hpwl, 2),
            "provenance": "RELATIVE_HPWL_IMPROVEMENT"
        }

        return reward, meta
