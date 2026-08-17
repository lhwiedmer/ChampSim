mkdir -p traces/
awk 'NF{print $NF}' download_traces.txt | parallel --bar -j 4 "curl -o traces/{} -C - --retry 3 https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/{}"

cd ../
ls traces/*.champsimtrace.xz | parallel --bar -j 49 './bin/champsim_goldencove_1c_hbm_llc --warmup-instructions 200000000 --simulation-instructions 300000000 --ramulator-stats results/ramulator/{/.}.yaml --json results/champsim/{/.}.json {}'