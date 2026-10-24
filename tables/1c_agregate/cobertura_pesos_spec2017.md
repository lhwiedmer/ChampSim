# Cobertura dos pesos SimPoint - SPEC CPU 2017

Cobertura calculada por benchmark como a soma dos pesos dos SimPoints com JSON disponível dividida pela soma total dos pesos em `weights.out`. Os pesos podem somar valores ligeiramente diferentes de 1 devido ao arredondamento nos arquivos originais.

Os arquivos JSON presentes e os pesos correspondentes são iguais nas dez configurações analisadas: `ddr5`, `ddr5_llc`, `hbm1`, `hbm1_llc`, `hbm2`, `hbm2_llc`, `hbm3`, `hbm3_llc`, `hbm4` e `hbm4_llc`.

| Benchmark | Peso presente | Cobertura | SimPoints presentes |
|---|---:|---:|---:|
| 600.perlbench_s | 0.99065400 | 99.0654% | 3/10 |
| 602.gcc_s | 0.97859040 | 97.8590% | 4/10 |
| 603.bwaves_s | 0.98804040 | 98.8040% | 7/10 |
| 605.mcf_s | 0.99949370 | 99.9494% | 9/10 |
| 607.cactuBSSN_s | 0.96904980 | 96.9049% | 4/10 |
| 619.lbm_s | 0.98688900 | 98.6889% | 4/10 |
| 620.omnetpp_s | 0.99178800 | 99.1788% | 2/10 |
| 621.wrf_s | 0.99187500 | 99.1876% | 4/7 |
| 623.xalancbmk_s | 0.99654310 | 99.6543% | 6/10 |
| 625.x264_s | 0.99767460 | 99.7674% | 5/6 |
| 627.cam4_s | 0.98936610 | 98.9366% | 2/10 |
| 628.pop2_s | 1.00000000 | 100.0000% | 1/1 |
| 631.deepsjeng_s | 0.99028700 | 99.0287% | 1/10 |
| 638.imagick_s | 0.99355100 | 99.3551% | 3/10 |
| 641.leela_s | 0.99039330 | 99.0393% | 7/10 |
| 644.nab_s | 0.97593320 | 97.5934% | 5/10 |
| 648.exchange2_s | 1.00000050 | 100.0000% | 10/10 |
| 649.fotonik3d_s | 0.99920830 | 99.9209% | 5/10 |
| 654.roms_s | 0.99512090 | 99.5122% | 9/10 |
| 657.xz_s | 0.99740220 | 99.7403% | 4/10 |

Menor cobertura: `607.cactuBSSN_s`, com peso presente de `0.96904980` e cobertura de `96.9049%`.
