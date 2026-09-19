#!/bin/bash
# run_selected.sh
# Executa apenas combinações específicas de config->workload (8 cores)

T_COMPATIBLE="traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1536B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/620.omnetpp_s-141B.champsimtrace.xz traces/620.omnetpp_s-874B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz"
T_MIX="traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz"
T_RANDOM="traces/657.xz_s-3167B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz traces/605.mcf_s-472B.champsimtrace.xz traces/641.leela_s-800B.champsimtrace.xz traces/607.cactuBSSN_s-4004B.champsimtrace.xz traces/648.exchange2_s-1227B.champsimtrace.xz traces/600.perlbench_s-1273B.champsimtrace.xz"

mkdir -p results/8c/hbm2/ramulator results/8c/hbm2/champsim
mkdir -p results/8c/hbm1_llc/ramulator results/8c/hbm1_llc/champsim
mkdir -p results/8c/hbm1/ramulator results/8c/hbm1/champsim

gerar_comandos() {
  echo "./bin/champsim_goldencove_8c_hbm2 --warmup-instructions 200000000 --ramulator-stats results/8c/hbm2/ramulator/llc-compatible.yaml --json results/8c/hbm2/champsim/llc-compatible.json ${T_COMPATIBLE}"

  echo "./bin/champsim_goldencove_8c_hbm1_llc --warmup-instructions 200000000 --ramulator-stats results/8c/hbm1_llc/ramulator/llc-compatible.yaml --json results/8c/hbm1_llc/champsim/llc-compatible.json ${T_COMPATIBLE}"

  echo "./bin/champsim_goldencove_8c_hbm1 --warmup-instructions 200000000 --ramulator-stats results/8c/hbm1/ramulator/llc-compatible.yaml --json results/8c/hbm1/champsim/llc-compatible.json ${T_COMPATIBLE}"
  echo "./bin/champsim_goldencove_8c_hbm1 --warmup-instructions 200000000 --ramulator-stats results/8c/hbm1/ramulator/random.yaml --json results/8c/hbm1/champsim/random.json ${T_RANDOM}"
  echo "./bin/champsim_goldencove_8c_hbm1 --warmup-instructions 200000000 --ramulator-stats results/8c/hbm1/ramulator/mix.yaml --json results/8c/hbm1/champsim/mix.json ${T_MIX}"
}

gerar_comandos | parallel -j 5 --bar --joblog execucao_champsim_selected.log
