#mkdir -p traces/
#awk 'NF{print $NF}' download_traces.txt | parallel --bar -j 4 "curl -o traces/{} -C - --retry 3 https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/{}"

#cd ../

mkdir -p results/ramulator results/champsim
ls traces/ | parallel --bar -j 32 './bin/champsim_goldencove_1c_ddr5_llc --warmup-instructions 200000000 --ramulator-stats results/ramulator/{/.}.yaml --json results/champsim/{/.}.json traces/{}'