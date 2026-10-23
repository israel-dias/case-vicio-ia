"""Compara recuperação lexical nos IDs de desenvolvimento do baseline existente.

Biblioteca padrão, sem rede, sem LLM e sem decisões finais de publicação.
O manifesto e o ranking do primeiro experimento fixam a divisão dos dados.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import shutil
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


VERSAO = "comparacao_campos_v1.1"
GRUPOS = ("desenvolvimento", "calibracao_reservada", "teste_reservado")
CONFIGURACOES = [
    {"nome": "campos_separados", "catalogo_limpo": False,
     "morfologia": False, "introducao": False},
    {"nome": "catalogo_limpo", "catalogo_limpo": True,
     "morfologia": False, "introducao": False},
    {"nome": "morfologia", "catalogo_limpo": True,
     "morfologia": True, "introducao": False},
    {"nome": "introducao_atenuada", "catalogo_limpo": True,
     "morfologia": True, "introducao": True},
]

# Grade pequena e explícita: todas as combinações são registradas, incluindo pioras.
for _limpo in (False, True):
    for _stop in (False, True):
        for _char, _meta, _pai in (
            (0.0, 0.0, False), (0.0, 0.0, True), (0.25, 0.0, False),
            (0.0, 0.2, False), (0.0, 0.2, True), (0.0, 0.4, False),
            (0.25, 0.2, False), (0.25, 0.2, True),
        ):
            CONFIGURACOES.append({
                "nome": f"texto_l{int(_limpo)}_s{int(_stop)}_c{int(100*_char)}_m{int(100*_meta)}_p{int(_pai)}",
                "catalogo_limpo": _limpo, "morfologia": bool(_char),
                "peso_caracteres": _char, "peso_metadado": _meta,
                "subir_pai": _pai, "stopwords": _stop,
                "introducao": False, "texto_unico": True,
            })

STOPWORDS = frozenset(
    "a o as os um uma uns umas de da do das dos e em no na nos nas por para com "
    "que se ao aos pelo pela pelos pelas sobre entre acerca cada este esta estes "
    "estas esse essa esses essas isso isto seu sua seus suas ou ser sao foi sera "
    "serao como quando pode podem mais menos caso respectivo respectiva segundo "
    "assinale alternativa correta incorreta julgue assertiva apresentada item itens "
    "seguinte seguintes respeito considere afirmacoes".split()
)


def sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def ler_csv(caminho):
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def limpar_html(valor):
    texto = html.unescape(str(valor or "")).replace("\\n", " ")
    texto = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", " ", texto,
                   flags=re.I | re.S)
    return re.sub(r"<[^>]+>", " ", texto)


def normalizar(valor):
    texto = unicodedata.normalize("NFKD", limpar_html(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", texto.lower()))


def atributos(texto, caracteres=False):
    palavras = texto.split()
    if caracteres:
        return Counter(
            f"c{n}:{palavra[i:i+n]}"
            for palavra in palavras if len(palavra) >= 4
            for n in (4, 5) for i in range(len(palavra) - n + 1)
        )
    saida = Counter(palavras)
    saida.update(f"{a}::{b}" for a, b in zip(palavras, palavras[1:]))
    return saida


def ancestrais(tema_id, temas):
    resultado, vistos = set(), {tema_id}
    pai = temas[tema_id]["parent_id"]
    while pai:
        if pai not in temas:
            raise ValueError(f"Pai ausente: {pai}")
        if pai in vistos:
            raise ValueError(f"Ciclo na árvore: {tema_id}")
        vistos.add(pai)
        resultado.add(pai)
        pai = temas[pai]["parent_id"]
    return resultado


def referencias(rotulo):
    itens = [rotulo.get("tema_central_id", "")]
    itens += rotulo.get("extras_ids", "").split(";")
    return [x.strip() for x in itens if x.strip()]


def aceito(previsto, rotulo, temas):
    if not previsto or rotulo["fora_da_taxonomia"] == "1":
        return False
    return any(
        previsto == ref or previsto in ancestrais(ref, temas)
        or ref in ancestrais(previsto, temas)
        for ref in referencias(rotulo)
    )


def ler_temas(caminho):
    temas = {}
    for original in ler_csv(caminho):
        registro = dict(original)
        tid = registro["tema_id"].strip()
        if not tid or tid in temas:
            raise ValueError("Tema vazio ou repetido.")
        registro["tema_id"] = tid
        registro["parent_id"] = registro["parent_id"].strip()
        if registro["parent_id"] in {"0", "null", "None"}:
            registro["parent_id"] = ""
        registro["nivel"] = int(registro["nivel"])
        status = normalizar(registro["status"])
        if status not in {"active", "ativo", "1", "true", "sim",
                          "inactive", "inativo", "0", "false", "nao"}:
            raise ValueError(f"Status desconhecido em {tid}.")
        registro["ativo"] = status in {"active", "ativo", "1", "true", "sim"}
        temas[tid] = registro
    for tid in temas:
        ancestrais(tid, temas)
    return temas


def localizar_particao(manifesto):
    encontradas = []

    def nome_grupo(valor):
        if not isinstance(valor, str):
            return None
        nome = normalizar(valor).replace(" ", "_")
        return {
            "desenvolvimento": "desenvolvimento",
            "calibracao": "calibracao_reservada",
            "calibracao_reservada": "calibracao_reservada",
            "teste": "teste_reservado",
            "teste_reservado": "teste_reservado",
        }.get(nome)

    def id_questao(valor):
        return isinstance(valor, str) and bool(re.fullmatch(r"Q\d{4}", valor))

    def grupo_registro(registro):
        campos = [registro[chave] for chave in ("grupo", "particao", "conjunto", "split")
                  if chave in registro]
        if not campos:
            return None
        grupos = [nome_grupo(valor) for valor in campos]
        if any(grupo is None for grupo in grupos) or len(set(grupos)) != 1:
            raise ValueError("Grupo desconhecido ou conflitante em registro da partição.")
        return grupos[0]

    def adicionar_registros(registros):
        divisao = {k: [] for k in GRUPOS}
        for qid, valor in registros:
            grupo = grupo_registro(valor) if isinstance(valor, dict) else nome_grupo(valor)
            if grupo is None:
                raise ValueError(f"Grupo desconhecido na partição do ID {qid}; "
                                 "a divisão original não foi alterada.")
            divisao[grupo].append(qid)
        encontradas.append(divisao)

    def procurar(objeto):
        if isinstance(objeto, dict):
            por_grupo = {}
            for chave, valor in objeto.items():
                grupo = nome_grupo(chave)
                ids = valor.get("ids") if isinstance(valor, dict) else valor
                if grupo and isinstance(ids, list) and all(isinstance(x, str) for x in ids):
                    if grupo in por_grupo:
                        raise ValueError("Duas chaves representam o mesmo grupo no manifesto.")
                    por_grupo[grupo] = ids
            if set(por_grupo) == set(GRUPOS):
                encontradas.append({k: por_grupo[k] for k in GRUPOS})
            if (objeto and all(id_questao(chave) for chave in objeto)
                    and any(nome_grupo(valor) or (isinstance(valor, dict)
                            and any(k in valor for k in ("grupo", "particao", "conjunto", "split")))
                            for valor in objeto.values())):
                adicionar_registros(objeto.items())
            for valor in objeto.values():
                procurar(valor)
        elif isinstance(objeto, list):
            if objeto and all(isinstance(x, dict) and id_questao(x.get("id"))
                              and any(k in x for k in ("grupo", "particao", "conjunto", "split"))
                              for x in objeto):
                adicionar_registros((x["id"], x) for x in objeto)
            for valor in objeto:
                procurar(valor)

    procurar(manifesto)
    if not encontradas:
        chaves = ", ".join(str(k) for k in list(manifesto)[:12]) if isinstance(manifesto, dict) else "sem objeto na raiz"
        raise ValueError("Estrutura de partição ainda não reconhecida. Aceitos: grupo → IDs, "
                         "ID → grupo e registros com id/grupo. "
                         f"Chaves da raiz: {chaves}. "
                         "Envie o manifesto original para adaptar a leitura; não refaça a divisão.")
    serializadas = {json.dumps({k: sorted(x[k]) for k in GRUPOS}, sort_keys=True)
                    for x in encontradas}
    if len(serializadas) != 1:
        raise ValueError("Manifesto contém partições diferentes.")
    return encontradas[0]


def validar_particao(particao, ids_rotulados, ranking):
    juntos = []
    for nome in GRUPOS:
        ids = particao[nome]
        if not ids or any(not isinstance(x, str) for x in ids):
            raise ValueError(f"Partição inválida: {nome}")
        juntos.extend(ids)
    if len(juntos) != len(set(juntos)) or set(juntos) != set(ids_rotulados):
        raise ValueError("Partição repetida, incompleta ou com IDs não rotulados.")
    ids_ranking = [linha["id"] for linha in ranking]
    if (len(ids_ranking) != len(set(ids_ranking))
            or set(ids_ranking) != set(particao["desenvolvimento"])):
        raise ValueError("O ranking inicial não corresponde ao desenvolvimento do manifesto.")


def verificar_hashes_anteriores(manifesto, arquivos):
    """Reconhece os formatos usuais {nome: sha256} sem presumir o nome da seção."""
    encontrados = defaultdict(set)
    todos_hashes = set()

    def procurar(objeto):
        if isinstance(objeto, dict):
            for chave, valor in objeto.items():
                if isinstance(valor, str) and re.fullmatch(r"[0-9a-fA-F]{64}", valor):
                    encontrados[Path(str(chave)).name].add(valor.lower())
                procurar(valor)
        elif isinstance(objeto, list):
            for valor in objeto:
                procurar(valor)
        elif isinstance(objeto, str) and re.fullmatch(r"[0-9a-fA-F]{64}", objeto):
            todos_hashes.add(objeto.lower())

    procurar(manifesto)
    verificados = []
    for nome, caminho in arquivos.items():
        atual = sha256(caminho)
        if nome in encontrados:
            if encontrados[nome] != {atual}:
                raise ValueError(f"{nome} difere do arquivo usado no baseline inicial.")
            verificados.append(nome)
        elif atual in todos_hashes:
            verificados.append(nome)
    if len(verificados) != len(arquivos):
        raise ValueError("Não foi possível confirmar todos os hashes de entrada no "
                         "manifesto. Envie o manifesto para adaptar sua leitura.")
    return verificados


def campo_tema(tema, limpo):
    descricao = tema.get("descricao", "")
    importada = bool(re.match(r"\s*Subtema de\s+", descricao, flags=re.I)
                     and re.search(r"questões no source\.\s*Path:", descricao, flags=re.I))
    if limpo and importada:
        descricao = ""
    return normalizar(" ".join([
        tema["titulo"], tema["titulo"], tema["caminho"], descricao,
    ]))


def texto_completo(questao):
    enunciado = normalizar(questao.get("enunciado_html", ""))
    comando = normalizar(questao.get("comando", ""))
    alternativas = questao.get("alternativas") or {}
    if isinstance(alternativas, dict):
        alternativas = [alternativas[k] for k in sorted(alternativas)]
    elif not isinstance(alternativas, list):
        raise ValueError("Alternativas precisam ser objeto ou lista.")
    return " ".join([enunciado]
                    + ([comando] if comando and comando not in enunciado else [])
                    + [normalizar(x) for x in alternativas])


def filtrar_stopwords(texto, habilitado):
    return " ".join(w for w in texto.split() if w not in STOPWORDS) if habilitado else texto


def campos_questao(questao, atenuar_introducao):
    bruto = str(questao.get("enunciado_html", "") or "")
    enunciado = normalizar(bruto)
    comando = normalizar(questao.get("comando", ""))
    repetido = not comando or comando in enunciado
    alternativas = questao.get("alternativas") or {}
    if isinstance(alternativas, dict):
        alternativas = [alternativas[k] for k in sorted(alternativas)]
    elif not isinstance(alternativas, list):
        raise ValueError("Alternativas precisam ser objeto ou lista.")
    texto_alternativas = normalizar(" ".join(str(x) for x in alternativas))
    peso_enunciado = 0.8 if repetido else 0.6
    campos = []
    partes = re.split(r"(?:<br\s*/?>\s*){2,}|\n\s*\n", bruto, flags=re.I)
    inicio_generico = re.match(
        r"^(em cada (?:um dos itens|item)|nos itens que se seguem|"
        r"julgue os itens que se seguem|cada um dos itens)",
        normalizar(partes[0]),
    )
    if atenuar_introducao and len(partes) > 1 and inicio_generico:
        campos.append((normalizar(partes[0]), peso_enunciado * 0.1))
        campos.append((normalizar(" ".join(partes[1:])), peso_enunciado * 0.9))
    else:
        campos.append((enunciado, peso_enunciado))
    if not repetido:
        campos.append((comando, 0.2))
    campos.append((texto_alternativas, 0.2))
    # Ausência de um campo não reduz toda a escala da questão.
    campos = [(texto, peso) for texto, peso in campos if texto]
    soma = sum(peso for _, peso in campos)
    return [(texto, peso / soma) for texto, peso in campos] if soma else []


class Indice:
    def __init__(self, documentos, caracteres=False):
        self.caracteres = caracteres
        contagens = {tid: atributos(texto, caracteres) for tid, texto in documentos.items()}
        df = Counter(token for doc in contagens.values() for token in doc)
        n = len(contagens)
        self.idf = {token: math.log((1 + n) / (1 + quantidade)) + 1
                    for token, quantidade in df.items()}
        self.invertido = defaultdict(list)
        for tid, contagem in contagens.items():
            for token, peso in self.vetor(contagem).items():
                self.invertido[token].append((tid, peso))

    def vetor(self, contagem):
        valores = {token: (1 + math.log(qtd)) * self.idf[token]
                   for token, qtd in contagem.items() if token in self.idf}
        norma = math.sqrt(sum(x * x for x in valores.values()))
        return {token: valor / norma for token, valor in valores.items()} if norma else {}

    def pontuar(self, texto):
        resultado = defaultdict(float)
        for token, peso in self.vetor(atributos(texto, self.caracteres)).items():
            for tid, peso_tema in self.invertido.get(token, ()):
                resultado[tid] += peso * peso_tema
        return resultado


class Classificador:
    def __init__(self, temas, configuracao):
        self.temas = temas
        self.configuracao = configuracao
        documentos = {
            tid: filtrar_stopwords(campo_tema(tema, configuracao["catalogo_limpo"]),
                                   configuracao.get("stopwords", False))
            for tid, tema in temas.items() if tema["ativo"] and tema["nivel"] != 0
            and all(temas[pai]["ativo"] for pai in ancestrais(tid, temas))
        }
        self.palavras = Indice(documentos)
        self.caracteres = Indice(documentos, True) if configuracao["morfologia"] else None

    def ranquear(self, questao):
        totais = defaultdict(float)
        peso_meta = self.configuracao.get("peso_metadado", 0.0)
        peso_char = self.configuracao.get("peso_caracteres", 0.25)
        if self.configuracao.get("texto_unico"):
            texto = filtrar_stopwords(texto_completo(questao),
                                     self.configuracao.get("stopwords", False))
            campos = [(texto, 1.0)]
        else:
            campos = campos_questao(questao, self.configuracao["introducao"])
        for texto, peso_campo in campos:
            canais = [(self.palavras, 1 - peso_char if self.caracteres else 1.0)]
            if self.caracteres:
                canais.append((self.caracteres, peso_char))
            for indice, peso_canal in canais:
                for tid, valor in indice.pontuar(texto).items():
                    totais[tid] += (1 - peso_meta) * peso_campo * peso_canal * valor
        if peso_meta:
            texto_meta = normalizar(questao.get("assunto_origem", ""))
            for tid, valor in self.palavras.pontuar(texto_meta).items():
                totais[tid] += peso_meta * valor
        if self.configuracao.get("subir_pai"):
            agrupado = {}
            for tid, valor in totais.items():
                pai = self.temas[tid]["parent_id"]
                destino = pai if (self.temas[tid]["nivel"] == 2 and pai
                                  and self.temas[pai]["ativo"]
                                  and self.temas[pai]["nivel"] != 0) else tid
                agrupado[destino] = max(agrupado.get(destino, 0.0), valor)
            totais = agrupado
        return sorted(totais.items(), key=lambda item: (-item[1], item[0]))[:5]


def metricas(linhas):
    dentro = [r for r in linhas if not r["fora_referencia"]]
    n, m = len(linhas), len(dentro)
    return {
        "questoes_avaliadas": n, "questoes_com_tema": m,
        "questoes_fora": n - m,
        "acertos_top1": sum(r["acerto_top1"] for r in linhas),
        "acerto_top1_total": sum(r["acerto_top1"] for r in linhas) / n if n else None,
        "acerto_top1_com_tema": sum(r["acerto_top1"] for r in dentro) / m if m else None,
        "acerto_top5_com_tema": sum(r["acerto_top5"] for r in dentro) / m if m else None,
    }


def avaliar(classificador, ids, questoes, verdade, temas):
    linhas = []
    for qid in sorted(ids):
        candidatos = classificador.ranquear(questoes[qid])
        previsto, score = candidatos[0] if candidatos else ("", 0.0)
        rotulo = verdade[qid]
        linhas.append({
            "id": qid, "tema_previsto": previsto,
            "caminho_previsto": temas[previsto]["caminho"] if previsto else "",
            "score_similaridade": round(score, 6),
            "acerto_top1": aceito(previsto, rotulo, temas),
            "acerto_top5": any(aceito(tid, rotulo, temas) for tid, _ in candidatos),
            "fora_referencia": rotulo["fora_da_taxonomia"] == "1",
            "candidatos_top5": ";".join(tid for tid, _ in candidatos),
        })
    return linhas


def booleano(valor):
    texto = str(valor).strip().lower()
    if texto in {"1", "true", "sim"}:
        return True
    if texto in {"0", "false", "nao", "não"}:
        return False
    raise ValueError(f"Booleano inválido no ranking inicial: {valor!r}")


def executar(dados, manifesto_path, ranking_path, saida):
    inicio = time.perf_counter()
    dados, saida = Path(dados), Path(saida)
    manifesto_path, ranking_path = Path(manifesto_path), Path(ranking_path)
    if saida.exists():
        raise ValueError("A pasta de saída já existe. Escolha outra para preservar o histórico.")
    arquivos = {nome: dados / nome for nome in
                ("questoes.jsonl", "temas.csv", "folha_verdade.csv")}
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8-sig"))
    particao = localizar_particao(manifesto)
    verificar_hashes_anteriores(manifesto, arquivos)
    verdade = {}
    for r in ler_csv(arquivos["folha_verdade.csv"]):
        if r["id"] in verdade:
            raise ValueError("ID repetido na folha-verdade.")
        verdade[r["id"]] = r
    questoes = {}
    with arquivos["questoes.jsonl"].open(encoding="utf-8-sig") as arquivo:
        for linha in arquivo:
            if linha.strip():
                q = json.loads(linha)
                if q["id"] in questoes:
                    raise ValueError("Questão repetida.")
                questoes[q["id"]] = q
    if set(questoes) != {f"Q{i:04d}" for i in range(1, 660)} or len(verdade) != 100:
        raise ValueError("Esperados Q0001 a Q0659 e 100 rótulos oficiais.")
    temas = ler_temas(arquivos["temas.csv"])
    for qid, r in verdade.items():
        if qid not in questoes or r["fora_da_taxonomia"] not in {"0", "1"}:
            raise ValueError("Rótulo oficial inválido.")
        refs = referencias(r)
        if r["fora_da_taxonomia"] == "1" and refs:
            raise ValueError("Rótulo fora com tema.")
        if r["fora_da_taxonomia"] == "0" and not r["tema_central_id"].strip():
            raise ValueError("Rótulo interno sem central.")
        if any(tid not in temas or not temas[tid]["ativo"] for tid in refs):
            raise ValueError("Referência oficial inexistente ou inativa.")
    ranking_base = ler_csv(ranking_path)
    validar_particao(particao, verdade, ranking_base)
    base_avaliada = []
    for r in ranking_base:
        previsto = r["tema_previsto"]
        candidatos = [x for x in r["candidatos_top5"].split(";") if x]
        if previsto and previsto not in temas:
            raise ValueError("Tema inválido no ranking inicial.")
        if any(tid not in temas for tid in candidatos):
            raise ValueError("Candidato inválido no ranking inicial.")
        rotulo = verdade[r["id"]]
        top1 = aceito(previsto, rotulo, temas)
        top5 = any(aceito(tid, rotulo, temas) for tid in candidatos)
        if top1 != booleano(r["acerto_top1"]) or top5 != booleano(r["acerto_top5"]):
            raise ValueError("Métrica inicial incompatível com a folha e a régua do case.")
        base_avaliada.append({"acerto_top1": top1, "acerto_top5": top5,
                              "fora_referencia": rotulo["fora_da_taxonomia"] == "1"})

    resultados = {"baseline_001": metricas(base_avaliada)}
    rankings = {}
    for config in CONFIGURACOES:
        classificador = Classificador(temas, config)
        linhas = avaliar(classificador, particao["desenvolvimento"], questoes, verdade, temas)
        rankings[config["nome"]] = linhas
        resultados[config["nome"]] = metricas(linhas)
    base_por_id = {r["id"]: r for r in ranking_base}
    divergencias_controle = [r["id"] for r in rankings["texto_l0_s0_c0_m0_p0"]
                            if r["tema_previsto"] != base_por_id[r["id"]]["tema_previsto"]
                            or r["candidatos_top5"] != base_por_id[r["id"]]["candidatos_top5"]]
    resumo = {
        "experimento": VERSAO,
        "tipo_avaliacao": "desenvolvimento; várias configurações, sem teste cego",
        "particao": {k: len(v) for k, v in particao.items()},
        "resultados": resultados,
        "divergencias_controle_lexical": divergencias_controle,
        "tempo_execucao_segundos": round(time.perf_counter() - inicio, 3),
        "observacoes": [
            "Mesmos IDs de desenvolvimento do manifesto inicial; divisão não recalculada.",
            "Calibração, teste e outras 559 questões não recebem previsões.",
            "Nenhum rótulo foi alterado, inclusive as marcações oficiais de fora.",
            "Sem treino supervisionado, inferência de LLM ou acesso à rede.",
            "IDs e disciplina_origem não participam dos escores.",
            "Nas variantes m20/m40, assunto_origem é sinal auxiliar; não é verdade nem filtro obrigatório.",
            "Nas variantes p1, um subtema é substituído pelo pai ativo, perdendo especificidade.",
            "Pesos são hipóteses de engenharia; similaridade não é probabilidade.",
            "Melhora no desenvolvimento precisa de validação posterior.",
            "Não há decisão de publicação, detector de fora ou publicacao.csv nesta etapa.",
        ],
    }
    registro = {
        "experimento": VERSAO, "configuracoes": list(CONFIGURACOES),
        "pesos_campos": {"enunciado": 0.6, "comando": 0.2, "alternativas": 0.2,
                          "enunciado_com_comando_repetido_ou_ausente": 0.8},
        "pesos_canais_morfologia": {"palavras": 0.75, "caracteres": 0.25},
        "peso_relativo_introducao_generica": 0.1,
        "stopwords": sorted(STOPWORDS),
        "particao": particao,
        "sha256_entradas": {nome: sha256(p) for nome, p in arquivos.items()},
        "sha256_manifesto_inicial": sha256(manifesto_path),
        "sha256_ranking_inicial": sha256(ranking_path),
        "sha256_codigo": sha256(Path(__file__)),
    }
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".campos-", dir=saida.parent))
    try:
        for nome, linhas in rankings.items():
            with (temporaria / f"ranking_{nome}.csv").open(
                    "w", encoding="utf-8", newline="") as arquivo:
                writer = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
                writer.writeheader()
                writer.writerows(linhas)
        for nome, objeto in (("resumo.json", resumo), ("manifesto.json", registro)):
            (temporaria / nome).write_text(json.dumps(objeto, ensure_ascii=False, indent=2)
                                           + "\n", encoding="utf-8")
        shutil.copyfile(manifesto_path, temporaria / "manifesto_inicial.json")
        linhas = ["# Comparação no desenvolvimento", "",
                  "| Configuração | Top 1 / todos | Top 1 / com tema | Top 5 / com tema |",
                  "|---|---:|---:|---:|"]
        for nome, m in resultados.items():
            linhas.append(f"| {nome} | {m['acerto_top1_total']:.2%} | "
                          f"{m['acerto_top1_com_tema']:.2%} | {m['acerto_top5_com_tema']:.2%} |")
        linhas += ["", "Similaridade não é confiança calibrada. Não há publicação nesta etapa.",
                   "As marcações oficiais de fora foram mantidas. "
                   "Nenhuma previsão foi produzida para calibração ou teste.", ""]
        (temporaria / "comparacao.md").write_text("\n".join(linhas), encoding="utf-8")
        if saida.exists():
            raise ValueError("A pasta de saída surgiu durante a execução; nada foi sobrescrito.")
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    return resumo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    parser.add_argument("--manifesto", type=Path,
                        default=Path("experimentos/baseline_001/manifesto.json"))
    parser.add_argument("--ranking-base", type=Path,
                        default=Path("experimentos/baseline_001/ranking_desenvolvimento.csv"))
    parser.add_argument("--saida", type=Path, default=Path("experimentos/campos_001"))
    parser.add_argument("--json", action="store_true", help="Exibe também o resumo JSON completo.")
    args = parser.parse_args()
    try:
        resumo = executar(args.dados, args.manifesto, args.ranking_base, args.saida)
    except (ValueError, OSError, KeyError, TypeError) as erro:
        parser.exit(2, f"Erro: {erro}\n")
    print("Avaliação somente no desenvolvimento. Nenhuma decisão de publicação.")
    if resumo["divergencias_controle_lexical"]:
        print("Atenção: o controle lexical divergiu do ranking inicial. "
              "Confira divergencias_controle_lexical no resumo antes de comparar.")
    print("Configuração                                      Top1/todos  Top1/tema  Top5/tema")
    for nome, m in resumo["resultados"].items():
        print(f"{nome:48} {m['acertos_top1']:2}/{m['questoes_avaliadas']:<3} "
              f"      {m['acerto_top1_com_tema']:6.2%}     {m['acerto_top5_com_tema']:6.2%}")
    print(f"Resultados completos: {args.saida / 'resumo.json'}")
    if args.json:
        print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
