"""CV aninhada: busca V15 fixa, três modos de escolha e calibração separada."""
import argparse
import csv
import importlib.metadata
import json
import time
from pathlib import Path

from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.experimento import validar_grupos
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from isolamento_v17 import modelo as m
from isolamento_v17.metricas import medir, curva_descritiva


def gravar(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def csv_salvar(path, rows):
    with path.open("w", encoding="utf-8", newline="") as arq:
        w = csv.DictWriter(arq, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader()
        w.writerows(rows)


def sub(d, ids):
    return {i: d[i] for i in sorted(ids)}


def controle(projeto, nome):
    p = projeto/"experimentos/ampliacao_v15_v16_002"/nome
    with p.open(encoding="utf-8", newline="") as arq:
        rr = [r for r in csv.DictReader(arq) if
              (r["variante"], r["corte"], r["politica"]) ==
              ("busca_multivista", "calibrado", "preservar_v15")]
    for r in rr:
        r["confianca"] = float(r["confianca"])
        for k in ["correto", "fora_oficial", "fold"]:
            if k in r:
                r[k] = int(r[k])
    if not rr or len(rr) != len({r["id"] for r in rr}):
        raise ValueError("Controle ausente ou repetido.")
    return rr


def dependencias(projeto):
    # Snapshot conservador de todo o código potencialmente importado e do
    # catálogo preparado. Não inclui questões, rótulos ou respostas por ID.
    arquivos = [p for p in projeto.rglob("*.py") if not any(
        x in p.parts for x in ["__pycache__", "tests", "testes_diagnostico_559"])]
    arquivos += [p for p in (projeto/"artefatos").rglob("*") if p.is_file()]
    arquivos += [projeto/"vocabulario_v8/dicionario.json",
                 projeto/"melhorias_v3/dados/referencias_normativas_v1.json"]
    return {str(p.relative_to(projeto)): sha(p) for p in sorted(set(arquivos))}


def executar(projeto, saida):
    projeto, saida = Path(projeto).resolve(), Path(saida).resolve()
    if saida.exists():
        raise ValueError("Use saída nova.")
    inicio = time.perf_counter()
    saida.mkdir(parents=True)
    deps = dependencias(projeto)
    protegidos = {n: sha(projeto/n) for n in ["publicacao.csv", "previsao.txt"]}
    dados = projeto/"dados/anexos"
    gravar(saida/"protocolo_previo.json", {
        "versao": "isolamento_v17_1", "variantes": m.VARIANTES,
        "top_k": m.TOP_K, "recuperador": "fusao_contextual V15 original, sem alterar pesos",
        "comparadores": m.ATRIBUTOS,
        "treino": "Todas as famílias; mesma regressão logística C=1, balanceamento e peso por texto duplicado.",
        "guardas": "Mesma guarda V15: evidência, piso textual .03 e homônimo lexical empatado com diferença de logit <.25.",
        "aprovacao_direta_por_identificador": False, "preservacao_automatica": False,
        "calibracao": "Cada opção calibra o tema que de fato escolheu, com previsões dos folds internos, excluídos do ajuste desses comparadores.",
        "limiar": "Maior cobertura interna com precisão empírica >=95% e suporte mínimo 10; sem corte manual 70%.",
        "selecao": "Comparador escolhido em cada fold só pelos dados internos. Comparação global é desenvolvimento exposto.",
        "metadados": "Mantido uso histórico de origem na fusão V15 e nos atributos V11. Origem não é veto obrigatório nem rótulo. Não foi alterada ao mesmo tempo que o comparador.",
        "rotulos_alvo": 0, "chamadas_llm": 0,
        "exposicao": "100 rótulos já vistos repetidamente; folds não constituem teste externo cego.",
        "fora": "8 referências fora são negativos e erros se publicadas; nenhuma exclusão automática por pouco sinal.",
        "uniao": "Apenas estatística descritiva com V16; não cria política de publicação nem certificação.",
        "projeto_sha256": deps,
        "dados_sha256": {n: sha(dados/n) for n in ["questoes.jsonl", "temas.csv", "folha_verdade.csv"]},
        "dependencias": {n: importlib.metadata.version(n) for n in ["numpy", "scipy", "scikit-learn", "threadpoolctl"]},
        "promove_entrega": False,
    })
    qs, temas, ys = f.carregar(dados)
    if (len(qs), len(temas), len(ys)) != (659, 377, 100):
        raise ValueError("Anexos diferentes do protocolo.")
    cat, _ = carregar_catalogo(projeto)
    dic = Dicionario(json.loads((projeto/"vocabulario_v8/dicionario.json").read_text()), temas, cat.familias)
    print("Preparando somente as 100 referências para o estudo do comparador.", flush=True)
    pp = m.preparar(cat, dic, sub(qs, ys))
    folds = json.loads((projeto/"experimentos/melhorias_v3_001/auditoria_folds.json").read_text())
    raw = {v: [] for v in m.VARIANTES}
    externas = {v: [] for v in [*m.VARIANTES, "selecionado_internamente"]}
    audit = []
    for fold in folds:
        n, tr, vl = fold["fold"], fold["treino_ids"], fold["avaliacao_ids"]
        validar_grupos(pp, tr, vl, ys)
        print(f"Fold externo {n}/5: mesmos candidatos; ajuste e calibração somente nos outros grupos.", flush=True)
        internas = {v: [] for v in m.VARIANTES}
        for di in fold["folds_internos"]:
            ti, vi = di["treino_ids"], di["validacao_ids"]
            validar_grupos(pp, ti, vi, tr)
            mods = {c: m.ajustar(sub(pp, ti), sub(ys, ti), cat, c) for c in m.ATRIBUTOS}
            for v in m.VARIANTES:
                ss = m.sinais(sub(pp, vi), mods[m.COMPARADOR[v]], cat, v)
                internas[v].extend(a.avaliar(ss, sub(ys, vi), temas))
        mods = {c: m.ajustar(sub(pp, tr), sub(ys, tr), cat, c) for c in m.ATRIBUTOS}
        pacotes = {v: m.pacote(sub(pp, tr), sub(ys, tr), cat, v, internas[v], mods[m.COMPARADOR[v]]) for v in m.VARIANTES}
        escolhido = m.escolher_internamente(pacotes, internas)
        registro = {"fold": n, "treino_ids": tr, "avaliacao_ids": vl,
                    "folds_internos": fold["folds_internos"], "modelos": pacotes,
                    "selecionado": escolhido, "escolha_antes_dos_rotulos_externos": True}
        gravar(saida/f"folds/fold_{n}.json", registro)
        audit.append({k: v for k, v in registro.items() if k != "modelos"})
        for v in m.VARIANTES:
            ss = m.sinais(sub(pp, vl), pacotes[v]["modelo"], cat, v)
            raw[v].extend(a.avaliar(ss, sub(ys, vl), temas))
            rr = a.avaliar(m.aplicar(sub(pp, vl), pacotes[v], cat, v), sub(ys, vl), temas)
            rr = [{**r, "fold": n} for r in rr]
            externas[v].extend(rr)
            if v == escolhido:
                externas["selecionado_internamente"].extend(rr)
    ref100 = controle(projeto, "avaliacao_desenvolvimento_100.csv")
    if set(ys) != {r["id"] for r in ref100}:
        raise ValueError("Controle de desenvolvimento diferente.")
    resumo = {v: {"desenvolvimento_100": medir(rr, ref100)} for v, rr in externas.items()}
    resumo["controle_v16"] = {"desenvolvimento_100": medir(ref100)}
    # A capacidade da recuperação não depende do comparador e é descrita uma vez.
    posicoes = []
    for i, y in ys.items():
        if int(y["fora_da_taxonomia"]):
            continue
        ordem = f.ordenar(pp[i]["ranking"])
        pos = [j+1 for j, k in enumerate(ordem) if f.aceito(cat.familias[int(k)], y, temas)]
        posicoes.append(min(pos) if pos else None)
    diagnostico = {"com_tema": len(posicoes), "fora": len(ys)-len(posicoes),
                  **{f"aceito_top{k}": sum(p is not None and p <= k for p in posicoes) for k in [1, 3, 5, 10]}}
    mods = {c: m.ajustar(pp, ys, cat, c) for c in m.ATRIBUTOS}
    finais = {v: m.pacote(pp, ys, cat, v, raw[v], mods[m.COMPARADOR[v]]) for v in m.VARIANTES}
    selecionado = m.escolher_internamente(finais, raw)
    dev = resumo["selecionado_internamente"]["desenvolvimento_100"]
    base = resumo["controle_v16"]["desenvolvimento_100"]
    melhora = bool(dev["meta_95_na_amostra"] and (dev["publicar"], -dev["erros_publicadas"]) > (base["publicar"], -base["erros_publicadas"]))
    gravar(saida/"escolha_antes_559.json", {
        "variante_final": selecionado,
        "politica_ja_fixada": finais[selecionado]["politica"],
        "procedimento_aninhado_melhora_controle_na_amostra": melhora,
        "fonte": "Somente referências de desenvolvimento; nada escolhido pelo volume das 559.",
        "controle_para_entrega": "V16 preservado; nenhuma promoção automática",
        "promove_entrega": False,
    })
    gravar(saida/"modelos_finais.json", {"versao": "isolamento_v17_1", "top_k": m.TOP_K,
           "selecionado": selecionado, "modelos": finais, "chamadas_llm": 0})
    csv_salvar(saida/"avaliacao_100.csv", [{**r, "avaliacao": v} for v, rr in externas.items() for r in rr])
    csv_salvar(saida/"curvas_descritivas_100.csv", [{**r, "variante": v} for v, rr in externas.items() for r in curva_descritiva(rr)])
    gravar(saida/"auditoria_folds.json", audit)
    gravar(saida/"diagnostico_recuperacao.json", diagnostico)
    # Artefatos de inferência definidos antes de consultar qualquer resultado no alvo.
    gravar(saida/"manifesto_inferencia.json", {
        "versao": "isolamento_v17_1", "projeto_sha256": deps,
        "artefatos_sha256": {n: sha(saida/n) for n in ["modelos_finais.json", "escolha_antes_559.json"]},
        "promove_entrega": False,
    })
    gravar(saida/"resumo_desenvolvimento_antes_559.json", resumo)
    print("Comparadores e políticas congelados. Classificando as 559 sem usar seus rótulos.", flush=True)
    alvo = {i: q for i, q in qs.items() if i not in ys}
    gravar_jsonl = "".join(json.dumps(q, ensure_ascii=False)+"\n" for i, q in sorted(alvo.items()))
    (saida/"questoes_559_sem_rotulos.jsonl").write_text(gravar_jsonl, encoding="utf-8")
    ps = m.preparar(cat, dic, alvo)
    ref559 = controle(projeto, "classificacoes_559_todas_variantes.csv")
    if len(ref559) != 559 or set(alvo) != {r["id"] for r in ref559}:
        raise ValueError("Controle alvo incompatível.")
    resultados = {}
    todas = []
    for v in m.VARIANTES:
        rows = m.aplicar(ps, finais[v], cat, v)
        resultados[v] = rows
        todas.extend(rows)
        resumo[v]["alvo_559"] = medir(rows, ref559)
        resumo[v]["recentes_300"] = medir([r for r in rows if int(r["id"][1:]) >= 360])
        resumo[v]["antigas_259"] = medir([r for r in rows if int(r["id"][1:]) < 360])
    # O alvo recebe a opção final escolhida antes desta preparação, sem nova seleção.
    resumo["selecionado_internamente"]["alvo_559"] = medir(resultados[selecionado], ref559)
    resumo["selecionado_internamente"]["recentes_300"] = medir([r for r in resultados[selecionado] if int(r["id"][1:]) >= 360])
    resumo["controle_v16"]["alvo_559"] = medir(ref559)
    resumo["controle_v16"]["recentes_300"] = medir([r for r in ref559 if int(r["id"][1:]) >= 360])
    csv_salvar(saida/"classificacoes_559_todas_variantes.csv", todas)
    gravar(saida/"resumo.json", resumo)
    gravar(saida/"execucao.json", {"segundos": time.perf_counter()-inicio,
           "variante_final": selecionado, "controle_promovido": False,
           "precisao_real_559": None, "diagnostico": diagnostico})
    for n, h in deps.items():
        if sha(projeto/n) != h:
            raise ValueError("Código alterado durante avaliação: "+n)
    for n, h in protegidos.items():
        if sha(projeto/n) != h:
            raise ValueError("Entrega anterior alterada: "+n)
    for v, r in resumo.items():
        print(v, json.dumps(r, ensure_ascii=False), flush=True)
    return resumo


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path("."))
    p.add_argument("--saida", type=Path, required=True)
    z = p.parse_args()
    executar(z.projeto, z.saida)
