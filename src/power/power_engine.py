"""
Dynamic Power, Static Power, Power Density, and Static IR-Drop Proxy Engine.
Reuses src.technology.rc_proxy for interconnect capacitance proxies.

CRITICAL NOTICE:
Foundry sign-off power tables, VCD/SAIF switching activity, and SPEF parasitics
are absent in CircuitNet N28. All quantities computed here are strictly
ANALYTICAL NORMALIZED PROXIES for relative placement evaluation.
"""

from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import numpy as np

from src.technology.rc_proxy import RCProxy28nm


class PowerAndIRProxyEngine:
    """
    Evaluates analytical dynamic power proxies, area-normalized static power proxies,
    spatial power density grids, and static IR-drop proxies.
    """

    def __init__(
        self,
        rc_proxy: Optional[RCProxy28nm] = None,
        v_dd_norm: float = 1.0,         # Normalized supply voltage proxy
        freq_norm: float = 1.0,         # Normalized operating frequency proxy
        c_unit: float = 0.18e-15,       # Wire capacitance proxy parameter (0.18 fF/um)
        c_gate: float = 0.5e-15,        # Gate input capacitance proxy (0.5 fF)
        r_sheet_pdn: float = 0.05       # Normalized PDN sheet resistance proxy (Ohm/sq)
    ):
        self.rc_proxy = rc_proxy if rc_proxy is not None else RCProxy28nm(c_unit=c_unit, c_gate_default=c_gate)
        self.v_dd_norm = v_dd_norm
        self.freq_norm = freq_norm
        self.r_sheet_pdn = r_sheet_pdn

    def compute_switching_activity_proxy(
        self,
        fanouts: np.ndarray,
        is_clock_mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Derives a deterministic normalized switching activity proxy (alpha) from graph fanout.
        Standard baseline assumption:
        - Nominal data nets: alpha = 0.15 (typical CMOS activity factor)
        - High-fanout / global nets: alpha scales up to 0.50 (probabilistic upper bound)
        - Clock nets (if flagged): alpha = 1.0 (switches every cycle)
        """
        f_safe = np.maximum(1, fanouts)
        # Base activity with mild logarithmic scaling for fanout fan-in activity
        alpha = 0.15 + 0.10 * np.log10(np.clip(f_safe, 1, 1000))
        alpha = np.clip(alpha, 0.10, 0.60)
        
        if is_clock_mask is not None:
            alpha = np.where(is_clock_mask, 1.0, alpha)
            
        return alpha

    def compute_net_dynamic_power_proxy(
        self,
        wirelengths_um: np.ndarray,
        fanouts: np.ndarray,
        is_clock_mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes dynamic power proxy per net in normalized arbitrary power units (a.u.).
        Equation:
            C_total = C_wire + N_sinks * C_gate
            P_dynamic = alpha * C_total * V^2 * f
        Returns:
            Tuple of (per_net_power_proxy, per_net_capacitance_proxy_femtofarads)
        """
        w_safe = np.maximum(0.0, wirelengths_um)
        f_safe = np.maximum(1, fanouts)
        
        # Total load capacitance in Farads
        c_wire = w_safe * self.rc_proxy.c_unit
        c_sinks = f_safe * self.rc_proxy.c_gate_default
        c_total_f = c_wire + c_sinks
        c_total_ff = c_total_f * 1e15 # convert to fF for numerical ease
        
        alpha = self.compute_switching_activity_proxy(fanouts, is_clock_mask=is_clock_mask)
        
        # Normalized power proxy: alpha * C(fF) * V_norm^2 * f_norm
        p_dyn = alpha * c_total_ff * (self.v_dd_norm ** 2) * self.freq_norm
        return p_dyn, c_total_ff

    def compute_spatial_power_density_and_ir(
        self,
        core_width_um: float,
        core_height_um: float,
        cell_coords: np.ndarray,       # (N, 2) in um
        cell_areas: np.ndarray,        # (N,) in um^2
        cell_powers: np.ndarray,       # (N,) power proxy allocated to cell
        grid_bins: int = 16,
        pdn_mesh_setting: int = 1      # p1 to p8
    ) -> Dict[str, Any]:
        """
        Computes 2D spatial power density grid and static IR-drop proxy map.

        Args:
            core_width_um: Core die width in um
            core_height_um: Core die height in um
            cell_coords: Array of (x, y) coordinates of cells in um
            cell_areas: Array of cell areas in um^2
            cell_powers: Dynamic power proxy attributed to cell
            grid_bins: Grid resolution (e.g. 8, 16, 32)
            pdn_mesh_setting: Integer from 1 to 8 representing p-setting

        Returns:
            Dictionary containing 2D power density map, 2D IR-drop map, and statistical summaries.
        """
        w_safe = max(10.0, core_width_um)
        h_safe = max(10.0, core_height_um)
        
        bin_w = w_safe / grid_bins
        bin_h = h_safe / grid_bins
        bin_area = bin_w * bin_h
        
        power_grid = np.zeros((grid_bins, grid_bins), dtype=np.float64)
        area_grid = np.zeros((grid_bins, grid_bins), dtype=np.float64)
        
        # Bin cells
        xs = np.clip(cell_coords[:, 0], 0.0, w_safe - 1e-4)
        ys = np.clip(cell_coords[:, 1], 0.0, h_safe - 1e-4)
        
        col_indices = np.floor(xs / bin_w).astype(np.int32)
        row_indices = np.floor(ys / bin_h).astype(np.int32)
        
        for i in range(len(cell_powers)):
            r = row_indices[i]
            c = col_indices[i]
            power_grid[r, c] += cell_powers[i]
            area_grid[r, c] += cell_areas[i]
            
        power_density_grid = power_grid / bin_area
        
        # Static IR-drop proxy calculation
        # R_pdn decreases with denser p-mesh (e.g. p8 is denser than p1)
        # Empirical scaling factor for p1-p8 mesh: rho_eff = r_sheet / (1.0 + 0.15 * p)
        rho_eff = self.r_sheet_pdn / (1.0 + 0.15 * max(1, pdn_mesh_setting))
        
        ir_drop_grid = np.zeros((grid_bins, grid_bins), dtype=np.float64)
        # Power rings/pads assumed around perimeter (x=0, x=W, y=0, y=H)
        for r in range(grid_bins):
            for c in range(grid_bins):
                # distance to closest core boundary in grid steps
                dist_boundary = min(r, grid_bins - 1 - r, c, grid_bins - 1 - c) + 1
                dist_um = dist_boundary * 0.5 * (bin_w + bin_h)
                # Resistance proxy from perimeter to bin (Ohm proxy)
                r_path_proxy = rho_eff * (dist_um / max(bin_w, bin_h))
                # Current proxy proportional to local power demand (I = P / V)
                i_local_proxy = power_grid[r, c] / max(0.1, self.v_dd_norm)
                # Static IR drop proxy in millivolts (mV proxy)
                ir_drop_grid[r, c] = i_local_proxy * r_path_proxy
                
        ir_flat = ir_drop_grid.flatten()
        return {
            'grid_bins': grid_bins,
            'bin_width_um': round(bin_w, 2),
            'bin_height_um': round(bin_h, 2),
            'total_dynamic_power_proxy': float(np.sum(power_grid)),
            'mean_power_density_proxy': float(np.mean(power_density_grid)),
            'max_power_density_proxy': float(np.max(power_density_grid)),
            'mean_ir_drop_proxy_mv': float(np.mean(ir_flat)),
            'p90_ir_drop_proxy_mv': float(np.percentile(ir_flat, 90)),
            'p95_ir_drop_proxy_mv': float(np.percentile(ir_flat, 95)),
            'p99_ir_drop_proxy_mv': float(np.percentile(ir_flat, 99)),
            'max_ir_drop_proxy_mv': float(np.max(ir_flat)),
            'power_density_grid': power_density_grid,
            'ir_drop_grid': ir_drop_grid
        }
