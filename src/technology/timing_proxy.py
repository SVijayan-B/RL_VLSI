"""
Timing Proxy and Surrogate Criticality Evaluation Module for CircuitNet N28.

IMPORTANT SCIENTIFIC NOTICE:
CircuitNet N28 does not provide foundry sign-off Liberty (.lib), SDC timing constraints,
or SPEF parasitic corner files. The quantities computed here are strictly ANALYTICAL
TIMING PROXIES designed for relative placement ranking and RL reward shaping.
They are NOT sign-off static timing analysis (STA) results, slacks, or WNS/TNS.
"""

from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import numpy as np

from src.technology.wirelength import compute_net_hpwl
from src.technology.rc_proxy import RCProxy28nm


class TimingProxyEngine:
    """
    Evaluates net delays, topological depths, path delay proxies, and criticality scores
    from CircuitNet layout and graph data using analytical normalized RC parameters.
    """

    def __init__(
        self,
        rc_proxy: Optional[RCProxy28nm] = None,
        r_unit: float = 0.25,        # Ohm / um
        c_unit: float = 0.18e-15,    # Farad / um (0.18 fF / um)
        c_gate: float = 0.5e-15,     # Farad (0.5 fF)
        r_driver: float = 450.0      # Ohm
    ):
        if rc_proxy is not None:
            self.rc_proxy = rc_proxy
        else:
            self.rc_proxy = RCProxy28nm(
                r_unit=r_unit,
                c_unit=c_unit,
                c_gate_default=c_gate,
                r_driver_default=r_driver
            )

    def compute_net_delay(
        self,
        wirelength_um: float,
        fanout: int = 1
    ) -> float:
        """
        Computes the Elmore net delay proxy in picoseconds (ps).

        Equation:
            T_net = R_driver * (C_wire + N_sinks * C_sink) + 0.5 * R_wire * C_wire + R_wire * (N_sinks * C_sink)
        """
        w_safe = max(0.0, float(wirelength_um))
        f_safe = max(1, int(fanout))
        return self.rc_proxy.compute_elmore_wire_delay(w_safe, num_sinks=f_safe)

    def compute_batch_net_delays(
        self,
        wirelengths_um: np.ndarray,
        fanouts: np.ndarray
    ) -> np.ndarray:
        """
        Vectorized computation of net delay proxies in picoseconds (ps).
        """
        return self.rc_proxy.compute_batch_delays(wirelengths_um, fanouts)

    def compute_topological_depths(
        self,
        num_cells: int,
        num_nets: int,
        edge_index_bipartite: np.ndarray
    ) -> np.ndarray:
        """
        Computes topological graph depth proxy via directed cell->net->cell acyclic ordering.
        To ensure deterministic, cycle-free evaluation without Liberty pin timing directions,
        this computes the longest topological level from primary inputs / leaf cells.

        Args:
            num_cells: Number of standard cells
            num_nets: Number of nets
            edge_index_bipartite: Array of shape (2, E) where [0] is cell_idx and [1] is net_idx

        Returns:
            Array of shape (num_cells,) containing topological depth (integer level >= 1).
        """
        # Build cell adjacency through nets with bounded fanout to prevent clock explosion
        net_to_cells = [[] for _ in range(num_nets)]
        for i in range(edge_index_bipartite.shape[1]):
            c = int(edge_index_bipartite[0, i])
            n = int(edge_index_bipartite[1, i])
            net_to_cells[n].append(c)

        # In-degree tracking
        cell_levels = np.ones(num_cells, dtype=np.int32)
        
        # Approximate topological leveling: for nets with fanout <= 30
        for n, cells in enumerate(net_to_cells):
            if 2 <= len(cells) <= 30:
                driver = cells[0]
                d_lvl = cell_levels[driver]
                for sink in cells[1:]:
                    if cell_levels[sink] < d_lvl + 1:
                        cell_levels[sink] = d_lvl + 1

        return cell_levels

    def compute_path_delay_proxies(
        self,
        num_cells: int,
        net_to_cells: List[List[int]],
        net_delays_ps: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """
        Propagates net delay proxies along topological connections to construct path delay proxies.

        Args:
            num_cells: Number of cells
            net_to_cells: Mapping from net index to list of connected cell indices
            net_delays_ps: Array of net delay proxies in ps

        Returns:
            Tuple of (cell_arrival_proxy_ps, max_observed_path_delay_proxy_ps)
        """
        cell_arrival_ps = np.zeros(num_cells, dtype=np.float64)

        for n_idx, cells in enumerate(net_to_cells):
            if len(cells) >= 2:
                driver = cells[0]
                delay = float(net_delays_ps[n_idx])
                arr_driver = cell_arrival_ps[driver]
                for sink in cells[1:]:
                    if arr_driver + delay > cell_arrival_ps[sink]:
                        cell_arrival_ps[sink] = arr_driver + delay

        max_path_delay = float(np.max(cell_arrival_ps)) if len(cell_arrival_ps) > 0 else 0.0
        return cell_arrival_ps, max_path_delay

    def compute_criticality_scores(
        self,
        net_delays_ps: np.ndarray,
        fanouts: np.ndarray
    ) -> np.ndarray:
        """
        Computes deterministic net criticality proxy scores normalized in [0, 1].

        Criticality is defined as:
            score = 0.7 * (delay_proxy / max_delay) + 0.3 * (fanout / max_fanout)
        """
        if len(net_delays_ps) == 0:
            return np.array([], dtype=np.float64)

        max_d = np.max(net_delays_ps)
        max_f = np.max(fanouts)

        norm_d = (net_delays_ps / max_d) if max_d > 0 else np.zeros_like(net_delays_ps)
        norm_f = (fanouts.astype(np.float64) / max_f) if max_f > 0 else np.zeros_like(net_delays_ps)

        criticality = 0.7 * norm_d + 0.3 * norm_f
        return np.clip(criticality, 0.0, 1.0)
