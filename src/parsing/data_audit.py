"""
Comprehensive Data Audit Script for CircuitNet 28nm Dataset
Phase 1 implementation for VLSI Placement Optimization
"""

import os
import re
import json
import gzip
import tarfile
from collections import Counter, defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

WORKSPACE_DIR = os.path.expanduser("~/CircuitNet_28nm")
RAW_DIR = os.path.join(WORKSPACE_DIR, "dataset/raw")
PROCESSED_NETLIST_DIR = os.path.join(WORKSPACE_DIR, "dataset/processed/netlists/netlist")
PROCESSED_DEF_DIR = os.path.join(WORKSPACE_DIR, "dataset/processed/sample_1/DEF")
RESULTS_DIR = os.path.join(WORKSPACE_DIR, "results/data_audit")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

def parse_lef(lef_path):
    print(f"Parsing LEF: {lef_path}")
    db_microns = 2000
    manufacturing_grid = None
    sites = {}
    layers = {}
    macros = {}

    current_macro = None
    current_site = None
    current_layer = None
    current_pin = None

    with open(lef_path, 'r', errors='ignore') as f:
        for line in f:
            line_s = line.strip()
            if not line_s or line_s.startswith('#'):
                continue

            # Database microns
            m_db = re.match(r'DATABASE\s+MICRONS\s+(\d+)', line_s)
            if m_db:
                db_microns = int(m_db.group(1))
                continue

            # Manufacturing grid
            m_grid = re.match(r'MANUFACTURINGGRID\s+([\d\.]+)', line_s)
            if m_grid:
                manufacturing_grid = float(m_grid.group(1))
                continue

            # SITE
            m_site = re.match(r'^SITE\s+(\S+)', line_s)
            if m_site:
                current_site = {'name': m_site.group(1)}
                continue
            if current_site:
                m_size = re.match(r'SIZE\s+([\d\.]+)\s+BY\s+([\d\.]+)', line_s)
                if m_size:
                    current_site['width'] = float(m_size.group(1))
                    current_site['height'] = float(m_size.group(2))
                m_class = re.match(r'CLASS\s+(\S+)', line_s)
                if m_class:
                    current_site['class'] = m_class.group(1).rstrip(';')
                m_sym = re.match(r'SYMMETRY\s+(.+);', line_s)
                if m_sym:
                    current_site['symmetry'] = m_sym.group(1).strip()
                if re.match(r'^END\s+' + re.escape(current_site['name']), line_s):
                    sites[current_site['name']] = current_site
                    current_site = None
                continue

            # LAYER
            m_layer = re.match(r'^LAYER\s+(\S+)', line_s)
            if m_layer:
                current_layer = {'name': m_layer.group(1)}
                continue
            if current_layer:
                m_type = re.match(r'TYPE\s+(\S+)', line_s)
                if m_type:
                    current_layer['type'] = m_type.group(1).rstrip(';')
                m_dir = re.match(r'DIRECTION\s+(\S+)', line_s)
                if m_dir:
                    current_layer['direction'] = m_dir.group(1).rstrip(';')
                m_pitch = re.match(r'PITCH\s+([\d\.]+)', line_s)
                if m_pitch:
                    current_layer['pitch'] = float(m_pitch.group(1))
                m_width = re.match(r'WIDTH\s+([\d\.]+)', line_s)
                if m_width:
                    current_layer['width'] = float(m_width.group(1))
                if re.match(r'^END\s+' + re.escape(current_layer['name']), line_s):
                    layers[current_layer['name']] = current_layer
                    current_layer = None
                continue

            # MACRO
            m_macro = re.match(r'^MACRO\s+(\S+)', line_s)
            if m_macro:
                current_macro = {
                    'name': m_macro.group(1),
                    'pins': {},
                    'class': 'CORE',
                    'width': 0.0,
                    'height': 0.0,
                    'site': None
                }
                continue
            if current_macro:
                if line_s.startswith('END '):
                    end_name = line_s.split()[1].rstrip(';')
                    if end_name == current_macro['name']:
                        macros[current_macro['name']] = current_macro
                        current_macro = None
                        continue
                    elif current_pin and end_name == current_pin['name']:
                        current_macro['pins'][current_pin['name']] = current_pin
                        current_pin = None
                        continue

                m_class = re.match(r'CLASS\s+(\S+)', line_s)
                if m_class:
                    current_macro['class'] = m_class.group(1).rstrip(';')
                    continue
                m_size = re.match(r'SIZE\s+([\d\.]+)\s+BY\s+([\d\.]+)', line_s)
                if m_size:
                    current_macro['width'] = float(m_size.group(1))
                    current_macro['height'] = float(m_size.group(2))
                    continue
                m_site = re.match(r'SITE\s+(\S+)', line_s)
                if m_site:
                    current_macro['site'] = m_site.group(1).rstrip(';')
                    continue

                m_pin = re.match(r'PIN\s+(\S+)', line_s)
                if m_pin:
                    current_pin = {'name': m_pin.group(1), 'direction': 'UNKNOWN', 'use': 'SIGNAL'}
                    continue
                if current_pin:
                    m_pdir = re.match(r'DIRECTION\s+(\S+)', line_s)
                    if m_pdir:
                        current_pin['direction'] = m_pdir.group(1).rstrip(';')
                    m_puse = re.match(r'USE\s+(\S+)', line_s)
                    if m_puse:
                        current_pin['use'] = m_puse.group(1).rstrip(';')
                    continue

    print(f"Parsed LEF: {len(macros)} macros, {len(layers)} layers, {len(sites)} sites")
    return {
        'db_microns': db_microns,
        'manufacturing_grid': manufacturing_grid,
        'sites': sites,
        'layers': layers,
        'macros': macros
    }

def parse_def(def_path):
    print(f"Parsing DEF: {def_path}")
    units = 2000
    design_name = ""
    die_area = None
    components = {}
    nets = defaultdict(list)
    pins = {}
    rows = []

    in_components = False
    in_nets = False
    in_pins = False
    current_net = None

    with open(def_path, 'r', errors='ignore') as f:
        for line in f:
            line_s = line.strip()
            if not line_s or line_s.startswith('#'):
                continue

            if line_s.startswith('DESIGN'):
                design_name = line_s.split()[1].rstrip(';')
                continue
            if 'UNITS DISTANCE MICRONS' in line_s:
                parts = line_s.split()
                idx = parts.index('MICRONS')
                units = int(parts[idx+1].rstrip(';'))
                continue
            if line_s.startswith('DIEAREA'):
                coords = re.findall(r'\(\s*(-?\d+)\s+(-?\d+)\s*\)', line_s)
                if len(coords) >= 2:
                    die_area = {
                        'llx': int(coords[0][0]),
                        'lly': int(coords[0][1]),
                        'urx': int(coords[1][0]),
                        'ury': int(coords[1][1])
                    }
                continue
            if line_s.startswith('ROW'):
                parts = line_s.split()
                if len(parts) >= 12:
                    rows.append({
                        'name': parts[1],
                        'site': parts[2],
                        'x': int(parts[3]),
                        'y': int(parts[4]),
                        'orient': parts[5],
                        'num_x': int(parts[7]),
                        'num_y': int(parts[9]),
                        'step_x': int(parts[11]),
                        'step_y': int(parts[12]) if len(parts) > 12 else 0
                    })
                continue

            if line_s.startswith('COMPONENTS'):
                in_components = True
                continue
            if in_components:
                if line_s.startswith('END COMPONENTS'):
                    in_components = False
                    continue
                if line_s.startswith('-'):
                    parts = line_s.split()
                    comp_name = parts[1]
                    cell_type = parts[2]
                    status = "UNPLACED"
                    pos = (0, 0)
                    orient = "N"
                    if len(parts) > 3 and '+' in parts:
                        plus_idx = parts.index('+')
                        if plus_idx + 1 < len(parts):
                            status = parts[plus_idx + 1]
                    m_pos = re.search(r'\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(\w+)', line_s)
                    if m_pos:
                        pos = (int(m_pos.group(1)), int(m_pos.group(2)))
                        orient = m_pos.group(3)
                    components[comp_name] = {
                        'cell_type': cell_type,
                        'status': status,
                        'pos': pos,
                        'orient': orient
                    }
                continue

            if line_s.startswith('PINS'):
                in_pins = True
                continue
            if in_pins:
                if line_s.startswith('END PINS'):
                    in_pins = False
                    continue
                if line_s.startswith('-'):
                    parts = line_s.split()
                    pin_name = parts[1]
                    pins[pin_name] = {'net': parts[3] if len(parts) > 3 and parts[2] == '+ NET' else pin_name}
                continue

            if line_s.startswith('NETS'):
                in_nets = True
                continue
            if in_nets:
                if line_s.startswith('END NETS'):
                    in_nets = False
                    continue
                if line_s.startswith('-'):
                    parts = line_s.split()
                    current_net = parts[1]
                    conns = re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)', line_s)
                    for c in conns:
                        nets[current_net].append({'comp': c[0], 'pin': c[1]})
                    continue
                if current_net:
                    conns = re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)', line_s)
                    for c in conns:
                        nets[current_net].append({'comp': c[0], 'pin': c[1]})
                    if ';' in line_s:
                        current_net = None
                continue

    core_llx = min((r['x'] for r in rows), default=0)
    core_lly = min((r['y'] for r in rows), default=0)
    core_urx = max((r['x'] + r['num_x'] * r['step_x'] for r in rows), default=0)
    core_ury = max(r['y'] for r in rows) + 2100 if rows else 0

    print(f"Parsed DEF: {len(components)} components, {len(nets)} nets, {len(pins)} pins, {len(rows)} rows")
    return {
        'design_name': design_name,
        'units': units,
        'die_area': die_area,
        'core_box': {'llx': core_llx, 'lly': core_lly, 'urx': core_urx, 'ury': core_ury},
        'rows_count': len(rows),
        'components': components,
        'nets': nets,
        'pins': pins
    }

def parse_gate_level_verilog(v_path):
    print(f"Parsing Verilog: {v_path}")
    module_name = ""
    primary_inputs = set()
    primary_outputs = set()
    inouts = set()
    wires = set()
    cell_instances = {}
    net_connections = defaultdict(list)
    clock_signals = set()
    reset_signals = set()

    with open(v_path, 'r', errors='ignore') as f:
        content = f.read()

    m_mod = re.search(r'\bmodule\s+([a-zA-Z0-9_]+)\s*\(', content)
    if m_mod:
        module_name = m_mod.group(1)

    for m in re.finditer(r'\binput\s+(?:\[[^\]]+\]\s+)?([^;]+);', content):
        names = [n.strip() for n in m.group(1).split(',')]
        primary_inputs.update(names)

    for m in re.finditer(r'\boutput\s+(?:\[[^\]]+\]\s+)?([^;]+);', content):
        names = [n.strip() for n in m.group(1).split(',')]
        primary_outputs.update(names)

    for m in re.finditer(r'\binout\s+(?:\[[^\]]+\]\s+)?([^;]+);', content):
        names = [n.strip() for n in m.group(1).split(',')]
        inouts.update(names)

    for m in re.finditer(r'\bwire\s+(?:\[[^\]]+\]\s+)?([^;]+);', content):
        names = [n.strip() for n in m.group(1).split(',')]
        wires.update(names)

    for inp in primary_inputs:
        inp_lower = inp.lower()
        if 'clk' in inp_lower or 'clock' in inp_lower:
            clock_signals.add(inp)
        if 'rst' in inp_lower or 'reset' in inp_lower:
            reset_signals.add(inp)

    inst_pattern = re.compile(
        r'\b([A-Z0-9_]+)\s+([a-zA-Z0-9_\/\.\[\]]+)\s*\((.*?)\);',
        re.DOTALL
    )

    cell_type_counts = Counter()
    sequential_count = 0
    combinational_count = 0
    macro_count = 0

    seq_prefixes = ('DF', 'LATCH', 'EDF', 'SDF', 'GDF', 'FF')
    macro_types = {'SRAM', 'PLL', 'ROM'}

    for m in inst_pattern.finditer(content):
        cell_type = m.group(1)
        inst_name = m.group(2)
        conns_str = m.group(3)

        if cell_type in ('module', 'input', 'output', 'wire', 'assign', 'supply0', 'supply1'):
            continue

        cell_type_counts[cell_type] += 1
        is_seq = any(cell_type.startswith(p) for p in seq_prefixes)
        is_macro = cell_type in macro_types

        if is_seq:
            sequential_count += 1
        elif is_macro:
            macro_count += 1
        else:
            combinational_count += 1

        pins = {}
        for pm in re.finditer(r'\.([a-zA-Z0-9_]+)\s*\(\s*([^)]*)\s*\)', conns_str):
            pin_name = pm.group(1)
            net_name = pm.group(2).strip()
            pins[pin_name] = net_name
            if net_name:
                net_connections[net_name].append((inst_name, pin_name))

        cell_instances[inst_name] = {
            'type': cell_type,
            'is_seq': is_seq,
            'is_macro': is_macro,
            'pins': pins
        }

    print(f"Parsed Verilog {os.path.basename(v_path)}: {len(cell_instances)} cells, {len(net_connections)} nets")

    return {
        'file_name': os.path.basename(v_path),
        'module_name': module_name,
        'primary_inputs': list(primary_inputs),
        'primary_outputs': list(primary_outputs),
        'inouts': list(inouts),
        'wires_count': len(wires),
        'clocks': list(clock_signals),
        'resets': list(reset_signals),
        'total_cells': len(cell_instances),
        'sequential_cells': sequential_count,
        'combinational_cells': combinational_count,
        'macro_cells': macro_count,
        'cell_type_counts': dict(cell_type_counts),
        'cell_instances': cell_instances,
        'net_connections': net_connections
    }

def audit_raw_archives():
    print("Auditing raw archives...")
    netlist_tar = os.path.join(RAW_DIR, "netlist.tar.gz")
    def_tar = os.path.join(RAW_DIR, "DEF-place-0.tar.gz")

    netlist_files = []
    if os.path.exists(netlist_tar):
        with tarfile.open(netlist_tar, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".v"):
                    netlist_files.append({
                        'name': os.path.basename(member.name),
                        'size_bytes': member.size
                    })

    def_files = []
    if os.path.exists(def_tar):
        with tarfile.open(def_tar, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".def.gz") or member.name.endswith(".def"):
                    def_files.append({
                        'name': os.path.basename(member.name),
                        'size_bytes': member.size
                    })

    def_params = []
    for d in def_files:
        m = re.match(r'(\d+)-([a-zA-Z0-9_\-]+?)-u([\d\.]+)-m(\d+)-p(\d+)-f(\d+)', d['name'])
        if m:
            def_params.append({
                'id': int(m.group(1)),
                'design': m.group(2),
                'utilization': float(m.group(3)),
                'macro_margin': int(m.group(4)),
                'placement_effort': int(m.group(5)),
                'fill_or_freq': int(m.group(6))
            })

    return {
        'netlist_archive_count': len(netlist_files),
        'def_archive_count': len(def_files),
        'total_def_params_parsed': len(def_params),
        'unique_designs_in_def': sorted(list(set(p['design'] for p in def_params))) if def_params else [],
        'utilization_values': sorted(list(set(p['utilization'] for p in def_params))) if def_params else [],
        'macro_margins': sorted(list(set(p['macro_margin'] for p in def_params))) if def_params else [],
        'placement_efforts': sorted(list(set(p['placement_effort'] for p in def_params))) if def_params else []
    }

def main():
    print("=" * 60)
    print("STARTING CIRCUITNET 28NM DATA AUDIT (PHASE 1)")
    print("=" * 60)

    lef_data = parse_lef(os.path.join(RAW_DIR, "circuitnet.lef"))
    sample_def_path = os.path.join(PROCESSED_DEF_DIR, "1-RISCY-a-1-c2-u0.7-m1-p1-f0.def")
    def_data = parse_def(sample_def_path)

    netlist_paths = sorted([
        os.path.join(PROCESSED_NETLIST_DIR, f)
        for f in os.listdir(PROCESSED_NETLIST_DIR)
        if f.endswith('.v')
    ])
    netlist_results = {}
    for p in netlist_paths:
        netlist_results[os.path.basename(p)] = parse_gate_level_verilog(p)

    raw_archive_audit = audit_raw_archives()

    print("\nPerforming consistency checks...")
    riscy_v = netlist_results.get("RISCY-a-1-c2.v")
    def_comps = def_data['components']
    def_nets = def_data['nets']

    netlist_cells = set(riscy_v['cell_instances'].keys())
    def_cells = set(def_comps.keys())

    common_cells = netlist_cells.intersection(def_cells)
    netlist_only_cells = netlist_cells - def_cells
    def_only_cells = def_cells - netlist_cells
    def_only_types = Counter(def_comps[c]['cell_type'] for c in def_only_cells)

    def_cell_types = set(c['cell_type'] for c in def_comps.values())
    lef_macros = set(lef_data['macros'].keys())

    def_types_in_lef = def_cell_types.intersection(lef_macros)
    def_types_missing_in_lef = def_cell_types - lef_macros

    all_netlist_cell_types = set()
    for nr in netlist_results.values():
        all_netlist_cell_types.update(nr['cell_type_counts'].keys())

    netlist_types_in_lef = all_netlist_cell_types.intersection(lef_macros)
    netlist_types_missing_in_lef = all_netlist_cell_types - lef_macros

    dbu = def_data['units']
    die = def_data['die_area']
    die_w_um = (die['urx'] - die['llx']) / dbu if die else 0
    die_h_um = (die['ury'] - die['lly']) / dbu if die else 0
    die_area_um2 = die_w_um * die_h_um

    core = def_data['core_box']
    core_w_um = (core['urx'] - core['llx']) / dbu
    core_h_um = (core['ury'] - core['lly']) / dbu
    core_area_um2 = core_w_um * core_h_um

    total_cell_area_um2 = 0.0
    for comp in def_comps.values():
        ctype = comp['cell_type']
        if ctype in lef_data['macros']:
            m = lef_data['macros'][ctype]
            total_cell_area_um2 += m['width'] * m['height']

    core_utilization_calc = (total_cell_area_um2 / core_area_um2) if core_area_um2 > 0 else 0

    design_stats = []
    for fname, d in netlist_results.items():
        fanouts = [len(sinks) for sinks in d['net_connections'].values()]
        degrees = [len(c['pins']) for c in d['cell_instances'].values()]
        design_stats.append({
            'design_name': d['module_name'],
            'source_file': fname,
            'primary_inputs': len(d['primary_inputs']),
            'primary_outputs': len(d['primary_outputs']),
            'inouts': len(d['inouts']),
            'clock_signals': len(d['clocks']),
            'reset_signals': len(d['resets']),
            'total_cells': d['total_cells'],
            'sequential_cells': d['sequential_cells'],
            'combinational_cells': d['combinational_cells'],
            'macro_cells': d['macro_cells'],
            'unique_cell_types': len(d['cell_type_counts']),
            'total_nets': len(d['net_connections']),
            'avg_fanout': round(float(np.mean(fanouts)), 2) if fanouts else 0,
            'max_fanout': int(np.max(fanouts)) if fanouts else 0,
            'avg_degree': round(float(np.mean(degrees)), 2) if degrees else 0,
            'max_degree': int(np.max(degrees)) if degrees else 0
        })

    df_designs = pd.DataFrame(design_stats)
    df_designs.to_csv(os.path.join(RESULTS_DIR, "design_statistics.csv"), index=False)
    print(f"Saved {os.path.join(RESULTS_DIR, 'design_statistics.csv')}")

    cell_stats = []
    for fname, d in netlist_results.items():
        for ctype, count in d['cell_type_counts'].items():
            cell_stats.append({
                'design': fname,
                'cell_type': ctype,
                'count': count,
                'is_sequential': any(ctype.startswith(p) for p in ('DF', 'LATCH', 'EDF', 'SDF', 'GDF', 'FF')),
                'is_macro': ctype in ('SRAM', 'PLL', 'ROM'),
                'in_lef': ctype in lef_macros
            })
    df_cells = pd.DataFrame(cell_stats)
    df_cells.to_csv(os.path.join(RESULTS_DIR, "cell_statistics.csv"), index=False)
    print(f"Saved {os.path.join(RESULTS_DIR, 'cell_statistics.csv')}")

    net_stats = []
    for fname, d in netlist_results.items():
        sorted_nets = sorted(d['net_connections'].items(), key=lambda x: len(x[1]), reverse=True)
        for net_name, conns in sorted_nets[:50]:
            net_stats.append({
                'design': fname,
                'net_name': net_name,
                'fanout_sinks': len(conns),
                'is_clock': net_name in d['clocks'] or 'clk' in net_name.lower(),
                'is_reset': net_name in d['resets'] or 'rst' in net_name.lower()
            })
    df_nets = pd.DataFrame(net_stats)
    df_nets.to_csv(os.path.join(RESULTS_DIR, "net_statistics.csv"), index=False)
    print(f"Saved {os.path.join(RESULTS_DIR, 'net_statistics.csv')}")

    summary = {
        'date': '2026-09-29',
        'phase': 'Phase 1 - Data Audit',
        'raw_dataset': {
            'lef_file': 'dataset/raw/circuitnet.lef',
            'lef_macros_count': len(lef_macros),
            'lef_layers_count': len(lef_data['layers']),
            'lef_sites_count': len(lef_data['sites']),
            'netlist_archive_netlist_count': raw_archive_audit['netlist_archive_count'],
            'def_archive_count': raw_archive_audit['def_archive_count'],
            'def_parameters_explored': {
                'utilizations': raw_archive_audit['utilization_values'],
                'macro_margins': raw_archive_audit['macro_margins'],
                'placement_efforts': raw_archive_audit['placement_efforts'],
                'designs': raw_archive_audit['unique_designs_in_def']
            }
        },
        'processed_netlists': {
            'count': len(netlist_results),
            'designs': design_stats
        },
        'processed_def_sample': {
            'def_file': os.path.basename(sample_def_path),
            'design_name': def_data['design_name'],
            'dbu_per_micron': dbu,
            'die_dimensions_um': {'width': die_w_um, 'height': die_h_um, 'area_um2': die_area_um2},
            'core_dimensions_um': {'width': core_w_um, 'height': core_h_um, 'area_um2': core_area_um2},
            'calculated_core_utilization': round(core_utilization_calc, 4),
            'target_utilization_in_filename': 0.70,
            'components_count': len(def_comps),
            'nets_count': len(def_nets),
            'pins_count': len(def_data['pins']),
            'rows_count': def_data['rows_count']
        },
        'consistency_analysis': {
            'netlist_vs_def': {
                'netlist_cell_count': riscy_v['total_cells'] if riscy_v else 0,
                'def_component_count': len(def_comps),
                'shared_components': len(common_cells),
                'netlist_only_cells': len(netlist_only_cells),
                'def_only_cells_added_in_pd': len(def_only_cells),
                'def_only_top_cell_types': dict(def_only_types.most_common(10))
            },
            'def_vs_lef': {
                'def_cell_types_count': len(def_cell_types),
                'types_found_in_lef': len(def_types_in_lef),
                'types_missing_in_lef': list(def_types_missing_in_lef)
            },
            'netlist_vs_lef': {
                'netlist_unique_cell_types': len(all_netlist_cell_types),
                'types_found_in_lef': len(netlist_types_in_lef),
                'types_missing_in_lef': len(netlist_types_missing_in_lef),
                'naming_adaptation_required': True,
                'explanation': 'Netlists use Synopsys/TSMC naming like DFCNQ_0100 where suffix encodes drive/speed, whereas CircuitNet LEF uses Innovus/LEF standard cell naming like DFCNQ_x1_0.'
            }
        }
    }

    with open(os.path.join(RESULTS_DIR, "dataset_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved {os.path.join(RESULTS_DIR, 'dataset_summary.json')}")

    print("\nGenerating audit plots...")
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    fig, ax = plt.subplots(figsize=(8, 5))
    designs = [d['design_name'] + f"\n({d['source_file'].replace('.v','')})" for d in design_stats]
    comb_cells = [d['combinational_cells'] for d in design_stats]
    seq_cells = [d['sequential_cells'] for d in design_stats]

    x = np.arange(len(designs))
    width = 0.35
    ax.bar(x - width/2, comb_cells, width, label='Combinational', color='#2b5c8f')
    ax.bar(x + width/2, seq_cells, width, label='Sequential', color='#e06666')
    ax.set_ylabel('Number of Cells', fontsize=12)
    ax.set_title('Cell Count Breakdown by Design (CircuitNet 28nm)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(designs, fontsize=10)
    ax.legend(fontsize=11)
    for i in range(len(designs)):
        ax.text(x[i] - width/2, comb_cells[i] + 500, f"{comb_cells[i]:,}", ha='center', fontsize=9)
        ax.text(x[i] + width/2, seq_cells[i] + 500, f"{seq_cells[i]:,}", ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "cell_count_by_design.png"), dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 5))
    net_counts = [d['total_nets'] for d in design_stats]
    bars = ax.bar(designs, net_counts, color=['#3470a3', '#4d908e', '#f9844a'], width=0.5)
    ax.set_ylabel('Number of Nets', fontsize=12)
    ax.set_title('Net Count by Design (CircuitNet 28nm)', fontsize=14, fontweight='bold')
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 500, f"{int(yval):,}", ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "net_count_by_design.png"), dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 6))
    top_cells = Counter(riscy_v['cell_type_counts']).most_common(15)
    ctypes = [c[0] for c in top_cells][::-1]
    ccounts = [c[1] for c in top_cells][::-1]
    ax.barh(ctypes, ccounts, color='#386b9a')
    ax.set_xlabel('Instance Count', fontsize=12)
    ax.set_title('Top 15 Cell Types in RISCY-a-1-c2 Netlist', fontsize=14, fontweight='bold')
    for i, v in enumerate(ccounts):
        ax.text(v + 50, i, f"{v:,}", va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "cell_type_distribution.png"), dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 5))
    all_fanouts = [len(s) for s in riscy_v['net_connections'].values() if len(s) > 0]
    ax.hist(all_fanouts, bins=np.logspace(0, 4, 30), color='#2a9d8f', edgecolor='black', alpha=0.8)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Fanout (Number of Sinks)', fontsize=12)
    ax.set_ylabel('Frequency (log count)', fontsize=12)
    ax.set_title('Net Fanout Distribution (Log-Log) for RISCY-a-1-c2', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "fanout_distribution.png"), dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 5))
    all_degrees = [len(c['pins']) for c in riscy_v['cell_instances'].values()]
    deg_counts = Counter(all_degrees)
    sorted_deg = sorted(deg_counts.items())
    deg_x = [d[0] for d in sorted_deg]
    deg_y = [d[1] for d in sorted_deg]
    ax.bar(deg_x, deg_y, color='#e76f51', edgecolor='black', width=0.6)
    ax.set_xlabel('Cell Degree (Connected Pins)', fontsize=12)
    ax.set_ylabel('Cell Count', fontsize=12)
    ax.set_title('Cell Degree Distribution for RISCY-a-1-c2', fontsize=14, fontweight='bold')
    for x_val, y_val in zip(deg_x, deg_y):
        ax.text(x_val, y_val + 200, f"{y_val:,}", ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "degree_distribution.png"), dpi=300)
    plt.close()

    print("\nPhase 1 Data Audit executed successfully!")

if __name__ == '__main__':
    main()
