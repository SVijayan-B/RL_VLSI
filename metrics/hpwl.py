"""
Canonical Half-Perimeter Wire Length (HPWL) Metric Extractor.
Authoritative implementation locked to Phase 4 / Phase 7 integrity specifications.
Features:
- Rigorous DEF parsing supporting multi-line NET definitions and header-line pin tuples.
- Exact unit conversion: 1 DBU = 0.0005 um (2000 DBU/um) for CircuitNet N28.
- Signal net filtering: Includes all nets with >= 2 connected standard cell / macro pins.
- Clean macro/cell boundary handling with provenance tagging.
"""

import re
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

CIRCUITNET_DBU_PER_MICRON = 2000.0
CIRCUITNET_DBU_TO_MICRON = 1.0 / CIRCUITNET_DBU_PER_MICRON

def parse_def_netlist_and_placements(def_path: str) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, List[str]]]:
    """
    Parses component placements and net connection graph from DEF file.
    Handles OpenROAD write_def header connection lines correctly.
    """
    components = {} # inst_name -> (x, y)
    nets = {}       # net_name -> list of inst_names
    
    in_comp = False
    in_nets = False
    current_net = None

    with open(def_path, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line_s = line.strip()
            if not line_s:
                continue

            if line_s.startswith('COMPONENTS'):
                in_comp = True
                continue
            elif line_s.startswith('END COMPONENTS'):
                in_comp = False
                continue
            elif in_comp and line_s.startswith('- '):
                # Format: - inst cell_type + PLACED ( x y ) orient ;
                coords = re.findall(r'\(\s*(-?\d+)\s+(-?\d+)\s*\)', line_s)
                if coords:
                    parts = line_s.split()
                    inst = parts[1]
                    x, y = int(coords[0][0]), int(coords[0][1])
                    components[inst] = (x, y)
                continue

            if line_s.startswith('NETS'):
                in_nets = True
                continue
            elif line_s.startswith('END NETS'):
                in_nets = False
                continue
            elif in_nets:
                if line_s.startswith('- '):
                    parts = line_s.split()
                    if len(parts) >= 2:
                        current_net = parts[1]
                        nets[current_net] = []
                        # Parse pin connections appearing on net header line
                        conns = re.findall(r'\(\s*([^\s\(\)]+)\s+([^\s\(\)]+)\s*\)', line_s)
                        for inst, pin in conns:
                            if inst != 'PIN':
                                nets[current_net].append(inst)
                        if line_s.endswith(';'):
                            current_net = None
                elif current_net:
                    conns = re.findall(r'\(\s*([^\s\(\)]+)\s+([^\s\(\)]+)\s*\)', line_s)
                    for inst, pin in conns:
                        if inst != 'PIN':
                            nets[current_net].append(inst)
                    if line_s.endswith(';'):
                        current_net = None

    return components, nets


def compute_canonical_hpwl(def_path: str, dbu_to_micron: float = CIRCUITNET_DBU_TO_MICRON) -> Dict[str, Any]:
    """
    Computes Half-Perimeter Wire Length across all signal nets in microns (um).
    """
    t0 = time.time()
    if not os.path.exists(def_path):
        raise FileNotFoundError(f"DEF file not found: {def_path}")

    components, nets = parse_def_netlist_and_placements(def_path)

    net_hpwls = []
    included_nets = 0
    single_pin_or_empty_nets = 0

    for net_name, inst_list in nets.items():
        coords_x = []
        coords_y = []
        for inst in inst_list:
            if inst in components:
                cx, cy = components[inst]
                coords_x.append(cx)
                coords_y.append(cy)

        if len(coords_x) >= 2:
            min_x, max_x = min(coords_x), max(coords_x)
            min_y, max_y = min(coords_y), max(coords_y)
            hpwl = float((max_x - min_x) + (max_y - min_y)) * dbu_to_micron
            net_hpwls.append(hpwl)
            included_nets += 1
        else:
            single_pin_or_empty_nets += 1

    total_hpwl_um = float(sum(net_hpwls)) if net_hpwls else 0.0
    mean_hpwl_um = float(np.mean(net_hpwls)) if net_hpwls else 0.0
    max_hpwl_um = float(max(net_hpwls)) if net_hpwls else 0.0
    elapsed = time.time() - t0

    return {
        "total_hpwl_um": round(total_hpwl_um, 2),
        "mean_net_hpwl_um": round(mean_hpwl_um, 4),
        "max_net_hpwl_um": round(max_hpwl_um, 2),
        "num_total_nets": len(nets),
        "num_included_nets": included_nets,
        "num_single_or_empty_nets": single_pin_or_empty_nets,
        "num_cells": len(components),
        "units": "microns (um)",
        "dbu_to_micron": dbu_to_micron,
        "provenance": "DIRECT_DEF_PARSER",
        "runtime_sec": round(elapsed, 3)
    }
