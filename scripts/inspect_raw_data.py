#!/usr/bin/env python3
import os
import glob

def main():
    netlists = sorted(glob.glob('dataset/processed/netlists/netlist/*.v'))
    print(f'Found {len(netlists)} processed netlists:')
    for f in netlists:
        size = os.path.getsize(f)
        with open(f, 'r') as fp:
            first_line = fp.readline().strip()
        print(f'  {os.path.basename(f)}: {size / (1024*1024):.2f} MB, header: {first_line}')

    defs = sorted(glob.glob('dataset/processed/sample_1/DEF/*.def'))
    print(f'\nFound {len(defs)} processed DEFs:')
    for f in defs:
        size = os.path.getsize(f)
        print(f'  {os.path.basename(f)}: {size / (1024*1024):.2f} MB')

    lefs = sorted(glob.glob('dataset/raw/*.lef'))
    print(f'\nFound {len(lefs)} raw LEFs:')
    for f in lefs:
        size = os.path.getsize(f)
        print(f'  {os.path.basename(f)}: {size / (1024*1024):.2f} MB')

if __name__ == '__main__':
    main()
