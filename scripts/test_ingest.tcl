# Experiment script to test OpenROAD LEF/DEF ingestion across benchmarks

proc test_ingestion {bench_id def_path log_prefix} {
    puts "=========================================================="
    puts "BENCHMARK: $bench_id"
    puts "DEF: $def_path"
    puts "=========================================================="
    
    # 1. Normal read_def
    puts "--- Test A: Normal read_def ---"
    set db [ord::get_db]
    if {$db != ""} {
        # clear db
    }
    
    # Run in a clean sub-block or catch
    read_lef /workspace/dataset/raw/circuitnet.lef
    set normal_status "UNKNOWN"
    set normal_error "None"
    
    if {[catch {read_def $def_path} err]} {
        set normal_status "FAILED"
        set normal_error $err
        puts "Normal read_def failed as expected with error: $err"
    } else {
        set normal_status "PASSED"
        puts "Normal read_def succeeded!"
    }
    
    # 2. read_def -continue_on_errors
    puts "--- Test B: read_def -continue_on_errors ---"
    set cont_status "UNKNOWN"
    set cont_error "None"
    set num_insts 0
    set num_nets 0
    set num_bterms 0
    
    if {[catch {read_def -continue_on_errors $def_path} err2]} {
        set cont_status "FAILED"
        set cont_error $err2
        puts "read_def -continue_on_errors failed with: $err2"
    } else {
        set cont_status "PASSED"
        set block [ord::get_db_block]
        set num_insts [llength [$block getInsts]]
        set num_nets [llength [$block getNets]]
        set num_bterms [llength [$block getBTerms]]
        puts "SUCCESS: read_def -continue_on_errors succeeded!"
        puts "Retained components: $num_insts, nets: $num_nets, pins: $num_bterms"
    }
    
    # Output record to a summary file
    set fp [open "/workspace/results/phase_04/ingestion/${bench_id}_result.txt" "w"]
    puts $fp "benchmark_id: $bench_id"
    puts $fp "def_path: $def_path"
    puts $fp "normal_status: $normal_status"
    puts $fp "normal_error: $normal_error"
    puts $fp "continue_status: $cont_status"
    puts $fp "continue_error: $cont_error"
    puts $fp "num_insts: $num_insts"
    puts $fp "num_nets: $num_nets"
    puts $fp "num_bterms: $num_bterms"
    close $fp
}

test_ingestion "BENCH_01_RISCY_C2_U70" "/workspace/dataset/processed/DEF_decompressed/DEF/1-RISCY-a-1-c2-u0.7-m1-p1-f0.def" "bench1"
exit
