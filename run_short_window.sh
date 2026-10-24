#!/bin/bash
# run_short_window.sh

usage() {
  echo "Uso: $0 [-m 1c|8c|all] [-j jobs] [-w instrucoes_warmup] [-s instrucoes_simulacao]" >&2
  echo "  -m  Conjunto de experimentos a executar (padrão: all)" >&2
  echo "  -j  Número de jobs paralelos do GNU Parallel (padrão: 48)" >&2
  echo "  -w  Instruções de warmup (padrão: 200000000)" >&2
  echo "  -s  Instruções de simulação da JANELA CURTA (padrão: 50000000)" >&2
  exit 1
}

MODE="all"
JOBS=25
WARMUP=200000000
SIM=300000000

while getopts ":m:j:w:s:h" opt; do
  case "$opt" in
    m) MODE="$OPTARG" ;;
    j) JOBS="$OPTARG" ;;
    w) WARMUP="$OPTARG" ;;
    s) SIM="$OPTARG" ;;
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

# Extrai uma lista única de traces para não rodar Single-Core de traces que não estão nos bundles
UNIQUE_TRACES=$(echo -e "${T_COMPATIBLE}\n${T_INCOMPATIBLE}\n${T_MIX}\n${T_RANDOM}" | tr ' ' '\n' | sort -u | grep -v '^$')

# Usar um novo diretório para preservar os dados originais
RES_DIR="results_sw"

# Log isolado para as execuções de short window
LOG="execucao_champsim_sw_${MODE}.log"
DONE_CMDS="/tmp/champsim_done_cmds_sw.$$"
NEW_LOG="/tmp/champsim_new_log_sw.$$"
trap 'rm -f "$DONE_CMDS" "$NEW_LOG"' EXIT

for config in "${CONFIGS[@]}"; do
  [[ "$MODE" == "1c" || "$MODE" == "all" ]] && mkdir -p "${RES_DIR}/1c/${config}/ramulator" "${RES_DIR}/1c/${config}/champsim"
  [[ "$MODE" == "8c" || "$MODE" == "all" ]] && mkdir -p "${RES_DIR}/8c/${config}/ramulator" "${RES_DIR}/8c/${config}/champsim"
done

gerar_comandos_8c() {
  for config in "${CONFIGS[@]}"; do
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions ${WARMUP} --simulation-instructions ${SIM} --ramulator-stats ${RES_DIR}/8c/${config}/ramulator/llc-compatible.yaml --json ${RES_DIR}/8c/${config}/champsim/llc-compatible.json ${T_COMPATIBLE}"
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions ${WARMUP} --simulation-instructions ${SIM} --ramulator-stats ${RES_DIR}/8c/${config}/ramulator/llc-incompatible.yaml --json ${RES_DIR}/8c/${config}/champsim/llc-incompatible.json ${T_INCOMPATIBLE}"
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions ${WARMUP} --simulation-instructions ${SIM} --ramulator-stats ${RES_DIR}/8c/${config}/ramulator/mix.yaml --json ${RES_DIR}/8c/${config}/champsim/mix.json ${T_MIX}"
    echo "./bin/champsim_goldencove_8c_${config} --warmup-instructions ${WARMUP} --simulation-instructions ${SIM} --ramulator-stats ${RES_DIR}/8c/${config}/ramulator/random.yaml --json ${RES_DIR}/8c/${config}/champsim/random.json ${T_RANDOM}"
  done
}

gerar_comandos_1c() {
  for config in "${CONFIGS[@]}"; do
    # Varre apenas os traces utilizados nos bundles
    for trace_path in ${UNIQUE_TRACES}; do
      trace_name=$(basename "$trace_path" | sed 's/\.champsimtrace\.xz//')
      echo "./bin/champsim_goldencove_1c_${config} --warmup-instructions ${WARMUP} --simulation-instructions ${SIM} --ramulator-stats ${RES_DIR}/1c/${config}/ramulator/${trace_name}.yaml --json ${RES_DIR}/1c/${config}/champsim/${trace_name}.json ${trace_path}"
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

if [[ -f "$LOG" ]]; then
  awk -F'\t' 'NR>1 && $7==0 { $1=$2=$3=$4=$5=$6=$7=$8=""; sub(/^\t+/,""); print }' OFS='\t' "$LOG" \
    | sed 's/^\t*//' > "$DONE_CMDS"
else
  : > "$DONE_CMDS"
fi

echo "Modo: $MODE | Comandos SW concluídos: $(wc -l < "$DONE_CMDS")"

gerar_comandos | grep -Fxv -f "$DONE_CMDS" | parallel -j "$JOBS" --bar --joblog "$NEW_LOG"

if [[ -s "$NEW_LOG" ]]; then
  if [[ -s "$LOG" ]]; then
    { head -n1 "$NEW_LOG"; tail -n +2 "$LOG"; tail -n +2 "$NEW_LOG"; } > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
  else
    mv "$NEW_LOG" "$LOG"
  fi
fi