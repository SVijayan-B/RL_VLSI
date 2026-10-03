"""
RC Proxy and Interconnect Delay Modeling Module for CircuitNet N28.

This module provides PROXY models for interconnect resistance, capacitance,
and wire delay estimation when sign-off Liberty (.lib) and SPEF parasitics are unavailable.

IMPORTANT:
These are defensible geometric proxy models designed for relative ranking and
RL reward shaping. They DO NOT claim to represent proprietary TSMC 28nm foundry sign-off timing.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np


class RCProxy28nm:
    """
    Interconnect RC and delay proxy calibrated for ~28nm typical metal stack.

    Reference 28nm typical intermediate metal layer parameters:
    - Unit wire resistance: ~0.25 Ohm / um (intermediate pitch M2-M4 typical)
    - Unit wire capacitance: ~0.18 fF / um (including area + fringing typical)
    - Gate input capacitance proxy: ~0.50 fF (nominal unit inverter)
    - Gate driving resistance proxy: ~450.0 Ohm (nominal unit inverter)
    """

    def __init__(
        self,
        r_unit: float = 0.25,        # Ohm / um
        c_unit: float = 0.18e-15,    # Farad / um (0.18 fF / um)
        c_gate_default: float = 0.5e-15,  # Farad (0.5 fF)
        r_driver_default: float = 450.0   # Ohm
    ):
        self.r_unit = r_unit
        self.c_unit = c_unit
        self.c_gate_default = c_gate_default
        self.r_driver_default = r_driver_default

    def compute_wire_parasitics(
        self,
        wirelength_um: float
    ) -> Tuple[float, float]:
        """
        Computes total wire resistance (Ohms) and total wire capacitance (Farads).

        Args:
            wirelength_um: Estimated Manhattan wirelength in microns.

        Returns:
            Tuple of (R_wire_ohms, C_wire_farads).
        """
        r_wire = max(0.0, wirelength_um) * self.r_unit
        c_wire = max(0.0, wirelength_um) * self.c_unit
        return r_wire, c_wire

    def compute_elmore_wire_delay(
        self,
        wirelength_um: float,
        num_sinks: int = 1,
        driver_res: Optional[float] = None,
        sink_cap: Optional[float] = None
    ) -> float:
        """
        Computes the Elmore wire delay proxy in picoseconds (ps).

        Approximation using lumped Pi-model / standard star topology:
        T_delay = R_driver * (C_wire + N_sinks * C_sink) + 0.5 * R_wire * C_wire + R_wire * (N_sinks * C_sink)

        Args:
            wirelength_um: Manhattan wirelength in microns.
            num_sinks: Fanout / number of sink pins driven by this net.
            driver_res: Output resistance of driver gate (Ohm). Defaults to r_driver_default.
            sink_cap: Load capacitance per sink pin (Farad). Defaults to c_gate_default.

        Returns:
            Delay proxy in picoseconds (ps).
        """
        if wirelength_um <= 0.0 or num_sinks < 1:
            return 0.0

        r_d = driver_res if driver_res is not None else self.r_driver_default
        c_s = sink_cap if sink_cap is not None else self.c_gate_default

        r_w, c_w = self.compute_wire_parasitics(wirelength_um)
        total_sink_c = num_sinks * c_s

        # Elmore delay in seconds
        # 1. Driver resistance charging wire cap and sink caps
        term_driver = r_d * (c_w + total_sink_c)
        # 2. Wire resistance charging its own distributed cap (0.5 factor for distributed line)
        term_wire_self = 0.5 * r_w * c_w
        # 3. Wire resistance charging downstream sink caps (lumped at end of wire proxy)
        term_wire_load = r_w * total_sink_c

        delay_seconds = term_driver + term_wire_self + term_wire_load
        return delay_seconds * 1e12  # convert to picoseconds (ps)

    def compute_batch_delays(
        self,
        wirelengths_um: np.ndarray,
        fanouts: np.ndarray
    ) -> np.ndarray:
        """
        Computes Elmore delay proxies in picoseconds for an array of nets.

        Args:
            wirelengths_um: Array of wirelengths in microns.
            fanouts: Array of sink counts.

        Returns:
            Array of delay proxies in picoseconds (ps).
        """
        w_safe = np.maximum(0.0, wirelengths_um)
        f_safe = np.maximum(1, fanouts)

        r_w = w_safe * self.r_unit
        c_w = w_safe * self.c_unit
        total_sink_c = f_safe * self.c_gate_default

        term_driver = self.r_driver_default * (c_w + total_sink_c)
        term_wire_self = 0.5 * r_w * c_w
        term_wire_load = r_w * total_sink_c

        delays_ps = (term_driver + term_wire_self + term_wire_load) * 1e12
        return delays_ps
