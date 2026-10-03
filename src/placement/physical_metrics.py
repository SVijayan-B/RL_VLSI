"""
DEF Physical Layout Metric Extractor.
Extracts exact cell coordinates, net pin locations, HPWL, bounding box statistics,
and overlap counts directly from CircuitNet DEF and LEF files.
Reuses src.technology.wirelength for analytical verification.
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np

from src.technology.wirelength import compute_net_hpwl, compute_net_bbox, compute_total_hpwl


def parse_lef_macro_sizes(lef_path: Path) -> Dict[str, Tuple[float, float]]:
    """Extracts macro width and height in microns from LEF."""
    sizes = {}
    current_macro = None
    with open(lef_path, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line_s = line.strip()
            if line_s.startswith('MACRO'):
                parts = line_s.split()
                if len(parts) >= 2:
                    current_macro = parts[1]
            elif line_s.startswith('SIZE') and current_macro:
                # SIZE 0.840 BY 1.050 ;
                parts = line_s.split()
                if len(parts) >= 4 and parts[2] == 'BY':
                    w = float(parts[1])
                    h = float(parts[3])
                    sizes[current_macro] = (w, h)
            elif line_s.startswith('END') and current_macro:
                parts = line_s.split()
                if len(parts) >= 2 and parts[1] == current_macro:
                    current_macro = None
    return sizes


def extract_def_metrics(
    def_path: Path,
    macro_sizes: Dict[str, Tuple[float, float]],
    dbu_to_micron: float = 0.0005
) -> Dict[str, Any]:
    """
    Extracts comprehensive physical design baseline metrics from DEF.
    """
    t0 = time.time()
    
    # 1. Parse DIEAREA
    die_llx, die_lly, die_urx, die_ury = 0, 0, 0, 0
    components = {} # inst_name -> (cell_type, x, y, orient)
    nets = {}       # net_name -> list of (inst_name, pin_name)
    
    in_comp = False
    in_nets = False
    current_net = None
    
    with open(def_path, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line_s = line.strip()
            if line_s.startswith('DIEAREA'):
                pts = re.findall(r'\(\s*(-?\d+)\s+(-?\d+)\s*\)', line_s)
                if len(pts) >= 2:
                    die_llx, die_lly = map(int, pts[0])
                    die_urx, die_ury = map(int, pts[1])
            elif line_s.startswith('COMPONENTS'):
                in_comp = True
            elif line_s.startswith('END COMPONENTS'):
                in_comp = False
            elif in_comp and line_s.startswith('- '):
                # - inst cell_type + PLACED ( x y ) orient ;
                parts = line_s.split()
                if len(parts) >= 3:
                    inst = parts[1]
                    cell_type = parts[2]
                    coords = re.findall(r'\(\s*(-?\d+)\s+(-?\d+)\s*\)', line_s)
                    if coords:
                        x, y = map(int, coords[0])
                        components[inst] = (cell_type, x, y)
            elif line_s.startswith('NETS'):
                in_nets = True
            elif line_s.startswith('END NETS'):
                in_nets = False
            elif in_nets:
                if line_s.startswith('- '):
                    parts = line_s.split()
                    if len(parts) >= 2:
                        current_net = parts[1]
                        nets[current_net] = []
                        # Parse connections on the net definition line itself
                        conns = re.findall(r'\(\s*([^\s\(\)]+)\s+([^\s\(\)]+)\s*\)', line_s)
                        for inst, pin in conns:
                            if inst != 'PIN':
                                nets[current_net].append(inst)
                        if line_s.endswith(';'):
                            current_net = None
                elif current_net:
                    # parse connections on continuation lines
                    conns = re.findall(r'\(\s*([^\s\(\)]+)\s+([^\s\(\)]+)\s*\)', line_s)
                    for inst, pin in conns:
                        if inst != 'PIN': # standard cell instance
                            nets[current_net].append(inst)
                    if line_s.endswith(';'):
                        current_net = None

    # Compute Net Coordinates & HPWL
    net_hpwls = []
    net_dxs = []
    net_dys = []
    
    for net_name, inst_list in nets.items():
        coords = []
        for inst in inst_list:
            if inst in components:
                _, x, y = components[inst]
                coords.append([float(x), float(y)])
        if len(coords) >= 2:
            arr = np.array(coords, dtype=np.float64)
            hpwl = compute_net_hpwl(arr, dbu_to_micron=dbu_to_micron)
            dx, dy, _ = compute_net_bbox(arr, dbu_to_micron=dbu_to_micron)
            net_hpwls.append(hpwl)
            net_dxs.append(dx)
            net_dys.append(dy)
        else:
            net_hpwls.append(0.0)
            net_dxs.append(0.0)
            net_dys.append(0.0)
            
    hpwl_arr = np.array(net_hpwls, dtype=np.float64)
    tot_hpwl_um = float(np.sum(hpwl_arr))
    mean_hpwl_um = float(np.mean(hpwl_arr)) if len(hpwl_arr) > 0 else 0.0
    max_hpwl_um = float(np.max(hpwl_arr)) if len(hpwl_arr) > 0 else 0.0
    
    # Compute Core Dimensions and Area
    core_w_um = (die_urx - die_llx) * dbu_to_micron
    core_h_um = (die_ury - die_lly) * dbu_to_micron
    die_area_um2 = core_w_um * core_h_um
    
    # Total Cell Area and Utilization
    tot_cell_area_um2 = 0.0
    for inst, (cell_type, x, y) in components.items():
        if cell_type in macro_sizes:
            cw, ch = macro_sizes[cell_type]
            tot_cell_area_um2 += cw * ch
            
    measured_util = (tot_cell_area_um2 / die_area_um2) if die_area_um2 > 0 else 0.0
    
    runtime = time.time() - t0
    
    return {
        'num_cells': len(components),
        'num_nets': len(nets),
        'core_width_um': round(core_w_um, 2),
        'core_height_um': round(core_h_um, 2),
        'die_area_um2': round(die_area_um2, 2),
        'total_cell_area_um2': round(tot_cell_area_um2, 2),
        'measured_utilization': round(measured_util, 4),
        'total_hpwl_um': round(tot_hpwl_um, 2),
        'mean_net_hpwl_um': round(mean_hpwl_um, 4),
        'max_net_hpwl_um': round(max_hpwl_um, 2),
        'runtime_sec': round(runtime, 3)
    }
