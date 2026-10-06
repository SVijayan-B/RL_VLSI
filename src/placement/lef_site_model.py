"""
LEF Site & Geometry Model for CircuitNet N28.
Parses dataset/raw/circuitnet.lef to extract site definitions, macro sizes,
and standard cell physical geometries.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional

class LEFSiteModel:
    def __init__(self, lef_path: str = "/home/b_siddarth_vijayan/CircuitNet_28nm/dataset/raw/circuitnet.lef"):
        self.lef_path = Path(lef_path)
        self.dbu_per_micron = 2000
        self.site_name = "CoreSite"
        self.site_w_um = 0.210
        self.site_h_um = 1.050
        self.site_w_dbu = int(round(self.site_w_um * self.dbu_per_micron))  # 420
        self.site_h_dbu = int(round(self.site_h_um * self.dbu_per_micron))  # 2100
        self.macro_sizes_um: Dict[str, Tuple[float, float]] = {}
        self.macro_sizes_dbu: Dict[str, Tuple[int, int]] = {}
        self.macro_classes: Dict[str, str] = {}
        self._parse_lef()

    def _parse_lef(self):
        if not self.lef_path.exists():
            raise FileNotFoundError(f"LEF file not found: {self.lef_path}")

        current_macro = None
        current_class = "CORE"
        with open(self.lef_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_s = line.strip()
                if line_s.startswith("UNITS"):
                    continue
                elif line_s.startswith("SITE") and "CoreSite" in line_s:
                    # SITE CoreSite ...
                    pass
                elif line_s.startswith("MACRO"):
                    parts = line_s.split()
                    if len(parts) >= 2:
                        current_macro = parts[1]
                        current_class = "CORE"
                elif line_s.startswith("CLASS") and current_macro:
                    parts = line_s.split()
                    if len(parts) >= 2:
                        current_class = parts[1]
                elif line_s.startswith("SIZE") and current_macro:
                    parts = line_s.split()
                    if len(parts) >= 4 and parts[2] == "BY":
                        w = float(parts[1])
                        h = float(parts[3])
                        self.macro_sizes_um[current_macro] = (w, h)
                        w_dbu = int(round(w * self.dbu_per_micron))
                        h_dbu = int(round(h * self.dbu_per_micron))
                        self.macro_sizes_dbu[current_macro] = (w_dbu, h_dbu)
                        self.macro_classes[current_macro] = current_class
                elif line_s.startswith("END") and current_macro:
                    parts = line_s.split()
                    if len(parts) >= 2 and parts[1] == current_macro:
                        current_macro = None

    def get_macro_size_dbu(self, master_name: str) -> Tuple[int, int]:
        if master_name in self.macro_sizes_dbu:
            return self.macro_sizes_dbu[master_name]
        # Default standard cell size fallback (1 site wide, 1 row high)
        return (self.site_w_dbu, self.site_h_dbu)

    def is_macro(self, master_name: str) -> bool:
        cls = self.macro_classes.get(master_name, "CORE")
        return cls in ("BLOCK", "RING", "PAD")
