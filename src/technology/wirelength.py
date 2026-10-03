"""
Wirelength computation module for CircuitNet N28 placement optimization.
Implements exact and deterministic Half-Perimeter Wirelength (HPWL),
bounding box dimensions, and net degree metrics.
"""

from typing import Dict, List, Tuple, Optional, Union
import numpy as np


def compute_net_hpwl(
    pin_coords: np.ndarray,
    dbu_to_micron: float = 0.0005
) -> float:
    """
    Computes the Half-Perimeter Wirelength (HPWL) for a set of pin coordinates.

    Args:
        pin_coords: Array of shape (N, 2) containing (x, y) coordinates of net pins.
        dbu_to_micron: Scale factor to convert database units to microns (default 1/2000 = 0.0005).

    Returns:
        HPWL in microns. Returns 0.0 if fewer than 2 pins.
    """
    if pin_coords is None or len(pin_coords) < 2:
        return 0.0

    min_x = np.min(pin_coords[:, 0])
    max_x = np.max(pin_coords[:, 0])
    min_y = np.min(pin_coords[:, 1])
    max_y = np.max(pin_coords[:, 1])

    delta_x = max(0.0, float(max_x - min_x))
    delta_y = max(0.0, float(max_y - min_y))

    return (delta_x + delta_y) * dbu_to_micron


def compute_net_bbox(
    pin_coords: np.ndarray,
    dbu_to_micron: float = 0.0005
) -> Tuple[float, float, float]:
    """
    Computes delta_x, delta_y, and bbox area for a net.

    Args:
        pin_coords: Array of shape (N, 2) of (x, y) coordinates.
        dbu_to_micron: Scale factor.

    Returns:
        Tuple of (delta_x_um, delta_y_um, bbox_area_um2).
    """
    if pin_coords is None or len(pin_coords) < 2:
        return (0.0, 0.0, 0.0)

    min_x = np.min(pin_coords[:, 0])
    max_x = np.max(pin_coords[:, 0])
    min_y = np.min(pin_coords[:, 1])
    max_y = np.max(pin_coords[:, 1])

    dx = max(0.0, float(max_x - min_x)) * dbu_to_micron
    dy = max(0.0, float(max_y - min_y)) * dbu_to_micron
    area = dx * dy

    return (dx, dy, area)


def compute_total_hpwl(
    net_pin_map: Dict[str, np.ndarray],
    weights: Optional[Dict[str, float]] = None,
    dbu_to_micron: float = 0.0005
) -> float:
    """
    Computes total HPWL across all nets in the design.

    Args:
        net_pin_map: Dictionary mapping net_name to (N, 2) pin coordinates.
        weights: Optional dictionary mapping net_name to criticality/timing weight (default 1.0).
        dbu_to_micron: Scale factor.

    Returns:
        Total HPWL in microns.
    """
    total = 0.0
    for net_name, coords in net_pin_map.items():
        w = weights.get(net_name, 1.0) if weights else 1.0
        hpwl = compute_net_hpwl(coords, dbu_to_micron=dbu_to_micron)
        total += w * hpwl
    return total


def compute_hpwl_from_positions(
    positions: np.ndarray,
    hyperedges: List[List[int]],
    dbu_to_micron: float = 0.0005
) -> Tuple[float, np.ndarray]:
    """
    Computes HPWL directly from node positions and hyperedge list (cell-level).

    Args:
        positions: Array of shape (num_nodes, 2) representing cell positions.
        hyperedges: List of node index lists, each representing a net connecting those nodes.
        dbu_to_micron: Scale factor.

    Returns:
        Tuple of (total_hpwl_um, array_of_per_net_hpwl_um).
    """
    per_net = np.zeros(len(hyperedges), dtype=np.float64)

    for i, edge in enumerate(hyperedges):
        if len(edge) < 2:
            continue
        coords = positions[edge]
        min_x = np.min(coords[:, 0])
        max_x = np.max(coords[:, 0])
        min_y = np.min(coords[:, 1])
        max_y = np.max(coords[:, 1])
        per_net[i] = ((max_x - min_x) + (max_y - min_y)) * dbu_to_micron

    return float(np.sum(per_net)), per_net
