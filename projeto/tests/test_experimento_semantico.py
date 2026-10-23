import copy
import gzip
import importlib
import json
import math
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import experimento_semantico as m
import semantico_textos as textos


def arvore():
    dados = [("1", "", 0, "Disciplina"), ("10", "1", 1, "Investigação"),
             ("11", "10", 2, "Arquivamento"), ("12", "10", 2, "Instauração"),
             ("20", "1", 1, "Penas")]
    return {tid: {"tema_id": tid, "parent_id": pai, "nivel": n, "ativo": True,
                  "titulo": titulo, "caminho": titulo, "descricao": "",
                  "disciplina": "Disciplina"} for tid, pai, n, titulo in dados}


class TestExperimentoSemantico(unittest.TestCase):
    def test_exclui_o_proprio_item_e_duplicatas_normalizadas(self):
        hashes = {"A": "mesmo", "B": "mesmo", "C": "outro", "D": "diferente"}
        self.assertEqual(m.ids_treino_para("A", hashes, hashes), ["C", "D"])

    def test_rotulo_do_item_avaliado_nao_pode_entrar_no_treino(self):
        rotulos = {"A": {"tema_central_id": "11", "extras_ids": "", "fora_da_taxonomia": "0"},
                   "B": {"tema_central_id": "20", "extras_ids": "", "fora_da_taxonomia": "0"}}
        vetores = {"A": [1., 0.], "B": [0., 1.]}
        with self.assertRaises(ValueError):
            m.VizinhosSupervisionados(["A"], rotulos, arvore(), vetores)

    def test_trocar_rotulo_excluido_nao_muda_seus_votos(self):
        todos = {"A": {"tema_central_id": "11", "extras_ids": "", "fora_da_taxonomia": "0"},
                 "B": {"tema_central_id": "20", "extras_ids": "", "fora_da_taxonomia": "0"}}
        vetores = {"A": [1., 0.], "B": [1., 0.]}
        def votos():
            mod = m.VizinhosSupervisionados(["B"], {"B": todos["B"]}, arvore(), vetores)
            return dict(mod.pontuar(mod.similares(vetores["A"]), 1))
        antes = votos()
        todos["A"]["tema_central_id"] = "20"
        self.assertEqual(votos(), antes)

    def test_rotulo_amplo_nao_inventa_um_filho(self):
        mod = m.VizinhosSupervisionados(["A"], {"A": {"tema_central_id": "10",
            "extras_ids": "", "fora_da_taxonomia": "0"}}, arvore(), {"A": [1., 0.]})
        self.assertEqual(mod.associacoes["A"], {"10"})

    def test_extra_e_pai_sao_preservados_sem_disciplina_raiz(self):
        mod = m.VizinhosSupervisionados(["A"], {"A": {"tema_central_id": "11",
            "extras_ids": "20", "fora_da_taxonomia": "0"}}, arvore(), {"A": [1., 0.]})
        self.assertEqual(mod.associacoes["A"], {"10", "11", "20"})

    def test_fora_nao_e_convertido_em_tema_por_treino(self):
        mod = m.VizinhosSupervisionados(["A"], {"A": {"tema_central_id": "",
            "extras_ids": "", "fora_da_taxonomia": "1"}}, arvore(), {"A": [1., 0.]})
        self.assertEqual(dict(mod.pontuar(mod.similares([1., 0.]), 1)), {})

    def test_vetor_zero_nan_booleano_e_dimensao_errada(self):
        for vetor in ([0., 0.], [float("nan"), 1.], [True, 1.], [float("inf")]):
            with self.assertRaises(ValueError):
                textos.normalizar_vetor(vetor)
        with self.assertRaises(ValueError):
            m.produto([1., 0.], [1.])

    def test_texto_preserva_alternativas_negacao_e_remove_script(self):
        q = {"enunciado_html": "Não arquivar.<script>codigo</script>",
             "comando": "Não arquivar.", "alternativas": {"A": "Penas", "B": "Investigação"}}
        t = textos.texto_questao(q)
        self.assertIn("Não", t)
        self.assertIn("Penas", t)
        self.assertIn("Investigação", t)
        self.assertNotIn("codigo", t)
        self.assertEqual(t.count("Não"), 1)

    def test_metadados_e_id_nao_entram_no_texto_do_embedding(self):
        q = {"id": "A", "enunciado_html": "Texto", "comando": "",
             "alternativas": {}, "disciplina_origem": "X", "assunto_origem": "Y"}
        alterado = dict(q, id="B", disciplina_origem="Z", assunto_origem="W")
        self.assertEqual(textos.texto_questao(q), textos.texto_questao(alterado))

    def test_vizinhos_so_consideram_ids_de_treino(self):
        palavras = {"A": {"x": 1.}, "B": {"x": .8}, "RESERVADO": {"x": 1.}}
        r = m.vizinhos_lexicos("A", ["B"], palavras, palavras)
        self.assertEqual([qid for qid, _ in r], ["B"])

    def test_importacao_e_calculo_nao_exigem_encoder_ou_rede(self):
        with patch.dict(sys.modules, {"fastembed": None, "onnxruntime": None, "numpy": None}), \
                patch.object(socket, "socket", side_effect=AssertionError("Sem rede")):
            mod = importlib.reload(m)
            resultado = mod.ranquear(mod.CONFIGURACOES[0], {"11": .5, "12": .3}, {}, {}, arvore())
            self.assertEqual(resultado[0][0], "10")

    def test_hash_incorreto_do_cache_e_rejeitado_antes_da_leitura(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            dados = pasta / "dados"; dados.mkdir()
            cache = pasta / "cache"; cache.mkdir()
            for nome in ("questoes.jsonl", "temas.csv"):
                (dados / nome).write_text("entrada")
            manifesto = {"versao_textos": textos.VERSAO_TEXTOS, "dimensao": 384,
                         "sha256_entradas": {n: m.base.sha256(dados / n)
                            for n in ("questoes.jsonl", "temas.csv")},
                         "sha256_vetores": "0" * 64}
            (cache / "manifesto_embeddings.json").write_text(json.dumps(manifesto))
            (cache / "vetores.json.gz").write_bytes(b"alterado")
            with self.assertRaisesRegex(ValueError, "Vetores alterados"):
                m.carregar_cache(cache, dados, {}, {})


if __name__ == "__main__":
    unittest.main()
