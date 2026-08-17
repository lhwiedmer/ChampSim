./config.sh champsim_configs/goldencove_1c_HBM_LLC.json

make -j$(nproc) CPPFLAGS='-DRAMULATOR_TX_BYTES=32 -DRAMULATOR_CONFIG=\"ramulator_configs/yaml/hbm4.yaml\"'

./bin/champsim_goldencove_1c_hbm_llc --warmup-instructions 10000000 \
               --simulation-instructions 30000000 \
               --ramulator-stats results/ramulator/429.mcf-184B.yaml \
               --json results/champsim/429.mcf-184B.json \
               traces/429.mcf-184B.champsimtrace.xz