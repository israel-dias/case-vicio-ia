"""Valida a árvore sem fundir temas ou inventar equivalências."""
from collections import defaultdict
from .preparacao import normalizar_nome


def validar_temas(temas: list[dict]) -> dict[str, dict]:
    campos = {"tema_id", "parent_id", "disciplina", "nivel", "titulo", "caminho", "descricao", "status"}
    indice = {}
    for tema in temas:
        if not campos <= tema.keys() or any(not isinstance(tema[c], str) for c in campos):
            raise ValueError("Tema com campos ausentes ou inválidos.")
        identificador = tema["tema_id"]
        if not identificador or identificador in indice:
            raise ValueError(f"ID de tema vazio ou duplicado: {identificador!r}")
        if tema["status"] not in {"active", "inactive"} or tema["nivel"] not in {"0", "1", "2"}:
            raise ValueError(f"{identificador}: status ou nível inválido.")
        if not tema["titulo"].strip() or not tema["caminho"].strip():
            raise ValueError(f"{identificador}: título ou caminho ausente.")
        indice[identificador] = tema
    for tema in temas:
        atual, visitados = tema, set()
        while atual:
            if atual["tema_id"] in visitados:
                raise ValueError(f"Ciclo na árvore a partir de {tema['tema_id']}.")
            visitados.add(atual["tema_id"])
            pai = atual["parent_id"]
            if pai and pai not in indice:
                raise ValueError(f"{atual['tema_id']}: pai inexistente {pai}.")
            atual = indice.get(pai)
        pai = indice.get(tema["parent_id"])
        if (tema["nivel"] == "0") != (pai is None):
            raise ValueError(f"{tema['tema_id']}: raiz incompatível com o nível.")
        if pai:
            if int(tema["nivel"]) != int(pai["nivel"]) + 1:
                raise ValueError(f"{tema['tema_id']}: nível incompatível com o pai.")
            if tema["disciplina"] != pai["disciplina"]:
                raise ValueError(f"{tema['tema_id']}: disciplina diferente da do pai.")
            if tema["status"] == "active" and pai["status"] == "inactive":
                raise ValueError(f"{tema['tema_id']}: tema ativo sob pai inativo; requer decisão.")
    return indice


def titulos_repetidos(temas: list[dict]) -> list[list[dict]]:
    grupos = defaultdict(list)
    for tema in temas:
        grupos[normalizar_nome(tema["titulo"])].append(tema)
    return [grupo for grupo in grupos.values() if len(grupo) > 1]


def mesmo_ramo(a: str, b: str, indice: dict[str, dict]) -> bool:
    """Ancestral/descendente ou mesmo nó. Irmãos não são equivalentes."""
    def ancestrais(identificador):
        encontrados = set()
        while identificador:
            encontrados.add(identificador)
            identificador = indice[identificador]["parent_id"]
        return encontrados
    if a not in indice or b not in indice:
        raise ValueError("Tema inexistente na comparação.")
    return a in ancestrais(b) or b in ancestrais(a)
