# Phase 8 — Phase 9 Interface Contract & Downstream Specification

**Document Version:** 1.0.0  
**Status:** LOCKED & FROZEN  
**Date:** 2026-10-03  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  
**Reference:** Agnesina et al., IEEE TCAD 2023  

---

## 1. Interface Scope

This document specifies the exact contract governing the interface between **Phase 8 (Graph Feature Extraction)** and **Phase 9 (GraphSAGE Architecture & Node Embeddings)**. 

Phase 9 must ingest graph topologies and feature arrays adhering strictly to this schema. Any deviation in dimensions or tensor layouts will violate system integrity.

---

## 2. Input Tensors & Shapes

For each design $d$ loaded from `dataset/graphs/{design_id}_graph.npz`:

### A. Cell Feature Matrix (`cell_features`)
- **Array Key:** `'cell_features'`
- **Tensor Shape:** $[N, 7]$ where $N$ is the number of cell instances (`cell_names`).
- **Data Type:** `torch.float32` (or `np.float32`).
- **Feature Dimension ($d_{\text{in}}$):** **EXACTLY 7**.
- **Feature Order:**
  1. `area`: Active silicon area ($w \times h$ in $\mu\text{m}^2$)
  2. `width`: Cell bounding box width ($\mu\text{m}$)
  3. `height`: Cell bounding box height ($\mu\text{m}$)
  4. `aspect_ratio`: Dimension ratio ($w / h$, unitless)
  5. `is_macro`: Binary flag ($1.0$ if macro/block, $0.0$ if std cell)
  6. `cell_degree`: Number of incident unrolled pins
  7. `log_degree`: $\log(1 + \text{cell\_degree})$

> **Strict Boundary Notice:**  
> The input dimension to GraphSAGE is **7**. Do not expect or pad with an arbitrary 8th feature.

### B. Graph Topology (`edge_index_cell`)
- **Array Key:** `'edge_index_cell'`
- **Tensor Shape:** $[2, E_{\text{cell}}]$ where $E_{\text{cell}}$ is the number of projected cell-to-cell undirected edges.
- **Data Type:** `torch.int64` (or `np.int32`).
- **Pruning Threshold:** Pre-pruned in Phase 2 at degree $\le 50$. No additional runtime edge filtering should be applied.

### C. Graph-Level Conditioning Vector ($\mathbf{g}$)
- **Source:** Loaded from `results/phase_08/graph_level_features.csv`
- **Vector Dimension:** 10 features (`num_cells`, `num_nets`, `num_pins`, `num_macros`, `total_cell_area`, `avg_net_degree`, `max_net_degree`, `bipartite_density`, `target_clock_period_ns`, `architecture_variant`).

---

## 3. Pre-Convolution Normalization

Prior to passing `cell_features` into GraphSAGE convolutional layers, the feature matrix must be standardized using the pre-calculated training parameters stored in:
`results/phase_08/normalization_parameters.json`

For feature $j \in \{0, \dots, 6\}$:
$$x_{u, j}^{\text{norm}} = \frac{x_{u, j} - \mu_j}{\sigma_j}$$
where $\mu_j, \sigma_j$ are fitted exclusively on the 51 training designs, preserving total test benchmark isolation.

---

## 4. Phase 9 Expected Output

In accordance with Section III.B of Agnesina et al.:
1. **Node Embeddings:** GraphSAGE must project each node $u$ into a **32-dimensional embedding space**:
   $$\mathbf{h}_u \in \mathbb{R}^{32}$$
2. **Graph-Level Embedding:** Obtained by permutation-invariant mean aggregation across all $N$ cells:
   $$\mathbf{h}_{\mathcal{G}} = \frac{1}{N} \sum_{u=1}^N \mathbf{h}_u \in \mathbb{R}^{32}$$
EOF
