"""Avaliação de desenvolvimento, sem rede ou chamadas a modelo de linguagem.

Usa vetores previamente preparados e rótulos apenas dos demais exemplos de
desenvolvimento. Não classifica calibração, teste ou as 559 questões sem rótulo.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import shutil
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import experimento_campos as base
import semantico_textos as textos

VERSAO = "semantico_supervisionado_v1"
CONFIGURACOES = [
    {"nome": "lexical_controle", "lexico": 1.0, "semantico": 0.0, "vizinhos": 0.0, "k": 0, "pai": True},
    {"nome": "semantico", "lexico": 0.0, "semantico": 1.0, "vizinhos": 0.0, "k": 0, "pai": False},
    {"nome": "semantico_pai", "lexico": 0.0, "semantico": 1.0, "vizinhos": 0.0, "k": 0, "pai": True},
    {"nome": "hibrido_50", "lexico": 0.5, "semantico": 0.5, "vizinhos": 0.0, "k": 0, "pai": False},
    {"nome": "hibrido_50_pai", "lexico": 0.5, "semantico": 0.5, "vizinhos": 0.0, "k": 0, "pai": True},
    {"nome": "hibrido_75", "lexico": 0.25, "semantico": 0.75, "vizinhos": 0.0, "k": 0, "pai": False},
    {"nome": "hibrido_75_pai", "lexico": 0.25, "semantico": 0.75, "vizinhos": 0.0, "k": 0, "pai": True},
    {"nome": "vizinhos_k5", "lexico": 0.0, "semantico": 0.0, "vizinhos": 1.0, "k": 5, "pai": False},
    {"nome": "hibrido_vizinhos_k3", "lexico": 0.25, "semantico": 0.5, "vizinhos": 0.25, "k": 3, "pai": True},
    {"nome": "hibrido_vizinhos_k5", "lexico": 0.25, "semantico": 0.5, "vizinhos": 0.25, "k": 5, "pai": True},
]
for _k in (1, 3, 5):
    CONFIGURACOES.append({"nome": f"lexico_vizinhos_k{_k}", "lexico": 0.75,
                         "semantico": 0.0, "vizinhos": 0.25, "k": _k,
                         "pai": True, "origem_vizinhos": "lexico", "normalizacao": "nenhuma"})


def produto(a, b):
    if len(a) != len(b):
        raise ValueError("Dimensões de vetores diferentes.")
    return sum(x * y for x, y in zip(a, b))


def escala_relativa(escores):
    if not escores:
        return {}
    minimo, maximo = min(escores.values()), max(escores.values())
    amplitude = maximo - minimo
    return {tid: (valor - minimo) / amplitude if amplitude > 0 else 0.0
            for tid, valor in escores.items()}


def produto_esparso(a, b):
    return sum(valor * b.get(chave, 0.0) for chave, valor in a.items())


def vizinhos_lexicos(qid, treino, vetores_palavras, vetores_caracteres):
    return sorted(((outro, 0.75 * produto_esparso(vetores_palavras[qid], vetores_palavras[outro])
                    + 0.25 * produto_esparso(vetores_caracteres[qid], vetores_caracteres[outro]))
                   for outro in treino), key=lambda item: (-item[1], item[0]))


def ids_treino_para(qid, ids_desenvolvimento, hashes):
    return sorted(outro for outro in ids_desenvolvimento
                  if hashes[outro] != hashes[qid])


def carregar_cache(pasta, dados, questoes, temas):
    manifesto_path = pasta / "manifesto_embeddings.json"
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    if manifesto["versao_textos"] != textos.VERSAO_TEXTOS or manifesto["dimensao"] != 384:
        raise ValueError("Versão textual ou dimensão do cache incompatível.")
    for nome in ("questoes.jsonl", "temas.csv"):
        if manifesto["sha256_entradas"][nome] != base.sha256(dados / nome):
            raise ValueError(f"Cache não corresponde aos anexos: {nome}.")
    caminho = pasta / "vetores.json.gz"
    if base.sha256(caminho) != manifesto["sha256_vetores"]:
        raise ValueError("Vetores alterados em relação ao manifesto de preparação.")
    with gzip.open(caminho, "rt", encoding="utf-8") as arquivo:
        vetores = json.load(arquivo)
    candidatos = textos.temas_candidatos(temas)
    esperados = {"questoes": questoes, "temas": candidatos}
    funcoes = {"questoes": textos.texto_questao, "temas": textos.texto_tema}
    for tipo, objetos in esperados.items():
        if set(vetores[tipo]) != set(objetos):
            raise ValueError(f"Cache incompleto, repetido ou extra: {tipo}.")
        for identificador, objeto in objetos.items():
            vetor = vetores[tipo][identificador]
            normalizado = textos.normalizar_vetor(vetor)
            if len(vetor) != 384 or abs(math.sqrt(sum(x*x for x in vetor)) - 1.0) > 1e-4:
                raise ValueError("Dimensão ou normalização de vetor inválida.")
            if textos.hash_texto(funcoes[tipo](objeto)) != manifesto["sha256_textos"][tipo][identificador]:
                raise ValueError(f"Texto diferente do usado no embedding: {identificador}.")
            vetores[tipo][identificador] = normalizado
    return vetores, manifesto


class Recuperador:
    def __init__(self, temas, vetores):
        self.temas = temas
        self.candidatos = textos.temas_candidatos(temas)
        self.vetores = vetores
        documentos = {tid: base.campo_tema(t, True) for tid, t in self.candidatos.items()}
        self.palavras = base.Indice(documentos)
        self.caracteres = base.Indice(documentos, True)

    def sinais(self, qid, questao):
        texto = base.texto_completo(questao)
        palavras = self.palavras.pontuar(texto)
        caracteres = self.caracteres.pontuar(texto)
        meta = self.palavras.pontuar(base.normalizar(questao.get("assunto_origem", "")))
        lexical = {tid: 0.8 * (0.75 * palavras.get(tid, 0) + 0.25 * caracteres.get(tid, 0))
                         + 0.2 * meta.get(tid, 0) for tid in self.candidatos}
        semantico = {tid: produto(self.vetores["questoes"][qid], self.vetores["temas"][tid])
                     for tid in self.candidatos}
        return lexical, semantico


class VizinhosSupervisionados:
    def __init__(self, ids_treino, rotulos_treino, temas, vetores_questoes):
        if set(ids_treino) != set(rotulos_treino):
            raise ValueError("O classificador deve receber somente os rótulos de treino.")
        self.vetores = {qid: vetores_questoes[qid] for qid in ids_treino}
        self.associacoes = {}
        for qid in ids_treino:
            r = rotulos_treino[qid]
            destinos = set()
            if r["fora_da_taxonomia"] == "0":
                for tid in base.referencias(r):
                    destinos.add(tid)
                    destinos.update(pai for pai in base.ancestrais(tid, temas)
                                     if temas[pai]["ativo"] and temas[pai]["nivel"] != 0)
            # Um rótulo amplo não inventa qual filho foi cobrado.
            self.associacoes[qid] = destinos

    def similares(self, vetor_consulta):
        return sorted(((qid, max(0.0, produto(vetor_consulta, vetor)))
                       for qid, vetor in self.vetores.items()), key=lambda x: (-x[1], x[0]))

    def pontuar(self, similares, k, potencia=2):
        votos = defaultdict(float)
        for qid, similaridade in similares[:k]:
            for tid in self.associacoes[qid]:
                votos[tid] += similaridade ** potencia / max(k, 1)
        return votos


def ranquear(config, lexical, semantico, votos, temas):
    if config.get("normalizacao") == "nenhuma":
        l, s, v = lexical, semantico, votos
    else:
        l, s, v = escala_relativa(lexical), escala_relativa(semantico), escala_relativa(votos)
    if config["nome"] == "lexical_controle":
        escores = dict(lexical)
    else:
        escores = {tid: config["lexico"] * l.get(tid, 0)
                       + config["semantico"] * s.get(tid, 0)
                       + config["vizinhos"] * v.get(tid, 0) for tid in lexical}
    if config["pai"]:
        pais = {}
        for tid, valor in escores.items():
            destino = temas[tid]["parent_id"] if temas[tid]["nivel"] == 2 else tid
            if temas[destino]["ativo"] and temas[destino]["nivel"] != 0:
                pais[destino] = max(pais.get(destino, float("-inf")), valor)
        escores = pais
    return sorted(((tid, valor) for tid, valor in escores.items() if valor > 0),
                  key=lambda item: (-item[1], item[0]))[:5]


def executar(dados, manifesto_path, ranking_path, pasta_cache, saida):
    inicio = time.perf_counter()
    if saida.exists():
        raise ValueError("Saída já existe; use uma pasta nova.")
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8-sig"))
    arquivos = {nome: dados / nome for nome in ("questoes.jsonl", "temas.csv", "folha_verdade.csv")}
    base.verificar_hashes_anteriores(manifesto, arquivos)
    particao = base.localizar_particao(manifesto)
    linhas_verdade = base.ler_csv(arquivos["folha_verdade.csv"])
    verdade = {r["id"]: r for r in linhas_verdade}
    if len(verdade) != len(linhas_verdade) or len(verdade) != 100:
        raise ValueError("Esperados 100 IDs oficiais únicos.")
    base.validar_particao(particao, verdade, base.ler_csv(ranking_path))
    questoes = {}
    with arquivos["questoes.jsonl"].open(encoding="utf-8-sig") as arquivo:
        for linha in arquivo:
            if linha.strip():
                q = json.loads(linha)
                if q["id"] in questoes:
                    raise ValueError("Questão repetida.")
                questoes[q["id"]] = q
    if set(questoes) != {f"Q{i:04d}" for i in range(1, 660)}:
        raise ValueError("Esperadas 659 questões, Q0001 a Q0659.")
    temas = base.ler_temas(arquivos["temas.csv"])
    vetores, manifesto_cache = carregar_cache(pasta_cache, dados, questoes, temas)
    ids = sorted(particao["desenvolvimento"])
    rotulos_dev = {qid: verdade[qid] for qid in ids}
    hashes = {qid: textos.hash_texto(base.texto_completo(questoes[qid])) for qid in ids}
    recuperador = Recuperador(temas, vetores)
    palavras_dev = {i: recuperador.palavras.vetor(base.atributos(base.texto_completo(questoes[i]))) for i in ids}
    caracteres_dev = {i: recuperador.caracteres.vetor(base.atributos(base.texto_completo(questoes[i]), True)) for i in ids}
    rankings = {c["nome"]: [] for c in CONFIGURACOES}
    folds = []
    for qid in ids:
        treino = ids_treino_para(qid, ids, hashes)
        if not treino:
            raise ValueError("Não há treino após excluir a questão e suas duplicatas.")
        modelo = VizinhosSupervisionados(treino, {i: rotulos_dev[i] for i in treino},
                                        temas, vetores["questoes"])
        similares = modelo.similares(vetores["questoes"][qid])
        similares_lexicos = vizinhos_lexicos(qid, treino, palavras_dev, caracteres_dev)
        lexical, semantico = recuperador.sinais(qid, questoes[qid])
        votos = {k: modelo.pontuar(similares, k) for k in (3, 5)}
        votos_lexicos = {k: modelo.pontuar(similares_lexicos, k, potencia=1) for k in (1, 3, 5)}
        folds.append({"id_avaliado": qid, "ids_treino": treino,
                      "ids_excluidos": sorted(set(ids) - set(treino)),
                      "hash_grupo_textual": hashes[qid],
                      "vizinhos_top5": [{"id": i, "similaridade": round(s, 8)} for i, s in similares[:5]],
                      "vizinhos_lexicos_top5": [{"id": i, "similaridade": round(s, 8)} for i, s in similares_lexicos[:5]]})
        for config in CONFIGURACOES:
            fonte_votos = votos_lexicos if config.get("origem_vizinhos") == "lexico" else votos
            candidatos = ranquear(config, lexical, semantico, fonte_votos.get(config["k"], {}), temas)
            previsto, score = candidatos[0] if candidatos else ("", 0.0)
            rotulo = rotulos_dev[qid]
            rankings[config["nome"]].append({
                "id": qid, "tema_previsto": previsto,
                "caminho_previsto": temas[previsto]["caminho"] if previsto else "",
                "score_ordenacao_nao_calibrado": round(score, 8),
                "acerto_top1": base.aceito(previsto, rotulo, temas),
                "acerto_top5": any(base.aceito(tid, rotulo, temas) for tid, _ in candidatos),
                "fora_referencia": rotulo["fora_da_taxonomia"] == "1",
                "candidatos_top5": ";".join(tid for tid, _ in candidatos),
            })
    resultados = {nome: base.metricas(linhas) for nome, linhas in rankings.items()}
    resumo = {"experimento": VERSAO,
              "avaliacao": "desenvolvimento; exclusão do próprio item e duplicatas de texto normalizado",
              "particao": {k: len(v) for k, v in particao.items()},
              "resultados": resultados, "tempo_segundos": round(time.perf_counter() - inicio, 3),
              "observacoes": [
                  "Nenhum treino ou previsão usa os 20 IDs de calibração ou os 20 de teste.",
                  "Os vetores das 659 questões são preparação sem rótulos; 559 não recebem classificações.",
                  "Encoder só foi usado antes, na preparação versionada; não é chamado nesta execução.",
                  "Pontuação de ordenação não é probabilidade nem precisão das publicadas.",
                  "Vários métodos foram comparados no desenvolvimento; não é teste externo intocado.",
                  "As marcações oficiais de fora são preservadas; não há detector de fora nesta versão.",
                  "Ainda não há publicacao.csv nem política de publicação.",
              ]}
    registro = {"experimento": VERSAO, "configuracoes": CONFIGURACOES, "particao": particao,
                "sha256_entradas": {n: base.sha256(p) for n, p in arquivos.items()},
                "sha256_manifesto_inicial": base.sha256(manifesto_path),
                "sha256_ranking_inicial": base.sha256(ranking_path),
                "sha256_manifesto_embeddings": base.sha256(pasta_cache / "manifesto_embeddings.json"),
                "sha256_vetores": manifesto_cache["sha256_vetores"],
                "sha256_codigo": {Path(p).name: base.sha256(Path(p))
                                  for p in (__file__, textos.__file__, base.__file__)}}
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".semantico-", dir=saida.parent))
    try:
        import csv
        for nome, linhas in rankings.items():
            with (temporaria / f"ranking_{nome}.csv").open("w", encoding="utf-8", newline="") as arquivo:
                w = csv.DictWriter(arquivo, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
        for nome, objeto in (("resumo.json", resumo), ("manifesto.json", registro),
                              ("auditoria_folds.json", folds)):
            (temporaria / nome).write_text(json.dumps(objeto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(manifesto_path, temporaria / "manifesto_inicial.json")
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    p.add_argument("--manifesto", type=Path, default=Path("experimentos/baseline_001/manifesto.json"))
    p.add_argument("--ranking-base", type=Path, default=Path("experimentos/baseline_001/ranking_desenvolvimento.csv"))
    p.add_argument("--cache", type=Path, default=Path("artefatos/embeddings_v1"))
    p.add_argument("--saida", type=Path, default=Path("experimentos/semantico_001"))
    args = p.parse_args()
    try:
        r = executar(args.dados, args.manifesto, args.ranking_base, args.cache, args.saida)
    except (ValueError, OSError, KeyError, TypeError) as erro:
        p.exit(2, f"Erro: {erro}\n")
    print("Desenvolvimento: questão avaliada e duplicatas excluídas do treino.")
    print("Configuração                    Top1/todos  Top1/tema  Top5/tema")
    for nome, m in r["resultados"].items():
        print(f"{nome:31} {m['acertos_top1']:2}/{m['questoes_avaliadas']:<3} "
              f"     {m['acerto_top1_com_tema']:6.2%}     {m['acerto_top5_com_tema']:6.2%}")
    print(f"Resultados: {args.saida / 'resumo.json'}")


if __name__ == "__main__":
    main()
