import json
import glob
import os
import csv

# Configurações de diretório e saída
DIRETORIO_RESULTADOS = "results/classification_prefetch/champsim/*.json"
ARQUIVO_SAIDA_CSV = "classificacao_traces_prefetch.csv"
LIMITE_MPKI = 2.0  # Limiar padrão para classificar em Memory-Bound

def somar_acessos(dicionario_cache, tipo_acesso):
    """Soma hits, misses e miss_merges de um tipo específico de acesso."""
    if tipo_acesso not in dicionario_cache:
        return 0
    dados = dicionario_cache[tipo_acesso]
    hits = sum(dados.get("hit", [0]))
    misses = sum(dados.get("miss", [0]))
    merges = sum(dados.get("miss_merge", [0]))
    return hits + misses + merges

def somar_misses_reais(dicionario_cache, tipos_acesso):
    """Soma apenas os misses primários (sem merges) para os tipos indicados."""
    total_misses = 0
    for req in tipos_acesso:
        if req in dicionario_cache:
            total_misses += sum(dicionario_cache[req].get("miss", [0]))
    return total_misses

def extrair_metricas(caminho_arquivo):
    with open(caminho_arquivo, 'r') as f:
        dados = json.load(f)
        
        # O ChampSim cospe uma lista cujo primeiro elemento é o bloco de simulação
        if isinstance(dados, list):
            dados = dados[0]
            
        sim = dados["sim"]
        nome_trace = dados["traces"][0] if "traces" in dados else os.path.basename(caminho_arquivo)
        
        # 1. Instruções, Ciclos e IPC
        instrucoes = sim["cores"][0]["instructions"]
        ciclos = sim["cores"][0]["cycles"]
        ipc = instrucoes / ciclos if ciclos > 0 else 0
        
        # 2. Intensidade Aritmética (CARM)
        l1d = sim["cpu0_L1D"]
        acessos_l1d = somar_acessos(l1d, "LOAD") + somar_acessos(l1d, "WRITE")
        bytes_requisitados = acessos_l1d * 8  # 8 bytes por acesso (64-bit)
        ia = instrucoes / bytes_requisitados if bytes_requisitados > 0 else 0
        
        # 3. LLC Misses e LLC MPKI
        llc = sim.get("LLC", {})
        tipos_requisicao = ["LOAD", "RFO", "PREFETCH", "WRITE", "TRANSLATION"]
        llc_misses_totais = somar_misses_reais(llc, tipos_requisicao)
        llc_mpki = (llc_misses_totais / instrucoes) * 1000 if instrucoes > 0 else 0
        
        # 4. Cálculo de Paralelismo via Lei de Little (L = lambda * W)
        # 4.1 MLP no L1D (Paralelismo de Memória gerado pelo Core)
        l1d_misses = somar_misses_reais(l1d, ["LOAD", "WRITE", "TRANSLATION"])
        l1d_miss_latency = l1d.get("miss latency", 0.0)
        mlp_l1d = (l1d_misses * l1d_miss_latency) / ciclos if ciclos > 0 else 0
        
        classificacao = "Memory-Bound" if llc_mpki > LIMITE_MPKI else "Compute-Bound"
        
        return {
            "Trace": nome_trace,
            "Classificacao": classificacao,
            "IPC": round(ipc, 4),
            "IA_Inst_per_Byte": round(ia, 4),
            "LLC_MPKI": round(llc_mpki, 4),
            "MLP_L1D": round(mlp_l1d, 4),
        }

def main():
    arquivos = glob.glob(DIRETORIO_RESULTADOS)
    if not arquivos:
        print(f"Nenhum arquivo JSON encontrado em: {DIRETORIO_RESULTADOS}")
        return

    resultados = []
    compute_bound = []
    memory_bound = []

    print(f"Processando arquivos em {DIRETORIO_RESULTADOS}...")
    for arq in arquivos:
        try:
            metricas = extrair_metricas(arq)
            resultados.append(metricas)
            
            if metricas["Classificacao"] == "Compute-Bound":
                compute_bound.append(metricas)
            else:
                memory_bound.append(metricas)
        except Exception as e:
            print(f"Erro ao processar {arq}: {e}")

    # Ordenar resultados por LLC MPKI decrescente
    resultados = sorted(resultados, key=lambda x: x["LLC_MPKI"], reverse=True)

    # Escrever CSV
    with open(ARQUIVO_SAIDA_CSV, 'w', newline='') as csvfile:
        campos = ["Trace", "Classificacao", "IPC", "IA_Inst_per_Byte", "LLC_MPKI", "MLP_L1D"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print("\n--- RESUMO ---")
    print(f"Total de Traces: {len(resultados)}")
    print(f"Compute-Bound: {len(compute_bound)}")
    print(f"Memory-Bound:  {len(memory_bound)}")
    print(f"Arquivo CSV gerado: {ARQUIVO_SAIDA_CSV}")

if __name__ == "__main__":
    main()