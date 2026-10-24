import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

METRICAS = ["LLC_MPKI", "L2D_MPKI"]
CORES_METRICAS = ["#176B87", "#E07A36"]


def main():
    parser = argparse.ArgumentParser(
        description="Gera um gráfico dos MPKIs da LLC e L2D em DDR5+LLC."
    )
    parser.add_argument(
        "--origem-dados",
        type=Path,
        default=Path("tables/1c_agregate"),
        help="Diretório dos CSVs de entrada (padrão: tables/1c_agregate).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("grafico_mpki_1c.png"),
        help="Nome ou caminho do arquivo PNG de destino.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="Resolução do PNG em pontos por polegada (padrão: 600).",
    )
    args = parser.parse_args()

    caminho_arquivo = args.origem_dados / "ddr5_llc.csv"
    try:
        df = pd.read_csv(caminho_arquivo, usecols=["Benchmark", *METRICAS])
    except FileNotFoundError:
        print(f"[Erro] Arquivo não encontrado: {caminho_arquivo}")
        return
    except ValueError as erro:
        print(f"[Erro] CSV inválido em {caminho_arquivo}: {erro}")
        return

    df = df[df["Benchmark"] != "Média"].set_index("Benchmark")
    df.sort_values("L2D_MPKI", ascending=False, inplace=True)

    plt.style.use("seaborn-v0_8-white")
    fig, ax = plt.subplots(figsize=(20, 12))
    df.plot(
        kind="bar",
        ax=ax,
        width=0.8,
        color=CORES_METRICAS,
        edgecolor="white",
        linewidth=0.8,
    )

    maior_mpki = df.max().max()
    ax.set_ylim(0, maior_mpki * 1.25 if maior_mpki > 0 else 1)
    for container in ax.containers:
        for barra in container:
            valor = barra.get_height()
            ax.annotate(
                f"{valor:.2f}",
                (barra.get_x() + barra.get_width() / 2, valor),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=24,
                rotation=90,
                clip_on=False,
            )

    ax.set_ylabel("Misses por mil instruções", fontsize=32)
    ax.set_xlabel("Benchmarks", fontsize=32)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", labelrotation=90, labelsize=28)
    ax.tick_params(axis="y", labelsize=26)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.legend(
        title="Métrica",
        fontsize=24,
        title_fontsize=24,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=len(METRICAS),
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.saida, dpi=args.dpi, bbox_inches="tight")
    print(f"Gráfico gerado com sucesso: {args.saida}")
    plt.show()


if __name__ == "__main__":
    main()