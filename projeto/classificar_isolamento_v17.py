"""Classifica textos novos com candidatos e comparador congelados; sem LLM."""
import argparse
import csv
import json
from pathlib import Path

from compatibilidade_v2.runtime import legado, validar_linear
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from isolamento_v17 import modelo as m
from isolamento_v17.metricas import medir


def executar(projeto, experimento, questoes, saida, variante="selecionado"):
    projeto, experimento, questoes, saida = [Path(p).resolve() for p in [projeto, experimento, questoes, saida]]
    if saida.exists():
        raise ValueError("Use saída nova.")
    registro = json.loads((experimento/"manifesto_inferencia.json").read_text())
    if registro["versao"] != "isolamento_v17_1":
        raise ValueError("Versão do manifesto incompatível.")
    verificar(projeto, registro["projeto_sha256"])
    verificar(experimento, registro["artefatos_sha256"])
    modelos = json.loads((experimento/"modelos_finais.json").read_text())
    if modelos["versao"] != "isolamento_v17_1" or modelos["top_k"] != m.TOP_K:
        raise ValueError("Versão ou quantidade de candidatos incompatível.")
    if variante == "selecionado":
        variante = modelos["selecionado"]
    if variante not in m.VARIANTES:
        raise ValueError("Variante desconhecida.")
    pack = modelos["modelos"][variante]
    validar_linear(pack["modelo"], len(m.ATRIBUTOS[m.COMPARADOR[variante]]))
    validar_linear(pack["calibrador"], 1)
    cat, _ = carregar_catalogo(projeto)
    dic = Dicionario(json.loads((projeto/"vocabulario_v8/dicionario.json").read_text()), cat.temas, cat.familias)
    qs = {q["id"]: q for q in legado.ler_questoes(questoes)}
    pp = m.preparar(cat, dic, qs)
    rows = sorted(m.aplicar(pp, pack, cat, variante), key=lambda r: r["id"])
    saida.mkdir(parents=True)
    with (saida/"classificacoes_experimentais.csv").open("w", encoding="utf-8", newline="") as arq:
        w = csv.DictWriter(arq, fieldnames=["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ["id", "decisao", "tema_central_id", "confianca", "motivo"]} | {"extras_ids": ""})
    with (saida/"rastreabilidade.jsonl").open("w", encoding="utf-8") as arq:
        for r in rows:
            arq.write(json.dumps(r, ensure_ascii=False, allow_nan=False)+"\n")
    resumo = medir(rows) | {"variante": variante, "folha_verdade_lida": False,
        "treino_supervisionado": False, "calibracao_reajustada": False,
        "chamadas_llm": 0, "promove_entrega": False,
        "indices": "TF-IDF reconstruído somente do catálogo congelado; nenhum ajuste com textos ou rótulos das entradas."}
    (saida/"resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2), flush=True)
    return rows


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path("."))
    p.add_argument("--experimento", type=Path, default=Path("experimentos/isolamento_v17_001"))
    p.add_argument("--questoes", type=Path, default=Path("experimentos/isolamento_v17_001/questoes_559_sem_rotulos.jsonl"))
    p.add_argument("--saida", type=Path, required=True)
    p.add_argument("--variante", choices=["selecionado", *m.VARIANTES], default="selecionado")
    z = p.parse_args()
    executar(z.projeto, z.experimento, z.questoes, z.saida, z.variante)
