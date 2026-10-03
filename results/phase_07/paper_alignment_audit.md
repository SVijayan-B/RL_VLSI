# Phase 7 — Paper Alignment & Parameter Mapping Audit

## Reference Paper:
Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim,
"Parameter Optimization of VLSI Placement Through Deep Reinforcement Learning,"
IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, 2023.

---

## 1. Table I Parameter Audit (12 Parameters)
The reference paper targets 12 placement parameters from Cadence Innovus 17.1 (Table I, page 1298):
1. `eco max distance`: integer in [0, 100], detail placement.
2. `legalization gap`: integer in [0, 100], detail placement.
3. `max density`: integer in [0, 100], global placement.
4. `eco priority`: enum {none, eco, placed}, detail placement.
5. `activity power driven`: enum {none, medium, high}, detail + effort.
6. `wire length opt`: enum {none, medium, high}, detail + effort.
7. `blockage channel`: enum {none, soft, hard}, global placement.
8. `timing effort`: enum {none, low, high}, global + effort.
9. `clock power driven`: enum {none, medium, high}, global + effort.
10. `congestion effort`: enum {none, low, high}, global + effort.
11. `clock gate aware`: bool {true, false}, global placement.
12. `uniform density`: bool {true, false}, global placement.

All 12 parameters are formally indexed in `results/phase_07/paper_parameter_reference.csv`.

---

## 2. Table III Action Audit (11 Actions)
The reference paper defines 11 deterministic actions (Table III, page 1299):
1. `FLIP Booleans`: Inverts Boolean flags.
2. `UP Integers`: Increases integer parameters by bounded delta $\Delta x_0$.
3. `DOWN Integers`: Decreases integer parameters by bounded delta $\Delta x_0$.
4. `UP Efforts`: Shifts enumerated effort levels up (none $\to$ medium $\to$ high).
5. `DOWN Efforts`: Shifts enumerated effort levels down (high $\to$ medium $\to$ none).
6. `UP Detailed`: Shifts detailed placement parameters up.
7. `DOWN Detailed`: Shifts detailed placement parameters down.
8. `UP Global`: Shifts global parameters up (excluding Booleans).
9. `DOWN Global`: Shifts global parameters down (excluding Booleans).
10. `INVERT-MIX`: Exchanges trade-off efforts (timing vs congestion vs WL).
11. `DO NOTHING`: Identity action; triggers environment reset if selected 5 times consecutively.

All 11 actions are formally indexed in `results/phase_07/paper_action_reference.csv`.

---

## 3. Open-Source Adaptation & Toolchain Realities
- In Cadence Innovus, the tool exposes unified global and detailed placement engines that can be steered concurrently with Liberty (`.lib`) timing libraries.
- In CircuitNet N28, standard cell Liberty `.lib` files are withheld by the dataset creators.
- In OpenROAD, running `global_placement` requires either `.lib` timing tables or pre-routed clock trees. However, OpenROAD's detailed placer (`detailed_placement` / `DPL`) is completely standalone, robust, and operates directly on ingested standard cell coordinates.
- Therefore, we map:
  - Detailed placement displacement and search windows to OpenROAD DPL arguments (`-max_displacement`, `-site_search_window`, etc.).
  - Global and timing/power-driven parameters are categorized strictly as `UNAVAILABLE` in `results/phase_07/paper_to_openroad_parameter_map.csv`.
- This ensures full fidelity to open-source physical design without fabricating proprietary EDA flags.
