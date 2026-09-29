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

### PHASE: DATASET FINALIZATION & CONSOLIDATION
**Status: COMPLETE** (Date: 2026-09-29)

#### 1. What Was Found & Audited
- **Circuit Graph Features:** 162 `.npy` files across 54 designs (`net_attr`, `node_attr`, `pin_attr`).
- **Placement Dataset:** Exactly 10,242 `.npy` placement samples across 54 designs in CircuitNet N28.
- **Coordinate System Verified:** Despite the archive name (`instance_placement_micron.tar.gz`), inspection confirmed coordinates are discrete GCell/tile bounding boxes $[x_1, y_1, x_2, y_2] \in [0, 255]$ ($256 \times 256$ grid, $2.25\,\mu\text{m}$ per tile).
- **Temporary / Duplicate Files Identified:**
  - Incomplete partial download: `instance_placement_gcell.tar.gzi53y992p.part` (31.5 MB).
  - Redundant tarball copy: `graph_information.tar.gz` (66.4 MB duplicate in subfolder).
  - Redundant sample: `dataset/processed/sample_1/` (52.2 MB duplicate).
  - Intermediate extraction duplicate: `dataset/processed/DEF/` (2.86 GB of `.def.gz` files identical to `dataset/raw/DEF-place-0.tar.gz`).

#### 2. What Was Retained
- **`dataset/raw/` (8.1 GB):** All 4 source compressed archives (`netlist.tar.gz`, `DEF-place-0.tar.gz`, `graph_information.tar.gz`, `instance_placement_micron.tar.gz`) + `circuitnet.lef`.
- **`dataset/circuit_graph/` (533 MB):** All 162 graph topological attribute files (`net_attr`, `node_attr`, `pin_attr`).
- **`dataset/placement/instance_placement/` (39 GB):** All 10,242 placement samples.
- **`dataset/processed/` (27 GB):** 54 gate-level netlists (992 MB) + 500 uncompressed DEFs (26 GB).
- **`dataset/metadata/` (7.4 MB):** All manifests, including `dataset_index.csv` (10,242 rows) and `dataset_index.json`.

#### 3. What Was Removed (Reclaimed ~2.85 GB)
- Removed incomplete `.part` file (31.5 MB).
- Removed duplicate `graph_information.tar.gz` (66.4 MB).
- Removed duplicate `sample_1/` directory (52.2 MB).
- Removed intermediate `.def.gz` folder (2.86 GB, perfectly preserved in raw archive and decompressed DEFs).

#### 4. Disk Usage
- **Before Cleanup:** 77.0 GB in `dataset/` (80 GB total on `/dev/sdd`)
- **After Cleanup:** 74.1 GB in `dataset/` (77 GB total on `/dev/sdd`)
- **Space Reclaimed:** ~2.85 GB

#### 5. Validation Suite Results
All post-cleanup validation checks passed with 100% success (`validate_dataset.py`):
- File counts: Passed (5 raw archives, 54 netlists, 54 net_attr, 54 node_attr, 54 pin_attr, 500 DEFs, 10,242 placement samples).
- Archive integrity: Passed (All tarball checksums & tar extractions verified).
- NumPy loading: Passed (Verified dictionary structure and coordinate bounds across multi-design samples).
- Master dataset index: Passed (10,242 entries validated).

#### 6. Known Limitations
- Commercial DEF files exist for 500 samples (focused on `RISCY-a-1` configurations); the broader 10,242 designs are represented via the placement `.npy` dictionary arrays.
- Placement `.npy` coordinates are represented in GCell grid space ($256 \times 256$) rather than continuous nanometer DBU units.

---

## NEXT PHASE

### PHASE 2 — Circuit Graph Construction / Feature Preparation
**Status: READY TO COMMENCE (DO NOT START YET)**
- Construct heterogeneous directed bipartite / hypergraph representations from the 54 netlists and `circuit_graph/` attributes.
- Construct node feature matrices combining cell function, area from LEF, pin counts, and connectivity.
- Prepare graph data loaders for GraphSAGE representation learning.

---

## ROADMAP OF SUBSEQUENT PHASES

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | **Data Audit & Inventory** | **COMPLETE** |
| **Dataset Finalization** | **Consolidation, Cleanup & Master Indexing** | **COMPLETE** |
| Phase 2 | Circuit Graph Construction / Feature Preparation | **NEXT UP** |
| Phase 3 | Technology Library Strategy & Wire-Load Modeling | PENDING |
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
