"""
Phase 10: Verified RL Action Space.
Direct adaptation of Agnesina et al. (IEEE TCAD 2023) Table III.
Maps verified macro-actions into deterministic OpenROAD detailed placement parameters.
Actions without verified OpenROAD implementation are strictly tagged UNAVAILABLE and rejected.
"""

import copy
import json
from typing import Dict, Any, Tuple, Optional

class PlacementActionRegistry:
    """
    Action registry controlling placement parameter updates.
    """
    ACTIONS = {
        0: {
            "name": "FLIP_BOOLEANS",
            "paper_action": "FLIP Booleans",
            "affected_parameters": ["disallow_one_site_gaps", "use_diamond_legalizer", "disable_window_extension"],
            "status": "VERIFIED",
            "description": "Inverts all boolean flags simultaneously"
        },
        1: {
            "name": "UP_INTEGERS",
            "paper_action": "UP Integers",
            "affected_parameters": ["max_displacement", "site_search_window", "row_search_window"],
            "status": "VERIFIED",
            "description": "Increases integer parameters by 1 step (clamped at upper bound)"
        },
        2: {
            "name": "DOWN_INTEGERS",
            "paper_action": "DOWN Integers",
            "affected_parameters": ["max_displacement", "site_search_window", "row_search_window"],
            "status": "VERIFIED",
            "description": "Decreases integer parameters by 1 step (clamped at lower bound)"
        },
        3: {
            "name": "UP_EFFORTS",
            "paper_action": "UP Efforts",
            "affected_parameters": ["row_search_window", "site_search_window"],
            "status": "VERIFIED",
            "description": "Expands detailed placement search effort window"
        },
        4: {
            "name": "DOWN_EFFORTS",
            "paper_action": "DOWN Efforts",
            "affected_parameters": ["row_search_window", "site_search_window"],
            "status": "VERIFIED",
            "description": "Contracts detailed placement search effort window"
        },
        5: {
            "name": "UP_DETAILED",
            "paper_action": "UP Detailed",
            "affected_parameters": ["max_displacement", "site_search_window"],
            "status": "VERIFIED",
            "description": "Expands displacement and site window"
        },
        6: {
            "name": "DOWN_DETAILED",
            "paper_action": "DOWN Detailed",
            "affected_parameters": ["max_displacement", "site_search_window"],
            "status": "VERIFIED",
            "description": "Reduces displacement and site window"
        },
        7: {
            "name": "DO_NOTHING",
            "paper_action": "DO NOTHING",
            "affected_parameters": [],
            "status": "VERIFIED",
            "description": "No-op action preserving current parameter state"
        },
        8: {
            "name": "UP_GLOBAL",
            "paper_action": "UP Global",
            "affected_parameters": [],
            "status": "UNAVAILABLE",
            "description": "Requires commercial Innovus global placement wirelength force (.lib)"
        },
        9: {
            "name": "DOWN_GLOBAL",
            "paper_action": "DOWN Global",
            "affected_parameters": [],
            "status": "UNAVAILABLE",
            "description": "Requires commercial Innovus global placement wirelength force (.lib)"
        },
        10: {
            "name": "INVERT_MIX",
            "paper_action": "INVERT-MIX",
            "affected_parameters": [],
            "status": "UNAVAILABLE",
            "description": "Requires commercial timing vs congestion trade-off engine"
        }
    }

    # Active action set in RL space: indices 0 to 7 (8 discrete actions)
    ACTIVE_ACTIONS = [0, 1, 2, 3, 4, 5, 6, 7]

    def __init__(self, bounds_config_path: str = "configs/phase10_parameter_space.json"):
        with open(bounds_config_path, "r") as f:
            cfg = json.load(f)

        self.param_bounds = {}
        self.param_steps = {}
        for p in cfg["parameters"]:
            self.param_bounds[p["name"]] = (p["minimum"], p["maximum"])
            self.param_steps[p["name"]] = p["step"]

        self.num_actions = len(self.ACTIVE_ACTIONS) # 8 active actions

    def apply_action(self, action_id: int, current_params: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Executes action transition deterministically.
        Returns:
            (new_params, is_valid_transition)
        """
        if action_id not in self.ACTIONS:
            raise ValueError(f"Unknown action_id: {action_id}")

        act_info = self.ACTIONS[action_id]
        if act_info["status"] != "VERIFIED":
            # Reject execution of unavailable actions
            return copy.deepcopy(current_params), False

        st = copy.deepcopy(current_params)

        if action_id == 0: # FLIP_BOOLEANS
            st["disallow_one_site_gaps"] = not st.get("disallow_one_site_gaps", False)
            st["use_diamond_legalizer"] = not st.get("use_diamond_legalizer", False)
            st["disable_window_extension"] = not st.get("disable_window_extension", False)

        elif action_id == 1: # UP_INTEGERS
            st["max_displacement"] = min(st.get("max_displacement", 0) + 10, self.param_bounds["max_displacement"][1])
            st["site_search_window"] = min(st.get("site_search_window", 0) + 10, self.param_bounds["site_search_window"][1])
            st["row_search_window"] = min(st.get("row_search_window", 0) + 2, self.param_bounds["row_search_window"][1])

        elif action_id == 2: # DOWN_INTEGERS
            st["max_displacement"] = max(st.get("max_displacement", 0) - 10, self.param_bounds["max_displacement"][0])
            st["site_search_window"] = max(st.get("site_search_window", 0) - 10, self.param_bounds["site_search_window"][0])
            st["row_search_window"] = max(st.get("row_search_window", 0) - 2, self.param_bounds["row_search_window"][0])

        elif action_id == 3: # UP_EFFORTS
            st["row_search_window"] = min(st.get("row_search_window", 0) + 2, self.param_bounds["row_search_window"][1])
            st["site_search_window"] = min(st.get("site_search_window", 0) + 10, self.param_bounds["site_search_window"][1])

        elif action_id == 4: # DOWN_EFFORTS
            st["row_search_window"] = max(st.get("row_search_window", 0) - 2, self.param_bounds["row_search_window"][0])
            st["site_search_window"] = max(st.get("site_search_window", 0) - 10, self.param_bounds["site_search_window"][0])

        elif action_id == 5: # UP_DETAILED
            st["max_displacement"] = min(st.get("max_displacement", 0) + 10, self.param_bounds["max_displacement"][1])
            st["site_search_window"] = min(st.get("site_search_window", 0) + 10, self.param_bounds["site_search_window"][1])

        elif action_id == 6: # DOWN_DETAILED
            st["max_displacement"] = max(st.get("max_displacement", 0) - 10, self.param_bounds["max_displacement"][0])
            st["site_search_window"] = max(st.get("site_search_window", 0) - 10, self.param_bounds["site_search_window"][0])

        elif action_id == 7: # DO_NOTHING
            pass

        return st, True
