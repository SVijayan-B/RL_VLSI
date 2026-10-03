# Test baseline placement feasibility in OpenROAD using CircuitNet N28
puts "=== Testing Placement Feasibility on CircuitNet N28 ==="

read_lef /workspace/dataset/raw/circuitnet.lef
read_def -continue_on_errors /workspace/dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def

puts "--- Probing legalize_placement ---"
if {[catch {legalize_placement} err_leg]} {
    puts "legalize_placement result: $err_leg"
} else {
    puts "legalize_placement SUCCESS"
}

puts "--- Probing check_placement ---"
if {[catch {check_placement} err_chk]} {
    puts "check_placement result: $err_chk"
} else {
    puts "check_placement SUCCESS"
}

puts "--- Probing global_placement ---"
if {[catch {global_placement -density 0.7} err_gpl]} {
    puts "global_placement result: $err_gpl"
} else {
    puts "global_placement SUCCESS"
}

puts "--- Probing detailed_placement ---"
if {[catch {detailed_placement} err_dpl]} {
    puts "detailed_placement result: $err_dpl"
} else {
    puts "detailed_placement SUCCESS"
}

exit
