"""Importa ou verifica as 34 respostas reais salvas; nenhuma chamada de IA."""
import argparse
import json
from pathlib import Path
from vicio_ia.arquivos import carregar_json, sha256
from vicio_ia.importacao import importar, validar_resposta

MODELO = "Assistente nesta conversa; identificador não confirmado"
NOTA = ("Conversa existente com contexto prévio; regras v3, leitura de todas as questões "
        "e inspeção dirigida do catálogo e referências pontuais. Prompt é referência, "
        "não transcrição de todo o contexto. Confiança não calibrada; sem API paga.")


def conferir_execucao(destino, lote, resposta):
    registro = carregar_json((destino / "registro_execucao.json").read_text(encoding="utf-8"))
    manifesto = carregar_json((lote / "manifesto.json").read_text(encoding="utf-8"))
    if (registro["manifesto_lote"] != manifesto
            or registro["sha256_resposta_original"] != sha256(resposta)
            or sha256(destino / "resposta_original.json") != sha256(resposta)
            or sha256(destino / "prompt.txt") != manifesto["sha256_prompt"]):
        raise ValueError(f"Execução existente difere dos arquivos: {destino}")
    temas = carregar_json((lote / "temas_ativos.json").read_text(encoding="utf-8"))
    esperado = validar_resposta(carregar_json(resposta.read_text(encoding="utf-8-sig")),
                               manifesto["ids"], {t["tema_id"] for t in temas if t["status"] == "active"})
    atual = carregar_json((destino / "classificacoes_validadas.json").read_text(encoding="utf-8"))
    if atual != {"classificacoes": esperado}:
        raise ValueError(f"Registros validados alterados: {destino}")


def executar(projeto):
    tarefas = []
    vistos = set()
    for numero in range(1, 35):
        nome = f"lote_{numero:03}"
        lote = projeto / "lotes_v3" / nome
        resposta = projeto / "respostas_v3" / f"{nome}.json"
        destino = projeto / "execucoes/v3" / nome
        m = carregar_json((lote / "manifesto.json").read_text(encoding="utf-8"))
        for arquivo, campo in (("prompt.txt", "sha256_prompt"), ("questoes.json", "sha256_questoes"),
                               ("temas_ativos.json", "sha256_temas")):
            if sha256(lote / arquivo) != m[campo]:
                raise ValueError(f"Entrada alterada: {nome}/{arquivo}")
        temas = carregar_json((lote / "temas_ativos.json").read_text(encoding="utf-8"))
        validar_resposta(carregar_json(resposta.read_text(encoding="utf-8-sig")), m["ids"],
                        {t["tema_id"] for t in temas if t["status"] == "active"})
        if vistos & set(m["ids"]):
            raise ValueError("Questões repetidas entre lotes.")
        vistos.update(m["ids"])
        existente = destino.exists() and any(destino.iterdir())
        if existente:
            conferir_execucao(destino, lote, resposta)
        tarefas.append((lote, resposta, destino, existente))
    piloto = carregar_json((projeto / "lotes_v1/piloto/manifesto.json").read_text(encoding="utf-8"))["ids"]
    if len(vistos) != 339 or vistos & set(piloto) or vistos | set(piloto) != {f"Q{i:04}" for i in range(1, 360)}:
        raise ValueError("Cobertura dos lotes e do piloto inválida.")
    novas = 0
    for lote, resposta, destino, existente in tarefas:
        if not existente:
            importar(lote, resposta, destino, MODELO, NOTA)
            novas += 1
    return {"lotes_verificados": len(tarefas), "novas_importacoes": novas,
            "questoes_v3": len(vistos), "questoes_piloto": len(piloto),
            "aviso": "Integridade validada; acerto jurídico não medido."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path.cwd())
    a = p.parse_args()
    try:
        print(json.dumps(executar(a.projeto), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        p.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
