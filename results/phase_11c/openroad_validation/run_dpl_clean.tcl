
read_lef /home/b_siddarth_vijayan/CircuitNet_28nm/dataset/raw/circuitnet.lef
read_def -continue_on_errors /home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_11c/def_reconstruction/RISCY-a-2-c2.def

# Detailed placement with default settings
detailed_placement -max_displacement 10 -site_search_window 10 -row_search_window 2

write_def /home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_11c/openroad_validation/RISCY-a-2-c2_legalized.def
exit
