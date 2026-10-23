"""Consolida a versão 2 já congelada; não treina ou seleciona outro modelo."""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from compatibilidade_v2 import runtime as rt
from compatibilidade_v2 import relatorio as rel
import treinar_compatibilidade_v2 as treino


def ler_csv(p):
    with Path(p).open(encoding="utf-8-sig", newline="") as arq:
        return list(csv.DictReader(arq))


def contar(linhas):
    c = Counter(r["decisao"] for r in linhas)
    return {"questoes": len(linhas), "decisoes": {d: c[d] for d in ("publicar", "revisar", "fora")},
            "cobertura": c["publicar"]/len(linhas) if linhas else 0.}


def verificar_metricas_cv(pasta, rotulos, temas):
    resumo = json.loads((pasta/"resumo.json").read_text())["metodos"]
    for nome, esperado in resumo.items():
        linhas = ler_csv(pasta/f"previsoes_{nome}.csv")
        if len(linhas) != 100 or {r["id"] for r in linhas} != set(rotulos):
            raise ValueError("Previsões CV de outro conjunto.")
        for r in linhas:
            ok = int(rt.f.aceito(r["tema_central_id"], rotulos[r["id"]], temas))
            if ok != int(r["correto"]):
                raise ValueError("Acerto declarado na CV diverge da folha oficial.")
        pubs = [r for r in linhas if r["decisao"] == "publicar"]
        acertos = sum(int(r["correto"]) for r in pubs)
        if (esperado["publicar"] != len(pubs) or esperado["acertos_publicadas"] != acertos
                or esperado["precisao_publicadas"] != (acertos/len(pubs) if pubs else None)):
            raise ValueError("Métricas da CV não reproduzem seus registros.")
    return resumo


def prever(linhas, ids_rotulados, cv):
    alvo = [r for r in linhas if r["id"] not in ids_rotulados]
    pubs = [r for r in alvo if r["decisao"] == "publicar"]
    p = math.fsum(float(r["confianca"]) for r in pubs)/len(pubs) if pubs else 0.
    faixas = [rt.cal.intervalo_exato(cv[n]["acertos_publicadas"], cv[n]["publicar"])
              for n in ("compatibilidade_fixa", "selecionado_internamente")]
    faixa = [min(a[0] for a in faixas), max(a[1] for a in faixas)] if pubs else [0., 1.]
    faixa = [min(faixa[0], p), max(faixa[1], p)]
    cobertura = len(pubs)/len(alvo) if alvo else 0.
    return {"precisao_prevista": p, "precisao_intervalo": faixa,
        "cobertura_prevista": cobertura, "cobertura_intervalo_exato": [cobertura, cobertura],
        "publicadas_no_alvo": len(pubs), "questoes_no_alvo": len(alvo), "precisao_definida": bool(pubs),
        "origem_precisao": "Média das probabilidades do calibrador congelado nas publicadas fora da folha-verdade.",
        "origem_intervalo": "Faixa de sensibilidade: união das faixas binomiais descritivas de CV da variante fixa e da seleção interna, ampliada se necessário para conter a previsão. Não é intervalo de confiança válido para a precisão das 559.",
        "origem_cobertura": "Fração exata das decisões conhecidas nas 559; não prevê semanas futuras.",
        "meta_95_sustentada": False}


def arredondar(v, superior=False):
    escala = 10**8
    a = math.ceil(v*escala) if superior else math.floor(v*escala)
    return f"{a/escala:.8f}"


def texto_previsao(p):
    lo, hi = p["precisao_intervalo"]
    cobertura = p["cobertura_prevista"]
    return (f"precisao_prevista: {p['precisao_prevista']:.8f}\n"
            f"precisao_intervalo: {arredondar(lo)}-{arredondar(hi, True)}\n"
            f"cobertura_prevista: {cobertura:.8f}\n"
            f"cobertura_intervalo: {arredondar(cobertura)}-{arredondar(cobertura, True)}\n\n"
            f"Universo: {p['questoes_no_alvo']} questões fora da folha-verdade; {p['publicadas_no_alvo']} publicadas.\n"
            "A precisão prevista é a média das probabilidades de acerto calculadas pelo modelo congelado para o tema central. "
            "Não é a similaridade do texto, nem uma precisão verdadeira medida nas questões sem rótulo.\n"
            "A compatibilidade foi treinada nos 100 exemplos oficiais; o calibrador e o corte final usam sinais fora do treino (OOF) desses mesmos 100. "
            "O corte selecionou 27 acertos em 28 itens do desenvolvimento. Essa métrica sofre otimismo de seleção e não é teste externo.\n"
            "Na CV aninhada de desenvolvimento, a variante fixa publicou 20 itens e acertou 20; a seleção interna de variantes acertou 19 de 20. "
            "A escolha da variante fixa ocorreu após observar esses resultados. Os 100 rótulos já influenciaram a preparação e discussões anteriores.\n"
            "A faixa de precisão usa a união dos intervalos binomiais descritivos desses dois resultados de CV. "
            "É uma faixa de sensibilidade, não um intervalo de confiança para a precisão das 559: não corrige correlação entre folds, exposição prévia, seleção de variante ou mudança de distribuição.\n"
            "A cobertura é conhecida exatamente para este lote; o intervalo cobre apenas o arredondamento a oito casas decimais. "
            "Não representa incerteza sobre o número de publicações já calculado nem cobertura de importações futuras.\n"
            "A precisão verdadeira das 559, especialmente das 300 recentes, permanece desconhecida. "
            "A previsão central está abaixo de 95%; esta entrega não demonstra que a meta mínima tenha sido alcançada.\n"
            + ("Sem publicadas, a precisão é indefinida; zero na primeira linha é apenas convenção de formato.\n" if not p["precisao_definida"] else ""))


def comparacao(antes, depois):
    if {r["id"] for r in antes} != {r["id"] for r in depois}:
        raise ValueError("Comparação entre universos diferentes.")
    a = {r["id"]: r for r in antes}
    transicoes = Counter(a[r["id"]]["decisao"]+" -> "+r["decisao"] for r in depois)
    return {"transicoes": dict(transicoes),
        "mudancas_tema": sum(a[r["id"]]["tema_central_id"] != r["tema_central_id"] for r in depois),
        "mudancas_confianca": sum(a[r["id"]]["confianca"] != r["confianca"] for r in depois),
        "nota": "Mudança de decisão/confiança não demonstra melhora da precisão nas questões sem rótulos."}


def executar(dados, artefatos, experimento, saida):
    saida = Path(saida)
    if saida.exists():
        raise ValueError("Saída existente: use outra pasta para preservar a entrega.")
    qs, temas, ys = rt.f.carregar(dados)
    if len(qs) != 659 or len(ys) != 100:
        raise ValueError("Entrega requer os anexos de 659 questões e 100 rótulos.")
    treino.conferir_experimento(experimento, dados, ys, temas)
    cv = verificar_metricas_cv(experimento, ys, temas)
    registro = json.loads((artefatos/"modelo.json").read_text())
    if registro["origem"]["previsoes_oof_sha256"] != rt.sha(experimento/"previsoes_compatibilidade_fixa.csv"):
        raise ValueError("Modelo final não corresponde ao experimento informado.")
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".entrega-v2-", dir=saida.parent))
    try:
        rt.executar(artefatos, dados/"questoes.jsonl", tmp/"_classificacao")
        for p in (tmp/"_classificacao").iterdir():
            shutil.move(p, tmp/p.name)
        (tmp/"_classificacao").rmdir()
        linhas = ler_csv(tmp/"publicacao.csv")
        alvo = [r for r in linhas if r["id"] not in ys]
        antigos = [r for r in alvo if int(r["id"][1:]) <= 359]
        recentes = [r for r in alvo if int(r["id"][1:]) >= 360]
        if (len(alvo), len(antigos), len(recentes)) != (559, 259, 300):
            raise ValueError("Recortes da entrega diferentes de 559 = 259 + 300.")
        previsao = prever(linhas, set(ys), cv)
        inferencia = json.loads((tmp/"resumo_classificacao.json").read_text())
        tempo_50000 = inferencia["tempos_segundos"]["classificacao"]*50000/659
        revisoes = (1-contar(alvo)["cobertura"])*50000
        resumo = {"versao": rt.VERSAO, "total": contar(linhas), "fora_folha_verdade": contar(alvo),
            "antigas_sem_rotulo": contar(antigos), "recentes_300": contar(recentes),
            "rotuladas_100": contar([r for r in linhas if r["id"] in ys]),
            "previsao": previsao, "cv_desenvolvimento": cv, "politica_final": registro["politica"],
            "precisao_real_559": None, "tempos": inferencia["tempos_segundos"], "ambiente": inferencia["ambiente"],
            "producao_cenario": {"questoes_semana": 50000, "classificacao_segundos_extrapolados": tempo_50000,
                "tarifa_compute_usd_hora_hipotetica": .05, "compute_usd_extrapolado": tempo_50000/3600*.05,
                "compute_usd_por_questao_extrapolado": tempo_50000/3600*.05/50000,
                "revisoes_projetadas": revisoes, "minutos_por_revisao_hipoteticos": 2,
                "horas_revisao_projetadas": revisoes*2/60,
                "nota": "Extrapolação do lote, não benchmark de 50 mil questões únicas; preço e tempo humano são hipóteses, não cotações nem medições."}}
        anterior = Path(__file__).parent/"entrega_etapa2/publicacao.csv"
        if anterior.exists():
            resumo["comparacao_v1_v2"] = comparacao(ler_csv(anterior), linhas)
        rt.escrever(tmp/"resumo_entrega.json", resumo)
        (tmp/"previsao.txt").write_text(texto_previsao(previsao), encoding="utf-8")
        documento = rel.documento(resumo)
        rt.escrever(tmp/"relatorio_paginas.json", documento)
        (tmp/"relatorio.md").write_text(rel.markdown(documento), encoding="utf-8")
        (tmp/"README.md").write_text(rel.readme(resumo), encoding="utf-8")
        rastros = {r["id"]: r for r in (json.loads(l) for l in (tmp/"rastreabilidade.jsonl").read_text().splitlines())}
        fila = [{"id": r["id"], "tema_sugerido_id": r["tema_central_id"], "caminho": temas[r["tema_central_id"]]["caminho"],
                 "confianca": r["confianca"], "motivo": r["motivo"]} for r in linhas if r["decisao"]=="revisar"]
        fila.sort(key=lambda r: (float(r["confianca"]), r["id"]))
        if fila:
            rt.cal.salvar_csv(tmp/"fila_revisao.csv", fila, list(fila[0]))
        shutil.copytree(artefatos, tmp/"modelo")
        rt.escrever(tmp/"manifesto_entrega.json", {"versao": rt.VERSAO,
            "anexos_sha256": {n: rt.sha(dados/n) for n in ("questoes.jsonl", "temas.csv", "folha_verdade.csv")},
            "modelo_sha256": rt.sha(artefatos/"modelo.json"),
            "arquivos_sha256": {str(p.relative_to(tmp)): rt.sha(p) for p in sorted(tmp.rglob("*")) if p.is_file()}})
        tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    p.add_argument("--artefatos", type=Path, default=Path("artefatos/compatibilidade_v2"))
    p.add_argument("--experimento", type=Path, default=Path("experimentos/folha_v2_escopos_001"))
    p.add_argument("--saida", type=Path, default=Path("entrega_etapa2_v2"))
    args = p.parse_args()
    try:
        resumo = executar(args.dados, args.artefatos, args.experimento, args.saida)
    except (OSError, ValueError, KeyError) as exc:
        p.exit(1, f"Erro: {exc}\n")
    print(json.dumps({k: resumo[k] for k in ("total", "fora_folha_verdade", "recentes_300", "previsao")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
