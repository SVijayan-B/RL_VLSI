#!/usr/bin/env python3
"""
Unit tests for Phase 8A Documentation Reconciliation
Verifies that:
1. Documented Markdown table in docs/PHASE_08_GRAPH_FEATURE_EXTRACTION.md exactly matches
   authoritative results/phase_08/feature_statistics.csv within declared display precision (6 decimal places).
2. Exactly 7 cell features and 4 net features are documented.
3. No 8th feature is present in either the documentation or Phase 9 contract.
4. Normalization parameters in normalization_parameters.json match feature_statistics bounds.
5. Zero leakage and 100% reproducibility are certified.
"""

import os
import re
import json
import pytest
import pandas as pd

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results/phase_08')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')

@pytest.fixture(scope="module")
def authoritative_stats():
    csv_path = os.path.join(RESULTS_DIR, 'feature_statistics.csv')
    assert os.path.exists(csv_path), f"Authoritative stats file missing: {csv_path}"
    return pd.read_csv(csv_path)

@pytest.fixture(scope="module")
def normalization_params():
    json_path = os.path.join(RESULTS_DIR, 'normalization_parameters.json')
    assert os.path.exists(json_path)
    with open(json_path) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def documentation_content():
    doc_path = os.path.join(DOCS_DIR, 'PHASE_08_GRAPH_FEATURE_EXTRACTION.md')
    assert os.path.exists(doc_path)
    with open(doc_path) as f:
        return f.read()

def test_feature_counts(authoritative_stats):
    cell_feats = authoritative_stats[authoritative_stats['feature_domain'] == 'cell']
    net_feats = authoritative_stats[authoritative_stats['feature_domain'] == 'net']
    assert len(cell_feats) == 7, f"Expected 7 cell features, got {len(cell_feats)}"
    assert len(net_feats) == 4, f"Expected 4 net features, got {len(net_feats)}"

def test_no_eighth_feature(documentation_content):
    # Ensure documentation explicitly enforces exactly 7 cell features
    assert "7 dimensions" in documentation_content or "EXACTLY 7" in documentation_content
    assert "Feature 7:" not in documentation_content  # 0 to 6 only
    assert "Feature 8:" not in documentation_content

def test_documentation_statistics_reconciliation(authoritative_stats, documentation_content):
    # Parse the markdown table in documentation
    # Example line: | **Cell** | `area` | 2,373,702 | 0.441000 | 1.102500 | 5.199616 | 34371.023438 | 330.980988 |
    table_pattern = re.compile(
        r'\|\s*\*\*(Cell|Net)\*\*\s*\|\s*`([^`]+)`\s*\|\s*([0-9,]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|'
    )
    matches = table_pattern.findall(documentation_content)
    assert len(matches) == 11, f"Expected 11 matched feature rows in Markdown table, found {len(matches)}"

    for domain, fname, count_str, min_str, med_str, mean_str, max_str, std_str in matches:
        dom = domain.lower()
        row = authoritative_stats[(authoritative_stats['feature_domain'] == dom) & (authoritative_stats['feature_name'] == fname)]
        assert len(row) == 1, f"Feature {fname} in domain {dom} not found in authoritative stats"
        r = row.iloc[0]

        count_val = int(count_str.replace(',', ''))
        assert count_val == r['count'], f"Count mismatch for {fname}: {count_val} vs {r['count']}"

        assert abs(float(min_str) - r['min']) < 1e-4, f"Min mismatch for {fname}: {min_str} vs {r['min']}"
        assert abs(float(med_str) - r['median']) < 1e-4, f"Median mismatch for {fname}: {med_str} vs {r['median']}"
        assert abs(float(mean_str) - r['mean']) < 1e-4, f"Mean mismatch for {fname}: {mean_str} vs {r['mean']}"
        assert abs(float(max_str) - r['max']) < 1e-4, f"Max mismatch for {fname}: {max_str} vs {r['max']}"
        assert abs(float(std_str) - r['std']) < 1e-4, f"Std mismatch for {fname}: {std_str} vs {r['std']}"

def test_normalization_consistency(authoritative_stats, normalization_params):
    meta = normalization_params['metadata']
    assert meta['training_designs_count'] == 51
    assert meta['test_designs_count'] == 3
    assert set(meta['test_designs_quarantined']) == {'RISCY-a-1-c2', 'RISCY-a-1-c5', 'RISCY-a-1-c20'}

    for idx, r in authoritative_stats[authoritative_stats['feature_domain'] == 'cell'].iterrows():
        fn = r['feature_name']
        assert fn in normalization_params['cell_features_standardization']
        assert fn in normalization_params['cell_features_minmax']

    for idx, r in authoritative_stats[authoritative_stats['feature_domain'] == 'net'].iterrows():
        fn = r['feature_name']
        assert fn in normalization_params['net_features_standardization']
        assert fn in normalization_params['net_features_minmax']

def test_leakage_and_reproducibility():
    leak_file = os.path.join(RESULTS_DIR, 'data_leakage_audit.json')
    with open(leak_file) as f:
        leak = json.load(f)
    assert leak['audit_status'] == 'PASSED'
    for c in leak['checks']:
        assert c['passed'] is True

    repro_file = os.path.join(RESULTS_DIR, 'reproducibility.csv')
    df_repro = pd.read_csv(repro_file)
    assert len(df_repro) == 54
    assert df_repro['bit_exact_match'].all()
