"""Importa respostas reais do chat e preserva sua proveniência."""
import math
from datetime import datetime, timezone
from pathlib import Path
from .arquivos import carregar_json, gravar_json, sha256


def validar_resposta(valor, ids: list[str], temas_ativos: set[str]) -> list[dict]:
    if not isinstance(valor, dict) or set(valor) != {"classificacoes"}:
        raise ValueError("Resposta deve conter somente o objeto classificacoes.")
    registros = valor["classificacoes"]
    if not isinstance(registros, list):
        raise ValueError("classificacoes deve ser uma lista.")
    campos = {"id", "sugestao_decisao", "tema_central_id", "extras_ids",
              "confianca_modelo", "justificativa", "temas_concorrentes_ids", "alertas"}
    vistos = set()
    for r in registros:
        if not isinstance(r, dict) or set(r) != campos:
            raise ValueError("Classificação com campos ausentes ou adicionais.")
        if not isinstance(r["id"], str) or r["id"] not in ids or r["id"] in vistos:
            raise ValueError("ID ausente do lote, inválido ou duplicado.")
        vistos.add(r["id"])
        decisao = r["sugestao_decisao"]
        if not isinstance(decisao, str) or decisao not in {"publicar", "revisar", "fora"}:
            raise ValueError(f"{r['id']}: sugestão inválida.")
        if not isinstance(r["justificativa"], str) or not r["justificativa"].strip():
            raise ValueError(f"{r['id']}: justificativa obrigatória.")
        for campo in ("extras_ids", "temas_concorrentes_ids", "alertas"):
            valores = r[campo]
            if not isinstance(valores, list) or any(not isinstance(v, str) for v in valores):
                raise ValueError(f"{r['id']}: {campo} deve ser lista de textos.")
            if len(valores) != len(set(valores)):
                raise ValueError(f"{r['id']}: valores duplicados em {campo}.")
        for identificador in r["extras_ids"] + r["temas_concorrentes_ids"]:
            if identificador not in temas_ativos:
                raise ValueError(f"{r['id']}: tema inexistente ou inativo {identificador}.")
        central, confianca = r["tema_central_id"], r["confianca_modelo"]
        if decisao == "fora":
            if central is not None or r["extras_ids"] or confianca is not None:
                raise ValueError(f"{r['id']}: fora exige central/confiança null e extras vazios.")
        else:
            if not isinstance(central, str) or central not in temas_ativos:
                raise ValueError(f"{r['id']}: central deve ser ID ativo.")
            if central in r["extras_ids"]:
                raise ValueError(f"{r['id']}: tema central repetido nos extras.")
            if isinstance(confianca, bool) or not isinstance(confianca, (int, float)):
                raise ValueError(f"{r['id']}: confiança deve ser numérica.")
            if not math.isfinite(confianca) or not 0 <= confianca <= 1:
                raise ValueError(f"{r['id']}: confiança fora do intervalo 0 a 1.")
    if vistos != set(ids):
        raise ValueError(f"Questões omitidas: {', '.join(sorted(set(ids) - vistos))}")
    return sorted(registros, key=lambda r: r["id"])


def importar(lote: Path, resposta: Path, destino: Path, modelo: str, nota: str) -> dict:
    if not modelo.strip():
        raise ValueError("Informe o modelo exibido ou declare explicitamente não identificado.")
    manifesto = carregar_json((lote / "manifesto.json").read_text(encoding="utf-8"))
    for nome, campo in (("prompt.txt", "sha256_prompt"), ("questoes.json", "sha256_questoes"),
                        ("temas_ativos.json", "sha256_temas")):
        if sha256(lote / nome) != manifesto[campo]:
            raise ValueError(f"{nome} mudou após a geração. Crie nova versão do lote.")
    temas = carregar_json((lote / "temas_ativos.json").read_text(encoding="utf-8"))
    ativos = {t["tema_id"] for t in temas if t["status"] == "active"}
    registros = validar_resposta(carregar_json(resposta.read_text(encoding="utf-8-sig")),
                                manifesto["ids"], ativos)
    if destino.exists() and any(destino.iterdir()):
        raise ValueError("Destino de importação não está vazio. Use pasta de execução nova.")
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "resposta_original.json").write_bytes(resposta.read_bytes())
    (destino / "prompt.txt").write_bytes((lote / "prompt.txt").read_bytes())
    gravar_json(destino / "classificacoes_validadas.json", {"classificacoes": registros})
    registro = {
        "origem": "chat_assistido", "modelo_informado": modelo, "nota_operador": nota,
        "importado_em_utc": datetime.now(timezone.utc).isoformat(),
        "manifesto_lote": manifesto, "sha256_resposta_original": sha256(resposta),
        "custo_api_executado_usd": 0, "tokens_api_medidos": None,
        "observacao_custo": "Importação da assinatura existente. Não mede tokens internos "
                           "nem custo da assinatura.",
        "publicacao_final": False,
    }
    gravar_json(destino / "registro_execucao.json", registro)
    return {"importadas": len(registros), "destino": str(destino),
            "aviso": "Formato validado. Acerto jurídico e publicação ainda não avaliados."}
