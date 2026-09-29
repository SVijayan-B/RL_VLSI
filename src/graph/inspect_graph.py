#!/usr/bin/env python3
"""
Inspect Graph Source Data in dataset/circuit_graph/
Part of Phase 2 — Circuit Graph Construction & Validation
"""

import os
import glob
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
CIRCUIT_GRAPH_DIR = os.path.join(PROJECT_ROOT, 'dataset/circuit_graph')
METADATA_DIR = os.path.join(PROJECT_ROOT, 'dataset/metadata')

def inspect_circuit_graph_sources():
    print("="*80)
    print("PHASE 2 — TASK 1: DATASET STRUCTURE AUDIT")
    print("="*80)
    
    node_files = sorted(glob.glob(os.path.join(CIRCUIT_GRAPH_DIR, 'node_attr', '*.npy')))
    net_files = sorted(glob.glob(os.path.join(CIRCUIT_GRAPH_DIR, 'net_attr', '*.npy')))
    pin_files = sorted(glob.glob(os.path.join(CIRCUIT_GRAPH_DIR, 'pin_attr', '*.npy')))
    
    print(f"Discovered in node_attr: {len(node_files)} files")
    print(f"Discovered in net_attr : {len(net_files)} files")
    print(f"Discovered in pin_attr : {len(pin_files)} files")
    
    # Extract unique design IDs
    node_designs = {os.path.basename(f).replace('_node_attr.npy', ''): f for f in node_files}
    net_designs = {os.path.basename(f).replace('_net_attr.npy', ''): f for f in net_files}
    pin_designs = {os.path.basename(f).replace('_pin_attr.npy', ''): f for f in pin_files}
    
    all_design_ids = sorted(list(set(node_designs.keys()) | set(net_designs.keys()) | set(pin_designs.keys())))
    print(f"Total unique design IDs across all components: {len(all_design_ids)}")
    
    inventory_records = []
    
    for design_id in all_design_ids:
        rec = {
            'design_id': design_id,
            'node_attr_file': 'missing',
            'node_attr_shape': 'missing',
            'node_attr_dtype': 'missing',
            'net_attr_file': 'missing',
            'net_attr_shape': 'missing',
            'net_attr_dtype': 'missing',
            'pin_attr_file': 'missing',
            'pin_attr_shape': 'missing',
            'pin_attr_dtype': 'missing',
            'requires_allow_pickle': True,
            'status': 'INCOMPLETE'
        }
        
        has_node = design_id in node_designs
        has_net = design_id in net_designs
        has_pin = design_id in pin_designs
        
        if has_node:
            p = node_designs[design_id]
            rec['node_attr_file'] = os.path.basename(p)
            arr = np.load(p, allow_pickle=True)
            rec['node_attr_shape'] = str(arr.shape)
            rec['node_attr_dtype'] = str(arr.dtype)
            
        if has_net:
            p = net_designs[design_id]
            rec['net_attr_file'] = os.path.basename(p)
            arr = np.load(p, allow_pickle=True)
            rec['net_attr_shape'] = str(arr.shape)
            rec['net_attr_dtype'] = str(arr.dtype)
            
        if has_pin:
            p = pin_designs[design_id]
            rec['pin_attr_file'] = os.path.basename(p)
            arr = np.load(p, allow_pickle=True)
            rec['pin_attr_shape'] = str(arr.shape)
            rec['pin_attr_dtype'] = str(arr.dtype)
            
        if has_node and has_net and has_pin:
            rec['status'] = 'COMPLETE'
            
        inventory_records.append(rec)
        
    df_inv = pd.DataFrame(inventory_records)
    os.makedirs(METADATA_DIR, exist_ok=True)
    out_csv = os.path.join(METADATA_DIR, 'graph_source_inventory.csv')
    df_inv.to_csv(out_csv, index=False)
    print(f"\nGenerated graph source inventory: {out_csv} ({len(df_inv)} rows)")
    
    complete_count = (df_inv['status'] == 'COMPLETE').sum()
    print(f"Complete designs with all 3 components: {complete_count} / {len(df_inv)}")
    
    # Representative inspection (Task 2)
    print("\n" + "="*80)
    print("PHASE 2 — TASK 2: REPRESENTATIVE SAMPLE INSPECTION")
    print("="*80)
    
    sample_designs = ['RISCY-a-1-c2', 'RISCY-FPU-b-2-c5', 'zero-riscy-b-1-c20']
    for d in sample_designs:
        print(f"\n--- Representative Design: {d} ---")
        node_arr = np.load(node_designs[d], allow_pickle=True)
        net_arr = np.load(net_designs[d], allow_pickle=True)
        pin_arr = np.load(pin_designs[d], allow_pickle=True)
        
        print(f"Node Array Shape: {node_arr.shape}, Dtype: {node_arr.dtype}")
        print("  Row 0 (Instance Names, first 5):", node_arr[0, :5])
        print("  Row 1 (Cell Types, first 5):", node_arr[1, :5])
        print(f"  Unique Cell Types: {len(np.unique(node_arr[1, :]))}")
        
        print(f"Net Array Shape: {net_arr.shape}, Dtype: {net_arr.dtype}")
        print("  Row 0 (Net Names, first 5):", net_arr[0, :5])
        print(f"  Total Nets: {net_arr.shape[1]}")
        
        print(f"Pin Array Shape: {pin_arr.shape}, Dtype: {pin_arr.dtype}")
        print("  Row 0 (Pin Names, first 5):", pin_arr[0, :5])
        print("  Row 1 (Node Indices, first 5):", pin_arr[1, :5])
        print("  Row 2 (Net Indices, first 5):", pin_arr[2, :5])
        
        # Unroll node indices safely
        all_node_indices = []
        for i in range(pin_arr.shape[1]):
            val = pin_arr[1, i]
            if isinstance(val, list):
                all_node_indices.extend(val)
            else:
                all_node_indices.append(int(val))
                
        all_net_indices = [int(pin_arr[2, i]) for i in range(pin_arr.shape[1])]
        
        node_idx_min, node_idx_max = min(all_node_indices), max(all_node_indices)
        net_idx_min, net_idx_max = min(all_net_indices), max(all_net_indices)
        print(f"  Node Index Range in Pins: [{node_idx_min}, {node_idx_max}] (Num Nodes: {node_arr.shape[1]})")
        print(f"  Net Index Range in Pins : [{net_idx_min}, {net_idx_max}] (Num Nets: {net_arr.shape[1]})")
        print(f"  Total unrolled pin connections (edges): {len(all_node_indices)}")
        
    return df_inv

if __name__ == '__main__':
    inspect_circuit_graph_sources()
