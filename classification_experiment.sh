#mkdir -p traces/
#awk 'NF{print $NF}' download_traces.txt | parallel --bar -j 4 "curl -o traces/{} -C - --retry 3 https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/{}"

#cd ../

#mkdir -p results/1c/ddr5/champsim results/1c/ddr5/ramulator

mkdir -p results/1c/{ddr5,ddr5_llc,hbm4,hbm4_llc}/{champsim,ramulator}
#ls traces/ | parallel --bar -j 32 './bin/champsim_goldencove_1c_ddr5_llc_prefetch
# --warmup-instructions 200000000 --ramulator-stats results/classification_prefetch/ramulator/{/.}.yaml --json results/classification_prefetch/champsim/{/.}.json traces/{}'

parallel --bar -j 40 \
  './bin/champsim_goldencove_1c_{1} \
  --warmup-instructions 200000000 \
  --ramulator-stats results/1c/{1}/ramulator/{2/.}.yaml \
  --json results/1c/{1}/champsim/{2/.}.json \
  {2}' \
  ::: ddr5 ddr5_llc hbm4 hbm4_llc \
  ::: traces/*