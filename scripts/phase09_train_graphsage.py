#!/usr/bin/env python3
"""
Phase 9 GraphSAGE Training Pipeline
Project: Parameter Optimization of VLSI Placement Through Deep RL
Reference: Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, IEEE TCAD 2023

Training Protocol:
- Reads configs/phase09_graphsage.json
- Loads normalization parameters from results/phase_08/normalization_parameters.json
- Trains on 51 training designs; keeps 3 benchmark designs (RISCY-a-1-c2, RISCY-a-1-c5, RISCY-a-1-c20) strictly quarantined
- InfoNCE contrastive learning (K=10 negative samples, T=0.5 temperature)
- Memory-safe individual graph processing with edge subsampling for loss computation
- Saves training_history.csv, model checkpoints, node embeddings, and graph embeddings
"""

import os
import sys
import glob
import time
import json
import random
import numpy as np
import pandas as pd
import torch
import torch.optim as optim

from src.graph.graphsage import NetlistGraphSAGE, InfoNCELoss

PROJECT_ROOT = os.path.expanduser('~/CircuitNet_28nm')
GRAPHS_DIR = os.path.join(PROJECT_ROOT, 'dataset/graphs')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results/phase_09')
CHECKPOINTS_DIR = os.path.join(RESULTS_DIR, 'checkpoints')
NODE_EMB_DIR = os.path.join(RESULTS_DIR, 'node_embeddings')
TEST_EMB_DIR = os.path.join(RESULTS_DIR, 'test_embeddings')
FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # Enable deterministic algorithms where possible
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def load_normalization_parameters():
    norm_path = os.path.join(PROJECT_ROOT, 'results/phase_08/normalization_parameters.json')
    with open(norm_path) as f:
        norm = json.load(f)
    
    cell_names = ['area', 'width', 'height', 'aspect_ratio', 'is_macro', 'cell_degree', 'log_degree']
    means = np.array([norm['cell_features_standardization'][k]['mean'] for k in cell_names], dtype=np.float32)
    stds = np.array([norm['cell_features_standardization'][k]['std'] for k in cell_names], dtype=np.float32)
    # Ensure no division by zero
    stds[stds == 0.0] = 1.0
    return means, stds

def train_graphsage():
    t_start = time.time()
    config_path = os.path.join(PROJECT_ROOT, 'configs/phase09_graphsage.json')
    with open(config_path) as f:
        config = json.load(f)

    seed = config.get('seed', 42)
    set_seed(seed)

    device_str = config.get('device', 'cuda')
    device = torch.device(device_str if (device_str == 'cuda' and torch.cuda.is_available()) else 'cpu')
    print(f"[*] Initialized GraphSAGE training on device: {device}")
    if device.type == 'cuda':
        print(f"[*] CUDA Device: {torch.cuda.get_device_name(0)}")

    means, stds = load_normalization_parameters()
    norm_means = torch.tensor(means, device=device)
    norm_stds = torch.tensor(stds, device=device)

    # Identify training and held-out test designs
    quarantined = set(config.get('quarantined_test_designs', []))
    all_graph_files = sorted(glob.glob(os.path.join(GRAPHS_DIR, "*.npz")))
    
    train_graph_files = []
    test_graph_files = []
    for gf in all_graph_files:
        d_id = os.path.basename(gf).replace('_graph.npz', '')
        if d_id in quarantined:
            test_graph_files.append(gf)
        else:
            train_graph_files.append(gf)

    print(f"[*] Total graphs discovered: {len(all_graph_files)}")
    print(f"[*] Training graphs (51): {len(train_graph_files)}")
    print(f"[*] Held-out test graphs (3): {len(test_graph_files)} -> {[os.path.basename(f).replace('_graph.npz', '') for f in test_graph_files]}")
    assert len(train_graph_files) == 51, f"Expected 51 training graphs, got {len(train_graph_files)}"
    assert len(test_graph_files) == 3, f"Expected 3 test graphs, got {len(test_graph_files)}"

    # Instantiate Model & Loss
    model = NetlistGraphSAGE(
        in_dim=config.get('input_dim', 7),
        hidden_dim=config.get('hidden_dim', 64),
        out_dim=config.get('embedding_dim', 32),
        dropout=config.get('dropout', 0.20)
    ).to(device)

    criterion = InfoNCELoss(
        temperature=config.get('temperature', 0.5),
        negative_samples=config.get('negative_samples', 10)
    )

    optimizer = optim.Adam(
        model.parameters(),
        lr=config.get('learning_rate', 0.001),
        weight_decay=config.get('weight_decay', 1e-5)
    )

    epochs = config.get('epochs', 15)
    history_records = []
    best_loss = float('inf')

    print("\n" + "="*80)
    print("STARTING GRAPHSAGE UNSUPERVISED INFONCE TRAINING")
    print("="*80)

    for epoch in range(1, epochs + 1):
        t_epoch = time.time()
        model.train()
        total_epoch_loss = 0.0
        total_nodes = 0
        total_edges = 0

        # Shuffle training graphs order deterministically per epoch
        epoch_train_files = train_graph_files.copy()
        random.seed(seed + epoch)
        random.shuffle(epoch_train_files)

        for gf in epoch_train_files:
            d_id = os.path.basename(gf).replace('_graph.npz', '')
            d = np.load(gf, allow_pickle=True)
            
            c_feat = d['cell_features'] # [N, 7]
            e_cell = d['edge_index_cell'] # [2, E]

            N = c_feat.shape[0]
            E = e_cell.shape[1]
            total_nodes += N
            total_edges += E

            # Normalize features using Phase 8 parameters
            x = torch.from_numpy(c_feat).to(device)
            x_norm = (x - norm_means) / norm_stds

            edge_index = torch.from_numpy(e_cell.astype(np.int64)).to(device)

            optimizer.zero_grad()
            h_nodes, _ = model(x_norm, edge_index)

            # Compute InfoNCE loss
            loss = criterion(h_nodes, edge_index, max_batch_edges=20000)
            loss.backward()
            optimizer.step()

            total_epoch_loss += loss.item()

            # Clean memory
            del x, x_norm, edge_index, h_nodes, loss
            if device.type == 'cuda':
                torch.cuda.empty_cache()

        avg_loss = total_epoch_loss / len(epoch_train_files)
        elapsed_epoch = time.time() - t_epoch

        history_records.append({
            'epoch': epoch,
            'training_loss': round(avg_loss, 6),
            'learning_rate': optimizer.param_groups[0]['lr'],
            'number_of_graphs': len(epoch_train_files),
            'number_of_nodes': total_nodes,
            'number_of_edges': total_edges,
            'epoch_time_seconds': round(elapsed_epoch, 2),
            'seed': seed
        })

        print(f"Epoch {epoch:02d}/{epochs:02d} | Avg InfoNCE Loss: {avg_loss:.6f} | Time: {elapsed_epoch:.2f}s")

        # Save best checkpoint
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), os.path.join(CHECKPOINTS_DIR, "graphsage_best.pt"))

        # Save periodic checkpoint
        if epoch % config.get('checkpoint_frequency', 5) == 0:
            torch.save(model.state_dict(), os.path.join(CHECKPOINTS_DIR, f"graphsage_epoch_{epoch}.pt"))

    # Save final model
    torch.save(model.state_dict(), os.path.join(CHECKPOINTS_DIR, "graphsage_final.pt"))
    print(f"\n[+] Saved checkpoints to {CHECKPOINTS_DIR}")

    # Save training history CSV
    df_hist = pd.DataFrame(history_records)
    hist_csv = os.path.join(RESULTS_DIR, "training_history.csv")
    df_hist.to_csv(hist_csv, index=False)
    print(f"[+] Saved training history to {hist_csv}")

    # Save model config
    config_out = config.copy()
    config_out['best_loss'] = round(best_loss, 6)
    config_out['final_loss'] = round(history_records[-1]['training_loss'], 6)
    config_out['total_training_time_seconds'] = round(time.time() - t_start, 2)
    with open(os.path.join(RESULTS_DIR, "model_config.json"), "w") as f:
        json.dump(config_out, f, indent=2)

    # =========================================================================
    # INFERENCE: Generate Node & Graph Embeddings Across All 54 Designs
    # =========================================================================
    print("\n" + "="*80)
    print("GENERATING NODE & GRAPH EMBEDDINGS (INFERENCE)")
    print("="*80)
    # Load best model for inference
    model.load_state_dict(torch.load(os.path.join(CHECKPOINTS_DIR, "graphsage_best.pt")))
    model.eval()

    graph_embedding_records = []

    with torch.no_grad():
        for idx, gf in enumerate(all_graph_files):
            d_id = os.path.basename(gf).replace('_graph.npz', '')
            d = np.load(gf, allow_pickle=True)

            c_names = d['cell_names']
            c_feat = d['cell_features']
            e_cell = d['edge_index_cell']

            x = torch.from_numpy(c_feat).to(device)
            x_norm = (x - norm_means) / norm_stds
            edge_index = torch.from_numpy(e_cell.astype(np.int64)).to(device)

            h_nodes, h_graph = model(x_norm, edge_index)

            # Node embeddings: [N, 32]
            h_nodes_cpu = h_nodes.cpu()
            h_graph_cpu = h_graph.cpu().numpy()

            # Sanity checks
            assert h_nodes_cpu.shape == (len(c_names), 32)
            assert not torch.isnan(h_nodes_cpu).any()
            assert not torch.isinf(h_nodes_cpu).any()
            assert not np.isnan(h_graph_cpu).any()
            assert not np.isinf(h_graph_cpu).any()

            # Save node embeddings
            node_emb_payload = {
                'design_id': d_id,
                'cell_names': c_names,
                'node_embeddings': h_nodes_cpu,
                'shape': list(h_nodes_cpu.shape)
            }
            emb_file = os.path.join(NODE_EMB_DIR, f"{d_id}_node_embeddings.pt")
            torch.save(node_emb_payload, emb_file)

            # If held-out test design, also save copy in test_embeddings
            if d_id in quarantined:
                test_payload = node_emb_payload.copy()
                test_payload['split'] = 'HELD_OUT_TEST'
                test_file = os.path.join(TEST_EMB_DIR, f"{d_id}_test_embeddings.pt")
                torch.save(test_payload, test_file)

            # Record graph-level embedding
            row = {'design_id': d_id}
            for dim_idx in range(32):
                row[f'emb_{dim_idx}'] = float(h_graph_cpu[dim_idx])
            graph_embedding_records.append(row)

            if (idx + 1) % 10 == 0 or (idx + 1) == len(all_graph_files):
                print(f"  Processed inference for {idx+1}/54 designs ({d_id})...")

            del x, x_norm, edge_index, h_nodes, h_graph
            if device.type == 'cuda':
                torch.cuda.empty_cache()

    # Save graph_embeddings.csv (54 rows, 32 dims)
    df_graph_emb = pd.DataFrame(graph_embedding_records)
    df_graph_emb.sort_values(by='design_id', inplace=True)
    graph_emb_csv = os.path.join(RESULTS_DIR, "graph_embeddings.csv")
    df_graph_emb.to_csv(graph_emb_csv, index=False)
    print(f"[+] Saved 54-design graph embeddings to {graph_emb_csv}")

    total_time = time.time() - t_start
    print("\n" + "="*80)
    print(f"GRAPHSAGE TRAINING & INFERENCE COMPLETED IN {total_time:.2f}s")
    print("="*80)

if __name__ == '__main__':
    train_graphsage()
