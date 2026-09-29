#!/usr/bin/env python3
"""
LEF Technology Library Parser for CircuitNet 28nm
Part of Phase 2 — Circuit Graph Construction & Validation
"""

import os
import re

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
LEF_PATH = os.path.join(PROJECT_ROOT, 'dataset/raw/circuitnet.lef')

def parse_circuitnet_lef(lef_path=LEF_PATH):
    """
    Parse CircuitNet 28nm LEF file to extract all macros, standard cells,
    their physical dimensions, site, class, and pin definitions.
    """
    macros = {}
    layers = []
    sites = {}
    
    current_macro = None
    in_pin = False
    in_obs = False
    
    with open(lef_path, 'r', errors='ignore') as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith('#'):
                continue
                
            parts = line_str.split()
            token = parts[0].upper()
            
            # Layers & Sites at top-level
            if not current_macro:
                if token == 'LAYER' and len(parts) >= 2:
                    layers.append(parts[1])
                    continue
                elif token == 'SITE' and len(parts) >= 2:
                    site_name = parts[1]
                    sites[site_name] = {'width': 0.21, 'height': 1.05} # Standard CoreSite default
                    continue
            
            # Macro parsing
            if token == 'MACRO' and len(parts) >= 2:
                current_macro = parts[1]
                macros[current_macro] = {
                    'cell_type': current_macro,
                    'class': 'CORE',
                    'site': 'CoreSite',
                    'width': None,
                    'height': None,
                    'area': None,
                    'pins': []
                }
                continue
                
            if current_macro:
                if token == 'CLASS' and len(parts) >= 2:
                    macros[current_macro]['class'] = parts[1].rstrip(';')
                elif token == 'SITE' and len(parts) >= 2:
                    macros[current_macro]['site'] = parts[1].rstrip(';')
                elif token == 'SIZE' and len(parts) >= 4:
                    try:
                        w = float(parts[1])
                        h = float(parts[3])
                        macros[current_macro]['width'] = w
                        macros[current_macro]['height'] = h
                        macros[current_macro]['area'] = round(w * h, 4)
                    except ValueError:
                        pass
                elif token == 'PIN' and len(parts) >= 2:
                    in_pin = True
                    macros[current_macro]['pins'].append(parts[1].rstrip(';'))
                elif token == 'OBS':
                    in_obs = True
                elif token == 'END':
                    if len(parts) >= 2:
                        target = parts[1].rstrip(';')
                        if in_pin and (target in macros[current_macro]['pins'] or target == 'PIN'):
                            in_pin = False
                        elif in_obs and target == 'OBS':
                            in_obs = False
                        elif target == current_macro:
                            current_macro = None
                    else:
                        if in_pin: in_pin = False
                        elif in_obs: in_obs = False
                        elif current_macro: current_macro = None

    return {
        'layers': layers,
        'sites': sites,
        'macros': macros
    }

if __name__ == '__main__':
    lef_data = parse_circuitnet_lef()
    print(f"Parsed {len(lef_data['macros'])} macros from LEF.")
    sample = list(lef_data['macros'].keys())[0]
    print(f"Sample macro '{sample}': {lef_data['macros'][sample]}")
