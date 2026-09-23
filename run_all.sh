#!/bin/bash
# run_all.sh

# Lista centralizada definindo os sufixos binários a serem executados
#CONFIGS=("ddr5" "ddr5_llc" "hbm1" "hbm1_llc" "hbm2" "hbm2_llc" "hbm3" "hbm3_llc" "hbm4" "hbm4_llc")
#
#T_COMPATIBLE="traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1536B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/620.omnetpp_s-141B.champsimtrace.xz traces/620.omnetpp_s-874B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz"
#T_INCOMPATIBLE="traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/603.bwaves_s-891B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/654.roms_s-293B.champsimtrace.xz traces/649.fotonik3d_s-7084B.champsimtrace.xz traces/605.mcf_s-484B.champsimtrace.xz"
#T_MIX="traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz"
#T_RANDOM="traces/657.xz_s-3167B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz traces/605.mcf_s-472B.champsimtrace.xz traces/641.leela_s-800B.champsimtrace.xz traces/607.cactuBSSN_s-4004B.champsimtrace.xz traces/648.exchange2_s-1227B.champsimtrace.xz traces/600.perlbench_s-1273B.champsimtrace.xz"
#
## Garante que todo o esqueleto de diretórios exista de antemão
#for config in "${CONFIGS[@]}"; do
#  mkdir -p "results/1c/${config}/ramulator" "results/1c/${config}/champsim"
#  mkdir -p "results/8c/${config}/ramulator" "results/8c/${config}/champsim"
#done
#
#gerar_comandos() {
#  for config in "${CONFIGS[@]}"; do
#    
#    # Injeta os comandos do experimento Multi-Core
#    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/llc-compatible.yaml --json results/8c/${config}/champsim/llc-compatible.json ${T_COMPATIBLE}"
#    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/llc-incompatible.yaml --json results/8c/${config}/champsim/llc-incompatible.json ${T_INCOMPATIBLE}"
#    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/mix.yaml --json results/8c/${config}/champsim/mix.json ${T_MIX}"
#    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/random.yaml --json results/8c/${config}/champsim/random.json ${T_RANDOM}"
#    
#    # Injeta os comandos dos experimentos Single-Core varrendo o diretório de traces
#    for trace_path in traces/*.champsimtrace.xz; do
#      # Substitui a diretiva {2/.} do GNU Parallel extraindo o nome base no próprio Bash
#      trace_name=$(basename "$trace_path" | sed 's/\.champsimtrace\.xz//')
#      echo "./bin/champsim_goldencove_1c_${config} --warmup-instructions 200000000 --ramulator-stats results/1c/${config}/ramulator/${trace_name}.yaml --json results/1c/${config}/champsim/${trace_name}.json ${trace_path}"
#    done
#    
#  done
#}
#
## Despeja a fila unificada no GNU Parallel com log e auto-resume
#gerar_comandos | parallel -j 48 --bar --joblog execucao_champsim.log --resume-failed

#!/bin/bash
# filepath: /home/lhwiedmer/tcc/ChampSim/run_all.sh
#!/bin/bash
# run_all.sh

usage() {
  echo "Uso: $0 [-m 1c|8c|all] [-j jobs]" >&2
  echo "  -m  Conjunto de experimentos a executar (padrão: all)" >&2
  echo "  -j  Número de jobs paralelos do GNU Parallel (padrão: 48)" >&2
  exit 1
}

MODE="all"
JOBS=48

while getopts ":m:j:h" opt; do
  case "$opt" in
    m) MODE="$OPTARG" ;;
    j) JOBS="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

case "$MODE" in
  1c|8c|all) ;;
  *) echo "Modo inválido: $MODE" >&2; usage ;;
esac

CONFIGS=("ddr5" "ddr5_llc" "hbm1" "hbm1_llc" "hbm2" "hbm2_llc" "hbm3" "hbm3_llc" "hbm4" "hbm4_llc")

T_COMPATIBLE="traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1536B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/620.omnetpp_s-141B.champsimtrace.xz traces/620.omnetpp_s-874B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz"
T_INCOMPATIBLE="traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/603.bwaves_s-891B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/654.roms_s-293B.champsimtrace.xz traces/649.fotonik3d_s-7084B.champsimtrace.xz traces/605.mcf_s-484B.champsimtrace.xz"
T_MIX="traces/649.fotonik3d_s-8225B.champsimtrace.xz traces/649.fotonik3d_s-1176B.champsimtrace.xz traces/602.gcc_s-2226B.champsimtrace.xz traces/602.gcc_s-1850B.champsimtrace.xz traces/605.mcf_s-782B.champsimtrace.xz traces/623.xalancbmk_s-10B.champsimtrace.xz traces/605.mcf_s-1554B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz"
T_RANDOM="traces/657.xz_s-3167B.champsimtrace.xz traces/605.mcf_s-1152B.champsimtrace.xz traces/605.mcf_s-665B.champsimtrace.xz traces/605.mcf_s-472B.champsimtrace.xz traces/641.leela_s-800B.champsimtrace.xz traces/607.cactuBSSN_s-4004B.champsimtrace.xz traces/648.exchange2_s-1227B.champsimtrace.xz traces/600.perlbench_s-1273B.champsimtrace.xz"

# Log e diretório de resultados isolados por modo para permitir execuções concorrentes
LOG="execucao_champsim_${MODE}.log"
DONE_CMDS="/tmp/champsim_done_cmds.$$"
trap 'rm -f "$DONE_CMDS"' EXIT

for config in "${CONFIGS[@]}"; do
  [[ "$MODE" == "1c" || "$MODE" == "all" ]] && mkdir -p "results/1c/${config}/ramulator" "results/1c/${config}/champsim"
  [[ "$MODE" == "8c" || "$MODE" == "all" ]] && mkdir -p "results/8c/${config}/ramulator" "results/8c/${config}/champsim"
done

gerar_comandos_8c() {
  for config in "${CONFIGS[@]}"; do
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/llc-compatible.yaml --json results/8c/${config}/champsim/llc-compatible.json ${T_COMPATIBLE}"
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/llc-incompatible.yaml --json results/8c/${config}/champsim/llc-incompatible.json ${T_INCOMPATIBLE}"
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/mix.yaml --json results/8c/${config}/champsim/mix.json ${T_MIX}"
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions 200000000 --ramulator-stats results/8c/${config}/ramulator/random.yaml --json results/8c/${config}/champsim/random.json ${T_RANDOM}"
  done
}

gerar_comandos_1c() {
  for config in "${CONFIGS[@]}"; do
    for trace_path in traces/*.champsimtrace.xz; do
      trace_name=$(basename "$trace_path" | sed 's/\.champsimtrace\.xz//')
      echo "./bin/champsim_goldencove_1c_${config} --warmup-instructions 200000000 --ramulator-stats results/1c/${config}/ramulator/${trace_name}.yaml --json results/1c/${config}/champsim/${trace_name}.json ${trace_path}"
    done
  done
}

gerar_comandos() {
  case "$MODE" in
    1c) gerar_comandos_1c ;;
    8c) gerar_comandos_8c ;;
    all) gerar_comandos_8c; gerar_comandos_1c ;;
  esac
}

# Extrai, pelo TEXTO do comando, apenas os que tiveram Exitval == 0 no log existente
if [[ -f "$LOG" ]]; then
  awk -F'\t' 'NR>1 && $7==0 { $1=$2=$3=$4=$5=$6=$7=$8=""; sub(/^\t+/,""); print }' OFS='\t' "$LOG" \
    | sed 's/^\t*//' > "$DONE_CMDS"
else
  : > "$DONE_CMDS"
fi

echo "Modo: $MODE | Comandos já concluídos com sucesso (Exitval=0): $(wc -l < "$DONE_CMDS")"

# Filtra por comparação exata de texto, não por posição/Seq
gerar_comandos | grep -Fxv -f "$DONE_CMDS" | parallel -j "$JOBS" --bar --joblog "$LOG"