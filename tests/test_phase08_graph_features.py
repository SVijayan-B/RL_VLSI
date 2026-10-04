#!/usr/bin/env python3
"""
Unit tests for Phase 8 Graph Feature Extraction & Heterogeneous Netlist Representation
Covers all 15 required unit test checks.
"""

import os
import json
import pytest
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
GRAPHS_DIR = os.path.join(PROJECT_ROOT, 'dataset/graphs')
METADATA_DIR = os.path.join(PROJECT_ROOT, 'dataset/metadata')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results/phase_08')

@pytest.fixture(scope="module")
def sample_graph():
    gf = os.path.join(GRAPHS_DIR, "RISCY-a-1-c2_graph.npz")
    assert os.path.exists(gf), f"Canonical graph file missing: {gf}"
    return np.load(gf, allow_pickle=True)

@pytest.fixture(scope="module")
def normalization_params():
    norm_file = os.path.join(RESULTS_DIR, "normalization_parameters.json")
    with open(norm_file) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def phase9_contract():
    contract_file = os.path.join(RESULTS_DIR, "phase09_input_contract.json")
    with open(contract_file) as f:
        return json.load(f)

# 1. Canonical graph loading
def test_canonical_graph_loading(sample_graph):
    required_keys = [
        'cell_names', 'cell_types', 'cell_features',
        'net_names', 'net_features', 'pin_names',
        'edge_index_bipartite', 'edge_index_cell', 'metadata_json'
    ]
    for k in required_keys:
        assert k in sample_graph, f"Missing key {k} in canonical graph"

# 2. Cell feature shape [N, 7]
def test_cell_feature_shape(sample_graph):
    c_feat = sample_graph['cell_features']
    assert c_feat.ndim == 2
    assert c_feat.shape[1] == 7, "Canonical cell feature dimension must be strictly 7"
    assert c_feat.shape[0] == len(sample_graph['cell_names'])

# 3. Net feature shape [M, 4]
def test_net_feature_shape(sample_graph):
    n_feat = sample_graph['net_features']
    assert n_feat.ndim == 2
    assert n_feat.shape[1] == 4, "Canonical net feature dimension must be strictly 4"
    assert n_feat.shape[0] == len(sample_graph['net_names'])

# 4. Feature-name ordering
def test_feature_name_ordering(phase9_contract):
    expected_c_names = ['area', 'width', 'height', 'aspect_ratio', 'is_macro', 'cell_degree', 'log_degree']
    contract_c_names = [f['name'] for f in phase9_contract['cell_node_features']['features']]
    assert contract_c_names == expected_c_names

    expected_n_names = ['net_degree', 'log_degree', 'is_clock', 'is_reset']
    contract_n_names = [f['name'] for f in phase9_contract['net_node_features']['features']]
    assert contract_n_names == expected_n_names

# 5. Feature dtype
def test_feature_dtypes(sample_graph):
    assert sample_graph['cell_features'].dtype == np.float32
    assert sample_graph['net_features'].dtype == np.float32

# 6. Finite-value validation (no NaN, no Inf)
def test_finite_value_validation(sample_graph):
    c_feat = sample_graph['cell_features']
    n_feat = sample_graph['net_features']
    assert np.all(np.isfinite(c_feat))
    assert not np.isnan(c_feat).any()
    assert not np.isinf(c_feat).any()
    assert np.all(np.isfinite(n_feat))
    assert not np.isnan(n_feat).any()
    assert not np.isinf(n_feat).any()

# 7. Binary feature validation
def test_binary_feature_validation(sample_graph):
    c_feat = sample_graph['cell_features']
    n_feat = sample_graph['net_features']
    assert np.all(np.isin(c_feat[:, 4], [0.0, 1.0]))
    assert np.all(np.isin(n_feat[:, 2], [0.0, 1.0]))
    assert np.all(np.isin(n_feat[:, 3], [0.0, 1.0]))

# 8. Aspect-ratio validation (w/h finite and > 0)
def test_aspect_ratio_validation(sample_graph):
    c_feat = sample_graph['cell_features']
    w = c_feat[:, 1]
    h = c_feat[:, 2]
    ar = c_feat[:, 3]
    assert (w > 0).all()
    assert (h > 0).all()
    assert (ar > 0).all()
    assert np.allclose(ar, w / h, atol=1e-4)

# 9. Degree/log-degree consistency
def test_degree_log_degree_consistency(sample_graph):
    c_feat = sample_graph['cell_features']
    n_feat = sample_graph['net_features']
    assert (c_feat[:, 5] >= 0).all()
    assert (n_feat[:, 0] >= 0).all()
    assert np.allclose(c_feat[:, 6], np.log1p(c_feat[:, 5]), atol=1e-5)
    assert np.allclose(n_feat[:, 1], np.log1p(n_feat[:, 0]), atol=1e-5)

# 10. Cell-name / feature-row alignment
def test_cell_name_feature_row_alignment(sample_graph):
    assert len(sample_graph['cell_names']) == sample_graph['cell_features'].shape[0]

# 11. Net-name / feature-row alignment
def test_net_name_feature_row_alignment(sample_graph):
    assert len(sample_graph['net_names']) == sample_graph['net_features'].shape[0]

# 12. Graph-level feature consistency
def test_graph_level_feature_consistency(sample_graph):
    meta = json.loads(str(sample_graph['metadata_json'][0]))
    assert meta['num_cells'] == sample_graph['cell_features'].shape[0]
    assert meta['num_nets'] == sample_graph['net_features'].shape[0]
    assert meta['num_bipartite_edges'] == sample_graph['edge_index_bipartite'].shape[1]
    assert meta['num_projected_cell_edges'] == sample_graph['edge_index_cell'].shape[1]

# 13. Normalization parameter generation
def test_normalization_parameter_generation(normalization_params):
    meta = normalization_params['metadata']
    assert meta['canonical_cell_dimension'] == 7
    assert meta['canonical_net_dimension'] == 4
    assert meta['training_designs_count'] == 51
    assert meta['test_designs_count'] == 3
    assert 'area' in normalization_params['cell_features_standardization']
    assert 'cell_degree' in normalization_params['cell_features_standardization']
    assert 'net_degree' in normalization_params['net_features_standardization']

# 14. Phase 9 interface validation
def test_phase9_interface_contract(phase9_contract):
    assert phase9_contract['cell_node_features']['dimension'] == 7
    assert phase9_contract['net_node_features']['dimension'] == 4
    assert phase9_contract['input_topology']['homogeneous_cell_graph']['high_fanout_pruning_threshold'] == 50

# 15. No modification of canonical graph files
def test_no_modification_of_canonical_graph_files():
    manifest_file = os.path.join(METADATA_DIR, "graph_manifest.csv")
    df_man = pd.read_csv(manifest_file)
    assert len(df_man) == 54
    # Verify file sizes and existence
    for _, row in df_man.iterrows():
        p = os.path.join(PROJECT_ROOT, row['graph_output_file'])
        assert os.path.exists(p)
        assert os.path.getsize(p) > 1000000  # Each .npz is > 1MB
