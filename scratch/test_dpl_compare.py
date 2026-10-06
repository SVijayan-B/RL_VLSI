import subprocess, time

def test_cmd(dpl_cmd):
    tcl = f'''read_lef /CircuitNet/dataset/raw/circuitnet.lef
read_def -continue_on_errors /CircuitNet/results/phase_11c/RISCY-a-2-c2_reconstructed.def
detailed_placement {dpl_cmd}
check_placement -verbose
exit
'''
    t0 = time.time()
    res = subprocess.run(
        ['docker', 'run', '--rm', '-i', '-v', '/home/b_siddarth_vijayan/CircuitNet_28nm:/CircuitNet', 'openroad/orfs:latest', '/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad', '-no_splash'],
        input=tcl, text=True, capture_output=True, timeout=60
    )
    print(f'CMD: [{dpl_cmd}] time={time.time()-t0:.2f}s, rc={res.returncode}')
    for l in res.stdout.splitlines():
        if any(k in l for k in ['HPWL', 'Placement analysis', 'violations', 'moves', 'max displacement']):
            print('  ', l)

test_cmd('')
test_cmd('-use_diamond_legalizer')
