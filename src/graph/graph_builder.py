#!/usr/bin/env python3
"""
Canonical Graph Builder for CircuitNet 28nm
Part of Phase 2 — Circuit Graph Construction & Validation
"""

import os
import json
import numpy as np
from src.graph.lef_parser import parse_circuitnet_lef

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
CIRCUIT_GRAPH_DIR = os.path.join(PROJECT_ROOT, 'dataset/circuit_graph')

def build_canonical_graph(design_id, lef_macros=None, max_net_degree_for_projection=50):
    """
    Build canonical bipartite and homogeneous cell graph representation
    for a given design.
    """
    if lef_macros is None:
        lef_macros = parse_circuitnet_lef()['macros']
        
    node_path = os.path.join(CIRCUIT_GRAPH_DIR, 'node_attr', f"{design_id}_node_attr.npy")
    net_path = os.path.join(CIRCUIT_GRAPH_DIR, 'net_attr', f"{design_id}_net_attr.npy")
    pin_path = os.path.join(CIRCUIT_GRAPH_DIR, 'pin_attr', f"{design_id}_pin_attr.npy")
    
    nodes = np.load(node_path, allow_pickle=True)
    nets = np.load(net_path, allow_pickle=True)
    pins = np.load(pin_path, allow_pickle=True)
    
    num_cells = nodes.shape[1]
    num_nets = nets.shape[1]
    raw_pins = pins.shape[1]
    
    cell_names = nodes[0, :]
    cell_types = nodes[1, :]
    net_names = nets[0, :]
    
    # 1. Unroll pin connections to bipartite edge index (cell <-> net)
    bipartite_cells = []
    bipartite_nets = []
    unrolled_pin_names = []
    
    cell_degree = np.zeros(num_cells, dtype=np.int32)
    net_degree = np.zeros(num_nets, dtype=np.int32)
    net_to_cells = [[] for _ in range(num_nets)]
    
    for i in range(raw_pins):
        pname = pins[0, i]
        net_val = pins[1, i]
        node_val = pins[2, i]
        
        net_list = net_val if isinstance(net_val, list) else [net_val]
        node_list = node_val if isinstance(node_val, list) else [node_val]
        
        for n_idx in node_list:
            n_int = int(n_idx)
            for bit_idx, net_idx in enumerate(net_list):
                net_int = int(net_idx)
                pin_label = f"{pname}[{bit_idx}]" if len(net_list) > 1 else pname
                
                bipartite_cells.append(n_int)
                bipartite_nets.append(net_int)
                unrolled_pin_names.append(pin_label)
                
                cell_degree[n_int] += 1
                net_degree[net_int] += 1
                net_to_cells[net_int].append(n_int)
                
    edge_index_bipartite = np.array([bipartite_cells, bipartite_nets], dtype=np.int32)
    
    # 2. Build Cell Features (N x 7)
    # [area, width, height, aspect_ratio, is_macro, cell_degree, log_degree]
    cell_features = np.zeros((num_cells, 7), dtype=np.float32)
    for i in range(num_cells):
        ct = cell_types[i]
        lef_info = lef_macros.get(ct, {})
        w = float(lef_info.get('width', 0.84))
        h = float(lef_info.get('height', 1.05))
        area = float(lef_info.get('area', w * h))
        ar = w / h if h > 0 else 1.0
        m_class = lef_info.get('class', 'CORE')
        is_macro = 1.0 if m_class in ('BLOCK', 'RING') or ct in ('SRAM', 'PLL', 'ROM') else 0.0
        deg = float(cell_degree[i])
        
        cell_features[i, 0] = area
        cell_features[i, 1] = w
        cell_features[i, 2] = h
        cell_features[i, 3] = ar
        cell_features[i, 4] = is_macro
        cell_features[i, 5] = deg
        cell_features[i, 6] = np.log1p(deg)

    # 3. Build Net Features (M x 4)
    # [net_degree, log_degree, is_clock, is_reset]
    net_features = np.zeros((num_nets, 4), dtype=np.float32)
    for j in range(num_nets):
        n_name = net_names[j].lower()
        deg = float(net_degree[j])
        is_clk = 1.0 if 'clk' in n_name or 'clock' in n_name else 0.0
        is_rst = 1.0 if 'rst' in n_name or 'reset' in n_name else 0.0
        
        net_features[j, 0] = deg
        net_features[j, 1] = np.log1p(deg)
        net_features[j, 2] = is_clk
        net_features[j, 3] = is_rst

    # 4. Homogeneous Cell-to-Cell Projection (with high fanout threshold)
    cell_src = []
    cell_dst = []
    for net_idx in range(num_nets):
        deg = net_degree[net_idx]
        if 2 <= deg <= max_net_degree_for_projection:
            conns = net_to_cells[net_idx]
            # Form clique of connections for this net
            n_conns = len(conns)
            for a in range(n_conns):
                for b in range(a + 1, n_conns):
                    u, v = conns[a], conns[b]
                    if u != v:
                        cell_src.extend([u, v])
                        cell_dst.extend([v, u])
                        
    if cell_src:
        edge_index_cell = np.array([cell_src, cell_dst], dtype=np.int32)
        # Deduplicate undirected edges
        unique_edges = np.unique(edge_index_cell, axis=1)
    else:
        unique_edges = np.zeros((2, 0), dtype=np.int32)

    metadata = {
        'design_id': design_id,
        'num_cells': int(num_cells),
        'num_nets': int(num_nets),
        'num_bipartite_edges': int(edge_index_bipartite.shape[1]),
        'num_projected_cell_edges': int(unique_edges.shape[1]),
        'max_net_degree_for_projection': int(max_net_degree_for_projection),
        'total_cell_area': float(np.sum(cell_features[:, 0])),
        'feature_schema_version': '2.0.0'
    }

    return {
        'cell_names': cell_names,
        'cell_types': cell_types,
        'cell_features': cell_features,
        'net_names': net_names,
        'net_features': net_features,
        'pin_names': np.array(unrolled_pin_names, dtype=object),
        'edge_index_bipartite': edge_index_bipartite,
        'edge_index_cell': unique_edges,
        'metadata_json': json.dumps(metadata)
    }

if __name__ == '__main__':
    d = 'RISCY-a-1-c2'
    g = build_canonical_graph(d)
    print(f"Built canonical graph for {d}:")
    print(f"  Cells: {len(g['cell_names'])}, Cell features: {g['cell_features'].shape}")
    print(f"  Nets : {len(g['net_names'])}, Net features: {g['net_features'].shape}")
    print(f"  Bipartite edges: {g['edge_index_bipartite'].shape}")
    print(f"  Projected cell-cell edges (fanout <= 50): {g['edge_index_cell'].shape}")
