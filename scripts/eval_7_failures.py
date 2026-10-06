import os
import sys
from pathlib import Path
import subprocess
import time
import re
import numpy as np

BASE_DIR = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
sys.path.insert(0, str(BASE_DIR))

from src.placement.lef_site_model import LEFSiteModel
from src.placement.coordinate_mapper import CoordinateMapper
from src.placement.def_reconstructor import DEFReconstructor

OUT_DIR = BASE_DIR / "results/phase_11d"
DEF_DIR = OUT_DIR / "reconstructed_defs"

lef_model = LEFSiteModel(BASE_DIR / 'dataset/raw/circuitnet.lef')
reconstructor = DEFReconstructor(dbu_per_micron=2000)
mapper = CoordinateMapper(lef_model=lef_model, dbu_per_micron=2000)

fails = ["RISCY-FPU-a-1-c2", "RISCY-FPU-a-2-c20", "RISCY-FPU-a-3-c2", "RISCY-b-1-c2", "RISCY-b-2-c2", "RISCY-b-2-c5", "zero-riscy-a-1-c2"]

import pandas as pd
df_map = pd.read_csv(BASE_DIR / 'results/phase_11b/manifests/placement_design_mapping.csv')
# get first sample for each
df_rep = df_map.groupby('graph_design_id').first().reset_index()

for d_id in fails:
    row = df_rep[df_rep['graph_design_id'] == d_id].iloc[0]
    p_path = BASE_DIR / row['placement_path']
    g_data = np.load(BASE_DIR / f"dataset/graphs/{d_id}_graph.npz", allow_pickle=True)
    
    tot_cell_area = sum([(lef_model.get_macro_size_dbu(ct)[0]/2000.0) * (lef_model.get_macro_size_dbu(ct)[1]/2000.0) for ct in g_data['cell_types']])
    m_util = re.findall(r'-u([0-9\.]+)-', p_path.name)
    target_util = float(m_util[0]) if m_util else 0.70
    target_dim = np.sqrt(tot_cell_area / target_util)
    num_rows = int(round(target_dim / 1.05))
    die_w = int(round(target_dim / 0.21)) * 420
    die_h = num_rows * 2100

    p_dict = np.load(p_path, allow_pickle=True).item()
    components, missing = mapper.reconstruct_layout(d_id, g_data['cell_names'], g_data['cell_types'], g_data['cell_features'], p_dict, die_w, die_h, num_rows)
    
    # Validation logic
    overlap_cnt = 0
    comp_boxes = []
    for inst, ctype, x, y, orient, status in components:
        w, h = lef_model.get_macro_size_dbu(ctype)
        comp_boxes.append((inst, x, y, x + w, y + h))
    row_map = {}
    for inst, x1, y1, x2, y2 in comp_boxes:
        r = y1 // 2100
        if r not in row_map: row_map[r] = []
        row_map[r].append((inst, x1, x2))
    for r, intervals in row_map.items():
        intervals.sort(key=lambda item: item[1])
        for k in range(len(intervals) - 1):
            if intervals[k][2] > intervals[k+1][1]:
                overlap_cnt += 1
                
    print(f"{d_id} recon overlap count: {overlap_cnt}")

    if overlap_cnt == 0:
        net_conns = {n: [] for n in g_data['net_names']}
        src_cells = g_data['edge_index_bipartite'][0]
        dst_nets = g_data['edge_index_bipartite'][1]
        for ci in range(len(src_cells)):
            net_conns[g_data['net_names'][dst_nets[ci]]].append((g_data['cell_names'][src_cells[ci]], g_data['pin_names'][ci]))
        valid_nets = [(n, conns) for n, conns in net_conns.items() if len(conns) >= 2]
        def_path = DEF_DIR / f"{d_id}.def"
        reconstructor.generate_def(d_id, die_w, die_h, num_rows, components, valid_nets, [], str(def_path))
        
        tcl = f"read_lef /CircuitNet/dataset/raw/circuitnet.lef\nread_def -continue_on_errors /CircuitNet/results/phase_11d/reconstructed_defs/{d_id}.def\ndetailed_placement -use_diamond_legalizer\ncheck_placement -verbose\nexit\n"
        res = subprocess.run(
            ["docker", "run", "--rm", "-i", "-v", f"{BASE_DIR}:/CircuitNet", "openroad/orfs:latest", "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad", "-no_splash"],
            input=tcl, text=True, capture_output=True, timeout=20
        )
        if "detailed placement checks failed" in res.stdout or "Total Placement Failures:" in res.stdout:
            print(f"{d_id} DPL FAIL")
        else:
            print(f"{d_id} DPL PASS")
