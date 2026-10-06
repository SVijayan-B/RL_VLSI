# Phase 11B — Methodological Decision on Physical Training Starting State

**Document Version:** 1.0.0  
**Status:** COMPLETE  
**Date:** 2026-10-04  

---

## 1. Context and Objective
In Agnesina et al. (*IEEE TCAD 2023*), the reinforcement learning agent is trained to optimize EDA tool parameters for commercial placement engines (Cadence Innovus). A central methodological question is:

> How should the RL placement state be initialized for the 51 training designs in an OpenROAD-based flow, given that CircuitNet N28 provides pre-computed GCell placement feature maps but no uncompressed placed DEF layouts for the training partition?

---

## 2. Evaluation of Strategic Options

### OPTION A: Ingest CircuitNet Pre-Placed Samples as Fixed Starting States
- **Mechanism:** Take the 256x256 GCell instance bounding boxes from `dataset/placement/instance_placement/*.npy`, convert them to spatial features or map them to candidate coordinates, and treat them as the pre-placed state.
- **Scientific Pros:**
  - Ingests authentic layout data from the original CircuitNet physical design experiments.
  - Covers 52 of 54 designs across 10,242 parameter configurations.
- **Scientific Cons & Fatal Flaws:**
  - **Quantization:** Coordinates are quantized integer grid bins in $[0, 255]$ rather than legal standard cell sites.
  - **Loss of Legalization Action Semantics:** Detailed placement parameters (such as `max_displacement`, `site_search_window`, `row_search_window`, and `disallow_one_site_gaps`) operate on sub-micron standard cell rows and sites defined in the LEF. Feeding a 256x256 integer grid directly into OpenROAD DPL fails because instances are stacked on coarse bins without legalized site snapping.
  - **Deviation from RL Premise:** If placement is already fully completed and fixed, the RL policy cannot optimize global placement or iterative placement refinement; it degenerates into a post-hoc evaluation proxy.

---

### OPTION B: Construct OpenROAD-Compatible Physical Design Flow from Netlists
- **Mechanism:** Utilize the authentic gate-level Verilog netlists (`dataset/processed/netlists/netlist/*.v`), technology LEF (`circuitnet.lef`), and standard OpenROAD commands (`initialize_floorplan`, `global_placement`, `detailed_placement`) to execute independent, authentic physical placement runs.
- **Scientific Pros:**
  - **Fidelity to Agnesina et al.:** The paper specifically trains the RL agent by having the policy execute discrete macro-actions that modify the active placement tool's parameters during physical design execution.
  - **Authentic OpenROAD Metrics:** Produces exact, bit-level verifiable OpenDB/OpenROAD HPWL values directly from the physical layout engine.
  - **Decoupled from Held-Out Benchmarks:** Each training design has its own genuine die area, pin placements, and cell instances, eliminating physical template coupling to `BENCH_01`.
- **Scientific Challenges:**
  - Requires technology files for floorplanning (`initialize_floorplan` using site rows from `circuitnet.lef`).
  - Global placement requires either standard cell IO pin placements or basic synthetic floorplan constraints.

---

## 3. Methodological Decision and Verdict

**RECOMMENDATION: OPTION B (OpenROAD Native Physical Flow)** supplemented by Option A as an analytical baseline.

1. **Role of CircuitNet Placement:** The 10,242 placement `.npy` files serve as an **empirical reference and validation set** for congestion, macro floorplanning, and spatial feature baselines.
2. **Role of OpenROAD Placement:** OpenROAD is the **authoritative physical execution engine** for RL training episodes.
3. **RL Starting-State Definition:**
   $$\mathcal{S}_0 = [\mathbf{e}_{\text{GraphSAGE}} \, (32\text{-D}), \, \boldsymbol{\theta}_0 \, (6\text{-D}), \, \mathbf{m}_0 \, (2\text{-D}), \, p_0 \, (1\text{-D})]$$
   where initial HPWL is extracted from the design's own default OpenROAD placement run.
4. **Honest Limitations:** We do NOT have commercial Cadence Innovus or signoff `.lib`/`.sdc` files. We must explicitly report that our implementation is an **OpenROAD Detailed Placement adaptation** on TSMC 28nm standard cells.
