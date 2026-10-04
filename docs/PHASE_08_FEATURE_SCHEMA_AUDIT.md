# Phase 8 Feature Schema Audit Report

**Document Version:** 1.0.0  
**Status:** COMPLETE & AUDITED  
**Date:** 2026-10-03  
**Project:** Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning  
**Reference Paper:** Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, *"Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning,"* IEEE TCAD, 2023.

---

## 1. Executive Summary

This audit establishes the authoritative feature schema for standard-cell nodes ($\mathcal{V}_{\text{cell}}$) and signal-net hyperedges ($\mathcal{V}_{\text{net}}$) in the CircuitNet N28 placement optimization framework. 

A specific audit inquiry was conducted regarding the dimensional consistency of cell features, specifically resolving potential ambiguity between 7-dimensional canonical formulations and informal references to 8 dimensions.

### Authoritative Conclusions:
1. **Canonical Cell Feature Dimension:** Strictly **7 dimensions** ($\mathbf{x}_u \in \mathbb{R}^7$).
2. **Canonical Net Feature Dimension:** Strictly **4 dimensions** ($\mathbf{z}_v \in \mathbb{R}^4$).
3. **Graph-Level Conditioning Features:** Strictly **10 features** ($\mathbf{g} \in \mathbb{R}^{10}$).
4. **Resolution of 8-Dimensional Reference:** Historical or informal planning references mentioning an 8th dimension represent a **documentation inconsistency**. In the canonical Phase 2 specification and in the underlying serialized dataset files (`dataset/graphs/*.npz`), exactly 7 features were implemented, validated, and frozen. No arbitrary eighth feature has been added, and the canonical 7-dimensional schema is locked for Phase 9 GraphSAGE ingestion.

---

## 2. Canonical Phase 2 Feature Schema (Dimension = 7)

Every cell instance node $u \in \mathcal{V}_{\text{cell}}$ ($N$ nodes per design, $2,373,702$ cells across all 54 designs) possesses a feature vector $\mathbf{x}_u \in \mathbb{R}^7$:

| Index | Feature Name | Source Domain | Mathematical Definition | Dtype | Units | Missing-Value Policy |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| **0** | `area` | `circuitnet.lef` | $w_u \times h_u$ | `float32` | $\mu\text{m}^2$ | Default to $0.882\,\mu\text{m}^2$ (1-pitch inverter) |
| **1** | `width` | `circuitnet.lef` | Bounding box width $w_u$ | `float32` | $\mu\text{m}$ | Default to $0.84\,\mu\text{m}$ (4 CoreSites) |
| **2** | `height` | `circuitnet.lef` | Bounding box height $h_u$ | `float32` | $\mu\text{m}$ | Default to $1.05\,\mu\text{m}$ (1 row) |
| **3** | `aspect_ratio` | Derived | $w_u / h_u$ | `float32` | unitless | Default to $0.80$ (with $h_u > 0$ defensive check) |
| **4** | `is_macro` | `node_attr` / LEF | $\mathbb{I}(c_u \in \{\text{SRAM, PLL, ROM}\} \lor \text{CLASS}=\text{BLOCK})$ | `float32` | binary $\{0.0, 1.0\}$ | Default to $0.0$ (Standard cell) |
| **5** | `cell_degree` | `pin_attr` | $\sum_{p \in \mathcal{P}} \mathbb{I}(\text{cell}(p) = u)$ | `float32` | pins | Default to $0.0$ |
| **6** | `log_degree` | Derived | $\log(1 + \text{deg}(u))$ | `float32` | $\log(\text{pins})$ | Default to $0.0$ |

---

## 3. Canonical Net Feature Schema (Dimension = 4)

In the lossless bipartite graph $\mathcal{G}_{\text{bipartite}}$, each signal net $v \in \mathcal{V}_{\text{net}}$ ($M$ nets per design, $2,469,557$ nets across all 54 designs) possesses a feature vector $\mathbf{z}_v \in \mathbb{R}^4$:

| Index | Feature Name | Source Domain | Mathematical Definition | Dtype | Units | Missing-Value Policy |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| **0** | `net_degree` | `pin_attr` | $\sum_{p \in \mathcal{P}} \mathbb{I}(\text{net}(p) = v)$ | `float32` | pins | Default to $0.0$ |
| **1** | `log_degree` | Derived | $\log(1 + \text{deg}(v))$ | `float32` | $\log(\text{pins})$ | Default to $0.0$ |
| **2** | `is_clock` | `net_attr` | $\mathbb{I}(\text{'clk'} \in \text{name}_v \lor \text{'clock'} \in \text{name}_v)$ | `float32` | binary $\{0.0, 1.0\}$ | Default to $0.0$ |
| **3** | `is_reset` | `net_attr` | $\mathbb{I}(\text{'rst'} \in \text{name}_v \lor \text{'reset'} \in \text{name}_v)$ | `float32` | binary $\{0.0, 1.0\}$ | Default to $0.0$ |

---

## 4. Documentation Discrepancy & Resolution

### Discrepancy Identification:
- Early planning roadmaps occasionally cited "8-dimensional standard cell feature vectors".
- Such references hypothetically envisioned including a one-hot gate functionality category (e.g. sequential vs combinational) or pin capacitance.
- However, CircuitNet N28 does not provide standard Liberty `.lib` files from which capacitance or timing arcs could be parsed without fabrication.
- Consequently, Phase 2 established a strictly verified 7-dimensional geometric-topological schema derived 100% from authentic LEF macros and unrolled netlist pins.

### Audit Decision & Resolution:
1. **No Schema Expansion:** The canonical `cell_features` matrix shape $[N, 7]$ across all 54 serialized files in `dataset/graphs/*.npz` is 100% intact and verified.
2. **Phase 9 Contract Alignment:** Phase 9 GraphSAGE will explicitly consume $d_{\text{in}} = 7$.
3. **Traceability:** Any future introduction of gate-type embeddings or auxiliary features must occur as an explicit, versioned transformation (e.g. Schema `3.0.0`), rather than an ad-hoc modification of canonical archives.
EOF
