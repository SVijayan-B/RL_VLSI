# Phase 11A — Training Environment Integrity Audit

**Document Version:** 1.0.0  
**Status:** COMPLETE (AUDIT COMPLETED)  
**Date:** 2026-10-04  
**Integrity Verdict:** **FAIL** (Implementation Coupling & Sampling Limitation Detected)  

---

## 1. Objective
Determine why Phase 11 A2C training logs contain only a small subset of training design IDs (`RISCY-a-2-c2`, `RISCY-a-3-c2`) while the placement/HPWL trajectory was anchored to the held-out benchmark baseline (`731,162.90 µm`). Rigorously trace the data and code flow, verify dataset constraints, audit held-out leakage, and establish the scientific validity of the training environment.

---

## 2. Authoritative Phase 11 Contract
- **Training Protocol:** `configs/phase11_a2c_training_protocol.json`
- **Expected Training Designs Count:** 51
- **Held-Out Benchmarks:** `BENCH_01_RISCY_C2_U70`, `BENCH_02_RISCY_C2_U90`, `BENCH_03_RISCY_C5_U70`, `BENCH_04_RISCY_C20_U70`
- **Held-Out Design Keys:** `RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`
- **Graph Representation:** Frozen GraphSAGE 32-D graph embeddings (`results/phase_09/checkpoints/graphsage_best.pt`)
- **State Dimension:** 41 (32 graph embedding + 6 parameters + 2 metrics + 1 progress)
- **Action Space:** 8 discrete OpenROAD macro-actions
- **Reward:** Relative HPWL improvement: $r_t = \frac{\text{HPWL}_{t-1} - \text{HPWL}_t}{\max(|\text{HPWL}_{t-1}|, 1e-6)}$
- **Official Seeds:** 42, 43, 44, 45, 46

---

## 3. Expected Training Partition
- The CircuitNet N28 dataset inventory contains 54 total gate-level netlists and canonical circuit graphs.
- 3 designs are reserved for the held-out test partition: `RISCY-a-1-c2`, `RISCY-a-1-c5`, and `RISCY-a-1-c20`.
- The remaining **51 designs** form the expected `TRAIN` partition (`dataset/metadata/design_manifest.csv`).

---

## 4. Actual Training Partition Observed
- **Actually Sampled Training Designs:** **2** (`RISCY-a-2-c2`, `RISCY-a-3-c2`).
- **Missing from Active Training:** 49 of the 51 training designs.
- Complete inventory generated in `results/phase_11a/integrity/training_design_inventory.csv`.

---

## 5. Episode Sampling Audit
Analysis of 5,000 transitions across seeds 42–46 in `results/phase_11/seed_*/transitions.csv` reveals:
- Total episodes: 500 (100 per seed).
- Total transitions: 5,000 (1,000 per seed).
- Only two designs were ever sampled:
  - `RISCY-a-2-c2`: ~50% of episodes
  - `RISCY-a-3-c2`: ~50% of episodes
- Complete breakdown recorded in `results/phase_11a/integrity/actual_training_sampling.csv` and `results/phase_11a/integrity/design_sampling_by_seed.csv`.

---

## 6. Design → DEF Mapping Audit
- Audit of `dataset/processed/DEF_decompressed/DEF/` (and documented in `docs/DATASET_MANIFEST.md`) proves that the physical placed DEF files in CircuitNet N28 are available for **only 3 designs**:
  - `RISCY-a-1-c2` (247 DEFs)
  - `RISCY-a-1-c5` (245 DEFs)
  - `RISCY-a-1-c20` (8 DEFs)
- The remaining 51 designs have gate-level netlists and graph attributes, but **zero uncompressed placed DEF layouts**.
- Consequently, Phase 10's registry creation script (`scripts/phase10_create_benchmark_registry.py`) mapped `TRAIN_01` and `TRAIN_02` to `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def`.
- Result: **FAIL** (`results/phase_11a/integrity/design_def_consistency.csv`). Training design keys were mismatched with the physical DEF layout.

---

## 7. HPWL Source Trace
- Detailed trace documented in `results/phase_11a/integrity/hpwl_source_trace.md`.
- `env.reset()` selects an active benchmark from `results/phase_10/benchmark_registry.csv`.
- `self.baseline_hpwl` is initialized from `default_dpl_baseline_HPWL_um`.
- For `TRAIN_01` and `TRAIN_02`, this field is hardcoded to `731162.9` µm (the Phase 4 / Phase 7 baseline of `BENCH_01_RISCY_C2_U70`).
- The initial HPWL of 731,162.90 µm is therefore directly derived from `results/phase_10/benchmark_registry.csv`.

---

## 8. BENCH_01 / Held-Out Leakage Audit
- Detailed in `results/phase_11a/integrity/leakage_audit.md`.
- **Policy Gradients & Checkpoint Selection:** **CLEAN (NOT_ACCESSED)**. Held-out benchmark IDs `BENCH_01` to `BENCH_04` were quarantined from training loops and checkpoint ranking.
- **Physical Layout / DEF Coupling:** **INDIRECT DEF ACCESS**. `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` (which belongs to held-out design `RISCY-a-1-c2`) was referenced as `source_DEF` in `TRAIN_01` and `TRAIN_02`.

---

## 9. Graph Embedding Mapping Audit
- Audit of 15 sample designs against `results/phase_09/graph_embeddings.csv` and `dataset/graphs/` confirms 100% mathematical integrity:
  - Embeddings are 32-dimensional, non-NaN, and strictly match their design keys.
  - Verification saved in `results/phase_11a/integrity/embedding_mapping_audit.csv` (**PASS**).

---

## 10. Parameter Transition Audit
- State parameter vector transitions strictly adhere to 6-parameter bounds and the 8 verified OpenROAD macro-actions. No invalid parameter states or actions were observed.

---

## 11. Reward Recalculation Audit
- 100 sampled transitions independently recomputed across all 5 seeds.
- Maximum absolute difference between logged reward and recomputed reward: $< 10^{-7}$ (**PASS**, `results/phase_11a/integrity/reward_recomputation.csv`).

---

## 12. Root Cause
1. **Upstream Dataset Asymmetry:** The raw CircuitNet N28 dataset provides DEF physical layouts exclusively for `RISCY-a-1` configurations (which host the held-out test benchmarks). The 51 training designs possess netlists and graph attributes, but no raw placed DEF files.
2. **Phase 10 Benchmark Registry Restriction:** `scripts/phase10_create_benchmark_registry.py` only registered 2 training benchmarks (`TRAIN_01_RISCY_A2_C2` and `TRAIN_02_RISCY_A3_C2`) and associated them with `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` and baseline `731,162.90 µm`.
3. **Environment Filtering:** `VLSIPlacementEnv` filters to `split == "TRAIN"`, restricting episode sampling to these 2 designs.

---

## 13. Corrective Action
1. **Preserve Phase 11 Artifacts:** Do not overwrite or delete existing Phase 11 logs/checkpoints.
2. **Design-to-Placement Decoupling / Multi-Design Calibration:**
   - To train across the 51 designs, the training environment must decouple topological graph embeddings (which exist for all 51 designs) from DEF geometry, OR synthesize/generate placement solutions for training netlists.
   - Decouple the training baseline from `BENCH_01` (`731,162.90 µm`).
3. **Formal Resolution in Phase 11B:** Rerun training only after the training registry is expanded and validated.

---

## 14. Files Changed
- `docs/PROGRESS.md` (Updated to reflect Phase 11A audit).

---

## 15. Files NOT Changed
- No modifications to upstream dataset archives.
- No modifications to Phase 8 / Phase 9 graph models or embeddings.
- Existing Phase 11 multi-seed checkpoints and logs preserved as historical records.

---

## 16. Validation Results
- Audit CSVs and MD traces generated in `results/phase_11a/integrity/`.
- Repository test suite remains fully operational (63/63 tests passing).

---

## 17. Scientific Integrity Verdict
**PHASE_11A = FAIL**
- **Rationale:** While policy gradients and checkpoint selection were isolated from test benchmarks, the training environment only sampled 2 of the 51 declared training designs, and used a DEF layout and baseline HPWL anchored to held-out design `RISCY-a-1-c2`. Phase 12 cannot proceed until this environment limitation is repaired.
