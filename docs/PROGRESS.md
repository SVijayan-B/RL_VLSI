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

---

### PHASE 3 — TECHNOLOGY LIBRARY STRATEGY & WIRE-LOAD MODELING
**Status: COMPLETE** (Date: 2026-09-29)

#### 1. Execution Summary
- **Technology Census:** Audited 555 design and technology files (`dataset/metadata/tech_files_inventory.csv`).
- **LEF & Cell Analysis:** Verified 18 layers (CO, M1–M8, VIA1–VIA7, RV, AP) and 915 standard cell macros with zero resistance/capacitance tables (`dataset/metadata/tech_layer_inventory.csv`, `dataset/metadata/tech_cell_inventory.csv`, `dataset/metadata/tech_assumptions.json`).
- **OpenROAD/OpenSTA Ingestion:** Verified OpenROAD container invocation with volume mounting; resolved DEF via warnings using `read_def -continue_on_errors`; verified that native OpenSTA requires `.lib` which is absent in CircuitNet N28; verified auxiliary OpenSTA execution on Nangate45 reference platform.
- **Scientific Classification:** Established the formal 5-tier taxonomy (DIRECT, DERIVED, PROXY, EXTERNAL, UNAVAILABLE) in `dataset/metadata/tech_capability_matrix.csv`.
- **Interconnect & Wirelength Implementation:**
  - `src/technology/wirelength.py`: Implemented exact Half-Perimeter Wirelength (HPWL), bounding box, and hyperedge wirelength calculation.
  - `src/technology/rc_proxy.py`: Implemented analytical normalized RC proxy parameters ($R_w=0.25\,\Omega/\mu\text{m}$, $C_w=0.18\,\text{fF}/\mu\text{m}$).
  - `src/technology/test_technology.py`: 7 unit tests, 100% PASS.
  - `src/technology/validate_technology.py`: Validated against canonical graph `RISCY-FPU-a-1-c2_graph.npz` (75,067 cells, 76,569 nets); output logged to `results/phase_03/validation_summary.csv`.
- **Documentation:** Created comprehensive `docs/PHASE_03_TECHNOLOGY_MODELING.md`.

---

### PHASE 4 — BASELINE PHYSICAL DESIGN & OPENROAD FLOW SETUP
**Status: COMPLETE** (Date: 2026-10-02)

#### 1. Execution Summary
- **Environment Audit:** Formally documented in `results/phase_04/environment_report.json` and `.md` (OpenROAD ORFS Docker `94d3c1c19b47`, Python 3.12.3, Yosys 0.33, Icarus Verilog 12.0, 500 DEFs, 54 Netlists, 54 Canonical Graphs).
- **Representative Benchmark Selection:** 4 distinct benchmarks spanning small, medium, and high density ($u=0.70$ and $u=0.90$) across `RISCY-a-1-c2`, `RISCY-a-1-c5`, and `RISCY-a-1-c20` documented in `results/phase_04/benchmark_selection.csv`.
- **Input Consistency Check:** All 4 benchmarks verified 100% consistent across netlist, DEF, LEF, instance counts, net counts, and terminal pin dimensions (`results/phase_04/benchmark_consistency.csv`).
- **OpenROAD Ingestion & VIA Policy:**
  - Normal `read_def` fails predictably due to missing VIA definitions in `circuitnet.lef`.
  - `read_def -continue_on_errors` succeeds 100%, retaining 49,931 to 52,147 cells and 53,246 to 55,403 nets per benchmark (`results/phase_04/ingestion/ingestion_summary.csv`).
  - No via geometries or external technologies were fabricated, keeping the CircuitNet N28 dataset fully authentic.
- **Baseline Placement Feasibility & Legalization:**
  - Global re-placement from scratch is constrained by lack of `.lib`.
  - OpenROAD detailed placement (`DPL`) legalization is **fully operational and verified**, resolving initial site violations and placing cells legal to the `CoreSite` grid in 2.5 to 133 seconds.
- **Independent HPWL Validation:**
  - Extracted layout metrics using Python origin approximation vs OpenROAD exact pin offsets.
  - Consistent $<4\%$ delta ($2.44\%$ to $3.87\%$) accounts exactly for pin center offsets across all benchmarks.
- **Deterministic Reproducibility:** Multi-seed repeat runs on `BENCH_01_RISCY_C2_U70` produced **100.0% identical legalized HPWL ($731,162.90\,\mu\text{m}$)** (`results/phase_04/reproducibility.csv`).
- **Validation Command:** Automated suite `python3 -m src.placement.validate_baseline` passes all 5 test criteria with 100% OK.
- **Documentation & Deliverables:** Created `docs/PHASE_04_BASELINE_OPENROAD.md` and publication plots in `results/phase_04/figures/phase_04_baseline_metrics.png`.

---

### PHASE 5 — TIMING MODELING & PROXY METRICS
**Status: COMPLETE** (Date: 2026-10-02)

#### 1. Execution Summary
- **Terminology Alignment & Audit:** Formally documented in `results/phase_05/model_audit.md` and `.json`. Corrected terminology to **analytical normalized RC proxy parameters** ($R_w=0.25\,\Omega/\mu\text{m}$, $C_w=0.18\,\text{fF}/\mu\text{m}$, $C_{\text{gate}}=0.50\,\text{fF}$, $R_{\text{driver}}=450.0\,\Omega$) to clarify that values represent idealized surrogates for relative ranking and not foundry sign-off numbers.
- **Timing-Proxy Taxonomy Established:** Formal 7-tier taxonomy separating DERIVED (HPWL), PROXY (Wire Parasitics, Net Delay, Topological Depth, Path Delay, Criticality), and UNAVAILABLE (Foundry Sign-off Slack, WNS/TNS).
- **Core Engine Implementation:** Developed `src/technology/timing_proxy.py` containing vectorized net delay evaluation, topological depth propagation, bounded path delay proxies, and normalized $[0, 1]$ criticality scores.
- **Benchmark Evaluation & Statistics:** Computed distributions across 53,246 to 55,401 nets for all 4 primary benchmarks (`results/phase_05/net_delay_statistics.csv`). Mean net delays range from $5.80$ to $6.21\,\text{ps}$; 95% of nets exhibit delay $\le 18.0\,\text{ps}$.
- **Correlation Analysis:** Generated `results/phase_05/correlation_matrix.csv`. Confirmed high monotonic rank agreement between HPWL and net delay proxy (Spearman $\rho = 0.77 - 0.82$), and verified that global clock/reset outliers dominate extreme delays (Pearson $r > 0.98$ with fanout).
- **Placement Sensitivity Experiment:** Compared initial CircuitNet placements against OpenROAD legalized layouts (`results/phase_05/benchmark_timing_comparison.csv`). Quantified that low-density benchmarks expand by $+2.7\%$ while high-density ($u=0.90$) congestion forces $+16.3\%$ wire delay expansion.
- **Verification & Reproducibility:** 7 unit tests in `src/technology/test_timing_proxy.py` (100% PASS). Master validation suite `python3 -m src.technology.validate_timing_proxy` passes 100% of checks.
- **Documentation & Visualizations:** Created `docs/PHASE_05_TIMING_MODELING.md` and publication-ready plots in `results/phase_05/figures/phase_05_timing_proxy_metrics.png`.

---

### PHASE 6 — POWER ESTIMATION & PDN IR-DROP PROXIES
**Status: COMPLETE** (Date: 2026-10-02)

#### 1. Execution Summary
- **SPECIALNETS & PDN Geometry Audit:** Audited all 4 benchmarks and variations across `p1` through `p8` (`results/phase_06/pdn_audit.csv` and `.json`). Verified that genuine PDN grids exist for `VDD` and `VSS` across layers `M1` through `M8`. Upper-metal stripe counts expand from 16,666 stripes in `p1` to 22,868 stripes in `p7`, reducing analytical effective PDN grid resistance.
- **Power-Proxy Engine Implementation:** Developed `src/power/power_engine.py` (`PowerAndIRProxyEngine`). Reuses Phase 3 normalized analytical interconnect RC parameters to model dynamic switching power ($P_{\text{dyn}} = \alpha C_{\text{total}} V_{\text{norm}}^2 f_{\text{norm}}$) with fanout-dependent switching activity $\alpha = \text{clip}(0.15 + 0.10 \log_{10}(\text{Fanout}), 0.10, 0.60)$, static leakage proxy scaled by standard cell area, and spatial power density mapping over a 2D grid ($16 \times 16$).
- **Benchmark Evaluation & Density Impact:** Evaluated initial vs legalized layouts for all primary benchmarks (`results/phase_06/benchmark_power_comparison.csv`). In Benchmark 02 ($u=0.90$), compaction increases average power density by $+20.9\%$ ($0.834$ vs $0.690\,\text{a.u.}/\mu\text{m}^2$) relative to Benchmark 01 ($u=0.70$) due to smaller floorplan area, driving peak IR-drop proxies higher.
- **Correlation Analysis:** Generated `results/phase_06/correlation_matrix.csv`. Demonstrated that net HPWL and dynamic power proxy have strong Spearman rank correlation ($\rho = 0.75 - 0.81$), confirming that HPWL minimization inherently reduces dynamic wire power. Pearson correlation with fanout is $>0.99$.
- **Architectural Policy Decision:** Formally established **`POWER_AS_SECONDARY_METRIC`**. HPWL remains the primary placement quality metric and RL optimization reward. Power and IR-drop proxies are retained as secondary multi-objective evaluation metrics to prevent confounding the placement agent.
- **Verification & Reproducibility:** 6 unit tests in `src/power/test_power_proxy.py` pass in $<0.05\,\text{s}$. Master validation command `python3 -m src.power.validate_power` passes 100% of checks across all 5 verification gates.
- **Documentation & Visualizations:** Completed comprehensive guide in `docs/PHASE_06_POWER_IR_MODELING.md` and publication-ready multi-panel plots in `results/phase_06/figures/phase_06_power_ir_metrics.png`.

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

## NEXT PHASE

### PHASE 8 — GRAPH FEATURE EXTRACTION (HETEROGENEOUS NETLIST GRAPH)
**Status: READY TO COMMENCE (DO NOT START YET)**
- Formulate heterogeneous graph representations from CircuitNet canonical graphs.
- Define node-level features for standard cells and net hyperedges for GraphSAGE ingestion.

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
| Phase 8 | Graph Feature Extraction (Heterogeneous Netlist Graph) | **READY TO COMMENCE** |
| Phase 9 | GraphSAGE Architecture & Node Embeddings | PENDING |
| Phase 10 | RL Environment (Placement State, Action Space, Rewards) | PENDING |
| Phase 11 | A2C Policy/Value Network Training | PENDING |
| Phase 12 | Experimental Validation & Benchmark Comparisons | PENDING |
| Phase 13 | Paper-Style Plots, Tables & Statistical Analysis | PENDING |
| Phase 14 | Final Reproducibility Report & Documentation | PENDING |
