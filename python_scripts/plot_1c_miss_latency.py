import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CONFIGURACOES = [
    "ddr5_llc",
    "hbm1_llc",
    "hbm2_llc",
    "hbm3_llc",
    "hbm4_llc",
]
CORES = [
    "#808080",
    "#2ca02c",
    "#d62728",
    "#8c564b",
    "#17becf",
]
METRICA = "LLC_Miss_Latency"


def main():
    parser = argparse.ArgumentParser(
        description="Gera um gráfico da miss latency média da LLC por configuração."
    )
    parser.add_argument(
        "--origem-dados",
        type=Path,
        default=Path("tables/1c_agregate"),
        help="Diretório dos CSVs agregados (padrão: tables/1c_agregate).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("grafico_miss_latency_1c.png"),
        help="Nome ou caminho do arquivo PNG de destino.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="Resolução do PNG em pontos por polegada (padrão: 600).",
    )
    args = parser.parse_args()

    configuracoes_validas = []
    medias = []
    for configuracao in CONFIGURACOES:
        caminho_csv = args.origem_dados / f"{configuracao}.csv"
        try:
            dados = pd.read_csv(caminho_csv, usecols=["Benchmark", METRICA])
        except FileNotFoundError:
            print(f"[Aviso] Arquivo não encontrado: {caminho_csv}")
            continue
        except ValueError as erro:
            print(f"[Aviso] CSV sem a métrica {METRICA}: {caminho_csv} ({erro})")
            continue

        benchmarks = dados.loc[dados["Benchmark"] != "Média", METRICA]
        benchmarks = pd.to_numeric(benchmarks, errors="coerce").dropna()
        if benchmarks.empty:
            print(f"[Aviso] Nenhuma miss latency válida em {caminho_csv}")
            continue

        configuracoes_validas.append(configuracao.replace("_", " + ").upper())
        medias.append(benchmarks.mean())

    if not medias:
        print("[Erro] Nenhuma miss latency disponível para gerar o gráfico.")
        return

    plt.style.use("seaborn-v0_8-white")
    fig, ax = plt.subplots(figsize=(14, 8))
    barras = ax.bar(
        configuracoes_validas,
        medias,
        color=[CORES[CONFIGURACOES.index(config.replace(" + ", "_").lower())] for config in configuracoes_validas],
        edgecolor="white",
        linewidth=0.8,
    )

    maior_media = max(medias)
    ax.set_ylim(0, maior_media * 1.15 if maior_media > 0 else 1)
    for barra, valor in zip(barras, medias):
        ax.annotate(
            f"{valor:.2f}",
            (barra.get_x() + barra.get_width() / 2, valor),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
        )

    ax.set_ylabel("Miss latency média da LLC (ciclos)")
    ax.set_xlabel("Configuração")
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", labelrotation=30)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    fig.tight_layout()

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.saida, dpi=args.dpi, bbox_inches="tight")
    print(f"Gráfico gerado com sucesso: {args.saida}")
    plt.show()


if __name__ == "__main__":
    main()