"""
Unit tests for src.technology.timing_proxy module.
Verifies monotonicity, batch calculation, path aggregation, criticality,
and numerical safety.
"""

import unittest
import numpy as np

from src.technology.timing_proxy import TimingProxyEngine
from src.technology.rc_proxy import RCProxy28nm


class TestTimingProxyEngine(unittest.TestCase):

    def setUp(self):
        self.engine = TimingProxyEngine()

    def test_wirelength_monotonicity(self):
        # Test A: same fanout, increasing wirelength -> delay must not decrease
        d1 = self.engine.compute_net_delay(wirelength_um=10.0, fanout=2)
        d2 = self.engine.compute_net_delay(wirelength_um=50.0, fanout=2)
        d3 = self.engine.compute_net_delay(wirelength_um=200.0, fanout=2)
        self.assertLess(d1, d2)
        self.assertLess(d2, d3)

    def test_fanout_monotonicity(self):
        # Test B: same wirelength, increasing fanout -> delay must not decrease
        d1 = self.engine.compute_net_delay(wirelength_um=100.0, fanout=1)
        d2 = self.engine.compute_net_delay(wirelength_um=100.0, fanout=4)
        d3 = self.engine.compute_net_delay(wirelength_um=100.0, fanout=16)
        self.assertLess(d1, d2)
        self.assertLess(d2, d3)

    def test_zero_and_negative_wirelength(self):
        # Zero or negative length nets have 0 wire delay proxy
        d_zero = self.engine.compute_net_delay(wirelength_um=0.0, fanout=1)
        d_neg = self.engine.compute_net_delay(wirelength_um=-10.0, fanout=1)
        self.assertEqual(d_zero, 0.0)
        self.assertEqual(d_neg, 0.0)

    def test_batch_calculation_consistency(self):
        lengths = np.array([10.0, 50.0, 100.0])
        fanouts = np.array([1, 2, 4])
        batch_delays = self.engine.compute_batch_net_delays(lengths, fanouts)
        for i in range(len(lengths)):
            single = self.engine.compute_net_delay(lengths[i], fanouts[i])
            self.assertAlmostEqual(batch_delays[i], single, places=4)

    def test_path_delay_propagation(self):
        # 3 cells: 0 -> net0 -> 1 -> net1 -> 2
        net_to_cells = [[0, 1], [1, 2]]
        delays = np.array([10.0, 25.0])
        arrivals, max_path = self.engine.compute_path_delay_proxies(3, net_to_cells, delays)
        self.assertAlmostEqual(arrivals[0], 0.0, places=4)
        self.assertAlmostEqual(arrivals[1], 10.0, places=4)
        self.assertAlmostEqual(arrivals[2], 35.0, places=4)
        self.assertAlmostEqual(max_path, 35.0, places=4)

    def test_criticality_scores(self):
        delays = np.array([10.0, 50.0, 100.0])
        fanouts = np.array([1, 5, 10])
        crit = self.engine.compute_criticality_scores(delays, fanouts)
        self.assertEqual(len(crit), 3)
        self.assertTrue(np.all(crit >= 0.0))
        self.assertTrue(np.all(crit <= 1.0))
        # Max delay and max fanout net must have maximum criticality (1.0)
        self.assertAlmostEqual(crit[2], 1.0, places=4)
        self.assertLess(crit[0], crit[1])
        self.assertLess(crit[1], crit[2])

    def test_numerical_safety(self):
        delays = np.array([0.0, 1000.0, 50000.0])
        fanouts = np.array([1, 100, 1000])
        crit = self.engine.compute_criticality_scores(delays, fanouts)
        self.assertFalse(np.any(np.isnan(crit)))
        self.assertFalse(np.any(np.isinf(crit)))


if __name__ == '__main__':
    unittest.main()
