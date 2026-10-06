# Phase 11A — Held-Out Test Leakage Audit

## 1. Executive Summary
This audit rigorously investigates whether any held-out evaluation benchmarks (`BENCH_01` to `BENCH_04`), their associated design keys (`RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`), or their source DEF layouts were improperly accessed during Phase 11 A2C training.

---

## 2. Leakage Classification Scheme
- **NOT_ACCESSED**: Neither the entity nor its data was loaded or queried during training.
- **METADATA_ONLY**: Entity is listed in frozen manifests/registries, but quarantined from training loops.
- **TRAINING_ACCESS**: Entity data was ingested during environment execution or policy gradient computation.
- **REWARD_ACCESS**: Held-out metrics were queried to calculate reinforcement learning rewards.
- **CHECKPOINT_SELECTION_ACCESS**: Checkpoints were ranked or saved based on held-out benchmark performance.
- **UNKNOWN**: Status cannot be proven.

---

## 3. Component-by-Component Audit

| Target Entity | Classification | Empirical Evidence / Rationale |
| :--- | :--- | :--- |
| **BENCH_01_RISCY_C2_U70** | **METADATA_ONLY / REWARD_INDIRECT** | Quarantined from `active_benchmarks`. However, its baseline HPWL (731,162.90 µm) and source DEF (`1-RISCY-a-1-c2-u0.7-m1-p1-f0.def`) were referenced by `TRAIN_01` and `TRAIN_02` in `results/phase_10/benchmark_registry.csv`. |
| **BENCH_02_RISCY_C2_U90** | **NOT_ACCESSED** | Zero occurrences in training logs or environment execution. |
| **BENCH_03_RISCY_C5_U70** | **NOT_ACCESSED** | Zero occurrences in training logs or environment execution. |
| **BENCH_04_RISCY_C20_U70** | **NOT_ACCESSED** | Zero occurrences in training logs or environment execution. |
| **RISCY-a-1-c2** (Graph/Embedding) | **NOT_ACCESSED** | Phase 11 state ingested embeddings for `RISCY-a-2-c2` and `RISCY-a-3-c2`, NOT `RISCY-a-1-c2`. |
| **RISCY-a-1-c5** (Graph/Embedding) | **NOT_ACCESSED** | Never loaded during training. |
| **RISCY-a-1-c20** (Graph/Embedding) | **NOT_ACCESSED** | Never loaded during training. |
| **1-RISCY-a-1-c2-u0.7-m1-p1-f0.def** | **TRAINING_ACCESS** | Recorded as `source_DEF` for `TRAIN_01` and `TRAIN_02` in `benchmark_registry.csv`. Evaluator baseline was anchored to this DEF's legalized HPWL. |

---

## 4. Leakage Findings & Scientific Interpretation
1. **Direct Gradient/Policy Leakage**: **NONE**. The held-out benchmark IDs (`BENCH_01` to `BENCH_04`) were strictly excluded from training loops (`self.df_bench["split"] == "TRAIN"`). No gradient update was computed on test benchmarks.
2. **Checkpoint Selection**: **NONE**. Checkpoint selection in Phase 11 was computed strictly on training episode returns.
3. **Indirect Physical Layout Coupling**: **CONFIRMED DEF COUPLING**. Because CircuitNet N28 only provides physical placed DEFs for `RISCY-a-1` designs, Phase 10's benchmark registry assigned `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` as the physical template for training benchmarks `TRAIN_01` and `TRAIN_02`.
   - While the graph embeddings were from the training set (`RISCY-a-2-c2` and `RISCY-a-3-c2`), the DEF layout and baseline HPWL belonged to `RISCY-a-1-c2`.
   - This coupling must be resolved before Phase 12.
