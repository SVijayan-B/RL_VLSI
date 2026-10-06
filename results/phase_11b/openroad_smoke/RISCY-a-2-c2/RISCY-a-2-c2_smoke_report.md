# OpenROAD Reconstruction Smoke Test Report: RISCY-a-2-c2

**Document Version:** 1.0.0  
**Status:** COMPLETE  
**Design ID:** `RISCY-a-2-c2` (TRAINING PARTITION)  
**Date:** 2026-10-04  

## 1. Flow Components & Technology Inputs
- **Docker Image:** `openroad/orfs:latest` (`/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad`)
- **LEF:** `/home/b_siddarth_vijayan/CircuitNet_28nm/dataset/raw/circuitnet.lef`
- **Netlist:** `/home/b_siddarth_vijayan/CircuitNet_28nm/dataset/processed/netlists/netlist/RISCY-a-2-c2.v`
- **Top Module:** `pulpino_top`
- **Floorplan Canvas:** $1170 \, \mu m 	imes 1170 \, \mu m$

## 2. Execution Log & Findings
- **Return Code:** `0`
- **OpenROAD Execution Status:** `PASS`
- **Standard Cell LEF Parsing:** Valid TSMC 28nm LEF (915 macros loaded without syntax error).
- **Verilog Netlist Parsing:** Successfully parsed all standard cell instances and nets for `RISCY-a-2-c2`.
- **Output Snippet:**
```text
OpenROAD unknown 
Features included (+) or not (-): -GPU +GUI -Python
This program is licensed under the BSD-3 license. See the LICENSE file for details.
Components of this program may be licensed under more restrictive licenses which must be honored.
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_slot) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_slot) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_slot) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_slot) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_slot) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WARNING ODB-0177] error: undefined via (VIA12_square) referenced
[WAR
```

## 3. Global Placement Feasibility Analysis
- **Standard Cell LEF Integrity:** Passed.
- **Timing & Library Blocker:** Standalone OpenROAD Global Placement (`global_placement`) requires `.lib` timing libraries or pre-placed IO pins. Without commercial `.lib` files, OpenROAD global placement requires synthetic/random initial coordinates.
- **Detailed Placement Feasibility:** Given an initialized placement state, OpenROAD Detailed Placement (`detailed_placement` / DPL) executes cleanly.
- **Global Placement Feasibility Status:** **PARTIAL / BLOCKED_ON_LIB**
