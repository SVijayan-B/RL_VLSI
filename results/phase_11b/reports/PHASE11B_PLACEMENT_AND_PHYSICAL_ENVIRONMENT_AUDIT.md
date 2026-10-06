# Phase 11B Audit: CircuitNet Placement Coverage & OpenROAD Physical Training Environment

**Document Version:** 1.0.0  
**Status:** COMPLETE (AUDIT COMPLETED)  
**Date:** 2026-10-04  
**Classification:** **CLASS B** (PLACEMENT DATA AVAILABLE BUT OPENROAD PHYSICAL RECONSTRUCTION INCOMPLETE)  

---

## 1. Objective
Rigorously audit the 10,242 CircuitNet placement samples, evaluate instance overlap against all 54 canonical graph designs, verify coordinate units, analyze HPWL proxy feasibility, test OpenROAD training-design physical reconstruction, and resolve the Phase 11A integrity failure.

---

## 2. Dataset Inventory
The CircuitNet N28 dataset in `dataset/` contains:
- **LEF Technology:** `dataset/raw/circuitnet.lef` (18 layers, 915 standard cell library macros).
- **Netlists:** `dataset/processed/netlists/netlist/*.v` (54 flattened gate-level Verilog files).
- **Canonical Graphs:** `dataset/graphs/*.npz` (54 bipartite & cell-projected circuit graphs).
- **Placed DEF Layouts:** `dataset/processed/DEF_decompressed/DEF/*.def` (500 placed DEFs, strictly covering `RISCY-a-1-c2`, `c5`, and `c20`).
- **Placement Archive:** `dataset/placement/instance_placement/*.npy` (10,242 placement samples).

---

## 3. 54-Design Graph Inventory
All 54 netlists possess corresponding canonical graph `.npz` files with:
- 7-D cell feature matrices (`cell_features`)
- 4-D net feature matrices (`net_features`)
- Topological bipartite edges (`edge_index_bipartite`) and cell-cell projected edges (`edge_index_cell`)
- 32-D frozen GraphSAGE graph embeddings (`results/phase_09/graph_embeddings.csv`).

---

## 4. 51 / 3 Train-Heldout Split
- **Held-Out Test Partition (3 designs):**
  - `RISCY-a-1-c2` (Hosts `BENCH_01_RISCY_C2_U70` and `BENCH_02_RISCY_C2_U90`)
  - `RISCY-a-1-c5` (Hosts `BENCH_03_RISCY_C5_U70`)
  - `RISCY-a-1-c20` (Hosts `BENCH_04_RISCY_C20_U70`)
- **Training Partition (51 designs):**
  - All remaining 51 RISC-V SoC netlists (`RISCY-FPU-*`, `RISCY-a/b-*`, `zero-riscy-*`).

---

## 5. 10,242 Placement Sample Inventory
- All **10,242 `.npy` files** were enumerated and validated via multiprocessing.
- **Validity Status:** 10,242 / 10,242 samples are structurally valid NumPy dictionary objects.
- Each sample maps instance names to integer bounding boxes `[x1, y1, x2, y2]`.
- Summary report saved in `results/phase_11b/placement_coverage/placement_validity_report.csv` and inventory in `placement_sample_inventory.csv`.

---

## 6. Per-Design Placement Coverage
- **Coverage Summary:**
  - 52 of the 54 designs have active placement samples in `instance_placement/` (ranging from ~190 to 200 samples per design).
  - Among the **51 training designs**, **49 designs** have complete placement samples.
  - Exactly **2 designs** (`zero-riscy-b-2-c2` and `zero-riscy-b-2-c20`) have 0 placement samples in CircuitNet.
- Audit table saved in `results/phase_11b/placement_coverage/design_placement_coverage.csv`.

---

## 7. Instance Overlap
- Instance name overlap between netlist cells and placement dictionary keys averages **97.85%** across all covered designs.
- Detailed per-design overlap saved in `results/phase_11b/instance_overlap/instance_overlap_summary.csv`.

---

## 8. Coordinate and Spatial Unit Audit
- Placed DEFs define units as `2000 DBU/um` over a chip canvas of $\sim 585 \, \mu m \times 585 \, \mu m$ ($1,167,600 \times 1,165,800$ DBU).
- In contrast, all placement `.npy` files contain integer coordinates bounded in $[0, 255]$.
- **Authoritative Determination:** The placement coordinates are **GCELL_GRID_256x256** quantized feature bins, NOT raw microns or DBU.
- Full audit report in `results/phase_11b/placement_coverage/coordinate_unit_audit.md`.

---

## 9. Placement-Derived HPWL Feasibility
- Combining the 256x256 GCell instance bounding boxes with graph net connectivity allows calculating a **center-based Manhattan HPWL proxy**.
- Evaluated on a sample of 10 training designs (`results/phase_11b/hpwl_feasibility/placement_hpwl_feasibility.csv`).
- **Feasibility Verdict:** **FEASIBLE_AS_PROXY_ONLY**. It is valid as an analytical heuristic, but NOT equivalent to OpenROAD legalized HPWL.

---

## 10. OpenROAD Reconstruction Smoke Test
- Tested on training design `RISCY-a-2-c2` using `openroad/orfs:latest`.
- Standard cell LEF geometry loaded 915 macros cleanly without syntax errors.
- OpenROAD's Verilog parser (`read_verilog` / STA) flags syntax errors on complex port declarations (multidimensional packed arrays on top-level IO ports, e.g. line 49 `.gpio_padcfg ( { gpio_padcfg[31][5] ... } )`).
- Detailed log in `results/phase_11b/openroad_smoke/RISCY-a-2-c2/RISCY-a-2-c2_smoke_report.md`.

---

## 11. Global Placement Feasibility
- Standalone OpenROAD Global Placement (`global_placement`) requires timing `.lib` files or pre-placed IO pin constraints.
- Without commercial `.lib` files, OpenROAD cannot execute standard analytical global placement.
- **Feasibility Status:** **PARTIAL / BLOCKED_ON_LIB**.

---

## 12. Training Physical Leakage Audit
- Zero coupling to `BENCH_01`–`04` or `RISCY-a-1-c2-u0.7-m1-p1-f0.def`.
- Baseline `731,162.90 µm` has been removed from all training representations.
- Audit report in `results/phase_11b/reports/training_physical_leakage_audit.md`.

---

## 13. Methodological Decision
- Documented in `results/phase_11b/reports/methodology_decision.md`.
- Concludes that neither Option A (pure 256x256 GCell grid) nor Option B (raw unconstrained OpenROAD from netlist) can be naively adopted without a proper floorplan/def reconstruction layer.

---

## 14. Pass/Fail Gates
- [x] **GATE A:** 54 graph designs correctly identified (**PASS**)
- [x] **GATE B:** 51 training + 3 held-out split verified (**PASS**)
- [x] **GATE C:** Placement sample inventory complete (**PASS**, 10,242 samples)
- [x] **GATE D:** Placement coverage established (**PASS**, 49/51 training designs covered)
- [x] **GATE E:** Instance overlap established (**PASS**, 97.85% mean overlap)
- [x] **GATE F:** Coordinate units established (**PASS**, GCell Grid 256x256)
- [x] **GATE G:** Placement-derived HPWL feasibility established (**PASS**, proxy only)
- [x] **GATE H:** OpenROAD physical smoke test evaluated (**COMPLETE**, technology blockers identified)
- [x] **GATE I:** No held-out physical coupling (**PASS**, zero leakage detected)
- [x] **GATE J:** Global/detailed placement characterized (**COMPLETE**)

---

## 15. Final Classification
**CLASS B: PLACEMENT DATA AVAILABLE BUT OPENROAD PHYSICAL RECONSTRUCTION INCOMPLETE**
- **Meaning:** Authentic placement data exists across 49 of the 51 training designs in the 256x256 GCell format. However, direct OpenROAD physical synthesis requires standard-cell DEF floorplan initialization before DPL parameter actions can be evaluated physically.

---

## 16. Recommended Phase 11C Architecture
To enable rigorous, leak-free RL training across the training partition:
1. **Floorplan / DEF Reconstructor:** Construct a lightweight Python DEF generator that maps the 256x256 GCell instance bounding boxes into legalized DBU coordinates within standard cell rows using `circuitnet.lef`.
2. **Dedicated Training Baselines:** Calculate independent OpenROAD default DPL baselines for each training design DEF.
3. **Decoupled Training Execution:** The A2C agent will optimize parameters against these genuine training DEFs, completely isolated from `BENCH_01`–`04`.

---

## 17. Limitations
- Does not claim commercial Cadence Innovus equivalence.
- Acknowledges that 2 designs in CircuitNet (`zero-riscy-b-2-c2`, `zero-riscy-b-2-c20`) lack placement `.npy` files.
- Notes OpenROAD's strictness regarding Verilog port declarations.
