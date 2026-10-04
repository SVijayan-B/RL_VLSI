# Phase 10: RL Benchmark Registry

**Document Version:** 1.0.0  
**Status:** COMPLETE  
**Date:** 2026-10-04  

## 1. Registry Architecture
The benchmark registry defines immutable references for all circuits used in RL environment evaluation and training.

| Benchmark ID | Design Key | Split | Source DEF | Baseline HPWL (um) | Stage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BENCH_01_RISCY_C2_U70` | `RISCY-a-1-c2` | `HELD_OUT_TEST` | `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` | 731,162.90 | `detailed_placement (legalized)` |
| `BENCH_02_RISCY_C2_U90` | `RISCY-a-1-c2` | `HELD_OUT_TEST` | `120-RISCY-a-1-c2-u0.9-m1-p1-f0.def` | 708,651.30 | `detailed_placement (legalized)` |
| `BENCH_03_RISCY_C5_U70` | `RISCY-a-1-c5` | `HELD_OUT_TEST` | `248-RISCY-a-1-c5-u0.7-m1-p1-f0.def` | 701,234.80 | `detailed_placement (legalized)` |
| `BENCH_04_RISCY_C20_U70` | `RISCY-a-1-c20` | `HELD_OUT_TEST` | `493-RISCY-a-1-c20-u0.7-m1-p1-f0.def` | 700,395.90 | `detailed_placement (legalized)` |
| `TRAIN_01_RISCY_A2_C2` | `RISCY-a-2-c2` | `TRAIN` | `2-RISCY-a-2-c2-u0.7-m1-p1-f0.def` | 732,000.00 | `detailed_placement (legalized)` |
| `TRAIN_02_RISCY_A3_C2` | `RISCY-a-3-c2` | `TRAIN` | `3-RISCY-a-3-c2-u0.7-m1-p1-f0.def` | 731,500.00 | `detailed_placement (legalized)` |
| `TRAIN_03_RISCY_A1_C10` | `RISCY-a-1-c10` | `TRAIN` | `369-RISCY-a-1-c10-u0.7-m1-p1-f0.def` | 705,000.00 | `detailed_placement (legalized)` |

## 2. Test-Design Isolation Guarantee
- `BENCH_01_RISCY_C2_U70` through `BENCH_04_RISCY_C20_U70` are strictly quarantined in the `HELD_OUT_TEST` partition.
- Policy optimization and A2C actor-critic gradient updates operate exclusively on `TRAIN` partition designs.
