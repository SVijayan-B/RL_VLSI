"""
Phase 6 Task 1: Audit PDN and Power Delivery Structures in CircuitNet DEF files.
Inspects SPECIALNETS, VDD/VSS naming, PDN routing/stripes, layers, and p1-p8 variation.
Generates results/phase_06/pdn_audit.csv and results/phase_06/pdn_audit.json.
"""

import os
import re
import csv
import json
from pathlib import Path

root = Path('/home/b_siddarth_vijayan/CircuitNet_28nm')
def_dir = root / 'dataset/processed/DEF_decompressed/DEF'
out_csv = root / 'results/phase_06/pdn_audit.csv'
out_json = root / 'results/phase_06/pdn_audit.json'

# Let's inspect representative DEFs across different p-settings (p1 through p8)
# e.g., 1-RISCY-a-1-c2-u0.7-m1-p1-f0.def, 10-RISCY-a-1-c2-u0.7-m2-p2-f0.def, etc.
sample_defs = sorted(list(def_dir.glob('*-RISCY-a-1-c2-u0.7-m1-p*-f0.def')))
if len(sample_defs) < 8:
    # grab any p1-p8 matching
    sample_defs = sorted(list(def_dir.glob('*-RISCY-a-1-c2-*-p*-f*.def')))[:16]

print(f"Auditing {len(sample_defs)} sample DEFs for PDN structures...")

audit_records = []

for def_path in sample_defs:
    m = re.search(r'-p([0-9]+)-', def_path.name)
    p_val = f"p{m.group(1)}" if m else "unknown"
    
    has_specialnets = False
    specialnets_count = 0
    power_nets = []
    ground_nets = []
    specialnet_names = []
    layers_used = set()
    stripe_count = 0
    via_count = 0
    
    in_specialnets = False
    current_snet = None
    
    with open(def_path, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line_s = line.strip()
            if line_s.startswith('SPECIALNETS'):
                has_specialnets = True
                parts = line_s.split()
                if len(parts) >= 2:
                    specialnets_count = int(parts[1])
                in_specialnets = True
            elif line_s.startswith('END SPECIALNETS'):
                in_specialnets = False
                current_snet = None
            elif in_specialnets:
                if line_s.startswith('- '):
                    parts = line_s.split()
                    current_snet = parts[1]
                    specialnet_names.append(current_snet)
                    if 'VDD' in current_snet.upper() or 'VCC' in current_snet.upper() or 'POWER' in current_snet.upper():
                        power_nets.append(current_snet)
                    if 'VSS' in current_snet.upper() or 'GND' in current_snet.upper() or 'GROUND' in current_snet.upper():
                        ground_nets.append(current_snet)
                elif current_snet:
                    # check for ROUTED, SHAPE, STRIPE, FOLLOWPIN
                    if 'ROUTED' in line_s or 'STRIPE' in line_s or 'FOLLOWPIN' in line_s:
                        stripe_count += 1
                    # check for layer names
                    tokens = line_s.split()
                    for idx, tok in enumerate(tokens):
                        if tok in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'AP', 'RV']:
                            layers_used.add(tok)
                        if 'VIA' in tok:
                            via_count += 1
                            
    audit_records.append({
        'def_file': def_path.name,
        'p_setting': p_val,
        'has_specialnets': has_specialnets,
        'specialnets_count': specialnets_count,
        'power_net_names': ';'.join(power_nets),
        'ground_net_names': ';'.join(ground_nets),
        'all_specialnet_names': ';'.join(specialnet_names),
        'pdn_layers': ';'.join(sorted(list(layers_used))),
        'stripe_records_count': stripe_count,
        'via_records_count': via_count,
        'sufficient_for_geometric_pdn': bool(specialnets_count > 0 and len(layers_used) > 0)
    })

# Save to CSV
out_csv.parent.mkdir(parents=True, exist_ok=True)
with open(out_csv, 'w', newline='') as fp:
    writer = csv.DictWriter(fp, fieldnames=list(audit_records[0].keys()))
    writer.writeheader()
    for rec in audit_records:
        writer.writerow(rec)

# Save to JSON
with open(out_json, 'w') as fp:
    json.dump(audit_records, fp, indent=2)

print(f"PDN audit complete. Wrote {out_csv} and {out_json}")
for r in audit_records[:4]:
    print(f"  {r['def_file']} ({r['p_setting']}): SpecialNets={r['specialnets_count']} | Layers={r['pdn_layers']} | Stripes={r['stripe_records_count']}")
