"""
Unit tests for src.technology wirelength and rc_proxy modules.
"""

import unittest
import numpy as np
from src.technology.wirelength import (
    compute_net_hpwl,
    compute_net_bbox,
    compute_total_hpwl,
    compute_hpwl_from_positions
)
from src.technology.rc_proxy import RCProxy28nm


class TestTechnologyModeling(unittest.TestCase):

    def test_single_pin_hpwl(self):
        # Degenerate net with 1 pin has 0 wirelength
        pins = np.array([[1000.0, 2000.0]])
        self.assertEqual(compute_net_hpwl(pins), 0.0)

    def test_two_pin_hpwl(self):
        # Points at (0, 0) and (2000, 4000) DBU
        # With 2000 DBU/um: dx = 1.0 um, dy = 2.0 um -> HPWL = 3.0 um
        pins = np.array([[0.0, 0.0], [2000.0, 4000.0]])
        hpwl = compute_net_hpwl(pins, dbu_to_micron=0.0005)
        self.assertAlmostEqual(hpwl, 3.0, places=5)

    def test_bbox_calculation(self):
        pins = np.array([[1000.0, 1000.0], [3000.0, 5000.0]])
        # dx = (3000 - 1000)*0.0005 = 1.0 um
        # dy = (5000 - 1000)*0.0005 = 2.0 um
        # area = 2.0 um^2
        dx, dy, area = compute_net_bbox(pins, dbu_to_micron=0.0005)
        self.assertAlmostEqual(dx, 1.0, places=5)
        self.assertAlmostEqual(dy, 2.0, places=5)
        self.assertAlmostEqual(area, 2.0, places=5)

    def test_positions_and_hyperedges(self):
        positions = np.array([
            [0.0, 0.0],       # node 0
            [2000.0, 0.0],    # node 1
            [2000.0, 2000.0]  # node 2
        ])
        hyperedges = [
            [0, 1],     # dx=1.0, dy=0.0 -> hpwl=1.0
            [0, 1, 2],  # dx=1.0, dy=1.0 -> hpwl=2.0
            [2]         # single node -> hpwl=0.0
        ]
        tot, per_net = compute_hpwl_from_positions(positions, hyperedges, dbu_to_micron=0.0005)
        self.assertAlmostEqual(tot, 3.0, places=5)
        self.assertAlmostEqual(per_net[0], 1.0, places=5)
        self.assertAlmostEqual(per_net[1], 2.0, places=5)
        self.assertAlmostEqual(per_net[2], 0.0, places=5)

    def test_rc_proxy_parasitics(self):
        proxy = RCProxy28nm(r_unit=0.25, c_unit=0.18e-15)
        # 100 um wire
        r, c = proxy.compute_wire_parasitics(100.0)
        self.assertAlmostEqual(r, 25.0, places=4)
        self.assertAlmostEqual(c, 18.0e-15, places=18)

    def test_elmore_delay_monotonicity(self):
        proxy = RCProxy28nm()
        d_short = proxy.compute_elmore_wire_delay(wirelength_um=10.0, num_sinks=1)
        d_long = proxy.compute_elmore_wire_delay(wirelength_um=100.0, num_sinks=1)
        d_high_fanout = proxy.compute_elmore_wire_delay(wirelength_um=100.0, num_sinks=5)

        # Longer wire must have strictly greater delay
        self.assertGreater(d_long, d_short)
        # Higher fanout must have strictly greater delay
        self.assertGreater(d_high_fanout, d_long)

    def test_batch_delays(self):
        proxy = RCProxy28nm()
        lengths = np.array([10.0, 50.0, 100.0])
        fanouts = np.array([1, 2, 4])
        delays = proxy.compute_batch_delays(lengths, fanouts)
        self.assertEqual(len(delays), 3)
        self.assertGreater(delays[1], delays[0])
        self.assertGreater(delays[2], delays[1])


if __name__ == '__main__':
    unittest.main()
