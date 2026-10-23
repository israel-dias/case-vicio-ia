"""Gera um visor HTML local a partir da entrega e da auditoria salvas.

Não classifica questões, não consulta modelos e não altera os arquivos de entrega.
O HTML gerado contém seus dados, estilos e scripts e pode ser aberto sem servidor.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import tempfile

from finalizar_case import gerar as reproduzir_entrega


REPOSITORIO = "https://github.com/israel-dias/case-vicio-ia"
PROJETO = Path(__file__).resolve().parent


def ler_json(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


def ler_csv(caminho):
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def sha256(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def verificar_entrega(projeto):
    """Reutiliza a validação do exportador antes de apresentar a entrega da raiz."""
    with tempfile.TemporaryDirectory(prefix="vicio-visor-") as pasta:
        destino = Path(pasta)
        resumo = reproduzir_entrega(projeto, destino)
        for nome in ("publicacao.csv", "previsao.txt"):
            if (projeto / nome).read_bytes() != (destino / nome).read_bytes():
                raise ValueError(
                    f"{nome} da raiz diverge da auditoria. Confira a entrega antes de gerar o visor."
                )
    return resumo


def montar_dados(projeto):
    projeto = Path(projeto)
    resumo = verificar_entrega(projeto)
    questoes = [json.loads(linha) for linha in
                (projeto / "dados/processados/questoes_preparadas.jsonl")
                .read_text(encoding="utf-8").splitlines() if linha.strip()]
    auditoria = ler_json(projeto / "auditoria_v4/reexame_359.json")["registros"]
    temas = {t["tema_id"]: t for t in ler_csv(projeto / "dados/originais/temas.csv")}
    por_id = {q["id"]: q for q in questoes}
    if len(por_id) != len(questoes) or set(por_id) != {a["id"] for a in auditoria}:
        raise ValueError("Questões preparadas e auditoria precisam conter os mesmos IDs, sem duplicatas.")
    previsao = ler_json(projeto / "docs/PREMISSAS_PREVISAO.json")
    fontes_dirigidas = ler_json(projeto / "auditoria_v4/fontes/reavaliacao_57.json")["fontes"]

    def tema(identificador):
        if not identificador:
            return None
        t = temas[identificador]
        return {k: t[k] for k in ("tema_id", "titulo", "caminho", "disciplina", "descricao", "status")}

    def classificacao(linha):
        return {**linha, "central": tema(linha["tema_central_id"]),
                "extras": [tema(t) for t in linha["extras_ids"].split(";") if t]}

    registros = []
    for a in sorted(auditoria, key=lambda registro: registro["id"]):
        identificador = a["id"]
        antes, atual = a["antes"], a["depois"]
        mudancas = {"decisao": antes["decisao"] != atual["decisao"],
                    "central": antes["tema_central_id"] != atual["tema_central_id"],
                    "extras": antes["extras_ids"] != atual["extras_ids"]}
        mudancas["qualquer"] = any(mudancas.values())
        fontes = [{k: f[k] for k in ("fonte", "url", "estado", "artigos", "limite") if k in f}
                  for f in fontes_dirigidas if identificador in f.get("ids", [])]
        registros.append({
            "id": identificador,
            "questao": por_id[identificador],
            "antes": classificacao(antes),
            "atual": classificacao(atual),
            "mudancas": mudancas,
            "resposta": a["resposta_proposta"],
            "estado_resposta": a["estado_resposta"],
            "gabarito": a["gabarito_oficial"],
            "analise": a["analise_individual"],
            "fundamento": a["fundamento_indicado"],
            "conferencias": a.get("conferencias_dirigidas_registradas", []),
            "justificativas_extras": a.get("justificativas_extras_independentes", {}),
            "fontes": fontes,
            "busca": a["busca_registrada"],
            "data_reexame": a["data_reexame"],
        })
    estados = Counter(r["estado_resposta"] for r in registros)
    totais = Counter(r["atual"]["decisao"] for r in registros)
    usados = {t["tema_id"]: t for r in registros
              for t in ([r["atual"]["central"]] if r["atual"]["central"] else []) + r["atual"]["extras"]}
    fontes = ["publicacao.csv", "previsao.txt", "dados/processados/questoes_preparadas.jsonl",
              "dados/originais/temas.csv", "auditoria_v4/reexame_359.json"]
    return {
        "meta": {"versao": 1, "data_auditoria": "2026-10-16", "repositorio": REPOSITORIO,
                 "total": len(registros), "decisoes": dict(totais),
                 "cobertura": totais["publicar"] / len(registros),
                 "precisao_medida": resumo["precisao_medida"],
                 "precisao_prevista_subjetiva": previsao["precisao_prevista"],
                 "sensibilidade_subjetiva": previsao["intervalo_sensibilidade"],
                 "estados_resposta": dict(estados),
                 "mudancas": {campo: sum(r["mudancas"][campo] for r in registros)
                              for campo in ("decisao", "central", "extras", "qualquer")},
                 "arquivos_sha256": {nome: sha256(projeto / nome) for nome in fontes}},
        "temas": sorted(usados.values(), key=lambda t: (t["caminho"], t["tema_id"])),
        "registros": registros,
    }


def serializar_dados(dados):
    """Escapa delimitadores de HTML, preservando o texto após JSON.parse."""
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    for caractere, escape in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"),
                             ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        texto = texto.replace(caractere, escape)
    return texto


def gerar(projeto=PROJETO, saida=None):
    projeto = Path(projeto)
    destino = Path(saida) if saida is not None else projeto / "visor/index.html"
    if destino.suffix.lower() != ".html" or destino.resolve() == (projeto / "visor/modelo.html").resolve():
        raise ValueError("Escolha um arquivo HTML de saída diferente do modelo.")
    dados = montar_dados(projeto)
    pasta = projeto / "visor"
    conteudo = (pasta / "modelo.html").read_text(encoding="utf-8")
    substituicoes = {
        "<!-- VICIO_ESTILOS -->": (pasta / "estilos.css").read_text(encoding="utf-8"),
        "<!-- VICIO_DADOS -->": serializar_dados(dados),
        "<!-- VICIO_FILTROS -->": (pasta / "filtros.js").read_text(encoding="utf-8"),
        "<!-- VICIO_APP -->": (pasta / "app.js").read_text(encoding="utf-8"),
    }
    for marcador, texto in substituicoes.items():
        if conteudo.count(marcador) != 1:
            raise ValueError("Marcador ausente ou duplicado no modelo: " + marcador)
        conteudo = conteudo.replace(marcador, texto)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Só substitui o visor após todas as validações e a montagem terem sucesso.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                     dir=destino.parent, suffix=".tmp", delete=False) as arquivo:
        temporario = Path(arquivo.name)
        arquivo.write(conteudo)
    try:
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)
    return {"questoes": dados["meta"]["total"], "decisoes": dados["meta"]["decisoes"],
            "arquivo": str(destino), "bytes": destino.stat().st_size,
            "precisao_medida": dados["meta"]["precisao_medida"], "nova_inferencia": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, help="Arquivo HTML; padrão: visor/index.html.")
    args = parser.parse_args()
    try:
        resultado = gerar(saida=args.saida)
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
