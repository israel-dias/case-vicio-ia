"""Gera lotes reais das 339 questões fora do piloto; não executa inferência."""
import argparse
import json
import shutil
from pathlib import Path

from vicio_ia.arquivos import carregar_json, gravar_json, ler_jsonl, sha256
from vicio_ia.temas import validar_temas


def gerar(projeto, saida, regras_path, tamanho=10):
    if tamanho < 1:
        raise ValueError("Tamanho deve ser positivo.")
    processados = projeto / "dados/processados"
    preparacao = processados / "manifesto.json"
    manifesto = carregar_json(preparacao.read_text(encoding="utf-8"))
    for nome, esperado in manifesto["saidas_sha256"].items():
        if sha256(processados / nome) != esperado:
            raise ValueError(f"Preparação alterada: {nome}")
    temas_path = processados / "temas_ativos.json"
    temas = carregar_json(temas_path.read_text(encoding="utf-8"))
    indice_temas = validar_temas(temas)
    if len(temas) != len(indice_temas) or any(t["status"] != "active" for t in temas):
        raise ValueError("Catálogo deve conter somente IDs ativos e únicos.")
    questoes = ler_jsonl(processados / "questoes_preparadas.jsonl")
    ids = [q["id"] for q in questoes]
    if len(ids) != 359 or set(ids) != {f"Q{i:04}" for i in range(1, 360)}:
        raise ValueError("Esperadas as 359 questões originais, sem omissões ou repetições.")
    piloto_pasta = projeto / "lotes_v1/piloto"
    piloto_manifesto = carregar_json((piloto_pasta / "manifesto.json").read_text(encoding="utf-8"))
    for nome, campo in [("questoes.json", "sha256_questoes"),
                        ("temas_ativos.json", "sha256_temas"), ("prompt.txt", "sha256_prompt")]:
        if sha256(piloto_pasta / nome) != piloto_manifesto[campo]:
            raise ValueError(f"Piloto de origem alterado: {nome}")
    if sha256(temas_path) != piloto_manifesto["sha256_temas"]:
        raise ValueError("Catálogo do piloto difere da preparação atual.")
    ids_piloto = piloto_manifesto["ids"]
    piloto_questoes = carregar_json((piloto_pasta / "questoes.json").read_text(encoding="utf-8"))
    if (len(ids_piloto) != 20 or len(set(ids_piloto)) != 20
            or set(ids_piloto) != {q["id"] for q in piloto_questoes}
            or not set(ids_piloto) <= set(ids)):
        raise ValueError("Piloto inválido ou diferente do conjunto original.")
    indice_questoes = {q["id"]: q for q in questoes}
    if any(q != indice_questoes[q["id"]] for q in piloto_questoes):
        raise ValueError("Conteúdo do piloto difere da preparação atual.")
    regras = regras_path.read_text(encoding="utf-8")
    if not regras.strip():
        raise ValueError("Regras vazias.")
    restantes = sorted((q for q in questoes if q["id"] not in set(ids_piloto)), key=lambda q: q["id"])
    if len(restantes) != 339:
        raise ValueError("Esperadas 339 questões restantes.")
    destino = saida.resolve()
    protegidas = (projeto / "dados/originais", processados, piloto_pasta)
    if destino == projeto.resolve() or any(
            destino == entrada.resolve() or destino in entrada.resolve().parents
            or entrada.resolve() in destino.parents for entrada in protegidas):
        raise ValueError("Escolha uma saída separada das entradas.")
    if saida.exists() and any(saida.iterdir()):
        raise ValueError("Destino já contém arquivos. Escolha nova pasta.")
    catalogo = [{k: t[k] for k in ("tema_id", "parent_id", "nivel", "titulo", "caminho")}
                for t in temas]
    descricoes = [{k: t[k] for k in ("tema_id", "caminho", "descricao")}
                  for t in temas if t["descricao"].strip()
                  and not t["descricao"].strip().startswith(("Subtema de ", "Disciplina (root)."))]
    contexto = ("\nCATÁLOGO ATIVO (JSONL):\n"
                + "\n".join(json.dumps(t, ensure_ascii=False) for t in catalogo)
                + "\n\nDESCRIÇÕES DISPONÍVEIS DIFERENTES DO PADRÃO DE IMPORTAÇÃO (JSON):\n"
                + json.dumps(descricoes, ensure_ascii=False, indent=2))
    saida.mkdir(parents=True, exist_ok=True)
    lotes = []
    for inicio in range(0, len(restantes), tamanho):
        nome = f"lote_{len(lotes)+1:03}"
        pasta = saida / nome
        pasta.mkdir()
        grupo = restantes[inicio:inicio+tamanho]
        gravar_json(pasta / "questoes.json", grupo)
        shutil.copyfile(temas_path, pasta / "temas_ativos.json")
        (pasta / "prompt.txt").write_text(regras + contexto + "\n\nQUESTÕES (JSON):\n"
                                         + json.dumps(grupo, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
        gravar_json(pasta / "manifesto.json", {
            "nome": nome, "finalidade": "classificacao_v3_pos_piloto", "versao_prompt": "v3",
            "ids": [q["id"] for q in grupo],
            "sha256_prompt": sha256(pasta / "prompt.txt"),
            "sha256_questoes": sha256(pasta / "questoes.json"),
            "sha256_temas": sha256(pasta / "temas_ativos.json"),
            "sha256_preparacao": sha256(preparacao),
            "sha256_regras": sha256(regras_path),
            "limite": "Inferência não executada. Não é avaliação nem gabarito.",
        })
        lotes.append({"nome": nome, "questoes": len(grupo), "ids": [q["id"] for q in grupo]})
    resumo = {
        "versao_prompt": "v3", "questoes_restantes": len(restantes), "lotes": len(lotes),
        "tamanho_maximo": tamanho, "ids_piloto_excluidos": sorted(ids_piloto),
        "sha256_regras": sha256(regras_path), "sha256_preparacao": sha256(preparacao),
        "classificacoes_realizadas": 0, "publicacao_final": False,
        "aviso": "As vinte questões do piloto continuam necessárias na consolidação final.",
        "indice": lotes,
    }
    gravar_json(saida / "indice.json", resumo)
    return {k: v for k, v in resumo.items() if k not in ("indice", "ids_piloto_excluidos")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path.cwd())
    p.add_argument("--saida", type=Path, default=Path("lotes_v3"))
    p.add_argument("--regras", type=Path,
                   default=Path(__file__).resolve().parent / "docs/PROMPT_V3.txt")
    p.add_argument("--tamanho", type=int, default=10)
    a = p.parse_args()
    try:
        resultado = gerar(a.projeto, a.saida, a.regras, a.tamanho)
    except (ValueError, KeyError, OSError) as exc:
        p.exit(2, f"Erro: {exc}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
