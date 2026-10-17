"""Reproduz a entrega a partir de respostas salvas e ajustes assistidos explícitos."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from importar_todos_v3 import conferir_execucao
from vicio_ia.arquivos import carregar_json, gravar_json, ler_csv, sha256
from vicio_ia.importacao import validar_resposta
from vicio_ia.temas import validar_temas

COLUNAS = ["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"]
SAIDAS = ["publicacao.csv", "previsao.txt", "resumo_entrega.json", "intervencoes_registradas.json"]


def carregar_entrega(projeto):
    manifest_path = projeto / "dados/processados/manifesto.json"
    manifesto = carregar_json(manifest_path.read_text(encoding="utf-8"))
    for n, h in manifesto["entradas_sha256"].items():
        if sha256(projeto / "dados/originais" / n) != h:
            raise ValueError(f"Original alterado: {n}")
    for n, h in manifesto["saidas_sha256"].items():
        if sha256(projeto / "dados/processados" / n) != h:
            raise ValueError(f"Preparação alterada: {n}")
    temas = validar_temas(ler_csv(projeto / "dados/originais/temas.csv"))
    ativos = {i for i, t in temas.items() if t["status"] == "active"}
    registros = {}
    proveniencia = {}
    fingerprints = {}
    for numero in range(1, 35):
        nome = f"lote_{numero:03}"
        lote, resposta = projeto / "lotes_v3" / nome, projeto / "respostas_v3" / f"{nome}.json"
        destino = projeto / "execucoes/v3" / nome
        m = carregar_json((lote / "manifesto.json").read_text(encoding="utf-8"))
        for n, campo in [("prompt.txt", "sha256_prompt"), ("questoes.json", "sha256_questoes"),
                          ("temas_ativos.json", "sha256_temas")]:
            if sha256(lote / n) != m[campo]:
                raise ValueError(f"Lote alterado: {nome}/{n}")
        if m["sha256_preparacao"] != sha256(manifest_path):
            raise ValueError("Lote de outra versão da preparação.")
        if sha256(lote / "temas_ativos.json") != sha256(projeto / "dados/processados/temas_ativos.json"):
            raise ValueError("Catálogo do lote diferente da preparação.")
        conferir_execucao(destino, lote, resposta)
        rs = validar_resposta(carregar_json(resposta.read_text(encoding="utf-8-sig")), m["ids"], ativos)
        for r in rs:
            if r["id"] in registros:
                raise ValueError("ID duplicado entre lotes.")
            registros[r["id"]] = r
            proveniencia[r["id"]] = f"v3/{nome}"
        fingerprints[str(resposta.relative_to(projeto))] = sha256(resposta)
    if len(registros) != 339:
        raise ValueError("Esperados 339 IDs únicos nos lotes v3.")
    piloto_path = projeto / "evidencias_assistente/consolidacao_piloto.json"
    consolidacao = carregar_json(piloto_path.read_text(encoding="utf-8"))
    manifesto_p = carregar_json((projeto / "lotes_v1/piloto/manifesto.json").read_text(encoding="utf-8"))
    v2 = {r["id"]: r for r in validar_resposta(
        carregar_json((projeto / "piloto-resposta-v2.json").read_text(encoding="utf-8-sig")),
        manifesto_p["ids"], ativos)}
    linhas_piloto = consolidacao["decisoes"]
    if len(linhas_piloto) != 20 or {x[0] for x in linhas_piloto} != set(manifesto_p["ids"]):
        raise ValueError("Consolidação do piloto incompleta ou com duplicatas.")
    intervencoes = []
    for i, d, t, c, motivo in linhas_piloto:
        if i in registros:
            raise ValueError("Piloto duplicado nos lotes finais.")
        r = {"id": i, "sugestao_decisao": d, "tema_central_id": t,
             "confianca_modelo": c, "justificativa": motivo, "extras_ids": [],
             "temas_concorrentes_ids": [], "alertas": ["consolidacao_assistida_piloto"]}
        validar_resposta({"classificacoes": [r]}, [i], ativos)
        registros[i] = r
        proveniencia[i] = "consolidacao_assistida_piloto_v1_v2"
        intervencoes.append({"id": i, "origem": consolidacao["origem"],
                            "antes_v2": v2[i], "depois": r, "motivo": motivo})
    ajustes_path = projeto / "evidencias_assistente/ajustes_finais.json"
    ajustes = carregar_json(ajustes_path.read_text(encoding="utf-8"))
    for a in ajustes["ajustes"]:
        r = registros[a["id"]]
        if r["sugestao_decisao"] != a["decisao_anterior"]:
            raise ValueError("Ajuste não corresponde à decisão original.")
        antes = dict(r)
        r = {**r, "sugestao_decisao": a["decisao"], "tema_central_id": a["tema_central_id"],
             "confianca_modelo": a["confianca"], "justificativa": a["motivo"],
             "extras_ids": [], "alertas": r["alertas"] + ["ajuste_assistido_registrado"]}
        validar_resposta({"classificacoes": [r]}, [a["id"]], ativos)
        registros[a["id"]] = r
        proveniencia[a["id"]] += "+ajuste_assistido"
        intervencoes.append({"id": a["id"], "origem": ajustes["origem"],
                            "antes": antes, "depois": r, "motivo": a["motivo"]})
    if set(registros) != {f"Q{i:04}" for i in range(1, 360)}:
        raise ValueError("A entrega precisa cobrir os 359 IDs exatamente uma vez.")
    linhas = []
    for i, r in sorted(registros.items()):
        t = r["tema_central_id"]
        if r["sugestao_decisao"] == "publicar" and temas[t]["nivel"] == "0":
            raise ValueError("A política não permite publicar numa raiz de disciplina.")
        linhas.append({"id": i, "decisao": r["sugestao_decisao"], "tema_central_id": t or "",
                       "extras_ids": ";".join(r["extras_ids"]),
                       "confianca": f"{r['confianca_modelo'] if t else 0:.2f}",
                       "motivo": r["justificativa"]})
    fingerprints["evidencias_assistente/consolidacao_piloto.json"] = sha256(piloto_path)
    fingerprints["evidencias_assistente/ajustes_finais.json"] = sha256(ajustes_path)
    return linhas, intervencoes, proveniencia, fingerprints


def gerar(projeto, saida):
    linhas, intervencoes, proveniencia, fingerprints = carregar_entrega(projeto)
    premissas_path = projeto / "docs/PREMISSAS_PREVISAO.json"
    p = carregar_json(premissas_path.read_text(encoding="utf-8"))
    fingerprints["docs/PREMISSAS_PREVISAO.json"] = sha256(premissas_path)
    contagens = {d: sum(r["decisao"] == d for r in linhas) for d in ("publicar", "revisar", "fora")}
    cobertura = contagens["publicar"] / len(linhas)
    if any((saida / n).exists() for n in SAIDAS):
        raise ValueError("Saída já contém arquivos de entrega. Escolha pasta nova para preservar versões.")
    saida.mkdir(parents=True, exist_ok=True)
    with (saida / "publicacao.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader(); w.writerows(linhas)
    intervalo = p["intervalo_sensibilidade"]
    previsao = (f"precisao_prevista: {p['precisao_prevista']:.2f}\n"
                f"precisao_intervalo: {intervalo[0]:.2f}-{intervalo[1]:.2f}\n"
                f"cobertura_prevista: {cobertura:.9f}\n"
                f"cobertura_intervalo: {cobertura:.9f}-{cobertura:.9f}\n\n"
                f"Cobertura fixa desta entrega: {contagens['publicar']}/359. Os limites iguais representam "
                "a contagem conhecida, não uma estimativa de generalização.\n"
                "A precisão de 0.96 é previsão subjetiva ex ante, não medida nem calibrada. "
                "O orçamento hipotético de erro soma 0.02 de interpretação do núcleo, 0.01 de escopo/ramo "
                "e 0.01 residual. Essas parcelas não são frequências observadas e podem se sobrepor.\n"
                "A faixa 0.85-0.99 é sensibilidade subjetiva, não intervalo de confiança estatístico; "
                "admite descumprimento da meta e não limita o risco real de erro correlacionado.\n"
                "A escolha se apoia no filtro qualitativo por conteúdo/caminho, revisão de conflitos "
                "e integridade dos registros. Não usamos a média da confiança da IA como precisão medida. "
                "Não há gabarito independente: duas respostas ou revisão pelo mesmo assistente não o substituem.\n"
                "A confiança do CSV é julgamento autodeclarado não calibrado. Em fora, 0 é convenção "
                "para ausência de tema central, não chance de a decisão fora estar correta. "
                "As premissas completas estão em docs/PREMISSAS_PREVISAO.json.\n")
    (saida / "previsao.txt").write_text(previsao, encoding="utf-8")
    resumo = {"questoes": len(linhas), "decisoes": contagens, "cobertura": cobertura,
              "precisao_prevista_subjetiva": p["precisao_prevista"], "precisao_medida": None,
              "referencia_independente": False, "modelos_usados": "ChatGPT/assistente; identificadores não confirmados",
              "custo_api_executado_usd": 0, "tokens_api_medidos": None,
              "intervencoes_assistidas_registradas": len(intervencoes),
              "origem_por_id": proveniencia, "entradas_sha256": fingerprints,
              "csv_sha256": sha256(saida / "publicacao.csv")}
    gravar_json(saida / "resumo_entrega.json", resumo)
    gravar_json(saida / "intervencoes_registradas.json", {"intervencoes": intervencoes})
    return {k: resumo[k] for k in ("questoes", "decisoes", "cobertura", "precisao_prevista_subjetiva", "precisao_medida")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path.cwd())
    p.add_argument("--saida", type=Path, default=Path("entrega_reproduzida"))
    a = p.parse_args()
    try:
        print(json.dumps(gerar(a.projeto, a.saida), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        p.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
