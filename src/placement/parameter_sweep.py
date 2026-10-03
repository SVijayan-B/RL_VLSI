import os
import sys
import time
import json
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

# Re-use our validated proxy engines and physical metrics
from src.placement.physical_metrics import extract_def_metrics
from src.technology.timing_proxy import TimingProxyEngine
from src.power.power_engine import PowerAndIRProxyEngine
from src.placement.phase7_action_space import Phase7ActionSpace

class PlacementEvaluator:
    """
    Evaluates OpenROAD detailed placement under various parameter settings.
    Extracts HPWL (primary), runtime, legality, timing proxy, power proxy, and IR proxy.
    """
    def __init__(self, workspace_dir="/home/b_siddarth_vijayan/CircuitNet_28nm"):
        self.workspace_dir = Path(workspace_dir)
        self.action_space = Phase7ActionSpace(str(self.workspace_dir / "configs/phase_07/baseline_placement.json"))
        self.timing_engine = TimingProxyEngine()
        self.power_engine = PowerAndIRProxyEngine()
        self.lef_path = self.workspace_dir / "dataset/raw/LEF/circuitnet.lef"

    def run_placement(self, benchmark_id, parameter_config, output_def_name="phase7_eval.def"):
        """
        Runs OpenROAD detailed placement with specified parameters.
        Returns:
            dict containing:
                hpwl_um: float
                runtime_sec: float
                legal: bool
                timing_proxy: dict
                power_proxy: dict
                ir_proxy: dict
                success: bool
        """
        t0 = time.time()
        
        # Benchmark paths
        benchmarks = {
            "BENCH_01_RISCY_C2_U70": {
                "def": self.workspace_dir / "dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def",
                "graph": self.workspace_dir / "dataset/graphs/RISCY-a-1-c2_graph.npz",
                "util": 0.70
            },
            "BENCH_02_RISCY_C2_U90": {
                "def": self.workspace_dir / "dataset/processed/DEF_decompressed/DEF/120-RISCY-a-1-c2-u0.9-m1-p1-f0.def",
                "graph": self.workspace_dir / "dataset/graphs/RISCY-a-1-c2_graph.npz",
                "util": 0.90
            },
            "BENCH_03_RISCY_C5_U70": {
                "def": self.workspace_dir / "dataset/processed/DEF_decompressed/DEF/248-RISCY-a-1-c5-u0.7-m1-p1-f0.def",
                "graph": self.workspace_dir / "dataset/graphs/RISCY-a-1-c5_graph.npz",
                "util": 0.70
            },
            "BENCH_04_RISCY_C20_U70": {
                "def": self.workspace_dir / "dataset/processed/DEF_decompressed/DEF/493-RISCY-a-1-c20-u0.7-m1-p1-f0.def",
                "graph": self.workspace_dir / "dataset/graphs/RISCY-a-1-c20_graph.npz",
                "util": 0.70
            }
        }

        if benchmark_id not in benchmarks:
            raise ValueError(f"Unknown benchmark: {benchmark_id}")

        info = benchmarks[benchmark_id]
        in_def = info["def"]
        graph_path = info["graph"]
        out_def_path = self.workspace_dir / "scratch" / output_def_name
        os.makedirs(self.workspace_dir / "scratch", exist_ok=True)

        dpl_args = self.action_space.to_openroad_args(parameter_config)

        tcl_script = f"""
read_lef {self.lef_path}
read_def -continue_on_errors {in_def}
detailed_placement {dpl_args}
check_placement
write_def {out_def_path}
exit
"""
        tcl_file = self.workspace_dir / "scratch" / f"eval_run_{benchmark_id}.tcl"
        with open(tcl_file, "w") as f:
            f.write(tcl_script)

        # Execute via OpenROAD Docker
        cmd = f"""docker run --rm -v "{self.workspace_dir}:/workspace" -w /workspace openroad/orfs:latest bash -lc '
export PATH=/OpenROAD-flow-scripts/tools/install/OpenROAD/bin:$PATH
openroad -exit scratch/eval_run_{benchmark_id}.tcl
'"""

        res = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
        runtime = time.time() - t0
        
        stdout = res.stdout + res.stderr
        legal = "Placement analysis: total 0" in stdout or "0 violations" in stdout or res.returncode == 0
        success = res.returncode == 0 and out_def_path.exists()

        if not success:
            return {
                "benchmark": benchmark_id,
                "hpwl_um": np.nan,
                "runtime_sec": runtime,
                "legal": False,
                "success": False,
                "notes": f"OpenROAD failed with code {res.returncode}"
            }

        # Extract HPWL and physical metrics
        metrics = extract_def_metrics(out_def_path, self.lef_path)
        hpwl_um = metrics.get("total_hpwl_um", 0.0)

        # Timing proxy
        timing_metrics = self.timing_engine.evaluate_placement_timing(str(graph_path), str(out_def_path))
        
        # Power proxy
        power_metrics = self.power_engine.evaluate_placement_power(str(graph_path), str(out_def_path))

        return {
            "benchmark": benchmark_id,
            "hpwl_um": hpwl_um,
            "runtime_sec": runtime,
            "legal": legal,
            "success": True,
            "delay_proxy": timing_metrics.get("mean_net_delay_ps", 0.0),
            "max_path_delay_proxy": timing_metrics.get("max_path_delay_proxy_ps", 0.0),
            "power_proxy": power_metrics.get("total_power_proxy", 0.0),
            "ir_proxy": power_metrics.get("peak_static_ir_drop_proxy_mv", 0.0),
            "notes": "Legalized successfully"
        }
