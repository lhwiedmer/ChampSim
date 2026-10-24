#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$HOME/tcc/TCC-latex"

cd "$ROOT_DIR"
mkdir -p "$OUTPUT_DIR"

gerar_grafico() {
    local benchmark="$1"
    shift
    python3 python_scripts/plot_1c.py \
        --configuracoes "$@" \
        --baseline "DDR5+LLC" \
        --saida "$OUTPUT_DIR/1c_${benchmark}.png"
}

gerar_grafico hbm4 DDR5+LLC HBM4 HBM4+LLC
gerar_grafico hbm3 DDR5+LLC HBM3 HBM3+LLC
gerar_grafico hbm2 DDR5+LLC HBM2 HBM2+LLC
gerar_grafico hbm1 DDR5+LLC HBM1 HBM1+LLC
gerar_grafico ddr5 DDR5+LLC DDR5

python3 python_scripts/plot_1c_mpki.py \
    --saida "$OUTPUT_DIR/1c_mpki.png"