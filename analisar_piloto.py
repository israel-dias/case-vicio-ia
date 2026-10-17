"""Resumo do piloto assistido. Não avalia acerto jurídico nem decide publicações.

Copie este arquivo para a pasta case-vicio-ia e execute:
    python analisar_piloto.py

Usa os registros reais do projeto. Requer somente Python e o pacote vicio_ia
já entregue. Os dados originais e as sugestões permanecem inalterados.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from vicio_ia.arquivos import carregar_json, gravar_json, sha256
from vicio_ia.importacao import validar_resposta
from vicio_ia.preparacao import normalizar_nome
from vicio_ia.temas import mesmo_ramo, validar_temas


def tipo_descricao(tema):
    texto = tema["descricao"].strip()
    if not texto:
        return "ausente"
    if texto.startswith("Subtema de ") or texto.startswith("Disciplina (root)."):
        return "padrao_importacao"
    return "outra_descricao"


def construir_resumo(registros, temas, metadados):
    indice = validar_temas(temas)
    ativos = [t for t in temas if t["status"] == "active"]
    contagem = Counter(r["sugestao_decisao"] for r in registros)
    descricoes = Counter(tipo_descricao(t) for t in ativos)
    linhas = []
    for r in registros:
        central = r["tema_central_id"]
        tema = indice.get(central)
        homonimos = [] if not tema else [
            t["tema_id"] for t in ativos
            if t["tema_id"] != central
            and normalizar_nome(t["titulo"]) == normalizar_nome(tema["titulo"])
            and not mesmo_ramo(central, t["tema_id"], indice)
        ]
        concorrentes = [
            {"tema_id": identificador, "caminho": indice[identificador]["caminho"],
             "mesmo_ramo_central": mesmo_ramo(central, identificador, indice) if central else None}
            for identificador in r["temas_concorrentes_ids"]
        ]
        linhas.append({
            "id": r["id"], "sugestao_ia": r["sugestao_decisao"],
            "tema_central_id": central, "caminho_central": tema["caminho"] if tema else None,
            "confianca_autodeclarada": r["confianca_modelo"],
            "justificativa_ia": r["justificativa"], "alertas_ia": r["alertas"],
            "tipo_descricao_central": tipo_descricao(tema) if tema else None,
            "homonimos_em_outros_ramos": homonimos, "temas_concorrentes": concorrentes,
            "revisao_especialista": "nao_realizada",
            "prioridade_de_inspecao": (
                "revisar_ambiguidade" if r["sugestao_decisao"] == "revisar"
                else "verificar_antes_de_publicar" if r["sugestao_decisao"] == "publicar"
                else "verificar_ausencia_de_tema"
            ),
        })
    centrais = {r["tema_central_id"] for r in registros if r["tema_central_id"]}
    return {
        "fase": "piloto_exploratorio_de_desenvolvimento",
        "questoes_analisadas": len(registros),
        "sugestoes": {d: contagem.get(d, 0) for d in ["publicar", "revisar", "fora"]},
        "fracao_candidatas_publicacao": contagem.get("publicar", 0) / len(registros) if registros else None,
        "publicacoes_finais_definidas": False,
        "precisao_medida": None,
        "referencia_juridica_independente": "nao_disponivel",
        "descricao_catalogo_ativo": {
            "total": len(ativos), "ausente": descricoes.get("ausente", 0),
            "padrao_importacao": descricoes.get("padrao_importacao", 0),
            "outra_descricao": descricoes.get("outra_descricao", 0),
        },
        "temas_centrais_distintos": len(centrais),
        "centrais_com_descricao_padrao": sum(tipo_descricao(indice[i]) == "padrao_importacao"
                                            for i in centrais),
        "origem_execucao": metadados["origem"],
        "modelo_informado": metadados["modelo_informado"],
        "nota_operador": metadados["nota_operador"],
        "custo_api_executado_usd": metadados.get("custo_api_executado_usd"),
        "tokens_api_medidos": metadados.get("tokens_api_medidos"),
        "limites": [
            "Sugestões não são classificações definitivas.",
            "Confiança autodeclarada não é precisão medida nem probabilidade calibrada.",
            "Revisão pelo mesmo assistente não constitui referência jurídica independente.",
            "Piloto de desenvolvimento não estima sozinho o desempenho nas 359 questões.",
            "Contagem por prefixo identifica um padrão textual de descrição, não sua verdade jurídica.",
        ],
        "questoes": linhas,
    }


def celula(texto):
    return str(texto).replace("|", "\\|").replace("\n", " ")


def como_markdown(resumo):
    s = resumo["sugestoes"]
    linhas = [
        "# Resumo do piloto exploratório", "",
        "## Estado", "",
        f"- Questões analisadas: {resumo['questoes_analisadas']}.",
        f"- Sugestões: {s['publicar']} candidatas a publicar, {s['revisar']} para revisão, {s['fora']} fora.",
        "- Precisão jurídica: **não medida**.",
        "- Publicações finais: ainda não definidas.",
        "- Referência jurídica independente: não disponível.",
        "",
        "Estes números descrevem as sugestões da IA, não um gabarito nem a cobertura final.",
        "", "## Diagnóstico das descrições", "",
    ]
    d = resumo["descricao_catalogo_ativo"]
    linhas += [
        f"Dos {d['total']} temas ativos, {d['padrao_importacao']} têm descrição com prefixo "
        f"do padrão de importação, {d['ausente']} estão sem descrição e "
        f"{d['outra_descricao']} têm descrição diferente desse padrão.",
        f"Os {resumo['temas_centrais_distintos']} temas centrais distintos do piloto incluem "
        f"{resumo['centrais_com_descricao_padrao']} com descrição no padrão de importação.",
        "",
        "Acrescentar metadados repetidos ao prompt não fornece automaticamente limites "
        "semânticos para resolver homônimos ou categorias Parte 1 e Parte 2.",
        "", "## Sugestões e prioridades", "",
        "| Questão | Sugestão IA | ID | Tema central | Confiança autodeclarada |",
        "|---|---|---|---|---|",
    ]
    for q in resumo["questoes"]:
        confianca = "não aplicável" if q["confianca_autodeclarada"] is None else f"{q['confianca_autodeclarada']:.2f}"
        linhas.append(f"| {q['id']} | {q['sugestao_ia']} | {q['tema_central_id'] or ''} | "
                      f"{celula(q['caminho_central'] or '')} | {confianca} |")
    linhas += ["", "## Casos propostos para revisão", ""]
    for q in resumo["questoes"]:
        if q["sugestao_ia"] == "revisar":
            linhas += [f"### {q['id']}", "", q["justificativa_ia"], ""]
            if q["homonimos_em_outros_ramos"]:
                linhas += ["Homônimos estruturais em outros ramos: "
                           + ", ".join(q["homonimos_em_outros_ramos"]) + ".", ""]
            if q["temas_concorrentes"]:
                linhas += ["Temas concorrentes apontados pela IA: "
                           + ", ".join(c["tema_id"] for c in q["temas_concorrentes"]) + ".", ""]
    linhas += [
        "## Próximas decisões", "",
        "1. Confirmar o escopo e a equivalência dos temas sobrepostos, ou documentar a "
        "hipótese adotada e manter os casos sem evidência suficiente na revisão.",
        "2. Verificar as candidatas à publicação. Revisão pelo mesmo assistente é exploratória.",
        "3. Reservar uma avaliação separada dos exemplos utilizados para ajustar o sistema.",
        "4. Definir as regras de publicação antes de estimar precisão.",
        "5. Registrar mudanças de prompt, decisões manuais e limitações das referências.",
        "", "## Proveniência", "",
        f"Origem: {celula(resumo['origem_execucao'])}.",
        f"Modelo informado: {celula(resumo['modelo_informado'])}.",
        f"Nota do operador: {celula(resumo['nota_operador'])}.",
        "", "## Limites", "",
    ]
    linhas += ["- " + limite for limite in resumo["limites"]]
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Resumir o piloto importado sem medir acerto jurídico")
    parser.add_argument("--execucao", type=Path, default=Path("execucoes/piloto_exploratorio_v1"))
    parser.add_argument("--lote", type=Path, default=Path("lotes_v1/piloto"))
    parser.add_argument("--saida", type=Path, default=Path("analises/piloto_v1"))
    args = parser.parse_args()
    try:
        execucao, lote = args.execucao, args.lote
        registro = carregar_json((execucao / "registro_execucao.json").read_text(encoding="utf-8"))
        manifesto = registro["manifesto_lote"]
        temas_path = lote / "temas_ativos.json"
        if sha256(temas_path) != manifesto["sha256_temas"]:
            raise ValueError("Catálogo atual diferente daquele registrado na execução.")
        original = execucao / "resposta_original.json"
        if sha256(original) != registro["sha256_resposta_original"]:
            raise ValueError("Resposta original foi alterada após a importação.")
        if sha256(execucao / "prompt.txt") != manifesto["sha256_prompt"]:
            raise ValueError("Prompt registrado foi alterado após a importação.")
        temas = carregar_json(temas_path.read_text(encoding="utf-8"))
        ativos = {t["tema_id"] for t in temas if t["status"] == "active"}
        registros = validar_resposta(
            carregar_json(original.read_text(encoding="utf-8-sig")), manifesto["ids"], ativos)
        normalizados = carregar_json(
            (execucao / "classificacoes_validadas.json").read_text(encoding="utf-8"))
        if registros != normalizados["classificacoes"]:
            raise ValueError("Registros validados diferentes da resposta original.")
        resumo = construir_resumo(registros, temas, registro)
        args.saida.mkdir(parents=True, exist_ok=True)
        gravar_json(args.saida / "resumo.json", resumo)
        (args.saida / "resumo.md").write_text(como_markdown(resumo), encoding="utf-8")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")
    print(json.dumps({
        "questoes_analisadas": resumo["questoes_analisadas"],
        "sugestoes": resumo["sugestoes"],
        "precisao_medida": "não medida",
        "descricao_catalogo_ativo": resumo["descricao_catalogo_ativo"],
        "arquivo_para_leitura": str(args.saida / "resumo.md"),
        "dados_detalhados": str(args.saida / "resumo.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
