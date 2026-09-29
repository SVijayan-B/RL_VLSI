# CircuitNet 28nm — PROGRESS LOG

## Project: Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning
## Reference: Agnesina et al., IEEE TCAD 2023 / CircuitNet Dataset

---

## COMPLETED PHASES

### PHASE 1 — DATA AUDIT & INVENTORY
**Status: COMPLETE** (Date: 2026-09-29)
- Audited all 54 gate-level netlists and 500 DEF physical files.
- Discovered and fixed LEF parser issues; verified 915 macros, 18 layers, CoreSite.
- Generated `netlist_manifest.csv`, `def_manifest.csv`, `design_manifest.csv`, and `lef_cell_mapping.json`.

---

### DATASET FINALIZATION & CONSOLIDATION
**Status: COMPLETE** (Date: 2026-09-29)
- Audited all 10,242 placement samples and 54 graph feature sets.
- Reorganized into canonical structure: `dataset/raw/`, `dataset/circuit_graph/`, `dataset/placement/`, `dataset/processed/`, `dataset/metadata/`.
- Deduplicated ~2.85 GB of redundant intermediate files.
- Generated master index: `dataset_index.csv` (10,242 rows) and `dataset_index.json`.

---

### PHASE 2 — CIRCUIT GRAPH CONSTRUCTION & VALIDATION
**Status: COMPLETE** (Date: 2026-09-29)

#### 1. Execution Summary
- **Graphs Discovered & Processed:** 54 of 54 (100.0%)
- **Validation Results:**
  - PASS: 27 designs (Variant 'a')
  - WARN: 27 designs (Variant 'b' — each contains exactly 1 benign duplicate pin record for APB error signal `pslverr` on node 40533 in the raw data)
  - FAIL: 0 designs
- **Integrity Checks:** 0 invalid node indices, 0 invalid net indices, 0 NaNs, 0 missing LEF types, 0 isolated cells, 0 empty nets.
- **LEF Mapping:** 286 unique cell types across all 54 designs mapped to `circuitnet.lef` with **100.0% coverage** (286 / 286).

#### 2. Global Graph Statistics (54 Designs Total)
- **Total Cell Nodes:** 2,373,702 (Mean: 43,957 cells/design, Range: 19,915 – 75,073)
- **Total Net Nodes:** 2,469,557 (Mean: 45,733 nets/design, Range: 21,632 – 76,604)
- **Total Pin Connections:** 9,489,204 raw pins; 9,572,055 unrolled bipartite edges
- **Total Active Silicon Area:** 12,342,337 $\mu\text{m}^2$ (Mean: 228,562 $\mu\text{m}^2$/design)
- **Average Net Degree:** 3.85 pins/net
- **Average Cell Degree:** 4.03 pins/cell
- **Global Clock Net Max Degree:** Up to 3,661 sinks

#### 3. Canonical Representations Exported
- **Output Directory:** `dataset/graphs/` (54 compressed `.npz` files, **156.41 MB total**)
- **Data Layers per Graph:**
  - `cell_names` $[N]$, `cell_types` $[N]$, `cell_features` $[N \times 7]$ (area, width, height, aspect ratio, is_macro, degree, log_degree)
  - `net_names` $[M]$, `net_features` $[M \times 4]$ (degree, log_degree, is_clock, is_reset)
  - `pin_names` $[E_{\text{bip}}]$ (unrolled with bit indices for bus pins)
  - `edge_index_bipartite` $[2 \times E_{\text{bip}}]$ (lossless bipartite hypergraph)
  - `edge_index_cell` $[2 \times E_{\text{cell}}]$ (homogeneous cell graph with high-fanout threshold $\le 50$)
  - `metadata_json` (parameter schema version `2.0.0`)

#### 4. Artifacts & Manifests Generated
- `src/graph/lef_parser.py` (LEF macro, geometry, and pin parser)
- `src/graph/inspect_graph.py` (Dataset structure auditor)
- `src/graph/validate_graph.py` (Automated 20-point validation suite)
- `src/graph/graph_features.py` (Feature extraction & statistical analysis)
- `src/graph/graph_builder.py` (Canonical graph representation builder)
- `src/graph/export_graph.py` (Batch canonical `.npz` exporter)
- `dataset/metadata/graph_source_inventory.csv` (Source file audit across 54 designs)
- `dataset/metadata/graph_validation.csv` (Detailed validation ledger)
- `dataset/metadata/graph_statistics.csv` (Design-by-design graph topological metrics)
- `dataset/metadata/graph_lef_mapping.csv` (286-entry cell type geometry mapping)
- `dataset/metadata/graph_manifest.csv` & `graph_manifest.json` (Canonical graph index)
- `results/phase_02/validation_summary.csv`
- `results/phase_02/graph_statistics.csv`
- `results/phase_02/feature_summary.csv`
- `docs/PHASE_02_FEATURE_SPECIFICATION.md`
- `docs/PHASE_02_GRAPH_CONSTRUCTION.md`

#### 5. Validation Command
```bash
python3 -m src.graph.validate_graph --all
```

#### 6. Known Limitations
- Variant-b designs contain 1 benign duplicate pin record for `pslverr` in raw CircuitNet files.
- Cell-to-cell projection uses a fanout threshold of 50 to prevent dense clique explosion on global clock/reset nets.

---

## NEXT PHASE

### PHASE 3 — TECHNOLOGY LIBRARY STRATEGY & WIRE-LOAD MODELING
**Status: READY TO COMMENCE (DO NOT START YET)**
- Formulate open-source wireload and RC parasitic models for TSMC 28nm interconnect layers (M1–M8) in the absence of proprietary `.lib` files.
- Establish timing proxy models (Elmore delay / FLUTE / Half-Perimeter Wirelength proxies).
- Prepare cell delay and capacitance tables compatible with OpenROAD / OpenSTA.

---

## ROADMAP OF SUBSEQUENT PHASES

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | **Data Audit & Inventory** | **COMPLETE** |
| **Dataset Finalization** | **Consolidation, Cleanup & Master Indexing** | **COMPLETE** |
| **Phase 2** | **Circuit Graph Construction & Validation** | **COMPLETE** |
| Phase 3 | Technology Library Strategy & Wire-Load Modeling | **NEXT UP** |
| Phase 4 | Baseline Physical Design & OpenROAD Flow Setup | PENDING |
| Phase 5 | Timing Modeling & Proxy Metrics | PENDING |
| Phase 6 | Power Estimation & PDN IR-Drop Proxies | PENDING |
| Phase 7 | Placement Parameter Sweep & Space Formulation | PENDING |
| Phase 8 | Graph Feature Extraction (Heterogeneous Netlist Graph) | PENDING |
| Phase 9 | GraphSAGE Architecture & Node Embeddings | PENDING |
| Phase 10 | RL Environment (Placement State, Action Space, Rewards) | PENDING |
| Phase 11 | A2C Policy/Value Network Training | PENDING |
| Phase 12 | Experimental Validation & Benchmark Comparisons | PENDING |
| Phase 13 | Paper-Style Plots, Tables & Statistical Analysis | PENDING |
| Phase 14 | Final Reproducibility Report & Documentation | PENDING |
