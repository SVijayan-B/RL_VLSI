import unittest
from src.placement.phase7_action_space import Phase7ActionSpace

class TestPhase7ActionSpace(unittest.TestCase):
    def setUp(self):
        self.env = Phase7ActionSpace()

    def test_01_boolean_flip(self):
        st0 = self.env.get_state()
        self.assertFalse(st0["disallow_one_site_gaps"])
        self.assertFalse(st0["use_diamond_legalizer"])
        self.assertFalse(st0["disable_window_extension"])
        
        st1, reset = self.env.apply_action(1) # FLIP Booleans
        self.assertFalse(reset)
        self.assertTrue(st1["disallow_one_site_gaps"])
        self.assertTrue(st1["use_diamond_legalizer"])
        self.assertTrue(st1["disable_window_extension"])

        st2, reset = self.env.apply_action(1) # FLIP back
        self.assertFalse(reset)
        self.assertFalse(st2["disallow_one_site_gaps"])
        self.assertFalse(st2["use_diamond_legalizer"])
        self.assertFalse(st2["disable_window_extension"])

    def test_02_up_integers(self):
        st1, reset = self.env.apply_action(2) # UP Integers
        self.assertFalse(reset)
        self.assertEqual(st1["max_displacement"], 10)
        self.assertEqual(st1["site_search_window"], 10)
        self.assertEqual(st1["row_search_window"], 2)

    def test_03_down_integers_bounded(self):
        # Already at 0, should not go negative
        st1, reset = self.env.apply_action(3) # DOWN Integers
        self.assertFalse(reset)
        self.assertEqual(st1["max_displacement"], 0)
        self.assertEqual(st1["site_search_window"], 0)
        self.assertEqual(st1["row_search_window"], 0)

    def test_04_numeric_upper_bound(self):
        # Apply UP 15 times to hit caps
        for _ in range(15):
            self.env.apply_action(2)
        st = self.env.get_state()
        self.assertEqual(st["max_displacement"], 100)
        self.assertEqual(st["site_search_window"], 100)
        self.assertEqual(st["row_search_window"], 20)

    def test_05_efforts_up_and_down(self):
        self.env.reset_to_baseline()
        st1, _ = self.env.apply_action(4) # UP Efforts
        self.assertEqual(st1["row_search_window"], 2)
        self.assertEqual(st1["site_search_window"], 10)
        self.assertEqual(st1["max_displacement"], 0) # Unchanged!

        st2, _ = self.env.apply_action(5) # DOWN Efforts
        self.assertEqual(st2["row_search_window"], 0)
        self.assertEqual(st2["site_search_window"], 0)

    def test_06_state_immutability_for_unrelated_params(self):
        self.env.reset_to_baseline()
        # Action 6 only changes max_displacement and site_search_window
        st1, _ = self.env.apply_action(6)
        self.assertEqual(st1["max_displacement"], 10)
        self.assertEqual(st1["site_search_window"], 10)
        self.assertEqual(st1["row_search_window"], 0)
        self.assertFalse(st1["disallow_one_site_gaps"])
        self.assertFalse(st1["use_diamond_legalizer"])
        self.assertFalse(st1["disable_window_extension"])

    def test_07_unavailable_actions_preserve_identity(self):
        self.env.reset_to_baseline()
        # Action 8: UP Global (UNAVAILABLE in DPL)
        st1, reset = self.env.apply_action(8)
        self.assertFalse(reset)
        self.assertEqual(st1, self.env.baseline_config["parameters"])
        self.assertEqual(self.env.get_action_status(8), "UNAVAILABLE")

        # Action 9: DOWN Global (UNAVAILABLE in DPL)
        st2, reset = self.env.apply_action(9)
        self.assertFalse(reset)
        self.assertEqual(st2, self.env.baseline_config["parameters"])
        self.assertEqual(self.env.get_action_status(9), "UNAVAILABLE")

        # Action 10: INVERT-MIX (UNAVAILABLE in DPL)
        st3, reset = self.env.apply_action(10)
        self.assertFalse(reset)
        self.assertEqual(st3, self.env.baseline_config["parameters"])
        self.assertEqual(self.env.get_action_status(10), "UNAVAILABLE")

    def test_08_reset_behavior_5_consecutive_nothings(self):
        self.env.reset_to_baseline()
        self.env.set_state({"max_displacement": 50, "disallow_one_site_gaps": True})
        
        # 4 DO NOTHINGS
        for i in range(4):
            st, reset = self.env.apply_action(11)
            self.assertFalse(reset)
            self.assertEqual(st["max_displacement"], 50)
            
        # 5th DO NOTHING triggers reset!
        st, reset = self.env.apply_action(11)
        self.assertTrue(reset)
        self.assertEqual(st["max_displacement"], 0)
        self.assertFalse(st["disallow_one_site_gaps"])

    def test_09_action_determinism(self):
        env1 = Phase7ActionSpace()
        env2 = Phase7ActionSpace()
        for a in [2, 1, 4, 10, 8, 3]:
            s1, _ = env1.apply_action(a)
            s2, _ = env2.apply_action(a)
            self.assertEqual(s1, s2)

    def test_10_openroad_args_generation(self):
        self.env.reset_to_baseline()
        self.assertEqual(self.env.to_openroad_args(), "")
        self.env.set_state({
            "max_displacement": 20,
            "disallow_one_site_gaps": True,
            "use_diamond_legalizer": True
        })
        args = self.env.to_openroad_args()
        self.assertIn("-max_displacement 20", args)
        self.assertIn("-disallow_one_site_gaps", args)
        self.assertIn("-use_diamond_legalizer", args)

    def test_11_invalid_action_rejection(self):
        with self.assertRaises(ValueError):
            self.env.apply_action(0)
        with self.assertRaises(ValueError):
            self.env.apply_action(12)

    def test_12_baseline_configuration_validity(self):
        st = self.env.reset_to_baseline()
        self.assertEqual(st["max_displacement"], 0)
        self.assertFalse(st["disallow_one_site_gaps"])
        self.assertEqual(st["site_search_window"], 0)
        self.assertEqual(st["row_search_window"], 0)
        self.assertFalse(st["use_diamond_legalizer"])
        self.assertFalse(st["disable_window_extension"])

if __name__ == "__main__":
    unittest.main()
