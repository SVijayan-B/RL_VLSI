puts "=== Test 1: read_def -continue_on_errors ==="
read_lef /workspace/dataset/raw/circuitnet.lef
if {[catch {read_def -continue_on_errors /workspace/dataset/processed/DEF_decompressed/DEF/441-RISCY-a-1-c5-u0.8-m3-p2-f1.def} err]} {
    puts "read_def error: $err"
} else {
    puts "SUCCESS: read_def succeeded with -continue_on_errors!"
    set block [ord::get_db_block]
    puts "Num insts: [llength [$block getInsts]]"
    puts "Num nets: [llength [$block getNets]]"
    puts "Num bterms: [llength [$block getBTerms]]"
}

puts "=== Test 2: Checking OpenSTA availability without .lib ==="
if {[catch {report_checks} err]} {
    puts "OpenSTA report_checks error: $err"
}
exit
