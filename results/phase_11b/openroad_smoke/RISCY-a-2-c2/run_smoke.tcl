
read_lef /home/b_siddarth_vijayan/CircuitNet_28nm/dataset/raw/circuitnet.lef
read_verilog /home/b_siddarth_vijayan/CircuitNet_28nm/dataset/processed/netlists/netlist/RISCY-a-2-c2.v
link_design pulpino_top
initialize_floorplan -site FreePDK45_38x28_100/unit -die_area "0 0 1170 1170" -core_area "20 20 1150 1150"
puts "\[SMOKE_TEST_PASS\] linked design successfully"
puts "\[SMOKE_TEST_PASS\] instances: [llength [get_cells *]]"
puts "\[SMOKE_TEST_PASS\] nets: [llength [get_nets *]]"
exit
