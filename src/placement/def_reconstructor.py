import os
import sys
import numpy as np

class DEFReconstructor:
    """
    Constructs an authentic, OpenROAD-compliant standard cell physical layout DEF
    from CircuitNet canonical graph netlist + GCell placement data.
    """
    def __init__(self, dbu_per_micron: int = 2000):
        self.dbu = dbu_per_micron

    def generate_def(
        self,
        design_id: str,
        die_w_dbu: int,
        die_h_dbu: int,
        num_rows: int,
        components: list, # [(inst_name, cell_type, x_dbu, y_dbu, orient, status)]
        nets: list,       # [(net_name, [(inst_name, pin_name), ...])]
        pins: list,       # [(pin_name, x_dbu, y_dbu, dir, layer)]
        out_def_path: str
    ):
        with open(out_def_path, "w") as f:
            f.write("VERSION 5.8 ;\n")
            f.write('DIVIDERCHAR "/" ;\n')
            f.write('BUSBITCHARS "[]" ;\n')
            f.write(f"DESIGN {design_id} ;\n")
            f.write(f"UNITS DISTANCE MICRONS {self.dbu} ;\n\n")

            # DIEAREA
            f.write(f"DIEAREA ( 0 0 ) ( {die_w_dbu} {die_h_dbu} ) ;\n\n")

            # Standard cell ROWs
            site_h = 2100  # 1.05um * 2000
            site_w = 420   # 0.21um * 2000
            num_sites = die_w_dbu // site_w
            for r in range(num_rows):
                ry = r * site_h
                rorient = "FS" if (r % 2 == 1) else "N"
                f.write(f"ROW ROW_{r} CoreSite 0 {ry} {rorient} DO {num_sites} BY 1 STEP {site_w} 0 ;\n")
            f.write("\n")

            # COMPONENTS
            f.write(f"COMPONENTS {len(components)} ;\n")
            for inst, master, x, y, orient, status in components:
                f.write(f"- {inst} {master} + {status} ( {x} {y} ) {orient} ;\n")
            f.write("END COMPONENTS\n\n")

            # PINS
            f.write(f"PINS {len(pins)} ;\n")
            for pname, px, py, pdir, layer in pins:
                f.write(f"- {pname} + NET {pname} + DIRECTION {pdir} + USE SIGNAL\n")
                f.write(f"  + LAYER {layer} ( -140 -140 ) ( 140 140 )\n")
                f.write(f"  + PLACED ( {px} {py} ) N ;\n")
            f.write("END PINS\n\n")

            # NETS
            f.write(f"NETS {len(nets)} ;\n")
            for net_name, conns in nets:
                f.write(f"- {net_name}\n")
                # Format 4 connections per line
                conn_strs = [f"( {inst} {pin} )" for inst, pin in conns]
                for i in range(0, len(conn_strs), 4):
                    f.write("  " + " ".join(conn_strs[i:i+4]) + "\n")
                f.write("  ;\n")
            f.write("END NETS\n\n")

            f.write("END DESIGN\n")
