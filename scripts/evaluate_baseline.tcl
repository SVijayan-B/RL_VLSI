# Evaluation script for baseline placement in OpenROAD
set bench_id $env(BENCH_ID)
set def_path $env(DEF_PATH)
set out_file $env(OUT_FILE)
set seed $env(SEED)

puts "=========================================================="
puts "EVALUATING BENCHMARK: $bench_id"
puts "DEF: $def_path"
puts "SEED: $seed"
puts "=========================================================="

read_lef /workspace/dataset/raw/circuitnet.lef
read_def -continue_on_errors $def_path

set block [ord::get_db_block]
set insts [llength [$block getInsts]]
set nets [llength [$block getNets]]
set bterms [llength [$block getBTerms]]

# Bounding box of core
set dbox [$block getDieArea]
set x0 [$dbox xMin]
set y0 [$dbox yMin]
set x1 [$dbox xMax]
set y1 [$dbox yMax]
set width_um [expr {($x1 - $x0) * 0.0005}]
set height_um [expr {($y1 - $y0) * 0.0005}]

# Run check_placement and detailed_placement (legalize)
set t0 [clock clicks -milliseconds]
set dpl_status "UNKNOWN"
set orig_hpwl "0.0"
set leg_hpwl "0.0"
set avg_disp "0.0"
set max_disp "0.0"

if {[catch {detailed_placement} err]} {
    set dpl_status "FAILED: $err"
} else {
    set dpl_status "SUCCESS"
}
set t1 [clock clicks -milliseconds]
set runtime_sec [expr {($t1 - $t0) / 1000.0}]

# Write JSON result
set fp [open $out_file "w"]
puts $fp "{"
puts $fp "  \"benchmark_id\": \"$bench_id\","
puts $fp "  \"def_path\": \"$def_path\","
puts $fp "  \"seed\": $seed,"
puts $fp "  \"num_cells\": $insts,"
puts $fp "  \"num_nets\": $nets,"
puts $fp "  \"num_pins\": $bterms,"
puts $fp "  \"core_width_um\": $width_um,"
puts $fp "  \"core_height_um\": $height_um,"
puts $fp "  \"detailed_placement_status\": \"$dpl_status\","
puts $fp "  \"runtime_sec\": $runtime_sec"
puts $fp "}"
close $fp

puts "Evaluation complete. Output written to $out_file"
exit
