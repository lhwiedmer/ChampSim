import contextlib
import csv
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from python_scripts import agregate


class TestMLPAgregado(unittest.TestCase):
    def setUp(self):
        self.resultados = [
            {
                "Trace_Original": f"traces/605.mcf_s-{sp}B.champsimtrace.xz",
                "CPI": cpi,
                "IA_Inst_per_Byte": 0.25,
                "LLC_MPKI": 3.0,
                "L2D_MPKI": 5.0,
                "LLC_Miss_Latency": 100.0,
                "MLP_L1D": mlp,
            }
            for sp, cpi, mlp in [(1, 2.0, 2.0), (2, 4.0, 6.0)]
        ]
        self.pesos = {"605.mcf_s": {"1": 0.2, "2": 0.6}}

    def test_media_ponderada_normalizada_preserva_metricas(self):
        resultado = agregate.agregar_resultados(self.resultados, self.pesos)[0]
        self.assertEqual(resultado["MLP_L1D"], 5.0)
        self.assertEqual(resultado["IPC"], round(1 / 3.5, 4))
        self.assertEqual(resultado["LLC_MPKI"], 3.0)
        self.assertEqual(resultado["L2D_MPKI"], 5.0)
        self.assertEqual(resultado["LLC_Miss_Latency"], 100.0)

    def test_sem_pesos_usa_media_simples(self):
        with contextlib.redirect_stdout(io.StringIO()):
            resultado = agregate.agregar_resultados(self.resultados, {})[0]
        self.assertEqual(resultado["MLP_L1D"], 4.0)

    def test_ausente_nao_e_zero_e_zero_e_valido(self):
        self.resultados[0]["MLP_L1D"] = None
        self.resultados[1]["MLP_L1D"] = 0.0
        resultado = agregate.agregar_resultados(self.resultados, self.pesos)
        self.assertEqual(resultado[0]["MLP_L1D"], 0.0)
        self.assertEqual(agregate.adicionar_linha_media(resultado)[-1]["MLP_L1D"], 0.0)
        self.resultados[1]["MLP_L1D"] = None
        resultado = agregate.agregar_resultados(self.resultados, self.pesos)
        self.assertIsNone(resultado[0]["MLP_L1D"])
        self.assertIsNone(agregate.adicionar_linha_media(resultado)[-1]["MLP_L1D"])

    def test_linha_media_ignora_ausentes(self):
        resultado = agregate.agregar_resultados(self.resultados, self.pesos)
        resultado.extend([
            {**resultado[0], "MLP_L1D": 3.0},
            {**resultado[0], "MLP_L1D": None},
        ])
        self.assertEqual(agregate.adicionar_linha_media(resultado)[-1]["MLP_L1D"], 4.0)

    def test_csv_por_configuracao_e_saida_integrada(self):
        with tempfile.TemporaryDirectory() as pasta:
            tabela = os.path.join(pasta, "hbm4.csv")
            with open(tabela, "w", newline="") as arquivo:
                writer = csv.DictWriter(arquivo, fieldnames=["Trace", "MLP_L1D"])
                writer.writeheader()
                writer.writerows(
                    {"Trace": r["Trace_Original"], "MLP_L1D": r["MLP_L1D"]}
                    for r in self.resultados
                )
            saida = os.path.join(pasta, "saida")
            with (
                patch.object(agregate, "DIRETORIO_TRACES", pasta),
                patch.object(agregate, "DIRETORIO_SAIDA", saida),
                patch.object(agregate.glob, "glob", return_value=["1.json", "2.json"]),
                patch.object(agregate, "extrair_metricas", side_effect=[
                    {**r, "Trace_Original": r["Trace_Original"].replace("traces/", "/outros/traces/")}
                    for r in self.resultados
                ]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                agregate.processar_diretorio("results/1c/hbm4/champsim", self.pesos)
            with open(os.path.join(saida, "hbm4.csv"), newline="") as arquivo:
                linhas = list(csv.DictReader(arquivo))
            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[0]["MLP_L1D"], "5.0")
            self.assertEqual(linhas[1]["MLP_L1D"], "5.0")

    def test_tabela_ausente_ou_sem_coluna_emite_aviso(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(agregate, "DIRETORIO_TRACES", pasta):
            for conteudo in [None, "Trace,IPC\ntrace,1.0\n"]:
                if conteudo is not None:
                    with open(os.path.join(pasta, "hbm4.csv"), "w") as arquivo:
                        arquivo.write(conteudo)
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(agregate.carregar_mlp_traces("hbm4"), {})
                self.assertIn("[Aviso]", output.getvalue())


if __name__ == "__main__":
    unittest.main()
