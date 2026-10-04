# Phase 9: GraphSAGE Architecture & Node Embeddings

## 1. Objective

Phase 9 implements and validates the GraphSAGE representation-learning stage for the **Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning** project, reproducing and adapting the methodology of **Agnesina et al., IEEE TCAD 2023** on the open **CircuitNet N28** dataset.

The core dataflow is:
```
CircuitNet N28 Canonical Graph
        ↓
7-dimensional Cell Features [N, 7]
        ↓
Standardization via Phase 8 Frozen Statistics
        ↓
2-Layer GraphSAGE with Mean Aggregation
        ↓
32-dimensional Cell Node Embeddings [N, 32]
        ↓
Permutation-Invariant Global Mean Pooling
        ↓
32-dimensional Graph Embedding [32]
```

**Scope Boundary**: Phase 9 is strictly graph representation learning. No reinforcement learning algorithms (A2C/PPO), RL rewards, OpenROAD invocations, placement parameter adjustments, or downstream policy heads are implemented in this phase.

---

## 2. Relationship to Agnesina et al. (IEEE TCAD 2023)

To maintain rigorous scientific fidelity, the exact origins and adaptations are categorized below:

| Feature / Protocol Component | Status | Details / Reference |
| :--- | :--- | :--- |
| **GraphSAGE Architecture** | DIRECTLY FROM PAPER | 2-layer GraphSAGE using mean aggregation, hidden dim = 64, output embedding dim = 32. |
| **Graph Pooling** | DIRECTLY FROM PAPER | Permutation-invariant mean pooling: $h_G = \frac{1}{N}\sum_{v=1}^N h_v$. |
| **Node Embedding Dimension** | DIRECTLY FROM PAPER | Node embedding dimension $d = 32$. |
| **Unsupervised Training Objective**| DIRECTLY FROM PAPER / ADAPTED | Unsupervised contrastive InfoNCE loss over connected neighbor node pairs vs. $K=10$ random negatives at temperature $T=0.5$. |
| **Input Cell Features** | ADAPTED FOR CIRCUITNET N28 | 7 cell features derived from CircuitNet N28 DEF/LEF standard cells (Area, Width, Height, Aspect Ratio, Is-Macro, Degree, Log-Degree). |
| **Graph Topology** | PROJECT IMPLEMENTATION CHOICE | Projected cell graph `edge_index_cell` ($[2, E_{\text{cell}}]$) constructed under Phase 2 policy (net degree $\le 50$ clique expanded; nets $> 50$ excluded). |
| **Normalization Protocol** | PROJECT IMPLEMENTATION CHOICE | Z-score standardization fitted strictly on 51 training designs and locked in `results/phase_08/normalization_parameters.json`. |

---

## 3. Input Graph & Feature Schema

The implementation strictly consumes inputs adhering to the Phase 8 contract (`results/phase_08/phase09_input_contract.json`):
1. **Graph Files**: `dataset/graphs/{design_id}_graph.npz` across all 54 canonical designs.
2. **Cell Feature Matrix**: Key `cell_features`, shape $[N, 7]$, `float32`.
   - `[0]`: Area ($\mu m^2$)
   - `[1]`: Width ($\mu m$)
   - `[2]`: Height ($\mu m$)
   - `[3]`: Aspect Ratio (width / height)
   - `[4]`: Is-Macro (binary indicator: 1.0 if macro, 0.0 standard cell)
   - `[5]`: Cell Degree (connected unrolled signal pin count)
   - `[6]`: Log Degree ($\log(1 + \text{cell\_degree})$)
3. **Graph Topology**: Key `edge_index_cell`, shape $[2, E_{\text{cell}}]$, `int32`, representing undirected cell-to-cell projected edges. No runtime graph alteration or pruning was performed.
4. **Cell Order**: Ingested and preserved identically according to `cell_names` ($[N]$).

---

## 4. Normalization & Data Split Integrity

### 4.1 Normalization
Normalization parameters were loaded directly from `results/phase_08/normalization_parameters.json` and applied via:
$$x_{\text{norm}} = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}$$
These statistics were fitted **exclusively on the 51 training designs**. No test data, batch statistics, or individual design standardizations were used.

### 4.2 Data Split & Test Quarantine
- **Training Designs (51 designs)**: Used for contrastive parameter optimization.
- **Held-Out Test Benchmarks (3 designs)**:
  - `RISCY-a-1-c20`
  - `RISCY-a-1-c2`
  - `RISCY-a-1-c5`
- **Quarantine Guarantee**: Zero gradient updates, zero loss evaluation, and zero normalization statistics were derived from the 3 test benchmark designs. Their embeddings were produced purely through forward inference after training completion and archived under `results/phase_09/test_embeddings/`.

---

## 5. Model Architecture & Neighborhood Aggregation

### 5.1 Architecture Details
```
Input: x in R^{N x 7}
  │
  ▼
SAGEConvMean Layer 1:
  h^{(1)}_v = W_{\text{self}}^{(1)} h_v + W_{\text{neigh}}^{(1)} \cdot \text{mean}_{u \in \mathcal{N}(v)}(h_u) + b^{(1)}
  Dimensions: 7 -> 64
  Nonlinearity: ReLU
  Dropout: 0.20 (active during training only)
  │
  ▼
SAGEConvMean Layer 2:
  h^{(2)}_v = W_{\text{self}}^{(2)} h^{(1)}_v + W_{\text{neigh}}^{(2)} \cdot \text{mean}_{u \in \mathcal{N}(v)}(h^{(1)}_u) + b^{(2)}
  Dimensions: 64 -> 32
  Nonlinearity: ReLU
  │
  ▼
Node Embeddings: H in R^{N x 32}
  │
  ▼
Global Permutation-Invariant Mean Pooling:
  h_G = (1/N) sum_{v=1}^N h^{(2)}_v in R^{32}
```

### 5.2 Aggregation Guarantees
- Neighborhood aggregation uses vector index accumulation (`index_add_`) normalized by exact destination in-degree, ensuring true message passing.
- Isolated nodes (degree 0) retain self-projected embeddings without NaN/Inf generation.
- No global pooling is performed prior to the second convolutional layer.

---

## 6. Training Objective & Contrastive Learning

Unsupervised representation learning was conducted via an InfoNCE contrastive objective:
$$\mathcal{L} = -\sum_{(u, v) \in \mathcal{E}} \log \frac{\exp(\text{sim}(h_u, h_v) / \tau)}{\exp(\text{sim}(h_u, h_v) / \tau) + \sum_{k=1}^K \exp(\text{sim}(h_u, n_k) / \tau)}$$

- **Positive Pairs**: True edges $(u, v)$ from `edge_index_cell`.
- **Negative Samples ($K=10$)**: Randomly sampled node indices $n_k \in \{0, \dots, N-1\}$.
- **Temperature ($\tau$)**: 0.5.
- **Similarity Metric**: Cosine similarity $\text{sim}(a, b) = \frac{a^\top b}{\|a\|_2 \|b\|_2}$.
- **Memory Safety**: For graph scalability with edge counts exceeding $10^6$, positive edges per graph were dynamically subsampled to a memory-safe batch limit of 20,000 edges per optimization step.

---

## 7. Hyperparameter Configuration

Central configuration stored at `configs/phase09_graphsage.json`:
```json
{
  "seed": 42,
  "input_dim": 7,
  "hidden_dim": 64,
  "embedding_dim": 32,
  "dropout": 0.20,
  "aggregation": "mean",
  "negative_samples": 10,
  "temperature": 0.5,
  "learning_rate": 0.001,
  "weight_decay": 1e-5,
  "epochs": 15,
  "device": "cuda",
  "checkpoint_frequency": 5,
  "high_fanout_pruning_threshold": 50
}
```

---

## 8. Hardware & Training Dynamics

- **Hardware**: NVIDIA GeForce RTX 3050 6GB Laptop GPU (PyTorch 2.6.0+cu124, CUDA 12.4).
- **Execution Time**: 15 epochs across 51 training designs completed in **73.43 seconds** ($\approx 4.89\text{s}$ per epoch).
- **Training Trajectory**:
  - Epoch 01: InfoNCE Loss = **1.789532**
  - Epoch 05: InfoNCE Loss = **1.411603**
  - Epoch 10: InfoNCE Loss = **1.352467**
  - Epoch 15: InfoNCE Loss = **1.318038** (Best & Final Loss)
- **Monotonic Convergence**: Loss decreased smoothly without NaN, Inf, or gradient divergence.

---

## 9. Embedding Artifacts & Statistics

### 9.1 Generated Files
- `results/phase_09/checkpoints/`:
  - `graphsage_best.pt`
  - `graphsage_final.pt`
  - Periodic checkpoints (`graphsage_epoch_5.pt`, `graphsage_epoch_10.pt`, `graphsage_epoch_15.pt`)
- `results/phase_09/node_embeddings/`: 54 `.pt` files containing node embeddings $[N, 32]$ and `cell_names` mapping.
- `results/phase_09/test_embeddings/`: Dedicated archive of 3 held-out test benchmarks (`RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`).
- `results/phase_09/graph_embeddings.csv`: 54 rows $\times$ 33 columns (`design_id`, `emb_0` through `emb_31`).
- `results/phase_09/training_history.csv`: Per-epoch logs (loss, lr, graph count, node count, edge count, elapsed time).
- `results/phase_09/reproducibility.csv`: Deterministic reproduction audit across all 54 designs.
- `results/phase_09/figures/`:
  - `training_loss_curve.png`
  - `embedding_norm_distribution.png`
  - `graph_embeddings_pca.png`
  - `cosine_similarity_matrix.png`

### 9.2 Embedding Properties
- **Total Cells Embedded**: 2,373,702 cells across 54 designs.
- **Mean L2 Norm**: 0.1758 (std: 0.0543, min: 0.0717, max: 0.3547).
- **Pairwise Cosine Similarity**: Mean = 0.7715, Min = 0.4268, Max = 1.0000.
- **PCA Explained Variance**: PC1 = 78.43%, PC2 = 18.46% (cumulative 2-component variance = 96.89%).
- **Architecture Group Observation**: Embeddings exhibit continuous manifold alignment driven by design scale and cell counts rather than discrete disjoint clustering.

---

## 10. Implementation Sanity & Ablation Verification

To confirm that GraphSAGE genuinely processes graph topology and features rather than collapsing to an unconditioned projection:
1. **Feature-Shuffled Input**: Evaluating graph representations after randomly permuting input cell feature vectors dropped cosine similarity with canonical embeddings to **0.3050**.
2. **Empty Edge Topology**: Evaluating graph representations with all edges removed dropped cosine similarity to **0.2266**.
3. **Conclusion**: The GraphSAGE model strongly and dynamically responds to both cell attribute values and netlist topology.

---

## 11. Deterministic Reproducibility Audit

A dual-pass inference audit was conducted across all 54 designs reloading `graphsage_best.pt` under fixed seed 42:
- **Max Absolute Difference**: $0.000000$ across all 54 designs.
- **Mean Absolute Difference**: $0.000000$ across all 54 designs.
- **Reproducibility Status**: **54 / 54 PASS (100% Bit-Exact Determinism)**.

---

## 12. Verification & Test Suite Summary

The comprehensive pytest suite (`tests/test_phase09_graphsage.py`) passed all 11 unit tests:
1. `test_01_input_dimension`: PASSED
2. `test_02_output_dimension`: PASSED
3. `test_03_edge_index_shape_valid`: PASSED
4. `test_04_05_no_nan_no_inf`: PASSED
5. `test_06_node_ordering_preserved`: PASSED
6. `test_07_graph_pooling_shape`: PASSED
7. `test_08_checkpoint_reload_works`: PASSED
8. `test_09_inference_deterministic`: PASSED
9. `test_10_test_graphs_excluded_from_training`: PASSED
10. `test_11_normalization_loaded_from_phase8`: PASSED
11. `test_12_model_actually_uses_graph_edges`: PASSED

Full repository regression test suite (`tests/`): **31 / 31 tests PASSED**.

---

## 13. Phase 10 Readiness Contract

Graph representation learning is frozen. The downstream Phase 10 RL environment may consume:
- Canonical graph embeddings `results/phase_09/graph_embeddings.csv` ($[32]$ dimensional state conditioning vector $h_G$).
- Canonical node embeddings `results/phase_09/node_embeddings/{design_id}_node_embeddings.pt` ($[N, 32]$ cell representations).
- Checkpoint `results/phase_09/checkpoints/graphsage_best.pt` for zero-shot test evaluation.
