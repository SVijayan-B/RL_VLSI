# CircuitNet 28nm — Dataset Cleanup Log

This document records every file and directory removed during the dataset consolidation and cleanup phase. Every deletion was verified against the project's strict safety rules prior to removal.

---

## Pre-Cleanup Disk Usage
- **Total WSL Filesystem:** 80 GB used / 877 GB available
- **Total `dataset/` Size:** 77 GB
  - `dataset/raw/`: 2.8 GB
  - `dataset/processed/`: 30 GB
  - `dataset/graph_features/`: 45 GB
  - `dataset/metadata/`: 7.4 MB
  - `dataset/preprocess_scripts/`: 4.0 KB

---

## Deleted Items

### 1. Incomplete Temporary Download Fragment
- **PATH:** `dataset/graph_features/graph_features/instance_placement_gcell.tar.gzi53y992p.part`
- **REASON:** Incomplete, corrupted temporary download artifact.
- **SIZE:** 31,457,280 bytes (~30.0 MB)
- **HOW IT WAS VERIFIED:** Checked file header, filename extension (`.part`), and size. The complete placement archive `instance_placement_micron.tar.gz` (5.70 GB) is present, verified, and fully extracted to 10,242 samples (39 GB).
- **SAFE TO DELETE BECAUSE:** It is an aborted partial download fragment with no valid data.

### 2. Duplicate Graph Information Archive
- **PATH:** `dataset/graph_features/graph_features/graph_information.tar.gz`
- **REASON:** Exact bit-for-bit duplicate of the primary graph information archive.
- **SIZE:** 66,418,737 bytes (~63.3 MB)
- **HOW IT WAS VERIFIED:** Computed MD5 checksum (`6624f16df5a0aa329a260565ae8d0a4c`) and verified it is 100% identical to `dataset/graph_features/graph_information.tar.gz`.
- **SAFE TO DELETE BECAUSE:** The identical archive is preserved in `dataset/raw/graph_information.tar.gz`, and its contents are already extracted to `dataset/circuit_graph/`.

### 3. Redundant Sample Directory
- **PATH:** `dataset/processed/sample_1/` (containing `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def`)
- **REASON:** Single-sample redundant duplicate.
- **SIZE:** 54,728,704 bytes (~52.2 MB)
- **HOW IT WAS VERIFIED:** Computed MD5 checksum (`304c0559797b68b5143e473b7a98f47e`) and confirmed it matches `1-RISCY-a-1-c2-u0.7-m1-p1-f0.def` in `DEF_decompressed/`.
- **SAFE TO DELETE BECAUSE:** The identical decompressed DEF is retained in the consolidated DEFs directory, and the original compressed copy exists in `DEF-place-0.tar.gz`.

### 4. Intermediate Compressed DEF Files
- **PATH:** `dataset/processed/DEF/` (containing 500 `.def.gz` files)
- **REASON:** Intermediate extraction duplicate of the raw archive.
- **SIZE:** 2,862,687,448 bytes (~2.73 GB)
- **HOW IT WAS VERIFIED:** Verified that `dataset/raw/DEF-place-0.tar.gz` contains these exact 500 `.def.gz` files (verified with sample MD5 `5ad52c8411a7816a5b1869708089c61d`), and all 500 files are already uncompressed and validated in `dataset/processed/DEF_decompressed/` (~26 GB).
- **SAFE TO DELETE BECAUSE:** Retaining both the raw `.tar.gz` (2.86 GB), the intermediate `.def.gz` (2.73 GB), and the uncompressed `.def` (26 GB) triples storage needlessly. The raw archive `dataset/raw/DEF-place-0.tar.gz` is retained for 100% reproducibility, and the uncompressed `.def` files are retained for OpenROAD baseline validation.

---

## Directory Reorganizations (Non-Destructive Moves)

The following moves were executed within the filesystem (zero copy overhead, instantaneous metadata rename):

1. **Graph Attributes:**
   - Source: `dataset/graph_features/graph_information/{net_attr, node_attr, pin_attr}`
   - Destination: `dataset/circuit_graph/{net_attr, node_attr, pin_attr}`
   - Verification: 54 files in each subdirectory (162 files total), 533 MB.

2. **Instance Placement:**
   - Source: `dataset/graph_features/instance_placement_micron/instance_placement_gcell/*.npy`
   - Destination: `dataset/placement/instance_placement/*.npy`
   - Verification: Exactly 10,242 `.npy` files, 39 GB.

3. **Graph & Placement Archives (Preserved Raw Data):**
   - Source: `dataset/graph_features/graph_information.tar.gz` -> `dataset/raw/graph_information.tar.gz`
   - Source: `dataset/graph_features/instance_placement_micron.tar.gz` -> `dataset/raw/instance_placement_micron.tar.gz`
   - Verification: Both archives preserved intact in `dataset/raw/` alongside `circuitnet.lef`, `netlist.tar.gz`, and `DEF-place-0.tar.gz`.

4. **Empty Source Containers Removed:**
   - `dataset/graph_features/graph_features/` (after deleting .part and duplicate .tar.gz)
   - `dataset/graph_features/instance_placement_micron/` (after moving placement files)
   - `dataset/graph_features/` (empty directory)

---

## Post-Cleanup Disk Usage Summary
- **Space Reclaimed:** ~2.85 GB
- **Retained Core Data:**
  - `dataset/raw/`: 8.6 GB (all 4 original archives + LEF)
  - `dataset/circuit_graph/`: 533 MB (162 attribute files across 54 designs)
  - `dataset/placement/`: 39 GB (10,242 placement samples)
  - `dataset/processed/`: 27 GB (54 netlists + 500 uncompressed DEFs)
  - `dataset/metadata/`: 7.4 MB (all manifests, dataset index CSV/JSON)
  - `dataset/preprocess_scripts/`: 4.0 KB
