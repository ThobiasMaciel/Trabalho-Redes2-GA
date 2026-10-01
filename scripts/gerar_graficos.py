#!/usr/bin/env python3
"""
gerar_graficos.py
Le metrics/metricas_coletadas.csv e gera um grafico de barras comparativo
(RIP x OSPF x Algoritmo proprio) para cada metrica presente no arquivo.
Os graficos sao salvos como PNG dentro de metrics/graficos/.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "../metrics/metricas_coletadas.csv"
OUT_DIR = "../metrics/graficos"

METRIC_LABELS = {
    "tamanho_tabela": ("Tamanho da tabela de roteamento", "entradas"),
    "pacotes_controle": ("Pacotes de controle em 60s", "pacotes"),
    "bytes_controle": ("Bytes de controle em 60s", "bytes"),
    "taxa_transmissao": ("Taxa de transmissao de controle", "bytes/s"),
    "tempo_convergencia": ("Tempo de convergencia (teste real)", "segundos"),
}

COLORS = {
    "RIP": "#4C72B0",
    "OSPF": "#55A868",
    "ALGORITMO_PROPRIO": "#C44E52",
}


def main():
    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["valor"])

    os.makedirs(OUT_DIR, exist_ok=True)

    for metric, (titulo, unidade) in METRIC_LABELS.items():
        subset = df[df["metrica"] == metric]
        if subset.empty:
            continue

        protocolos = subset["protocolo"].tolist()
        valores = subset["valor"].astype(float).tolist()
        cores = [COLORS.get(p, "#888888") for p in protocolos]

        fig, ax = plt.subplots(figsize=(6, 4.5))
        bars = ax.bar(protocolos, valores, color=cores)

        ax.set_title(titulo)
        ax.set_ylabel(unidade)
        ax.bar_label(bars, fmt="%.1f")

        fig.tight_layout()
        out_path = os.path.join(OUT_DIR, f"{metric}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Grafico salvo: {out_path}")

    print("\nTodos os graficos foram gerados em", OUT_DIR)


if __name__ == "__main__":
    main()
