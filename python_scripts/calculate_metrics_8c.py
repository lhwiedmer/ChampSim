import json
import glob
import os
import csv

# Configurações de diretórios
DIRETORIOS_RESULTADOS = [
    "results/8c/ddr5/champsim",
    "results/8c/ddr5_llc/champsim",
    "results/8c/hbm1/champsim",
    "results/8c/hbm1_llc/champsim",
    "results/8c/hbm2/champsim",
    "results/8c/hbm2_llc/champsim",
    "results/8c/hbm3/champsim",
    "results/8c/hbm3_llc/champsim",
    "results/8c/hbm4/champsim",
    "results/8c/hbm4_llc/champsim"
]
DIRETORIO_SAIDA = os.path.join("tables", "8c")
CONFIGURACAO_BASELINE_SINGLE_CORE = "ddr5_llc"
LIMITE_MPKI = 2.0  # Limiar padrão para classificar em Memory-Bound

def somar_acessos(dicionario_cache, tipo_acesso):
    if tipo_acesso not in dicionario_cache:
        return 0
    dados = dicionario_cache[tipo_acesso]
    hits = sum(dados.get("hit", [0]))
    misses = sum(dados.get("miss", [0]))
    merges = sum(dados.get("miss_merge", [0]))
    return hits + misses + merges

def somar_misses_reais(dicionario_cache, tipos_acesso):
    total_misses = 0
    for req in tipos_acesso:
        if req in dicionario_cache:
            total_misses += sum(dicionario_cache[req].get("miss", [0]))
    return total_misses

def calcular_weighted_speedup(cores, traces, ipc_single_core):
    if ipc_single_core is None or len(cores) != len(traces):
        return None

    weighted_speedup = 0
    for core, trace in zip(cores, traces):
        ipc_isolado = ipc_single_core.get(trace)
        ciclos = core["cycles"]
        if ipc_isolado is None or ipc_isolado <= 0 or ciclos <= 0:
            return None

        ipc_multicore = core["instructions"] / ciclos
        weighted_speedup += ipc_multicore / ipc_isolado

    return weighted_speedup

def carregar_ipcs_single_core(nome_config):
    caminho_tabela = os.path.join("tables", "1c_trace", f"{nome_config}.csv")
    if not os.path.exists(caminho_tabela):
        return None

    with open(caminho_tabela, "r", newline="") as csvfile:
        leitor = csv.DictReader(csvfile)
        return {linha["Trace"]: float(linha["IPC"]) for linha in leitor}

def extrair_metricas(caminho_arquivo, ipc_single_core=None):
    with open(caminho_arquivo, 'r') as f:
        dados = json.load(f)
        
        if isinstance(dados, list):
            dados = dados[0]
            
        roi = dados["roi"]
        traces = dados.get("traces", [])
        
        # CORREÇÃO AQUI: Pega o nome do arquivo (ex: "llc-compatible")
        nome_trace = os.path.basename(caminho_arquivo).replace(".json", "")
        
        num_cores = len(roi["cores"])
        
        # 1. Instruções, Ciclos e IPC Agregado (System IPC)
        total_instrucoes = 0
        max_ciclos = 0
        
        for core in roi["cores"]:
            total_instrucoes += core["instructions"]
            if core["cycles"] > max_ciclos:
                max_ciclos = core["cycles"]
                
        ipc_agregado = total_instrucoes / max_ciclos if max_ciclos > 0 else 0
        weighted_speedup = calcular_weighted_speedup(roi["cores"], traces, ipc_single_core)
        
        # 2. Intensidade Aritmética (CARM) Agregada
        total_acessos_l1d = 0
        for i in range(num_cores):
            l1d = roi.get(f"cpu{i}_L1D", {})
            total_acessos_l1d += somar_acessos(l1d, "LOAD") + somar_acessos(l1d, "WRITE")
            
        bytes_requisitados = total_acessos_l1d * 8 
        ia_agregada = total_instrucoes / bytes_requisitados if bytes_requisitados > 0 else 0
        
        # 3. LLC Misses e LLC MPKI
        llc = roi.get("LLC", {})
        tipos_requisicao = ["LOAD", "RFO", "PREFETCH", "WRITE", "TRANSLATION"]
        llc_misses_totais = somar_misses_reais(llc, tipos_requisicao)
        llc_mpki = (llc_misses_totais / total_instrucoes) * 1000 if total_instrucoes > 0 else 0

        l2d_misses_totais = 0
        for i in range(num_cores):
            l2d = roi.get(f"cpu{i}_L2C", {})
            l2d_misses_totais += somar_misses_reais(l2d, tipos_requisicao)
        l2d_mpki = (l2d_misses_totais / total_instrucoes) * 1000 if total_instrucoes > 0 else 0
        
        classificacao = "Memory-Bound" if llc_mpki > LIMITE_MPKI else "Compute-Bound"
        
        return {
            "Trace": nome_trace, # Agora aparecerá llc-compatible, mix, etc.
            "Classificacao": classificacao,
            "IPC_Agregado": round(ipc_agregado, 4),
            "Weighted_Speedup": round(weighted_speedup, 4) if weighted_speedup is not None else None,
            "IA_Inst_per_Byte": round(ia_agregada, 4),
            "LLC_MPKI": round(llc_mpki, 4),
            "L2D_MPKI": round(l2d_mpki, 4),
        }

def adicionar_linha_media(resultados):
    if not resultados:
        return resultados

    metricas = ["IPC_Agregado", "Weighted_Speedup", "IA_Inst_per_Byte", "LLC_MPKI", "L2D_MPKI"]
    media = {}
    for metrica in metricas:
        valores = [resultado[metrica] for resultado in resultados if resultado[metrica] is not None]
        media[metrica] = round(sum(valores) / len(valores), 4) if valores else None

    resultados.append({
        "Trace": "Resumo",
        "Classificacao": "Memory-Bound" if media["LLC_MPKI"] > LIMITE_MPKI else "Compute-Bound",
        **media
    })
    return resultados

def processar_diretorio(diretorio):
    padrao_busca = os.path.join(diretorio, "*.json")
    arquivos = glob.glob(padrao_busca)
    
    if not arquivos:
        print(f"\n[Aviso] Nenhum arquivo JSON encontrado em: {diretorio}")
        return

    partes_caminho = os.path.normpath(diretorio).split(os.sep)
    nome_config = partes_caminho[2] if len(partes_caminho) > 2 else "desconhecido"
    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    arquivo_saida_csv = os.path.join(DIRETORIO_SAIDA, f"{nome_config}.csv")
    ipc_single_core = carregar_ipcs_single_core(CONFIGURACAO_BASELINE_SINGLE_CORE)
    if ipc_single_core is None:
        print(
            f"[Aviso] Tabela single-core não encontrada para "
            f"{CONFIGURACAO_BASELINE_SINGLE_CORE}; Weighted Speedup ficará vazio."
        )

    resultados = []
    
    print(f"\nProcessando arquivos em {diretorio}...")
    for arq in arquivos:
        try:
            metricas = extrair_metricas(arq, ipc_single_core)
            if metricas["Weighted_Speedup"] is None and ipc_single_core is not None:
                print(f"[Aviso] Não foi possível calcular Weighted Speedup para {arq}: trace sem IPC single-core válido.")
            resultados.append(metricas)
        except Exception as e:
            print(f"Erro ao processar {arq}: {e}")

    # Ordenar por nome do Trace para ficar mais fácil de ler
    resultados = sorted(resultados, key=lambda x: x["Trace"])
    resultados = adicionar_linha_media(resultados)

    # Escrever CSV
    with open(arquivo_saida_csv, 'w', newline='') as csvfile:
        campos = ["Trace", "Classificacao", "IPC_Agregado", "Weighted_Speedup", "IA_Inst_per_Byte", "LLC_MPKI", "L2D_MPKI"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"--- RESUMO: {nome_config.upper()} ---")
    print(f"Arquivo CSV gerado: {arquivo_saida_csv}")

def main():
    for diretorio in DIRETORIOS_RESULTADOS:
        processar_diretorio(diretorio)

if __name__ == "__main__":
    main()