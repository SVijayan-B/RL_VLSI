import subprocess
tcl = '''read_lef /CircuitNet/dataset/raw/circuitnet.lef
read_def -continue_on_errors /CircuitNet/results/phase_11c/def_reconstruction/RISCY-a-2-c2.def
detailed_placement -use_diamond_legalizer
check_placement -verbose
exit
'''
res = subprocess.run(
    ['docker', 'run', '--rm', '-i', '-v', '/home/b_siddarth_vijayan/CircuitNet_28nm:/CircuitNet', 'openroad/orfs:latest', '/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad', '-no_splash'],
    input=tcl, text=True, capture_output=True
)
print('STDOUT:')
print(res.stdout)
print('STDERR:')
print(res.stderr)
print('RC:', res.returncode)
