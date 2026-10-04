#!/usr/bin/env python3
"""
Phase 8 — Graph Feature Extraction Smoke Test
Verifies canonical graph loading, feature shapes, dtypes, edge indices,
statistics calculation, graph-level feature extraction, normalization parameters,
and Phase 9 interface contract without training any neural network.
"""

import os
import sys
import json
import numpy as np

def run_smoke_test():
    print("="*60)
    print("PHASE 8 FEATURE EXTRACTION — SMOKE TEST")
    print("="*60)

    project_root = os.path.expanduser('~/CircuitNet_28nm')
    test_graph = os.path.join(project_root, "dataset/graphs/RISCY-a-1-c2_graph.npz")
    assert os.path.exists(test_graph), f"Graph file not found: {test_graph}"

    # 1. Load one canonical graph
    print("1. Loading canonical graph: RISCY-a-1-c2_graph.npz...")
    d = np.load(test_graph, allow_pickle=True)

    # 2. Inspect all fields
    required_keys = [
        'cell_names', 'cell_types', 'cell_features',
        'net_names', 'net_features', 'pin_names',
        'edge_index_bipartite', 'edge_index_cell', 'metadata_json'
    ]
    for k in required_keys:
        assert k in d, f"Missing required field {k} in npz"
    print("   [PASS] All 9 required npz fields exist.")

    # 3. Verify cell_features shape
    c_feat = d['cell_features']
    assert c_feat.ndim == 2, f"cell_features ndim={c_feat.ndim} != 2"
    assert c_feat.shape[1] == 7, f"cell_features dim={c_feat.shape[1]} != 7 (Canonical requirement)"
    assert c_feat.shape[0] == len(d['cell_names']), "cell_features rows != cell_names count"
    assert c_feat.dtype == np.float32, f"cell_features dtype={c_feat.dtype} != float32"
    print(f"   [PASS] cell_features verified: shape={c_feat.shape}, dtype={c_feat.dtype}")

    # 4. Verify net_features shape
    n_feat = d['net_features']
    assert n_feat.ndim == 2, f"net_features ndim={n_feat.ndim} != 2"
    assert n_feat.shape[1] == 4, f"net_features dim={n_feat.shape[1]} != 4 (Canonical requirement)"
    assert n_feat.shape[0] == len(d['net_names']), "net_features rows != net_names count"
    assert n_feat.dtype == np.float32, f"net_features dtype={n_feat.dtype} != float32"
    print(f"   [PASS] net_features verified: shape={n_feat.shape}, dtype={n_feat.dtype}")

    # 5. Verify edge indices
    e_bip = d['edge_index_bipartite']
    e_cell = d['edge_index_cell']
    assert e_bip.shape[0] == 2, "edge_index_bipartite row dim != 2"
    assert e_bip.shape[1] == len(d['pin_names']), "edge_index_bipartite edge count != pin_names count"
    assert e_cell.shape[0] == 2, "edge_index_cell row dim != 2"
    assert e_cell.shape[1] > 0, "edge_index_cell is empty"
    print(f"   [PASS] edge indices verified: bipartite={e_bip.shape}, projected cell={e_cell.shape}")

    # 6. Calculate feature statistics
    c_mean = np.mean(c_feat, axis=0)
    c_std = np.std(c_feat, axis=0)
    assert np.all(np.isfinite(c_mean)) and np.all(np.isfinite(c_std)), "Non-finite cell feature stats"
    print("   [PASS] Feature statistics successfully computed (finite & valid).")

    # 7. Generate graph-level features
    meta = json.loads(str(d['metadata_json'][0]))
    gl_features = {
        'num_cells': int(meta['num_cells']),
        'num_nets': int(meta['num_nets']),
        'num_pins': len(d['pin_names']),
        'num_macros': int(np.sum(c_feat[:, 4])),
        'total_cell_area': float(meta['total_cell_area']),
        'avg_net_degree': float(np.mean(n_feat[:, 0])),
        'max_net_degree': int(np.max(n_feat[:, 0])),
        'bipartite_density': float(len(d['pin_names'])) / (float(meta['num_cells']) * float(meta['num_nets']))
    }
    assert gl_features['num_cells'] == c_feat.shape[0]
    print(f"   [PASS] Graph-level features generated: {gl_features}")

    # 8. Generate normalization parameters
    norm_params = {
        'area_mean': float(c_mean[0]), 'area_std': float(c_std[0]),
        'degree_mean': float(c_mean[5]), 'degree_std': float(c_std[5])
    }
    print(f"   [PASS] Normalization parameters generated: {norm_params}")

    # 9. Validate Phase 9 interface contract
    contract_file = os.path.join(project_root, "results/phase_08/phase09_input_contract.json")
    assert os.path.exists(contract_file), f"Contract file missing: {contract_file}"
    with open(contract_file) as f:
        contract = json.load(f)
    assert contract['cell_node_features']['dimension'] == 7
    assert contract['net_node_features']['dimension'] == 4
    print("   [PASS] Phase 9 input contract matches canonical representations.")

    # 10. Exit successfully without neural network training
    print("="*60)
    print("ALL 10 SMOKE TEST CHECKS PASSED (NO NN TRAINING EXECUTED)")
    print("="*60)
    return 0

if __name__ == '__main__':
    sys.exit(run_smoke_test())
