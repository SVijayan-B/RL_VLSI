# Phase 10A: Final Integrity Cleanup & A2C Training Protocol Lock

**Document Version:** 1.0.0  
**Status:** COMPLETE (Locked & Verified)  
**Date:** 2026-10-04  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  
**Reference:** Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, *IEEE TCAD 2023*  
**Dataset:** CircuitNet N28 (`circuitnet.lef` + DEF/Verilog)  
**Placement Engine:** OpenROAD Detailed Placement (`DPL`)  

---

## 1. Authoritative HPWL Terminology Lock

To prevent conflation between layout stages, all metrics in Phase 10, Phase 10A, and subsequent phases strictly adhere to the following definitions:

1. **`INITIAL_HPWL`**:
   - The Half-Perimeter Wire Length measured directly from the decompressed source CircuitNet DEF before running OpenROAD detailed placement legalization.
2. **`DEFAULT_DPL_BASELINE_HPWL`**:
   - The Half-Perimeter Wire Length measured after running default OpenROAD detailed placement legalization (`-max_displacement 0`, default flags).
3. **`RL_START_HPWL`**:
   - The starting HPWL at step 0 of an RL episode. For all baseline experiments, `RL_START_HPWL` is locked to `DEFAULT_DPL_BASELINE_HPWL`.

### Four Authoritative Benchmarks Audit
| Benchmark ID | Design Key | Split | Source DEF | Initial HPWL ($\mu\text{m}$) | Default DPL Baseline HPWL ($\mu\text{m}$) | Status |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: |
| `BENCH_01_RISCY_C2_U70` | `RISCY-a-1-c2` | `HELD_OUT_TEST` | `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` | **730,968.99** | **731,162.90** | **LOCKED** |
| `BENCH_02_RISCY_C2_U90` | `RISCY-a-1-c2` | `HELD_OUT_TEST` | `120-RISCY-a-1-c2-u0.9-m1-p1-f0.def` | **585,708.96** | **708,651.30** | **LOCKED** |
| `BENCH_03_RISCY_C5_U70` | `RISCY-a-1-c5` | `HELD_OUT_TEST` | `248-RISCY-a-1-c5-u0.7-m1-p1-f0.def` | **699,223.74** | **701,234.80** | **LOCKED** |
| `BENCH_04_RISCY_C20_U70`| `RISCY-a-1-c20`| `HELD_OUT_TEST` | `493-RISCY-a-1-c20-u0.7-m1-p1-f0.def` | **699,355.68** | **700,395.90** | **LOCKED** |

---

## 2. Six Authorized Placement Parameters

The active parameter space is locked to the 6 verified OpenROAD detailed placer parameters defined in `configs/phase10_parameter_space.json`:
1. `max_displacement` (Integer, $[0, 100]$ sites, default: 0, step: 10)
2. `site_search_window` (Integer, $[0, 100]$ sites, default: 0, step: 10)
3. `row_search_window` (Integer, $[0, 20]$ rows, default: 0, step: 2)
4. `disallow_one_site_gaps` (Boolean, $\{0, 1\}$, default: False)
5. `use_diamond_legalizer` (Boolean, $\{0, 1\}$, default: False)
6. `disable_window_extension` (Boolean, $\{0, 1\}$, default: False)

Parameters from the paper requiring commercial signoff `.lib` files or proprietary Innovus commands are categorized `UNAVAILABLE` and prohibited from entering the action space.

---

## 3. Paper Action Space Adaptation

The 11 conceptual actions from Agnesina et al. Table III are mapped to 8 executable OpenROAD macro-actions:
- **Verified Actions (8 active)**:
  - 0: `FLIP_BOOLEANS` (Inverts all 3 boolean flags)
  - 1: `UP_INTEGERS` (Increments integer parameters by 1 step)
  - 2: `DOWN_INTEGERS` (Decrements integer parameters by 1 step)
  - 3: `UP_EFFORTS` (Expands row and site search window)
  - 4: `DOWN_EFFORTS` (Contracts row and site search window)
  - 5: `UP_DETAILED` (Expands displacement and site window)
  - 6: `DOWN_DETAILED` (Reduces displacement and site window)
  - 7: `DO_NOTHING` (No-op; preserves parameter state)
- **Unavailable Paper Actions (Guarded & Rejected)**:
  - `UP Global` (`UNAVAILABLE`)
  - `DOWN Global` (`UNAVAILABLE`)
  - `INVERT-MIX` (`UNAVAILABLE`)

---

## 4. 41-Dimensional RL State Space

The observation vector $s_t \in \mathbb{R}^{41}$ is constructed programmatically:
$$\mathbf{s}_t = [\,\mathbf{h}_G\,(32) \;\parallel\; \mathbf{p}_{\text{norm}}\,(6) \;\parallel\; \mathbf{m}\,(2) \;\parallel\; \text{prog}\,(1)\,]^\top$$
- **Graph Embedding ($\mathbf{h}_G$)**: 32-D frozen global embedding from Phase 9 GraphSAGE.
- **Normalized Parameters ($\mathbf{p}_{\text{norm}}$)**: 6 continuous dimensions normalized via declared bounds.
- **Placement Metrics ($\mathbf{m}$)**: Normalized HPWL ($\text{HPWL}_t / \text{HPWL}_{\text{base}}$) and relative step change.
- **Episode Progress ($\text{prog}$)**: $t / T_{\max}$.

---

## 5. Frozen Representation & Test-Design Quarantine

- **GraphSAGE Model**: Checkpoint `results/phase_09/checkpoints/graphsage_best.pt` is strictly frozen. No gradient update during RL modifies GraphSAGE weights.
- **Data Partition Isolation**:
  - **Training Partition**: 51 designs.
  - **Held-Out Test Partition**: 3 designs (`RISCY-a-1-c2`, `RISCY-a-1-c5`, `RISCY-a-1-c20`) hosting `BENCH_01` through `BENCH_04`.
  - **Quarantine Rule**: No actor-critic policy or value gradient updates will ever touch held-out test benchmarks.

---

## 6. Relative HPWL Reward Formula

The step reward is mathematically explicit:
$$r_t = \frac{\text{HPWL}_{t-1} - \text{HPWL}_t}{\max(|\text{HPWL}_{t-1}|, \epsilon)}$$
- Wirelength reduction yields $r_t > 0$.
- Wirelength expansion yields $r_t < 0$.
- OpenROAD execution failures or unroutable placements receive $r_t = -1.0$ with execution status `FAILED`.

---

## 7. Multi-Seed Training Protocol for Phase 11

Stored centrally in `configs/phase11_a2c_training_protocol.json`:
- **Training Seed Set**: $\{42, 43, 44, 45, 46\}$ (minimum 5 distinct seeds).
- **Seed Directory Isolation**: `results/phase_11/seed_{seed}/`.
- **Episodes per Seed**: 100 episodes.
- **Max Steps per Episode**: 10 steps.
- **Learning Rate**: $0.0007$ (Adam).
- **Discount Factor ($\gamma$)**: $0.99$.
- **Entropy Coefficient**: $0.01$.
- **Value Loss Coefficient**: $0.5$.
- **Gradient Clipping**: $0.5$.
- **Output Artifacts per Seed**: `transitions.csv`, `episode_metrics.csv`, `checkpoint_metadata.json`.

---

## 8. Protocol Smoke Test Certification

A 2-episode protocol smoke test under seed 42 verified end-to-end execution:
- Output directories created at `results/phase_11/seed_42/`.
- Both `transitions.csv` and `episode_metrics.csv` generated adhering strictly to the schema.
- Checkpoint metadata logged with SHA-256 configuration provenance.
- All losses and gradients finite without NaN/Inf.
