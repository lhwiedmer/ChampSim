import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CONFIGURACOES_PADRAO = ["DDR5", "DDR5+LLC", "HBM1", "HBM1+LLC", "HBM2", "HBM2+LLC", "HBM3", "HBM3+LLC", "HBM4", "HBM4+LLC"]

# Cores mantidas para diferenciar as múltiplas configurações no mesmo gráfico
CORES = {
    "DDR5": "#404040",       # Cinza escuro
    "DDR5 + LLC": "#808080", "HBM1": "#ff7f0e", "HBM1 + LLC": "#2ca02c",
    "HBM2": "#1f77b4", "HBM2 + LLC": "#d62728", "HBM3": "#9467bd",
    "HBM3 + LLC": "#8c564b", "HBM4": "#e377c2", "HBM4 + LLC": "#7f7f7f",
}

def normalizar_configuracao(configuracao):
    config = configuracao.strip().lower().replace("+", "_").replace(" ", "_")
    base = {f"hbm{i}" for i in range(1, 5)} | {"ddr5"}
    if config not in base and not (config.endswith("_llc") and config[:-4] in base):
        raise ValueError(f"Configuração inválida: {configuracao}")
    return config

def nome_configuracao(configuracao):
    return configuracao.replace("_", " + ").upper()

def carregar_dados(origem_dados, configuracoes):
    dfs = {}
    for configuracao in configuracoes:
        nome = nome_configuracao(configuracao)
        arquivo = f"{configuracao}.csv"
        caminho_arquivo = origem_dados / arquivo
        try:
            df = pd.read_csv(caminho_arquivo)
            df.set_index("Trace", inplace=True)
            df = df.loc[~df.index.astype(str).str.lower().isin(["média", "media", "resumo"])]
            dfs[nome] = df["Weighted_Speedup"]
        except FileNotFoundError:
            print(f"[Erro] Arquivo não encontrado: {caminho_arquivo}")
    return dfs

def main():
    parser = argparse.ArgumentParser(description="Gera o gráfico de speedup dos traces de 8 núcleos.")
    parser.add_argument(
        "--origem-dados",
        type=Path,
        default=Path("tables/8c"),
        help="Diretório que contém os arquivos CSV de entrada (padrão: tables/8c).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("grafico_speedup_8c.png"),
        help="Nome ou caminho do arquivo PNG de destino.",
    )
    parser.add_argument("--configuracoes", nargs="+", default=CONFIGURACOES_PADRAO, help="Configurações a comparar.")
    parser.add_argument(
        "--baseline",
        default="DDR5+LLC",
        help="Configuração de referência a incluir como barra (padrão: DDR5+LLC).",
    )
    args = parser.parse_args()

    try:
        configuracoes = [normalizar_configuracao(config) for config in args.configuracoes]
        baseline = normalizar_configuracao(args.baseline)
        configuracoes = list(dict.fromkeys(configuracoes))
        configuracoes = ["ddr5_llc"] + [
            config for config in configuracoes if config != "ddr5_llc"
        ]
        if baseline not in configuracoes:
            configuracoes.append(baseline)
    except ValueError as erro:
        parser.error(str(erro))
    nomes = {config: nome_configuracao(config) for config in configuracoes}
    nome_baseline = nome_configuracao(baseline)
    dfs = carregar_dados(args.origem_dados, configuracoes)
    if not dfs or nome_baseline not in dfs:
        print("Dados insuficientes para gerar o gráfico.")
        return

    df_weighted_speedup = pd.DataFrame(dfs)
    df_weighted_speedup = df_weighted_speedup.dropna()

    df_plot = pd.DataFrame(index=df_weighted_speedup.index)
    
    for config in configuracoes:
        nome = nomes[config]
        if nome in df_weighted_speedup:
            df_plot[nome] = df_weighted_speedup[nome]

    medias_aritmeticas = df_plot.mean(axis=0)
    ordenacao = df_plot.mean(axis=1)
    df_plot = df_plot.loc[ordenacao.sort_values(ascending=False).index]
    df_plot.loc["Média Aritmética"] = medias_aritmeticas

    # 3. Configurar e Gerar o Gráfico
    plt.style.use('seaborn-v0_8-white') # Estilo mais limpo, fundo totalmente branco
    
    fig, ax = plt.subplots(figsize=(20, 12))

    # Plota as barras agrupadas
    df_plot.plot(
        kind='bar', 
        ax=ax, 
        width=0.8, 
        color=[CORES.get(c, "#333333") for c in df_plot.columns],
        edgecolor='white',
        linewidth=1
    )

    max_y = df_plot.max().max()
    margem_superior = max_y * 0.15
    ax.set_ylim(0, max_y + margem_superior)

    # --- Adicionando os números formatados como "1.xx" ---
    for container in ax.containers:
        for bar in container:
            valor = bar.get_height()
            
            if pd.isna(valor) or valor == 0:
                continue
                
            ax.text(
                bar.get_x() + bar.get_width() / 2, 
                valor + (max_y * 0.015),           # Distância curta acima da barra
                f"{valor:.2f}",                    # Formato com 2 casas (ex: 1.25)
                ha='center',                       
                va='bottom',                             
                fontsize=16,                        
                rotation=90,
                color='#111111'
            )

    # Estilização
    ax.set_ylabel("Weighted Speedup", fontsize=24)
    ax.set_xlabel("Aplicações", fontsize=24)
    
    # Grid horizontal cinza claro, eixo atrás das barras
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#e0e0e0', linestyle='-', linewidth=1)
    ax.grid(axis='x', visible=False)

    # Rotaciona os rótulos do eixo X em 90 graus
    plt.xticks(rotation=90, ha='center', fontsize=22)
    plt.yticks(np.arange(0, ax.get_ylim()[1], 1.0), fontsize=20)

    # Remove bordas superior e direita para visual mais limpo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')

    ax.legend(
        title="",
        fontsize=14,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=max(1, len(df_plot.columns)),
    )

    plt.tight_layout(rect=(0, 0, 1, 0.92))

    # Salva com alta resolução
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.saida, dpi=300, bbox_inches='tight')
    print(f"Gráfico gerado com sucesso: {args.saida}")
    
    plt.show()

if __name__ == "__main__":
    main()