"""Busca e compatibilidade aprendida, sem LLM e sem exceções por questão.

Os IDs das questões identificam os registros de avaliação; não são atributos.
Os rótulos oficiais só podem chegar a ajustar() para os textos de treino.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


class TextoVisivel(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes, self.ocultos = [], []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "xml"}:
            self.ocultos.append(tag)
        elif not self.ocultos and tag in {"br", "p", "div", "li", "tr"}:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if self.ocultos:
            if tag == self.ocultos[-1]:
                self.ocultos.pop()
        elif tag in {"p", "div", "li", "tr"}:
            self.partes.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self.ocultos and tag in {"br", "p", "div"}:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self.ocultos:
            self.partes.append(data)


def visivel(value):
    if not isinstance(value, str):
        raise ValueError("Texto precisa ser uma string.")
    parser = TextoVisivel()
    parser.feed(value.replace("\\n", "\n"))
    parser.close()
    return " ".join("".join(parser.partes).split())


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", texto))


def campos(questao):
    enunciado = visivel(questao.get("enunciado_html", ""))
    comando = visivel(questao.get("comando", ""))
    alternativas = questao.get("alternativas", {})
    if not isinstance(alternativas, dict) or not alternativas:
        raise ValueError("Alternativas precisam ser um objeto não vazio.")
    alts = [visivel(alternativas[k]) for k in sorted(alternativas)]
    partes = [enunciado]
    if normalizar(comando) not in normalizar(enunciado):
        partes.append(comando)
    partes.extend(alts)
    completo = normalizar(" ".join(partes))
    if not completo:
        raise ValueError("Questão sem conteúdo textual.")
    return {
        "enunciado": normalizar(enunciado), "comando": normalizar(comando),
        "alternativas": [normalizar(a) for a in alts], "completo": completo,
        "hash": hashlib.sha256(completo.encode()).hexdigest(),
        "certo_errado": int(set(map(normalizar, alts)) == {"certo", "errado"}),
        "assertivas": int(bool(re.search(r"(?:^|[\s:;.])(?:I|II|III|IV|V)\s*[.\-–—]", enunciado))),
    }


def raiz_origem(texto):
    t = normalizar(texto)
    return {
        "direito penal": "penal", "penal": "penal",
        "direito processual penal": "processo penal", "processo penal": "processo penal",
        "direito penal legislacao especial": "direito penal legislacao especial",
        "legislacao penal especial": "direito penal legislacao especial",
        "criminologia": "criminologia",
    }.get(t, "")


def referencias_literais(texto):
    # Só normaliza a citação; não resolve a questão nem mapeia artigo para tema.
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    leis = set()
    for a, b in re.findall(r"\blei\s*(?:n[.oº°\s]*)?(\d[\d.]*)\s*/\s*(\d{2,4})", t):
        ano = int(b)
        if ano < 100:
            ano += 1900 if ano >= 30 else 2000
        leis.add("lei:" + a.replace(".", "") + "/" + str(ano))
    for codigo, extenso in (("cpp", "codigo de processo penal"), ("cp", "codigo penal"),
                            ("lep", "lei de execucao penal"), ("lcp", "lei das contravencoes penais")):
        if re.search(r"\b" + codigo + r"\b", t) or extenso in t:
            leis.add(codigo)
    artigos = set(re.findall(r"\bart(?:igo)?\.?\s*(\d+(?:\s*[-–]\s*[a-z])?)", t))
    return leis, {re.sub(r"\s+", "", a).replace("–", "-") for a in artigos}


def carregar(dados):
    dados = Path(dados)
    with (dados / "temas.csv").open(encoding="utf-8-sig", newline="") as f:
        temas = {}
        for linha in csv.DictReader(f):
            tid = linha["tema_id"]
            if tid in temas:
                raise ValueError("Tema duplicado.")
            linha["nivel"] = int(linha["nivel"])
            linha["ativo"] = linha["status"].lower() in {"active", "ativo", "1"}
            temas[tid] = linha
    for tid in temas:
        pais(tid, temas)
    questoes = {}
    with (dados / "questoes.jsonl").open(encoding="utf-8-sig") as f:
        for linha in f:
            q = json.loads(linha)
            if not isinstance(q.get("id"), str) or not q["id"] or q["id"] in questoes:
                raise ValueError("ID de questão ausente ou repetido.")
            questoes[q["id"]] = q
    with (dados / "folha_verdade.csv").open(encoding="utf-8-sig", newline="") as f:
        verdade = {}
        for y in csv.DictReader(f):
            if y["id"] in verdade or y["id"] not in questoes:
                raise ValueError("ID oficial duplicado ou ausente nas questões.")
            if y["fora_da_taxonomia"] not in {"0", "1"}:
                raise ValueError("fora_da_taxonomia precisa ser 0 ou 1.")
            if (y["fora_da_taxonomia"] == "1") != (not y["tema_central_id"]):
                raise ValueError("Tema central incompatível com fora_da_taxonomia.")
            for tid in referencias(y):
                if not elegivel(tid, temas):
                    raise ValueError("Referência oficial inválida, raiz ou inativa.")
            verdade[y["id"]] = y
    if not questoes or not verdade:
        raise ValueError("Anexos vazios.")
    return questoes, temas, verdade


def pais(tid, temas):
    vistos = set()
    while tid:
        if tid not in temas or tid in vistos:
            raise ValueError("Pai ausente ou ciclo na árvore de temas.")
        vistos.add(tid)
        tid = temas[tid]["parent_id"]
    return vistos


def elegivel(tid, temas):
    return (tid in temas and temas[tid]["nivel"] > 0
            and all(temas[p]["ativo"] for p in pais(tid, temas)))


def referencias(y):
    return [t for t in [y["tema_central_id"], *y.get("extras_ids", "").split(";")] if t]


def aceito(tid, y, temas):
    if not tid or not elegivel(tid, temas) or y["fora_da_taxonomia"] == "1":
        return False
    return any(tid in pais(ref, temas) or ref in pais(tid, temas) for ref in referencias(y))


NOMES_BASE = [
    "media3_completo", "max_completo", "palavra_completo", "char_completo",
    "palavra_enunciado", "char_enunciado", "palavra_comando", "char_comando",
    "palavra_alternativas", "char_alternativas", "palavra_alt_max", "palavra_alt_media",
    "palavra_assunto_origem", "apoio_enunciado_e_alternativas", "origem_compativel",
    "origem_reconhecida", "lei_literal", "artigo_literal", "certo_errado",
    "assertivas_numeradas", "numero_alternativas", "cobertura_vocabulario",
]
NOMES_VIZINHOS = ["voto_vizinhos", "vizinho_compativel", "vizinho_incompativel", "vizinho_fora"]


class Catalogo:
    def __init__(self, temas):
        self.temas = temas
        self.ids = sorted((t for t in temas if elegivel(t, temas)), key=int)
        self.familias = sorted((t for t in self.ids if temas[t]["nivel"] == 1), key=int)
        self.membros = [[i for i, t in enumerate(self.ids) if p in pais(t, temas)] for p in self.familias]
        documentos = []
        for tid in self.ids:
            t = temas[tid]
            desc = t.get("descricao", "")
            # Dados de importação contêm contagens e o mesmo título: não definem escopo.
            if desc.startswith("Subtema de '") or desc.startswith("Disciplina (root)"):
                desc = ""
            caminho_sem_raiz = " ".join(t["caminho"].split(" > ")[1:])
            documentos.append(normalizar(" ".join([t["titulo"]] * 2 + [caminho_sem_raiz, desc])))
        if not documentos:
            raise ValueError("Catálogo sem temas ativos utilizáveis.")
        self.palavras = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, dtype=np.float64)
        self.caracteres = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, dtype=np.float64)
        self.wp = self.palavras.fit_transform(documentos)
        self.cp = self.caracteres.fit_transform(documentos)
        self.refs = []
        for membros in self.membros:
            a, b = set(), set()
            for i in membros:
                t = temas[self.ids[i]]
                l, ar = referencias_literais(t["titulo"] + " " + t.get("descricao", ""))
                a.update(l); b.update(ar)
            self.refs.append((a, b))

    def transformar(self, qs):
        saida = {}
        for qid, q in qs.items():
            c = campos(q)
            textos = [c["completo"], c["enunciado"], c["comando"],
                      " ".join(c["alternativas"]), normalizar(visivel(q.get("assunto_origem", ""))),
                      *c["alternativas"]]
            wv = self.palavras.transform(textos)
            w = (wv @ self.wp.T).toarray()
            ch = (self.caracteres.transform(textos[:4]) @ self.cp.T).toarray()
            # Controle fixo e não supervisionado. Não é a versão anterior com escopos.
            bruto = .75 * w[0] + .25 * ch[0]
            origem = raiz_origem(q.get("disciplina_origem", ""))
            refs = referencias_literais(" ".join([visivel(q.get("enunciado_html", "")),
                                                   visivel(q.get("comando", "")),
                                                   *[visivel(a) for a in q["alternativas"].values()]]))
            tokens = c["completo"].split()
            cobertura = sum(t in self.palavras.vocabulary_ for t in tokens) / max(1, len(tokens))
            features, scores = [], []
            for k, membros in enumerate(self.membros):
                def media3(a):
                    valores = sorted(a[membros], reverse=True)[:3]
                    return float(sum(valores) / min(3, len(membros)))
                wf = [media3(a) for a in w[:5]]
                cf = [media3(a) for a in ch]
                af = [media3(a) for a in w[5:]]
                lei, art = self.refs[k]
                raw = media3(bruto)
                features.append([
                    raw, float(max(bruto[membros])), wf[0], cf[0], wf[1], cf[1], wf[2], cf[2],
                    wf[3], cf[3], max(af), float(np.mean(af)), wf[4], min(wf[1], wf[3]),
                    float(origem != "" and origem == normalizar(self.temas[self.familias[k]]["disciplina"])),
                    float(bool(origem)), len(refs[0] & lei) / max(1, len(refs[0])),
                    len(refs[1] & art) / max(1, len(refs[1])), c["certo_errado"], c["assertivas"],
                    min(10, len(c["alternativas"])) / 10, cobertura,
                ])
                scores.append(raw)
            saida[qid] = {"hash": c["hash"], "features": np.asarray(features),
                          "scores": np.asarray(scores), "vetor": wv[0]}
        return saida


def ajustar_linear(x, y, pesos=None, balancear=False):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=int)
    if x.ndim != 2 or len(x) != len(y) or not len(x) or not np.isfinite(x).all():
        raise ValueError("Atributos de treino inválidos.")
    pesos = np.ones(len(y)) if pesos is None else np.asarray(pesos, dtype=float)
    if len(pesos) != len(y) or not np.isfinite(pesos).all() or (pesos <= 0).any():
        raise ValueError("Pesos de treino inválidos.")
    if len(set(y)) == 1:
        p = (float(np.dot(pesos, y)) + 1) / (float(sum(pesos)) + 2)
        return {"constante": p, "dimensao": x.shape[1]}
    scaler = StandardScaler().fit(x, sample_weight=pesos)
    z = scaler.transform(x)
    if balancear:
        total = float(sum(pesos))
        pesos = pesos * np.array([total / (2 * float(sum(pesos[y == classe]))) for classe in y])
    lr = LogisticRegression(C=1.0, solver="liblinear", max_iter=1500, random_state=2026)
    with threadpool_limits(limits=2):
        lr.fit(z, y, sample_weight=pesos)
    return {"dimensao": x.shape[1], "media": scaler.mean_.tolist(), "escala": scaler.scale_.tolist(),
            "coeficientes": lr.coef_[0].tolist(), "intercepto": float(lr.intercept_[0])}


def predizer_linear(x, modelo):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] != modelo["dimensao"] or not np.isfinite(x).all():
        raise ValueError("Atributos de inferência inválidos.")
    if "constante" in modelo:
        return np.full(len(x), modelo["constante"])
    z = (x - np.asarray(modelo["media"])) / np.asarray(modelo["escala"])
    v = np.clip(z @ np.asarray(modelo["coeficientes"]) + modelo["intercepto"], -50, 50)
    return 1 / (1 + np.exp(-v))


def vizinhanca(perfil, perfis_treino, ys, familias, temas):
    if set(perfis_treino) != set(ys):
        raise ValueError("Rótulos precisam corresponder exatamente aos textos de treino.")
    proximos = []
    for qid, p in perfis_treino.items():
        if p["hash"] == perfil["hash"]:
            continue
        sim = float((p["vetor"] @ perfil["vetor"].T).toarray()[0, 0])
        proximos.append((sim, p["hash"], qid))
    proximos.sort(key=lambda x: (-x[0], x[1]))
    proximos = proximos[:3]
    total = max(1e-12, sum(x[0] for x in proximos))
    resultado = []
    for tid in familias:
        positivos = [s for s, _, qid in proximos if aceito(tid, ys[qid], temas)]
        negativos = [s for s, _, qid in proximos if not aceito(tid, ys[qid], temas)]
        fora = [s for s, _, qid in proximos if ys[qid]["fora_da_taxonomia"] == "1"]
        resultado.append([sum(positivos) / total, max(positivos, default=0),
                          max(negativos, default=0), max(fora, default=0)])
    return np.asarray(resultado)


def matriz(perfil, treino, ys, familias, temas, usar_vizinhos):
    x = perfil["features"]
    if usar_vizinhos:
        x = np.hstack([x, vizinhanca(perfil, treino, ys, familias, temas)])
    return x


def ajustar(treino, ys, familias, temas, usar_vizinhos=False):
    if set(treino) != set(ys) or not treino:
        raise ValueError("Ajuste recebeu rótulos externos ou dados de treino vazios.")
    contagens = Counter(p["hash"] for p in treino.values())
    xx, yy, pesos = [], [], []
    for qid, p in treino.items():
        x = matriz(p, treino, ys, familias, temas, usar_vizinhos)
        xx.extend(x)
        yy.extend(int(aceito(t, ys[qid], temas)) for t in familias)
        # Mesma massa por texto; duplicações não multiplicam sua influência.
        pesos.extend([1 / contagens[p["hash"]]] * len(familias))
    return ajustar_linear(xx, yy, pesos, balancear=True)


def ordenar(scores):
    # Família é a unidade candidata; o empate não vira um extra automaticamente.
    return np.argsort(-np.asarray(scores), kind="stable")


def sinais(perfil, familias, modelos, treino, ys, temas):
    raw = perfil["scores"]
    lex = ordenar(raw)
    a, b = (int(lex[0]), int(lex[1])) if len(lex) > 1 else (int(lex[0]), int(lex[0]))
    margem = (raw[a] - raw[b]) / max(1e-12, raw[a])
    saida = {"lexical_margem": {"indice": a, "sinal": float(margem)}}
    for metodo in ("compatibilidade_fixa", "compatibilidade_ranking", "compatibilidade_vizinhos"):
        viz = metodo == "compatibilidade_vizinhos"
        modelo = modelos["vizinhos" if viz else "base"]
        x = matriz(perfil, treino, ys, familias, temas, viz)
        ps = predizer_linear(x, modelo)
        j = a if metodo == "compatibilidade_fixa" else int(ordenar(ps)[0])
        saida[metodo] = {"indice": j, "sinal": float(ps[j])}
    for metodo, r in saida.items():
        j = r["indice"]
        r.update(tema_central_id=familias[j], elegivel=bool(raw[j] >= .03),
                 score_lexical=float(raw[j]), primeiro_lexical=familias[a],
                 segundo_lexical=familias[b])
        if metodo == "lexical_margem":
            r["elegivel"] = r["elegivel"] and margem > 0
    return saida


def logit(p):
    p = min(1 - 1e-6, max(1e-6, float(p)))
    return math.log(p / (1 - p))


def calibrador(linhas):
    if not linhas:
        raise ValueError("Calibração vazia.")
    x = [[logit(r["sinal"])] for r in linhas]
    y = [r["correto"] for r in linhas]
    mod = ajustar_linear(x, y)
    if "coeficientes" in mod and mod["coeficientes"][0] < 0:
        mod = {"dimensao": 1, "constante": (sum(y) + 1) / (len(y) + 2)}
    return mod


def confiancas(linhas, mod):
    return predizer_linear([[logit(r["sinal"])] for r in linhas], mod).tolist()


def escolher_politica(linhas, probs, minimo=10):
    candidatos = []
    for corte in sorted(set(p for r, p in zip(linhas, probs) if r["elegivel"])):
        selecionadas = [r for r, p in zip(linhas, probs) if r["elegivel"] and p >= corte]
        acertos = sum(r["correto"] for r in selecionadas)
        n = len(selecionadas)
        if n >= minimo and acertos / n >= .95:
            candidatos.append((n, corte, acertos))
    if not candidatos:
        return {"ativa": False, "limiar": None, "suporte_interno": 0, "acertos_internos": 0}
    n, corte, acertos = max(candidatos)
    return {"ativa": True, "limiar": corte, "suporte_interno": n, "acertos_internos": acertos}


def decidir(sinal, prob, politica):
    if not math.isfinite(prob) or not 0 <= prob <= 1:
        raise ValueError("Confiança inválida.")
    publicar = politica["ativa"] and sinal["elegivel"] and prob >= politica["limiar"]
    return "publicar" if publicar else "revisar"
