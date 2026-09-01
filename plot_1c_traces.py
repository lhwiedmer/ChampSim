import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Configurações
ARQUIVOS = {
    "DDR5": "classificacao_traces_ddr5.csv",
    "Baseline (DDR5 + LLC)": "classificacao_traces_ddr5_llc.csv",
    "HBM4": "classificacao_traces_hbm4.csv",
    "HBM4 + LLC": "classificacao_traces_hbm4_llc.csv"
}

NOME_BASELINE = "Baseline (DDR5 + LLC)"

# Cores mantidas para diferenciar as múltiplas configurações no mesmo gráfico
CORES = {
    "DDR5": "#404040",       # Cinza escuro
    "HBM4": "#ff7f0e",       # Laranja
    "HBM4 + LLC": "#2ca02c"  # Verde
}

def carregar_dados():
    dfs = {}
    for nome, arquivo in ARQUIVOS.items():
        try:
            df = pd.read_csv(arquivo)
            df.set_index("Trace", inplace=True)
            dfs[nome] = df["IPC"]
        except FileNotFoundError:
            print(f"[Erro] Arquivo não encontrado: {arquivo}")
    return dfs

def main():
    dfs = carregar_dados()
    if not dfs or NOME_BASELINE not in dfs:
        print("Dados insuficientes para gerar o gráfico.")
        return

    df_ipc = pd.DataFrame(dfs)

    # 2. Calcular o Speedup (Formato 1.x)
    df_speedup = pd.DataFrame(index=df_ipc.index)
    
    for config in ARQUIVOS.keys():
        if config != NOME_BASELINE:
            # Divisão direta: IPC / Baseline IPC (ex: resulta em 1.25, 0.95, 1.00)
            df_speedup[config] = df_ipc[config] / df_ipc[NOME_BASELINE]

    # Ordenar o eixo X pela média de speedup (decrescente, similar à imagem)
    df_speedup["Media"] = df_speedup.mean(axis=1)
    df_speedup.sort_values("Media", ascending=False, inplace=True)
    df_speedup.drop(columns=["Media"], inplace=True)

    # 3. Configurar e Gerar o Gráfico
    plt.style.use('seaborn-v0_8-white') # Estilo mais limpo, fundo totalmente branco
    
    fig, ax = plt.subplots(figsize=(20, 8))

    # Plota as barras agrupadas
    df_speedup.plot(
        kind='bar', 
        ax=ax, 
        width=0.8, 
        color=[CORES[c] for c in df_speedup.columns],
        edgecolor='white',
        linewidth=1
    )

    # Linha de referência em 1.0 (Baseline)
    ax.axhline(1.0, color='black', linewidth=1.2, linestyle='-', alpha=0.5)

    # Limites do eixo Y (iniciando no 0.0)
    max_y = df_speedup.max().max()
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
                fontsize=10,                        
                rotation=0,                        # Texto horizontal como na imagem
                color='#111111'
            )

    # Estilização
    ax.set_ylabel("Speedup", fontsize=16)
    ax.set_xlabel("Applications", fontsize=16)
    
    # Grid horizontal cinza claro, eixo atrás das barras
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#e0e0e0', linestyle='-', linewidth=1)
    ax.grid(axis='x', visible=False)

    # Rotaciona os rótulos do eixo X em 90 graus
    plt.xticks(rotation=90, ha='center', fontsize=14)
    plt.yticks(np.arange(0, ax.get_ylim()[1], 0.2), fontsize=14) # Intervalos de 0.2

    # Remove bordas superior e direita para visual mais limpo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')

    ax.legend(title="", fontsize=14, loc='upper right')

    plt.tight_layout()

    # Salva com alta resolução
    nome_saida = "grafico_speedup_academico.png"
    plt.savefig(nome_saida, dpi=300, bbox_inches='tight')
    print(f"Gráfico gerado com sucesso: {nome_saida}")
    
    plt.show()

if __name__ == "__main__":
    main()