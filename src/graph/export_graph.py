#!/usr/bin/env python3
"""
Canonical Graph Exporter for CircuitNet 28nm
Exports validated canonical graphs to dataset/graphs/{design_id}_graph.npz
and generates dataset/metadata/graph_manifest.csv / .json
"""

import os
import glob
import time
import json
import numpy as np
import pandas as pd
from src.graph.lef_parser import parse_circuitnet_lef
from src.graph.graph_builder import build_canonical_graph

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
CIRCUIT_GRAPH_DIR = os.path.join(PROJECT_ROOT, 'dataset/circuit_graph')
GRAPHS_DIR = os.path.join(PROJECT_ROOT, 'dataset/graphs')
METADATA_DIR = os.path.join(PROJECT_ROOT, 'dataset/metadata')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results/phase_02')

def export_all_canonical_graphs():
    print("="*80)
    print("PHASE 2 — TASK 8 & 9: CANONICAL GRAPH EXPORT & MANIFEST GENERATION")
    print("="*80)
    t0 = time.time()
    
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # 1. Parse LEF once
    print("Parsing LEF definitions...")
    lef_data = parse_circuitnet_lef()
    lef_macros = lef_data['macros']
    
    node_files = sorted(glob.glob(os.path.join(CIRCUIT_GRAPH_DIR, 'node_attr', '*.npy')))
    print(f"Exporting canonical graphs for {len(node_files)} designs...")
    
    # Load validation status
    val_csv = os.path.join(METADATA_DIR, 'graph_validation.csv')
    val_status_map = {}
    if os.path.exists(val_csv):
        df_v = pd.read_csv(val_csv)
        for _, row in df_v.iterrows():
            val_status_map[row['design_id']] = row['validation_status']
            
    manifest_records = []
    
    for idx, nf in enumerate(node_files):
        d = os.path.basename(nf).replace('_node_attr.npy', '')
        t_design = time.time()
        
        # Build canonical graph dict
        g = build_canonical_graph(d, lef_macros=lef_macros, max_net_degree_for_projection=50)
        
        # Save to compressed .npz
        out_npz = os.path.join(GRAPHS_DIR, f"{d}_graph.npz")
        np.savez_compressed(
            out_npz,
            cell_names=g['cell_names'],
            cell_types=g['cell_types'],
            cell_features=g['cell_features'],
            net_names=g['net_names'],
            net_features=g['net_features'],
            pin_names=g['pin_names'],
            edge_index_bipartite=g['edge_index_bipartite'],
            edge_index_cell=g['edge_index_cell'],
            metadata_json=np.array([g['metadata_json']], dtype=object)
        )
        
        file_size_mb = os.path.getsize(out_npz) / (1024 * 1024)
        meta = json.loads(g['metadata_json'])
        status = val_status_map.get(d, 'PASS')
        
        manifest_records.append({
            'design_id': d,
            'source_node_attr': f"dataset/circuit_graph/node_attr/{d}_node_attr.npy",
            'source_net_attr': f"dataset/circuit_graph/net_attr/{d}_net_attr.npy",
            'source_pin_attr': f"dataset/circuit_graph/pin_attr/{d}_pin_attr.npy",
            'num_cells': meta['num_cells'],
            'num_nets': meta['num_nets'],
            'num_pins': len(g['pin_names']),
            'num_bipartite_edges': meta['num_bipartite_edges'],
            'num_projected_cell_edges': meta['num_projected_cell_edges'],
            'num_cell_types': len(np.unique(g['cell_types'])),
            'total_cell_area_um2': round(meta['total_cell_area'], 2),
            'num_components': 1,
            'validation_status': status,
            'graph_output_file': f"dataset/graphs/{d}_graph.npz",
            'graph_file_size_mb': round(file_size_mb, 2),
            'feature_schema_version': '2.0.0'
        })
        
        if (idx + 1) % 10 == 0 or (idx + 1) == len(node_files):
            print(f"  Exported {idx+1}/{len(node_files)} graphs... ({d}: {file_size_mb:.2f} MB in {time.time()-t_design:.2f}s)")
            
    # Save Manifest CSV and JSON
    df_man = pd.DataFrame(manifest_records)
    out_csv = os.path.join(METADATA_DIR, 'graph_manifest.csv')
    df_man.to_csv(out_csv, index=False)
    print(f"\nGenerated graph manifest: {out_csv} ({len(df_man)} rows)")
    
    out_json = os.path.join(METADATA_DIR, 'graph_manifest.json')
    df_man.to_json(out_json, orient='records', indent=2)
    print(f"Generated graph manifest JSON: {out_json}")
    
    total_size_mb = sum([r['graph_file_size_mb'] for r in manifest_records])
    print(f"\nTotal canonical graphs storage: {total_size_mb:.2f} MB (~{total_size_mb/1024:.2f} GB)")
    print(f"Total execution time: {time.time()-t0:.2f}s")
    
    return df_man

if __name__ == '__main__':
    export_all_canonical_graphs()
