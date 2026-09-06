#!/bin/bash
# compile_all.sh

MEM_TYPES=("ddr5" "hbm1" "hbm2" "hbm3" "hbm4")
CORES=("1c" "8c")
LLC_VARIANTS=("" "_LLC") 

for mem in "${MEM_TYPES[@]}"; do
  
  # Aplica o tamanho de transação física correto conforme a tecnologia
  if [ "$mem" == "ddr5" ]; then
    TX_BYTES=64
  else
    TX_BYTES=32
  fi
  
  # Converte o nome da memória para maiúsculo para mapear com o arquivo JSON (ex: ddr5 -> DDR5)
  mem_upper=$(echo "$mem" | tr '[:lower:]' '[:upper:]')
  
  for core in "${CORES[@]}"; do
    for llc in "${LLC_VARIANTS[@]}"; do
      
      config_file="champsim_configs/${mem}/goldencove_${core}_${mem_upper}${llc}.json"
      
      if [ -f "$config_file" ]; then
        echo "=================================================="
        echo "Compilando: $config_file"
        echo "=================================================="
        
        ./config.sh "$config_file"
        
        # A compilação é sequencial para evitar concorrência de reescrita nos objetos do ChampSim
        make -j$(nproc) CPPFLAGS="-DRAMULATOR_TX_BYTES=${TX_BYTES} -DRAMULATOR_CONFIG=\\\"ramulator_configs/yaml/${mem}.yaml\\\""
      else
        echo "Aviso: Arquivo $config_file não encontrado, ignorando..."
      fi
      
    done
  done
done