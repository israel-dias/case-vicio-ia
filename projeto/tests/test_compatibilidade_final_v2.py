from __future__ import annotations

import copy
import csv
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compatibilidade_v2 import runtime as rt
import finalizar_compatibilidade_v2 as entrega
import treinar_compatibilidade_v2 as treino

ROOT = Path(__file__).resolve().parents[1]
ARTEFATOS = ROOT/"artefatos/compatibilidade_v2"


class TestCompatibilidadeFinalV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = rt.Runtime(ARTEFATOS)
        cls.questoes = rt.legado.ler_questoes(ROOT/"dados/anexos/questoes.jsonl")

    def test_runtime_sem_rotulos_sem_rede_sem_treino_supervisionado(self):
        abrir = Path.open
        def protegido(path, *args, **kwargs):
            if path.name == "folha_verdade.csv":
                raise AssertionError("Inferência não pode ler a folha-verdade")
            return abrir(path, *args, **kwargs)
        with patch.object(Path, "open", protegido), \
             patch("socket.socket.connect", side_effect=AssertionError("Rede proibida")), \
             patch.object(rt.f.LogisticRegression, "fit", side_effect=AssertionError("Treino proibido")):
            inferencia = rt.Runtime(ARTEFATOS)
            linha, registro = inferencia.classificar(self.questoes[0])
        self.assertIn(linha["decisao"], {"publicar", "revisar"})
        self.assertEqual(registro["tema_central_id"], linha["tema_central_id"])

    def test_id_e_so_identificador_da_saida(self):
        q = self.questoes[149]
        a, _ = self.runtime.classificar(q)
        outro = {**q, "id": "importacao_nova_001"}
        b, _ = self.runtime.classificar(outro)
        self.assertEqual({k:v for k,v in a.items() if k!="id"}, {k:v for k,v in b.items() if k!="id"})

    def test_texto_alterado_recalcula_sinais_mesmo_com_id_conhecido(self):
        q = self.questoes[0]
        _, a = self.runtime.classificar(q)
        outro = {**q, "enunciado_html": "Inquérito policial: conclusão e arquivamento.", "comando": "",
                 "alternativas": {"A": "Conclusão do inquérito", "B": "Arquivamento do inquérito"},
                 "assunto_origem": "Inquérito policial"}
        _, b = self.runtime.classificar(outro)
        self.assertNotEqual(a["sha256_texto"], b["sha256_texto"])
        self.assertNotEqual(a["top5_escopos"], b["top5_escopos"])

    def test_artefato_nao_contem_tabela_de_questoes(self):
        texto = (ARTEFATOS/"modelo.json").read_text()
        self.assertIsNone(re.search(r'Q\d{4}', texto))
        self.assertFalse(self.runtime.registro["origem"]["tabela_de_respostas_por_questao"])
        self.assertEqual(self.runtime.registro["origem"]["sem_rotulo_usados_no_ajuste"], 0)

    def test_alteracao_do_modelo_e_dos_dados_e_detectada(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"modelo"
            shutil.copytree(ARTEFATOS, p)
            arq = p/"modelo.json"
            arq.write_text(arq.read_text()+" ")
            with self.assertRaises(ValueError):
                rt.Runtime(p)
            shutil.copyfile(ARTEFATOS/"modelo.json", arq)
            arq = p/"temas.csv"
            arq.write_text(arq.read_text()+"\n")
            with self.assertRaises(ValueError):
                rt.Runtime(p)

    def test_modelo_rejeita_probabilidades_e_parametros_invalidos(self):
        mod = {"dimensao": 1, "media": [0.], "escala": [1.], "coeficientes": [1.], "intercepto": 0.}
        for campo, valor in (("escala", [0.]), ("coeficientes", [float("nan")]), ("media", [True])):
            errado = {**mod, campo: valor}
            with self.assertRaises(ValueError):
                rt.validar_linear(errado, 1)

    def test_contrato_csv_659_e_previsao_so_559(self):
        rs = entrega.ler_csv(ROOT/"entrega_etapa2_v2/publicacao.csv")
        self.assertEqual(len(rs), 659)
        rt.legado.validar_entrega(rs, self.runtime.temas, [q["id"] for q in self.questoes])
        resumo = json.loads((ROOT/"entrega_etapa2_v2/resumo_entrega.json").read_text())
        self.assertEqual(resumo["fora_folha_verdade"]["questoes"], 559)
        self.assertEqual(resumo["recentes_300"]["questoes"], 300)
        self.assertFalse(resumo["previsao"]["meta_95_sustentada"])
        self.assertIsNone(resumo["precisao_real_559"])

    def test_fila_revisao_explica_regra_sem_usar_dois_temas_como_veto(self):
        rs = entrega.ler_csv(ROOT/"entrega_etapa2_v2/publicacao.csv")
        for r in rs:
            if r["decisao"] == "revisar":
                self.assertTrue(r["motivo"])
                self.assertNotIn("dúvida entre ramos", r["motivo"])
                self.assertTrue("corte" in r["motivo"] or "evidência textual" in r["motivo"])

    def test_sem_publicadas_precisao_nao_e_cem_porcento(self):
        cv = {n: {"publicar": 0, "acertos_publicadas": 0} for n in ("compatibilidade_fixa", "selecionado_internamente")}
        p = entrega.prever([{"id":"novo", "decisao":"revisar", "confianca":".7"}], set(), cv)
        self.assertFalse(p["precisao_definida"])
        self.assertEqual(p["precisao_intervalo"], [0., 1.])

    def test_sobrescrita_rejeitada(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                rt.executar(ARTEFATOS, ROOT/"dados/anexos/questoes.jsonl", Path(d))
            with self.assertRaises(ValueError):
                entrega.executar(ROOT/"dados/anexos", ARTEFATOS, ROOT/"experimentos/folha_v2_escopos_001", Path(d))

    def test_novo_treino_recebe_apenas_os_100_rotulados(self):
        vistos = []
        transformar = rt.CatalogoCompatibilidade.transformar
        def registrar(cat, qs):
            vistos.extend(qs)
            return transformar(cat, qs)
        with tempfile.TemporaryDirectory() as d, patch.object(rt.CatalogoCompatibilidade, "transformar", registrar), \
             patch("socket.socket.connect", side_effect=AssertionError("Rede proibida")):
            resumo = treino.executar(ROOT/"dados/anexos", ROOT/"experimentos/folha_v2_escopos_001", Path(d)/"modelo")
        self.assertEqual(len(vistos), 100)
        self.assertEqual(resumo["sem_rotulo_usadas_no_ajuste"], 0)
        self.assertTrue(all(int(qid[1:]) <= 359 for qid in vistos))

    def test_regeneracao_calcula_csv_identico_sem_folha_verdade(self):
        original = (ROOT/"entrega_etapa2_v2/publicacao.csv").read_bytes()
        abrir = Path.open
        def protegido(path, *args, **kwargs):
            if path.name == "folha_verdade.csv":
                raise AssertionError("Rótulos proibidos na regeneração")
            return abrir(path, *args, **kwargs)
        with tempfile.TemporaryDirectory() as d, patch.object(Path, "open", protegido), \
             patch("socket.socket.connect", side_effect=AssertionError("Rede proibida")), \
             patch.object(rt.f.LogisticRegression, "fit", side_effect=AssertionError("Treino proibido")):
            destino = Path(d)/"reproduzida"
            resumo = rt.executar(ARTEFATOS, ROOT/"dados/anexos/questoes.jsonl", destino)
            self.assertEqual((destino/"publicacao.csv").read_bytes(), original)
            self.assertFalse(resumo["rotulos_consultados_na_inferencia"])


if __name__ == "__main__":
    unittest.main()
