# Missing Training Design Strategy: zero-riscy-b-2-c2 & zero-riscy-b-2-c20

## 1. Executive Summary & Problem Formulation
In the Phase 11B placement inventory audit, all 54 canonical graph designs in the CircuitNet 28nm dataset were cross-referenced against the raw placement dataset (`dataset/placement/instance_placement/`). The audit established:
- **Total Canonical Graph Designs:** 54
- **Held-Out Benchmark Designs:** 3 (`RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`)
- **Training Candidate Designs:** 51
- **Designs with Valid CircuitNet Placement Samples:** 52 / 54 (96.3%)
- **Training Designs with Placement Samples:** 49 / 51 (96.1%)
- **Missing Placement Samples:** Exactly 2 designs:
  1. `zero-riscy-b-2-c2`
  2. `zero-riscy-b-2-c20`

Both missing designs possess complete canonical graph representations (`dataset/graphs/zero-riscy-b-2-c2_graph.npz`, `dataset/graphs/zero-riscy-b-2-c20_graph.npz`), gate-level netlists, and cell LEF definitions, but have zero corresponding `.npy` placement samples in the CircuitNet release.

---

## 2. Leakage Protection & Inadmissible Solutions
Under Phase 11A and Phase 11B integrity mandates, the following practices are **STRICTLY PROHIBITED**:
1. **No Held-Out Leakage:** Held-out placement templates (from `RISCY-a-1-c2`, `RISCY-a-1-c5`, or `RISCY-a-1-c20`) MUST NOT be borrowed, scaled, or adapted for `zero-riscy` designs.
2. **No Cross-Family Topology Borrowing:** Sizing or floorplan shapes must not be copied from unrelated designs with disparate gate counts.
3. **No Synthetic Fiction:** Placing cells at arbitrary coordinates without a documented physical rationale is prohibited.

---

## 3. Evaluated Resolution Strategies

| Strategy | Description | Scientific Validity | Leakage Risk | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Strategy A: Dataset Exclusion (Pruning)** | Remove `zero-riscy-b-2-c2` and `zero-riscy-b-2-c20` from the active RL training set, leaving **49 fully grounded training designs**. | **High** (Standard practice when raw data is missing; preserves pure authentic data distribution). | **Zero** | **RECOMMENDED FOR RL (Primary)** |
| **Strategy B: OpenROAD Autonomous Global Placement** | Run OpenROAD `global_placement` (RePlAce) directly on the reconstructed gate-level netlist to establish an independent physical baseline. | **High** (Produces a valid physical baseline purely through OpenROAD algorithms). | **Zero** (Independent engine execution). | **SECONDARY (Optional Augmentation)** |
| **Strategy C: Template Transfer** | Transfer placement coordinates from `zero-riscy-a` or `RISCY` families. | **Unacceptable** (Distorts topological connectivity and creates unphysical net stretches). | **High** | **REJECTED** |

---

## 4. Operational Protocol for Phase 11C and Phase 12
1. **Primary Policy (Phase 11C & Phase 12 RL Environment):**
   - The active training pool for the RL placement optimization agent is locked at **49 training designs**.
   - These 49 designs provide over 10,200 authentic CircuitNet placement samples, representing an extensive, diverse training distribution.
2. **Audit Tracking:**
   - Both `zero-riscy-b-2-c2` and `zero-riscy-b-2-c20` remain indexed in the design registry but are explicitly flagged with `placement_status: MISSING_RAW_NPY` and `training_eligibility: EXCLUDED_PENDING_OPENROAD_GPL`.
3. **Reproducibility Guarantee:**
   - No training script or evaluation script will fail silently due to missing files. Environment initializers will validate design eligibility against the Phase 11B/11C manifest prior to episode sampling.
