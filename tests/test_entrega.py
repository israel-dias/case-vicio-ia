import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from finalizar_case import COLUNAS, gerar
from gerar_respostas_salvas import gerar as formatar
from importar_todos_v3 import conferir_execucao, executar

ROOT = Path(__file__).resolve().parents[1]


class TestEntrega(unittest.TestCase):
    def test_exportacao_completa_e_reproducao_exata(self):
        with tempfile.TemporaryDirectory() as td:
            destino = Path(td)
            resultado = gerar(ROOT, destino)
            self.assertEqual(resultado["questoes"], 359)
            self.assertIsNone(resultado["precisao_medida"])
            with (destino / "publicacao.csv").open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, COLUNAS)
                linhas = list(reader)
            self.assertEqual({r["id"] for r in linhas}, {f"Q{i:04}" for i in range(1, 360)})
            self.assertEqual(len(linhas), 359)
            self.assertEqual((destino / "publicacao.csv").read_bytes(), (ROOT / "publicacao.csv").read_bytes())
            self.assertEqual((destino / "previsao.txt").read_bytes(), (ROOT / "previsao.txt").read_bytes())
            for r in linhas:
                self.assertTrue(0 <= float(r["confianca"]) <= 1)
                if r["decisao"] == "fora":
                    self.assertFalse(r["tema_central_id"])
                else:
                    self.assertTrue(r["tema_central_id"])

    def test_sobrescrita_da_entrega_e_rejeitada(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "publicacao.csv").write_text("versao_anterior", encoding="utf-8")
            with self.assertRaises(ValueError):
                gerar(ROOT, p)
            self.assertEqual((p / "publicacao.csv").read_text(), "versao_anterior")

    def test_importacao_repetida_preserva_execucoes(self):
        resultado = executar(ROOT)
        self.assertEqual(resultado["novas_importacoes"], 0)
        self.assertEqual(resultado["questoes_v3"], 339)

    def test_alteracao_de_resposta_mesmo_so_espaco_e_detectada(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            shutil.copytree(ROOT / "lotes_v3/lote_001", p / "lote")
            shutil.copytree(ROOT / "execucoes/v3/lote_001", p / "execucao")
            shutil.copyfile(ROOT / "respostas_v3/lote_001.json", p / "resposta.json")
            conferir_execucao(p / "execucao", p / "lote", p / "resposta.json")
            with (p / "resposta.json").open("a") as f:
                f.write(" ")
            with self.assertRaises(ValueError):
                conferir_execucao(p / "execucao", p / "lote", p / "resposta.json")

    def test_formatacao_de_anotacoes_nao_e_nova_inferencia(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            resultado = formatar(ROOT, p)
            self.assertEqual(resultado["questoes"], 329)
            self.assertFalse(resultado["nova_inferencia_realizada"])
            for numero in range(2, 35):
                nome = f"lote_{numero:03}.json"
                self.assertEqual((p / nome).read_bytes(), (ROOT / "respostas_v3" / nome).read_bytes())


if __name__ == "__main__":
    unittest.main()
