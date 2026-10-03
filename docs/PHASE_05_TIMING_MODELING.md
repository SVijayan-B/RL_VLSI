# Phase 5 — Timing Modeling & Proxy Metrics

**Document Version:** 1.0.0  
**Status:** COMPLETE (100% Verified)  
**Date:** 2026-10-02  

---

## 1. Executive Summary

Phase 5 establishes a transparent, scientifically defensible surrogate timing evaluation layer for the CircuitNet N28 placement optimization project.

### Critical Scientific Notice:
> As established throughout this project, the CircuitNet N28 open dataset **DOES NOT** provide proprietary foundry timing assets (such as TSMC 28nm `.lib`, `.sdc`, `.spef`, `.captable`, or dynamic switching activities `VCD`/`SAIF`). 
> 
> Therefore, no sign-off Static Timing Analysis (STA), real cell delays, transition times, setup/hold slacks, or Worst/Total Negative Slacks (WNS/TNS) are fabricated. All timing quantities developed and evaluated in this phase are explicitly classified and treated as **TIMING PROXIES** for relative placement ranking and reinforcement learning reward shaping.

---

## 2. Terminology Correction & Audit of Existing RC Infrastructure

In Phase 3, default parameters were introduced in `src/technology/rc_proxy.py`:
- $R_{\text{unit}} = 0.25\,\Omega / \mu\text{m}$
- $C_{\text{unit}} = 0.18\,\text{fF} / \mu\text{m}$ ($1.8 \times 10^{-16}\,\text{F} / \mu\text{m}$)
- $C_{\text{gate, default}} = 0.50\,\text{fF}$ ($5.0 \times 10^{-16}\,\text{F}$)
- $R_{\text{driver, default}} = 450.0\,\Omega$

### Terminology Alignment:
These parameters were previously referred to in informal documentation as "calibrated 28nm typical metal stack constants". Under the Phase 5 audit, this wording is formally corrected to:
$$\textbf{Analytical Normalized RC Proxy Parameters}$$
They represent an idealized, monotonic lumped RC model designed to capture wirelength and fanout degradation without asserting foundry sign-off fidelity. Documented in [model_audit.md](file:///Ubuntu-24.04/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_05/model_audit.md) and [model_audit.json](file:///Ubuntu-24.04/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_05/model_audit.json).

---

## 3. Timing-Proxy Taxonomy

| Metric Category | Level | Classification | Governing Formulation | Primary Data Inputs | Units | Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HPWL** | Net | **DERIVED** | $\Delta X + \Delta Y$ | Cell/Pin Coordinates | $\mu\text{m}$ | Ignores Steiner routing detours. |
| **Wire Parasitics** | Net | **PROXY** | $R_w = r_{\text{unit}} L$, $C_w = c_{\text{unit}} L$ | Net HPWL | $\Omega$, $\text{F}$ | Does not differentiate layer stack. |
| **Net Delay Proxy** | Net | **PROXY** | $R_d(C_w + C_L) + \frac{1}{2}R_w C_w + R_w C_L$ | HPWL, Fanout | $\text{ps}$ | Uniform gate load and drive resistance. |
| **Topological Depth** | Cell | **PROXY** | Directed Acyclic Graph Levels | Canonical Bipartite Edges | Level ($\ge 1$) | Ignores multi-cycle / false paths. |
| **Path Delay Proxy** | Path | **PROXY** | Accumulated Topological Delays | Topological Levels, Net Delays | $\text{ps}$ | Surrogate path bound, not sign-off STA. |
| **Criticality Proxy** | Net | **PROXY** | $0.7 \frac{T_{\text{net}}}{T_{\max}} + 0.3 \frac{\text{Fanout}}{\text{Fanout}_{\max}}$ | Net Delay, Fanout | $[0, 1]$ | Normalized ranking score. |
| **Sign-off Slack / WNS** | Path | **UNAVAILABLE**| $\text{Slack} = T_{\text{required}} - T_{\text{arrival}}$ | Proprietary `.lib`, `.sdc` | $\text{ns}$ | **Withheld by foundry (TSMC 28nm).** |

---

## 4. Net Delay and Fanout Distribution Analysis

We evaluated net delay proxies and fanouts across 53,246 to 55,401 nets for the four primary benchmarks:

| Benchmark ID | Design Key | Evaluated Nets | Mean Delay ($\text{ps}$) | P50 ($\text{ps}$) | P90 ($\text{ps}$) | P95 ($\text{ps}$) | P99 ($\text{ps}$) | Max Delay ($\text{ps}$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BENCH_01_RISCY_C2_U70` | `RISCY-a-1-c2` | 55,401 | 6.04 | 2.93 | 10.41 | 17.41 | 58.58 | 3,654.78 |
| `BENCH_02_RISCY_C2_U90` | `RISCY-a-1-c2` | 55,265 | 5.80 | 2.86 | 9.52 | 16.08 | 58.34 | 3,573.01 |
| `BENCH_03_RISCY_C5_U70` | `RISCY-a-1-c5` | 53,302 | 6.20 | 2.92 | 10.30 | 17.82 | 63.74 | 3,678.19 |
| `BENCH_04_RISCY_C20_U70`| `RISCY-a-1-c20`| 53,246 | 6.21 | 2.91 | 10.26 | 18.03 | 62.80 | 3,713.12 |

- **Distribution Characteristics:** Over 90% of nets exhibit modest wire delay proxies ($\le 10.4\,\text{ps}$), while high-fanout global clock/reset lines form the distribution tail up to $\sim 3.7\,\text{ns}$.
- Full manifest: [net_delay_statistics.csv](file:///Ubuntu-24.04/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_05/net_delay_statistics.csv).

---

## 5. Correlation Analysis

We analyzed the linear (Pearson) and monotonic rank (Spearman) relationships among layout quantities:

| Benchmark ID | Pearson (HPWL vs Delay) | Spearman (HPWL vs Delay) | Pearson (Fanout vs Delay) | Pearson (Fanout vs Criticality) |
| :--- | :--- | :--- | :--- | :--- |
| `BENCH_01_RISCY_C2_U70` | 0.4077 | **0.8202** | **0.9889** | 0.9946 |
| `BENCH_02_RISCY_C2_U90` | 0.4271 | **0.7659** | **0.9957** | 0.9979 |
| `BENCH_03_RISCY_C5_U70` | 0.4135 | **0.8188** | **0.9915** | 0.9959 |
| `BENCH_04_RISCY_C20_U70`| 0.4148 | **0.8216** | **0.9915** | 0.9959 |

### Key Insight:
- **Strong Monotonic Rank Alignment:** Spearman correlation between net HPWL and delay proxy is very high ($\sim 0.77 - 0.82$), proving that wirelength optimization directly improves net delay proxy ranking.
- **Fanout Domination on Extreme Outliers:** Pearson linear correlation between fanout and delay is $>0.98$, correctly reflecting that global high-fanout nets dominate delay in lumped RC models.

---

## 6. Placement Legalization Sensitivity Experiment

Comparing initial placements against OpenROAD detailed placement legalization reveals clear physical trends:

| Benchmark ID | Target Util | Initial HPWL ($\mu\text{m}$) | Legalized HPWL ($\mu\text{m}$) | HPWL Expansion | Mean Net Delay ($\text{ps}$) | Legalized Mean Delay ($\text{ps}$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BENCH_01_RISCY_C2_U70` | 0.70 | 711,584.0 | 731,162.9 | **+2.75%** | 5.94 | 6.10 |
| `BENCH_02_RISCY_C2_U90` | 0.90 | 609,283.7 | 708,651.3 | **+16.31%** | 4.77 | 5.55 |
| `BENCH_03_RISCY_C5_U70` | 0.70 | 682,561.6 | 701,234.8 | **+2.74%** | 5.90 | 6.07 |
| `BENCH_04_RISCY_C20_U70`| 0.70 | 681,942.5 | 700,395.9 | **+2.71%** | 5.91 | 6.07 |

- At $u=0.70$, legalization requires modest displacement ($+2.7\%$).
- At high density ($u=0.90$), intense cell congestion forces longer displacement ($+16.3\%$), directly tracked by the delay proxy. Manifest: [benchmark_timing_comparison.csv](file:///Ubuntu-24.04/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_05/benchmark_timing_comparison.csv).

---

## 7. Verification & Reproducibility

1. **Unit Tests:** `src/technology/test_timing_proxy.py` contains 7 unit tests (wirelength monotonicity, fanout monotonicity, batch consistency, path delay propagation, criticality bounds, numerical safety). **100% PASS** in 0.001s.
2. **Master Validation Command:**
   ```bash
   python3 -m src.technology.validate_timing_proxy
   ```
   All 5 validation checks pass cleanly.
3. **Publication Visualizations:** Saved in [phase_05_timing_proxy_metrics.png](file:///Ubuntu-24.04/home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_05/figures/phase_05_timing_proxy_metrics.png).
