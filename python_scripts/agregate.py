import json
import glob
import os
import csv
import re

# Configurações de diretórios
DIRETORIOS_RESULTADOS = [
    "results/1c/ddr5/champsim",
    "results/1c/ddr5_llc/champsim",
    "results/1c/hbm1/champsim",
    "results/1c/hbm1_llc/champsim",
    "results/1c/hbm2/champsim",
    "results/1c/hbm2_llc/champsim",
    "results/1c/hbm3/champsim",
    "results/1c/hbm3_llc/champsim",
    "results/1c/hbm4/champsim",
    "results/1c/hbm4_llc/champsim"
]
DIRETORIO_SAIDA = os.path.join("tables", "1c_agregate")
DIRETORIO_TRACES = os.path.join("tables", "1c_trace")
DIRETORIO_PESOS = "traces/weights-and-simpoints-speccpu"
LIMITE_MPKI = 2.0  # Limiar padrão para classificar em Memory-Bound

def carregar_mlp_traces(nome_config):
    caminho = os.path.join(DIRETORIO_TRACES, f"{nome_config}.csv")
    if not os.path.exists(caminho):
        print(f"[Aviso] Tabela de MLP não encontrada: {caminho}. MLP_L1D ficará vazio.")
        return {}

    with open(caminho, newline='') as arquivo:
        leitor = csv.DictReader(arquivo)
        if not leitor.fieldnames or not {"Trace", "MLP_L1D"}.issubset(leitor.fieldnames):
            print(f"[Aviso] Colunas Trace/MLP_L1D ausentes em {caminho}. MLP_L1D ficará vazio.")
            return {}
        return {
            os.path.basename(linha["Trace"]): float(linha["MLP_L1D"])
            for linha in leitor
            if linha["MLP_L1D"] and linha["MLP_L1D"].strip()
        }

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
            
        roi = dados["roi"]
        nome_trace = dados.get("traces", [os.path.basename(caminho_arquivo)])[0]
        
        instrucoes = roi["cores"][0]["instructions"]
        ciclos = roi["cores"][0]["cycles"]
        ipc = instrucoes / ciclos if ciclos > 0 else 0
        
        l1d = roi["cpu0_L1D"]
        acessos_l1d = somar_acessos(l1d, "LOAD") + somar_acessos(l1d, "WRITE")
        bytes_requisitados = acessos_l1d * 8
        ia = instrucoes / bytes_requisitados if bytes_requisitados > 0 else 0
        
        llc = roi.get("LLC", {})
        llc_misses_totais = somar_misses_reais(llc, ["LOAD", "RFO", "PREFETCH", "WRITE", "TRANSLATION"])
        llc_mpki = (llc_misses_totais / instrucoes) * 1000 if instrucoes > 0 else 0
        llc_miss_latency = llc.get("miss latency") if isinstance(llc, dict) else None

        l2d = roi.get("cpu0_L2C", {})
        l2d_misses_totais = somar_misses_reais(l2d, ["LOAD", "RFO", "PREFETCH", "WRITE", "TRANSLATION"])
        l2d_mpki = (l2d_misses_totais / instrucoes) * 1000 if instrucoes > 0 else 0
        
        return {
            "Trace_Original": nome_trace,
            "IPC": ipc,
            "CPI": ciclos / instrucoes if instrucoes > 0 else 0,
            "IA_Inst_per_Byte": ia,
            "LLC_MPKI": llc_mpki,
            "L2D_MPKI": l2d_mpki,
            "LLC_Miss_Latency": llc_miss_latency
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
            
        cpi_agregado = 0
        ia_agregado = 0
        mpki_agregado = 0
        l2d_mpki_agregado = 0
        latencias_llc_validas = [
            (peso, res["LLC_Miss_Latency"])
            for peso, res in pesos_validos
            if res["LLC_Miss_Latency"] is not None
        ]
        soma_pesos_latencia = sum(peso for peso, _ in latencias_llc_validas)
        latencia_llc_agregada = None
        if soma_pesos_latencia > 0:
            latencia_llc_agregada = sum(
                latencia * peso for peso, latencia in latencias_llc_validas
            ) / soma_pesos_latencia

        mlps_validos = [
            (peso, res["MLP_L1D"])
            for peso, res in pesos_validos
            if res.get("MLP_L1D") is not None
        ]
        soma_pesos_mlp = sum(peso for peso, _ in mlps_validos)
        mlp_agregado = None
        if soma_pesos_mlp > 0:
            mlp_agregado = sum(mlp * peso for peso, mlp in mlps_validos) / soma_pesos_mlp

        for peso, r in pesos_validos:
            peso_normalizado = peso / soma_pesos
            cpi_agregado += r["CPI"] * peso_normalizado
            ia_agregado += r["IA_Inst_per_Byte"] * peso_normalizado
            mpki_agregado += r["LLC_MPKI"] * peso_normalizado
            l2d_mpki_agregado += r["L2D_MPKI"] * peso_normalizado

        ipc_agregado = 1 / cpi_agregado if cpi_agregado > 0 else 0
            
        classificacao = "Memory-Bound" if mpki_agregado > LIMITE_MPKI else "Compute-Bound"
        
        resultados_finais.append({
            "Benchmark": core_name,
            "Classificacao": classificacao,
            "IPC": round(ipc_agregado, 4),
            "IA_Inst_per_Byte": round(ia_agregado, 4),
            "LLC_MPKI": round(mpki_agregado, 4),
            "L2D_MPKI": round(l2d_mpki_agregado, 4),
            "LLC_Miss_Latency": round(latencia_llc_agregada, 4) if latencia_llc_agregada is not None else None,
            "MLP_L1D": round(mlp_agregado, 4) if mlp_agregado is not None else None,
            "Simpoints_Usados": len(simulacoes),
            "Soma_Pesos_Original": round(soma_pesos, 4)
        })
        
    return resultados_finais

def adicionar_linha_media(resultados):
    if not resultados:
        return resultados

    metricas = ["IPC", "IA_Inst_per_Byte", "LLC_MPKI", "L2D_MPKI"]
    media = {
        metrica: round(sum(resultado[metrica] for resultado in resultados) / len(resultados), 4)
        for metrica in metricas
    }
    latencias_llc = [
        resultado["LLC_Miss_Latency"]
        for resultado in resultados
        if resultado["LLC_Miss_Latency"] is not None
    ]
    mlps = [
        resultado["MLP_L1D"]
        for resultado in resultados
        if resultado["MLP_L1D"] is not None
    ]
    resultados.append({
        "Benchmark": "Média",
        "Classificacao": "Memory-Bound" if media["LLC_MPKI"] > LIMITE_MPKI else "Compute-Bound",
        **media,
        "LLC_Miss_Latency": round(sum(latencias_llc) / len(latencias_llc), 4) if latencias_llc else None,
        "MLP_L1D": round(sum(mlps) / len(mlps), 4) if mlps else None,
        "Simpoints_Usados": "",
        "Soma_Pesos_Original": ""
    })
    return resultados

def processar_diretorio(diretorio, pesos_db):
    padrao_busca = os.path.join(diretorio, "*.json")
    arquivos = glob.glob(padrao_busca)
    
    if not arquivos:
        print(f"\n[Aviso] Nenhum arquivo JSON encontrado em: {diretorio}")
        return

    partes_caminho = os.path.normpath(diretorio).split(os.sep)
    nome_config = partes_caminho[2] if len(partes_caminho) > 2 else "desconhecido"
    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    arquivo_saida_csv = os.path.join(DIRETORIO_SAIDA, f"{nome_config}.csv")

    print(f"\nProcessando {len(arquivos)} arquivos de trace em {diretorio}...")
    resultados_individuais = []
    mlp_traces = carregar_mlp_traces(nome_config)
    
    for arq in arquivos:
        try:
            metricas = extrair_metricas(arq)
            nome_trace = os.path.basename(metricas["Trace_Original"])
            metricas["MLP_L1D"] = mlp_traces.get(nome_trace)
            if metricas["MLP_L1D"] is None and mlp_traces:
                print(f"[Aviso] MLP_L1D ausente para {nome_trace} em {nome_config}.")
            resultados_individuais.append(metricas)
        except Exception as e:
            print(f"Erro ao processar {arq}: {e}")

    resultados_agregados = agregar_resultados(resultados_individuais, pesos_db)
    resultados_agregados = sorted(resultados_agregados, key=lambda x: x["IPC"], reverse=False)
    resultados_agregados = adicionar_linha_media(resultados_agregados)

    with open(arquivo_saida_csv, 'w', newline='') as csvfile:
        campos = ["Benchmark", "Classificacao", "IPC", "IA_Inst_per_Byte", "LLC_MPKI", "L2D_MPKI", "LLC_Miss_Latency", "MLP_L1D", "Simpoints_Usados", "Soma_Pesos_Original"]
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