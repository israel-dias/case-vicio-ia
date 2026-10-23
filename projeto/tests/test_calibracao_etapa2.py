import copy
import csv
import json
import math
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import calibrar_etapa2 as m


def registro(qid, margem, certo=True, score=.3, escopo=True):
    return {"id": qid, "tema_previsto": "10", "score_top1": score,
            "score_top2": score * (1 - margem), "margem_relativa": margem,
            "escopo_proposto": escopo, "acerto_top1": certo, "fora_referencia": False}


def desenvolvimento():
    return [registro(f"D{i}", .95 - .05 * i) for i in range(8)] + [registro("D8", .3, False)]


def fixture(pasta):
    dados = pasta / "dados"; dados.mkdir()
    with (dados / "temas.csv").open("w", newline="", encoding="utf-8") as arquivo:
        campos = ["tema_id", "parent_id", "disciplina", "nivel", "titulo", "caminho", "descricao", "status"]
        w = csv.DictWriter(arquivo, fieldnames=campos); w.writeheader()
        for tid, pai, nivel, titulo in (("1", "", 0, "Disciplina"),
                                       ("10", "1", 1, "Investigação"),
                                       ("11", "10", 2, "Arquivamento"),
                                       ("20", "1", 1, "Penas")):
            w.writerow(dict(tema_id=tid, parent_id=pai, disciplina="Disciplina", nivel=nivel,
                            titulo=titulo, caminho=titulo, descricao="", status="ativo"))
    with (dados / "questoes.jsonl").open("w", encoding="utf-8") as arquivo:
        for i in range(1, 660):
            arquivo.write(json.dumps({"id": f"Q{i:04d}", "enunciado_html": f"Investigação inquérito arquivamento número {i}.",
                                      "comando": "", "alternativas": {"A": "Arquivamento"},
                                      "disciplina_origem": "Incerta", "assunto_origem": ""}) + "\n")
    with (dados / "folha_verdade.csv").open("w", newline="", encoding="utf-8") as arquivo:
        w = csv.DictWriter(arquivo, fieldnames=["id", "tema_central_id", "tema_central_caminho", "extras_ids", "fora_da_taxonomia"])
        w.writeheader()
        for i in range(1, 101):
            w.writerow(dict(id=f"Q{i:04d}", tema_central_id="10", tema_central_caminho="Investigação", extras_ids="", fora_da_taxonomia="0"))
    vocabulario = pasta / "vocab.tsv"; vocabulario.write_text("10;11\tInvestigação inquérito arquivamento\n20\tPenas sanções\n", encoding="utf-8")
    escopos = pasta / "escopos.json"
    m.autoria.gerar(dados / "temas.csv", vocabulario, escopos)
    particao = {"desenvolvimento": [f"Q{i:04d}" for i in range(1, 61)],
                "calibracao_reservada": [f"Q{i:04d}" for i in range(61, 81)],
                "teste_reservado": [f"Q{i:04d}" for i in range(81, 101)]}
    hashes = {n: m.base.sha256(dados / n) for n in ("questoes.jsonl", "temas.csv", "folha_verdade.csv")}
    manifesto = {"particao": particao, "sha256_entradas": hashes}
    m.escrever_json(pasta / "manifesto_inicial.json", manifesto)
    metodo = {"versao": "metodo_catalogo_v1", "metodo": m.esc.METODO_ESCOLHIDO,
              "configuracao": next(c for c in m.esc.CONFIGURACOES if c["nome"] == m.esc.METODO_ESCOLHIDO),
              "sha256_codigo": {Path(p).name: m.base.sha256(Path(p)) for p in (m.esc.__file__, m.autoria.__file__, m.base.__file__)},
              "sha256_entradas": hashes, "sha256_escopos": m.base.sha256(escopos),
              "sha256_vocabulario": m.base.sha256(vocabulario), "particao": particao,
              "metricas_desenvolvimento": {"acertos_top1": 60}}
    caminho = pasta / "metodo_congelado.json"; m.escrever_json(caminho, metodo)
    return dados, caminho, escopos, vocabulario


class TestCalibracao(unittest.TestCase):
    def test_intervalo_exato_confere_exemplo_nist(self):
        inferior, superior = m.intervalo_exato(4, 20, .90)
        self.assertAlmostEqual(inferior, .071354, places=5)
        self.assertAlmostEqual(superior, .401029, places=5)

    def test_vinte_acertos_nao_estabelecem_minimo_95_porcento(self):
        s = m.estatistica(20, 20)
        self.assertAlmostEqual(s["limite_inferior_unilateral_95_descritivo"], .05 ** (1 / 20))
        self.assertLess(s["limite_inferior_unilateral_95_descritivo"], .95)
        self.assertEqual(s["intervalo_exato_95_descritivo"][1], 1.)

    def test_sem_publicadas_precisao_indefinida_e_intervalo_aberto(self):
        s = m.estatistica(0, 0)
        self.assertIsNone(s["precisao_empirica"])
        self.assertEqual(s["intervalo_exato_95_descritivo"], [0., 1.])
        self.assertEqual(s["media_beta_1_1"], .5)

    def test_contagens_booleanas_negativas_e_invertidas_sao_rejeitadas(self):
        for c, n in ((True, 2), (1, False), (-1, 2), (3, 2), (1.5, 3)):
            with self.assertRaises(ValueError): m.estatistica(c, n)

    def test_nan_infinito_booleano_nao_sao_margem(self):
        for valor in (math.nan, math.inf, True, -.1, 1.1):
            with self.assertRaises(ValueError): m.elegivel(registro("X", valor), .3)

    def test_limites_candidatos_vem_apenas_desenvolvimento(self):
        dev = desenvolvimento(); antes = copy.deepcopy(dev)
        candidatos = m.propor_limiares(dev)
        self.assertTrue(candidatos)
        self.assertTrue(all(c["limiar_margem"] in {r["margem_relativa"] for r in dev} for c in candidatos))
        self.assertTrue(all(c["dev_publicadas"] >= 5 and c["dev_precisao"] >= .95 for c in candidatos))
        self.assertEqual(dev, antes)

    def test_calibracao_escolhe_cobertura_sem_inventar_limiar(self):
        cal = [registro(f"C{i}", .9 - .05 * i) for i in range(5)] + [registro("C5", .2, False)]
        politica, candidatos = m.construir_politica(desenvolvimento(), cal)
        self.assertTrue(politica["ativa"])
        self.assertEqual(politica["escolha"]["cal_publicadas"], 5)
        self.assertEqual(politica["escolha"]["dev_publicadas"], 8)
        self.assertIn(politica["limiar_margem"], {c["limiar_margem"] for c in candidatos})

    def test_dois_exemplos_perfeitos_nao_ativam_publicacao(self):
        politica, _ = m.construir_politica(desenvolvimento(), [registro("C1", .9), registro("C2", .8)])
        self.assertFalse(politica["ativa"])
        self.assertIsNone(politica["limiar_margem"])
        self.assertEqual(m.aplicar_politica(registro("NOVA", .99), politica)["decisao"], "revisar")

    def test_erro_de_calibracao_nao_e_ocultado_pelo_desenvolvimento(self):
        cal = [registro(f"C{i}", .99 - i / 100, False) for i in range(5)]
        politica, _ = m.construir_politica(desenvolvimento(), cal)
        self.assertFalse(politica["ativa"])
        self.assertEqual(politica["confianca_por_decisao"]["revisar"]["acertos"], 0)

    def test_confianca_usa_calibracao_suavizada_nao_cosseno(self):
        cal = [registro(f"C{i}", .99, score=.9) for i in range(3)]
        politica, _ = m.construir_politica(desenvolvimento(), cal)
        saida = m.aplicar_politica(registro("NOVO", .99, score=.7), politica)
        self.assertEqual(saida["decisao"], "publicar")
        self.assertEqual(saida["confianca"], 4 / 5)
        self.assertNotEqual(saida["confianca"], .7)
        self.assertNotEqual(saida["confianca"], 1.)

    def test_id_e_rotulo_nao_alteram_decisao(self):
        politica, _ = m.construir_politica(desenvolvimento(), [registro(f"C{i}", .99) for i in range(3)])
        linha = registro("Q0001", .9, True)
        outra = dict(linha, id="Q0600", acerto_top1=False, fora_referencia=True)
        self.assertEqual(m.aplicar_politica(linha, politica), m.aplicar_politica(outra, politica))

    def test_empate_escopo_pendente_e_pouco_sinal_seguem_revisao(self):
        self.assertFalse(m.elegivel(registro("X", 0), 0))
        self.assertFalse(m.elegivel(registro("X", .9, escopo=False), .2))
        self.assertFalse(m.elegivel(registro("X", 1, score=.049), .2))

    def test_fora_nao_e_inventado_por_baixa_similaridade(self):
        politica, _ = m.construir_politica(desenvolvimento(), [registro(f"C{i}", .99) for i in range(3)])
        saida = m.aplicar_politica(registro("X", 1, score=.001), politica)
        self.assertEqual(saida["decisao"], "revisar")
        self.assertFalse(m.PROTOCOLO["fora_automatico"])

    def test_sem_candidato_nao_recebe_falsa_publicacao(self):
        politica, _ = m.construir_politica(desenvolvimento(), [registro(f"C{i}", .99) for i in range(3)])
        linha = dict(registro("X", 0, score=0), tema_previsto="", escopo_proposto=False)
        self.assertEqual(m.aplicar_politica(linha, politica)["decisao"], "revisar")

    def test_avaliador_rejeita_rotulos_de_outro_grupo(self):
        with self.assertRaises(ValueError):
            m.avaliar_ids(None, ["Q0001"], {}, {"Q0001": {}, "Q0002": {}}, {}, {})

    def test_duplicatas_entre_grupos_sao_sinalizadas_sem_redistribuir(self):
        qs = {"A": {"enunciado_html": "<b>Texto</b>", "alternativas": {}},
              "B": {"enunciado_html": "Texto", "alternativas": {}}}
        particao = {"dev": ["A"], "cal": ["B"]}; antes = copy.deepcopy(particao)
        with self.assertRaises(ValueError): m.conferir_duplicatas(qs, particao)
        self.assertEqual(particao, antes)

    def test_saida_existente_e_preservada(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "salvo"; destino.mkdir()
            sentinela = destino / "sentinela"; sentinela.write_text("preservado")
            with self.assertRaises(ValueError):
                m.executar(Path("ausente"), Path("ausente"), Path("ausente"), Path("ausente"), destino)
            self.assertEqual(sentinela.read_text(), "preservado")

    def test_integracao_nao_prediz_teste_nem_559_e_nao_usa_rede(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta); entradas = fixture(pasta)
            vistos = []; original = m.esc.ClassificadorEscopos.ranquear
            def registrar(self, questao):
                vistos.append(questao["id"])
                return original(self, questao)
            with patch.object(m.esc.ClassificadorEscopos, "ranquear", registrar), \
                    patch.object(socket, "socket", side_effect=AssertionError("Sem rede")), \
                    patch.dict(sys.modules, {"fastembed": None, "onnxruntime": None, "numpy": None}):
                resumo = m.executar(*entradas, pasta / "saida")
            self.assertEqual(set(vistos), {f"Q{i:04d}" for i in range(1, 81)})
            self.assertEqual(len(vistos), 80)
            self.assertFalse(resumo["teste_reservado"]["previsoes_geradas"])
            self.assertFalse(resumo["questoes_sem_rotulo"]["previsoes_geradas"])
            manifesto = m.ler_json(pasta / "saida/manifesto.json")
            for nome, hash_esperado in manifesto["sha256_artefatos"].items():
                self.assertEqual(m.base.sha256(pasta / "saida" / nome), hash_esperado)
            politica = m.ler_json(pasta / "saida/politica_congelada.json")
            self.assertEqual(politica["configuracao"], m.ler_json(entradas[1])["configuracao"])

    def test_alterar_codigo_anexo_configuracao_ou_divisao_e_rejeitado(self):
        with tempfile.TemporaryDirectory() as pasta:
            entradas = fixture(Path(pasta)); original = m.ler_json(entradas[1])
            m.conferir_congelamento(*entradas)
            for campo, novo in (("sha256_codigo", {}), ("sha256_entradas", {}),
                                ("configuracao", {}), ("sha256_vocabulario", "0" * 64)):
                alterado = copy.deepcopy(original); alterado[campo] = novo
                m.escrever_json(entradas[1], alterado)
                with self.assertRaises(ValueError): m.conferir_congelamento(*entradas)
            alterado = copy.deepcopy(original)
            alterado["particao"]["calibracao_reservada"][0] = "Q0099"
            m.escrever_json(entradas[1], alterado)
            with self.assertRaises(ValueError): m.conferir_congelamento(*entradas)


if __name__ == "__main__":
    unittest.main()
