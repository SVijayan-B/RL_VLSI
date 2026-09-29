import re
from collections import Counter

lef_path = 'dataset/raw/circuitnet.lef'

layers = []
sites = []
macros = {}

current_macro = None
current_site = None
current_layer = None

with open(lef_path, 'r') as f:
    for line in f:
        line_s = line.strip()
        if not line_s or line_s.startswith('#'):
            continue
        
        # Site
        m_site = re.match(r'^SITE\s+(\S+)', line_s)
        if m_site:
            current_site = {'name': m_site.group(1)}
            continue
        if current_site:
            m_size = re.match(r'SIZE\s+([\d\.]+)\s+BY\s+([\d\.]+)', line_s)
            if m_size:
                current_site['width'] = float(m_size.group(1))
                current_site['height'] = float(m_size.group(2))
            if re.match(r'^END\s+' + re.escape(current_site['name']), line_s):
                sites.append(current_site)
                current_site = None
            continue
            
        # Layer
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
                layers.append(current_layer)
                current_layer = None
            continue

        # Macro
        m_macro = re.match(r'^MACRO\s+(\S+)', line_s)
        if m_macro:
            current_macro = {'name': m_macro.group(1), 'pins': set()}
            continue
        if current_macro:
            m_class = re.match(r'CLASS\s+(\S+)', line_s)
            if m_class:
                current_macro['class'] = m_class.group(1).rstrip(';')
            m_size = re.match(r'SIZE\s+([\d\.]+)\s+BY\s+([\d\.]+)', line_s)
            if m_size:
                current_macro['width'] = float(m_size.group(1))
                current_macro['height'] = float(m_size.group(2))
            m_pin = re.match(r'PIN\s+(\S+)', line_s)
            if m_pin:
                current_macro['pins'].add(m_pin.group(1))
            if re.match(r'^END\s+' + re.escape(current_macro['name']), line_s):
                macros[current_macro['name']] = current_macro
                current_macro = None
            continue

print(f'LEF Summary for {lef_path}:')
print(f'Total Layers: {len(layers)}')
for l in layers:
    print(f"  Layer {l.get('name')}: Type={l.get('type')}, Dir={l.get('direction', 'N/A')}, Pitch={l.get('pitch', 'N/A')}, Width={l.get('width', 'N/A')}")

print(f'\nTotal Sites: {len(sites)}')
for s in sites:
    print(f"  Site {s['name']}: {s.get('width')} x {s.get('height')}")

print(f'\nTotal Macros (Cells/Blocks): {len(macros)}')
classes = Counter(m.get('class', 'UNKNOWN') for m in macros.values())
for c, count in classes.most_common():
    print(f'  Class {c}: {count}')

sample_macros = sorted(macros.keys())[:15]
print(f'\nSample Macro Names (first 15):')
for m in sample_macros:
    print(f"  {m}: {macros[m].get('width')}x{macros[m].get('height')}, Class={macros[m].get('class')}, Pins={len(macros[m]['pins'])}")

block_macros = [m for m in macros.values() if m.get('class') == 'BLOCK' or (m.get('width', 0) > 10 and m.get('height', 0) > 10)]
print(f'\nLarge / BLOCK Macros ({len(block_macros)}):')
for bm in block_macros:
    print(f"  {bm['name']}: {bm.get('width')} x {bm.get('height')}, Pins={len(bm['pins'])}")
