# Phase 2 — Circuit Graph Feature Specification
## Project: Parameter Optimization of VLSI Placement Through Deep RL
### Reference: Agnesina et al., IEEE TCAD 2023 / CircuitNet Dataset

---

## 1. Feature System Overview

This specification establishes the standardized schema for graph-structured features extracted from CircuitNet N28. In accordance with the methodology of Agnesina et al. (IEEE TCAD 2023), physical placement parameter optimization requires a graph representation that simultaneously captures:
1. **Gate-level netlist connectivity:** How standard cells and functional macros exchange signals.
2. **Physical geometric attributes:** Cell dimensions, areas, and aspect ratios defined by the technology library (`circuitnet.lef`).
3. **Topological centrality & fanout:** Net degree distributions and cell pin connectivity.

To avoid arbitrary feature engineering, every feature in this specification is derived directly from verified data sources (`node_attr`, `net_attr`, `pin_attr`, `circuitnet.lef`) and has an explicit architectural justification.

---

## 2. Cell Node Features ($\mathcal{V}_{cell}$)

Each cell instance node $u \in \mathcal{V}_{cell}$ ($N$ nodes per design) has a feature vector $\mathbf{x}_u \in \mathbb{R}^7$:

| Index | Feature Name | Source | Mathematical Definition | Dtype | Normalization | Missing-Value Handling | Reason for Inclusion |
|---|---|---|---|---|---|---|---|
| **0** | `area` | `circuitnet.lef` | $w_u \times h_u$ ($\mu\text{m}^2$) | `float32` | Standard score / Min-Max $[0, 1]$ | Default to $0.84 \times 1.05 = 0.882$ (1-pitch inverter) | Primary driver of placement area demand and core congestion. |
| **1** | `width` | `circuitnet.lef` | Bounding box width $w_u$ ($\mu\text{m}$) | `float32` | Divided by CoreSite width ($0.21\,\mu\text{m}$) | Default to $0.84\,\mu\text{m}$ (4 sites) | Reflects standard-cell horizontal span and track blockage. |
| **2** | `height` | `circuitnet.lef` | Bounding box height $h_u$ ($\mu\text{m}$) | `float32` | Divided by CoreSite height ($1.05\,\mu\text{m}$) | Default to $1.05\,\mu\text{m}$ (1 row) | Distinguishes multi-row macros (SRAM, PLL) from standard cells. |
| **3** | `aspect_ratio` | Derived | $w_u / h_u$ | `float32` | Log-transformed: $\log(w_u / h_u)$ | Default to $0.80$ | Critical for floorplanning and aspect ratio parameter ($AR$). |
| **4** | `is_macro` | `node_attr` / LEF | $\mathbb{I}(c_u \in \{\text{SRAM, PLL, ROM}\} \lor \text{CLASS}=\text{BLOCK})$ | `float32` | Binary $\{0.0, 1.0\}$ | Default to $0.0$ | Macros dominate floorplan whitespace, halo margin $m$, and pin congestion. |
| **5** | `cell_degree` | `pin_attr` | $\text{deg}(u) = \sum_{e \in \mathcal{E}} \mathbb{I}(u \in e)$ | `float32` | Divided by max degree ($\approx 100$) | Default to $0$ | Number of connected signal nets; indicates high-connectivity hubs. |
| **6** | `log_degree` | Derived | $\log(1 + \text{deg}(u))$ | `float32` | None (naturally bounded $[0, 5]$) | Default to $0.0$ | Compress heavy-tailed degree distribution for stable neural gradient flow. |

---

## 3. Net Node Features ($\mathcal{V}_{net}$)

In the canonical bipartite graph representation, each net $v \in \mathcal{V}_{net}$ ($M$ nodes per design) has a feature vector $\mathbf{z}_v \in \mathbb{R}^4$:

| Index | Feature Name | Source | Mathematical Definition | Dtype | Normalization | Missing-Value Handling | Reason for Inclusion |
|---|---|---|---|---|---|---|---|
| **0** | `net_degree` | `pin_attr` | $\text{deg}(v) = \sum_{p \in \mathcal{P}} \mathbb{I}(\text{net}(p) = v)$ | `float32` | Divided by 100 or global max | Default to $0$ | Fanout degree; primary predictor of HPWL (half-perimeter wirelength) and routing demand. |
| **1** | `log_degree` | Derived | $\log(1 + \text{deg}(v))$ | `float32` | None | Default to $0.0$ | Linearizes exponential distribution of global clocks vs local nets. |
| **2** | `is_clock` | `net_attr` | $\mathbb{I}(\text{'clk'} \in \text{name}_v \lor \text{'clock'} \in \text{name}_v)$ | `float32` | Binary $\{0.0, 1.0\}$ | Default to $0.0$ | Clock nets dictate clock tree synthesis (CTS) and placement effort $p$. |
| **3** | `is_reset` | `net_attr` | $\mathbb{I}(\text{'rst'} \in \text{name}_v \lor \text{'reset'} \in \text{name}_v)$ | `float32` | Binary $\{0.0, 1.0\}$ | Default to $0.0$ | High-fanout asynchronous control signals affecting timing and buffer insertion. |

---

## 4. Edge Representations ($\mathcal{E}$)

The canonical representation provides two complementary edge schemas stored in each design's `.npz` archive:

### A. Canonical Bipartite Edges (`edge_index_bipartite`)
- **Structure:** $[2 \times E_{bipartite}]$ directed/undirected edges connecting Cell Node $u$ and Net Node $v$.
- **Edge Attribute:** Pin functional label (e.g. `'A1'`, `'Z'`, `'RTSEL[0]'`, `'Q[31]'`).
- **Semantic Fidelity:** 100% loss-free representation of the exact circuit hypergraph.

### B. Projected Cell-to-Cell Edges (`edge_index_cell`)
- **Structure:** $[2 \times E_{cell}]$ homogeneous edges connecting Cell Node $u$ and Cell Node $w$ sharing a net.
- **High-Fanout Threshold Filter:** Nets with $\text{deg}(v) > 50$ (such as global clock trees, global reset, and test enable lines) are excluded from the cell-to-cell clique expansion.
  - *Rationale:* Expanding a 3,661-fanout clock net into a full clique would generate $\binom{3661}{2} \approx 6.7 \times 10^6$ edges for a single net, destroying GraphSAGE sparsity and neighborhood sampling efficiency.
  - Standard CAD practice in placement engines (e.g., hMETIS, SimPL, ePlace) thresholds global nets at degree 50–100.
- **Edge Weight (Derived):** $w_{uw} = \sum_{v \in \text{shared}(u,w)} \frac{1}{\text{deg}(v) - 1}$ (Standard VLSI clique-model wirelength weighting).

---

## 5. Graph-Level Global Features ($\mathbf{g} \in \mathbb{R}^{10}$)

Used by the RL policy / value network to condition parameter selection on design scale:

1. `num_cells`: Total standard cell and macro count $N$.
2. `num_nets`: Total signal net count $M$.
3. `num_pins`: Total pin connections $P$.
4. `num_macros`: Large functional macro count (1, 2, or 3).
5. `total_cell_area`: Total active silicon footprint ($\mu\text{m}^2$).
6. `avg_net_degree`: Mean net degree $\bar{d}_{net}$.
7. `max_net_degree`: Global clock network fanout.
8. `bipartite_density`: Ratio $\frac{E}{N \times M}$.
9. `target_clock_period_ns`: Target clock constraint (`2.0`, `5.0`, or `20.0` ns).
10. `architecture_variant`: Categorical encoding of core architecture (`RISCY-FPU`, `RISCY`, `zero-riscy`).

---

## 6. Schema Versioning & Compatibility

- **Feature Schema Version:** `2.0.0`
- **Output Storage:** `dataset/graphs/{design_id}_graph.npz`
- **Downstream Consumers:**
  - GraphSAGE representation learning (Phase 8 & 9)
  - Placement state formulation & reward normalization (Phase 10 & 11)
