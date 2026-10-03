import os
import sys
import time
import subprocess
from pathlib import Path

root = Path("/home/b_siddarth_vijayan/CircuitNet_28nm")
bench_defs = {
    "BENCH_01_RISCY_C2_U70": "dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def",
    "BENCH_02_RISCY_C2_U90": "dataset/processed/DEF_decompressed/DEF/120-RISCY-a-1-c2-u0.9-m1-p1-f0.def",
}

def run_dpl(bench, dpl_args):
    tcl_content = f"""read_lef dataset/raw/circuitnet.lef
read_def -continue_on_errors {bench_defs[bench]}
detailed_placement {dpl_args}
exit
"""
    tcl_path = root / "scratch/sample_dpl.tcl"
    with open(tcl_path, "w") as f:
        f.write(tcl_content)
    cmd = "docker run --rm -v /home/b_siddarth_vijayan/CircuitNet_28nm:/workspace -w /workspace openroad/orfs:latest /OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad -exit scratch/sample_dpl.tcl"
    t0 = time.time()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    dt = time.time() - t0
    hpwl = None
    for line in res.stdout.splitlines():
        if "legalized HPWL" in line:
            parts = line.split()
            hpwl = float(parts[2])
    print(f"{bench} | args: '{dpl_args}' -> HPWL: {hpwl} um | time: {dt:.2f}s")
    return hpwl, dt

print("Testing DPL variations on BENCH_01:")
run_dpl("BENCH_01_RISCY_C2_U70", "")
run_dpl("BENCH_01_RISCY_C2_U70", "-max_displacement 60")
run_dpl("BENCH_01_RISCY_C2_U70", "-site_search_window 60")
run_dpl("BENCH_01_RISCY_C2_U70", "-use_diamond_legalizer")
