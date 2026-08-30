#./config.sh champsim_configs/goldencove_1c_HBM_LLC.json

#make -j$(nproc) CPPFLAGS='-DRAMULATOR_TX_BYTES=32 -DRAMULATOR_CONFIG=\"ramulator_configs/yaml/hbm4.yaml\"'

./bin/champsim_goldencove_1c_hbm4_llc --warmup-instructions 1000000 \
               --simulation-instructions 1000000 \
               --ramulator-stats test_ramulator.yaml \
               --json test_champsim.josn \
               traces/602.gcc_s-2375B.champsimtrace.xz