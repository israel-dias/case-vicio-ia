"""Reexecuta o alvo inteiro com rede, treino, rótulos e recalibração bloqueados."""
import argparse
import csv
import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import legado, sha
from isolamento_v17 import modelo as m
from classificar_isolamento_v17 import executar


def verificar(projeto, experimento, saida):
    projeto, experimento, saida = [Path(x).resolve() for x in [projeto, experimento, saida]]
    with (experimento/"classificacoes_559_todas_variantes.csv").open() as arq:
        anteriores = list(csv.DictReader(arq))
    modelos = json.loads((experimento/"modelos_finais.json").read_text())
    abrir = Path.open
    preparar = m.preparar
    capturado = {}

    def protegido(path, *args, **kwargs):
        if path.name == "folha_verdade.csv":
            raise AssertionError("Tentou ler rótulos")
        return abrir(path, *args, **kwargs)

    def preparar_uma_vez(cat, dic, qs):
        if capturado:
            raise AssertionError("Preparação repetida inesperada")
        pp = preparar(cat, dic, qs)
        capturado.update(cat=cat, pp=pp)
        return pp

    with patch.object(Path, "open", protegido), \
         patch.object(socket, "socket", side_effect=AssertionError("rede")), \
         patch.object(f, "carregar", side_effect=AssertionError("rótulos")), \
         patch.object(f, "aceito", side_effect=AssertionError("avaliação com rótulo")), \
         patch.object(m, "ajustar", side_effect=AssertionError("treino")), \
         patch.object(m.a, "calibrar", side_effect=AssertionError("recalibração")), \
         patch.object(f.LogisticRegression, "fit", side_effect=AssertionError("fit supervisionado")), \
         patch.object(m, "preparar", side_effect=preparar_uma_vez):
        selecionadas = executar(projeto, experimento, experimento/"questoes_559_sem_rotulos.jsonl", saida)
        provas = {}
        for v in m.VARIANTES:
            rows = selecionadas if v == modelos["selecionado"] else m.aplicar(
                capturado["pp"], modelos["modelos"][v], capturado["cat"], v)
            ant = {r["id"]: r for r in anteriores if r["variante"] == v}
            if len(rows) != 559 or {r["id"] for r in rows} != set(ant):
                raise AssertionError("Conjunto alvo diferente")
            for r in rows:
                a = ant[r["id"]]
                for k in ["tema_central_id", "decisao", "motivo", "candidatos_ids"]:
                    if r[k] != a[k]:
                        raise AssertionError((v, r["id"], k))
                if r["confianca"] != float(a["confianca"]):
                    raise AssertionError((v, r["id"], "confianca"))
            provas[v] = {"questoes": len(rows), "publicar": sum(r["decisao"] == "publicar" for r in rows),
                         "reproducao_exata_decisoes_temas_confiancas": True}
    reg = {"variantes": provas, "total_previsoes_conferidas": 559*len(provas),
           "selecionada_executada_pelo_comando_publico": modelos["selecionado"],
           "rede_rotulos_treino_avaliador_e_recalibracao_bloqueados": True,
           "entrada_sha256": sha(experimento/"questoes_559_sem_rotulos.jsonl"),
           "csv_resultante_sha256": sha(saida/"classificacoes_experimentais.csv"),
           "precisao_real_559": None, "promove_entrega": False}
    (experimento/"reproducao_verificada.json").write_text(json.dumps(reg, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(reg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path("."))
    p.add_argument("--experimento", type=Path, default=Path("experimentos/isolamento_v17_001"))
    p.add_argument("--saida", type=Path, required=True)
    z = p.parse_args()
    verificar(z.projeto, z.experimento, z.saida)
