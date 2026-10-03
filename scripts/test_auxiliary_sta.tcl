puts "=== OpenSTA Auxiliary Technology Smoke Test (Nangate45) ==="

set nangate_lib "/OpenROAD-flow-scripts/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib"
set nangate_lef "/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef"

read_liberty $nangate_lib
read_lef $nangate_lef
puts "Successfully read Nangate45 liberty and LEF!"
exit
