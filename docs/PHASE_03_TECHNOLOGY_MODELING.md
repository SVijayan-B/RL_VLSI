# Phase 3: Technology Library Strategy & Wire-Load Modeling

**Document Version:** 1.0.0  
**Status:** COMPLETE (100% Passed)  
**Date:** 2026-09-29  

---

## 1. Executive Summary

Phase 3 establishes the physical, parasitics, and timing evaluation strategy for the CircuitNet N28 replication and adaptation of Agnesina et al. (IEEE TCAD 2023). 

Because the CircuitNet open dataset provides design layouts and graph topology without commercial, proprietary foundry libraries (e.g. TSMC 28nm `.lib`, `.sdc`, `.spef`), this phase establishes a **scientifically rigorous, fully transparent taxonomy of direct, derived, proxy, external, and unavailable quantities**. 

All implementations are deterministic, reproducible, and tested against canonical graph representations and OpenROAD toolchain components.

---

## 2. Technology Inventory & Artifact Audit

A comprehensive search of the repository confirms:
- **Total DEF files:** 500 placed/routed layout files across 54 unique designs.
- **LEF file:** `dataset/raw/circuitnet.lef` (Version 5.7, 2000 DBU/$\mu$m, 18 layers: CO, M1–M8, VIA1–VIA7, RV, AP; 915 standard cell macros).
- **Verilog Netlists:** 54 gate-level netlists (`.v`).
- **Foundry Files Absent (Proprietary to TSMC):** `.lib`, `.db`, `.sdc`, `.spef`, `.vcd`, `.saif`, `.captable`, `.itf`.

Inventories generated:
1. `dataset/metadata/tech_layer_inventory.csv`: 18 layers, routing directions, min widths, pitches.
2. `dataset/metadata/tech_cell_inventory.csv`: 915 standard cell macros with dimensions, areas, pin counts.
3. `dataset/metadata/tech_assumptions.json`: Explicit documentation of DBU conversion, manufacturing grid, and layer stack.
4. `dataset/metadata/tech_files_inventory.csv`: Complete census of all 555 design and tech files.

---

## 3. Toolchain Capabilities & Findings

### OpenROAD & OpenDB
- OpenROAD is executed via containerization:
  ```bash
  docker run --rm -v ~/CircuitNet_28nm:/workspace openroad/orfs:latest /OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad <script>
  ```
- **LEF/DEF Ingestion Finding:** `circuitnet.lef` defines macros and layers but does not define standard via geometries (e.g., `VIA12_1cut_H`, `VIA23_PBSB_V`). Consequently, standard `read_def` halts unless executed with `-continue_on_errors`. With `-continue_on_errors`, OpenROAD successfully parses all DEF components, terminals, and net topologies (tested on `441-RISCY-a-1-c5-u0.8-m3-p2-f1.def` with 49,942 instances and 53,259 nets).

### OpenSTA
- When executed on CircuitNet N28 netlists directly, OpenSTA produces `[ERROR STA-2141] No liberty libraries found`.
- When tested with open-source reference libraries (Nangate45 in `/OpenROAD-flow-scripts/flow/platforms/nangate45/lib/`), OpenSTA parses timing libraries and establishes full timer capability.
- **Conclusion:** Sign-off STA on CircuitNet designs cannot be performed natively without proprietary TSMC 28nm `.lib` files. All timing metrics on CircuitNet N28 must rely on defensible, relative geometric proxies.

---

## 4. Technology Capability Matrix

| Quantity Name | Category | Source / Method | Scientific Justification & Boundaries |
| :--- | :--- | :--- | :--- |
| `cell_width_height` | **DIRECT** | `circuitnet.lef` | Extracted directly from `MACRO SIZE` statements (2000 DBU/$\mu$m). |
| `cell_area` | **DIRECT** | `circuitnet.lef` | Computed as $W \times H$ directly from geometry. |
| `cell_pins_and_directions`| **DIRECT** | `circuitnet.lef` | Extracted directly from `PIN` and `DIRECTION` statements. |
| `layer_geometry_and_rules`| **DIRECT** | `circuitnet.lef` | Layers M1–M8, widths, and pitches parsed from LEF. |
| `placement_coordinates` | **DIRECT** | `def` and `.npy` | Exact $(x, y)$ coordinates in DBU. |
| `routing_tracks_die_area` | **DIRECT** | `circuitnet.def` | `DIEAREA` and `TRACKS` extracted from DEF. |
| `hpwl_wirelength` | **DERIVED** | Analytical / `src/technology/wirelength.py` | Half-Perimeter Wirelength computed deterministically from placed pin/cell locations. |
| `bounding_box_area` | **DERIVED** | Analytical / `src/technology/wirelength.py` | $\Delta X \times \Delta Y$ bounding box per net. |
| `net_degree_and_fanout` | **DERIVED** | Netlist / Graph | Exact number of sink pins driven per net. |
| `pin_pitch_and_density` | **DERIVED** | LEF / Placement | Pin spacing and pin congestion density. |
| `elmore_wire_delay_proxy` | **PROXY** | `src/technology/rc_proxy.py` | Geometric lumped RC tree wire delay proxy using nominal 28nm metal constants ($R_w=0.25\,\Omega/\mu\text{m}$, $C_w=0.18\,\text{fF}/\mu\text{m}$). |
| `wire_capacitance_proxy` | **PROXY** | `src/technology/rc_proxy.py` | Normalized wire capacitance proportional to Manhattan wirelength ($C_w \times L$). |
| `wire_resistance_proxy` | **PROXY** | `src/technology/rc_proxy.py` | Normalized wire resistance proportional to Manhattan wirelength ($R_w \times L$). |
| `timing_criticality_proxy`| **PROXY** | `src/technology/rc_proxy.py` | Relative ranking proxy based on topological fanout and high-wirelength nets. |
| `openroad_physical_db` | **EXTERNAL**| OpenROAD Docker | Layout parsing and geometric extraction via OpenDB with `-continue_on_errors`. |
| `opensta_auxiliary_engine`| **EXTERNAL**| OpenSTA Docker | Auxiliary timing smoke testing using Nangate45/ASAP7 open platforms. |
| `signoff_cell_delay` | **UNAVAILABLE**| Proprietary TSMC 28nm | Not present in CircuitNet open dataset. |
| `signoff_slack_wns_tns` | **UNAVAILABLE**| Proprietary TSMC 28nm | Requires proprietary TSMC 28nm `.lib` and `.sdc`. |
| `signoff_spef_parasitics` | **UNAVAILABLE**| Proprietary TSMC 28nm | Sign-off extracted parasitics not present in dataset. |
| `signoff_dynamic_power` | **UNAVAILABLE**| Proprietary TSMC 28nm | Requires switching activity (VCD/SAIF) and Liberty power tables. |

---

## 5. Implementation Architecture (`src/technology/`)

### 1. `src/technology/wirelength.py`
- `compute_net_hpwl(pin_coords, dbu_to_micron)`: Computes exact Manhattan bounding box perimeter half-length.
- `compute_net_bbox(pin_coords, dbu_to_micron)`: Returns $(\Delta X, \Delta Y, \text{Area})$.
- `compute_total_hpwl(net_pin_map, weights)`: Computes weighted or unweighted total design HPWL.
- `compute_hpwl_from_positions(positions, hyperedges)`: Direct vector calculation from canonical graph node positions and hyperedge connections.

### 2. `src/technology/rc_proxy.py`
- Implements `RCProxy28nm` with calibrated 28nm typical metal stack constants:
  - $R_{\text{unit}} = 0.25\,\Omega / \mu\text{m}$
  - $C_{\text{unit}} = 0.18\,\text{fF} / \mu\text{m}$
  - $C_{\text{gate, default}} = 0.50\,\text{fF}$
  - $R_{\text{driver, default}} = 450.0\,\Omega$
- `compute_elmore_wire_delay`: Computes distributed line + load Elmore delay:
  $$\tau_{\text{Elmore}} = R_{\text{driver}} (C_{\text{wire}} + N_{\text{sinks}} C_{\text{sink}}) + 0.5 R_{\text{wire}} C_{\text{wire}} + R_{\text{wire}} (N_{\text{sinks}} C_{\text{sink}})$$
- `compute_batch_delays`: Vectorized computation across tens of thousands of nets in sub-millisecond time.

### 3. Unit Testing & Validation
- Unit test suite: `src/technology/test_technology.py` (7 tests, 100% PASS in 0.001s).
- Full canonical validation: `src/technology/validate_technology.py` ran on `RISCY-FPU-a-1-c2_graph.npz` (75,067 cells, 76,569 nets):
  - Total HPWL: $33,810,876.25\,\mu\text{m}$
  - Mean Net HPWL: $441.57\,\mu\text{m}$
  - Mean Wire Delay Proxy: $42.16\,\text{ps}$
  - Max Wire Delay Proxy: $1384.13\,\text{ps}$
  - Summary saved to `results/phase_03/validation_summary.csv`.

---

## 6. Defensive Replication Statement

This replication study explicitly follows the scientific protocol of using **audited direct geometric values and defensible proxy models for relative reinforcement learning reward shaping**. We make no claims of reproducing TSMC commercial sign-off timing numbers, ensuring 100% academic integrity and legal compliance with proprietary foundry confidentiality.
