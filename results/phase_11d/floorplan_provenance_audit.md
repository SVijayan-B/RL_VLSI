# Floorplan Provenance Audit: Phase 11C Forensic Analysis & Phase 11D Independent Derivation

## 1. Executive Summary & Forensic Audit Finding
A rigorous forensic audit was conducted on how Phase 11C derived the floorplan geometry (`die_w = 1167600 DBU`, `die_h = 1165800 DBU`, `num_rows = 498`, core area $\approx 583.8 \times 582.9\,\mu\text{m}$) for training design `RISCY-a-2-c2`.

### Audit Verdict on Phase 11C:
- **Source of Dimensions:** Direct inspection of `dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` (Line 6: `DIEAREA ( 0 0 ) ( 1167600 1165800 ) ;`).
- **Benchmark Relationship:** `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` is the official baseline DEF for **`BENCH_01`** (a held-out evaluation benchmark).
- **Finding:** The floorplan in Phase 11C was **MANUALLY HARDCODED and COPIED/REUSED from `BENCH_01`**.
- **Phase 11C Provenance Verdict:** **FAIL (BENCHMARK DEF LEAKAGE DETECTED)**.

---

## 2. Forensic Code Trace
In `results/phase_11c/` and the Phase 11C reconstruction scripts:
```python
# Phase 11C run_reconstruct_validated.py (Lines 44-46):
die_w = 1167600
die_h = 1165800
num_rows = 498
```
Cross-referencing `dataset/processed/DEF_decompressed/DEF/`:
- Exactly 500 reference DEFs exist in this directory.
- All 500 DEFs belong exclusively to held-out benchmarks `RISCY-a-1-c2`, `RISCY-a-1-c5`, and `RISCY-a-1-c20`.
- The exact dimension `1167600 × 1165800` belongs to `BENCH_01_RISCY_C2_U70`.

Reusing this geometry for training design `RISCY-a-2-c2` or any other training design violates the zero-leakage firewall and distorts placement physics for designs with different gate counts.

---

## 3. Phase 11D Remediation: Independent Mathematical Floorplan Derivation
To achieve complete scientific independence, the floorplan dimensions for all 49 active training designs must be calculated dynamically from the design's own topological and technological features.

### Derivation Protocol:
1. **Total Cell Area ($A_{\text{cells}}$):**
   Computed by querying `circuitnet.lef` via `LEFSiteModel` for each cell type present in the design's canonical bipartite graph:
   $$A_{\text{cells}} = \sum_{c \in \mathcal{V}_{\text{cells}}} W_{\text{LEF}}(c) \times H_{\text{LEF}}(c)$$
2. **Target Utilization ($U_{\text{target}}$):**
   Parsed directly from the representative CircuitNet placement sample filename (e.g. `...-u0.7-...` yields $U_{\text{target}} = 0.70$).
3. **Core Area ($A_{\text{core}}$):**
   $$A_{\text{core}} = \frac{A_{\text{cells}}}{U_{\text{target}}}$$
4. **Site & Row Grid Quantization (TSMC 28nm):**
   - Standard cell height: $H_{\text{row}} = 1.05\,\mu\text{m} = 2100\,\text{DBU}$
   - Standard cell site width: $W_{\text{site}} = 0.21\,\mu\text{m} = 420\,\text{DBU}$
   - Aspect ratio: Square target ($AR = 1.0$)
   - Number of rows: $N_{\text{rows}} = \text{round}\left( \frac{\sqrt{A_{\text{core}}}}{1.05} \right)$
   - Number of sites per row: $N_{\text{sites}} = \text{round}\left( \frac{\sqrt{A_{\text{core}}}}{0.21} \right)$
   - Die height: $H_{\text{die}} = N_{\text{rows}} \times 2100\,\text{DBU}$
   - Die width: $W_{\text{die}} = N_{\text{sites}} \times 420\,\text{DBU}$

---

## 4. Verification on Target Design `RISCY-a-2-c2`

| Parameter | Phase 11C (Hardcoded Benchmark Copy) | Phase 11D (Independent Mathematical Derivation) | Impact / Correction |
| :--- | :--- | :--- | :--- |
| **Derivation Method** | Hardcoded from `BENCH_01.def` | Analytical from canonical graph + LEF | **Purely Independent** |
| **Total Cell Area** | Unused in floorplan calculation | $225,987.74\,\mu\text{m}^2$ | **Design-Specific** |
| **Target Utilization** | Assumed | $70.0\%$ (from sample token `u0.7`) | **Sample-Consistent** |
| **Core Width** | $583.80\,\mu\text{m}$ ($1,167,600\,\text{DBU}$) | $568.26\,\mu\text{m}$ ($1,136,520\,\text{DBU}$) | **Tailored (-2.66%)** |
| **Core Height** | $582.90\,\mu\text{m}$ ($1,165,800\,\text{DBU}$) | $568.05\,\mu\text{m}$ ($1,136,100\,\text{DBU}$) | **Tailored (-2.55%)** |
| **Number of Rows** | 498 rows | 541 rows | **Exact pitch alignment** |
| **Number of Sites** | 2780 sites | 2706 sites | **Exact site alignment** |
| **Actual Utilization** | $66.41\%$ | $70.01\%$ | **Exact target match** |
| **Illegal Sites/Rows** | 0 | 0 | **Verified Legal** |
| **Overlaps** | 0 | 0 | **Verified Legal** |
| **Benchmark Leakage**| DETECTED (`BENCH_01` geometry copied) | **NONE (Zero benchmark access)** | **PASS** |

---

## 5. Audit Conclusion & Certification
- The Phase 11C floorplan derivation has been officially documented as failing zero-leakage standards due to hardcoded benchmark reuse.
- The Phase 11D independent derivation protocol has been fully implemented in `src/placement/coordinate_mapper.py` and validated on `RISCY-a-2-c2`.
- All 49 training designs will strictly use the independent mathematical floorplan derivation.
- **Phase 11D Floorplan Provenance Status:** **PASS**.
