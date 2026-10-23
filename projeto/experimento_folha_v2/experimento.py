"""Experimento independente sobre as 100 questões oficiais, com CV aninhada.

Não substitui a entrega existente. Não classifica as 559 questões sem rótulos.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import time
from collections import Counter, defaultdict
from pathlib import Path

import modelo as m

METODOS = ("lexical_margem", "compatibilidade_fixa", "compatibilidade_ranking", "compatibilidade_vizinhos")
SEMENTE = "vde-folha-v2-2026-10-21"


def escrever_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dividir(perfis, ys, temas, quantidade, semente):
    if set(perfis) != set(ys):
        raise ValueError("Partição exige exatamente os rótulos do grupo selecionado.")
    grupos = defaultdict(list)
    for qid, p in perfis.items():
        grupos[p["hash"]].append(qid)
    if len(grupos) < quantidade:
        raise ValueError("Poucos textos diferentes para os folds.")
    folds = [[] for _ in range(quantidade)]
    por_estrato = [Counter() for _ in folds]
    ordenados = sorted(grupos, key=lambda h: (-len(grupos[h]), hashlib.sha256((semente+h).encode()).hexdigest()))
    for h in ordenados:
        ids = grupos[h]
        estratos = []
        for qid in ids:
            y = ys[qid]
            estratos.append("FORA" if y["fora_da_taxonomia"] == "1" else temas[y["tema_central_id"]]["disciplina"])
        estrato = "|".join(sorted(set(estratos)))
        k = min(range(quantidade), key=lambda i: (por_estrato[i][estrato], len(folds[i]),
                hashlib.sha256((semente+h+str(i)).encode()).hexdigest()))
        folds[k].extend(ids)
        por_estrato[k][estrato] += len(ids)
    return [sorted(f) for f in folds]


def separar(perfis, ids):
    return {qid: perfis[qid] for qid in sorted(ids)}


def validar_separacao(treino, avaliacao):
    if set(treino) & set(avaliacao):
        raise ValueError("Questão aparece no treino e na avaliação.")
    if {p["hash"] for p in treino.values()} & {p["hash"] for p in avaliacao.values()}:
        raise ValueError("Texto duplicado aparece no treino e na avaliação.")


def modelos(treino, ys, catalogo):
    return {"base": m.ajustar(treino, ys, catalogo.familias, catalogo.temas),
            "vizinhos": m.ajustar(treino, ys, catalogo.familias, catalogo.temas, usar_vizinhos=True)}


def calibrar_internamente(treino, ys, catalogo, semente):
    if set(treino) != set(ys):
        raise ValueError("A calibração interna recebeu rótulos externos.")
    folds = dividir(treino, ys, catalogo.temas, 4, semente)
    linhas = {nome: [] for nome in METODOS}
    audit = []
    for k, ids in enumerate(folds):
        fit = separar(treino, set(treino) - set(ids))
        val = separar(treino, ids)
        validar_separacao(fit, val)
        yfit = {qid: ys[qid] for qid in fit}
        mods = modelos(fit, yfit, catalogo)
        audit.append({"fold": k+1, "treino_ids": sorted(fit), "validacao_ids": ids})
        for qid, p in val.items():
            sinais = m.sinais(p, catalogo.familias, mods, fit, yfit, catalogo.temas)
            for nome, r in sinais.items():
                linhas[nome].append({"id": qid, **r, "correto": int(m.aceito(r["tema_central_id"], ys[qid], catalogo.temas))})
    calibradores, politicas = {}, {}
    for nome in METODOS:
        calibradores[nome] = m.calibrador(linhas[nome])
        probs = m.confiancas(linhas[nome], calibradores[nome])
        politicas[nome] = m.escolher_politica(linhas[nome], probs)
        politicas[nome]["acertos_top1_internos"] = sum(r["correto"] for r in linhas[nome])
    # A escolha da variante usa somente os dados internos, antes de ver o fold externo.
    candidatos = list(METODOS[1:])
    escolhido = max(candidatos, key=lambda n: (politicas[n]["suporte_interno"],
                    politicas[n]["acertos_top1_internos"], -candidatos.index(n)))
    return calibradores, politicas, escolhido, audit


def avaliar(sem_rotulos, ys, temas):
    if {r["id"] for r in sem_rotulos} != set(ys) or len(sem_rotulos) != len(ys):
        raise ValueError("Avaliador recebeu rótulos ou previsões de outro conjunto.")
    saida = []
    for r in sem_rotulos:
        y = ys[r["id"]]
        saida.append({**r, "correto": int(m.aceito(r["tema_central_id"], y, temas)),
                      "fora_oficial": int(y["fora_da_taxonomia"]),
                      "referencias_oficiais": ";".join(m.referencias(y)),
                      "top2_lexicais_aceitos": int(m.aceito(r["primeiro_lexical"], y, temas) and
                                                   m.aceito(r["segundo_lexical"], y, temas))})
    return saida


def resumo(linhas):
    publicadas = [r for r in linhas if r["decisao"] == "publicar"]
    acertos = sum(r["correto"] for r in publicadas)
    n = len(publicadas)
    total = len(linhas)
    return {
        "avaliadas": total, "acertos_top1": sum(r["correto"] for r in linhas),
        "publicar": n, "revisar": total-n, "fora": 0,
        "acertos_publicadas": acertos, "erros_publicadas": n-acertos,
        "precisao_publicadas": acertos/n if n else None, "cobertura": n/total,
        "brier": sum((r["confianca"]-r["correto"])**2 for r in linhas)/total,
        "fora_oficial_publicadas": sum(r["fora_oficial"] for r in publicadas),
        "duas_familias_aceitas": sum(r["top2_lexicais_aceitos"] for r in linhas),
        "duas_familias_aceitas_publicadas": sum(r["top2_lexicais_aceitos"] for r in publicadas),
        "meta_95_na_amostra": acertos/n >= .95 if n else False,
        "prova_de_minimo_95_populacional": False,
    }


def diagnostico(ys, temas):
    fora = [qid for qid, y in ys.items() if y["fora_da_taxonomia"] == "1"]
    centrais = Counter(y["tema_central_id"] for y in ys.values() if y["tema_central_id"])
    multi_familia, multi_disciplina = [], []
    for qid, y in ys.items():
        refs = m.referencias(y)
        familias = set()
        for tid in refs:
            familias.update(p for p in m.pais(tid, temas) if temas[p]["nivel"] == 1)
        if len(familias) > 1:
            multi_familia.append(qid)
        if len({temas[t]["disciplina"] for t in refs}) > 1:
            multi_disciplina.append(qid)
    return {"rotulos": len(ys), "com_extras": sum(bool(y.get("extras_ids")) for y in ys.values()),
            "fora_ids": sorted(fora), "familias_distintas_ids": sorted(multi_familia),
            "disciplinas_distintas_ids": sorted(multi_disciplina),
            "temas_centrais_distintos": len(centrais), "centrais_com_um_exemplo": sum(c == 1 for c in centrais.values()),
            "nota": "Extras oficiais são referências aceitas; não provam equivalência global entre seus ramos."}


def leitura(resultados, tempo):
    textos = ["# Experimento sobre a folha-verdade — versão 2", "",
        "Este é um experimento independente sobre os 100 rótulos já conhecidos. As 559 questões sem rótulos não foram classificadas. Não é um novo teste externo cego.", "",
        "O controle usa o catálogo original, sem os escopos enriquecidos da entrega anterior. Por isso as diferenças desta tabela isolam os métodos deste pacote; não são uma reprodução do classificador anterior.", "",
        "| Método | Top1/100 | Publicar | Acertos nas publicadas | Precisão | Cobertura | Fora oficial publicada |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for nome, r in resultados.items():
        precisao = "indefinida" if r["precisao_publicadas"] is None else f'{r["precisao_publicadas"]:.2%}'
        textos.append(f'| {nome} | {r["acertos_top1"]} | {r["publicar"]} | {r["acertos_publicadas"]} | {precisao} | {r["cobertura"]:.2%} | {r["fora_oficial_publicadas"]} |')
    textos += ["", "## O que está sendo testado", "",
        "1. **Régua correta:** tema central, extras e ancestrais/descendentes de cada referência são aceitos. Irmãos não são equivalentes automaticamente.",
        "2. **Compatibilidade:** cada par questão–família recebe um sinal independente. Duas famílias com sinal alto podem coexistir; a margem entre elas deixa de ser veto automático.",
        "3. **Leitura por campos:** enunciado, comando e todas as alternativas são preservados e comparados separadamente. O sistema não conhece a alternativa certa e não confunde essas comparações com uma resolução jurídica.",
        "4. **Exemplos oficiais:** na variante com vizinhos, apenas os rótulos de treino auxiliam o cálculo. O próprio texto e duplicatas normalizadas são excluídos dos vizinhos.",
        "5. **Origem e citações:** disciplina de origem é uma evidência fraca aprendida, nunca um filtro obrigatório. Leis e artigos são extraídos literalmente; uma citação não determina o tema.",
        "6. **Fora:** itens oficiais fora recebem alvos negativos para todas as famílias. O experimento mede publicações indevidas desses itens, mas não ativa exclusão automática com apenas oito exemplos.", "",
        "## Avaliação e limites", "",
        "Cada um dos cinco folds externos recebe previsões produzidas com os outros quatro. Dentro do treino externo, quatro folds internos geram sinais fora do próprio treino. Somente esses sinais internos ajustam a confiança, escolhem o corte e selecionam a variante. Textos duplicados ficam no mesmo grupo.", "",
        "A regra exige pelo menos dez publicações internas com 95% de acerto empírico. Isso é um critério de seleção, não uma comprovação estatística. As probabilidades são estimativas regularizadas; devem ser examinadas com o Brier e os erros externos. O ajuste do calibrador e do corte usa os mesmos sinais internos, portanto a avaliação dessas escolhas é feita nos folds externos.", "",
        "**A linha `selecionado_internamente` representa a escolha do algoritmo antes de ver cada fold externo.** Escolher depois a linha de melhor resultado produz uma nova decisão de desenvolvimento e exige confirmação em dados novos. Os 100 rótulos já influenciaram discussões anteriores; a validação cruzada não apaga essa exposição.", "",
        "As famílias candidatas são nós ativos de nível 1, cuja escolha é aceita quando está na cadeia de uma referência oficial. Isso não torna os subtemas irmãos equivalentes. O pacote não atribui extras automaticamente, nem usa nomes encontrados nos distratores como rótulos.", "",
        f"Tempo medido nesta execução: {tempo:.3f} s, incluindo preparação, ajustes e avaliação. Não é a latência de classificar uma questão nem uma projeção para 50 mil.", "",
        "Nenhum `publicacao.csv` ou `previsao.txt` anterior é alterado. O repositório principal só deve adotar a variante após examinar os resultados e registrar uma nova versão. O pacote não garante a meta de 95% nas questões que a empresa guardou.", ""]
    return "\n".join(textos)


def executar(dados, saida, fabrica_catalogo=None, origem_preparada=None):
    saida = Path(saida)
    if saida.exists():
        raise ValueError("A saída já existe. Escolha uma pasta nova para preservar o histórico.")
    inicio = time.perf_counter()
    questoes, temas, ys = m.carregar(dados)
    if len(questoes) != 659 or len(temas) != 377 or len(ys) != 100:
        raise ValueError("Este protocolo é para os anexos de 659 questões, 377 temas e 100 rótulos.")
    arquivos = ["questoes.jsonl", "temas.csv", "folha_verdade.csv"]
    protocolo = {
        "versao": "folha_v2_independente", "semente": SEMENTE, "folds_externos": 5,
        "folds_internos": 4, "metodos": list(METODOS), "minimo_publicadas_internas": 10,
        "precisao_empirica_interna_alvo": .95, "llm_na_decisao": False,
        "atributos_base": m.NOMES_BASE, "atributos_vizinhos": m.NOMES_VIZINHOS,
        "dados_sha256": {n: sha(Path(dados)/n) for n in arquivos},
        "codigo_sha256": {n: sha(Path(__file__).parent/n) for n in ("modelo.py", "experimento.py")},
        "dependencias": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "scikit-learn", "threadpoolctl")},
        "python": platform.python_version(),
        "exposicao_previa": "Todos os rótulos já foram discutidos. Resultados são desenvolvimento, não teste externo inteiramente cego.",
        "selecao": "Maior número de publicações internas; desempate pelo top1 interno e menor complexidade.",
        "novas_559": "Não classificar neste experimento.",
        "origem_preparada": origem_preparada,
    }
    saida.mkdir(parents=True)
    # Escrito antes de qualquer previsão. Seu hash vai em cada registro de fold.
    escrever_json(saida/"protocolo_previo.json", protocolo)
    catalogo = m.Catalogo(temas) if fabrica_catalogo is None else fabrica_catalogo(temas)
    # A função de featurização recebe apenas os 100 itens oficiais, não os outros 559.
    perfis = catalogo.transformar({qid: questoes[qid] for qid in sorted(ys)})
    folds = dividir(perfis, ys, temas, 5, SEMENTE)
    previsoes = {nome: [] for nome in (*METODOS, "selecionado_internamente")}
    auditoria = []
    for k, ids in enumerate(folds):
        print(f"Fold externo {k+1}/5: ajuste e seleção somente nos outros folds.", flush=True)
        treino = separar(perfis, set(perfis)-set(ids))
        holdout = separar(perfis, ids)
        validar_separacao(treino, holdout)
        ytreino = {qid: ys[qid] for qid in treino}
        cs, ps, escolhido, internos = calibrar_internamente(treino, ytreino, catalogo, SEMENTE+f":{k}")
        mods = modelos(treino, ytreino, catalogo)
        registro = {"fold": k+1, "treino_ids": sorted(treino), "avaliacao_ids": ids, "folds_internos": internos,
                    "selecionado": escolhido, "calibradores": cs, "politicas": ps,
                    "protocolo_sha256": sha(saida/"protocolo_previo.json")}
        # Coeficientes e regras são persistidos antes de predizer o holdout externo.
        escrever_json(saida/"modelos_folds"/f"fold_{k+1}.json", {"modelos": mods, **registro})
        auditoria.append(registro)
        externas = {nome: [] for nome in METODOS}
        for qid, p in holdout.items():
            sinais = m.sinais(p, catalogo.familias, mods, treino, ytreino, temas)
            for nome in METODOS:
                r = sinais[nome]
                prob = m.confiancas([r], cs[nome])[0]
                externas[nome].append({"id": qid, "fold": k+1, **r, "confianca": prob,
                                       "decisao": m.decidir(r, prob, ps[nome])})
        # Só agora os rótulos do holdout chegam ao avaliador.
        yholdout = {qid: ys[qid] for qid in holdout}
        for nome in METODOS:
            avaliadas = avaliar(externas[nome], yholdout, temas)
            previsoes[nome].extend(avaliadas)
            if nome == escolhido:
                previsoes["selecionado_internamente"].extend({**r, "variante": nome} for r in avaliadas)
    for nome, linhas in previsoes.items():
        linhas.sort(key=lambda r: r["id"])
        campos_csv = sorted(set().union(*(r.keys() for r in linhas)))
        with (saida/f"previsoes_{nome}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos_csv)
            w.writeheader(); w.writerows(linhas)
    resultados = {nome: resumo(linhas) for nome, linhas in previsoes.items()}
    tempo = time.perf_counter()-inicio
    escrever_json(saida/"resumo.json", {"metodos": resultados, "segundos": tempo,
        "selecoes": dict(Counter(r["selecionado"] for r in auditoria)),
        "questoes_classificadas": len(perfis), "questoes_sem_rotulo_classificadas": 0,
        "familias_candidatas": len(catalogo.familias)})
    escrever_json(saida/"diagnostico_folha.json", diagnostico(ys, temas))
    escrever_json(saida/"auditoria_folds.json", auditoria)
    (saida/"LEITURA.md").write_text(leitura(resultados, tempo), encoding="utf-8")
    escrever_json(saida/"manifesto.json", {str(p.relative_to(saida)): sha(p)
                  for p in sorted(saida.rglob("*")) if p.is_file() and p.name != "manifesto.json"})
    return resultados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Path(__file__).parent/"dados"/"anexos")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    try:
        with m.threadpool_limits(limits=2):
            resultados = executar(args.dados, args.saida)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Erro: {exc}\n")
    print("Avaliação de desenvolvimento; somente os 100 rótulos oficiais. Sem LLM.")
    print("Método                              Top1   Publicar  Acertos   Precisão  Cobertura")
    for nome, r in resultados.items():
        p = "indefinida" if r["precisao_publicadas"] is None else f'{r["precisao_publicadas"]:.2%}'
        print(f'{nome:35} {r["acertos_top1"]:4}   {r["publicar"]:7}  {r["acertos_publicadas"]:7}   {p:>9}  {r["cobertura"]:8.2%}')
    print("Leitura:", args.saida/"LEITURA.md")


if __name__ == "__main__":
    main()
