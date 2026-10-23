"""Compara duas respostas reais. Concordância não comprova precisão."""
import argparse
import json
from collections import Counter
from pathlib import Path
from vicio_ia.arquivos import carregar_json, gravar_json, sha256
from vicio_ia.importacao import validar_resposta
from vicio_ia.temas import mesmo_ramo, validar_temas


def ler_execucao(pasta, temas):
    registro = carregar_json((pasta / "registro_execucao.json").read_text(encoding="utf-8"))
    manifesto = registro["manifesto_lote"]
    original = pasta / "resposta_original.json"
    if sha256(original) != registro["sha256_resposta_original"]:
        raise ValueError(f"Resposta original alterada: {pasta}")
    if sha256(pasta / "prompt.txt") != manifesto["sha256_prompt"]:
        raise ValueError(f"Prompt alterado: {pasta}")
    registros = validar_resposta(carregar_json(original.read_text(encoding="utf-8-sig")),
                                manifesto["ids"], set(temas))
    normalizados = carregar_json((pasta / "classificacoes_validadas.json").read_text(encoding="utf-8"))
    if registros != normalizados["classificacoes"]:
        raise ValueError(f"Registros diferentes da resposta original: {pasta}")
    return {r["id"]: r for r in registros}, registro


def comparar(v1, v2, temas_path):
    temas_lista = carregar_json(temas_path.read_text(encoding="utf-8"))
    temas = validar_temas(temas_lista)
    ativos = {i: t for i, t in temas.items() if t["status"] == "active"}
    a, ra = ler_execucao(v1, ativos)
    b, rb = ler_execucao(v2, ativos)
    ma, mb = ra["manifesto_lote"], rb["manifesto_lote"]
    if set(a) != set(b) or ma["sha256_questoes"] != mb["sha256_questoes"]:
        raise ValueError("As execuções não usam as mesmas questões.")
    if ma["sha256_temas"] != mb["sha256_temas"] or sha256(temas_path) != ma["sha256_temas"]:
        raise ValueError("As execuções não usam o mesmo catálogo ativo.")
    if ma["sha256_prompt"] == mb["sha256_prompt"]:
        raise ValueError("Os prompts são iguais; não há comparação entre versões de prompt.")
    linhas = []
    for identificador in sorted(a):
        x, y = a[identificador], b[identificador]
        tx, ty = x["tema_central_id"], y["tema_central_id"]
        linhas.append({
            "id": identificador, "sugestao_v1": x["sugestao_decisao"],
            "sugestao_v2": y["sugestao_decisao"], "tema_v1": tx, "tema_v2": ty,
            "caminho_v1": temas[tx]["caminho"] if tx else None,
            "caminho_v2": temas[ty]["caminho"] if ty else None,
            "mudou_sugestao": x["sugestao_decisao"] != y["sugestao_decisao"],
            "mudou_tema_central": tx != ty,
            "temas_no_mesmo_ramo": mesmo_ramo(tx, ty, temas) if tx and ty else None,
            "justificativa_v1": x["justificativa"], "justificativa_v2": y["justificativa"],
            "alertas_v1": x["alertas"], "alertas_v2": y["alertas"],
            "resultado_juridico_confirmado": None,
        })
    contar = lambda rs: {d: Counter(r["sugestao_decisao"] for r in rs.values()).get(d, 0)
                         for d in ["publicar", "revisar", "fora"]}
    return {
        "questoes": len(linhas), "sugestoes_v1": contar(a), "sugestoes_v2": contar(b),
        "mudancas_sugestao": sum(l["mudou_sugestao"] for l in linhas),
        "mudancas_tema_central": sum(l["mudou_tema_central"] for l in linhas),
        "precisao_medida": None,
        "modelo_informado_v1": ra["modelo_informado"], "modelo_informado_v2": rb["modelo_informado"],
        "nota_v1": ra["nota_operador"], "nota_v2": rb["nota_operador"],
        "limites": [
            "Concordância entre rodadas não equivale a acerto.",
            "Mudança de classificação não comprova melhoria.",
            "Contexto anterior, configuração e modelo podem diferir.",
            "O piloto é de desenvolvimento; não é referência jurídica independente.",
        ],
        "comparacoes": linhas,
    }


def markdown(resultado):
    linhas = ["# Comparação exploratória dos pilotos", "",
              f"Questões comparadas: {resultado['questoes']}.",
              f"Mudanças de sugestão: {resultado['mudancas_sugestao']}.",
              f"Mudanças de tema central: {resultado['mudancas_tema_central']}.",
              "Precisão jurídica: **não medida**.", "",
              "| Questão | Sugestão v1 | Tema v1 | Sugestão v2 | Tema v2 |",
              "|---|---|---|---|---|"]
    for l in resultado["comparacoes"]:
        linhas.append(f"| {l['id']} | {l['sugestao_v1']} | {l['tema_v1'] or ''} | "
                      f"{l['sugestao_v2']} | {l['tema_v2'] or ''} |")
    linhas += ["", "## Divergências para inspeção", ""]
    diferentes = [l for l in resultado["comparacoes"] if l["mudou_sugestao"] or l["mudou_tema_central"]]
    if not diferentes:
        linhas.append("Nenhuma divergência de sugestão ou tema central. Isso não demonstra acerto.")
    for l in diferentes:
        linhas += [f"### {l['id']}", "", "v1: " + l["justificativa_v1"], "",
                   "v2: " + l["justificativa_v2"], "",
                   "Conclusão jurídica confirmada: pendente.", ""]
    linhas += ["", "## Limites", ""]
    linhas += ["- " + texto for texto in resultado["limites"]]
    return "\n".join(linhas) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--v1", type=Path, default=Path("execucoes/piloto_exploratorio_v1"))
    p.add_argument("--v2", type=Path, default=Path("execucoes/piloto_verificacao_v2"))
    p.add_argument("--temas", type=Path, default=Path("lotes_v1/piloto/temas_ativos.json"))
    p.add_argument("--saida", type=Path, default=Path("analises/comparacao_v1_v2"))
    args = p.parse_args()
    try:
        resultado = comparar(args.v1, args.v2, args.temas)
        args.saida.mkdir(parents=True, exist_ok=True)
        gravar_json(args.saida / "comparacao.json", resultado)
        (args.saida / "comparacao.md").write_text(markdown(resultado), encoding="utf-8")
    except (ValueError, KeyError, OSError) as exc:
        p.exit(2, f"Erro: {exc}\n")
    print(json.dumps({k: v for k, v in resultado.items() if k not in ["comparacoes", "limites", "nota_v1", "nota_v2"]},
                     ensure_ascii=False, indent=2))
    print("Leitura:", args.saida / "comparacao.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
