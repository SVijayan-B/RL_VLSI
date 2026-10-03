import copy
import json
import os

class Phase7ActionSpace:
    """
    OpenROAD Placement Parameter Optimization Action Space.
    Adapts Agnesina et al. (IEEE TCAD 2023) Table III into OpenROAD controls.
    Explicitly categorizes actions by implementation and availability status.
    """
    ACTION_NAMES = {
        1: "FLIP Booleans",
        2: "UP Integers",
        3: "DOWN Integers",
        4: "UP Efforts",
        5: "DOWN Efforts",
        6: "UP Detailed",
        7: "DOWN Detailed",
        8: "UP Global",
        9: "DOWN Global",
        10: "INVERT-MIX",
        11: "DO NOTHING"
    }

    ACTION_STATUS = {
        1: "VERIFIED",
        2: "VERIFIED",
        3: "VERIFIED",
        4: "PARTIALLY_VERIFIED",
        5: "PARTIALLY_VERIFIED",
        6: "VERIFIED",
        7: "VERIFIED",
        8: "UNAVAILABLE",
        9: "UNAVAILABLE",
        10: "UNAVAILABLE",
        11: "VERIFIED"
    }

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = "/home/b_siddarth_vijayan/CircuitNet_28nm/configs/phase_07/baseline_placement.json"
        
        with open(config_path, "r") as f:
            self.baseline_config = json.load(f)
            
        self.param_metadata = self.baseline_config.get("parameter_metadata", {})
        self.current_state = copy.deepcopy(self.baseline_config.get("parameters", {}))
        self.consecutive_nothing_count = 0
        self.reset_count = 0

    def get_state(self):
        return copy.deepcopy(self.current_state)

    def set_state(self, state):
        for k, v in state.items():
            if k in self.current_state:
                self.current_state[k] = v

    def reset_to_baseline(self):
        self.current_state = copy.deepcopy(self.baseline_config.get("parameters", {}))
        self.consecutive_nothing_count = 0
        self.reset_count += 1
        return copy.deepcopy(self.current_state)

    def get_action_status(self, action_id):
        if action_id not in self.ACTION_STATUS:
            raise ValueError(f"Invalid action_id: {action_id}. Expected 1-11.")
        return self.ACTION_STATUS[action_id]

    def apply_action(self, action_id):
        """
        Applies one of the 11 actions according to Agnesina et al. Table III rules:
        1: FLIP Booleans (VERIFIED in OpenROAD)
        2: UP Integers (VERIFIED in OpenROAD)
        3: DOWN Integers (VERIFIED in OpenROAD)
        4: UP Efforts (PARTIALLY_VERIFIED: DPL search window analog)
        5: DOWN Efforts (PARTIALLY_VERIFIED: DPL search window analog)
        6: UP Detailed (VERIFIED in OpenROAD)
        7: DOWN Detailed (VERIFIED in OpenROAD)
        8: UP Global (UNAVAILABLE: Innovus global group requires .lib)
        9: DOWN Global (UNAVAILABLE: Innovus global group requires .lib)
        10: INVERT-MIX (UNAVAILABLE: Timing vs congestion vs WL trade-off requires .lib)
        11: DO NOTHING (VERIFIED: triggers reset if picked 5 times consecutively)
        """
        if action_id != 11:
            self.consecutive_nothing_count = 0

        st = self.current_state

        if action_id == 1: # FLIP Booleans
            st["disallow_one_site_gaps"] = not st["disallow_one_site_gaps"]
            st["use_diamond_legalizer"] = not st["use_diamond_legalizer"]
            st["disable_window_extension"] = not st["disable_window_extension"]

        elif action_id == 2: # UP Integers (bounded transformation)
            st["max_displacement"] = min(st["max_displacement"] + 10, 100)
            st["site_search_window"] = min(st["site_search_window"] + 10, 100)
            st["row_search_window"] = min(st["row_search_window"] + 2, 20)

        elif action_id == 3: # DOWN Integers (bounded transformation)
            st["max_displacement"] = max(st["max_displacement"] - 10, 0)
            st["site_search_window"] = max(st["site_search_window"] - 10, 0)
            st["row_search_window"] = max(st["row_search_window"] - 2, 0)

        elif action_id == 4: # UP Efforts (search window analog)
            st["row_search_window"] = min(st["row_search_window"] + 2, 20)
            st["site_search_window"] = min(st["site_search_window"] + 10, 100)

        elif action_id == 5: # DOWN Efforts (search window analog)
            st["row_search_window"] = max(st["row_search_window"] - 2, 0)
            st["site_search_window"] = max(st["site_search_window"] - 10, 0)

        elif action_id == 6: # UP Detailed
            st["max_displacement"] = min(st["max_displacement"] + 10, 100)
            st["site_search_window"] = min(st["site_search_window"] + 10, 100)

        elif action_id == 7: # DOWN Detailed
            st["max_displacement"] = max(st["max_displacement"] - 10, 0)
            st["site_search_window"] = max(st["site_search_window"] - 10, 0)

        elif action_id == 8: # UP Global (UNAVAILABLE in OpenROAD DPL flow)
            # Preserves paper action identity without modifying unrelated DPL parameters
            pass

        elif action_id == 9: # DOWN Global (UNAVAILABLE in OpenROAD DPL flow)
            # Preserves paper action identity without modifying unrelated DPL parameters
            pass

        elif action_id == 10: # INVERT-MIX (UNAVAILABLE in OpenROAD DPL flow)
            # Preserves paper action identity without modifying unrelated DPL parameters
            pass

        elif action_id == 11: # DO NOTHING
            self.consecutive_nothing_count += 1
            if self.consecutive_nothing_count >= 5:
                # Equation 24: reset when {a_{j-4}...a_j} == NOTHING
                self.reset_to_baseline()
                return copy.deepcopy(self.current_state), True # reset triggered

        else:
            raise ValueError(f"Invalid action_id: {action_id}. Expected 1-11.")

        return copy.deepcopy(self.current_state), False

    def to_openroad_args(self, state=None):
        if state is None:
            state = self.current_state
        args = []
        if state.get("max_displacement", 0) > 0:
            args.append(f"-max_displacement {state['max_displacement']}")
        if state.get("site_search_window", 0) > 0:
            args.append(f"-site_search_window {state['site_search_window']}")
        if state.get("row_search_window", 0) > 0:
            args.append(f"-row_search_window {state['row_search_window']}")
        if state.get("disallow_one_site_gaps", False):
            args.append("-disallow_one_site_gaps")
        if state.get("use_diamond_legalizer", False):
            args.append("-use_diamond_legalizer")
        if state.get("disable_window_extension", False):
            args.append("-disable_window_extension")
        return " ".join(args)
