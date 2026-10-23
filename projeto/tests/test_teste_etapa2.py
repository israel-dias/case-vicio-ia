import copy
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import avaliar_teste_etapa2 as m
from test_calibracao_etapa2 import fixture


def preparar(pasta):
    dados, metodo, escopos, vocab = fixture(pasta)
    destino = pasta / "calibracao"
    m.cal.executar(dados, metodo, escopos, vocab, destino)
    return dados, metodo, destino / "politica_congelada.json", escopos, vocab


def linha(qid, certa, decisao="publicar", ramo="Penal", confianca=.8):
    return {"id": qid, "acerto_top1": certa, "decisao": decisao,
            "ramo_referencia": ramo, "confianca": confianca}


def politica_minima():
    return {"confianca_por_decisao": {"publicar": {"media_beta_1_1": .8}}}


class TestTesteEtapa2(unittest.TestCase):
    def test_precisao_e_cobertura_tem_denominadores_diferentes(self):
        registros = [linha("A", True), linha("B", True), linha("C", False, "revisar"), linha("D", False, "revisar")]
        r = m.resumir_teste(registros, politica_minima())
        self.assertEqual(r["precisao_publicadas"], 1.)
        self.assertEqual(r["cobertura"], .5)
        self.assertEqual(r["acerto_top1_todas"], .5)
        self.assertFalse(r["minimo_95_sustentado_por_limite_unilateral"])

    def test_zero_publicadas_nao_vira_precisao_cem_porcento(self):
        r = m.resumir_teste([linha("A", True, "revisar")], politica_minima())
        self.assertIsNone(r["precisao_publicadas"])
        self.assertIsNone(r["meta_95_atingida_na_amostra"])
        self.assertEqual(r["cobertura"], 0.)
        self.assertEqual(r["intervalo_binomial_95_publicadas"], [0., 1.])

    def test_meta_na_amostra_nao_significa_minimo_populacional_comprovado(self):
        r = m.resumir_teste([linha(str(i), True) for i in range(20)], politica_minima())
        self.assertTrue(r["meta_95_atingida_na_amostra"])
        self.assertFalse(r["minimo_95_sustentado_por_limite_unilateral"])
        self.assertLess(r["limite_inferior_unilateral_95"], .95)

    def test_erro_de_publicacao_conta_e_nao_muda_a_politica(self):
        politica = politica_minima(); antes = copy.deepcopy(politica)
        r = m.resumir_teste([linha("A", True), linha("B", False)], politica)
        self.assertEqual(r["erros_publicadas"], 1)
        self.assertEqual(r["precisao_publicadas"], .5)
        self.assertFalse(r["meta_95_atingida_na_amostra"])
        self.assertEqual(politica, antes)

    def test_brier_mede_probabilidades_originais_sem_reajuste(self):
        r = m.resumir_teste([linha("A", True, confianca=.8), linha("B", False, confianca=.6)], politica_minima())
        self.assertAlmostEqual(r["brier_todas"], (.2 ** 2 + .6 ** 2) / 2)
        self.assertEqual(r["confianca_publicar_fixada_na_calibracao"], .8)

    def test_publicacao_de_fora_referencia_e_reportada_como_erro(self):
        r = m.resumir_teste([linha("A", False, ramo="FORA"), linha("B", True, ramo="Penal")], politica_minima())
        self.assertEqual(r["por_ramo_referencia"]["FORA"]["publicadas"], 1)
        self.assertEqual(r["por_ramo_referencia"]["FORA"]["publicadas_corretas"], 0)

    def test_teste_vazio_e_rejeitado(self):
        with self.assertRaises(ValueError): m.resumir_teste([], politica_minima())

    def test_manifesto_com_travessia_de_diretorio_e_rejeitado(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ValueError):
                m.validar_artefatos(Path(pasta), {"sha256_artefatos": {"../fora": "a"}}, {"../fora"})

    def test_calibracao_integra_e_aceita_sem_novas_previsoes(self):
        with tempfile.TemporaryDirectory() as pasta:
            entradas = preparar(Path(pasta))
            metodo = m.cal.ler_json(entradas[1])
            with patch.object(m.cal.esc.ClassificadorEscopos, "ranquear", side_effect=AssertionError("Não reclassificar")):
                politica = m.conferir_politica(entradas[2], entradas[1], metodo)
            self.assertEqual(politica, m.cal.ler_json(entradas[2]))

    def test_qualquer_alteracao_em_politica_ou_csv_e_detectada(self):
        with tempfile.TemporaryDirectory() as pasta:
            entradas = preparar(Path(pasta)); metodo = m.cal.ler_json(entradas[1])
            for caminho in (entradas[2], entradas[2].parent / "calibracao.csv", entradas[2].parent / "desenvolvimento.csv"):
                original = caminho.read_bytes(); caminho.write_bytes(original + b" ")
                with self.assertRaises(ValueError): m.conferir_politica(entradas[2], entradas[1], metodo)
                caminho.write_bytes(original)

    def test_rejeita_codigo_ou_metodo_divergente(self):
        with tempfile.TemporaryDirectory() as pasta:
            entradas = preparar(Path(pasta)); metodo = m.cal.ler_json(entradas[1])
            with patch.object(m.cal, "__file__", str(entradas[1])):
                with self.assertRaises(ValueError): m.conferir_politica(entradas[2], entradas[1], metodo)
            metodo["configuracao"] = {"outro": True}
            with self.assertRaises(ValueError): m.conferir_politica(entradas[2], entradas[1], metodo)

    def test_csv_de_outro_grupo_nao_e_aceito(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / "grupo.csv"; p.write_text("id\nQ0001\n", encoding="utf-8")
            with self.assertRaises(ValueError): m.ler_registros_calibracao(p, ["Q0002"])

    def test_saida_existente_e_preservada(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "teste"; destino.mkdir(); (destino / "registro").write_text("preservar")
            with self.assertRaises(ValueError):
                m.executar(*(Path("ausente") for _ in range(5)), destino)
            self.assertEqual((destino / "registro").read_text(), "preservar")

    def test_integracao_so_20_testes_sem_rede_sem_retreino_e_com_registro_previo(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta); entradas = preparar(pasta); destino = pasta / "teste"
            polit_antes = entradas[2].read_bytes(); metodo_antes = entradas[1].read_bytes()
            arquivos = list(entradas[0].glob('*')) + list(entradas[2].parent.glob('*'))
            hashes_antes = {p: m.cal.base.sha256(p) for p in arquivos if p.is_file()}
            vistos = []; original = m.cal.esc.ClassificadorEscopos.ranquear
            def registrar(self, questao):
                registros = list(pasta.glob('.teste-*/congelamento_antes_teste.json'))
                if len(registros) != 1:
                    raise AssertionError("Ausência do congelamento anterior à primeira previsão")
                vistos.append(questao["id"])
                return original(self, questao)
            with patch.object(m.cal.esc.ClassificadorEscopos, "ranquear", registrar), \
                    patch.object(socket, "socket", side_effect=AssertionError("Sem rede")), \
                    patch.dict(sys.modules, {"fastembed": None, "onnxruntime": None, "numpy": None}):
                resultado = m.executar(*entradas, destino)
            self.assertEqual(vistos, [f"Q{i:04d}" for i in range(81, 101)])
            self.assertEqual(resultado["teste"]["questoes"], 20)
            self.assertFalse(resultado["metodo_ou_politica_alterados"])
            self.assertFalse(resultado["questoes_sem_rotulo"]["previsoes_geradas"])
            self.assertEqual(entradas[2].read_bytes(), polit_antes)
            self.assertEqual(entradas[1].read_bytes(), metodo_antes)
            for p, hash_original in hashes_antes.items(): self.assertEqual(m.cal.base.sha256(p), hash_original)
            manifesto = m.cal.ler_json(destino / "manifesto.json")
            self.assertEqual(manifesto["ids_com_previsoes"], vistos)
            m.validar_artefatos(destino, manifesto, {"congelamento_antes_teste.json", "resumo.json", "teste.csv", "LEITURA.md"})


if __name__ == "__main__":
    unittest.main()
