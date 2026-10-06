import os
import numpy as np
from typing import List, Tuple, Dict, Any
from src.placement.lef_site_model import LEFSiteModel

class CoordinateMapper:
    def __init__(self, lef_model: LEFSiteModel = None, dbu_per_micron: int = 2000):
        self.dbu = dbu_per_micron
        self.lef_model = lef_model if lef_model else LEFSiteModel()
        self.site_w_dbu = self.lef_model.site_w_dbu
        self.site_h_dbu = self.lef_model.site_h_dbu

    def reconstruct_layout(
        self,
        design_id: str,
        cell_names: List[str],
        cell_types: List[str],
        cell_features: np.ndarray,
        placement_dict: Dict[str, List[int]],
        die_w_dbu: int,
        die_h_dbu: int,
        num_rows: int
    ) -> Tuple[List[Tuple[str, str, int, int, str, str]], List[Dict[str, Any]]]:
        num_sites_per_row = die_w_dbu // self.site_w_dbu
        row_intervals = [[[0, num_sites_per_row]] for _ in range(num_rows)]
        row_free_sites = [num_sites_per_row for _ in range(num_rows)]

        placed_cells = []
        missing_cells = []

        for cname, ctype in zip(cell_names, cell_types):
            is_macro = self.lef_model.is_macro(ctype)
            w_dbu, h_dbu = self.lef_model.get_macro_size_dbu(ctype)
            if cname in placement_dict:
                gbox = placement_dict[cname]
                placed_cells.append((cname, ctype, is_macro, w_dbu, h_dbu, gbox))
            else:
                missing_cells.append((cname, ctype, is_macro, w_dbu, h_dbu))

        components = []
        macros = [c for c in placed_cells if c[2]]
        std_placed = [c for c in placed_cells if not c[2]]
        missing_macros = [c for c in missing_cells if c[2]]
        missing_std = [c for c in missing_cells if not c[2]]

        def block_out(r1, r2, s1, s2):
            for r in range(max(0, r1), min(num_rows, r2)):
                new_ints = []
                freed = 0
                for start, end in row_intervals[r]:
                    if end <= s1 or start >= s2:
                        new_ints.append([start, end])
                        freed += (end - start)
                    else:
                        if start < s1:
                            new_ints.append([start, s1])
                            freed += (s1 - start)
                        if end > s2:
                            new_ints.append([s2, end])
                            freed += (end - s2)
                row_intervals[r] = new_ints
                row_free_sites[r] = freed

        macro_boxes = []

        def place_macro_no_overlap(w_dbu, h_dbu, ideal_site, ideal_row):
            max_site = max(0, (die_w_dbu - w_dbu) // self.site_w_dbu)
            max_row = max(0, (die_h_dbu - h_dbu) // self.site_h_dbu)
            
            ideal_site = min(max(ideal_site, 0), max_site)
            ideal_row = min(max(ideal_row, 0), max_row)
            
            halo_x = 2 * self.site_w_dbu
            halo_y = 1 * self.site_h_dbu
            
            for radius in range(500):
                for dr in range(-radius, radius + 1):
                    if abs(dr) == radius:
                        ds_range = range(-radius, radius + 1)
                    else:
                        ds_range = [-radius, radius] if radius > 0 else [0]
                    for ds in ds_range:
                        cand_s = ideal_site + ds
                        cand_r = ideal_row + dr
                        
                        if cand_s < 0 or cand_s > max_site or cand_r < 0 or cand_r > max_row:
                            continue
                            
                        clx = cand_s * self.site_w_dbu
                        cly = cand_r * self.site_h_dbu
                        crx = clx + w_dbu
                        cry = cly + h_dbu
                        
                        overlap = False
                        for (mx1, my1, mx2, my2) in macro_boxes:
                            if not (crx + halo_x <= mx1 or clx - halo_x >= mx2 or cry + halo_y <= my1 or cly - halo_y >= my2):
                                overlap = True
                                break
                        
                        if not overlap:
                            macro_boxes.append((clx, cly, crx, cry))
                            return cand_s, cand_r
            
            clx = ideal_site * self.site_w_dbu
            cly = ideal_row * self.site_h_dbu
            macro_boxes.append((clx, cly, clx + w_dbu, cly + h_dbu))
            return ideal_site, ideal_row

        for cname, ctype, is_macro, w_dbu, h_dbu, gbox in macros:
            gx1, gy1 = gbox[0], gbox[1]
            raw_x = (gx1 / 256.0) * die_w_dbu
            raw_y = (gy1 / 256.0) * die_h_dbu
            
            ideal_site = int(round(raw_x / self.site_w_dbu))
            ideal_row = int(round(raw_y / self.site_h_dbu))
            
            site_idx, row_idx = place_macro_no_overlap(w_dbu, h_dbu, ideal_site, ideal_row)
            
            lx = site_idx * self.site_w_dbu
            ly = row_idx * self.site_h_dbu
            components.append((cname, ctype, lx, ly, "N", "PLACED"))
            
            sites_span = int(np.ceil(w_dbu / self.site_w_dbu))
            rows_span = int(np.ceil(h_dbu / self.site_h_dbu))
            block_out(row_idx, row_idx + rows_span, site_idx, site_idx + sites_span)

        missing_macros.sort(key=lambda x: x[0])
        for i, (cname, ctype, is_macro, w_dbu, h_dbu) in enumerate(missing_macros):
            max_macro_site = max(0, (die_w_dbu - w_dbu) // self.site_w_dbu)
            max_macro_row = max(0, (die_h_dbu - h_dbu) // self.site_h_dbu)
            
            ideal_site = ((i + 1) * 73) % (max_macro_site + 1)
            ideal_row = int(((i + 1) / max(len(missing_macros), 1)) * max_macro_row) % (max_macro_row + 1)
            
            site_idx, row_idx = place_macro_no_overlap(w_dbu, h_dbu, ideal_site, ideal_row)
            
            lx = site_idx * self.site_w_dbu
            ly = row_idx * self.site_h_dbu
            components.append((cname, ctype, lx, ly, "N", "PLACED"))
            
            sites_span = int(np.ceil(w_dbu / self.site_w_dbu))
            rows_span = int(np.ceil(h_dbu / self.site_h_dbu))
            block_out(row_idx, row_idx + rows_span, site_idx, site_idx + sites_span)

        def allocate_std_cell(target_row, preferred_site, w_dbu):
            sites_needed = max(int(np.ceil(w_dbu / self.site_w_dbu)), 1)
            row_candidates = [target_row]
            for delta in range(1, max(target_row, num_rows - target_row) + 1):
                if target_row + delta < num_rows:
                    row_candidates.append(target_row + delta)
                if target_row - delta >= 0:
                    row_candidates.append(target_row - delta)

            for r in row_candidates:
                if row_free_sites[r] < sites_needed:
                    continue
                ints = row_intervals[r]
                best_idx = -1
                best_start = -1
                min_dist = 1e9

                for idx, (st, en) in enumerate(ints):
                    if en - st >= sites_needed:
                        cand_pos = min(max(preferred_site, st), en - sites_needed)
                        dist = abs(cand_pos - preferred_site)
                        if dist < min_dist:
                            min_dist = dist
                            best_idx = idx
                            best_start = cand_pos
                            if dist == 0:
                                break
                
                if best_idx != -1:
                    s = best_start
                    st, en = ints[best_idx]
                    if s == st and s + sites_needed == en:
                        ints.pop(best_idx)
                    elif s == st:
                        ints[best_idx] = [s + sites_needed, en]
                    elif s + sites_needed == en:
                        ints[best_idx] = [st, s]
                    else:
                        ints[best_idx] = [st, s]
                        ints.insert(best_idx + 1, [s + sites_needed, en])
                    
                    row_free_sites[r] -= sites_needed
                    x = s * self.site_w_dbu
                    y = r * self.site_h_dbu
                    orient = "FS" if (r % 2 == 1) else "N"
                    return x, y, orient
            return 0, 0, "N"

        gcell_bins = {}
        for cname, ctype, is_macro, w_dbu, h_dbu, gbox in std_placed:
            key = (gbox[0], gbox[1])
            if key not in gcell_bins:
                gcell_bins[key] = []
            gcell_bins[key].append((cname, ctype, w_dbu, h_dbu))

        sorted_bin_keys = sorted(gcell_bins.keys(), key=lambda k: (k[1], k[0]))
        for bin_key in sorted_bin_keys:
            gx, gy = bin_key
            cells_in_bin = gcell_bins[bin_key]
            cells_in_bin.sort(key=lambda item: item[0])
            
            target_row = min(max(int(round((gy / 256.0) * num_rows)), 0), num_rows - 1)
            preferred_site = min(max(int(round((gx / 256.0) * num_sites_per_row)), 0), num_sites_per_row - 1)
            
            for cname, ctype, w_dbu, h_dbu in cells_in_bin:
                x, y, orient = allocate_std_cell(target_row, preferred_site, w_dbu)
                components.append((cname, ctype, x, y, orient, "PLACED"))

        missing_std.sort(key=lambda item: item[0])
        total_missing = len(missing_std)
        missing_records = []
        for i, (cname, ctype, is_macro, w_dbu, h_dbu) in enumerate(missing_std):
            t_row = int((i / max(total_missing, 1)) * num_rows) % num_rows
            pref_site = (i * 37) % num_sites_per_row
            x, y, orient = allocate_std_cell(t_row, pref_site, w_dbu)
            components.append((cname, ctype, x, y, orient, "PLACED"))

        return components, missing_records
