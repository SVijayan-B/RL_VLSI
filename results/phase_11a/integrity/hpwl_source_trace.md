# Phase 11A — HPWL Source Trace

## 1. Executive Summary
This document provides the definitive architectural trace of the placement and HPWL evaluation pipeline during Phase 11 A2C training, explaining the exact provenance of the observed initial HPWL value of **731,162.90 µm** and the design sampling behavior across seeds 42–46.

---

## 2. End-to-End Execution Trace

```
Training Step
    ↓
src/rl/train_a2c_multiseed.py (train_seed())
    ↓
env.reset() [src/rl/environment.py:76-132]
    ↓
Benchmark Selection from self.active_benchmarks
    ↓
Lookup in results/phase_10/benchmark_registry.csv
    ↓
self.baseline_hpwl extracted from default_dpl_baseline_HPWL_um
    ↓
Initial HPWL set to 731,162.90 µm
    ↓
Transition Step [env.step(action_id)]
    ↓
Analytical/Layout sensitivity update anchored to self.baseline_hpwl
    ↓
Relative HPWL reward computation: (HPWL_{t-1} - HPWL_t) / max(|HPWL_{t-1}|, 1e-6)
```

---

## 3. Detailed Component Breakdown

### Stage 1: Environment Initialization & Active Benchmarks
In `src/rl/environment.py` (lines 48–58):
```python
self.df_bench = pd.read_csv(benchmark_registry_path)
if self.quarantine_test_designs:
    self.active_benchmarks = self.df_bench[self.df_bench["split"] == "TRAIN"].copy()
```
When `quarantine_test_designs=True`, the environment filters `results/phase_10/benchmark_registry.csv` to rows where `split == "TRAIN"`.
Inspection of `results/phase_10/benchmark_registry.csv` reveals exactly 6 rows:
- 4 rows with `split == "HELD_OUT_TEST"` (`BENCH_01` to `BENCH_04`)
- 2 rows with `split == "TRAIN"`:
  - `TRAIN_01_RISCY_A2_C2` (design `RISCY-a-2-c2`)
  - `TRAIN_02_RISCY_A3_C2` (design `RISCY-a-3-c2`)

Consequently, `len(self.active_benchmarks) == 2`. Only these two designs were available for training episodes.

### Stage 2: Reset and Baseline HPWL Assignment
In `src/rl/environment.py` (lines 90–106):
```python
idx = np.random.randint(0, len(self.active_benchmarks))
self.current_benchmark = self.active_benchmarks.iloc[idx].to_dict()
...
self.baseline_hpwl = float(
    self.current_benchmark.get("default_dpl_baseline_HPWL_um") or
    self.current_benchmark.get("rl_start_HPWL_um") or
    self.current_benchmark.get("baseline_HPWL") or
    self.current_benchmark.get("initial_HPWL_um")
)
self.current_hpwl = self.baseline_hpwl
self.previous_hpwl = self.baseline_hpwl
```
In `results/phase_10/benchmark_registry.csv`:
For both `TRAIN_01_RISCY_A2_C2` and `TRAIN_02_RISCY_A3_C2`:
- `default_dpl_baseline_HPWL_um = 731162.9`
- `source_DEF = dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def`

Thus, `self.baseline_hpwl` was assigned `731,162.90 µm` for every training episode.

### Stage 3: Provenance of the 731,162.90 µm Baseline
Where did `731,162.90 µm` originate?
1. It is the validated Phase 4 / Phase 7 baseline for `BENCH_01_RISCY_C2_U70` (design `RISCY-a-1-c2`, DEF `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def`), locked in `results/phase_07/integrity/baseline_lock.json`.
2. When `scripts/phase10_create_benchmark_registry.py` created the registry, it assigned `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` and the baseline HPWL of `731,162.90 µm` to the training entries because raw CircuitNet N28 only contains DEF layouts for `RISCY-a-1` designs (500 DEFs covering `c2`, `c5`, and `c20`).
3. Hence, the HPWL trajectory in Phase 11 was anchored to `731,162.90 µm` because the training benchmarks were coupled to this DEF and baseline in the registry.

---

## 4. Conclusion
The initial HPWL value of 731,162.90 µm did not arise from an ad-hoc hack or random initialization; it was directly read from `results/phase_10/benchmark_registry.csv` as configured in Phase 10. However, because only 2 training benchmarks were defined in that registry, the training process was confined to 2 designs instead of the full 51 training designs.
