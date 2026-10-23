import csv
import io
import json
import re
import socket
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from compatibilidade_v2 import features as f
from isolamento_v17 import modelo as m
from classificar_isolamento_v17 import executar


class TestRuntimeV17(unittest.TestCase):
    projeto = Path(__file__).resolve().parents[2]
    experimento = projeto/"experimentos/isolamento_v17_001"

    def test_modelo_congelado_nao_contem_respostas_por_id(self):
        texto = (self.experimento/"modelos_finais.json").read_text()
        self.assertIsNone(re.search(r"Q\d{4}", texto))
        d = json.loads(texto)
        self.assertEqual(set(d["modelos"]), set(m.VARIANTES))

    def test_saida_existente_nao_e_sobrescrita(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "saída nova"):
                executar(self.projeto, self.experimento, "ausente", tmp)

    def test_artefato_alterado_e_rejeitado_antes_de_abrir_entrada(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            exp = p/"experimento"
            exp.mkdir()
            for n in ["manifesto_inferencia.json", "modelos_finais.json", "escolha_antes_559.json"]:
                (exp/n).write_bytes((self.experimento/n).read_bytes())
            (exp/"modelos_finais.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "alterado"):
                executar(self.projeto, exp, p/"entrada_ausente", p/"saida")

    def test_textos_novos_sem_rede_rotulos_treino_ou_recalibracao(self):
        q = {"id": "texto_novo_a", "enunciado_html": "A respeito da interceptação telefônica, julgue o item: a autorização deve ser judicial.",
             "comando": "", "alternativas": {"C": "Certo", "E": "Errado"},
             "disciplina_origem": "Processo Penal", "assunto_origem": "Provas"}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            entrada = p/"novas.jsonl"
            entrada.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in [q, {**q, "id": "texto_novo_b"}])+"\n")
            abrir = Path.open

            def protegido(path, *args, **kwargs):
                if path.name == "folha_verdade.csv":
                    raise AssertionError("Inferência tentou ler rótulos")
                return abrir(path, *args, **kwargs)

            with patch.object(Path, "open", protegido), \
                 patch.object(socket, "socket", side_effect=AssertionError("rede")), \
                 patch.object(f, "carregar", side_effect=AssertionError("rótulos")), \
                 patch.object(f, "aceito", side_effect=AssertionError("avaliador")), \
                 patch.object(m, "ajustar", side_effect=AssertionError("treino")), \
                 patch.object(m.a, "calibrar", side_effect=AssertionError("recalibração")), \
                 patch.object(f.LogisticRegression, "fit", side_effect=AssertionError("fit supervisionado")), \
                 redirect_stdout(io.StringIO()):
                rr = executar(self.projeto, self.experimento, entrada, p/"saida")
            for k in ["tema_central_id", "confianca", "decisao", "candidatos_ids"]:
                self.assertEqual(rr[0][k], rr[1][k])


if __name__ == "__main__":
    unittest.main()
