# Model Audit: Existing Timing & RC Proxy Implementation

**Phase:** Phase 5 — Step 1  
**Target:** `src/technology/rc_proxy.py` and `src/technology/wirelength.py`  
**Date:** 2026-10-02  

---

## 1. Executive Summary & Terminology Correction

In Phase 3, an analytical interconnect RC and delay proxy was introduced in `src/technology/rc_proxy.py` with nominal values:
- $R_{\text{unit}} = 0.25\,\Omega / \mu\text{m}$
- $C_{\text{unit}} = 0.18\,\text{fF} / \mu\text{m}$ ($1.8 \times 10^{-16}\,\text{F} / \mu\text{m}$)
- $C_{\text{gate, default}} = 0.50\,\text{fF}$ ($5.0 \times 10^{-16}\,\text{F}$)
- $R_{\text{driver, default}} = 450.0\,\Omega$

### Crucial Terminology Correction:
As mandated by the scientific protocol:
> These parameters **MUST NOT** be described as "calibrated 28nm typical metal stack constants" or "foundry extracted values". No foundry technology file or SPEF rule deck was provided in CircuitNet N28.
>
> They are strictly **ANALYTICAL NORMALIZED RC PROXY PARAMETERS**, formulated as an idealized, monotonic surrogate to evaluate relative wirelength and fanout degradation in placement optimization.

---

## 2. Technical Audit of Current Implementation

### A. Inputs & Parameters
| Parameter | Default Value | Internal Units | Description / Role |
| :--- | :--- | :--- | :--- |
| `wirelength_um` | Dynamic | $\mu\text{m}$ (microns) | Manhattan Half-Perimeter Wirelength (HPWL) or wire length |
| `num_sinks` | Dynamic ($\ge 1$) | Integer | Number of downstream fanout sink pins driven by the net |
| `r_unit` | $0.25$ | $\Omega / \mu\text{m}$ | Normalized wire resistance per micron proxy |
| `c_unit` | $1.8 \times 10^{-16}$ | $\text{F} / \mu\text{m}$ | Normalized wire capacitance per micron proxy |
| `c_gate_default` | $5.0 \times 10^{-16}$ | $\text{F}$ | Proxy load capacitance per sink pin |
| `r_driver_default` | $450.0$ | $\Omega$ | Proxy output impedance of driving standard cell |

### B. Mathematical Equations
1. **Wire Parasitics:**
   $$R_{\text{wire}} = \max(0.0, L) \times r_{\text{unit}}$$
   $$C_{\text{wire}} = \max(0.0, L) \times c_{\text{unit}}$$

2. **Sink Load:**
   $$C_{\text{load}} = N_{\text{sinks}} \times C_{\text{gate, default}}$$

3. **Elmore Net Delay Proxy:**
   $$T_{\text{delay}} = R_{\text{driver}} (C_{\text{wire}} + C_{\text{load}}) + \frac{1}{2} R_{\text{wire}} C_{\text{wire}} + R_{\text{wire}} C_{\text{load}}$$
   Output scaled by $10^{12}$ to yield picoseconds ($\text{ps}$).

### C. Strengths & Limitations
- **Strengths:** Strictly monotonic with respect to both wirelength $L$ and fanout $N$; robust against negative/zero lengths; zero external library dependencies; vectorizable over tens of thousands of nets.
- **Limitations:** Does not incorporate non-linear cell input pin capacitance differences from `.lib`; does not distinguish metal layer stack variation (M1 vs M8); assumes a star/lumped-Pi topology rather than Steiner routing topology.
