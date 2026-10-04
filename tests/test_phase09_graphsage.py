import json
import os
import glob
import numpy as np
import pytest
import torch

from src.graph.graphsage import NetlistGraphSAGE, SAGEConvMean, InfoNCELoss

CONFIG_PATH = "configs/phase09_graphsage.json"
NORM_PATH = "results/phase_08/normalization_parameters.json"
GRAPH_EMB_PATH = "results/phase_09/graph_embeddings.csv"
CHECKPOINT_PATH = "results/phase_09/checkpoints/graphsage_best.pt"
TEST_BENCHMARKS = {"RISCY-a-1-c20", "RISCY-a-1-c2", "RISCY-a-1-c5"}


def test_01_input_dimension():
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
    assert cfg["input_dim"] == 7
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=16, out_dim=8)
    x = torch.randn(10, 7)
    edge_index = torch.zeros((2, 0), dtype=torch.long)
    h_nodes, h_graph = model(x, edge_index)
    assert h_nodes.shape == (10, 8)
    assert h_graph.shape == (8,)


def test_02_output_dimension():
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
    assert cfg["embedding_dim"] == 32
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    x = torch.randn(15, 7)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    h_nodes, h_graph = model(x, edge_index)
    assert h_nodes.shape == (15, 32)
    assert h_graph.shape == (32,)


def test_03_edge_index_shape_valid():
    sample_graph = "dataset/graphs/RISCY-a-1-c2_graph.npz"
    assert os.path.exists(sample_graph)
    data = np.load(sample_graph)
    edge_index = data["edge_index_cell"]
    assert edge_index.ndim == 2
    assert edge_index.shape[0] == 2
    assert edge_index.shape[1] > 0


def test_04_05_no_nan_no_inf():
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    model.eval()
    x = torch.randn(50, 7)
    edge_index = torch.randint(0, 50, (2, 100), dtype=torch.long)
    with torch.no_grad():
        h_nodes, h_graph = model(x, edge_index)
    assert not torch.isnan(h_nodes).any()
    assert not torch.isinf(h_nodes).any()
    assert not torch.isnan(h_graph).any()
    assert not torch.isinf(h_graph).any()


def test_06_node_ordering_preserved():
    sample_id = "RISCY-a-1-c2"
    graph_path = f"dataset/graphs/{sample_id}_graph.npz"
    emb_path = f"results/phase_09/node_embeddings/{sample_id}_node_embeddings.pt"
    assert os.path.exists(emb_path)
    
    g_data = np.load(graph_path, allow_pickle=True)
    g_cells = g_data["cell_names"]
    
    emb_data = torch.load(emb_path, map_location="cpu", weights_only=False)
    emb_cells = emb_data["cell_names"]
    
    assert len(g_cells) == len(emb_cells)
    assert np.array_equal(g_cells, emb_cells)
    assert emb_data["node_embeddings"].shape == (len(g_cells), 32)


def test_07_graph_pooling_shape():
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    model.eval()
    x = torch.randn(100, 7)
    edge_index = torch.randint(0, 100, (2, 200), dtype=torch.long)
    with torch.no_grad():
        h_nodes, h_graph = model(x, edge_index)
    assert h_graph.shape == (32,)
    expected_pool = h_nodes.mean(dim=0)
    assert torch.allclose(h_graph, expected_pool, atol=1e-6)


def test_08_checkpoint_reload_works():
    assert os.path.exists(CHECKPOINT_PATH)
    state_dict = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    assert isinstance(state_dict, dict)
    assert "conv1.lin_self.weight" in state_dict
    assert "conv2.lin_self.weight" in state_dict
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    model.load_state_dict(state_dict)
    assert model is not None


def test_09_inference_deterministic():
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    state_dict = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    
    x = torch.randn(30, 7)
    edge_index = torch.randint(0, 30, (2, 60), dtype=torch.long)
    
    with torch.no_grad():
        out1_n, out1_g = model(x, edge_index)
        out2_n, out2_g = model(x, edge_index)
    assert torch.equal(out1_n, out2_n)
    assert torch.equal(out1_g, out2_g)


def test_10_test_graphs_excluded_from_training():
    with open("results/phase_09/model_config.json", "r") as f:
        m_cfg = json.load(f)
        
    assert m_cfg["training_designs_count"] == 51
    quarantined = set(m_cfg["quarantined_test_designs"])
    assert quarantined == TEST_BENCHMARKS
    
    with open(NORM_PATH, "r") as f:
        norm = json.load(f)
    assert norm["metadata"]["training_designs_count"] == 51
    assert set(norm["metadata"]["test_designs_quarantined"]) == TEST_BENCHMARKS


def test_11_normalization_loaded_from_phase8():
    assert os.path.exists(NORM_PATH)
    with open(NORM_PATH, "r") as f:
        norm = json.load(f)
    cell_std = norm["cell_features_standardization"]
    assert len(cell_std) == 7
    for feat_name, stats in cell_std.items():
        assert "mean" in stats and "std" in stats
        assert stats["std"] > 0


def test_12_model_actually_uses_graph_edges():
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    state_dict = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    
    torch.manual_seed(42)
    x = torch.randn(40, 7)
    edge_index = torch.randint(0, 40, (2, 80), dtype=torch.long)
    empty_edges = torch.zeros((2, 0), dtype=torch.long)
    
    with torch.no_grad():
        out_graph, _ = model(x, edge_index)
        out_no_graph, _ = model(x, empty_edges)
        
    diff = (out_graph - out_no_graph).abs().max().item()
    assert diff > 1e-3, f"Model output did not change when edges were removed (diff={diff})!"
