
set cmds [info commands]
puts "=== GLOBAL PLACEMENT COMMANDS ==="
foreach c $cmds {
    if {[string match "*global_placement*" $c] || [string match "*gpl*" $c]} {
        puts "CMD: $c"
    }
}
puts "=== DETAILED PLACEMENT COMMANDS ==="
foreach c $cmds {
    if {[string match "*detailed_placement*" $c] || [string match "*dpl*" $c] || [string match "*legal*" $c]} {
        puts "CMD: $c"
    }
}
puts "=== HELP global_placement ==="
catch {help global_placement} msg
puts $msg

puts "=== HELP detailed_placement ==="
catch {help detailed_placement} msg
puts $msg

puts "=== HELP improve_placement ==="
catch {help improve_placement} msg
puts $msg

puts "=== HELP optimize_placement ==="
catch {help optimize_placement} msg
puts $msg

puts "=== HELP check_placement ==="
catch {help check_placement} msg
puts $msg
exit
