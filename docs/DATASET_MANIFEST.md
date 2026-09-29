# CircuitNet 28nm — Dataset Manifest
## Project: Parameter Optimization of VLSI Placement Through Deep RL
### Reference: Agnesina et al., IEEE TCAD 2023 / CircuitNet Dataset

---

## 1. Dataset Overview

This manifest documents the consolidated, validated dataset for the open-source replication/adaptation of Agnesina et al. (IEEE TCAD 2023) using the CircuitNet N28 benchmark suite.

The dataset captures multi-stage VLSI physical design data across 54 RISC-V SoC configurations (`pulpino_top`), including gate-level Verilog netlists, physical design DEF layouts, standard-cell LEF geometry definitions, circuit graph topological features (node, net, and pin attributes), and 10,242 physical instance placement solutions across varied utilization, floorplan, power grid, and filler insertion configurations.

---

## 2. Directory Structure

The final dataset is structured as follows:

```
dataset/
├── raw/                                 # 8.1 GB: All source archives & technology definitions
│   ├── circuitnet.lef                   # TSMC 28nm standard cell & tech LEF (915 macros, 18 layers)
│   ├── netlist.tar.gz                   # Raw archive of 54 gate-level netlists
│   ├── DEF-place-0.tar.gz               # Raw archive of 500 placed DEF files
│   ├── graph_information.tar.gz         # Raw archive of graph attributes (node, net, pin)
│   └── instance_placement_micron.tar.gz # Raw archive of 10,242 placement samples
│
├── circuit_graph/                       # 533 MB: Extracted graph topological features
│   ├── node_attr/                       # 54 .npy files: Instance names and LEF cell types (shape 2 x N)
│   ├── net_attr/                        # 54 .npy files: Signal net names (shape 1 x M)
│   └── pin_attr/                        # 54 .npy files: Pin names, node indices, net indices (shape 3 x P)
│
├── placement/                           # 39 GB: Physical instance placement coordinates
│   └── instance_placement/              # 10,242 .npy files: Dict mapping instance -> [x1, y1, x2, y2]
│
├── processed/                           # 27 GB: Active files required for downstream modeling
│   ├── netlists/netlist/                # 54 flattened gate-level Verilog files (.v)
│   └── DEF_decompressed/DEF/            # 500 uncompressed placed DEF layouts (.def)
│
├── metadata/                            # 7.4 MB: Machine-readable manifests and indices
│   ├── dataset_index.csv                # Unified master index (10,242 rows)
│   ├── dataset_index.json               # Master index in JSON format
│   ├── netlist_manifest.csv             # Inspection metrics for 54 netlists
│   ├── def_manifest.csv                 # Structural audit of 500 DEF layouts
│   ├── design_manifest.csv              # Cross-matching matrix across 54 designs
│   ├── lef_cell_mapping.json            # LEF compatibility and cell-type mapping analysis
│   ├── tech_files_manifest.csv          # Inventory of system EDA tech files
│   └── audit_summary.json               # Top-level audit statistics
│
└── preprocess_scripts/                  # Helper preprocessing scripts
```

---

## 3. Raw Files Inventory

All original compressed archives are preserved in `dataset/raw/` to ensure 100% reproducibility:

| File Name | Size | Checksum (MD5) | Description |
|---|---|---|---|
| `circuitnet.lef` | 7.84 MB | `7f7a1f592d6e326bdf3b5e40733d0f62` | Technology LEF (18 layers, CoreSite, 915 macros) |
| `netlist.tar.gz` | 47.34 MB | `73855e9ad715ee27c08283eb26c04f91` | Compressed archive of 54 gate-level netlists |
| `DEF-place-0.tar.gz` | 2.86 GB | `532c53a2cb859083236e76fae6396e95` | Compressed archive of 500 placed DEF layouts |
| `graph_information.tar.gz` | 66.42 MB | `6624f16df5a0aa329a260565ae8d0a4c` | Graph topological attributes for all 54 netlists |
| `instance_placement_micron.tar.gz` | 5.70 GB | `4b0ee77b4ba7ea04344485583bdfd80d` | Compressed archive of 10,242 placement samples |

---

## 4. Circuit Graph Files (`dataset/circuit_graph/`)

Topological graph attributes are stored as NumPy binary arrays (`.npy`), with exact 1-to-1 correspondence with the 54 netlists:

| Subdirectory | File Count | Array Shape | Data Types | Contents |
|---|---|---|---|---|
| `node_attr/` | 54 files | $(2 \times N_{\text{nodes}})$ | `object` (string, string) | Row 0: Instance hierarchy name<br>Row 1: LEF standard cell type |
| `net_attr/` | 54 files | $(1 \times M_{\text{nets}})$ | `object` (string) | Row 0: Signal net name |
| `pin_attr/` | 54 files | $(3 \times P_{\text{pins}})$ | `object` (str, int, int) | Row 0: Pin name<br>Row 1: Node index<br>Row 2: Net index |

- Total extracted size: **533 MB**
- Coverage: **100% (54 of 54 netlists represented)**

---

## 5. Placement Files (`dataset/placement/instance_placement/`)

Contains **10,242 placement files** in `.npy` format:
- Total extracted size: **39 GB**
- Storage format: NumPy object array containing a Python `dict`
- Dictionary structure: `{instance_name: [x1, y1, x2, y2]}`
- Coordinate representation:
  - Despite the tarball name (`instance_placement_micron.tar.gz`) and internal extraction folder name (`instance_placement_gcell`), the values are **discrete GCell / tile coordinates** $[x_1, y_1, x_2, y_2] \in [0, 255]$ on a $256 \times 256$ grid where each tile is $2.25\,\mu\text{m} \times 2.25\,\mu\text{m}$.
  - For standard cells, $x_1=x_2$ and $y_1=y_2$ (or 1 tile span).
  - For large macros (`PLL_i`, `sp_ram_bank_i`), $[x_1, y_1, x_2, y_2]$ represents the full multi-tile bounding box matching DEF coordinates.

---

## 6. Numerical Counts & Cross-Matching

| Entity | Count | Cross-Matching Coverage |
|---|---|---|
| **Placement Samples** | **10,242** | 100% match a known design and graph attribute set |
| **Circuit Graph Attribute Sets** | **54** | 100% match the 54 gate-level netlists (1:1) |
| **Gate-Level Netlists** | **54** | All 54 have corresponding graph attributes |
| **DEF Physical Layouts** | **500** | Concentrated on `RISCY-a-1` across `c2` (247), `c5` (245), `c20` (8) |
| **Samples with Graph Attributes** | **10,242 (100.0%)** | All 10,242 placement samples have complete graph features |
| **Samples with Netlists** | **10,242 (100.0%)** | All 10,242 placement samples have gate-level netlists |
| **Samples with DEF Layouts** | **500 (4.88%)** | 500 samples have full uncompressed DEF layouts |

---

## 7. Design Names and Parameter Naming Convention

### Design Name Nomenclature
Each sample filename follows the verified CircuitNet pattern:
$$\text{\{ID\}-\{Design\}-\{\#Macros\}-c\{Clock\}-u\{Utilization\}-m\{Macro placement\}-p\{Power mesh\}-f\{Filler\}}.\text{npy}$$
*Example:* `6589-RISCY-FPU-b-2-c5-u0.85-m1-p8-f1.npy`
- `ID`: 6589
- `Design`: `RISCY-FPU-b`
- `#Macros`: `2`
- `Clock`: `c5` (Target period: 5.0 ns)
- `Utilization`: `0.85` (Target placement density: 85%)
- `Macro placement`: `m1` (Macro floorplan strategy index)
- `Power mesh`: `p8` (PDN top-metal grid configuration)
- `Filler stage`: `f1` (Post-placement filler insertion)

### Distribution Across Dataset (10,242 Samples)

#### Base Designs (6 configurations)
- `zero-riscy-a`: 2,042 samples
- `RISCY-a`: 2,003 samples
- `RISCY-FPU-a`: 1,969 samples
- `RISCY-b`: 1,858 samples
- `RISCY-FPU-b`: 1,248 samples
- `zero-riscy-b`: 1,122 samples

#### Macro Count (# of macros instantiated)
- `1`: 3,861 samples
- `2`: 3,090 samples
- `3`: 3,291 samples

#### Clock Constraints
- `c2` (2.0 ns / 500 MHz): 3,250 samples
- `c5` (5.0 ns / 200 MHz): 4,172 samples
- `c20` (20.0 ns / 50 MHz): 2,820 samples

#### Placement Density / Utilization ($u$)
- `0.70`: 2,269 samples
- `0.75`: 2,262 samples
- `0.80`: 2,216 samples
- `0.85`: 1,962 samples
- `0.90`: 1,533 samples

#### Macro Placement Configurations ($m$)
- `m1`: 3,421 samples
- `m2`: 3,165 samples
- `m3`: 2,950 samples
- `m4`: 705 samples
- `mNone`: 1 sample (authentic edge-case sample in CircuitNet)

#### Power Mesh Configurations ($p$)
- Balanced across 8 settings: `p1` (1273), `p2` (1255), `p3` (1271), `p4` (1264), `p5` (1298), `p6` (1302), `p7` (1292), `p8` (1287)

#### Filler Insertion Stage ($f$)
- `f0` (no placement filler / after routing): 4,385 samples
- `f1` (filler inserted post-placement): 5,857 samples

---

## 8. Files Required for Project vs Excluded vs Deleted

### Required Files (Retained)
1. `dataset/raw/*`: All 5 raw source archives + `circuitnet.lef` retained for reproducibility.
2. `dataset/circuit_graph/*`: 162 attribute files (`net_attr`, `node_attr`, `pin_attr`) required for heterogeneous circuit graph construction and GraphSAGE node embedding.
3. `dataset/placement/instance_placement/*`: All 10,242 placement samples required for RL ground-truth placement supervision, HPWL calculation, and state formulation.
4. `dataset/processed/netlists/`: 54 Verilog netlists required for graph topology and OpenROAD synthesis verification.
5. `dataset/processed/DEF_decompressed/`: 500 uncompressed DEFs required for OpenROAD baseline validation.
6. `dataset/metadata/*`: Master indices and manifests.

### Intentionally Excluded Files
- IR-drop feature maps (unneeded for placement optimization).
- Dynamic switching activity files (`.vcd`, `.saif`).
- Proprietary TSMC 28nm `.lib` and `.sdc` files (withheld by CircuitNet; replaced by structural proxy models).

### Deleted Items & Rationale
All deleted items were documented in `docs/DATASET_CLEANUP.md`:
1. `dataset/graph_features/graph_features/instance_placement_gcell.tar.gzi53y992p.part` (31.5 MB): Incomplete partial download fragment.
2. `dataset/graph_features/graph_features/graph_information.tar.gz` (66.4 MB): Exact bit-for-bit duplicate of preserved raw archive (MD5: `6624f16df5a0aa329a260565ae8d0a4c`).
3. `dataset/processed/sample_1/` (54.7 MB): Single-sample duplicate of DEF 1 (MD5: `304c0559797b68b5143e473b7a98f47e`).
4. `dataset/processed/DEF/` (2.86 GB): 500 intermediate `.def.gz` files identical to `dataset/raw/DEF-place-0.tar.gz`.

---

## 9. Disk Usage Accounting

| Stage | Total Dataset Size | Raw Archives | Circuit Graph | Placement | Processed Netlists/DEFs | Metadata |
|---|---|---|---|---|---|---|
| **Before Cleanup** | **77.0 GB** | 2.8 GB | 533 MB | 39.0 GB | 30.0 GB | 7.4 MB |
| **After Cleanup** | **74.1 GB** | 8.1 GB | 533 MB | 39.0 GB | 27.0 GB | 7.4 MB |
| **Net Reclaimed** | **~2.85 GB** | *(Consolidated)*| *(Moved)* | *(Moved)* | *(Deduplicated)* | *(Preserved)* |

---

## 10. Post-Cleanup Verification Results

A comprehensive verification test suite (`validate_dataset.py`) was executed:
- **File Counts:** Passed (5 raw files, 54 netlists, 54 net_attr, 54 node_attr, 54 pin_attr, 500 DEFs, 10,242 placement files).
- **Archive Integrity:** Passed (`tar -tzf` verified exit code 0 for all archives).
- **NumPy Loading:** Passed (Tested across `RISCY-a-1-c2`, `RISCY-FPU-b-2-c5`, `zero-riscy-b-1-c5`; all returned non-empty dictionaries with valid coordinate bounds).
- **Dataset Master Index:** Passed (Verified 10,242 rows in [`dataset/metadata/dataset_index.csv`](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/dataset_index.csv)).

---

## 11. Known Limitations

1. **DEF Physical Layout Coverage:** While all 54 designs have gate-level netlists, circuit graph attributes, and placement `.npy` files, full commercial DEF files are present for 500 samples (covering `RISCY-a-1-c2`, `RISCY-a-1-c5`, and `RISCY-a-1-c20`). The remaining designs are represented via the 10,242 placement `.npy` files and graph attributes.
2. **Standard Cell Coordinate Space:** Placement `.npy` files encode discrete tile/GCell coordinates ($256 \times 256$ grid, $2.25\,\mu\text{m}$ per tile) rather than raw DBU nanometer coordinates. This is directly compatible with the tile-based feature representations in CircuitNet and Agnesina et al.
