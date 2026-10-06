# Phase 11B — Placement-Derived HPWL Methodology

**Document Version:** 1.0.0  
**Status:** COMPLETE  
**Date:** 2026-10-04  

---

## 1. Methodology Objective
Investigate whether the 10,242 CircuitNet placement `.npy` files can be combined with graph/netlist connectivity to calculate a placement-derived Half-Perimeter Wirelength (HPWL).

---

## 2. Mathematical Definition of Center-Based HPWL Proxy
For each net $e \in \mathcal{E}$ connecting pins on a set of cell instances $\mathcal{V}_e$:
1. Each instance $v \in \mathcal{V}_e$ has quantized bounding box $[x_{1,v}, y_{1,v}, x_{2,v}, y_{2,v}]$ in the $256 \times 256$ GCell coordinate system.
2. The representative instance center is:
   $$c_{x,v} = \frac{x_{1,v} + x_{2,v}}{2}, \quad c_{y,v} = \frac{y_{1,v} + y_{2,v}}{2}$$
3. The bounding box of net $e$ in GCell units is:
   $$\text{HPWL}_{\text{proxy}}(e) = \left( \max_{v \in \mathcal{V}_e} c_{x,v} - \min_{v \in \mathcal{V}_e} c_{x,v} \right) + \left( \max_{v \in \mathcal{V}_e} c_{y,v} - \min_{v \in \mathcal{V}_e} c_{y,v} \right)$$
4. The total placement-derived HPWL proxy is:
   $$\text{HPWL}_{\text{proxy}} = \sum_{e \in \mathcal{E}} \text{HPWL}_{\text{proxy}}(e)$$

---

## 3. Critical Limitations & Non-Equivalence to OpenROAD HPWL
1. **Grid Quantization:** The coordinates are integers in $[0, 255]$. Standard cell instances placed in the same GCell share the identical center coordinate $(c_x, c_y)$.
2. **Missing Pin Offsets:** Standard cell internal pin offsets (available only in standard cell LEF macros) are omitted in the center-to-center proxy.
3. **Absence of Detailed Legalization:** A center-based GCell proxy cannot evaluate fine-grained detailed placement legalization effects (e.g., standard cell row snapping, site search window displacement, or one-site gap constraints).
4. **Authoritative Label:** This metric is strictly designated **PLACEMENT-DERIVED HPWL PROXY** and must never be represented as authoritative OpenROAD HPWL.
