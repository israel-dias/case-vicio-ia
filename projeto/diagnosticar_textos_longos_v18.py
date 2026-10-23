"""Diagnóstico de extensão e contexto nas referências; não altera inferência."""
import argparse
import csv
import json
from pathlib import Path

from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha


def executar(projeto, saida):
    projeto, saida = Path(projeto).resolve(), Path(saida).resolve()
    if saida.exists():
        raise ValueError("Use saída nova.")
    dados = projeto/"dados/anexos"
    questoes, temas, ys = f.carregar(dados)
    avaliacao = projeto/"experimentos/isolamento_v17_001/avaliacao_100.csv"
    with avaliacao.open(encoding="utf-8", newline="") as arq:
        rr = {r["id"]: r for r in csv.DictReader(arq) if r["avaliacao"] == "primeiro_fusao_v15"}
    if len(rr) != 100 or set(rr) != set(ys):
        raise ValueError("Avaliação e referências incompatíveis.")
    campos = {i: f.campos(questoes[i]) for i in rr}
    quartis = []
    for campo in ["enunciado", "completo"]:
        ordem = sorted(rr, key=lambda i: (len(campos[i][campo].split()), i))
        for n in range(4):
            ids = ordem[25*n:25*(n+1)]
            c1 = sum(int(rr[i]["correto"]) for i in ids)
            c5 = sum(any(f.aceito(t, ys[i], temas) for t in rr[i]["candidatos_ids"].split(";")) for i in ids)
            quartis.append({"campo": campo, "quartil": n+1, "questoes": len(ids),
                "min_palavras": len(campos[ids[0]][campo].split()),
                "max_palavras": len(campos[ids[-1]][campo].split()),
                "com_tema": sum(int(ys[i]["fora_da_taxonomia"]) == 0 for i in ids),
                "acertos_top1": c1, "tema_aceito_top5": c5,
                "erros_com_tema_aceito_ainda_no_top5": c5-c1, "ids": ids})
    erros = sorted((i for i in rr if rr[i]["correto"] == "0"),
                   key=lambda i: (-len(campos[i]["enunciado"].split()), i))
    exemplos = [{"id": i, "questao": questoes[i], "referencia": ys[i], "previsao_v17": rr[i],
                 "palavras_enunciado": len(campos[i]["enunciado"].split())} for i in erros[:10]]
    saida.mkdir(parents=True)
    resultado = {"versao": "diagnostico_contexto_v18_1", "referencias_expostas": 100,
                 "alvo_559_avaliado": False, "quartis": quartis,
                 "corte_por_tamanho_ativado": False, "classificacoes_modificadas": 0,
                 "causalidade_demonstrada": False,
                 "nota": "Quartis têm 25 referências cada e são somente descrição; tamanho não determina tema nem decisão.",
                 "fontes_sha256": {"avaliacao_100": sha(avaliacao), "questoes": sha(dados/"questoes.jsonl"),
                                      "folha_verdade": sha(dados/"folha_verdade.csv"),
                                      "codigo_diagnostico": sha(Path(__file__))}}
    for nome, obj in [("resumo_contexto.json", resultado), ("dez_erros_longos_referencias.json", exemplos)]:
        (saida/nome).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in resultado.items() if k != "fontes_sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path("."))
    p.add_argument("--saida", type=Path, required=True)
    z = p.parse_args()
    executar(z.projeto, z.saida)
