"""Mesmo recuperador, candidatos e guardas; apenas o comparador varia.

V11 significa o comparador com seus 39 atributos, sem a regra de aprovação
direta por identificador e sem preservar publicações de outra versão.
"""
from collections import Counter

from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from roteamento_v15 import modelo as v15
from experimento_atributos_v11 import modelo as v11

VARIANTES = ("primeiro_fusao_v15", "reordenar_v11", "reordenar_v15")
COMPARADOR = {"primeiro_fusao_v15": "v15", "reordenar_v11": "v11", "reordenar_v15": "v15"}
IX_V11 = v11.indices("sem_apoio_duplo")
ATRIBUTOS = {"v11": [v11.ATRIBUTOS[j] for j in IX_V11], "v15": list(v15.NOMES)}
TOP_K = 5


def preparar(cat, dic, qs):
    # As duas representações recebem os mesmos textos e metadados. Congelar a
    # fusão V15 preserva também seu uso histórico de metadados de origem.
    pp = v15.preparar(cat, dic, qs)["fusao_contextual"]
    legado = v11.preparar(cat, dic, qs)
    return {i: {
        **p,
        "x_v11": legado[i]["x_mescla"][:, IX_V11],
        "candidatos": [int(k) for k in f.ordenar(p["ranking"])[:TOP_K]],
    } for i, p in pp.items()}


def matriz(p, comparador):
    if comparador not in ATRIBUTOS:
        raise ValueError("Comparador desconhecido.")
    return p["x_v11"] if comparador == "v11" else p["x"]


def ajustar(pp, ys, cat, comparador):
    if not pp or set(pp) != set(ys):
        raise ValueError("Treino vazio ou rótulos de outro conjunto.")
    cont = Counter(p["hash"] for p in pp.values())
    xx, yy, ww = [], [], []
    for i, p in pp.items():
        xx.extend(matriz(p, comparador))
        yy.extend(int(f.aceito(t, ys[i], cat.temas)) for t in cat.familias)
        ww.extend([1 / cont[p["hash"]]] * len(cat.familias))
    # Mesmo estimador, regularização, balanceamento e peso por texto.
    return ajustar_linear_eficiente(xx, yy, ww, True)


def mesmo_ramo(t, u, temas):
    return t in f.pais(u, temas) or u in f.pais(t, temas)


def sinais(pp, mod, cat, variante):
    if variante not in VARIANTES:
        raise ValueError("Variante desconhecida.")
    comparador = COMPARADOR[variante]
    out = []
    for i, p in pp.items():
        ks = p["candidatos"]
        if not ks or len(ks) != len(set(ks)) or len(ks) > TOP_K:
            raise ValueError("Lista de candidatos inválida.")
        es = a.escore_linear(matriz(p, comparador), mod)
        # Empates preservam a ordem da recuperação, nunca a ordem dos IDs.
        k = ks[0] if variante == "primeiro_fusao_v15" else max(ks, key=lambda j: float(es[j]))
        t = cat.familias[k]
        hom = any(
            abs(float(p["sinal_textual"][k] - p["sinal_textual"][cat.familias.index(u)])) <= 1e-6
            and abs(float(es[k] - es[cat.familias.index(u)])) < .25
            for u in p["homonimos"][t]
        )
        # A guarda é a mesma em todas as variantes e reaproveita a V15.
        sem = bool(p["rota"]["sem_evidencia"])
        pouco = bool(max(p["x"][k, :4]) < .03)
        motivos = [n for n, ativo in [
            ("sem_evidencia", sem), ("pouco_sinal_textual", pouco),
            ("homonimo_sem_escopo_resolvido", hom),
        ] if ativo]
        out.append({
            "id": i, "tema_central_id": t, "sinal": float(es[k]),
            "elegivel": not motivos, "homonimo_nao_resolvido": bool(hom),
            "motivos_bloqueio": ";".join(motivos),
            "primeiro_recuperado": cat.familias[ks[0]],
            "posicao_escolhida": ks.index(k) + 1,
            "candidatos_ids": ";".join(cat.familias[j] for j in ks),
            "variante": variante,
        })
    return out


def aplicar(pp, pacote, cat, variante):
    comparador = COMPARADOR[variante]
    if pacote["atributos"] != ATRIBUTOS[comparador]:
        raise ValueError("Atributos incompatíveis com o comparador.")
    ss = sinais(pp, pacote["modelo"], cat, variante)
    cs = a.confiancas(ss, pacote["calibrador"])
    rr = []
    for r, c in zip(ss, cs):
        decisao = f.decidir(r, float(c), pacote["politica"])
        motivo = ""
        if decisao == "revisar":
            motivo = r["motivos_bloqueio"] or (
                "sem_politica_com_suporte" if not pacote["politica"]["ativa"]
                else "abaixo_do_limiar_calibrado"
            )
        rr.append({**r, "confianca": float(c), "decisao": decisao, "motivo": motivo})
    return rr


def pacote(pp, ys, cat, variante, internas, mod=None):
    comparador = COMPARADOR[variante]
    cal = a.calibrar(internas)
    return {
        "atributos": ATRIBUTOS[comparador],
        "modelo": mod if mod is not None else ajustar(pp, ys, cat, comparador),
        "calibrador": cal,
        "politica": a.politica(internas, a.confiancas(internas, cal)),
    }


def escolher_internamente(pacotes, internas):
    # Rótulos do fold externo nunca participam desta escolha.
    return max(VARIANTES, key=lambda v: (
        pacotes[v]["politica"]["suporte_interno"],
        sum(int(r["correto"]) for r in internas[v]),
        -VARIANTES.index(v),
    ))
