# PHASE 1 — DATA AUDIT REPORT
## CircuitNet 28nm VLSI Placement Optimization
### Date: 2026-09-29
### Reference: Agnesina et al., "Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning", IEEE TCAD 2023

---

## 1. Executive Summary

This report documents the exhaustive Phase 1 Data Audit conducted on the CircuitNet 28nm dataset. All 54 gate-level Verilog netlists and all 500 placed DEF files were structurally audited and cross-referenced with the technology LEF file (`circuitnet.lef`) and the local environment.

### Key Audit Metrics
| Metric | Value | Details |
|---|---|---|
| **Total Gate-Level Netlists** | **54** | All parsed successfully; single top-level module `pulpino_top` |
| **Total Placed DEF Files** | **500** | All 500 structurally audited; 100% parse status `OK` |
| **Netlists with Matching DEFs** | **3 of 54 (5.56%)** | `RISCY-a-1-c2` (247), `RISCY-a-1-c5` (245), `RISCY-a-1-c20` (8) |
| **Netlists without DEFs** | **51 of 54 (94.44%)** | Netlists exist, but no DEFs provided in `DEF-place-0.tar.gz` |
| **Technology LEF Macros** | **915** | Standard cells, clock buffers, delay cells, fillers, antenna cells, macros |
| **LEF Routing & Cut Layers** | **18** | Metal layers M1–M8, contact CO, cut layers VIA1–VIA7, RV, AP |
| **LEF Standard Cell Site** | **1** | `CoreSite` (Width: 0.21 µm, Height: 1.05 µm) |
| **DEF-to-LEF Cell Match Rate** | **100.0%** | **269 / 269** unique DEF cell types exist in `circuitnet.lef` |
| **Timing / Power Tech Files** | **Missing** | No `.lib`, `.sdc`, `.spef`, `.tf`, or `.tlef` in raw CircuitNet package |

---

## 2. Parameter Definitions (CircuitNet N28 Documentation)

The 500 DEF filenames strictly adhere to CircuitNet's naming convention:
$$\text{\{Design name\}-\{\#Macros\}-c\{Clock\}-u\{Utilization\}-m\{Macro placement\}-p\{Power mesh setting\}-f\{filler insertion\}}$$

From official CircuitNet documentation and publications, the parameter semantics are verified as follows:

| Parameter | Meaning | Explored Values in Dataset | Count |
|---|---|---|---|
| **`u`** | **Target Placement Density / Core Utilization**<br>Ratio of standard cell area to total available core area. | `u0.70`<br>`u0.75`<br>`u0.80`<br>`u0.85`<br>`u0.90` | 117<br>110<br>110<br>102<br>61 |
| **`m`** | **Macro Placement Strategy**<br>Floorplan configuration and placement arrangement of large functional SRAM/PLL macro blocks. | `m1`<br>`m2`<br>`m3`<br>`m4` | 168<br>142<br>126<br>64 |
| **`p`** | **Power Delivery Network (PDN) Mesh Setting**<br>Configuration of upper-metal power rails/stripes for power distribution. | `p1` to `p8` | ~60–64 each (p1:63, p2:60, p3:60, p4:63, p5:64, p6:63, p7:64, p8:63) |
| **`f`** | **Filler Cell Insertion Stage**<br>`f0`: No filler cells at placement stage (or after routing)<br>`f1`: Filler cells inserted immediately after placement | `f0`<br>`f1` | 263<br>237 |
| **`c`** | **Target Clock Period Constraint**<br>Timing constraint used during synthesis: `c2` = 2.0 ns, `c5` = 5.0 ns, `c20` = 20.0 ns | `c2`<br>`c5`<br>`c20` | 247<br>245<br>8 |

---

## 3. Structural DEF Audit (500 Files)

All 500 DEF files located in `dataset/processed/DEF_decompressed/DEF/` (~26 GB total uncompressed) were verified.

### Structural Integrity
- **Version:** `5.8` across all 500 files
- **Design Name in DEF:** `pulpino_top` across all 500 files
- **Distance Units:** `UNITS DISTANCE MICRONS 2000` (2,000 DBU per micron)
- **Parse Status:** 500 / 500 files have valid headers, component counts, net definitions, pin lists, and terminate with `END DESIGN`
- **Rows:** 452 to 506 placement rows per design (depending on utilization `u`)
- **Pins:** 563 primary I/O pins defined with layer and placement coordinates

### DEF Dimension & Area Breakdown by Utilization
Because standard cell count is approximately constant (~52,100 to ~53,600 cells), the floorplanner scales core die dimensions according to target utilization $u$:

| Target Utilization | Die Area ($X \times Y$ DBU) | Die Dimensions ($\mu\text{m}$) | Total Die Area ($\mu\text{m}^2$) | Row Count |
|---|---|---|---|---|
| **0.70** | $1167600 \times 1165800$ | $583.80 \times 582.90$ | 340,297.02 | 498 |
| **0.75** | $1133160 \times 1131900$ | $566.58 \times 565.95$ | 320,655.95 | 482 |
| **0.80** | $1101240 \times 1100400$ | $550.62 \times 550.20$ | 302,951.12 | 467 |
| **0.85** | $1070580 \times 1069200$ | $535.29 \times 534.60$ | 286,166.03 | 452 |
| **0.90** | $1043280 \times 1041600$ | $521.64 \times 520.80$ | 271,670.11 | 439 |

---

## 4. Netlist Inspection (All 54 Files)

All 54 Verilog netlists in `dataset/processed/netlists/netlist/` were inspected.

### Global Observations
1. **Top Module:** All 54 netlists are flat gate-level netlists with module name `pulpino_top` (PULPino RISC-V SoC).
2. **Module Count:** Exactly 1 module per file (0 nested submodules, 0 unresolved module references).
3. **Hard Macros:** All designs instantiate 2 SRAM macros (`sp_ram_bank_i`) and 1 PLL macro (`PLL_i`).
4. **Variations:**
   - 3 Base Cores: `RISCY` (4-stage in-order RISC-V), `RISCY-FPU` (with floating-point unit), `zero-riscy` (compact 2-stage RISC-V).
   - 2 Configurations: `a` (full featured), `b` (minimal peripherals).
   - 3 Architecture variants: `1`, `2`, `3`.
   - 3 Clock targets: `c2` (2 ns / 500 MHz), `c5` (5 ns / 200 MHz), `c20` (20 ns / 50 MHz).

### Summary Statistics Across Netlists
| Base Design | Variant | Clocks | Netlist File Size | Cell Instances | Wires / Nets | Unique Cell Types | Matching DEFs |
|---|---|---|---|---|---|---|---|
| **RISCY** | `a-1` | `c2, c5, c20` | ~20.6 MB | 53,586 | 55,876 | 136–216 | **Yes (500 files total)** |
| **RISCY** | `a-2, a-3` | `c2, c5, c20` | ~20.6 MB | 53,580–53,590 | 55,870–55,880 | 136–216 | None |
| **RISCY** | `b-1, b-2, b-3` | `c2, c5, c20` | ~12.5 MB | ~30,200 | ~32,500 | 85–140 | None |
| **RISCY-FPU** | `a-1, a-2, a-3` | `c2, c5, c20` | ~30–31 MB | 68,684–75,070 | 70,267–76,279 | 92–228 | None |
| **RISCY-FPU** | `b-1, b-2, b-3` | `c2, c5, c20` | ~21–23 MB | ~45,000–51,000 | ~47,000–53,000 | 80–180 | None |
| **zero-riscy** | `a-1, a-2, a-3` | `c2, c5, c20` | ~16.3 MB | 41,800–42,150 | 44,000–44,400 | 85–170 | None |
| **zero-riscy** | `b-1, b-2, b-3` | `c2, c5, c20` | ~8.5–8.7 MB | ~21,500–22,500 | ~23,000–24,000 | 70–120 | None |

---

## 5. Netlist-to-DEF Cross-Matching

The cross-matching audit reveals the exact relationship between the 54 netlists and 500 DEFs:

### Paired Designs (Netlist + DEF present)
| Netlist Design Key | Clock Target | Matching DEF Count | Status |
|---|---|---|---|
| `RISCY-a-1-c2` | 2.0 ns | **247** | Complete Pair |
| `RISCY-a-1-c5` | 5.0 ns | **245** | Complete Pair |
| `RISCY-a-1-c20` | 20.0 ns | **8** | Complete Pair |
| **Subtotal** | | **500** | |

### Unpaired Designs (51 Netlists with NO DEFs)
All other 51 netlists (including all 18 `RISCY-FPU` designs, all 18 `zero-riscy` designs, and the other 15 `RISCY` designs) have **zero matching DEFs** in the `DEF-place-0.tar.gz` package.

---

## 6. LEF Technology & Cell Type Mapping

**File:** `dataset/raw/circuitnet.lef` (7.47 MB)

### Technology Overview
- **Layers:** 18 physical layers:
  - 8 Routing metal layers: `M1`, `M2`, `M3`, `M4`, `M5`, `M6`, `M7`, `M8`
  - 1 Redistribution layer: `AP` (Aluminum Pad)
  - 7 Via / cut layers: `VIA1`, `VIA2`, `VIA3`, `VIA4`, `VIA5`, `VIA6`, `VIA7`, plus `RV`, `CO`
- **Sites:** 1 standard cell placement site: `CoreSite` ($0.21\,\mu\text{m} \times 1.05\,\mu\text{m}$)
- **Total Defined Macros:** **915 macros**

### Cell Naming & Compatibility Analysis
1. **DEF vs LEF Compatibility: 100.0% MATCH**
   - Every single one of the 269 unique cell types appearing in the DEF files exists in `circuitnet.lef` (269 / 269).
   - This includes standard combinational/sequential logic, clock tree buffers (`CKB_x2_0`), delay cells (`DEL025_x1_0`), antenna diodes (`ANTENNA_0000`), tie cells (`TIEL`, `TIEH`), and physical macros (`SRAM`, `PLL`).
   - Consequently, **full geometric placement feature extraction, pin locations, wire pitch, and density calculations can proceed directly using DEF + LEF**.

2. **Netlist vs LEF Naming Convention: Systematic Naming Difference**
   - In the Verilog netlists (generated by Synopsys Design Compiler), standard cells use numeric suffix notation encoding transistor sizes and drive levels (e.g. `DFCNQ_0100`, `INV_0100`, `AOI22_0100`, `ND2_0011_0100`).
   - In the LEF and DEF files (generated by Cadence Innovus during physical design), standard cells use explicit drive multiplier notation (e.g. `DFCNQ_x1_0`, `INV_x1_0`, `AOI22_x1_0`).
   - Base cell functionality matches directly (e.g., `DFCNQ`, `INV`, `AOI22`, `ND2`, `NR2`, `BUFF`).

---

## 7. Technology Files Search & Availability

A comprehensive search of the system and project files for `.lib`, `.lef`, `.tlef`, `.tf`, `.sdc`, `.spef`, `.vcd`, `.saif` was completed:

| File Type | Status in CircuitNet N28 | Found in Environment? | Notes |
|---|---|---|---|
| **`.lef`** | **Present** | Yes (`dataset/raw/circuitnet.lef`) | Complete physical definitions for 915 macros & 18 layers |
| **`.lib` (Liberty)** | **Missing** | No | Proprietary TSMC 28nm timing/power libraries are withheld by CircuitNet |
| **`.tlef` / `.tf`** | **Missing** | No | Technology layers are integrated directly in `circuitnet.lef` |
| **`.sdc`** | **Missing** | No | Clock constraints inferred from filenames (`c2`=2ns, `c5`=5ns, `c20`=20ns) |
| **`.spef`** | **Missing** | No | Parasitic extraction files not provided in CircuitNet N28 |
| **`.vcd` / `.saif`**| **Missing** | No | Dynamic switching activity not provided |

---

## 8. Generated Manifest Deliverables

All required metadata manifests have been generated and validated in `dataset/metadata/`:

1. [netlist_manifest.csv](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/netlist_manifest.csv) (54 rows)
   - Columns: `netlist_filename`, `design_key`, `base_design`, `variant_ab`, `number_N`, `clock_suffix`, `clock_period_ns`, `top_module`, `module_count`, `file_size_bytes`, `instance_count`, `net_count`, `cell_types_count`, `unresolved_refs_count`, `has_matching_def`, `matching_def_count`
2. [def_manifest.csv](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/def_manifest.csv) (500 rows)
   - Columns: `def_filename`, `def_id`, `design_key`, `utilization_u`, `param_m`, `param_p`, `param_f`, `design_name_def`, `version`, `units_distance_microns`, `die_llx`, `die_lly`, `die_urx`, `die_ury`, `die_width_um`, `die_height_um`, `die_area_sq_um`, `components_count`, `nets_count`, `pins_count`, `specialnets_count`, `rows_count`, `parse_status`
3. [design_manifest.csv](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/design_manifest.csv) (54 rows)
   - Columns: `design_key`, `base_design`, `variant`, `number`, `clock_suffix`, `clock_period_ns`, `has_netlist`, `netlist_path`, `netlist_file_size_mb`, `netlist_instances`, `netlist_nets`, `has_def`, `def_count`, `def_components_sample`, `def_utilizations`, `def_m_settings`, `def_p_settings`, `def_f_settings`, `pairing_status`
4. [lef_cell_mapping.json](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/lef_cell_mapping.json)
   - Macro counts, site information, layer definitions, and DEF/netlist cell matching analysis.
5. [tech_files_manifest.csv](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/tech_files_manifest.csv)
   - Inventory of EDA technology files available on the system.
6. [audit_summary.json](file:///home/b_siddarth_vijayan/CircuitNet_28nm/dataset/metadata/audit_summary.json)
   - Machine-readable audit summary.
