
read_lef /home/b_siddarth_vijayan/CircuitNet_28nm/dataset/raw/circuitnet.lef
read_def /home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_11c/def_reconstruction/RISCY-a-2-c2.def

# Measure initial HPWL
set init_hpwl [detailed_placement_hpwl]
puts "\[OPENROAD_SMOKE\] INITIAL_HPWL: $init_hpwl"

# Run OpenROAD DPL legalization
detailed_placement
set post_hpwl [detailed_placement_hpwl]
puts "\[OPENROAD_SMOKE\] POST_DPL_HPWL: $post_hpwl"

write_def /home/b_siddarth_vijayan/CircuitNet_28nm/results/phase_11c/openroad_validation/RISCY-a-2-c2_legalized.def
exit
