"""Métricas separam desenvolvimento exposto, alvo e adições."""
from collections import Counter


def medir(rows, base=None):
    if not rows or len(rows) != len({r["id"] for r in rows}):
        raise ValueError("Conjunto vazio ou IDs repetidos.")
    pubs = [r for r in rows if r["decisao"] == "publicar"]
    rotuladas = all("correto" in r for r in rows)
    out = {"questoes": len(rows), "publicar": len(pubs), "revisar": len(rows) - len(pubs),
           "fora": 0, "cobertura": len(pubs) / len(rows), "precisao_real_alvo": None,
           "motivos_revisao": dict(Counter(r.get("motivo", "") for r in rows if r["decisao"] == "revisar"))}
    if rotuladas:
        c = sum(int(r["correto"]) for r in pubs)
        out.update(acertos_top1=sum(int(r["correto"]) for r in rows),
                   acertos_publicadas=c, erros_publicadas=len(pubs)-c,
                   precisao_desenvolvimento=c/len(pubs) if pubs else None,
                   fora_oficial_publicadas=sum(int(r["fora_oficial"]) for r in pubs),
                   brier=sum((float(r["confianca"])-int(r["correto"]))**2 for r in rows)/len(rows),
                   meta_95_na_amostra=bool(pubs and c/len(pubs) >= .95),
                   prova_de_minimo_95_populacional=False)
    if base is not None:
        antes = {r["id"]: r for r in base}
        if set(antes) != {r["id"] for r in rows}:
            raise ValueError("Controle e variante têm conjuntos diferentes.")
        novas = [r for r in pubs if antes[r["id"]]["decisao"] != "publicar"]
        perdidas = [r for r in rows if r["decisao"] != "publicar" and antes[r["id"]]["decisao"] == "publicar"]
        trocas = [r for r in pubs if antes[r["id"]]["decisao"] == "publicar" and antes[r["id"]]["tema_central_id"] != r["tema_central_id"]]
        out.update(novas_publicacoes=len(novas), publicacoes_anteriores_perdidas=len(perdidas),
                   publicadas_com_tema_trocado=len(trocas))
        if rotuladas:
            out.update(novas_corretas=sum(int(r["correto"]) for r in novas),
                       novas_erradas=sum(1-int(r["correto"]) for r in novas),
                       acertos_perdidos=sum(int(antes[r["id"]]["correto"]) for r in perdidas),
                       erros_retidos=sum(1-int(r["correto"]) for r in pubs if antes[r["id"]]["decisao"] == "publicar"))
        # Comparação da união é apenas descritiva; não ativa uma nova política.
        uniao = [antes[r["id"]] if antes[r["id"]]["decisao"] == "publicar" else r for r in rows]
        pu = [r for r in uniao if r["decisao"] == "publicar"]
        out["uniao_descritiva_nao_ativada"] = {
            "publicar": len(pu), "cobertura": len(pu)/len(rows),
            "precisao_desenvolvimento": sum(int(r["correto"]) for r in pu)/len(pu) if pu and rotuladas else None,
            "politica_calibrada_para_uniao": False,
        }
    return out


def curva_descritiva(rows):
    """Não escolhe limiar: descreve os escores OOF depois da avaliação."""
    if not all("correto" in r for r in rows):
        raise ValueError("A curva de erro exige referências.")
    out = []
    for corte in [j/100 for j in range(101)]:
        pubs = [r for r in rows if r["elegivel"] and r["confianca"] >= corte]
        c = sum(int(r["correto"]) for r in pubs)
        out.append({"corte_descritivo": corte, "publicar": len(pubs),
                    "cobertura": len(pubs)/len(rows),
                    "precisao": c/len(pubs) if pubs else None,
                    "erro": 1-c/len(pubs) if pubs else None})
    return out
