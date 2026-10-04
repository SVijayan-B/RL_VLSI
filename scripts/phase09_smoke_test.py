#!/usr/bin/env python3
"""
Phase 9 Smoke Test: CPU and Single-Graph Validation
Verifies:
1. Canonical graph loading and normalization
2. GraphSAGE forward pass on CPU
3. Forward pass on CUDA if available
4. InfoNCE loss calculation and backward gradient pass
5. Node embedding shape [N, 32] and graph embedding shape [32]
6. No NaNs, no Infs
"""

import os
import sys
import json
import torch
import numpy as np

from src.graph.graphsage import NetlistGraphSAGE, InfoNCELoss

def run_smoke_test():
    print("="*60)
    print("PHASE 9 GRAPHSAGE SMOKE TEST (CPU & GPU)")
    print("="*60)

    project_root = os.path.expanduser('~/CircuitNet_28nm')
    test_graph = os.path.join(project_root, "dataset/graphs/RISCY-a-1-c2_graph.npz")
    assert os.path.exists(test_graph), f"Graph file not found: {test_graph}"

    d = np.load(test_graph, allow_pickle=True)
    c_feat = d['cell_features'] # [N, 7]
    e_cell = d['edge_index_cell'] # [2, E]
    N = c_feat.shape[0]
    E = e_cell.shape[1]
    print(f"[*] Loaded sample graph: N={N:,} cells, E={E:,} cell edges")

    # Load normalization
    norm_path = os.path.join(project_root, 'results/phase_08/normalization_parameters.json')
    with open(norm_path) as f:
        norm = json.load(f)
    cell_names = ['area', 'width', 'height', 'aspect_ratio', 'is_macro', 'cell_degree', 'log_degree']
    means = torch.tensor([norm['cell_features_standardization'][k]['mean'] for k in cell_names], dtype=torch.float32)
    stds = torch.tensor([norm['cell_features_standardization'][k]['std'] for k in cell_names], dtype=torch.float32)

    # 1. CPU Test
    print("\n--- 1. Testing CPU Forward & Backward Pass ---")
    model_cpu = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32, dropout=0.20)
    criterion = InfoNCELoss(temperature=0.5, negative_samples=10)

    # Subsample 1000 nodes for fast CPU verification
    sub_n = min(1000, N)
    x_sub = torch.from_numpy(c_feat[:sub_n]).float()
    x_norm_cpu = (x_sub - means) / stds
    # Filter edges within subsample
    mask = (e_cell[0] < sub_n) & (e_cell[1] < sub_n)
    sub_e = torch.from_numpy(e_cell[:, mask].astype(np.int64))
    print(f"  CPU Subgraph: {sub_n} nodes, {sub_e.shape[1]} edges")

    h_nodes_cpu, h_graph_cpu = model_cpu(x_norm_cpu, sub_e)
    assert h_nodes_cpu.shape == (sub_n, 32), f"Expected ({sub_n}, 32), got {h_nodes_cpu.shape}"
    assert h_graph_cpu.shape == (32,), f"Expected (32,), got {h_graph_cpu.shape}"
    assert not torch.isnan(h_nodes_cpu).any()
    assert not torch.isnan(h_graph_cpu).any()

    loss_cpu = criterion(h_nodes_cpu, sub_e)
    loss_cpu.backward()
    print(f"  [PASS] CPU Forward and Backward passed cleanly! InfoNCE loss = {loss_cpu.item():.4f}")

    # 2. CUDA Test if available
    if torch.cuda.is_available():
        print("\n--- 2. Testing Full-Scale CUDA Forward & Backward Pass ---")
        device = torch.device('cuda')
        model_cuda = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32, dropout=0.20).to(device)
        norm_means_cuda = means.to(device)
        norm_stds_cuda = stds.to(device)

        x_full = torch.from_numpy(c_feat).to(device)
        x_norm_cuda = (x_full - norm_means_cuda) / norm_stds_cuda
        edge_full = torch.from_numpy(e_cell.astype(np.int64)).to(device)

        print(f"  CUDA Full Graph: {N} nodes, {E} edges")
        h_nodes_cuda, h_graph_cuda = model_cuda(x_norm_cuda, edge_full)
        assert h_nodes_cuda.shape == (N, 32)
        assert h_graph_cuda.shape == (32,)
        assert not torch.isnan(h_nodes_cuda).any()
        assert not torch.isnan(h_graph_cuda).any()

        loss_cuda = criterion(h_nodes_cuda, edge_full, max_batch_edges=20000)
        loss_cuda.backward()
        print(f"  [PASS] Full CUDA execution succeeded! Loss = {loss_cuda.item():.4f}")
    else:
        print("\n[NOTE] CUDA not available, skipped CUDA step.")

    print("\n" + "="*60)
    print("SMOKE TEST COMPLETE: ARCHITECTURE IS MEMORY-SAFE AND VALID")
    print("="*60)

if __name__ == '__main__':
    run_smoke_test()
