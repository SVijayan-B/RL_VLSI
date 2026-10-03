# Phase 7B Final Integrity Audit & Alignment Report

**Document Version:** 1.0.0  
**Status:** COMPLETE & FINALIZED  
**Date:** 2026-10-03  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  
**Reference Paper:** Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, *"Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning,"* IEEE TCAD, 2023.

---

## A. What Was Corrected
1. **Paper Parameter Metadata (Table I):**
   - Corrected cardinalities in `results/phase_07/paper_parameter_reference.csv`: `timing effort` has 2 values ({none, high}), and `clock power driven` has 3 values ({none, medium, high}).
   - Removed artificial universal default values from Table I metadata.
   - Segregated experiment-specific settings from Table VIII into `results/phase_07/paper_table_viii_reference.csv`.
2. **Paper Action Metadata (Table III):**
   - Restored exact conceptual names in `results/phase_07/paper_action_reference.csv`: Action 8 (`UP Global`), Action 9 (`DOWN Global`), and Action 10 (`INVERT-MIX`).
   - Replaced artificial renamings (`UP Constraints`, `DOWN Constraints`, `INVERT-MIX search windows`).
3. **OpenROAD Action Space Adaptation Semantics:**
   - Updated `src/placement/phase7_action_space.py` and `results/phase_07/action_validation.csv` to explicitly categorize actions as `VERIFIED` (1, 2, 3, 6, 7, 11), `PARTIALLY_VERIFIED` (4, 5), and `UNAVAILABLE` (8, 9, 10).
   - Prohibited fake mappings of unavailable global/timing actions onto detailed placement knobs.
4. **Sensitivity-Direction Classification Rules:**
   - Formalized numerical tolerance $\tau_{\text{HPWL}} = 0.001\%$ in `results/phase_07/parameter_sensitivity_final.csv`.
   - Applied consistent classification: $\Delta > +\tau \implies \text{DEGRADATION}$, $\Delta < -\tau \implies \text{IMPROVEMENT}$, $|\Delta| \le \tau \implies \text{NEUTRAL}$.
   - Decoupled `hpwl_effect_detected` and `runtime_effect_detected`.
5. **Pairwise Parameter Interaction Metrics:**
   - Mathematically formalized both HPWL interaction ($\Delta\text{HPWL}_{\text{obs}} - (\Delta_A + \Delta_B) = 0.0\,\mu\text{m}$, `hpwl_interaction_detected = FALSE`) and Runtime interaction ($\Delta\text{RT}_{\text{obs}} - (\Delta_A + \Delta_B)$) in `results/phase_07/parameter_interactions_final.csv`.
   - Report strictly no measurable HPWL interaction on `BENCH_01_RISCY_C2_U70`.
6. **Runtime Repeat Validation:**
   - Executed 18 repeat trials (6 configurations × 3 repeats) in `results/phase_07/runtime_repeat_validation.csv` and `results/phase_07/runtime_repeat_summary.csv`.
   - Confirmed 100% bit-exact HPWL reproducibility across all repeats and quantified runtime distributions.
7. **Regenerated Visualizations & Manifest:**
   - Generated 6 high-resolution publication figures in `results/phase_07/figures/`.
   - Updated `results/phase_07/run_manifest.json` and documentation in `docs/PHASE_07_PLACEMENT_PARAMETER_SPACE.md` and `docs/PROGRESS.md`.

---

## B. What Was Not Changed
1. **Underlying Measured Sweep Values:**
   - All 38 physical placement sweep runs regenerated in Phase 7A were preserved verbatim in `results/phase_07/parameter_sweep_final.csv` (and `.csv` / `_corrected.csv`).
2. **Phase 4 Baseline Controls:**
   - All baseline measurements across all 4 benchmarks (`BENCH_01`: $731,162.90\,\mu\text{m}$, `BENCH_02`: $708,651.30\,\mu\text{m}$, `BENCH_03`: $701,234.80\,\mu\text{m}$, `BENCH_04`: $700,395.90\,\mu\text{m}$) remain bit-exact controls.
3. **Scientific Boundaries:**
   - No Phase 8/9/10/11 code, GraphSAGE networks, or RL training loops were introduced.

---

## C. Paper Parameter Corrections (Table I vs Table VIII)
- **Table I Integrity:** Defines the complete CAD parameter search space ($|\mathcal{P}| \approx 2 \times 10^9$ candidate configurations).
- **Table VIII Distinction:** Table VIII details active learning evaluations from particular testcases (e.g. `eco max distance = 54`, `max density = 0.92`, `wire length opt = medium`). These values are now isolated in `paper_table_viii_reference.csv` to ensure they are never confused with tool defaults.

---

## D. Action-Space Corrections & OpenROAD Adaptation
- Actions 1, 2, 3, 6, 7, and 11 map directly to OpenROAD detailed placement controls (`-max_displacement`, `-disallow_one_site_gaps`, `-use_diamond_legalizer`, `-disable_window_extension`, and identity reset).
- Actions 4 and 5 represent heuristic search envelope expansions/contractions in DPL (`PARTIALLY_VERIFIED`).
- Actions 8 (`UP Global`), 9 (`DOWN Global`), and 10 (`INVERT-MIX`) represent global placement density and timing/congestion trade-offs in Cadence Innovus. In the absence of standard cell Liberty `.lib` files in CircuitNet N28, these actions cannot be executed in OpenROAD DPL and are honestly reported as `UNAVAILABLE`.

---

## E. OpenROAD Limitations
- OpenROAD detailed placement is an open-source legalization engine. It does not contain an integrated proprietary timing engine or activity-driven power placer that operates without foundry Liberty `.lib` tables.
- All timing and power estimations in this project are evaluated strictly post-placement using validated analytical proxy engines (Phase 5/Phase 6).

---

## F. Sensitivity Classification Rules
- Evaluated on `BENCH_01_RISCY_C2_U70` ($u=0.70$) using $\tau = 0.001\%$:
  - `max_displacement`: $\Delta = 0.0000\% \implies \text{NEUTRAL}$ (`hpwl_effect = FALSE`, `runtime_effect = TRUE`)
  - `site_search_window`: $\Delta = 0.0000\% \implies \text{NEUTRAL}$ (`hpwl_effect = FALSE`, `runtime_effect = TRUE`)
  - `row_search_window`: $\Delta = -0.0015\% \implies \text{IMPROVEMENT}$ (`hpwl_effect = TRUE`, `runtime_effect = TRUE`)
  - `disallow_one_site_gaps`: $\Delta = 0.0000\% \implies \text{NEUTRAL}$ (`hpwl_effect = FALSE`, `runtime_effect = TRUE`)
  - `use_diamond_legalizer`: $\Delta = -0.0083\% \implies \text{IMPROVEMENT}$ (`hpwl_effect = TRUE`, `runtime_effect = TRUE`)
  - `disable_window_extension`: $\Delta = -0.0018\% \implies \text{IMPROVEMENT}$ (`hpwl_effect = TRUE`, `runtime_effect = TRUE`)

---

## G. Runtime Repeat Validation Results
- Executed 3 repeated runs for 6 configurations (18 runs total):
  - `BENCH_01 baseline`: Median = $3.97\,\text{s}$, Mean = $4.20 \pm 0.64\,\text{s}$, HPWL = $731,162.90\,\mu\text{m}$ ($\sigma = 0.00$)
  - `BENCH_01 diamond`: Median = $2.45\,\text{s}$, Mean = $2.49 \pm 0.23\,\text{s}$, HPWL = $731,102.30\,\mu\text{m}$ ($\sigma = 0.00$)
  - `BENCH_02 baseline`: Median = $61.78\,\text{s}$, Mean = $61.08 \pm 2.14\,\text{s}$, HPWL = $708,651.30\,\mu\text{m}$ ($\sigma = 0.00$)
  - `BENCH_02 diamond`: Median = $2.63\,\text{s}$, Mean = $2.65 \pm 0.15\,\text{s}$, HPWL = $644,211.40\,\mu\text{m}$ ($\sigma = 0.00$)
  - `BENCH_02 site_search=60`: Median = $82.96\,\text{s}$, Mean = $83.08 \pm 0.35\,\text{s}$, HPWL = $724,420.80\,\mu\text{m}$ ($\sigma = 0.00$)
  - `BENCH_02 row_search=12`: Median = $59.27\,\text{s}$, Mean = $58.93 \pm 0.70\,\text{s}$, HPWL = $724,039.90\,\mu\text{m}$ ($\sigma = 0.00$)
- **Significance:** HPWL is 100% deterministic across all runs. The $\approx 23\times$ speedup of `use_diamond_legalizer` on high density ($u=0.90$) is statistically robust.

---

## H. HPWL Integrity Confirmation
- The original $151,825.80\,\mu\text{m}$ Phase 7 HPWL was caused by an incomplete DEF parsing implementation that omitted connection pairs on OpenROAD `write_def` net-header lines. It is **not** used as an authoritative experimental result.
- The authoritative `BENCH_01` baseline is:
  $$\mathbf{731,162.90\,\mu\text{m}}$$
  extracted directly from OpenROAD console legalized HPWL.
- The analytical extraction:
  $$\mathbf{731,824.32\,\mu\text{m}}$$
  is retained only as an independent cross-check ($0.09\%$ pin-offset delta).

---

## I. Final Validation Results
- `python3 -m src.placement.validate_phase7`: **20 / 20 Gates PASSED (100% OK)**
- `pytest -v src/placement/test_phase7_action_space.py`: **12 / 12 Unit Tests PASSED (100% PASS)**
- `pytest -v src/placement/test_phase7b_audit.py`: **8 / 8 Audit Tests PASSED (100% PASS)**

---

## J. Known Limitations
1. Commercial Innovus-specific global placement and clock power optimizations remain unavailable due to the absence of foundry `.lib` timing tables in CircuitNet N28.
2. The action space is an honest open-source adaptation, with Actions 8, 9, and 10 preserved conceptually but flagged as unavailable.

---

## K. Final Recommendation
Phase 7 implementation, baseline locks, action spaces, empirical sweeps, interaction models, and documentation are verified and frozen. Phase 8 is ready to commence upon user authorization.
