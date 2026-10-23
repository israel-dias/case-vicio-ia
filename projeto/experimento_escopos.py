"""Compara escopos do catálogo no desenvolvimento e registra um método fixo.

Biblioteca padrão. Sem rede, encoder ou chamada a modelo de linguagem.
"""
import argparse
import csv
import json
import math
import shutil
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import experimento_campos as base
import gerar_escopos as autoria

VERSAO = "comparacao_escopos_v1"
METODO_ESCOLHIDO = "escopos_separados_media3"
CONFIGURACOES = [
    {"nome": "controle_lexical", "modo": "original", "meta": .2, "caracteres": .25, "familia": "max"},
    {"nome": "escopos_juntos", "modo": "juntos", "meta": .2, "caracteres": .25, "familia": "max"},
    {"nome": "escopos_juntos_sem_meta", "modo": "juntos", "meta": 0., "caracteres": .25, "familia": "max"},
    {"nome": "escopos_juntos_sem_char", "modo": "juntos", "meta": .2, "caracteres": 0., "familia": "max"},
    {"nome": "escopos_juntos_subtema", "modo": "juntos", "meta": .2, "caracteres": .25, "familia": "nenhuma"},
    {"nome": "escopos_com_filhos", "modo": "filhos", "meta": .2, "caracteres": .25, "familia": "max"},
    {"nome": "escopos_separados_10", "modo": "separados", "peso_escopo": .1, "meta": .2, "caracteres": .25, "familia": "max"},
    {"nome": "escopos_separados_25", "modo": "separados", "peso_escopo": .25, "meta": .2, "caracteres": .25, "familia": "max"},
    {"nome": "escopos_separados_50", "modo": "separados", "peso_escopo": .5, "meta": .2, "caracteres": .25, "familia": "max"},
    {"nome": "escopos_separados_media2", "modo": "separados", "peso_escopo": .5, "meta": .2, "caracteres": .25, "familia": "media2"},
    {"nome": "escopos_separados_media3", "modo": "separados", "peso_escopo": .5, "meta": .2, "caracteres": .25, "familia": "media3"},
]


def carregar_propostas(temas, temas_path, arquivo, vocabulario_path):
    objeto = json.loads(arquivo.read_text(encoding="utf-8"))
    if objeto["versao"] != autoria.VERSAO:
        raise ValueError("Versão de escopos desconhecida.")
    if objeto["sha256_temas"] != base.sha256(temas_path):
        raise ValueError("O catálogo mudou desde a preparação dos escopos.")
    if objeto["sha256_vocabulario_autorado"] != base.sha256(vocabulario_path):
        raise ValueError("O vocabulário autorado mudou; registre nova preparação.")
    esperado = autoria.construir(temas, autoria.ler_vocabulario(vocabulario_path))
    if objeto["temas"] != esperado:
        raise ValueError("Escopos não correspondem ao vocabulário e ao catálogo registrados.")
    return objeto


def documentos_catalogo(temas, propostas, modo):
    candidatos = {tid: t for tid, t in temas.items() if t["ativo"] and t["nivel"] != 0
                  and all(temas[p]["ativo"] for p in base.ancestrais(tid, temas))}
    documentos = {}
    for tid, t in candidatos.items():
        texto = base.campo_tema(t, True)
        if modo in {"juntos", "filhos"}:
            texto += " " + base.normalizar(propostas[tid]["descricao_proposta"])
        documentos[tid] = texto
    if modo == "filhos":
        for tid, t in candidatos.items():
            if t["nivel"] == 1:
                documentos[tid] += " " + " ".join(
                    base.normalizar(propostas[z]["descricao_proposta"])
                    for z, filho in candidatos.items() if filho["parent_id"] == tid)
    return documentos


def agregar_familias(escores, temas, modo):
    if modo == "nenhuma":
        return dict(escores)
    familias = defaultdict(list)
    for tid, valor in escores.items():
        destino = temas[tid]["parent_id"] if temas[tid]["nivel"] == 2 else tid
        if not destino or not temas[destino]["ativo"] or temas[destino]["nivel"] == 0:
            continue
        familias[destino].append(valor)
    finais = {}
    for tid, valores in familias.items():
        valores = sorted(valores, reverse=True)
        if modo == "max":
            finais[tid] = valores[0]
        elif modo in {"media2", "media3"}:
            n = int(modo[-1])
            finais[tid] = sum(valores[:n]) / min(n, len(valores))
        else:
            raise ValueError("Agregação hierárquica desconhecida.")
    return finais


class ClassificadorEscopos:
    def __init__(self, temas, propostas, configuracao):
        self.temas, self.configuracao = temas, dict(configuracao)
        documentos = documentos_catalogo(temas, propostas, configuracao["modo"])
        self.ids_temas = sorted(documentos)
        self.palavras = base.Indice(documentos)
        self.caracteres = base.Indice(documentos, True) if configuracao["caracteres"] else None
        self.escopos = base.Indice({tid: base.normalizar(propostas[tid]["descricao_proposta"])
                                   for tid in documentos}) if configuracao["modo"] == "separados" else None

    def pontuar(self, questao):
        texto = base.texto_completo(questao)
        w = self.palavras.pontuar(texto)
        c = self.caracteres.pontuar(texto) if self.caracteres else {}
        meta = self.palavras.pontuar(base.normalizar(questao.get("assunto_origem", "")))
        cfg = self.configuracao
        escores = {tid: (1 - cfg["meta"]) * ((1 - cfg["caracteres"]) * w.get(tid, 0)
                    + cfg["caracteres"] * c.get(tid, 0)) + cfg["meta"] * meta.get(tid, 0)
                   for tid in self.ids_temas}
        if self.escopos:
            sinais_escopo = self.escopos.pontuar(texto)
            peso = cfg["peso_escopo"]
            escores = {tid: (1 - peso) * valor + peso * sinais_escopo.get(tid, 0)
                       for tid, valor in escores.items()}
        return agregar_familias(escores, self.temas, cfg["familia"])

    def ranquear(self, questao):
        return sorted(((tid, valor) for tid, valor in self.pontuar(questao).items() if valor > 0),
                      key=lambda item: (-item[1], item[0]))[:5]


def executar(dados, manifesto_path, ranking_path, escopos_path, vocabulario_path, saida):
    inicio = time.perf_counter()
    if saida.exists():
        raise ValueError("Saída já existe; use outra pasta para preservar a versão.")
    arquivos = {n: dados / n for n in ("questoes.jsonl", "temas.csv", "folha_verdade.csv")}
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8-sig"))
    base.verificar_hashes_anteriores(manifesto, arquivos)
    particao = base.localizar_particao(manifesto)
    lista_rotulos = base.ler_csv(arquivos["folha_verdade.csv"])
    rotulos = {r["id"]: r for r in lista_rotulos}
    if len(rotulos) != 100 or len(lista_rotulos) != 100:
        raise ValueError("Esperados 100 rótulos únicos.")
    ranking_base = base.ler_csv(ranking_path)
    base.validar_particao(particao, rotulos, ranking_base)
    questoes = {}
    with arquivos["questoes.jsonl"].open(encoding="utf-8-sig") as arquivo:
        for linha in arquivo:
            if linha.strip():
                q = json.loads(linha)
                if q["id"] in questoes:
                    raise ValueError("Questão repetida.")
                questoes[q["id"]] = q
    if set(questoes) != {f"Q{i:04d}" for i in range(1, 660)}:
        raise ValueError("Esperadas Q0001 a Q0659.")
    temas = base.ler_temas(arquivos["temas.csv"])
    propostas = carregar_propostas(temas, arquivos["temas.csv"], escopos_path, vocabulario_path)
    ids = sorted(particao["desenvolvimento"])
    resultados, rankings = {}, {}
    for cfg in CONFIGURACOES:
        modelo = ClassificadorEscopos(temas, propostas["temas"], cfg)
        linhas = base.avaliar(modelo, ids, questoes, rotulos, temas)
        rankings[cfg["nome"]] = linhas
        resultados[cfg["nome"]] = base.metricas(linhas)
    controle = rankings["controle_lexical"]
    escolhido = rankings[METODO_ESCOLHIDO]
    mudancas = []
    for antes, depois in zip(controle, escolhido):
        if antes["tema_previsto"] != depois["tema_previsto"]:
            qid = antes["id"]
            mudancas.append({"id": qid, "antes": antes["caminho_previsto"],
                             "depois": depois["caminho_previsto"],
                             "antes_aceito": antes["acerto_top1"], "depois_aceito": depois["acerto_top1"],
                             "central_oficial": rotulos[qid]["tema_central_caminho"],
                             "extras_oficiais": rotulos[qid]["extras_ids"]})
    resumo = {"experimento": VERSAO, "avaliacao": "desenvolvimento; múltiplas configurações",
              "particao": {k: len(v) for k, v in particao.items()}, "escopos": propostas["contagens"],
              "resultados": resultados, "metodo_registrado": METODO_ESCOLHIDO,
              "transicoes_controle": {
                  "passou_a_acertar": sum(not r["antes_aceito"] and r["depois_aceito"] for r in mudancas),
                  "passou_a_errar": sum(r["antes_aceito"] and not r["depois_aceito"] for r in mudancas)},
              "tempo_segundos": round(time.perf_counter() - inicio, 3),
              "observacoes": [
                  "Somente os 60 IDs de desenvolvimento recebem previsões.",
                  "Rótulos da calibração e teste não são usados para escolher configurações.",
                  "Os 100 rótulos já foram vistos na conversa; não é teste externo cego.",
                  "Descrições são propostas do assistente; não houve validação jurídica independente.",
                  "Não altera IDs, árvore, status, anexos nem marcações oficiais de fora.",
                  "Agregação média escolhe pais de nível 1; há perda de especificidade.",
                  "Resultados de desenvolvimento não medem precisão das futuras publicadas.",
                  "Ainda faltam política de decisão, calibração, teste e entrega das 659 linhas.",
              ]}
    hashes = {n: base.sha256(p) for n, p in arquivos.items()}
    codigo = {Path(p).name: base.sha256(Path(p)) for p in (__file__, autoria.__file__, base.__file__)}
    registro = {"experimento": VERSAO, "particao": particao, "configuracoes": CONFIGURACOES,
                "sha256_entradas": hashes, "sha256_manifesto_inicial": base.sha256(manifesto_path),
                "sha256_ranking_inicial": base.sha256(ranking_path),
                "sha256_escopos": base.sha256(escopos_path),
                "sha256_vocabulario": base.sha256(vocabulario_path), "sha256_codigo": codigo}
    congelado = {
        "versao": "metodo_catalogo_v1", "metodo": METODO_ESCOLHIDO,
        "configuracao": next(dict(c) for c in CONFIGURACOES if c["nome"] == METODO_ESCOLHIDO),
        "momento": "Registrado antes de gerar previsões para calibração e teste.",
        "motivo": "Seleção pelo desenvolvimento; agregação hierárquica e escopos em índice separado. Há otimismo de seleção.",
        "metricas_desenvolvimento": resultados[METODO_ESCOLHIDO],
        "particao": particao, "sha256_entradas": hashes,
        "sha256_escopos": base.sha256(escopos_path), "sha256_vocabulario": base.sha256(vocabulario_path),
        "sha256_codigo": codigo,
        "estado_politica_publicacao": "pendente; nenhum limiar ou precisão de publicação foi aprovado",
        "instrucoes": "A calibração deverá usar esta configuração fixa. Não alterar o método em resposta ao teste reservado sem registrar que ele passou a desenvolvimento.",
    }
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".escopos-", dir=saida.parent))
    try:
        for nome, linhas in rankings.items():
            with (temporaria / f"ranking_{nome}.csv").open("w", encoding="utf-8", newline="") as arquivo:
                w = csv.DictWriter(arquivo, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
        for nome, objeto in (("resumo.json", resumo), ("manifesto.json", registro),
                              ("mudancas_desenvolvimento.json", mudancas),
                              ("metodo_congelado.json", congelado)):
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
    p.add_argument("--escopos", type=Path, default=Path("artefatos/escopos_v1/escopos.json"))
    p.add_argument("--vocabulario", type=Path, default=Path("artefatos/escopos_v1/vocabulario_autorado.tsv"))
    p.add_argument("--saida", type=Path, default=Path("experimentos/escopos_001"))
    args = p.parse_args()
    try:
        r = executar(args.dados, args.manifesto, args.ranking_base, args.escopos, args.vocabulario, args.saida)
    except (ValueError, OSError, KeyError, TypeError) as erro:
        p.exit(2, f"Erro: {erro}\n")
    print("Desenvolvimento somente; calibração e teste continuam sem previsões.")
    print("Configuração                         Top1/todos  Top1/tema  Top5/tema")
    for nome, m in r["resultados"].items():
        print(f"{nome:36} {m['acertos_top1']:2}/{m['questoes_avaliadas']:<3} "
              f"     {m['acerto_top1_com_tema']:6.2%}     {m['acerto_top5_com_tema']:6.2%}")
    print(f"Método registrado: {r['metodo_registrado']}")
    print(f"Registro para calibração: {args.saida / 'metodo_congelado.json'}")


if __name__ == "__main__":
    main()
