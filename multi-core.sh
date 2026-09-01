#!/bin/bash

# 1. Definimos as 4 configurações
CONFIGS=("hbm4_llc" "hbm4" "ddr5" "ddr5_llc")

# 2. Agrupamos as listas de traces em variáveis para o código ficar limpo
T_COMPATIBLE="traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1536B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/605.mcf_s-472B.champsimtrace.xz traces/620.omnetpp_s-141B.champsimtrace.xz traces/620.omnetpp_s-874B.champsimtrace.xz traces/623.xalancbmk_s-202B.champsimtrace.xz"

T_INCOMPATIBLE="traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/603.bwaves_s-891B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/654.roms_s-293B.champsimtrace.xz traces/628.pop2_s-17B.champsimtrace.xz traces/654.roms_s-523B.champsimtrace.xz"

T_MIX="traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1536B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz"

T_RANDOM="traces/657.xz_s-3167B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz traces/605.mcf_s-472B.champsimtrace.xz traces/641.leela_s-800B.champsimtrace.xz traces/607.cactuBSSN_s-4004B.champsimtrace.xz traces/648.exchange2_s-1227B.champsimtrace.xz traces/600.perlbench_s-1273B.champsimtrace.xz"

# 3. Função que "imprime" os 16 comandos
gerar_comandos() {
  for config in "${CONFIGS[@]}"; do
    # Garante que os diretórios de saída existam antes de rodar, senão o Champsim/Ramulator pode falhar
    mkdir -p "results/8c/${config}/ramulator" "results/8c/${config}/champsim"

    # Monta os comandos atualizando o binário e os caminhos dinamicamente
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/llc-compatible.yaml --json results/8c/${config}/champsim/llc-compatible.json ${T_COMPATIBLE}"
    
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/llc-incompatible.yaml --json results/8c/${config}/champsim/llc-incompatible.json ${T_INCOMPATIBLE}"
    
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/mix.yaml --json results/8c/${config}/champsim/mix.json ${T_MIX}"
    
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/random.yaml --json results/8c/${config}/champsim/random.json ${T_RANDOM}"
  done
}

mkdir -p results/8c/{hbm4,hbm4_llc,ddr5,ddr5_llc}/{champsim,ramulator}

# 4. Passa todos os 16 comandos para o GNU Parallel
gerar_comandos | parallel -j 16 --bar