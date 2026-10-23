"""Diagnóstico estrutural automático; não estima acerto jurídico."""
from collections import Counter
from .temas import titulos_repetidos


def diagnosticar(originais, preparadas, temas):
    def textos(q):
        return [q["enunciado_html"], q["comando"], *q["alternativas"].values()]
    return {
        "questoes": len(preparadas), "ids_unicos": len({q["id"] for q in preparadas}),
        "temas": len(temas), "status_temas": dict(Counter(t["status"] for t in temas)),
        "niveis_temas": dict(Counter(t["nivel"] for t in temas)),
        "temas_por_disciplina": dict(Counter(t["disciplina"] for t in temas)),
        "origens_questoes": dict(Counter(q["disciplina_origem"] for q in originais)),
        "alternativas_por_questao": dict(Counter(str(len(q["alternativas"])) for q in originais)),
        "campos_vazios": {c: sum(not q[c].strip() for q in originais)
                         for c in ("comando", "disciplina_origem", "assunto_origem")},
        "questoes_com_escape_literal_n": sum(any("\\n" in t for t in textos(q)) for q in originais),
        "temas_sem_descricao": [t["tema_id"] for t in temas if not t["descricao"].strip()],
        "temas_inativos": [t for t in temas if t["status"] == "inactive"],
        "titulos_repetidos": [[{"tema_id": t["tema_id"], "caminho": t["caminho"],
                              "status": t["status"]} for t in g] for g in titulos_repetidos(temas)],
        "questoes_com_alertas": [{"id": q["id"], "alertas": q["alertas_preparacao"]}
                               for q in preparadas if q["alertas_preparacao"]],
        "limite": "Diagnóstico estrutural. Não há classificações finais nem precisão medida.",
    }


def markdown_diagnostico(d):
    linhas = ["# Diagnóstico da preparação", "", d["limite"], "",
              "| Verificação | Resultado |", "|---|---:|",
              f"| Questões / IDs únicos | {d['questoes']} / {d['ids_unicos']} |",
              f"| Temas ativos | {d['status_temas'].get('active', 0)} |",
              f"| Temas inativos | {d['status_temas'].get('inactive', 0)} |",
              f"| Temas sem descrição | {len(d['temas_sem_descricao'])} |",
              f"| Grupos de títulos repetidos | {len(d['titulos_repetidos'])} |"]
    for campo, numero in d["campos_vazios"].items():
        linhas.append(f"| Campo vazio: {campo} | {numero} |")
    linhas += ["", "## Títulos repetidos", "",
               "Não fundir IDs automaticamente. Caminhos distintos podem exigir revisão.", ""]
    for grupo in d["titulos_repetidos"]:
        linhas.append("- " + " / ".join(f"{t['tema_id']}: {t['caminho']}" for t in grupo))
    linhas += ["", "## Interpretação", "",
               "Comando vazio pode ter sua instrução no enunciado. Disciplina de origem fora "
               "do catálogo não determina que a questão seja fora. Alertas são pistas para "
               "inspeção, não classificações.", "",
               "A árvore foi validada quanto a IDs, pais, ciclos, níveis e status.", ""]
    return "\n".join(linhas)
