import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Configurações
ARQUIVOS = {
    "DDR5": "classificacao_benchmarks_agregado_ddr5.csv",
    "Baseline (DDR5 + LLC)": "classificacao_benchmarks_agregado_ddr5_llc.csv",
    "HBM4": "classificacao_benchmarks_agregado_hbm4.csv",
    "HBM4 + LLC": "classificacao_benchmarks_agregado_hbm4_llc.csv"
}

NOME_BASELINE = "Baseline (DDR5 + LLC)"

CORES = {
    "DDR5": "#1f77b4",       # Azul
    "HBM4": "#ff7f0e",       # Laranja
    "HBM4 + LLC": "#2ca02c"  # Verde
}

def carregar_dados():
    dfs = {}
    for nome, arquivo in ARQUIVOS.items():
        try:
            df = pd.read_csv(arquivo)
            df.set_index("Benchmark", inplace=True)
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

    # 2. Calcular o Speedup Relativo em porcentagem
    df_speedup = pd.DataFrame(index=df_ipc.index)
    
    for config in ARQUIVOS.keys():
        if config != NOME_BASELINE:
            df_speedup[config] = ((df_ipc[config] / df_ipc[NOME_BASELINE]) - 1) * 100

    # Ordenar o eixo X pela média de speedup
    df_speedup["Media"] = df_speedup.mean(axis=1)
    df_speedup.sort_values("Media", inplace=True)
    df_speedup.drop(columns=["Media"], inplace=True)

    # 3. Configurar e Gerar o Gráfico
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # AUMENTADO: Imagem mais larga (20) e um pouco mais alta (9)
    fig, ax = plt.subplots(figsize=(20, 9))

    # Plota as barras agrupadas
    df_speedup.plot(
        kind='bar', 
        ax=ax, 
        width=0.85, 
        color=[CORES[c] for c in df_speedup.columns],
        edgecolor='black',
        linewidth=0.5
    )

    # Linha horizontal no zero
    ax.axhline(0, color='black', linewidth=1.2, linestyle='-')

    # --- NOVO: Adicionando os números em cada barra ---
    espacamento_texto = 0.5 # Distância entre o topo da barra e o texto
    
    for container in ax.containers:
        for bar in container:
            valor = bar.get_height()
            
            # Pula se o valor for exatamente zero ou nulo
            if pd.isna(valor) or valor == 0:
                continue
                
            # Define se o texto vai acima ou abaixo da barra dependendo se é speedup/slowdown
            if valor > 0:
                y_pos = valor + espacamento_texto
                va = 'bottom'
            else:
                y_pos = valor - espacamento_texto
                va = 'top'
                
            ax.text(
                bar.get_x() + bar.get_width() / 2, # Posição X (centro da barra)
                y_pos,                             # Posição Y
                f"{valor:.1f}%",                   # Formato do texto (ex: 12.3%)
                ha='center',                       # Alinhamento horizontal
                va=va,                             # Alinhamento vertical
                fontsize=9,                        # Tamanho da fonte dos números
                rotation=90,                       # Rotaciona 90 graus para caber
                fontweight='bold',
                color='#333333'
            )

    # --- NOVO: Ajustando limites do eixo Y para os números não cortarem ---
    min_y = df_speedup.min().min()
    max_y = df_speedup.max().max()
    
    # Adiciona uma margem de 15% acima do maior valor e 15% abaixo do menor valor
    margem_y = max(abs(max_y), abs(min_y)) * 0.15
    ax.set_ylim(min_y - margem_y if min_y < 0 else 0, max_y + margem_y)

    # Estilização
    ax.set_title("Speedup Relativo ao Baseline (DDR5 + LLC)", fontsize=18, pad=20, fontweight='bold')
    ax.set_ylabel("Ganho / Perda de Desempenho (%)", fontsize=14, fontweight='bold')
    ax.set_xlabel("Benchmarks (SPEC CPU)", fontsize=14, fontweight='bold')
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.grid(axis='x', visible=False)

    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)

    ax.legend(title="Configurações", fontsize=12, title_fontsize=13, loc='best')

    plt.tight_layout()

    # Salva com alta qualidade
    nome_saida = "grafico_speedup_hbm_ddr5_anotado.png"
    plt.savefig(nome_saida, dpi=300, bbox_inches='tight')
    print(f"Gráfico gerado com sucesso: {nome_saida}")
    
    plt.show()

if __name__ == "__main__":
    main()