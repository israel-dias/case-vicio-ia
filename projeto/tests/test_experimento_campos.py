import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import experimento_campos as m


def arvore():
    dados = [
        ("1", "", 0, "Disciplina"),
        ("10", "1", 1, "Investigação"),
        ("11", "10", 2, "Arquivamento"),
        ("12", "10", 2, "Instauração"),
        ("20", "1", 1, "Penas"),
    ]
    return {tid: {"tema_id": tid, "parent_id": pai, "nivel": nivel,
                  "ativo": True, "titulo": titulo, "caminho": titulo,
                  "descricao": ""} for tid, pai, nivel, titulo in dados}


class TestExperimentoCampos(unittest.TestCase):
    def test_regua_distingue_ancestrais_irmaos_e_extras(self):
        temas = arvore()
        r = {"tema_central_id": "11", "extras_ids": "20", "fora_da_taxonomia": "0"}
        self.assertTrue(m.aceito("11", r, temas))
        self.assertTrue(m.aceito("10", r, temas))
        self.assertTrue(m.aceito("20", r, temas))
        self.assertFalse(m.aceito("12", r, temas))
        r["fora_da_taxonomia"] = "1"
        self.assertFalse(m.aceito("11", r, temas))

    def test_particao_preserva_reservas_e_rejeita_sobreposicao(self):
        p = {"desenvolvimento": ["Q1"], "calibracao_reservada": ["Q2"],
             "teste_reservado": ["Q3"]}
        manifesto = {"interno": {"particao": p}}
        self.assertEqual(m.localizar_particao(manifesto), p)
        m.validar_particao(p, {"Q1", "Q2", "Q3"}, [{"id": "Q1"}])
        errado = copy.deepcopy(p)
        errado["teste_reservado"] = ["Q2"]
        with self.assertRaises(ValueError):
            m.validar_particao(errado, {"Q1", "Q2", "Q3"}, [{"id": "Q1"}])

    def test_ranking_de_outro_conjunto_nao_e_aceito(self):
        p = {"desenvolvimento": ["Q1"], "calibracao_reservada": ["Q2"],
             "teste_reservado": ["Q3"]}
        with self.assertRaises(ValueError):
            m.validar_particao(p, {"Q1", "Q2", "Q3"}, [{"id": "Q3"}])

    def test_manifesto_id_para_grupo_preserva_divisao(self):
        manifesto = {"particao": {
            "Q0001": "desenvolvimento", "Q0002": "calibracao_reservada",
            "Q0003": "teste_reservado",
        }}
        p = m.localizar_particao(manifesto)
        self.assertEqual(p, {"desenvolvimento": ["Q0001"],
                             "calibracao_reservada": ["Q0002"],
                             "teste_reservado": ["Q0003"]})
        m.validar_particao(p, {"Q0001", "Q0002", "Q0003"}, [{"id": "Q0001"}])

    def test_manifesto_com_registros_e_nomes_equivalentes(self):
        manifesto = {"divisao": [
            {"id": "Q0001", "grupo": "desenvolvimento"},
            {"id": "Q0002", "grupo": "calibração"},
            {"id": "Q0003", "grupo": "teste"},
        ]}
        p = m.localizar_particao(manifesto)
        self.assertEqual(p["calibracao_reservada"], ["Q0002"])
        self.assertEqual(p["teste_reservado"], ["Q0003"])

    def test_manifesto_id_para_registro_e_grupo_para_objeto(self):
        p = {"desenvolvimento": ["Q0001"], "calibracao_reservada": ["Q0002"],
             "teste_reservado": ["Q0003"]}
        por_id = {"Q0001": {"split": "desenvolvimento"},
                  "Q0002": {"split": "calibracao_reservada"},
                  "Q0003": {"split": "teste_reservado"}}
        self.assertEqual(m.localizar_particao({"particao": por_id}), p)
        self.assertEqual(m.localizar_particao({k: {"ids": ids} for k, ids in p.items()}), p)

    def test_contagens_sozinhas_nao_recriam_ids(self):
        with self.assertRaises(ValueError):
            m.localizar_particao({"particao": {"desenvolvimento": 60,
                "calibracao_reservada": 20, "teste_reservado": 20}})

    def test_representacoes_conflitantes_sao_rejeitadas(self):
        p = {"desenvolvimento": ["Q0001"], "calibracao_reservada": ["Q0002"],
             "teste_reservado": ["Q0003"]}
        por_id = {"Q0001": "teste_reservado", "Q0002": "calibracao_reservada",
                  "Q0003": "desenvolvimento"}
        with self.assertRaises(ValueError):
            m.localizar_particao({"listas": p, "por_id": por_id})

    def test_grupo_desconhecido_nao_e_adivinhado(self):
        with self.assertRaises(ValueError):
            m.localizar_particao({"particao": {"Q0001": "validacao"}})

    def test_listas_com_ordem_diferente_representam_mesmos_grupos(self):
        p = {"desenvolvimento": ["Q0001", "Q0004"],
             "calibracao_reservada": ["Q0002"], "teste_reservado": ["Q0003"]}
        por_id = {"Q0004": "desenvolvimento", "Q0001": "desenvolvimento",
                  "Q0002": "calibracao_reservada", "Q0003": "teste_reservado"}
        self.assertEqual(m.localizar_particao({"listas": p, "por_id": por_id}), p)

    def test_hashes_por_id_nao_sao_confundidos_com_particao(self):
        p = {"desenvolvimento": ["Q0001"], "calibracao_reservada": ["Q0002"],
             "teste_reservado": ["Q0003"]}
        manifesto = {"hashes_por_id": {"Q0001": "a" * 64}, "particao": p}
        self.assertEqual(m.localizar_particao(manifesto), p)

    def test_avaliacao_nao_classifica_ids_fora_do_desenvolvimento(self):
        modelo = Mock()
        modelo.ranquear.return_value = [("11", 0.3)]
        questoes = {"D": {"id": "D"}, "C": {"id": "C"}, "T": {"id": "T"},
                    "N": {"id": "N"}}
        rotulos = {qid: {"tema_central_id": "11", "extras_ids": "",
                        "fora_da_taxonomia": "0"} for qid in ("D", "C", "T")}
        saida = m.avaliar(modelo, ["D"], questoes, rotulos, arvore())
        modelo.ranquear.assert_called_once_with(questoes["D"])
        self.assertEqual([r["id"] for r in saida], ["D"])

    def test_texto_preserva_negacao_e_todas_as_alternativas(self):
        q = {"enunciado_html": "Não arquivar.<script>senha</script>",
             "comando": "Não arquivar.", "alternativas": {"A": "Penas", "B": "Investigação"}}
        texto = m.texto_completo(q)
        self.assertIn("nao", texto)
        self.assertIn("penas", texto)
        self.assertIn("investigacao", texto)
        self.assertNotIn("senha", texto)
        self.assertEqual(texto.count("nao"), 1)
        self.assertNotIn("nao", m.STOPWORDS)

    def test_id_e_disciplina_nao_afetam_ranking(self):
        q = {"id": "Q1", "enunciado_html": "Arquivamento da investigação",
             "comando": "", "alternativas": {}, "disciplina_origem": "Origem errada"}
        modelo = m.Classificador(arvore(), m.CONFIGURACOES[0])
        outro = dict(q, id="Q9999", disciplina_origem="Outra origem")
        self.assertEqual(modelo.ranquear(q), modelo.ranquear(outro))

    def test_boilerplate_removido_sem_apagar_descricao_semantica(self):
        tema = arvore()["11"]
        tema["descricao"] = "Subtema de 'X' (Y). 25 questões no source. Path: X > Y."
        self.assertIn("source", m.campo_tema(tema, False))
        self.assertNotIn("source", m.campo_tema(tema, True))
        tema["descricao"] = "Condições de encerramento da investigação."
        self.assertIn("encerramento", m.campo_tema(tema, True))

    def test_introducao_nao_e_atenuada_em_caso_concreto_comum(self):
        q = {"enunciado_html": "Uma investigação iniciou.<br><br>O juiz decidiu.",
             "comando": "", "alternativas": {}}
        self.assertEqual(m.campos_questao(q, False), m.campos_questao(q, True))

    def test_ciclo_e_pai_ausente_sao_rejeitados(self):
        temas = arvore()
        temas["10"]["parent_id"] = "11"
        with self.assertRaises(ValueError):
            m.ancestrais("11", temas)
        temas = arvore()
        temas["11"]["parent_id"] = "999"
        with self.assertRaises(ValueError):
            m.ancestrais("11", temas)

    def test_variantes_com_pai_nao_escolhem_disciplina_raiz(self):
        config = dict(m.CONFIGURACOES[-1])
        config["peso_metadado"] = 0
        modelo = m.Classificador(arvore(), config)
        resultado = modelo.ranquear({"enunciado_html": "Arquivamento", "alternativas": {}})
        self.assertTrue(resultado)
        self.assertNotIn("1", [tid for tid, _ in resultado])


if __name__ == "__main__":
    unittest.main()
