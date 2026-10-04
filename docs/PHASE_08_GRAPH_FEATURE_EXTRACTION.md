# Phase 8 — Graph Feature Extraction & Heterogeneous Netlist Representation Report

**Document Version:** 1.1.0 (Phase 8A Documentation Reconciled)  
**Status:** COMPLETE (100% Validated & Frozen)  
**Date:** 2026-10-03  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  
**Reference Paper:** Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, *"Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning,"* IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems (TCAD), 2023.

---

## 1. Objective & Research Scope

The primary objective of Phase 8 is to finalize, audit, statistically profile, and freeze the graph feature representations derived from the CircuitNet N28 dataset. This representation forms the topological and geometric foundation that will subsequently be consumed by the **GraphSAGE representation learning model in Phase 9**.

### Strict Scientific Boundaries:
- **No Model Training:** Phase 8 is strictly feature engineering, audit, and interface formulation. No GraphSAGE models, neighborhood aggregators, or reinforcement learning policies were trained.
- **No Data Fabrication:** All features originate from authenticated LEF physical dimensions (`circuitnet.lef`) and unrolled netlist connectivity (`node_attr`, `net_attr`, `pin_attr`).
- **No Alteration of Prior Phases:** All results, baseline metrics ($731,162.90\,\mu\text{m}$), and parameter spaces from Phases 1–7 remain frozen.

---

## 2. Relationship to Agnesina et al. (IEEE TCAD 2023)

In the reference paper by Agnesina et al., placement parameter optimization conditions RL state representations on learned netlist embeddings:
- **Paper Specification:** "Simple node features include concepts such as degree, fanout, area, and encoded gate type. GraphSAGE produces 32-dimensional node embeddings, which are then aggregated by permutation-invariant mean pooling into a fixed-length graph-level context vector." (Section III.B).
- **Adaptation Realities:** In CircuitNet N28, timing tables (`.lib`) are withheld for IP protection, preventing precise timing-arc/capacitance extraction without fabrication. Therefore, our standard cell representation captures full geometric bounding boxes (width, height, area, aspect ratio) and topological centrality (cell degree, log degree, macro classification) to ground spatial clustering.

---

## 3. Canonical Graph Representation

The graph infrastructure defines two complementary representations stored inside `dataset/graphs/{design_id}_graph.npz`:
1. **Lossless Heterogeneous Bipartite Graph ($\mathcal{G}_{\text{bipartite}}$):**
   - $\mathcal{V}_{\text{cell}}$: Standard cell and macro instance nodes ($N$).
   - $\mathcal{V}_{\text{net}}$: Signal net nodes ($M$).
   - $\mathcal{E}_{\text{bipartite}}$: Lossless pin connections connecting cell $u$ and net $v$. Shape: $[2, P]$.
   - Total across 54 designs: $9,572,055$ pin connections.
2. **Projected Homogeneous Cell Graph ($\mathcal{G}_{\text{cell}}$):**
   - Connects cell $u$ and cell $w$ if they share a common net $v$.
   - **High-Fanout Pruning Threshold ($\le 50$):** Nets with degree $> 50$ (such as global clock nets with up to 3,661 sinks) are excluded from clique expansion to prevent dense $O(N^2)$ subgraph explosion.
   - Total across 54 designs: $54,342,544$ cell-cell edges.

---

## 4. Feature Schemas

### A. Canonical Cell Node Features ($\mathbf{x}_u \in \mathbb{R}^7$)
The schema is strictly **7 dimensions**:
- Feature 0: `area` ($w \times h$ in $\mu\text{m}^2$)
- Feature 1: `width` (bounding box width in $\mu\text{m}$)
- Feature 2: `height` (bounding box height in $\mu\text{m}$)
- Feature 3: `aspect_ratio` ($w / h$, unitless)
- Feature 4: `is_macro` (binary indicator: $1.0$ for block/macro, $0.0$ for standard cell)
- Feature 5: `cell_degree` (unrolled pin connectivity count)
- Feature 6: `log_degree` ($\log(1 + \text{cell\_degree})$)

### B. Canonical Net Features ($\mathbf{z}_v \in \mathbb{R}^4$)
- Feature 0: `net_degree` (fanout pin count)
- Feature 1: `log_degree` ($\log(1 + \text{net\_degree})$)
- Feature 2: `is_clock` (binary indicator for clock nets)
- Feature 3: `is_reset` (binary indicator for reset nets)

### C. Graph-Level Conditioning Features ($\mathbf{g} \in \mathbb{R}^{10}$)
Recorded deterministically in `results/phase_08/graph_level_features.csv`:
`num_cells`, `num_nets`, `num_pins`, `num_macros`, `total_cell_area`, `avg_net_degree`, `max_net_degree`, `bipartite_density`, `target_clock_period_ns`, `architecture_variant`.

---

## 5. Summary Statistics Across All 54 Designs

Directly reconciled from authoritative computational artifact `results/phase_08/feature_statistics.csv` (display precision: 6 decimal places):

| Domain | Feature Name | Count | Min | Median | Mean | Max | Std Dev |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cell** | `area` | 2,373,702 | 0.441000 | 1.102500 | 5.199616 | 34371.023438 | 330.980988 |
| **Cell** | `width` | 2,373,702 | 0.420000 | 1.050000 | 1.584666 | 242.707504 | 2.581250 |
| **Cell** | `height` | 2,373,702 | 1.050000 | 1.050000 | 1.070121 | 183.660004 | 1.594055 |
| **Cell** | `aspect_ratio` | 2,373,702 | 0.400000 | 1.000000 | 1.483433 | 7.200000 | 1.166965 |
| **Cell** | `is_macro` | 2,373,702 | 0.000000 | 0.000000 | 0.000205 | 1.000000 | 0.014322 |
| **Cell** | `cell_degree` | 2,373,702 | 1.000000 | 4.000000 | 4.032543 | 936.000000 | 4.040965 |
| **Cell** | `log_degree` | 2,373,702 | 0.693147 | 1.609438 | 1.580152 | 6.842683 | 0.250716 |
| **Net** | `net_degree` | 2,469,557 | 1.000000 | 2.000000 | 3.876021 | 3661.000000 | 12.716327 |
| **Net** | `log_degree` | 2,469,557 | 0.693147 | 1.098612 | 1.357285 | 8.205765 | 0.488446 |
| **Net** | `is_clock` | 2,469,557 | 0.000000 | 0.000000 | 0.004326 | 1.000000 | 0.065629 |
| **Net** | `is_reset` | 2,469,557 | 0.000000 | 0.000000 | 0.001831 | 1.000000 | 0.042747 |

*Distribution of binary indicators across population:*
- `is_macro`: 2,373,215 standard cells (99.98%), 487 macros (0.02%).
- `is_clock`: 2,458,874 non-clock nets (99.57%), 10,683 clock nets (0.43%).
- `is_reset`: 2,465,036 non-reset nets (99.82%), 4,521 reset nets (0.18%).

---

## 6. Normalization Strategy & Zero-Leakage Quarantine

To prepare for Phase 9 without data leakage:
- Normalization parameters are stored in `results/phase_08/normalization_parameters.json`.
- Parameters were fitted strictly on the **51 training designs**.
- The **3 benchmark evaluation designs** (`RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`) were quarantined.
- Standard $z$-score and min-max bounds are provided for each feature.

---

## 7. Data Leakage Audit

A comprehensive leakage audit was conducted (`results/phase_08/data_leakage_audit.json`):
- [x] No future placement coordinates ($x, y$) in graph features.
- [x] No OpenROAD DPL displacement or runtime metrics in features.
- [x] No Phase 7 parameter sweep outcomes or RL reward signals in features.
- [x] Zero test-design parameter leakage during normalization fitting.

---

## 8. Reproducibility & Validation

- **Reproducibility:** A full second pass across all 54 designs produced bit-exact matches (`results/phase_08/reproducibility.csv`: 54/54 PASS).
- **Unit Test Suite:** All 15 tests in `tests/test_phase08_graph_features.py` passed cleanly (100% OK).
- **Master Validation Command:**
  ```bash
  python3 -m src.graph.validate_phase8_features
  ```
  Result: 54 / 54 PASS (0 WARN, 0 FAIL).

---

## 9. Data Authority and Reconciliation (Phase 8A)

- **Authority Hierarchy:** Serialized CSV and JSON artifacts in `results/phase_08/` represent the ground truth for all numerical values.
- **Documentation Alignment:** All Markdown tables and summaries are reconciled directly from these artifacts without manual estimation or rounding discrepancies.
- **Integrity Guarantee:** No underlying graph files (`dataset/graphs/*.npz`), feature arrays, or normalization parameters were altered during Phase 8A.

---

## 10. Output Deliverables

The output directory `results/phase_08/` is fully populated:
- `feature_provenance.csv` (21 feature traceability records)
- `feature_statistics.csv` (Exhaustive percentiles and counts)
- `feature_validation.csv` (Per-design 20-check validation log)
- `feature_correlations.csv` (Pearson & Spearman correlation matrix)
- `graph_level_features.csv` (54 design rows)
- `design_feature_summary.csv` (Sorted benchmark scale comparison)
- `normalization_parameters.json` (Fitted on 51 training designs)
- `data_leakage_audit.json` (Audit certification)
- `phase09_input_contract.json` (Phase 9 interface contract)
- `reproducibility.csv` (Bit-exact execution comparison)
- `figures/cell_feature_distributions.png`
- `figures/net_feature_distributions.png`
- `figures/graph_feature_distributions.png`
- `figures/feature_correlation.png`
- `figures/design_feature_summary.png`
EOF
