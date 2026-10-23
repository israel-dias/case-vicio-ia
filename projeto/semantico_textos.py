"""Preparação textual compartilhada. Não consulta rótulos nem escolhe temas."""
import hashlib
import math
import re

import experimento_campos as base

VERSAO_TEXTOS = "semantico_textos_v1"


def texto_questao(questao):
    enunciado = " ".join(base.limpar_html(questao.get("enunciado_html", "")).split())
    comando = " ".join(base.limpar_html(questao.get("comando", "")).split())
    partes = [enunciado]
    if comando and base.normalizar(comando) not in base.normalizar(enunciado):
        partes.append(comando)
    alternativas = questao.get("alternativas") or {}
    if isinstance(alternativas, dict):
        partes += [f"{k}) {' '.join(base.limpar_html(alternativas[k]).split())}"
                   for k in sorted(alternativas)]
    elif isinstance(alternativas, list):
        partes += [" ".join(base.limpar_html(x).split()) for x in alternativas]
    else:
        raise ValueError("Alternativas precisam ser objeto ou lista.")
    return "\n".join(x for x in partes if x)


def texto_tema(tema):
    descricao = tema.get("descricao", "")
    if (re.match(r"\s*Subtema de\s+", descricao, flags=re.I)
            and re.search(r"questões no source\.\s*Path:", descricao, flags=re.I)):
        descricao = ""
    partes = [f"Disciplina: {tema['disciplina']}.", f"Tema: {tema['titulo']}.",
              f"Caminho: {tema['caminho']}."]
    if descricao:
        partes.append("Descrição: " + " ".join(base.limpar_html(descricao).split()))
    return "\n".join(partes)


def hash_texto(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def normalizar_vetor(vetor):
    if (not isinstance(vetor, (list, tuple)) or not vetor
            or any(isinstance(x, bool) or not isinstance(x, (int, float))
                   or not math.isfinite(x) for x in vetor)):
        raise ValueError("Vetor inválido: esperado número finito em cada dimensão.")
    norma = math.sqrt(sum(x * x for x in vetor))
    if norma <= 0:
        raise ValueError("Vetor com norma zero.")
    return [x / norma for x in vetor]


def temas_candidatos(temas):
    return {tid: t for tid, t in temas.items()
            if t["ativo"] and t["nivel"] != 0
            and all(temas[pai]["ativo"] for pai in base.ancestrais(tid, temas))}
