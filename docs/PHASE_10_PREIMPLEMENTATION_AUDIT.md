# Phase 10: Pre-Implementation Audit & System Architecture

**Document Version:** 1.0.0  
**Status:** COMPLETE (Pre-Implementation Gate Passed)  
**Date:** 2026-10-04  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  
**Reference:** Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, *IEEE TCAD 2023*  

---

## 1. Existing System Architecture

The overall repository implements an experimentally rigorous adaptation of the Agnesina et al. framework tailored to the open **CircuitNet N28** dataset with **OpenROAD** physical design execution and validated analytical proxies.

The flow through completed phases is structured as follows:
```
[Phase 1 & Dataset Finalization]
   Canonical Netlists (54) + DEF Files (500) + LEF (circuitnet.lef)
         │
         ▼
[Phase 2]
   Homogeneous Cell Graphs (edge_index_cell, high-fanout threshold <= 50)
   + Bipartite Netlist Graphs (54 designs in dataset/graphs/)
         │
         ▼
[Phase 3 - 6]
   Wireload Technology Models (Phase 3)
   OpenROAD Containerized Flow (openroad/orfs:latest) & DPL Baseline (Phase 4)
   Analytical Timing Proxy Engine (Phase 5)
   Analytical Power & PDN IR-Drop Proxy Engine (Phase 6)
         │
         ▼
[Phase 7 & 7A/7B]
   Placement Parameter Sweep & Action Space Formulation (Table III adaptation)
   DEF Connection Parser Repair & OpenROAD Baseline Lock (results/phase_07/integrity/)
         │
         ▼
[Phase 8 & 8A]
   7-Dimensional Cell Features ([N, 7]) & Normalization locked on 51 Train Designs
         │
         ▼
[Phase 9]
   GraphSAGE (2-layer Mean Aggregation: 7 -> 64 -> 32)
   InfoNCE Contrastive Representation Learning (15 epochs, Loss 1.7895 -> 1.3180)
   Frozen 32-D Graph Embeddings (54 designs) + Node Embeddings (2,373,702 cells)
         │
         ▼
[Phase 10 (Current)]
   Validated Gymnasium RL Environment Infrastructure:
   State Space (Graph Emb [32] + Norm Params [6] + Placement Metrics + Progress)
   Verified Action Space (OpenROAD DPL 6 parameters, Table III actions)
   Deterministic Transitions, OpenROAD Execution Isolation, Reward Formulation
   A2C Policy/Value Networks & Smoke-Test Training Validation
```

---

## 2. Existing File Locations

| Module / Component | Path | Description / Key Artifacts |
| :--- | :--- | :--- |
| **LEF / Tech** | `dataset/raw/circuitnet.lef` | TSMC 28nm standard cell macro definitions |
| **Canonical Graphs** | `dataset/graphs/{design_id}_graph.npz` | 54 canonical graphs (cells, nets, cell_features, edge_index_cell) |
| **DEFs** | `dataset/processed/DEF_decompressed/DEF/*.def` | 500 decompressed DEF files across 51 designs |
| **Phase 4 Baselines** | `results/phase_04/baseline_manifest.json` | Baseline OpenROAD DPL execution metrics |
| **Phase 7 Space** | `configs/phase_07/baseline_placement.json` | 6 verified DPL parameter definitions & bounds |
| **Phase 7 Integrity** | `results/phase_07/integrity/baseline_lock.json` | Authoritative locked baseline HPWL (731,162.90 um) |
| **Phase 8 Contract** | `results/phase_08/phase09_input_contract.json` | Hard 7-D cell feature schema and rules |
| **Phase 8 Norm** | `results/phase_08/normalization_parameters.json` | Frozen normalization parameters (51 train designs) |
| **Phase 9 Model** | `src/graph/graphsage.py` | `NetlistGraphSAGE`, `SAGEConvMean`, `InfoNCELoss` |
| **Phase 9 Checkpoint**| `results/phase_09/checkpoints/graphsage_best.pt` | Frozen PyTorch weights for GraphSAGE |
| **Phase 9 Config** | `configs/phase09_graphsage.json` | Exact GraphSAGE architecture hyperparameters |
| **Phase 9 Embeddings**| `results/phase_09/graph_embeddings.csv` | 54 designs x 32-D global graph embeddings |
| **Phase 9 Node Embs** | `results/phase_09/node_embeddings/*.pt` | 54 files containing all cell node embeddings [N, 32] |

---

## 3. Existing GraphSAGE Interface

The GraphSAGE model is **FROZEN**. No weights, feature definitions, or normalization parameters will be modified.

- **Model Class**: `NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32, dropout=0.20)` in `src/graph/graphsage.py`.
- **Checkpoint**: `results/phase_09/checkpoints/graphsage_best.pt`.
- **Node Features (7-D)**:
  0. `area` (um^2)
  1. `width` (um)
  2. `height` (um)
  3. `aspect_ratio` (width / height)
  4. `is_macro` (1.0 for macro, 0.0 standard cell)
  5. `cell_degree` (connected unrolled pins)
  6. `log_degree` (log(1 + cell_degree))
- **Standardization**: Applied strictly via `(x - mean) / std` using `results/phase_08/normalization_parameters.json`.
- **Graph Embedding Extraction**: `h_G = mean_pool(h_nodes, dim=0)` -> [32].
- **Precomputed Table**: `results/phase_09/graph_embeddings.csv` (54 rows x 32 features).

---

## 4. Existing OpenROAD Interface

- **Execution Engine**: OpenROAD inside Docker image `openroad/orfs:latest` (or local binary where configured).
- **Execution Script**:
  ```tcl
  read_lef dataset/raw/circuitnet.lef
  read_def -continue_on_errors <input_def_path>
  detailed_placement <dpl_args>
  check_placement
  write_def <output_def_path>
  exit
  ```
- **Controlled Ingestion Policy**: `-continue_on_errors` handles lack of unneeded routing VIA rules in `circuitnet.lef` while preserving 100% of standard cell components, instance placement coordinates, net connectivity, and terminal pins.
- **Detailed Placer (`DPL`)**: Operates directly on cell coordinates to resolve site overlaps without requiring proprietary Liberty (`.lib`) timing files.

---

## 5. Existing Placement Metric Interface

- **Physical Metric Extraction**: `src/placement/physical_metrics.py` (`extract_def_metrics`).
- **HPWL Formula**: Half-Perimeter Wire Length across all multi-pin signal nets in canonical units of microns (um), using CircuitNet DBU conversion 1 DBU = 0.0005 um (2000 DBU/um).
- **Integrity Lock**: Analytical extraction matches OpenROAD OpenDB output within 0.09% (locked in `results/phase_07/integrity/baseline_lock.json`).
- **Timing & Power Proxies**: `TimingProxyEngine` (`src/technology/timing_proxy.py`) and `PowerAndIRProxyEngine` (`src/power/power_engine.py`).

---

## 6. Existing Benchmark Definitions

From `results/phase_04/benchmark_selection.csv` and `results/phase_07/integrity/baseline_lock.json`:

| Benchmark ID | Design Key | Util | Category | Baseline HPWL (um) | Source DEF |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BENCH_01_RISCY_C2_U70` | `RISCY-a-1-c2` | 0.70 | primary_baseline_low_util | **731,162.90** | `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` |
| `BENCH_02_RISCY_C2_U90` | `RISCY-a-1-c2` | 0.90 | high_density_stress | **708,651.30** | `120-RISCY-a-1-c2-u0.9-m1-p1-f0.def` |
| `BENCH_03_RISCY_C5_U70` | `RISCY-a-1-c5` | 0.70 | medium_clock_baseline | **701,234.80** | `248-RISCY-a-1-c5-u0.7-m1-p1-f0.def` |
| `BENCH_04_RISCY_C20_U70`| `RISCY-a-1-c20`| 0.70 | relaxed_clock_baseline | **700,395.90** | `493-RISCY-a-1-c20-u0.7-m1-p1-f0.def` |

---

## 7. Existing Train / Validation / Test Split

- **Total Canonical Designs**: 54 designs.
- **Training Partition (51 designs)**:
  - All 27 `RISCY-FPU` designs (`RISCY-FPU-a-*-c*`)
  - 15 `RISCY` designs (excluding `RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`)
  - All 9 `zero-riscy` designs (`zero-riscy-a-*-c*`)
- **Quarantined Held-Out Test Partition (3 designs)**:
  - `RISCY-a-1-c2` (Hosts `BENCH_01` and `BENCH_02`)
  - `RISCY-a-1-c5` (Hosts `BENCH_03`)
  - `RISCY-a-1-c20` (Hosts `BENCH_04`)
- **RL Training Rule**:
  - RL agent parameter updates and policy optimization must occur **exclusively on training partition designs**.
  - Held-out benchmark designs are evaluated only in frozen inference / validation mode.

---

## 8. Existing Random Seed Handling

- Canonical training seed: **42**.
- Seeds are explicitly applied to Python `random`, NumPy `np.random`, PyTorch CPU `torch.manual_seed`, and PyTorch CUDA `torch.cuda.manual_seed_all`.
- Model determinism confirmed bit-exact across repeated runs in Phase 4 and Phase 9.

---

## 9. Existing Phase 7 Verified Parameter Controls

From `configs/phase_07/baseline_placement.json`:

| Parameter Name | Data Type | Legal Bounds | Step | Default | OpenROAD Flag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `max_displacement` | Integer (sites) | [0, 100] | 10 | 0 | `-max_displacement <val>` |
| `site_search_window` | Integer (sites) | [0, 100] | 10 | 0 | `-site_search_window <val>` |
| `row_search_window` | Integer (rows) | [0, 20] | 2 | 0 | `-row_search_window <val>` |
| `disallow_one_site_gaps` | Boolean | {0, 1} | FLIP | False | `-disallow_one_site_gaps` |
| `use_diamond_legalizer` | Boolean | {0, 1} | FLIP | False | `-use_diamond_legalizer` |
| `disable_window_extension` | Boolean | {0, 1} | FLIP | False | `-disable_window_extension` |

*Note on Agnesina et al. 12 parameters*:
Parameters related to global placement wirelength forces, timing weight multipliers, and commercial Innovus flags that require `.lib` or non-existent OpenROAD flags are marked `UNAVAILABLE` and excluded from entering the active RL action space.

---

## 10. Existing Phase 8 / 9 Outputs

- `results/phase_08/normalization_parameters.json`: Authoritative feature normalization parameters.
- `results/phase_08/phase09_input_contract.json`: Authoritative input schema.
- `results/phase_09/checkpoints/graphsage_best.pt`: Locked GraphSAGE checkpoint.
- `results/phase_09/graph_embeddings.csv`: Locked 54-design graph embeddings table (54 x 32).
- `results/phase_09/model_config.json`: Frozen GraphSAGE hyperparameters.

---

## 11. Potential Integration Risks & Mitigation Strategies

1. **Docker Execution Latency**: Spawning Docker containers on every step introduces overhead. For Phase 10 smoke validation, rollout lengths will be kept minimal (2-3 episodes of 3-5 steps).
2. **OpenROAD Execution Failures**: Strict parameter clamping prevents crashes. Failed transitions log explicit statuses and never yield artificial positive rewards.
3. **Data Leakage from Held-Out Benchmarks**: Strict quarantine checks ensure `BENCH_01`-`04` are never used for A2C gradient updates.
4. **Metric Definition Divergence**: Centralized `metrics/hpwl.py` ensures bit-exact consistency with Phase 7A validation.

---

## 12. Files to be Modified / Created

### Files to be Modified
- `docs/PROGRESS.md`

### Files to be Newly Created
- `configs/phase10_parameter_space.json`
- `configs/phase10_a2c.json`
- `metrics/hpwl.py`
- `src/rl/__init__.py`
- `src/rl/state.py`
- `src/rl/action_space.py`
- `src/rl/reward.py`
- `src/rl/environment.py`
- `src/rl/a2c.py`
- `src/rl/smoke_train.py`
- `src/rl/validate_phase10.py`
- `tests/test_hpwl_metric.py`
- `tests/test_phase10_parameter_transitions.py`
- `tests/test_phase10_state.py`
- `tests/test_phase10_actions.py`
- `tests/test_phase10_reward.py`
- `tests/test_phase10_environment.py`
- `tests/test_phase10_determinism.py`
- `tests/test_phase10_no_leakage.py`
- `tests/test_phase10_hpwl_consistency.py`
- `docs/PHASE_10_*.md` (Full documentation suite)
- `results/phase_10/` (Result artifacts)
