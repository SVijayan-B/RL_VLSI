"""
PDN Geometry Extraction Module for CircuitNet N28.
Extracts power/ground stripes, layers, geometries, and computes normalized
PDN grid resistance proxies from DEF SPECIALNETS.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np


def extract_pdn_stripes(
    def_path: Path,
    dbu_to_micron: float = 0.0005,
    max_stripes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extracts geometric power/ground stripes and shapes from DEF SPECIALNETS.

    Args:
        def_path: Path to CircuitNet DEF file.
        dbu_to_micron: DBU conversion factor (default 1/2000 = 0.0005).
        max_stripes: Optional cap on stripes parsed for fast processing.

    Returns:
        Dictionary containing extracted stripe records, layer breakdown, and summary.
    """
    stripes = [] # dict per stripe: {net, layer, x1, y1, x2, y2, width_um, length_um, orientation}
    in_specialnets = False
    current_net = None
    
    with open(def_path, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line_s = line.strip()
            if line_s.startswith('SPECIALNETS'):
                in_specialnets = True
            elif line_s.startswith('END SPECIALNETS'):
                in_specialnets = False
                break
            elif in_specialnets:
                if line_s.startswith('- '):
                    parts = line_s.split()
                    current_net = parts[1]
                elif current_net and ('ROUTED' in line_s or 'STRIPE' in line_s or 'FOLLOWPIN' in line_s):
                    # Sample DEF syntax:
                    # + ROUTED M1 420 + SHAPE STRIPE ( 0 1000 ) ( 500000 * )
                    # Extract layer and width
                    tokens = line_s.split()
                    layer = None
                    width_dbu = 0
                    for idx, tok in enumerate(tokens):
                        if tok in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'AP', 'RV']:
                            layer = tok
                            if idx + 1 < len(tokens):
                                try:
                                    width_dbu = int(tokens[idx+1])
                                except ValueError:
                                    width_dbu = 0
                            break
                    # Extract coordinate points ( x y )
                    coords = re.findall(r'\(\s*([^\s\(\)]+)\s+([^\s\(\)]+)\s*\)', line_s)
                    if len(coords) >= 2 and layer:
                        p1_x, p1_y = coords[0]
                        p2_x, p2_y = coords[1]
                        
                        try:
                            x1 = float(p1_x)
                            y1 = float(p1_y)
                            x2 = float(p2_x) if p2_x != '*' else x1
                            y2 = float(p2_y) if p2_y != '*' else y1
                            
                            x1_um = min(x1, x2) * dbu_to_micron
                            x2_um = max(x1, x2) * dbu_to_micron
                            y1_um = min(y1, y2) * dbu_to_micron
                            y2_um = max(y1, y2) * dbu_to_micron
                            
                            w_um = width_dbu * dbu_to_micron if width_dbu > 0 else 0.21
                            l_um = max(x2_um - x1_um, y2_um - y1_um)
                            orient = 'H' if (x2_um - x1_um) >= (y2_um - y1_um) else 'V'
                            
                            stripes.append({
                                'net': current_net,
                                'layer': layer,
                                'x1_um': round(x1_um, 3),
                                'y1_um': round(y1_um, 3),
                                'x2_um': round(x2_um, 3),
                                'y2_um': round(y2_um, 3),
                                'width_um': round(w_um, 3),
                                'length_um': round(l_um, 3),
                                'orientation': orient
                            })
                            if max_stripes and len(stripes) >= max_stripes:
                                break
                        except ValueError:
                            continue

    # Layer breakdown
    layer_counts = {}
    for s in stripes:
        layer_counts[s['layer']] = layer_counts.get(s['layer'], 0) + 1

    return {
        'total_stripes_extracted': len(stripes),
        'layer_counts': layer_counts,
        'stripes': stripes
    }


def compute_pdn_effective_resistance(
    die_width_um: float,
    die_height_um: float,
    pdn_density_factor: float = 1.0,
    r_sheet_norm: float = 0.05 # normalized Ohm/square proxy
) -> float:
    """
    Computes an analytical normalized PDN effective grid resistance proxy (Ohms)
    from core edge to center.

    Formula:
        R_pdn_proxy = (r_sheet_norm / pdn_density_factor) * (distance_center / width_eff)
    """
    w_safe = max(1.0, die_width_um)
    h_safe = max(1.0, die_height_um)
    dist_center = 0.5 * min(w_safe, h_safe)
    eff_width = max(w_safe, h_safe)
    
    r_proxy = (r_sheet_norm / max(0.1, pdn_density_factor)) * (dist_center / eff_width)
    return float(r_proxy)
