# CircuitNet 28nm — VLSI Placement Optimization via Deep Reinforcement Learning

An experimental, open-source replication of:

> **Agnesina et al., "Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning," IEEE TCAD 2023.**

---

## ⚠️ Important Disclaimer

This is an **experimental adaptation**, not a reproduction of the original proprietary paper flow.

| Original Paper | This Implementation |
|----------------|---------------------|
| Synopsys Design Compiler | Gate-level netlists from CircuitNet (pre-synthesized) |
| TSMC 28nm (proprietary) | CircuitNet 28nm LEF (research dataset) |
| Cadence Innovus | OpenROAD (open source) |
| Proprietary Liberty (.db) | CircuitNet LEF only (no Liberty available) |

---

## Dataset

**CircuitNet N28** — A large-scale dataset for VLSI design quality prediction.
- 3 PULPino SoC variants (RISCY-FPU, RISCY, zero-RISCY)
- 54 gate-level Verilog netlists
- 500 placed DEF files with varied parameters

---

## Project Structure

```
CircuitNet_28nm/
├── dataset/
│   ├── raw/          # Original CircuitNet files (DO NOT MODIFY)
│   └── processed/    # Extracted netlists and sample DEF
├── data/
│   ├── graphs/       # Circuit graph representations
│   ├── features/     # Extracted graph features
│   ├── embeddings/   # GraphSAGE embeddings
│   └── activity/     # Simulation VCD (if generated)
├── technology/       # Technology library files
├── configs/          # Experiment configurations (YAML)
├── scripts/          # Utility/inspection scripts
├── src/
│   ├── parsing/      # LEF/DEF/Verilog parsers
│   ├── graph/        # Graph construction
│   ├── features/     # Feature extraction
│   ├── placement/    # OpenROAD wrappers
│   ├── timing/       # Timing analysis
│   ├── power/        # Power analysis
│   └── rl/           # RL environment helpers
├── rl/               # RL agent (environment, actions, state, reward)
├── models/
│   ├── graphsage/    # GraphSAGE encoder
│   └── a2c/          # A2C agent
├── results/
│   ├── data_audit/   # Phase 1 outputs
│   ├── netlist_analysis/
│   ├── baseline/
│   ├── timing/
│   ├── power/
│   ├── experiments/
│   └── final/
├── plots/            # Global plots
├── reports/          # Generated reports
└── docs/
    ├── PROGRESS.md
    ├── PHASE_01_DATA_AUDIT.md
    └── ...
```

---

## Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Data Audit | ✅ COMPLETE |
| Phase 2 | Gate-Level Netlist Analysis | ⬜ NOT STARTED |
| Phase 3 | Technology Library Validation | ⬜ NOT STARTED |
| Phase 4 | Baseline Physical Design | ⬜ NOT STARTED |
| Phase 5 | Timing Analysis | ⬜ NOT STARTED |
| Phase 6 | Power Analysis | ⬜ NOT STARTED |
| Phase 7 | Parameter Sweep | ⬜ NOT STARTED |
| Phase 8 | Graph Features | ⬜ NOT STARTED |
| Phase 9 | GraphSAGE | ⬜ NOT STARTED |
| Phase 10 | RL Environment | ⬜ NOT STARTED |
| Phase 11 | A2C Training | ⬜ NOT STARTED |
| Phase 12 | Final Experiments | ⬜ NOT STARTED |
| Phase 13 | Paper-Style Results | ⬜ NOT STARTED |
| Phase 14 | Final Report | ⬜ NOT STARTED |

See [docs/PROGRESS.md](docs/PROGRESS.md) for detailed phase logs.

---

## Quick Start

```bash
# Activate environment
source ~/envs/vlsi/bin/activate

# Run Phase 1 data audit
cd ~/CircuitNet_28nm
python3 src/parsing/data_audit.py
```

---

## Requirements

- Python 3.12+ with virtualenv at `~/envs/vlsi`
- `numpy`, `pandas`, `matplotlib`, `networkx`, `scipy`, `pyyaml`
- Yosys (installed)
- Icarus Verilog (installed)
- OpenROAD (**not yet installed** — required for Phase 4+)
- PyTorch + PyTorch Geometric (required for Phase 9–11)

---

## Key Phase 1 Findings

| Design | Cells | Nets | Seq Cells | Comb Cells |
|--------|-------|------|-----------|------------|
| RISCY-FPU | 75,067 | 76,583 | 11,546 | 63,518 |
| RISCY | 53,586 | 54,748 | 10,017 | 43,566 |
| zero-RISCY | 42,102 | 42,442 | 8,459 | 33,640 |

DEF Sample (`1-RISCY-a-1-c2-u0.7-m1-p1-f0.def`):
- Die: 583.8 × 582.9 µm²
- Components: 52,147 | Nets: 55,401 | Rows: 498

---

*Last updated: 2026-09-29*
