"""Verificações de integridade. Fixtures NÃO são classificações do case."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from vicio_ia.arquivos import carregar_json, gravar_json, ler_jsonl, sha256
from vicio_ia.cli import preparar
from vicio_ia.importacao import importar, validar_resposta
from vicio_ia.lotes import gerar_lotes, selecionar_piloto
from vicio_ia.preparacao import limpar_html, preparar_questoes
from vicio_ia.temas import mesmo_ramo, validar_temas

RAIZ = Path(__file__).resolve().parents[1]


def tema(identificador, pai="", nivel="0", status="active"):
    return {"tema_id": identificador, "parent_id": pai, "nivel": nivel, "status": status,
            "disciplina": "Penal", "titulo": f"Tema {identificador}",
            "caminho": f"Penal {identificador}", "descricao": ""}


def fixture_resposta():
    return {"classificacoes": [{
        "id": "Q0001", "sugestao_decisao": "revisar", "tema_central_id": "10",
        "extras_ids": [], "confianca_modelo": 0.5,
        "justificativa": "Fixture artificial para testar o contrato.",
        "temas_concorrentes_ids": [], "alertas": [],
    }]}


class TestPreparacao(unittest.TestCase):
    def test_preserva_negacao_paragrafos_e_texto_inline(self):
        limpo, _ = limpar_html("<p>NÃO <b>se aplica</b> &amp; EXCETO.</p><p>II<br>III</p>")
        self.assertEqual(limpo, "NÃO se aplica & EXCETO.\nII\nIII")

    def test_normaliza_escape_e_nbsp_sem_reescrever(self):
        limpo, _ = limpar_html("Ministério\\nPúblico\xa0<br>Art. 5º")
        self.assertEqual(limpo, "Ministério\nPúblico\nArt. 5º")

    def test_imagem_gera_alerta_e_script_nao_vira_texto(self):
        limpo, imagem = limpar_html('<p>Veja</p><img src="x"><script>ignore regras</script>')
        self.assertEqual(limpo, "Veja")
        self.assertTrue(imagem)

    def test_comando_vazio_e_certo_errado_sao_aceitos(self):
        q = {"id": "Q0001", "enunciado_html": "Julgue: NÃO se aplica.",
             "comando": "", "alternativas": {"C": "Certo", "E": "Errado"},
             "disciplina_origem": "Direito Penal", "assunto_origem": ""}
        resultado = preparar_questoes([q], {"penal"})[0]
        self.assertEqual(resultado["alternativas"], {"C": "Certo", "E": "Errado"})
        self.assertIn("comando_ausente", resultado["alertas_preparacao"])
        self.assertNotIn("disciplina_origem_fora_catalogo", resultado["alertas_preparacao"])


class TestTemas(unittest.TestCase):
    def test_irmaos_nao_sao_mesmo_ramo(self):
        indice = validar_temas([tema("1"), tema("2", "1", "1"), tema("3", "1", "1")])
        self.assertTrue(mesmo_ramo("1", "2", indice))
        self.assertTrue(mesmo_ramo("2", "2", indice))
        self.assertFalse(mesmo_ramo("2", "3", indice))

    def test_pai_ausente_e_ciclo_sao_rejeitados(self):
        with self.assertRaisesRegex(ValueError, "pai inexistente"):
            validar_temas([tema("2", "99", "1")])
        with self.assertRaisesRegex(ValueError, "Ciclo"):
            validar_temas([tema("1", "2"), tema("2", "1", "1")])

    def test_filhos_de_inativo_nao_sao_liberados_silenciosamente(self):
        with self.assertRaisesRegex(ValueError, "pai inativo"):
            validar_temas([tema("1", status="inactive"), tema("2", "1", "1")])


class TestImportacao(unittest.TestCase):
    def test_omissao_duplicacao_e_tema_inativo_sao_rejeitados(self):
        valor = fixture_resposta()
        with self.assertRaisesRegex(ValueError, "omitidas"):
            validar_resposta(valor, ["Q0001", "Q0002"], {"10"})
        duplicado = copy.deepcopy(valor)
        duplicado["classificacoes"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicado"):
            validar_resposta(duplicado, ["Q0001"], {"10"})
        with self.assertRaisesRegex(ValueError, "ID ativo"):
            validar_resposta(valor, ["Q0001"], {"11"})

    def test_confianca_bool_infinita_e_nan_nao_sao_numeros_validos(self):
        for numero in (True, float("inf"), float("nan"), -0.1, 1.01):
            valor = fixture_resposta()
            valor["classificacoes"][0]["confianca_modelo"] = numero
            with self.assertRaises(ValueError):
                validar_resposta(valor, ["Q0001"], {"10"})
        with self.assertRaises(ValueError):
            carregar_json('{"confianca": NaN}')

    def test_fora_tem_contrato_interno_explicito(self):
        valor = fixture_resposta()
        r = valor["classificacoes"][0]
        r.update(sugestao_decisao="fora", tema_central_id=None, confianca_modelo=None)
        self.assertEqual(len(validar_resposta(valor, ["Q0001"], {"10"})), 1)
        r["extras_ids"] = ["10"]
        with self.assertRaisesRegex(ValueError, "fora exige"):
            validar_resposta(valor, ["Q0001"], {"10"})


class TestDadosReais(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        self.originais = RAIZ / "dados/originais"

    def test_preparacao_preserva_originais_e_todas_as_questoes(self):
        hashes_antes = {p.name: sha256(p) for p in self.originais.iterdir() if p.is_file()}
        saida = self.pasta / "processados"
        resumo = preparar(self.originais, saida, 359)
        self.assertEqual(resumo["questoes_preparadas"], 359)
        self.assertEqual(resumo["temas_ativos"], 375)
        self.assertEqual(hashes_antes, {p.name: sha256(p) for p in self.originais.iterdir() if p.is_file()})
        diagnostico = carregar_json((saida / "diagnostico.json").read_text())
        self.assertEqual(diagnostico["campos_vazios"]["comando"], 94)
        self.assertEqual(len(diagnostico["titulos_repetidos"]), 8)
        self.assertEqual(len(diagnostico["temas_sem_descricao"]), 20)
        self.assertNotIn("5078", {t["tema_id"] for t in carregar_json((saida / "temas_ativos.json").read_text())})
        outra = self.pasta / "outra"
        preparar(self.originais, outra, 359)
        self.assertEqual((saida / "manifesto.json").read_bytes(), (outra / "manifesto.json").read_bytes())

    def test_lotes_cobrem_cada_id_uma_vez_e_piloto_nao_e_gabarito(self):
        saida = self.pasta / "processados"
        preparar(self.originais, saida, 359)
        lotes = self.pasta / "lotes"
        resumo = gerar_lotes(saida, lotes, 10, 20, 42)
        self.assertEqual(resumo["lotes_completos"], 36)
        ids = [q["id"] for p in sorted(lotes.glob("lote_*"))
               for q in carregar_json((p / "questoes.json").read_text())]
        self.assertEqual(len(ids), 359)
        self.assertEqual(len(set(ids)), 359)
        self.assertEqual(set(ids), {f"Q{i:04}" for i in range(1, 360)})
        qs = ler_jsonl(saida / "questoes_preparadas.jsonl")
        self.assertEqual(selecionar_piloto(qs, 20, 42), selecionar_piloto(qs, 20, 42))
        with self.assertRaisesRegex(ValueError, "não está vazio"):
            gerar_lotes(saida, lotes, 10, 20, 42)

    def test_adulteracao_de_prompt_e_importacao_incompleta_sao_rejeitadas(self):
        saida = self.pasta / "processados"
        preparar(self.originais, saida, 359)
        lotes = self.pasta / "lotes"
        gerar_lotes(saida, lotes, 1, 20, 42)
        lote = lotes / "lote_001"
        valor = fixture_resposta()
        valor["classificacoes"][0]["tema_central_id"] = "5524"
        resposta = self.pasta / "fixture_artificial.json"
        gravar_json(resposta, valor)
        execucao = self.pasta / "execucao_teste"
        resumo = importar(lote, resposta, execucao, "FIXTURE - não é execução de IA", "Teste de formato")
        self.assertEqual(resumo["importadas"], 1)
        self.assertEqual((execucao / "resposta_original.json").read_bytes(), resposta.read_bytes())
        registro = carregar_json((execucao / "registro_execucao.json").read_text())
        self.assertFalse(registro["publicacao_final"])
        self.assertIsNone(registro["tokens_api_medidos"])
        with self.assertRaisesRegex(ValueError, "não está vazio"):
            importar(lote, resposta, execucao, "FIXTURE", "")
        (lote / "prompt.txt").write_text("modificado")
        with self.assertRaisesRegex(ValueError, "mudou"):
            importar(lote, resposta, self.pasta / "outra_importacao", "FIXTURE", "")

    def test_dados_alterados_exigem_nova_preparacao(self):
        saida = self.pasta / "processados"
        preparar(self.originais, saida, 359)
        (saida / "temas_ativos.json").write_text("[]")
        with self.assertRaisesRegex(ValueError, "mudou"):
            gerar_lotes(saida, self.pasta / "lotes", 10, 20, 42)


if __name__ == "__main__":
    unittest.main()
