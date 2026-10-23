"""Baseline local da etapa complementar. Não gera a entrega final."""

import argparse
import csv
import hashlib
import html
import json
import math
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Usados somente para organizar a avaliação, nunca para escolher temas.
DISCUTIDOS = {
    "Q0003", "Q0040", "Q0115",
    "Q0138", "Q0144", "Q0324",
}


def normalizar(value):
    text = html.unescape(str(value or "")).replace("\\n", " ")
    text = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ", text, flags=re.I | re.S,
    )
    text = re.sub(r"<[^>]*>", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text if not unicodedata.combining(c)
    )
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def texto_questao(q):
    base = normalizar(q.get("enunciado_html", ""))
    comando = normalizar(q.get("comando", ""))
    alternativas = q.get("alternativas", {}) or {}

    if isinstance(alternativas, dict):
        values = [
            alternativas[k] for k in sorted(alternativas)
        ]
    else:
        values = alternativas

    partes = [base]
    if comando and comando not in base:
        partes.append(comando)
    partes.extend(normalizar(v) for v in values)
    return " ".join(partes)


def atributos(text):
    words = normalizar(text).split()
    bigramas = [
        a + "::" + b for a, b in zip(words, words[1:])
    ]
    return Counter(words + bigramas)


def ler_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def coluna(rows, opcoes):
    campos = list(rows[0]) if rows else []
    indice = {
        normalizar(c).replace(" ", "_"): c
        for c in campos
    }
    for nome in opcoes:
        if nome in indice:
            return indice[nome]
    raise ValueError(
        f"Coluna não encontrada: {opcoes}. "
        f"Cabeçalho recebido: {campos}"
    )


def ler_temas(path):
    rows = ler_csv(path)
    id_col = coluna(rows, ["tema_id", "id"])
    pai_col = coluna(rows, [
        "parent_id", "tema_pai_id", "pai_id",
        "id_pai", "tema_pai", "parent_tema_id",
    ])
    nome_col = coluna(rows, [
        "titulo", "nome", "nome_tema", "tema", "tema_nome",
    ])
    status_col = coluna(rows, ["status", "ativo"])
    nivel_col = coluna(rows, ["nivel"])
    desc_col = next(
        (c for c in rows[0] if normalizar(c) == "descricao"),
        None,
    )

    temas, pais = {}, {}
    ativos = {"ativo", "active", "1", "true", "sim"}
    inativos = {"inativo", "inactive", "0", "false", "nao"}

    for row in rows:
        tid = row[id_col].strip()
        if not tid or tid in temas:
            raise ValueError(
                f"ID de tema vazio ou duplicado: {tid}"
            )

        pai = row[pai_col].strip()
        status = normalizar(row[status_col])
        if status not in ativos | inativos:
            raise ValueError(
                f"Status desconhecido: {row[status_col]!r}"
            )

        temas[tid] = {
            "nome": row[nome_col],
            "descricao": row.get(desc_col, "") if desc_col else "",
            "ativo": status in ativos,
            "nivel": int(row[nivel_col]),
        }
        pais[tid] = (
            None if pai in {"", "0", "null", "None"} else pai
        )

    for tid in temas:
        vistos, atual = set(), tid
        while atual is not None:
            if atual not in temas or atual in vistos:
                raise ValueError(
                    f"Pai ausente ou ciclo no tema {tid}: {atual}"
                )
            vistos.add(atual)
            atual = pais[atual]

    return temas, pais


def ancestrais(tid, pais):
    resultado = set()
    atual = pais.get(tid)
    while atual is not None:
        resultado.add(atual)
        atual = pais[atual]
    return resultado


def referencias(g):
    valores = [
        g["tema_central_id"],
        *g["extras_ids"].split(";"),
    ]
    return [x.strip() for x in valores if x.strip()]


def aceito(previsto, g, pais):
    if not previsto or g["fora_da_taxonomia"] == "1":
        return False

    return any(
        previsto == ref
        or previsto in ancestrais(ref, pais)
        or ref in ancestrais(previsto, pais)
        for ref in referencias(g)
    )


class Baseline:
    """TF-IDF de palavras e bigramas, com similaridade por cosseno."""

    def __init__(self, temas, pais):
        documentos = {}
        self.caminhos = {}

        for tid, tema in temas.items():
            if not tema["ativo"] or tema["nivel"] == 0:
                continue

            cadeia, atual = [], tid
            while atual is not None:
                cadeia.append(temas[atual]["nome"])
                atual = pais[atual]

            caminho = " > ".join(reversed(cadeia))
            self.caminhos[tid] = caminho
            documentos[tid] = atributos(" ".join([
                tema["nome"],
                tema["nome"],
                caminho,
                tema["descricao"],
            ]))

        if not documentos:
            raise ValueError(
                "Nenhum tema ativo e não raiz disponível."
            )

        df = Counter(
            token
            for doc in documentos.values()
            for token in doc
        )
        self.idf = {
            token: math.log(
                (1 + len(documentos)) / (1 + n)
            ) + 1
            for token, n in df.items()
        }

        self.indice = defaultdict(list)
        for tid, counts in documentos.items():
            for token, peso in self.vetor(counts).items():
                self.indice[token].append((tid, peso))

    def vetor(self, counts):
        valores = {
            token: (1 + math.log(n)) * self.idf[token]
            for token, n in counts.items()
            if token in self.idf
        }
        norma = math.sqrt(
            sum(v * v for v in valores.values())
        )
        return (
            {t: v / norma for t, v in valores.items()}
            if norma else {}
        )

    def prever(self, text):
        scores = defaultdict(float)

        for token, peso in self.vetor(atributos(text)).items():
            for tid, peso_tema in self.indice.get(token, []):
                scores[tid] += peso * peso_tema

        return sorted(
            scores.items(),
            key=lambda item: (-item[1], item[0]),
        )[:5]


def particionar(gabarito, textos):
    # Questões com texto idêntico ficam no mesmo grupo.
    grupos = defaultdict(list)
    for qid in gabarito:
        assinatura = hashlib.sha256(
            textos[qid].encode()
        ).hexdigest()
        grupos[assinatura].append(qid)

    buckets = defaultdict(list)
    particao = {}

    for assinatura, ids in grupos.items():
        if DISCUTIDOS.intersection(ids):
            for qid in ids:
                particao[qid] = "desenvolvimento"
        else:
            disciplinas = sorted({
                gabarito[q]["tema_central_caminho"].split(" > ")[0]
                or "FORA"
                for q in ids
            })
            buckets["|".join(disciplinas)].append(
                (assinatura, ids)
            )

    totais = Counter(
        g["tema_central_caminho"].split(" > ")[0] or "FORA"
        for g in gabarito.values()
    )

    for disciplina, lista in sorted(buckets.items()):
        lista.sort(
            key=lambda item: hashlib.sha256(
                ("vde-etapa2-v1:" + item[0]).encode()
            ).hexdigest()
        )
        tamanho = totais.get(
            disciplina, sum(len(ids) for _, ids in lista)
        )
        alvo = round(tamanho * 0.20)

        for destino in (
            "teste_reservado",
            "calibracao_reservada",
        ):
            usados = 0
            while lista and usados < alvo:
                _, ids = lista.pop(0)
                for qid in ids:
                    particao[qid] = destino
                usados += len(ids)

        for _, ids in lista:
            for qid in ids:
                particao[qid] = "desenvolvimento"

    if set(particao) != set(gabarito):
        raise ValueError("Partição incompleta.")

    return particao


def autoteste():
    pais = {
        "1": None,
        "10": "1",
        "11": "10",
        "12": "10",
        "20": "1",
    }
    g = {
        "tema_central_id": "11",
        "extras_ids": "",
        "fora_da_taxonomia": "0",
    }

    assert aceito("11", g, pais)
    assert aceito("10", g, pais)
    assert not aceito("12", g, pais), (
        "Irmãos não são equivalentes."
    )
    assert aceito("20", dict(g, extras_ids="20"), pais)
    assert not aceito(
        "11", dict(g, fora_da_taxonomia="1"), pais
    )
    assert "nao" in normalizar("<p>Não constitui crime.</p>")
    assert "alert" not in normalizar(
        "<script>alert(1)</script>texto"
    )

    print(
        "Autoteste OK: hierarquia, extras, fora, "
        "negação e remoção de script."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dados", type=Path, default=Path("dados/anexos")
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("experimentos/baseline_001"),
    )
    parser.add_argument("--autoteste", action="store_true")
    args = parser.parse_args()

    if args.autoteste:
        autoteste()
        return

    if args.saida.exists():
        raise FileExistsError(
            "Use uma pasta de saída nova."
        )

    inicio = time.perf_counter()
    arquivos = {
        nome: args.dados / nome
        for nome in (
            "questoes.jsonl",
            "temas.csv",
            "folha_verdade.csv",
        )
    }

    questoes = {}
    conteudo = arquivos["questoes.jsonl"].read_text(
        encoding="utf-8-sig"
    )
    for linha in conteudo.splitlines():
        if not linha.strip():
            continue
        q = json.loads(linha)
        if q["id"] in questoes:
            raise ValueError(f"Questão repetida: {q['id']}")
        questoes[q["id"]] = q

    esperados = {f"Q{i:04d}" for i in range(1, 660)}
    if set(questoes) != esperados:
        raise ValueError(
            "Os IDs devem cobrir Q0001 a Q0659 exatamente."
        )

    gold_rows = ler_csv(arquivos["folha_verdade.csv"])
    gold = {g["id"]: g for g in gold_rows}

    if len(gold_rows) != 100 or len(gold) != 100:
        raise ValueError(
            "Esperados 100 rótulos com IDs únicos."
        )
    if not set(gold).issubset(questoes):
        raise ValueError(
            "Folha-verdade referencia questões ausentes."
        )

    temas, pais = ler_temas(arquivos["temas.csv"])

    for g in gold.values():
        if g["fora_da_taxonomia"] not in {"0", "1"}:
            raise ValueError(
                "Valor inválido em fora_da_taxonomia."
            )

        refs = referencias(g)
        if g["fora_da_taxonomia"] == "1" and refs:
            raise ValueError(
                "Questão fora com tema preenchido."
            )
        if (
            g["fora_da_taxonomia"] == "0"
            and not g["tema_central_id"].strip()
        ):
            raise ValueError(
                "Questão dentro da taxonomia sem central."
            )

        for ref in refs:
            if ref not in temas or not temas[ref]["ativo"]:
                raise ValueError(
                    f"Referência inexistente ou inativa: {ref}"
                )

    textos = {
        qid: texto_questao(q)
        for qid, q in questoes.items()
    }
    if any(not textos[qid] for qid in gold):
        raise ValueError(
            "Questão rotulada sem texto utilizável."
        )

    particao = particionar(gold, textos)
    modelo = Baseline(temas, pais)
    linhas = []

    for qid in sorted(gold):
        if particao[qid] != "desenvolvimento":
            continue

        ranking = modelo.prever(textos[qid])
        previsto, score = ranking[0] if ranking else ("", 0.0)
        g = gold[qid]

        linhas.append({
            "id": qid,
            "tema_previsto": previsto,
            "caminho_previsto": modelo.caminhos.get(previsto, ""),
            "score_similaridade": round(score, 6),
            "acerto_top1": int(aceito(previsto, g, pais)),
            "acerto_top5": int(any(
                aceito(tid, g, pais)
                for tid, _ in ranking
            )),
            "fora_referencia": int(g["fora_da_taxonomia"]),
            "candidatos_top5": ";".join(
                tid for tid, _ in ranking
            ),
        })

    if not linhas:
        raise ValueError(
            "Nenhum exemplo em desenvolvimento."
        )

    dentro = [
        row for row in linhas
        if not row["fora_referencia"]
    ]

    resumo = {
        "experimento": "baseline_lexical_v1",
        "tipo_avaliacao": "desenvolvimento; não é teste cego",
        "questoes_recebidas": len(questoes),
        "rotulos": len(gold),
        "particao": dict(Counter(particao.values())),
        "questoes_avaliadas": len(linhas),
        "acerto_top1_total": (
            sum(r["acerto_top1"] for r in linhas) / len(linhas)
        ),
        "acerto_top1_com_tema": (
            sum(r["acerto_top1"] for r in dentro) / len(dentro)
            if dentro else None
        ),
        "acerto_top5_com_tema": (
            sum(r["acerto_top5"] for r in dentro) / len(dentro)
            if dentro else None
        ),
        "tempo_preparacao_e_avaliacao_segundos": round(
            time.perf_counter() - inicio, 3
        ),
        "observacoes": [
            "TF-IDF ajustado somente nos textos do catálogo.",
            "Sem treino supervisionado nesta versão.",
            "ID e metadados de origem não são atributos.",
            "Similaridade não é probabilidade de acerto.",
            "Baseline não detecta fora nem decide publicação.",
            "Calibração e teste permanecem sem previsões.",
            "As outras 559 questões não foram classificadas.",
        ],
    }

    manifesto = {
        "hashes_entrada": {
            nome: hashlib.sha256(path.read_bytes()).hexdigest()
            for nome, path in arquivos.items()
        },
        "hash_codigo": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "particao": dict(sorted(particao.items())),
        "ids_discutidos": sorted(DISCUTIDOS),
        "metodo": (
            "TF-IDF de palavras e bigramas; cosseno; "
            "título repetido, caminho e descrição"
        ),
        "nota": (
            "Os rótulos já foram inspecionados na conversa. "
            "O teste reservado não é avaliação externa."
        ),
    }

    args.saida.mkdir(parents=True, exist_ok=False)

    with (args.saida / "ranking_desenvolvimento.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(linhas[0])
        )
        writer.writeheader()
        writer.writerows(linhas)

    for nome, dados in (
        ("resumo.json", resumo),
        ("manifesto.json", manifesto),
    ):
        (args.saida / nome).write_text(
            json.dumps(dados, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()