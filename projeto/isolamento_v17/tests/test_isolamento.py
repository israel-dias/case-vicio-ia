import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from compatibilidade_v2 import features as f
from melhorias_v3.experimento import validar_grupos
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from isolamento_v17 import modelo as m
from isolamento_v17.metricas import medir, curva_descritiva


class TestComparadores(unittest.TestCase):
    def setUp(self):
        self.cat = SimpleNamespace(familias=[str(j) for j in range(1, 7)],
                                  temas={str(j): {"parent_id": ""} for j in range(1, 7)})
        x = np.zeros((6, len(m.ATRIBUTOS["v15"])))
        x[:, 0] = [.5, .6, .7, .8, .9, 100]
        y = np.zeros((6, len(m.ATRIBUTOS["v11"])))
        y[:, 0] = [.9, .8, .7, .6, .5, 100]
        self.p = {"x": x, "x_v11": y, "candidatos": [0, 1, 2, 3, 4],
                  "rota": {"sem_evidencia": False}, "sinal_textual": np.arange(6),
                  "homonimos": {t: [] for t in self.cat.familias}, "hash": "texto"}

    def mod(self, comparador):
        n = len(m.ATRIBUTOS[comparador])
        return {"dimensao": n, "media": [0]*n, "escala": [1]*n,
                "coeficientes": [1]+[0]*(n-1), "intercepto": 0}

    def test_mesmos_cinco_candidatos_e_mudanca_apenas_do_comparador(self):
        r = {v: m.sinais({"nova": self.p}, self.mod(m.COMPARADOR[v]), self.cat, v)[0] for v in m.VARIANTES}
        self.assertEqual(r["primeiro_fusao_v15"]["tema_central_id"], "1")
        self.assertEqual(r["reordenar_v11"]["tema_central_id"], "1")
        self.assertEqual(r["reordenar_v15"]["tema_central_id"], "5")
        self.assertEqual({z["candidatos_ids"] for z in r.values()}, {"1;2;3;4;5"})
        self.assertNotIn("6", [z["tema_central_id"] for z in r.values()])

    def test_rotulo_nao_e_argumento_da_selecao(self):
        with patch.object(f, "aceito", side_effect=AssertionError("rótulo")):
            self.assertEqual(m.sinais({"nova": self.p}, self.mod("v15"), self.cat, "reordenar_v15")[0]["tema_central_id"], "5")

    def test_empate_preserva_ordem_recuperada_em_vez_de_id(self):
        self.p["x"][:, 0] = .5
        self.p["candidatos"] = [4, 3, 2, 1, 0]
        r = m.sinais({"q": self.p}, self.mod("v15"), self.cat, "reordenar_v15")[0]
        self.assertEqual(r["tema_central_id"], "5")

    def test_homonimo_pendente_bloqueia_todos_os_comparadores(self):
        self.p["x"][:, 0] = .6
        self.p["x_v11"][:, 0] = .6
        self.p["sinal_textual"][:] = .5
        self.p["homonimos"]["1"] = ["2"]
        for v in m.VARIANTES:
            r = m.sinais({"q": self.p}, self.mod(m.COMPARADOR[v]), self.cat, v)[0]
            self.assertFalse(r["elegivel"])
            self.assertIn("homonimo", r["motivos_bloqueio"])

    def test_treino_rejeita_rotulos_externos(self):
        with self.assertRaisesRegex(ValueError, "outro conjunto"):
            m.ajustar({"q": self.p}, {"outra": {}}, self.cat, "v15")

    def test_duplicata_entre_grupos_e_rejeitada_sem_redistribuicao(self):
        with self.assertRaisesRegex(ValueError, "duplicado"):
            validar_grupos({"a": self.p, "b": self.p}, ["a"], ["b"], ["a", "b"])

    def test_calibracao_controla_probabilidade_sem_bonus_fixo(self):
        pack = {"atributos": m.ATRIBUTOS["v15"], "modelo": self.mod("v15"),
                "calibrador": {"dimensao": 1, "constante": .6},
                "politica": {"ativa": True, "limiar": .8}}
        r = m.aplicar({"q": self.p}, pack, self.cat, "reordenar_v15")[0]
        self.assertEqual(r["confianca"], .6)
        self.assertEqual(r["decisao"], "revisar")
        self.assertEqual(r["motivo"], "abaixo_do_limiar_calibrado")

    def test_sem_politica_com_suporte_nao_publica(self):
        pack = {"atributos": m.ATRIBUTOS["v15"], "modelo": self.mod("v15"),
                "calibrador": {"dimensao": 1, "constante": .99},
                "politica": {"ativa": False, "limiar": None}}
        r = m.aplicar({"q": self.p}, pack, self.cat, "primeiro_fusao_v15")[0]
        self.assertEqual(r["motivo"], "sem_politica_com_suporte")

    def test_selecao_interna_nao_recebe_acertos_externos(self):
        p = {v: {"politica": {"suporte_interno": n}} for v, n in zip(m.VARIANTES, [15, 20, 10])}
        ss = {v: [{"correto": 1}] for v in m.VARIANTES}
        self.assertEqual(m.escolher_internamente(p, ss), "reordenar_v11")

    def test_regua_preserva_ancestrais_sem_aceitar_irmaos(self):
        temas = {"1": {"parent_id": ""}, "2": {"parent_id": "1"}, "3": {"parent_id": "1"}}
        self.assertTrue(m.mesmo_ramo("1", "2", temas))
        self.assertFalse(m.mesmo_ramo("2", "3", temas))


class TestMetricas(unittest.TestCase):
    def linha(self, i, correto, publicar, tema="1"):
        return {"id": i, "tema_central_id": tema, "decisao": "publicar" if publicar else "revisar",
                "confianca": .9, "elegivel": True, "correto": correto, "fora_oficial": 1-correto}

    def test_adicoes_nao_ficam_escondidas_no_total_e_fora_e_erro(self):
        base = [self.linha("a", 1, True), self.linha("b", 0, False)]
        novo = [self.linha("a", 1, False), self.linha("b", 0, True)]
        r = medir(novo, base)
        self.assertEqual(r["novas_erradas"], 1)
        self.assertEqual(r["acertos_perdidos"], 1)
        self.assertEqual(r["fora_oficial_publicadas"], 1)
        self.assertEqual(r["uniao_descritiva_nao_ativada"]["precisao_desenvolvimento"], .5)

    def test_sem_publicadas_precisao_indefinida(self):
        self.assertIsNone(medir([self.linha("q", 1, False)])["precisao_desenvolvimento"])

    def test_sem_rotulo_nao_inventa_precisao(self):
        r = self.linha("q", 1, True)
        del r["correto"]
        del r["fora_oficial"]
        z = medir([r])
        self.assertIsNone(z["precisao_real_alvo"])
        self.assertNotIn("precisao_desenvolvimento", z)

    def test_curva_descritiva_nao_e_nova_escolha_de_limiar(self):
        r = curva_descritiva([self.linha("q", 1, True)])
        self.assertEqual(len(r), 101)
        self.assertIsNone(r[-1]["precisao"])


class TestRepresentacaoReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projeto = Path(__file__).resolve().parents[2]
        cls.cat, _ = carregar_catalogo(cls.projeto)
        cls.dic = Dicionario(json.loads((cls.projeto/"vocabulario_v8/dicionario.json").read_text()), cls.cat.temas, cls.cat.familias)

    def test_trocar_id_preserva_candidatos_atributos_e_texto(self):
        q = {"id": "nova", "enunciado_html": "A respeito da interceptação telefônica, julgue a assertiva.",
             "comando": "", "alternativas": {"C": "Certo", "E": "Errado"},
             "disciplina_origem": "Processo Penal", "assunto_origem": "Provas"}
        with patch.object(f, "carregar", side_effect=AssertionError("folha verdade")):
            pp = m.preparar(self.cat, self.dic, {"nova": q, "novo_id": {**q, "id": "novo_id"}})
        for n in ["x", "x_v11", "ranking"]:
            np.testing.assert_array_equal(pp["nova"][n], pp["novo_id"][n])
        self.assertEqual(pp["nova"]["candidatos"], pp["novo_id"]["candidatos"])
        self.assertEqual(pp["nova"]["candidatos"], [int(k) for k in f.ordenar(pp["nova"]["ranking"])[:5]])


if __name__ == "__main__":
    unittest.main()
