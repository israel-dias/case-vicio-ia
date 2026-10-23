import copy
import importlib
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import experimento_escopos as m
import gerar_escopos as g


def arvore():
    dados = [("1", "", 0, "Disciplina"), ("10", "1", 1, "Investigação"),
             ("11", "10", 2, "Arquivamento"), ("12", "10", 2, "Instauração"),
             ("20", "1", 1, "Penas")]
    return {tid: {"tema_id": tid, "parent_id": pai, "nivel": n, "ativo": True,
                  "titulo": titulo, "caminho": titulo, "descricao": "",
                  "disciplina": "Disciplina"} for tid, pai, n, titulo in dados}


class TestExperimentoEscopos(unittest.TestCase):
    def test_propostas_preservam_ids_e_nao_inventam_recorte_ausente(self):
        temas = arvore(); antes = copy.deepcopy(temas)
        propostas = g.construir(temas, {"11": "Arquivamento e encerramento da investigação."})
        self.assertEqual(set(propostas), {"10", "11", "12", "20"})
        self.assertEqual(propostas["10"]["status_proposta"], "escopo_pendente")
        self.assertEqual(propostas["10"]["descricao_proposta"], "")
        self.assertEqual(temas, antes)

    def test_vocabulos_para_raiz_inativo_ou_desconhecido_sao_rejeitados(self):
        temas = arvore(); temas["20"]["ativo"] = False
        for tid in ("1", "20", "999"):
            with self.assertRaises(ValueError):
                g.construir(temas, {tid: "Proposta"})

    def test_nao_aceita_id_de_questao_no_vocabulario(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "vocabulario.tsv"
            caminho.write_text("11\tA questão Q0001 pertence a este tema.\n")
            with self.assertRaises(ValueError):
                g.ler_vocabulario(caminho)

    def test_rejeita_definicoes_duplicadas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "vocabulario.tsv"
            caminho.write_text("10;11\tTermos\n11\tOutra descrição\n")
            with self.assertRaises(ValueError):
                g.ler_vocabulario(caminho)

    def test_compartilhar_vocabulario_nao_funde_ids(self):
        temas = arvore()
        propostas = g.construir(temas, {"10": "Investigação", "20": "Investigação"})
        self.assertEqual(propostas["10"]["tema_id"], "10")
        self.assertEqual(propostas["20"]["tema_id"], "20")
        self.assertNotEqual(propostas["10"]["caminho_original"], propostas["20"]["caminho_original"])

    def test_limites_nao_sao_indexados_como_evidencia_positiva(self):
        temas = arvore(); propostas = g.construir(temas, {"11": "Arquivamento"})
        for r in propostas.values(): r["limites_para_documentacao"] = "saturno galaxia"
        documentos = m.documentos_catalogo(temas, propostas, "juntos")
        self.assertTrue(all("saturno" not in d for d in documentos.values()))

    def test_media3_agrega_pai_e_filhos_sem_disciplina_raiz(self):
        temas = arvore()
        r = m.agregar_familias({"10": .1, "11": .9, "12": .5, "20": .2}, temas, "media3")
        self.assertAlmostEqual(r["10"], .5)
        self.assertEqual(r["20"], .2)
        self.assertNotIn("1", r)
        self.assertNotIn("11", r)

    def test_ramos_diferentes_nao_sao_somados(self):
        r = m.agregar_familias({"11": .9, "12": .3, "20": .8}, arvore(), "media2")
        self.assertAlmostEqual(r["10"], .6)
        self.assertAlmostEqual(r["20"], .8)

    def test_classificacao_nao_depende_do_id_ou_disciplina_de_origem(self):
        temas = arvore(); propostas = g.construir(temas, {"11": "Arquivamento da investigação."})
        cfg = next(c for c in m.CONFIGURACOES if c["nome"] == m.METODO_ESCOLHIDO)
        modelo = m.ClassificadorEscopos(temas, propostas, cfg)
        q = {"id": "Q0001", "enunciado_html": "Arquivamento da investigação",
             "comando": "", "alternativas": {}, "assunto_origem": "", "disciplina_origem": "X"}
        self.assertEqual(modelo.ranquear(q), modelo.ranquear(dict(q, id="Q9999", disciplina_origem="Y")))

    def test_classificador_funciona_sem_encoder_numpy_ou_rede(self):
        temas = arvore(); propostas = g.construir(temas, {"11": "Arquivamento"})
        with patch.dict(sys.modules, {"fastembed": None, "onnxruntime": None, "numpy": None}), \
                patch.object(socket, "socket", side_effect=AssertionError("Sem rede")):
            cfg = next(c for c in m.CONFIGURACOES if c["nome"] == m.METODO_ESCOLHIDO)
            modelo = m.ClassificadorEscopos(temas, propostas, cfg)
            self.assertTrue(modelo.ranquear({"enunciado_html": "Arquivamento", "alternativas": {}}))

    def test_adulteracao_de_proposta_e_detectada(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta); vocab = pasta / "vocab.tsv"; catalogo = pasta / "temas.csv"
            vocab.write_text("11\tArquivamento\n"); catalogo.write_text("entrada")
            temas = arvore()
            objeto = {"versao": g.VERSAO, "sha256_temas": m.base.sha256(catalogo),
                      "sha256_vocabulario_autorado": m.base.sha256(vocab),
                      "temas": g.construir(temas, g.ler_vocabulario(vocab))}
            arquivo = pasta / "escopos.json"; arquivo.write_text(json.dumps(objeto))
            m.carregar_propostas(temas, catalogo, arquivo, vocab)
            objeto["temas"]["11"]["descricao_proposta"] = "Texto modificado"
            arquivo.write_text(json.dumps(objeto))
            with self.assertRaises(ValueError): m.carregar_propostas(temas, catalogo, arquivo, vocab)

    def test_gerador_nao_sobrescreve_artefato_existente(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / "escopos.json"; p.write_text("preservar")
            with self.assertRaises(ValueError): g.gerar(Path("ausente"), Path("ausente"), p)
            self.assertEqual(p.read_text(), "preservar")


if __name__ == "__main__":
    unittest.main()
