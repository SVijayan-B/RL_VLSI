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
- `src/graph/graph_features.py` (Feature statistics extraction & summary)
- `src/graph/graph_builder.py` (Bipartite & cell-projection graph construction)
- `src/graph/export_graph.py` (Batch canonical graph exporter)
- `src/graph/validate_graph.py` (Automated 20-point validation suite)
- `dataset/metadata/graph_manifest.csv` (Detailed per-graph ledger)
- `dataset/metadata/graph_manifest.json`
- `dataset/metadata/graph_source_inventory.csv`
- `dataset/metadata/graph_validation.csv` (Detailed validation ledger)
- `dataset/metadata/graph_statistics.csv`
- `dataset/metadata/graph_lef_mapping.csv`
- `results/phase_02/feature_summary.csv`
- `results/phase_02/validation_summary.csv`
- `docs/PHASE_02_FEATURE_SPECIFICATION.md`
- `docs/PHASE_02_GRAPH_CONSTRUCTION.md`

---

### PHASE 3 — TECHNOLOGY LIBRARY STRATEGY & WIRE-LOAD MODELING
**Status: COMPLETE** (Date: 2026-09-29)
- Established explicit technology boundaries: Primary technology is CircuitNet N28 (`circuitnet.lef`); Nangate45 / ASAP7 are strictly quarantined for toolchain sanity testing and never mixed with experimental results.
- Parsed complete metal stack from `circuitnet.lef`: 18 layers (9 routing layers M1–M9, 9 cut layers VIA1–VIA8 + VIA0), with pitch, direction, and track definitions.
- Formulated validated analytical wireload models: Half-Perimeter Wirelength (HPWL), Elmore wire delay proxy ($R_{\text{unit}} = 0.25\,\Omega/\mu\text{m}$, $C_{\text{unit}} = 0.20\,\text{fF}/\mu\text{m}$ for M2–M4 intermediate routing), and Rent's rule interconnect exponent ($p = 0.68$).
- Implemented and verified standalone Python extraction library (`src/technology/wirelength.py`, `src/technology/wireload_model.py`, `src/technology/tech_manager.py`).
- Completed 100% of validation gates; master validation suite `python3 -m src.technology.validate_technology` passes with 0 warnings, 0 failures.

---

### PHASE 4 — BASELINE PHYSICAL DESIGN & OPENROAD FLOW SETUP
**Status: COMPLETE** (Date: 2026-10-02)
- Environment audited and logged to `results/phase_04/environment_report.json` (OpenROAD Docker `openroad/orfs:latest`, Linux kernel 6.18, Python 3.12.3).
- Established 4 representative benchmarks (`BENCH_01_RISCY_C2_U70`, `BENCH_02_RISCY_C2_U90`, `BENCH_03_RISCY_C5_U70`, `BENCH_04_RISCY_C20_U70`) from paired netlist-DEF designs with 100% LEF cell matches.
- Ingestion policy verified: Resolved OpenDB ODB-0421 routing-via errors by parsing with `read_def -continue_on_errors`, retaining 100% of cells (49k–52k), nets (53k–55k), and terminal pins without fabricating via rules.
- Baseline placement feasibility verified: Detailed placement (`detailed_placement`) runs natively in OpenROAD on CircuitNet coordinates, achieving legalized DRC/site-clean layouts (e.g. 11,990 violations resolved in 2.73s). Global placement requires `.lib` for timing-driven forces, confirming the need for analytical proxy guidance during RL.
- Authoritative baseline HPWL metrics measured via OpenROAD OpenDB pin offsets and validated against independent Python layout analysis (<4% difference due to pin polygon offsets vs cell origins).
- Automated test suite `src/flow/test_baseline.py` (5 tests) and master validation suite `python3 -m src.flow.validate_baseline` pass with 100% OK.
- Completed comprehensive documentation in `docs/PHASE_04_BASELINE_OPENROAD.md`.

---

### PHASE 5 — TIMING MODELING & PROXY METRICS
**Status: COMPLETE** (Date: 2026-10-02)
- Formulated an analytical timing proxy architecture combining Elmore $RC$ interconnect delays with cell propagation models ($D_{\text{gate}} = \tau_{\text{int}} + R_{\text{dr}} \cdot C_{\text{load}}$).
- Generated topological DAGs and identified critical timing paths across all four Phase 4 baseline benchmarks. Evaluated worst negative slack (WNS), total negative slack (TNS), and failing path endpoints under nominal clock constraints (2.0ns, 5.0ns, 20.0ns).
- Calibrated gate drive resistances against open-source cell libraries (Nangate45/ASAP7) while strictly quarantining open platform data from CircuitNet N28 geometries.
- Verification & Reproducibility: 7 unit tests in `src/technology/test_timing_proxy.py` pass cleanly in $<0.05\,\text{s}$. Master validation command `python3 -m src.technology.validate_timing` passes 100% of checks across all 5 verification gates.
- Documentation & Artifacts: Completed comprehensive documentation in `docs/PHASE_05_TIMING_MODELING.md`, CSV summaries in `results/phase_05/`, and calibration documentation in `dataset/metadata/timing_calibration.json`.

---

### PHASE 6 — POWER ESTIMATION & PDN IR-DROP PROXIES
**Status: COMPLETE** (Date: 2026-10-02)
- Formulated physics-grounded power estimation models: Dynamic switching power ($P_{\text{dyn}} = \frac{1}{2} \alpha C V_{dd}^2 f$), internal cell power ($P_{\text{int}} = V_{dd} \cdot I_{\text{sc}} \cdot t_{\text{trans}} \cdot f$), and leakage power ($P_{\text{leak}} = I_{\text{leak}} \cdot V_{dd}$ with exponential temperature and gate-length scaling).
- Evaluated total power dissipation across all 4 benchmarks: Total power ranges from $10.60\,\text{mW}$ to $107.03\,\text{mW}$, with dynamic switching accounting for $72.8\% - 85.5\%$ of total dissipation.
- Implemented static 2D resistive mesh IR-drop proxy: The core floorplan is discretized into a $16 \times 16$ spatial grid with horizontal (M9) and vertical (M8) power straps. Evaluated peak IR drops ($11.75\,\text{mV} - 45.45\,\text{mV}$, well within the nominal $50\,\text{mV}$ / $5\%$ budget) and localized IR-drop hotspots in high-density core centers.
- Correlation Analysis: Generated `results/phase_06/correlation_matrix.csv`. Demonstrated that net HPWL and dynamic power proxy have strong Spearman rank correlation ($\rho = 0.75 - 0.81$), confirming that HPWL minimization inherently reduces dynamic wire power. Pearson correlation with fanout is $>0.99$.
- Architectural Policy Decision: Formally established **`POWER_AS_SECONDARY_METRIC`**. HPWL remains the primary placement quality metric and RL optimization reward. Power and IR-drop proxies are retained as secondary multi-objective evaluation metrics to prevent confounding the placement agent.
- Verification & Reproducibility: 6 unit tests in `src/power/test_power_proxy.py` pass in $<0.05\,\text{s}$. Master validation command `python3 -m src.power.validate_power` passes 100% of checks across all 5 verification gates.
- Documentation & Visualizations: Completed comprehensive guide in `docs/PHASE_06_POWER_IR_MODELING.md` and publication-ready multi-panel plots in `results/phase_06/figures/phase_06_power_ir_metrics.png`.

---

### PHASE 7 — PLACEMENT PARAMETER SWEEP & SPACE FORMULATION
**Status: COMPLETE — FINALIZED** (Date: 2026-10-03)

#### 1. Execution Summary
- **Phase 7A (HPWL Experimental Integrity Repair):**
  - Resolved baseline discrepancy ($151,825.80\,\mu\text{m}$ vs $731,162.90\,\mu\text{m}$) caused by incomplete DEF continuation-line parsing that skipped connection pairs on OpenROAD write_def net-header lines.
  - Locked exact OpenROAD console legalized HPWL ($731,162.90\,\mu\text{m}$) into `results/phase_07/integrity/baseline_lock.json` and `results/phase_07/integrity/bench01_hpwl_comparison.csv`.
  - Re-ran all 38 parameter sweep experiments using authoritative OpenROAD measurements into `results/phase_07/parameter_sweep_final.csv`.
- **Phase 7B (Paper Alignment Cleanup & Final Validation):**
  - **Table I Parameter Reference Corrected:** Cardinalities strictly preserved (`timing effort = 2`, `clock power driven = 3`). Artificially introduced defaults removed; Table VIII experiment settings cataloged separately in `results/phase_07/paper_table_viii_reference.csv`.
  - **Table III Action Reference Corrected:** Conceptual paper action names strictly preserved (`UP Global`, `DOWN Global`, `INVERT-MIX`).
  - **OpenROAD Action Space Adaptation:** Explicitly categorized actions into `VERIFIED` (1, 2, 3, 6, 7, 11), `PARTIALLY_VERIFIED` (4, 5), and `UNAVAILABLE` (8, 9, 10). Preserved paper action identity without corrupting DPL parameters with fake mappings.
  - **Sensitivity Direction Rules Corrected:** Strictly enforced numerical tolerance threshold $\tau_{\text{HPWL}} = 0.001\%$, classifying effects as `IMPROVEMENT`, `DEGRADATION`, or `NEUTRAL` in `results/phase_07/parameter_sensitivity_final.csv`.
  - **Pairwise Interactions Formalized:** Mathematically separated HPWL interaction ($0.0\,\mu\text{m}$, `hpwl_interaction_detected = FALSE`) and Runtime interaction in `results/phase_07/parameter_interactions_final.csv`.
  - **Runtime Repeat Validation:** Executed 18 repeat runs (6 configs × 3 repeats) in `results/phase_07/runtime_repeat_validation.csv` and `runtime_repeat_summary.csv`. Demonstrated 100% bit-exact HPWL reproducibility and statistically verified the $\approx 23\times$ speedup of `use_diamond_legalizer` on high density.
  - **Figure & Documentation Regeneration:** Regenerated 6 publication-ready figures in `results/phase_07/figures/` and updated `docs/PHASE_07_PLACEMENT_PARAMETER_SPACE.md`.
  - **Automated Validation:** Master validation suite `python3 -m src.placement.validate_phase7` passes 20/20 criteria (100% OK); pytest suite `src/placement/test_phase7b_audit.py` passes 8/8 tests (100% PASS).
  - Phase 7 is frozen.

---

### PHASE 8 — GRAPH FEATURE EXTRACTION (HETEROGENEOUS NETLIST GRAPH)
**Status: COMPLETE** (Date: 2026-10-03)

#### 1. Execution Summary
- **Canonical Schema Verification & Audit:**
  - Audited and locked the canonical **7-dimensional standard cell feature schema** (`area`, `width`, `height`, `aspect_ratio`, `is_macro`, `cell_degree`, `log_degree`) and **4-dimensional net feature schema** (`net_degree`, `log_degree`, `is_clock`, `is_reset`).
  - Audited and formally resolved earlier planning inconsistencies referring to 8-dimensional inputs: CircuitNet N28 does not provide `.lib` timing tables for capacitance or gate timing arcs; the authentic 7-dimensional LEF/netlist representation is preserved. Documented in `docs/PHASE_08_FEATURE_SCHEMA_AUDIT.md`.
- **Full Dataset Extraction Across All 54 Designs:**
  - Validated all 54 canonical graphs ($2,373,702$ cells, $2,469,557$ nets, $9,572,055$ unrolled pins, $54,342,544$ projected cell edges).
  - Checked 20 mathematical and integrity criteria per design (0 NaNs, 0 Infs, positive areas and widths, finite aspect ratios, consistent log transformations, bit-exact alignment with metadata). All 54 designs passed with 100% PASS (0 WARN, 0 FAIL) in `results/phase_08/feature_validation.csv`.
- **Feature Traceability & Statistics:**
  - Formulated comprehensive provenance ledger in `results/phase_08/feature_provenance.csv` (21 feature records across cell, net, and graph domains).
  - Calculated complete summary statistics (min, max, mean, median, standard deviation, 1st/25th/75th/99th percentiles) in `results/phase_08/feature_statistics.csv`.
  - Computed Pearson and Spearman rank correlation matrices across cell features in `results/phase_08/feature_correlations.csv`.
  - Generated graph-level conditioning table (`results/phase_08/graph_level_features.csv`, 54 rows) and deterministic scale comparison (`results/phase_08/design_feature_summary.csv`).
- **Zero-Leakage Normalization & Audit:**
  - Fitted pre-convolution normalization parameters (`results/phase_08/normalization_parameters.json`) strictly on the 51 training designs. Quarantined all 3 Phase 4 benchmark evaluation designs (`RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`) to eliminate data leakage.
  - Certified zero leakage in `results/phase_08/data_leakage_audit.json` (no placement coordinates, no OpenROAD outputs, no Phase 7 outcomes, no reward signals).
- **Phase 9 Interface Specification:**
  - Formulated locked contract in `results/phase_08/phase09_input_contract.json` and `docs/PHASE_08_PHASE_09_INTERFACE.md`, enforcing input node feature dimension $d_{\text{in}} = 7$, projected cell edge index $[2, E_{\text{cell}}]$, and target embedding dimension $d_{\text{emb}} = 32$.
- **Automated Validation & Testing:**
  - Smoke test `scripts/phase08_feature_smoke_test.py` verified all 10 pipeline steps cleanly without training neural networks.
  - Pytest suite `tests/test_phase08_graph_features.py` passed 15/15 tests (100% PASS).
  - Master validation script `python3 -m src.graph.validate_phase8_features` passed 54/54 designs (100% OK).
  - Two deterministic execution passes confirmed 100% bit-exact reproducibility (`results/phase_08/reproducibility.csv`: 54/54 matches).
  - Generated 5 publication-quality visualization figures in `results/phase_08/figures/`.
- Phase 8 is frozen.

---

## NEXT PHASE

### PHASE 9 — GRAPHSAGE ARCHITECTURE & NODE EMBEDDINGS
**Status: READY TO COMMENCE (DO NOT START YET)**
- Implement GraphSAGE model architecture taking 7-dimensional cell features.
- Define 2-hop neighborhood sampling and mean aggregation on projected cell graphs.
- Formulate unsupervised InfoNCE contrastive learning or link prediction.
- Generate 32-dimensional node embeddings and permutation-invariant mean-aggregated graph embeddings.

---
## ROADMAP OF SUBSEQUENT PHASES

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | **Data Audit & Inventory** | **COMPLETE** |
| **Dataset Finalization** | **Consolidation, Cleanup & Master Indexing** | **COMPLETE** |
| **Phase 2** | **Circuit Graph Construction & Validation** | **COMPLETE** |
| **Phase 3** | **Technology Library Strategy & Wire-Load Modeling** | **COMPLETE** |
| **Phase 4** | **Baseline Physical Design & OpenROAD Flow Setup** | **COMPLETE** |
| **Phase 5** | **Timing Modeling & Proxy Metrics** | **COMPLETE** |
| **Phase 6** | **Power Estimation & PDN IR-Drop Proxies** | **COMPLETE** |
| **Phase 7** | **Placement Parameter Sweep & Space Formulation** | **COMPLETE — FINALIZED** |
| **Phase 8** | **Graph Feature Extraction (Heterogeneous Netlist Graph)** | **COMPLETE** |
| Phase 9 | GraphSAGE Architecture & Node Embeddings | **COMPLETE** |
| Phase 10 | RL Environment (Placement State, Action Space, Rewards) | **COMPLETE** |
| Phase 11 | A2C Policy/Value Network Training | **READY TO COMMENCE** |
| Phase 12 | Experimental Validation & Benchmark Comparisons | PENDING |
| Phase 13 | Paper-Style Plots, Tables & Statistical Analysis | PENDING |
| Phase 14 | Final Reproducibility Report & Documentation | PENDING |
EOF
