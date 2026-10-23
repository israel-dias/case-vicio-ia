from __future__ import annotations

import copy
import csv
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import modelo as m
import experimento as e
import com_escopos_existentes as adapter


def temas_toy():
    def t(tid, pai, nivel, titulo, disciplina="Penal", ativo=True):
        return {"tema_id": tid, "parent_id": pai, "nivel": nivel, "titulo": titulo,
                "disciplina": disciplina, "caminho": disciplina+" > "+titulo,
                "descricao": "", "ativo": ativo, "status": "active" if ativo else "inactive"}
    return {"1": t("1", "", 0, "Penal"), "2": t("2", "1", 1, "Crimes contra a vida"),
            "3": t("3", "2", 2, "Homicídio"), "4": t("4", "2", 2, "Suicídio"),
            "5": t("5", "1", 1, "Prescrição"), "6": t("6", "", 0, "Processo Penal", "Processo Penal"),
            "7": t("7", "6", 1, "Crimes contra a vida", "Processo Penal"),
            "8": t("8", "6", 1, "Inquérito policial", "Processo Penal")}


def y(tid="3", extras="", fora="0"):
    return {"tema_central_id": tid, "extras_ids": extras, "fora_da_taxonomia": fora}


def q(texto="Sobre homicídio, assinale a alternativa correta."):
    return {"id": "X", "enunciado_html": texto, "comando": "Assinale a alternativa correta.",
            "alternativas": {"A": "Não há crime.", "B": "Há homicídio."},
            "disciplina_origem": "Penal", "assunto_origem": "Homicídio"}


def fixture(destino):
    temas = temas_toy()
    for i in range(9, 378):
        temas[str(i)] = {**temas["5"], "tema_id": str(i), "ativo": False, "status": "inactive"}
    destino.mkdir()
    campos = ["tema_id", "parent_id", "disciplina", "nivel", "titulo", "caminho", "descricao", "status"]
    with (destino/"temas.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore"); w.writeheader();w.writerows(temas.values())
    questoes = []
    labels = []
    for i in range(1, 660):
        texto = ("homicídio", "prescrição", "inquérito policial", "homicídio")[i % 4]
        item = q(f"{texto}: analise a situação número {i}.")
        item["id"] = f"Q{i:04}"
        questoes.append(item)
        if i <= 100:
            label = y(("3", "5", "8", "2")[i % 4]) if i % 10 else y("", fora="1")
            labels.append({"id": item["id"], **label})
    (destino/"questoes.jsonl").write_text("\n".join(json.dumps(a, ensure_ascii=False) for a in questoes), encoding="utf-8")
    with (destino/"folha_verdade.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "tema_central_id", "extras_ids", "fora_da_taxonomia"])
        w.writeheader();w.writerows(labels)


class TestMelhoriaFolha(unittest.TestCase):
    def test_regua_pais_filhos_extras_e_irmaos(self):
        ts = temas_toy()
        self.assertTrue(m.aceito("2", y(), ts))
        self.assertFalse(m.aceito("4", y(), ts))
        self.assertTrue(m.aceito("4", y(extras="2"), ts))
        self.assertTrue(m.aceito("5", y(extras="5"), ts))
        self.assertFalse(m.aceito("1", y(), ts))
        self.assertFalse(m.aceito("7", y(), ts))

    def test_fora_nao_recebe_tema_positivo(self):
        for tid in ("2", "3", "5", "8"):
            self.assertFalse(m.aceito(tid, y("", fora="1"), temas_toy()))

    def test_html_preserva_negacao_e_todas_alternativas(self):
        item = q("<p>N<b>ão</b> se admite.</p><!-- comentário semântico --><script>homicídio</script>")
        c = m.campos(item)
        self.assertIn("nao se admite", c["completo"])
        self.assertNotIn("comentario", c["completo"])
        self.assertEqual(c["enunciado"], "nao se admite")
        self.assertEqual(len(c["alternativas"]), 2)
        self.assertIn("nao ha crime", c["completo"])

    def test_citacoes_literais_nao_confundem_cp_cpp(self):
        a, _ = m.referencias_literais("Segundo o CPP e a Lei nº 9.099/95, art. 77.")
        self.assertIn("cpp", a);self.assertNotIn("cp", a)
        self.assertIn("lei:9099/1995", a)
        _, b = m.referencias_literais("art. 218-B do CP")
        self.assertIn("218-b", b)

    def test_id_nao_e_atributo_e_origem_nao_veta_ramo(self):
        cat = m.Catalogo(temas_toy())
        a, b = q(), q()
        b["id"] = "ID-totalmente-diferente"
        pa, pb = cat.transformar({"a": a, "b": b}).values()
        self.assertTrue(m.np.array_equal(pa["features"], pb["features"]))
        b["disciplina_origem"] = "Disciplina Unificada"
        pc = cat.transformar({"c": b})["c"]
        self.assertTrue(m.np.array_equal(pa["scores"], pc["scores"]))
        self.assertEqual(len(pa["features"]), len(cat.familias))

    def test_treino_rejeita_rotulo_do_holdout(self):
        cat = m.Catalogo(temas_toy())
        ps = cat.transformar({"a": q()})
        with self.assertRaises(ValueError):
            m.ajustar(ps, {"a": y(), "externo": y()}, cat.familias, cat.temas)
        with self.assertRaises(ValueError):
            e.calibrar_internamente(ps, {"a": y(), "externo": y()}, cat, "seed")

    def test_vizinhos_excluem_texto_identico_mesmo_com_outro_id(self):
        cat = m.Catalogo(temas_toy())
        ps = cat.transformar({"a": q(), "b": q()})
        x = m.vizinhanca(ps["a"], {"b": ps["b"]}, {"b": y()}, cat.familias, cat.temas)
        self.assertEqual(float(abs(x).sum()), 0)

    def test_folds_agrupam_duplicatas_e_rejeitam_sobreposicao(self):
        ps = {str(i): {"hash": str(i // 2)} for i in range(16)}
        ys = {i: y() for i in ps}
        fs = e.dividir(ps, ys, temas_toy(), 4, "teste")
        destino = {qid: k for k, ids in enumerate(fs) for qid in ids}
        for i in range(0, 16, 2):
            self.assertEqual(destino[str(i)], destino[str(i+1)])
        with self.assertRaises(ValueError):
            e.validar_separacao({"a": {"hash": "igual"}}, {"b": {"hash": "igual"}})

    def test_poucos_acertos_nao_ativam_publicacao(self):
        r = [{"elegivel": True, "correto": 1}] * 2
        self.assertFalse(m.escolher_politica(r, [.99, .99])["ativa"])
        r = [{"elegivel": False, "correto": 1}] * 20
        self.assertFalse(m.escolher_politica(r, [.99]*20)["ativa"])

    def test_confianca_nao_e_similaridade_e_json_preserva_modelo(self):
        mod = m.ajustar_linear([[0], [1], [2], [3]], [0, 0, 1, 1])
        antes = m.predizer_linear([[.2], [2.8]], mod).tolist()
        depois = m.predizer_linear([[.2], [2.8]], json.loads(json.dumps(mod))).tolist()
        self.assertEqual(antes, depois)
        self.assertTrue(all(0 < p < 1 for p in antes))
        with self.assertRaises(ValueError):
            m.predizer_linear([[float("nan")]], mod)

    def test_dois_sinais_altos_nao_exigem_margem(self):
        politica = {"ativa": True, "limiar": .9}
        self.assertEqual(m.decidir({"elegivel": True}, .96, politica), "publicar")
        self.assertEqual(m.decidir({"elegivel": False}, .96, politica), "revisar")

    def test_zero_publicadas_nao_significa_cem_porcento(self):
        r = {"id": "a", "decisao": "revisar", "confianca": .8, "correto": 1,
             "fora_oficial": 0, "top2_lexicais_aceitos": 0}
        self.assertIsNone(e.resumo([r])["precisao_publicadas"])

    def test_erro_em_fora_e_contado_e_nao_ajusta_previsao(self):
        r = {"id": "a", "tema_central_id": "2", "primeiro_lexical": "2", "segundo_lexical": "5",
             "decisao": "publicar", "confianca": .97}
        saida = e.avaliar([r], {"a": y("", fora="1")}, temas_toy())
        res = e.resumo(saida)
        self.assertEqual(res["erros_publicadas"], 1)
        self.assertEqual(res["fora_oficial_publicadas"], 1)
        self.assertEqual(saida[0]["confianca"], .97)

    def test_arvore_invalida_rejeitada(self):
        ts = temas_toy()
        ts["2"]["parent_id"] = "3"
        with self.assertRaises(ValueError):
            m.pais("3", ts)

    def test_saida_existente_preservada(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                e.executar(Path(d)/"dados_ausentes", d)

    def test_adaptador_rejeita_configuracao_ambigua(self):
        cfg = {"modo": "separados", "peso_escopo": .5, "familia": "media3"}
        self.assertEqual(adapter.configuracao_metodo({"configuracao": cfg}), cfg)
        with self.assertRaises(ValueError):
            adapter.configuracao_metodo({"a": cfg, "b": {**cfg, "peso_escopo": .4}})

    def test_relatorio_identifica_controle_com_escopos(self):
        texto = adapter.formatar_leitura(e.leitura, {}, 1.)
        self.assertIn("Nesta execução, o controle usa os escores", texto)
        self.assertNotIn("O controle usa o catálogo original", texto)

    def test_adaptador_preserva_arquivos_e_altera_apenas_evidencia_preparada(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("calibrar_etapa2.py", "experimento_escopos.py", "experimento_campos.py", "gerar_escopos.py",
                         "experimentos/escopos_001/metodo_congelado.json", "artefatos/escopos_v1/escopos.json",
                         "artefatos/escopos_v1/vocabulario_autorado.tsv"):
                p = root/name;p.parent.mkdir(parents=True, exist_ok=True);p.write_text("fixture")
            antes = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            cfg = {"modo": "separados", "peso_escopo": .5, "familia": "media3"}
            fake = types.SimpleNamespace(__file__=str(root/"calibrar_etapa2.py"),
                conferir_congelamento=lambda *a: ({"cfg": cfg}, {}, {}, temas_toy(), {}),
                esc=types.SimpleNamespace(ClassificadorEscopos=lambda *a: types.SimpleNamespace(pontuar=lambda q: {"2": .4, "5": .2})))
            with patch.dict(sys.modules, {"calibrar_etapa2": fake}):
                fabrica, origem = adapter.preparar(root, root/"dados")
            cat = fabrica(temas_toy())
            p = cat.transformar({"a": q()})["a"]
            self.assertEqual(p["scores"].tolist(), [.4, .2, 0., 0.])
            self.assertEqual(p["features"][:, 0].tolist(), p["scores"].tolist())
            self.assertTrue(origem["sha256"])
            self.assertEqual(antes, {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_integracao_so_100_sem_rede_parametros_antes_do_holdout(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            fixture(base/"dados")
            vistos = []
            transformar_real = m.Catalogo.transformar
            sinais_reais = m.sinais
            saida = base/"resultado"
            def transformar(cat, qs):
                vistos.extend(qs)
                return transformar_real(cat, qs)
            def sinais(perfil, familias, mods, treino, ys, temas):
                # Nos folds externos o arquivo já existe ao predizer.
                if len(treino) == 80:
                    self.assertTrue(list((saida/"modelos_folds").glob("*.json")))
                return sinais_reais(perfil, familias, mods, treino, ys, temas)
            with patch.object(m.Catalogo, "transformar", transformar), patch.object(m, "sinais", sinais), \
                 patch("socket.socket.connect", side_effect=AssertionError("Rede proibida")):
                resultados = e.executar(base/"dados", saida)
            self.assertEqual(len(vistos), 100)
            self.assertNotIn("Q0101", vistos)
            self.assertEqual(resultados["selecionado_internamente"]["avaliadas"], 100)
            audit = json.loads((saida/"auditoria_folds.json").read_text())
            for fold in audit:
                self.assertFalse(set(fold["treino_ids"]) & set(fold["avaliacao_ids"]))
                for interno in fold["folds_internos"]:
                    self.assertFalse(set(interno["treino_ids"]) & set(fold["avaliacao_ids"]))
            self.assertFalse((base/"publicacao.csv").exists())
            self.assertFalse((base/"previsao.txt").exists())


if __name__ == "__main__":
    unittest.main()
