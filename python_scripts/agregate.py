import json
import glob
import os
import csv
import re

# Configurações de diretórios
DIRETORIOS_RESULTADOS = [
    "results/1c/ddr5/champsim",
    "results/1c/ddr5_llc/champsim",
    "results/1c/hbm4/champsim",
    "results/1c/hbm4_llc/champsim"
]
DIRETORIO_PESOS = "traces/weights-and-simpoints-speccpu"
LIMITE_MPKI = 2.0  # Limiar padrão para classificar em Memory-Bound

def carregar_pesos_simpoints(diretorio_base):
    pesos_db = {}
    if not os.path.exists(diretorio_base):
        print(f"[Aviso] Diretório de pesos não encontrado: {diretorio_base}")
        return pesos_db

    pastas_benchmarks = glob.glob(os.path.join(diretorio_base, "*"))
    for pasta in pastas_benchmarks:
        if not os.path.isdir(pasta):
            continue
            
        nome_pasta = os.path.basename(pasta)
        arq_simpoints = os.path.join(pasta, "simpoints.out")
        arq_pesos = os.path.join(pasta, "weights.out")
        
        if os.path.exists(arq_simpoints) and os.path.exists(arq_pesos):
            with open(arq_simpoints, 'r') as f_sim:
                simpoints = [linha.strip() for linha in f_sim if linha.strip()]
            with open(arq_pesos, 'r') as f_peso:
                pesos = [float(linha.strip()) for linha in f_peso if linha.strip()]
            
            if len(simpoints) == len(pesos):
                pesos_db[nome_pasta] = {sp: peso for sp, peso in zip(simpoints, pesos)}
            else:
                print(f"[Aviso] Tamanho de simpoints e pesos difere em {nome_pasta}")
                
    return pesos_db

def extrair_identificadores_trace(nome_trace):
    nome_arquivo = os.path.basename(nome_trace)
    match = re.search(r'([0-9]+\.[a-zA-Z0-9_]+)-(\d+)B', nome_arquivo)
    if match:
        core_name = match.group(1)
        simpoint_id = match.group(2)
        return core_name, simpoint_id
        
    return None, None

def somar_acessos(dicionario_cache, tipo_acesso):
    if tipo_acesso not in dicionario_cache: return 0
    dados = dicionario_cache[tipo_acesso]
    return sum(dados.get("hit", [0])) + sum(dados.get("miss", [0])) + sum(dados.get("miss_merge", [0]))

def somar_misses_reais(dicionario_cache, tipos_acesso):
    total_misses = 0
    for req in tipos_acesso:
        if req in dicionario_cache:
            total_misses += sum(dicionario_cache[req].get("miss", [0]))
    return total_misses

def extrair_metricas(caminho_arquivo):
    with open(caminho_arquivo, 'r') as f:
        dados = json.load(f)
        if isinstance(dados, list): dados = dados[0]
            
        sim = dados["sim"]
        nome_trace = dados.get("traces", [os.path.basename(caminho_arquivo)])[0]
        
        instrucoes = sim["cores"][0]["instructions"]
        ciclos = sim["cores"][0]["cycles"]
        ipc = instrucoes / ciclos if ciclos > 0 else 0
        
        l1d = sim["cpu0_L1D"]
        acessos_l1d = somar_acessos(l1d, "LOAD") + somar_acessos(l1d, "WRITE")
        bytes_requisitados = acessos_l1d * 8
        ia = instrucoes / bytes_requisitados if bytes_requisitados > 0 else 0
        
        llc = sim.get("LLC", {})
        llc_misses_totais = somar_misses_reais(llc, ["LOAD", "RFO", "PREFETCH", "WRITE", "TRANSLATION"])
        llc_mpki = (llc_misses_totais / instrucoes) * 1000 if instrucoes > 0 else 0
        
        l1d_misses = somar_misses_reais(l1d, ["LOAD", "WRITE", "TRANSLATION"])
        
        # CORREÇÃO: Trata o caso onde miss latency vem como null (None no Python) do ChampSim
        l1d_miss_latency = l1d.get("miss latency")
        if l1d_miss_latency is None:
            l1d_miss_latency = 0.0
            
        mlp_l1d = (l1d_misses * l1d_miss_latency) / ciclos if ciclos > 0 else 0
        
        return {
            "Trace_Original": nome_trace,
            "IPC": ipc,
            "IA_Inst_per_Byte": ia,
            "LLC_MPKI": llc_mpki,
            "MLP_L1D": mlp_l1d
        }

def agregar_resultados(resultados_individuais, pesos_db):
    agrupados = {}
    for r in resultados_individuais:
        core_name, sp_id = extrair_identificadores_trace(r["Trace_Original"])
        
        if not core_name or not sp_id:
            print(f"[Aviso] Formato não reconhecido (pulando agregação): {r['Trace_Original']}")
            continue
            
        if core_name not in agrupados:
            agrupados[core_name] = []
        agrupados[core_name].append((sp_id, r))

    resultados_finais = []
    
    for core_name, simulacoes in agrupados.items():
        mapa_pesos = pesos_db.get(core_name, {})
        
        if not mapa_pesos:
            print(f"[Aviso] Pesos não encontrados para o benchmark '{core_name}'. O cálculo usará média simples.")
            soma_pesos = 1.0 * len(simulacoes)
            pesos_validos = [(1.0, res) for _, res in simulacoes]
        else:
            soma_pesos = 0.0
            pesos_validos = []
            for sp_id, res in simulacoes:
                peso = mapa_pesos.get(sp_id, 0.0)
                if peso == 0.0:
                    print(f"  -> [Aviso] Simpoint {sp_id} de {core_name} não achou peso correspondente. Assumindo peso 0.")
                soma_pesos += peso
                pesos_validos.append((peso, res))
                
        if soma_pesos == 0.0:
            print(f"[Erro] Soma dos pesos encontrados é 0 para {core_name}. Pulando agregação desse benchmark...")
            continue
            
        ipc_agregado = 0
        ia_agregado = 0
        mpki_agregado = 0
        mlp_agregado = 0
        
        for peso, r in pesos_validos:
            peso_normalizado = peso / soma_pesos
            ipc_agregado += r["IPC"] * peso_normalizado
            ia_agregado += r["IA_Inst_per_Byte"] * peso_normalizado
            mpki_agregado += r["LLC_MPKI"] * peso_normalizado
            mlp_agregado += r["MLP_L1D"] * peso_normalizado
            
        classificacao = "Memory-Bound" if mpki_agregado > LIMITE_MPKI else "Compute-Bound"
        
        resultados_finais.append({
            "Benchmark": core_name,
            "Classificacao": classificacao,
            "IPC": round(ipc_agregado, 4),
            "IA_Inst_per_Byte": round(ia_agregado, 4),
            "LLC_MPKI": round(mpki_agregado, 4),
            "MLP_L1D": round(mlp_agregado, 4),
            "Simpoints_Usados": len(simulacoes),
            "Soma_Pesos_Original": round(soma_pesos, 4)
        })
        
    return resultados_finais

def processar_diretorio(diretorio, pesos_db):
    padrao_busca = os.path.join(diretorio, "*.json")
    arquivos = glob.glob(padrao_busca)
    
    if not arquivos:
        print(f"\n[Aviso] Nenhum arquivo JSON encontrado em: {diretorio}")
        return

    partes_caminho = os.path.normpath(diretorio).split(os.sep)
    nome_config = partes_caminho[2] if len(partes_caminho) > 2 else "desconhecido"
    arquivo_saida_csv = f"classificacao_benchmarks_agregado_{nome_config}.csv"

    print(f"\nProcessando {len(arquivos)} arquivos de trace em {diretorio}...")
    resultados_individuais = []
    
    for arq in arquivos:
        try:
            resultados_individuais.append(extrair_metricas(arq))
        except Exception as e:
            print(f"Erro ao processar {arq}: {e}")

    resultados_agregados = agregar_resultados(resultados_individuais, pesos_db)
    resultados_agregados = sorted(resultados_agregados, key=lambda x: x["IPC"], reverse=False)

    with open(arquivo_saida_csv, 'w', newline='') as csvfile:
        campos = ["Benchmark", "Classificacao", "IPC", "IA_Inst_per_Byte", "LLC_MPKI", "MLP_L1D", "Simpoints_Usados", "Soma_Pesos_Original"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados_agregados)

    compute_bound = sum(1 for r in resultados_agregados if r["Classificacao"] == "Compute-Bound")
    memory_bound = sum(1 for r in resultados_agregados if r["Classificacao"] == "Memory-Bound")

    print(f"--- RESUMO AGREGADO: {nome_config.upper()} ---")
    print(f"Total de Benchmarks distintos: {len(resultados_agregados)}")
    print(f"Compute-Bound: {compute_bound}")
    print(f"Memory-Bound:  {memory_bound}")
    print(f"Arquivo CSV gerado: {arquivo_saida_csv}")

def main():
    print(f"Carregando base de dados de pesos SimPoint a partir de: {DIRETORIO_PESOS}...")
    pesos_db = carregar_pesos_simpoints(DIRETORIO_PESOS)
    
    if not pesos_db:
        print("[Aviso] A base de pesos falhou ou está vazia.")
    else:
        print(f"Pesos mapeados com sucesso para {len(pesos_db)} benchmarks.")
        
    for diretorio in DIRETORIOS_RESULTADOS:
        processar_diretorio(diretorio, pesos_db)

if __name__ == "__main__":
    main()