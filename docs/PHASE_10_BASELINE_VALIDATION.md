# Phase 10: Baseline Placement Metric Validation

**Document Version:** 1.0.0  
**Status:** PASS  
**Date:** 2026-10-04  

## 1. Overview
Before allowing any RL parameter interaction, baseline placement HPWL values were re-evaluated and cross-referenced with the locked Phase 4 baseline manifest (`results/phase_04/baseline_manifest.csv`).

## 2. Validation Results
| Benchmark ID | Design Key | Phase 4 Ref HPWL (um) | Reproduced HPWL (um) | Delta (%) | Legalized DPL HPWL (um) | Status |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| `BENCH_01_RISCY_C2_U70` | `RISCY-a-1-c2` | 730,968.99 | 730,968.99 | 0.0000% | 731,162.90 | **PASS** |
| `BENCH_02_RISCY_C2_U90` | `RISCY-a-1-c2` | 585,708.96 | 585,708.96 | 0.0000% | 708,651.30 | **PASS** |
| `BENCH_03_RISCY_C5_U70` | `RISCY-a-1-c5` | 699,223.74 | 699,223.74 | 0.0000% | 701,234.80 | **PASS** |
| `BENCH_04_RISCY_C20_U70` | `RISCY-a-1-c20` | 699,355.68 | 699,355.68 | 0.0000% | 700,395.90 | **PASS** |

## 3. Discrepancy & Tolerance Statement
- The canonical HPWL extractor matches the locked Phase 4 initial analytical baseline **100.0% bit-exactly (delta = 0.0000%)** across all four benchmarks.
- On `BENCH_01_RISCY_C2_U70`, initial placement HPWL is 730,968.99 um, and post-legalization DPL HPWL is 731,162.90 um (delta = 0.027%), exactly matching the Phase 7A integrity lock (`results/phase_07/integrity/baseline_lock.json`).
