import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from gerar_visor import gerar, montar_dados, serializar_dados, verificar_entrega

ROOT = Path(__file__).resolve().parents[1]


class RecursosHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.externos = []

    def handle_starttag(self, tag, attrs):
        valores = dict(attrs)
        if tag == "script" and valores.get("src"):
            self.externos.append(valores["src"])
        if tag == "link" and valores.get("rel") == "stylesheet":
            self.externos.append(valores.get("href"))


class TestVisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = montar_dados(ROOT)

    def test_visor_preserva_todas_as_decisoes_e_textos_sem_inventar_confirmacoes(self):
        with (ROOT / "publicacao.csv").open(encoding="utf-8", newline="") as f:
            linhas = {r["id"]: r for r in csv.DictReader(f)}
        questoes = {q["id"]: q for q in map(json.loads,
                    (ROOT / "dados/processados/questoes_preparadas.jsonl").read_text().splitlines())}
        registros = self.dados["registros"]
        self.assertEqual(len(registros), len(linhas))
        for r in registros:
            self.assertEqual(r["questao"], questoes[r["id"]])
            self.assertEqual({k: r["atual"][k] for k in linhas[r["id"]]}, linhas[r["id"]])
        por_id = {r["id"]: r for r in registros}
        self.assertEqual(por_id["Q0298"]["questao"]["alternativas"], {"C": "Certo", "E": "Errado"})
        self.assertEqual(por_id["Q0355"]["estado_resposta"], "gabarito_oficial_definitivo")
        self.assertEqual(por_id["Q0355"]["atual"]["decisao"], "revisar")
        self.assertIsNone(por_id["Q0219"]["resposta"])
        self.assertIsNone(self.dados["meta"]["precisao_medida"])

    def test_texto_hostil_nao_fecha_o_bloco_json_e_e_preservado_na_decodificacao(self):
        hostil = {"texto": '</script><img src=x onerror="alert(1)"> & \u2028 \u2029'}
        serializado = serializar_dados(hostil)
        self.assertNotIn("<", serializado)
        self.assertNotIn("&", serializado)
        self.assertEqual(json.loads(serializado), hostil)

    def test_html_e_reproduzivel_autossuficiente_e_preserva_a_entrega(self):
        originais = {nome: (ROOT / nome).read_bytes() for nome in ("publicacao.csv", "previsao.txt")}
        with tempfile.TemporaryDirectory() as td:
            saida = Path(td) / "visor.html"
            gerar(ROOT, saida)
            primeira = saida.read_bytes()
            gerar(ROOT, saida)
            self.assertEqual(primeira, saida.read_bytes())
            html = saida.read_text(encoding="utf-8")
            incorporado = re.search(r'<script type="application/json" id="base-auditoria">(.*?)</script>', html, re.S)
            self.assertIsNotNone(incorporado)
            self.assertEqual(json.loads(incorporado.group(1)), self.dados)
            self.assertNotIn("<!-- VICIO_", html)
            recursos = RecursosHTML()
            recursos.feed(html)
            self.assertEqual(recursos.externos, [])
        for nome, conteudo in originais.items():
            self.assertEqual((ROOT / nome).read_bytes(), conteudo)

    def test_csv_da_raiz_divergente_e_rejeitado_antes_de_apresentar_os_dados(self):
        with tempfile.TemporaryDirectory() as td:
            copia = Path(td) / "case"
            shutil.copytree(ROOT, copia, ignore=shutil.ignore_patterns(
                "__pycache__", ".venv", "*.pyc", "index.html", "entrega_reproduzida*"))
            with (copia / "publicacao.csv").open("a", encoding="utf-8") as f:
                f.write("\n")
            with self.assertRaisesRegex(ValueError, "publicacao.csv da raiz diverge"):
                verificar_entrega(copia)


if __name__ == "__main__":
    unittest.main()
