#!/usr/bin/env python3
"""
Phase 2 — Graph Validation Suite
Executable via: python3 -m src.graph.validate_graph --all
"""

import os
import sys
import glob
import time
import argparse
import numpy as np
import pandas as pd
from src.graph.lef_parser import parse_circuitnet_lef

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
CIRCUIT_GRAPH_DIR = os.path.join(PROJECT_ROOT, 'dataset/circuit_graph')
METADATA_DIR = os.path.join(PROJECT_ROOT, 'dataset/metadata')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results/phase_02')

def validate_all_graphs():
    t0 = time.time()
    os.makedirs(METADATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(RESULTS_DIR, 'logs'), exist_ok=True)
    
    # 1. Parse LEF for cell verification
    lef_data = parse_circuitnet_lef()
    lef_macros = set(lef_data['macros'].keys())
    
    node_files = sorted(glob.glob(os.path.join(CIRCUIT_GRAPH_DIR, 'node_attr', '*.npy')))
    total_discovered = len(node_files)
    
    records = []
    total_cells = 0
    total_nets = 0
    total_pins = 0
    total_unrolled_edges = 0
    total_missing_lef = 0
    total_invalid_idx = 0
    total_nans = 0
    
    pass_count = 0
    warn_count = 0
    fail_count = 0
    
    for nf in node_files:
        d = os.path.basename(nf).replace('_node_attr.npy', '')
        node_path = nf
        net_path = os.path.join(CIRCUIT_GRAPH_DIR, 'net_attr', f"{d}_net_attr.npy")
        pin_path = os.path.join(CIRCUIT_GRAPH_DIR, 'pin_attr', f"{d}_pin_attr.npy")
        
        nodes = np.load(node_path, allow_pickle=True)
        nets = np.load(net_path, allow_pickle=True)
        pins = np.load(pin_path, allow_pickle=True)
        
        num_cells = nodes.shape[1]
        num_nets = nets.shape[1]
        raw_pins = pins.shape[1]
        
        total_cells += num_cells
        total_nets += num_nets
        total_pins += raw_pins
        
        # Check cell types in LEF
        cell_types = nodes[1, :]
        missing_lef = [ct for ct in cell_types if ct not in lef_macros]
        missing_lef_count = len(missing_lef)
        total_missing_lef += missing_lef_count
        
        invalid_node_idx = 0
        invalid_net_idx = 0
        nan_count = 0
        
        cell_degree = np.zeros(num_cells, dtype=int)
        net_degree = np.zeros(num_nets, dtype=int)
        unrolled_edges = 0
        duplicate_pins = 0
        
        seen_pin_connections = set()
        
        for i in range(raw_pins):
            pname = pins[0, i]
            net_val = pins[1, i]
            node_val = pins[2, i]
            
            # Row 1 is net index, Row 2 is node index
            net_list = net_val if isinstance(net_val, list) else [net_val]
            node_list = node_val if isinstance(node_val, list) else [node_val]
            
            for n_idx in node_list:
                for bit_idx, net_idx in enumerate(net_list):
                    unrolled_edges += 1
                    
                    if n_idx is None or (isinstance(n_idx, float) and np.isnan(n_idx)):
                        nan_count += 1
                        continue
                    if net_idx is None or (isinstance(net_idx, float) and np.isnan(net_idx)):
                        nan_count += 1
                        continue
                        
                    n_int = int(n_idx)
                    net_int = int(net_idx)
                    
                    pin_label = f"{pname}[{bit_idx}]" if len(net_list) > 1 else pname
                    pair_key = (n_int, net_int, pin_label)
                    if pair_key in seen_pin_connections:
                        duplicate_pins += 1
                    else:
                        seen_pin_connections.add(pair_key)
                        
                    if n_int < 0 or n_int >= num_cells:
                        invalid_node_idx += 1
                    else:
                        cell_degree[n_int] += 1
                        
                    if net_int < 0 or net_int >= num_nets:
                        invalid_net_idx += 1
                    else:
                        net_degree[net_int] += 1
                        
        total_unrolled_edges += unrolled_edges
        total_invalid_idx += (invalid_node_idx + invalid_net_idx)
        total_nans += nan_count
        
        isolated_cells = int(np.sum(cell_degree == 0))
        isolated_nets = int(np.sum(net_degree == 0))
        
        status = 'PASS'
        warnings = []
        if invalid_node_idx > 0 or invalid_net_idx > 0 or nan_count > 0 or missing_lef_count > 0:
            status = 'FAIL'
            fail_count += 1
        elif isolated_cells > 0 or isolated_nets > 0 or duplicate_pins > 0:
            status = 'WARN'
            warn_count += 1
            if isolated_cells > 0: warnings.append(f"{isolated_cells} isolated cells")
            if isolated_nets > 0: warnings.append(f"{isolated_nets} empty nets")
            if duplicate_pins > 0: warnings.append(f"{duplicate_pins} duplicate pin pairings")
        else:
            status = 'PASS'
            pass_count += 1
            
        records.append({
            'design_id': d,
            'num_cells': num_cells,
            'num_nets': num_nets,
            'num_pins': raw_pins,
            'num_edges': unrolled_edges,
            'isolated_cells': isolated_cells,
            'isolated_nets': isolated_nets,
            'duplicate_pins': duplicate_pins,
            'invalid_node_indices': invalid_node_idx,
            'invalid_net_indices': invalid_net_idx,
            'missing_lef_cells': missing_lef_count,
            'nan_count': nan_count,
            'validation_status': status,
            'warnings': '; '.join(warnings) if warnings else 'None'
        })
        
    df_val = pd.DataFrame(records)
    val_csv = os.path.join(METADATA_DIR, 'graph_validation.csv')
    df_val.to_csv(val_csv, index=False)
    
    val_res_csv = os.path.join(RESULTS_DIR, 'validation_summary.csv')
    df_val.to_csv(val_res_csv, index=False)
    
    elapsed = time.time() - t0
    
    # Required clean output banner
    print("\n" + "="*50)
    print("PHASE 2 GRAPH VALIDATION")
    print("="*50)
    print(f"Graphs discovered : {total_discovered}")
    print(f"Graphs processed  : {len(df_val)}")
    print(f"PASS              : {pass_count}")
    print(f"WARN              : {warn_count}")
    print(f"FAIL              : {fail_count}")
    print("")
    print(f"Cells             : {total_cells:,}")
    print(f"Nets              : {total_nets:,}")
    print(f"Pins              : {total_pins:,}")
    print(f"Unrolled Edges    : {total_unrolled_edges:,}")
    print("")
    print(f"Missing LEF types : {total_missing_lef}")
    print(f"Invalid indices   : {total_invalid_idx}")
    print(f"NaNs              : {total_nans}")
    print(f"Execution time    : {elapsed:.2f}s")
    print("="*50)
    
    return df_val

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Phase 2 Graph Validation")
    parser.add_argument('--all', action='store_true', help="Validate all 54 graphs")
    args = parser.parse_args()
    validate_all_graphs()
