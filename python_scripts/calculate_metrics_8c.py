import json
import glob
import os
import csv

# Configurações de diretórios
DIRETORIOS_RESULTADOS = [
    "results/8c/ddr5/champsim",
    "results/8c/ddr5_llc/champsim",
    "results/8c/hbm4/champsim",
    "results/8c/hbm4_llc/champsim"
]
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

def extrair_metricas(caminho_arquivo):
    with open(caminho_arquivo, 'r') as f:
        dados = json.load(f)
        
        if isinstance(dados, list):
            dados = dados[0]
            
        sim = dados["sim"]
        
        # CORREÇÃO AQUI: Pega o nome do arquivo (ex: "llc-compatible")
        nome_trace = os.path.basename(caminho_arquivo).replace(".json", "")
        
        num_cores = len(sim["cores"])
        
        # 1. Instruções, Ciclos e IPC Agregado (System IPC)
        total_instrucoes = 0
        max_ciclos = 0
        
        for core in sim["cores"]:
            total_instrucoes += core["instructions"]
            if core["cycles"] > max_ciclos:
                max_ciclos = core["cycles"]
                
        ipc_agregado = total_instrucoes / max_ciclos if max_ciclos > 0 else 0
        
        # 2. Intensidade Aritmética (CARM) Agregada
        total_acessos_l1d = 0
        for i in range(num_cores):
            l1d = sim.get(f"cpu{i}_L1D", {})
            total_acessos_l1d += somar_acessos(l1d, "LOAD") + somar_acessos(l1d, "WRITE")
            
        bytes_requisitados = total_acessos_l1d * 8 
        ia_agregada = total_instrucoes / bytes_requisitados if bytes_requisitados > 0 else 0
        
        # 3. LLC Misses e LLC MPKI
        llc = sim.get("LLC", {})
        tipos_requisicao = ["LOAD", "RFO", "PREFETCH", "WRITE", "TRANSLATION"]
        llc_misses_totais = somar_misses_reais(llc, tipos_requisicao)
        llc_mpki = (llc_misses_totais / total_instrucoes) * 1000 if total_instrucoes > 0 else 0
        
        # 4. Cálculo de Paralelismo via Lei de Little Agregado
        mlp_l1d_total = 0
        for i in range(num_cores):
            l1d = sim.get(f"cpu{i}_L1D", {})
            l1d_misses = somar_misses_reais(l1d, ["LOAD", "WRITE", "TRANSLATION"])
            l1d_miss_latency = l1d.get("miss latency", 0.0)
            if l1d_miss_latency is None:
                l1d_miss_latency = 0.0
            
            mlp_core = (l1d_misses * l1d_miss_latency) / max_ciclos if max_ciclos > 0 else 0
            mlp_l1d_total += mlp_core
        
        classificacao = "Memory-Bound" if llc_mpki > LIMITE_MPKI else "Compute-Bound"
        
        return {
            "Trace": nome_trace, # Agora aparecerá llc-compatible, mix, etc.
            "Classificacao": classificacao,
            "IPC_Agregado": round(ipc_agregado, 4),
            "IA_Inst_per_Byte": round(ia_agregada, 4),
            "LLC_MPKI": round(llc_mpki, 4),
            "MLP_L1D_Total": round(mlp_l1d_total, 4),
        }

def processar_diretorio(diretorio):
    padrao_busca = os.path.join(diretorio, "*.json")
    arquivos = glob.glob(padrao_busca)
    
    if not arquivos:
        print(f"\n[Aviso] Nenhum arquivo JSON encontrado em: {diretorio}")
        return

    partes_caminho = os.path.normpath(diretorio).split(os.sep)
    nome_config = partes_caminho[2] if len(partes_caminho) > 2 else "desconhecido"
    arquivo_saida_csv = f"classificacao_traces_{nome_config}_8core.csv"

    resultados = []
    
    print(f"\nProcessando arquivos em {diretorio}...")
    for arq in arquivos:
        try:
            metricas = extrair_metricas(arq)
            resultados.append(metricas)
        except Exception as e:
            print(f"Erro ao processar {arq}: {e}")

    # Ordenar por nome do Trace para ficar mais fácil de ler
    resultados = sorted(resultados, key=lambda x: x["Trace"])

    # Escrever CSV
    with open(arquivo_saida_csv, 'w', newline='') as csvfile:
        campos = ["Trace", "Classificacao", "IPC_Agregado", "IA_Inst_per_Byte", "LLC_MPKI", "MLP_L1D_Total"]
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