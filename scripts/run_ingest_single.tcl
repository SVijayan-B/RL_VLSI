# Read arguments from environment variables
set mode $env(INGEST_MODE)
set bench_id $env(INGEST_BENCH_ID)
set def_path $env(INGEST_DEF_PATH)

read_lef /workspace/dataset/raw/circuitnet.lef

if {$mode == "normal"} {
    puts "RUNNING NORMAL READ_DEF for $bench_id"
    if {[catch {read_def $def_path} err]} {
        puts "STATUS: FAILED"
        puts "ERROR: $err"
        exit 1
    } else {
        puts "STATUS: PASSED"
        exit 0
    }
} elseif {$mode == "continue"} {
    puts "RUNNING READ_DEF -CONTINUE_ON_ERRORS for $bench_id"
    if {[catch {read_def -continue_on_errors $def_path} err]} {
        puts "STATUS: FAILED"
        puts "ERROR: $err"
        exit 1
    } else {
        set block [ord::get_db_block]
        set insts [llength [$block getInsts]]
        set nets [llength [$block getNets]]
        set bterms [llength [$block getBTerms]]
        puts "STATUS: PASSED"
        puts "RETAINED: insts=$insts nets=$nets bterms=$bterms"
        exit 0
    }
}
