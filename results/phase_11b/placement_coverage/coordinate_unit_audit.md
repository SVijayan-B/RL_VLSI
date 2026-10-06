# Phase 11B — Coordinate and Spatial Unit Audit

**Document Version:** 1.0.0  
**Status:** COMPLETE  
**Date:** 2026-10-04  

---

## 1. Executive Summary
A critical question in VLSI machine learning datasets is whether spatial coordinates stored in numerical arrays represent physical layout dimensions in microns ($\mu m$), integer database units (DBU), or a quantized global routing / grid cell (GCell) feature map.

This audit definitively establishes the coordinate system across all 10,242 `.npy` files in `dataset/placement/instance_placement/`.

---

## 2. Empirical Findings

### Direct Comparison: Placed DEF vs Placement `.npy`
We compared sample DEF `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` with its exact corresponding placement file `1-RISCY-a-1-c2-u0.7-m1-p1-f0.npy`:

| Attribute | Placed DEF File (`.def`) | Placement Object (`.npy`) |
| :--- | :--- | :--- |
| **Units Distance Micron** | `UNITS DISTANCE MICRONS 2000` | N/A (dimensionless integer grid) |
| **Die Area Range** | `( 0 0 ) ( 1167600 1165800 )` | N/A (implicit $[0, 255] \times [0, 255]$) |
| **Die Area ($\mu m$)** | $583.80 \, \mu m \times 582.90 \, \mu m$ | Normalized $256 \times 256$ spatial map |
| **PLL Coordinate** | `FIXED ( 60060 738480 )` | `[13, 164, 94, 245]` |
| **PLL X Ratio** | $60060 / 1167600 = 0.0514388$ | $13 / 256 = 0.0507812$ |
| **PLL Y Ratio** | $738480 / 1165800 = 0.6334534$ | $164 / 256 = 0.6406250$ |
| **SRAM 1 Coordinate** | `FIXED ( 60060 60000 )` | `[13, 13, 121, 76]` |
| **DEL025 Standard Cell**| `PLACED ( 378840 681600 )` | `[84, 151, 84, 151]` |
| **DEL025 X Ratio** | $378840 / 1167600 = 0.324460$ | $84 / 256 = 0.328125$ |
| **DEL025 Y Ratio** | $681600 / 1165800 = 0.584663$ | $151 / 256 = 0.589844$ |

### Dataset-Wide Coordinate Distribution
Across all 10,242 placement samples:
- `min_x`: $\ge 0$ (typically $13$)
- `max_x`: $\le 255$ (typically $245–246$)
- `min_y`: $\ge 0$ (typically $13$)
- `max_y`: $\le 255$ (typically $245–246$)
- Instance format: Each record contains `[x1, y1, x2, y2]`, representing the quantized lower-left and upper-right bounding box in a $256 \times 256$ grid.

---

## 3. Authoritative Determination

- **Coordinate System Status:** **GCELL_GRID_256x256**
- **Physical Meaning:** The placement `.npy` files store quantized GCell grid tile indices spanning the normalized chip canvas $[0, 255] \times [0, 255]$, intended by CircuitNet for 2D spatial feature map generation (e.g., congestion maps, macro density heatmaps).
- **Conversion to DBU / Microns:**
  $$\text{DBU}_x = \text{Grid}_x \times \frac{\text{DieWidth}_{\text{DBU}}}{256}$$
  $$\text{Microns}_x = \frac{\text{DBU}_x}{2000}$$
- **Integrity Rule:** These coordinates must NEVER be directly passed to OpenROAD as literal micron or DBU coordinates without scaling by the design's true floorplan die bounding box.
