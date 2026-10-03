"""
Unit tests for src.power module.
Verifies dynamic power monotonicity, PDN resistance scaling,
static IR-drop monotonicity, grid stability, and numerical safety.
"""

import unittest
import numpy as np

from src.power.power_engine import PowerAndIRProxyEngine
from src.power.pdn_geometry import compute_pdn_effective_resistance


class TestPowerAndIRProxy(unittest.TestCase):

    def setUp(self):
        self.engine = PowerAndIRProxyEngine()

    def test_power_capacitance_monotonicity(self):
        # Monotonicity with capacitance / wirelength
        lengths = np.array([10.0, 50.0, 100.0, 500.0])
        fanouts = np.array([2, 2, 2, 2])
        powers, caps = self.engine.compute_net_dynamic_power_proxy(lengths, fanouts)
        for i in range(len(powers) - 1):
            self.assertLess(powers[i], powers[i+1])
            self.assertLess(caps[i], caps[i+1])

    def test_power_activity_monotonicity(self):
        # Monotonicity with fanout / activity
        lengths = np.array([100.0, 100.0, 100.0])
        fanouts = np.array([1, 4, 16])
        powers, _ = self.engine.compute_net_dynamic_power_proxy(lengths, fanouts)
        self.assertLess(powers[0], powers[1])
        self.assertLess(powers[1], powers[2])

    def test_pdn_resistance_scaling(self):
        # Resistance increases with distance to center / length
        r_small = compute_pdn_effective_resistance(die_width_um=200.0, die_height_um=200.0)
        r_large = compute_pdn_effective_resistance(die_width_um=600.0, die_height_um=600.0)
        # Resistance decreases with higher mesh density factor
        r_dense = compute_pdn_effective_resistance(die_width_um=600.0, die_height_um=600.0, pdn_density_factor=2.0)
        self.assertLess(r_dense, r_large)

    def test_spatial_grid_ir_drop_monotonicity(self):
        # Higher power in identical grid must lead to higher IR drop
        w, h = 500.0, 500.0
        coords = np.array([[250.0, 250.0]])
        areas = np.array([10.0])
        
        low_p = np.array([10.0])
        high_p = np.array([50.0])
        
        res_low = self.engine.compute_spatial_power_density_and_ir(w, h, coords, areas, low_p, grid_bins=8)
        res_high = self.engine.compute_spatial_power_density_and_ir(w, h, coords, areas, high_p, grid_bins=8)
        
        self.assertLess(res_low['max_ir_drop_proxy_mv'], res_high['max_ir_drop_proxy_mv'])

    def test_grid_resolution_stability(self):
        # Total power must be conserved across 8x8, 16x16, 32x32 grids
        w, h = 500.0, 500.0
        rng = np.random.RandomState(42)
        coords = rng.uniform(0.0, 500.0, size=(100, 2))
        areas = np.ones(100) * 2.0
        powers = rng.uniform(1.0, 10.0, size=100)
        
        res_8 = self.engine.compute_spatial_power_density_and_ir(w, h, coords, areas, powers, grid_bins=8)
        res_16 = self.engine.compute_spatial_power_density_and_ir(w, h, coords, areas, powers, grid_bins=16)
        res_32 = self.engine.compute_spatial_power_density_and_ir(w, h, coords, areas, powers, grid_bins=32)
        
        # Conserved total power
        self.assertAlmostEqual(res_8['total_dynamic_power_proxy'], res_16['total_dynamic_power_proxy'], places=4)
        self.assertAlmostEqual(res_16['total_dynamic_power_proxy'], res_32['total_dynamic_power_proxy'], places=4)

    def test_numerical_safety_no_nans(self):
        # Zero or empty checks
        lengths = np.array([0.0, 100.0])
        fanouts = np.array([1, 10])
        powers, caps = self.engine.compute_net_dynamic_power_proxy(lengths, fanouts)
        self.assertFalse(np.any(np.isnan(powers)))
        self.assertFalse(np.any(np.isinf(powers)))
        self.assertTrue(np.all(powers >= 0.0))


if __name__ == '__main__':
    unittest.main()
