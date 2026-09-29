# Phase 2 — Circuit Graph Construction & Validation Report
## Project: Parameter Optimization of VLSI Placement Through Deep RL
### Reference: Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, IEEE TCAD 2023

---

## 1. Objective

The primary objective of Phase 2 is to construct, validate, and standardize a canonical circuit-graph representation from the CircuitNet N28 dataset. This graph representation forms the foundational topological infrastructure that will subsequently be consumed by node feature embedding (GraphSAGE) and reinforcement learning (A2C placement parameter optimization).

This phase is strictly **infrastructure, feature specification, and validation**. No GraphSAGE training or reinforcement learning is performed in this phase.

---

## 2. Input Data

The inputs to Phase 2 are the verified, consolidated files established during Phase 1:
1. **`dataset/circuit_graph/node_attr/`:** 54 `.npy` files containing instance names and LEF cell types.
2. **`dataset/circuit_graph/net_attr/`:** 54 `.npy` files containing signal net identifiers.
3. **`dataset/circuit_graph/pin_attr/`:** 54 `.npy` files containing pin names, net indices, and node indices.
4. **`dataset/raw/circuitnet.lef`:** Standard-cell and macro physical library containing 915 macros, 18 layers, and the CoreSite grid.
5. **`dataset/metadata/netlist_manifest.csv`:** Baseline gate-level netlist metrics across all 54 designs.

---

## 3. Dataset Structure

An exhaustive inventory of the source graph files was conducted and recorded in [`dataset/metadata/graph_source_inventory.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_source_inventory.csv):
- **Completeness:** Exactly 54 of 54 designs possess all three components (`node_attr`, `net_attr`, and `pin_attr`).
- **Data Types:** All source arrays are NumPy object arrays with shape:
  - `node_attr`: Shape $(2 \times N_{\text{cells}})$
  - `net_attr`: Shape $(1 \times M_{\text{nets}})$
  - `pin_attr`: Shape $(3 \times P_{\text{pins}})$
- **Loading Protocol:** Source arrays contain strings and nested Python lists, requiring `np.load(path, allow_pickle=True)`.

---

## 4. Node, Net, and Pin Interpretation

Detailed inspection of the raw arrays revealed critical nuances in CircuitNet's data structure:

### `node_attr.npy`
- **Row 0 (Instance Names):** Full hierarchical instance path (e.g. `'clk_rst_gen_i/PLL_i'`, `'core_region_i/instr_mem/sp_ram_wrap_i/sp_ram_bank_i'`, `'FE_OCPC3547_FE_OFN0_rstn_int'`).
- **Row 1 (Cell Types):** Standard cell or macro library name matching `circuitnet.lef` (e.g. `'PLL'`, `'SRAM'`, `'DFCNQ_x1_0'`, `'INV_x2_0'`).

### `net_attr.npy`
- **Row 0 (Net Names):** Signal net identifier (e.g. `'clk'`, `'rst_n'`, `'axi_interconnect_i/n326'`).

### `pin_attr.npy`
A key technical finding was made regarding row semantics and multi-bit pins:
- **Row 0 (Pin Names):** Pin name on the instance (e.g. `'RCLK'`, `'Z'`, `'A'`, `'Q'`, `'RTSEL'`).
- **Row 1 (Net Index):** The index into `net_attr` ($0 \le \text{idx} < M_{\text{nets}}$). For scalar pins, this is a single integer. For multi-bit macro bus pins (e.g., 32-bit data bus `Q[31:0]`, 11-bit address bus `A[10:0]`, 2-bit test select `RTSEL[1:0]`), this is a Python `list` of net indices!
- **Row 2 (Node Index):** The integer index into `node_attr` ($0 \le \text{idx} < N_{\text{cells}}$) representing the cell instance to which the pin belongs.

*Handling Multi-Bit Pins:* To prevent data loss or crashes, each list in Row 1 is unrolled with its corresponding bit index (e.g. `'Q[0]'`, `'Q[1]'`, ..., `'Q[31]'`).

---

## 5. Canonical Graph Design

Circuit connectivity in physical design naturally forms a **hypergraph**, where each net connects a single driver pin to multiple sink pins across different cells. To preserve complete topological fidelity without arbitrary edge pruning:

### The Dual-Model Architecture
1. **Primary Ground Truth: Bipartite Graph $\mathcal{G}_{\text{bipartite}}$**
   - Independent cell nodes $\mathcal{V}_{cell}$ ($N$ instances) and net nodes $\mathcal{V}_{net}$ ($M$ nets).
   - Edges $\mathcal{E}_{\text{bipartite}}$ represent actual physical pin connections.
   - Directed and bidirectional traversal supported.
   - Preserved as the lossless source of truth.
2. **Projected Homogeneous Cell Graph $\mathcal{G}_{\text{cell}}$**
   - Standard GraphSAGE architectures require homogeneous message passing.
   - Edges connect cell $u$ to cell $w$ if they share a common net $v$.
   - **High-Fanout Pruning Threshold ($\le 50$):** Nets with degree $> 50$ (such as global clock nets with 3,661 sinks) are excluded from the cell-to-cell clique expansion to avoid generating $O(N^2)$ dense cliques while preserving local placement clustering.

Both representations are unified and exported in a single compressed archive per design: `dataset/graphs/{design_id}_graph.npz`.

---

## 6. Validation Methodology & Results

Every one of the 54 designs was subjected to an automated 20-point validation suite ([`src/graph/validate_graph.py`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/src/graph/validate_graph.py)):

### Validation Checks
1. Out-of-bounds node indices: **0 across all designs**
2. Out-of-bounds net indices: **0 across all designs**
3. Invalid or negative indices: **0 across all designs**
4. NaN or missing values: **0 across all designs**
5. Isolated cells ($\text{deg}=0$): **0 across all designs**
6. Empty nets ($\text{deg}=0$): **0 across all designs**
7. Missing LEF cell mappings: **0 across all designs (286/286 matched)**
8. Graph connectivity: **All 54 designs form a single connected component**

### Validation Summary
- **Total Graphs Processed:** 54
- **PASS:** 27 designs (Variant 'a')
- **WARN:** 27 designs (Variant 'b')
  - *Warning Explanation:* Each of the 27 variant-b designs has exactly 1 duplicate pin record in the raw dataset (the APB bus error pin `pslverr` on node 40533 is recorded twice). This is an authentic artifact of CircuitNet's raw extraction that does not impact graph connectivity or validity.
- **FAIL:** 0 designs (100% operational success)

---

## 7. LEF Cell Type Mapping

Using [`src/graph/lef_parser.py`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/src/graph/lef_parser.py), every cell type across all 54 designs was matched against `dataset/raw/circuitnet.lef`:
- **Unique Graph Cell Types:** 286
- **Matched in LEF:** **286 / 286 (100.0%)**
- **Extracted Attributes:** Bounding box width, height, active area ($\mu\text{m}^2$), placement site (`CoreSite`), and cell class (`CORE` vs `BLOCK` / `MACRO`).
- Documented in [`dataset/metadata/graph_lef_mapping.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_lef_mapping.csv).

---

## 8. Summary Statistics Across All 54 Designs

Extracted by [`src/graph/graph_features.py`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/src/graph/graph_features.py) and stored in [`results/phase_02/feature_summary.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_02/feature_summary.csv):

| Metric | Minimum | Mean | Maximum |
|---|---|---|---|
| **Cells per Design ($N$)** | 19,915 | 43,957.4 | 75,073 |
| **Nets per Design ($M$)** | 21,632 | 45,732.5 | 76,604 |
| **Bipartite Edges ($E_{\text{bip}}$)** | 80,360 | 177,260.3 | 295,107 |
| **Projected Cell Edges ($E_{\text{cell}}$)** | 402,890 | 912,410.6 | 1,532,840 |
| **Unique Cell Types** | 84 | 118.9 | 228 |
| **Total Active Cell Area ($\mu\text{m}^2$)** | 173,381.4 | 228,561.8 | 288,715.5 |
| **Average Net Degree** | 3.65 | 3.85 | 4.01 |
| **Max Net Degree (Clock)** | 303 | 1,370.2 | 3,661 |
| **Average Cell Degree** | 3.88 | 4.03 | 4.11 |

---

## 9. Output Deliverables & Storage

All 54 canonical graphs were generated and verified:
- **Location:** `dataset/graphs/{design_id}_graph.npz`
- **Total Storage:** **156.41 MB (~0.15 GB)**
- **Contents per `.npz` Archive:**
  - `cell_names`: String array $[N]$ of instance names
  - `cell_types`: String array $[N]$ of LEF macro names
  - `cell_features`: Float32 array $[N \times 7]$ (area, width, height, aspect ratio, is_macro, degree, log_degree)
  - `net_names`: String array $[M]$ of net identifiers
  - `net_features`: Float32 array $[M \times 4]$ (degree, log_degree, is_clock, is_reset)
  - `pin_names`: String array $[P]$ of unrolled pin labels
  - `edge_index_bipartite`: Int32 array $[2 \times E_{\text{bip}}]$ (cell $\leftrightarrow$ net)
  - `edge_index_cell`: Int32 array $[2 \times E_{\text{cell}}]$ (cell $\leftrightarrow$ cell)
  - `metadata_json`: JSON string encoding design metadata and parameter schema version (`2.0.0`)
- **Metadata Records:**
  - [`dataset/metadata/graph_manifest.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_manifest.csv) (54 rows)
  - [`dataset/metadata/graph_manifest.json`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_manifest.json)
  - [`dataset/metadata/graph_source_inventory.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_source_inventory.csv)
  - [`dataset/metadata/graph_validation.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_validation.csv)
  - [`dataset/metadata/graph_statistics.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_statistics.csv)
  - [`dataset/metadata/graph_lef_mapping.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/graph_lef_mapping.csv)

---

## 10. Reproducibility & Software Environment

- **Python Version:** `3.12.3`
- **Virtual Environment:** `~/envs/vlsi`
- **NumPy Version:** `2.5.3`
- **Pandas Version:** `3.0.6`
- **NetworkX Version:** `3.7`
- **SciPy Version:** `1.18.1`
- **OS:** Ubuntu 24.04 LTS (WSL2 Linux 5.15 x86_64)
- **Validation Command:**
  ```bash
  python3 -m src.graph.validate_graph --all
  ```

---

## 11. Relationship to Agnesina et al. (TCAD 2023)

In the reference paper, placement parameter optimization is driven by extracting netlist graph embeddings via GraphSAGE before reinforcement learning. Our Phase 2 implementation matches the reference structure:
- **Topology:** The heterogeneous bipartite netlist connectivity matches the graph definition in Section III.B of the paper.
- **Physical Features:** Cell dimensions and macro attributes derived from the TSMC 28nm LEF library provide geometric grounding for spatial clustering.
- **Scalability:** Net-degree thresholding prevents clique explosion on high-fanout global nets, enabling memory-efficient GNN neighborhood aggregation.

---

## 12. What is NOT Implemented Yet & Next Phase

- **NOT Implemented in Phase 2:** GraphSAGE training, neural network weights, reinforcement learning agents, OpenROAD baseline placements, and RL reward calculation.
- **Next Phase:** **PHASE 3 — Technology Library Strategy & Wire-Load Modeling**, followed by baseline physical placement setup (Phase 4).
