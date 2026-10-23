import copy
import json
import math
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import finalizar_etapa2 as m
import runtime_etapa2 as rt
from test_teste_etapa2 import preparar


def preparar_teste(pasta):
    dados, metodo, politica, escopos, vocab = preparar(pasta)
    teste = pasta / "teste"
    m.teste_mod.executar(dados, metodo, politica, escopos, vocab, teste)
    return dados, metodo, politica, teste, escopos, vocab


def artefatos_runtime(pasta):
    dados, metodo, politica, teste, escopos, vocab = preparar_teste(pasta)
    destino = pasta / "modelo"
    rt.preparar_artefatos(dados / "temas.csv", escopos, vocab, m.cal.ler_json(metodo),
                         m.cal.ler_json(politica), metodo, politica, destino)
    return destino, dados


def qnova(qid="NOVA_1"):
    return {"id": qid, "enunciado_html": "<b>Investigação e arquivamento de inquérito</b>",
            "comando": "", "alternativas": {"A": "Arquivamento", "B": "Investigação"},
            "disciplina_origem": "Metadado incorreto", "assunto_origem": ""}


class TestEntregaEtapa2(unittest.TestCase):
    def test_artefato_nao_guarda_questoes_ou_rotulos_por_id(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta))
            modelo = (destino / "modelo.json").read_text()
            self.assertNotRegex(modelo, r"Q\d{4}")
            self.assertEqual({p.name for p in destino.iterdir()}, {"modelo.json", *rt.ARQUIVOS_DADOS})

    def test_inferencia_sem_folha_verdade_sem_rede_encoder_ou_bibliotecas_ml(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, dados = artefatos_runtime(Path(pasta))
            (dados / "folha_verdade.csv").unlink()
            original = rt.cal.base.ler_csv
            def leitor(caminho):
                if Path(caminho).name != "temas.csv":
                    raise AssertionError("Inferência leu rótulos ou experimentos")
                return original(caminho)
            with patch.object(rt.cal.base, "ler_csv", leitor), \
                    patch.object(rt.cal, "conferir_congelamento", side_effect=AssertionError("Não avaliar novamente")), \
                    patch.object(rt.cal, "construir_politica", side_effect=AssertionError("Não treinar")), \
                    patch.object(socket, "socket", side_effect=AssertionError("Sem rede")), \
                    patch.dict(sys.modules, {n: None for n in ("fastembed", "onnxruntime", "numpy", "sklearn", "reportlab")}):
                runtime = rt.Runtime(destino); linha, _ = runtime.classificar(qnova())
            self.assertEqual(linha["tema_central_id"], "10")

    def test_trocar_id_e_disciplina_nao_muda_tema_decisao_ou_confianca(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta)); runtime = rt.Runtime(destino)
            a, _ = runtime.classificar(qnova("Q0001"))
            b, _ = runtime.classificar(dict(qnova("NOVA_700"), disciplina_origem="Outro ramo"))
            self.assertNotEqual(a.pop("id"), b.pop("id")); self.assertEqual(a, b)

    def test_modificar_texto_de_id_conhecido_recalcula_ranking(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta)); runtime = rt.Runtime(destino)
            antes, _ = runtime.classificar(qnova("Q0001"))
            outra = {"id": "Q0001", "enunciado_html": "Penas sanções penas", "alternativas": {"A": "Penas sanções"}}
            depois, _ = runtime.classificar(outra)
            self.assertEqual(antes["tema_central_id"], "10")
            self.assertEqual(depois["tema_central_id"], "20")

    def test_sem_texto_ou_candidato_nao_inventa_tema_nem_fora(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta)); runtime = rt.Runtime(destino)
            for texto in ("", "xyzzqkft"):
                with self.assertRaises(ValueError):
                    runtime.classificar({"id": "NOVA", "enunciado_html": texto, "alternativas": {}})

    def test_empate_vai_revisar_e_top5_nao_vira_extras(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta)); runtime = rt.Runtime(destino)
            with patch.object(runtime.modelo, "ranquear", return_value=[("10", .5), ("20", .5)]):
                linha, _ = runtime.classificar(qnova())
            self.assertEqual(linha["decisao"], "revisar")
            self.assertEqual(linha["extras_ids"], "")

    def test_artefato_adulterado_e_codigo_diferente_sao_rejeitados(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta))
            p = destino / "modelo.json"; original = m.cal.ler_json(p)
            for campo, valor in (("sha256_codigo", {}), ("sha256_dados", {}), ("configuracao", {})):
                alterado = copy.deepcopy(original); alterado[campo] = valor; m.cal.escrever_json(p, alterado)
                with self.assertRaises(ValueError): rt.Runtime(destino)
            m.cal.escrever_json(p, original)
            with (destino / "temas.csv").open("a") as a: a.write(" ")
            with self.assertRaises(ValueError): rt.Runtime(destino)

    def test_confianca_e_suporte_nao_podem_ser_alterados_silenciosamente(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino, _ = artefatos_runtime(Path(pasta)); p = destino / "modelo.json"
            original = m.cal.ler_json(p)
            alterado = copy.deepcopy(original)
            alterado["politica"]["confianca_por_decisao"]["publicar"]["media_beta_1_1"] = .999
            m.cal.escrever_json(p, alterado)
            with self.assertRaises(ValueError): rt.Runtime(destino)

    def test_csv_rejeita_raiz_inativo_falta_id_e_confianca_nan(self):
        temas = {"1": {"ativo": True, "nivel": 0, "parent_id": ""},
                 "10": {"ativo": True, "nivel": 1, "parent_id": "1"},
                 "20": {"ativo": False, "nivel": 1, "parent_id": "1"}}
        linha = dict(zip(rt.CAMPOS_ENTREGA, ("A", "revisar", "10", "", ".5", "Dúvida")))
        rt.validar_entrega([linha], temas, ["A"])
        for alteracao in ({"tema_central_id": "1"}, {"tema_central_id": "20"}, {"confianca": "nan"}, {"motivo": ""}):
            with self.assertRaises(ValueError): rt.validar_entrega([dict(linha, **alteracao)], temas, ["A"])
        with self.assertRaises(ValueError): rt.validar_entrega([linha], temas, ["A", "B"])

    def test_jsonl_rejeita_duplicados_e_vazio(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / "questoes.jsonl"
            p.write_text(json.dumps(qnova()) + "\n" + json.dumps(qnova()))
            with self.assertRaises(ValueError): rt.ler_questoes(p)
            p.write_text("")
            with self.assertRaises(ValueError): rt.ler_questoes(p)

    def test_previsao_exclui_rotulados_e_preserva_confianca(self):
        linhas = [{"id": "G", "decisao": "publicar", "confianca": ".99"},
                  {"id": "A", "decisao": "publicar", "confianca": ".8"},
                  {"id": "B", "decisao": "revisar", "confianca": ".6"}]
        teste = {"teste": {"publicar": 2, "intervalo_binomial_95_publicadas": [.158, 1.]}}
        r = m.prever(linhas, {"G"}, teste)
        self.assertEqual(r["questoes_no_alvo"], 2); self.assertEqual(r["publicadas_no_alvo"], 1)
        self.assertEqual(r["precisao_prevista"], .8)
        self.assertEqual(r["cobertura_intervalo_exato"], [.5, .5])

    def test_cobertura_e_intervalo_arredondados_para_fora(self):
        valor = 23 / 559
        self.assertLessEqual(float(m.limite_texto(valor)), valor)
        self.assertGreaterEqual(float(m.limite_texto(valor, True)), valor)

    def test_sem_publicadas_precisao_indefinida_sem_afirmacao_de_acerto(self):
        teste = {"teste": {"publicar": 0, "intervalo_binomial_95_publicadas": [0., 1.]}}
        p = m.prever([{"id": "A", "decisao": "revisar", "confianca": ".6"}], set(), teste)
        self.assertFalse(p["precisao_definida"]); self.assertEqual(p["precisao_intervalo"], [0., 1.])

    def test_finalizacao_completa_e_reproducao_exata_csv_e_previsao(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta); entradas = preparar_teste(pasta)
            hashes = {p: m.cal.base.sha256(p) for p in pasta.rglob('*') if p.is_file()}
            vistos = []; original = rt.Runtime.classificar
            def registrar(self, q):
                vistos.append(q["id"]); return original(self, q)
            with patch.object(rt.Runtime, "classificar", registrar), patch.object(socket, "socket", side_effect=AssertionError("Sem rede")):
                resumo = m.executar(*entradas, pasta / "entrega")
            self.assertEqual(len(vistos), 659); self.assertEqual(len(set(vistos)), 659)
            self.assertEqual(resumo["total"]["questoes"], 659)
            self.assertEqual(resumo["fora_folha_verdade"]["questoes"], 559)
            self.assertEqual(resumo["antigas_fora_folha"]["questoes"], 259)
            self.assertEqual(resumo["recentes_300"]["questoes"], 300)
            self.assertEqual(resumo["registros_congelados_conferidos"], 100)
            self.assertIsNone(resumo["precisao_real_559"])
            m.executar(*entradas, pasta / "reproducao")
            for nome in ("publicacao.csv", "previsao.txt"):
                self.assertEqual((pasta / "entrega" / nome).read_bytes(), (pasta / "reproducao" / nome).read_bytes())
            for p, h in hashes.items(): self.assertEqual(m.cal.base.sha256(p), h)
            doc = m.cal.ler_json(pasta / "entrega/relatorio_paginas.json")
            self.assertEqual(len(doc["paginas"]), 4); self.assertIn("Memo", doc["paginas"][-1]["titulo"])
            manifesto = m.cal.ler_json(pasta / "entrega/manifesto_entrega.json")
            for nome, h in manifesto["sha256_artefatos"].items():
                self.assertEqual(m.cal.base.sha256(pasta / "entrega" / nome), h)

    def test_csv_se_reproduz_so_com_modelo_e_jsonl_sem_qualquer_rotulo(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta); destino, dados = artefatos_runtime(pasta)
            texto = pasta / "novas.jsonl"
            texto.write_text(json.dumps(qnova("NOVA_999")) + "\n", encoding="utf-8")
            with patch.object(rt.cal, "conferir_congelamento", side_effect=AssertionError("Não acessar folha")):
                r = rt.executar(destino, texto, pasta / "resultado")
            self.assertEqual(r["questoes"], 1); self.assertFalse(r["rotulos_consultados_na_inferencia"])

    def test_teste_alterado_impede_finalizacao(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta); entradas = preparar_teste(pasta)
            with (entradas[3] / "teste.csv").open("a") as p: p.write(" ")
            with self.assertRaises(ValueError): m.executar(*entradas, pasta / "entrega")
            self.assertFalse((pasta / "entrega").exists())

    def test_nao_sobrescreve_entrega_ou_classificacao_existentes(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / "salvo"; p.mkdir(); sentinela = p / "dado"; sentinela.write_text("preservar")
            with self.assertRaises(ValueError): m.executar(*(Path("ausente") for _ in range(6)), p)
            with self.assertRaises(ValueError): rt.executar(Path("ausente"), Path("ausente"), p)
            self.assertEqual(sentinela.read_text(), "preservar")


if __name__ == "__main__":
    unittest.main()
