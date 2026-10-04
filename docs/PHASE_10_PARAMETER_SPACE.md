# Phase 10: OpenROAD Placement Parameter Space

**Document Version:** 1.0.0  
**Status:** COMPLETE (100% Verified)  
**Date:** 2026-10-04  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  

---

## 1. Overview
The Agnesina et al. (*IEEE TCAD 2023*) reference framework conceptualizes a placement parameter optimization problem across commercial EDA tools (Cadence Innovus). To maintain complete experimental authenticity on open-source **OpenROAD**, our RL environment controls **strictly the six placement parameters** that are experimentally verified in the OpenROAD detailed placer (`DPL`).

---

## 2. Authorized Parameter Inventory

| Index | Parameter Name | Data Type | Units | Bounds [Min, Max] | Default | Step | OpenROAD Flag | Verification |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| 0 | `max_displacement` | Integer | sites | $[0, 100]$ | 0 | 10 | `-max_displacement` | **VERIFIED** |
| 1 | `site_search_window` | Integer | sites | $[0, 100]$ | 0 | 10 | `-site_search_window` | **VERIFIED** |
| 2 | `row_search_window` | Integer | rows | $[0, 20]$ | 0 | 2 | `-row_search_window` | **VERIFIED** |
| 3 | `disallow_one_site_gaps` | Boolean | binary | $\{0, 1\}$ | 0 | 1 | `-disallow_one_site_gaps`| **VERIFIED** |
| 4 | `use_diamond_legalizer` | Boolean | binary | $\{0, 1\}$ | 0 | 1 | `-use_diamond_legalizer` | **VERIFIED** |
| 5 | `disable_window_extension` | Boolean | binary | $\{0, 1\}$ | 0 | 1 | `-disable_window_extension` | **VERIFIED** |

---

## 3. Parameter Normalization Protocol

Normalization maps all parameter values into the continuous interval $[0.0, 1.0]$ for input into the RL actor-critic networks:
- **Integer Parameters**:
  $$p_{\text{norm}} = \frac{p - p_{\min}}{p_{\max} - p_{\min}}$$
- **Boolean Parameters**:
  $$p_{\text{norm}} = \begin{cases} 0.0 & \text{if False} \\ 1.0 & \text{if True} \end{cases}$$

Normalization relies exclusively on the **declared parameter bounds**, never on transient observed values. Values outside $[p_{\min}, p_{\max}]$ are strictly rejected.

---

## 4. Unsupported Paper Parameters & Exclusion Rationale

To maintain scientific integrity, parameters from Agnesina et al. that require proprietary technologies or non-existent OpenROAD flags are categorized as `UNAVAILABLE` and excluded from entering the action space:
1. `global_wirelength_weight`: Requires timing-driven global placement forces with `.lib` models.
2. `timing_driven_effort`: Requires proprietary sign-off timing Liberty libraries.
3. `congestion_effort`: Innovus-specific routing congestion engine controls.
4. `pin_access_opt`: Commercial foundry DRC pin access density heuristics.
5. `clock_tree_synthesis_effort`: Belongs to the CTS stage, outside placement.
6. `power_driven_effort`: Requires dynamic power sign-off analysis engines.
