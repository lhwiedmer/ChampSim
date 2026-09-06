#./config.sh champsim_configs/goldencove_1c_HBM_LLC.json

#make -j$(nproc) CPPFLAGS='-DRAMULATOR_TX_BYTES=32 -DRAMULATOR_CONFIG=\"ramulator_configs/yaml/hbm4.yaml\"'

./bin/champsim_goldencove_8c_hbm4 --warmup-instructions 100000 \
               --simulation-instructions 10000 \
               --ramulator-stats test_ramulator.yaml \
               --json test_champsim.json \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz \
               traces/602.gcc_s-2375B.champsimtrace.xz