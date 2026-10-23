"""Formata anotações REAIS do assistente; não executa IA nem faz nova classificação."""
import argparse
import json
from pathlib import Path
from vicio_ia.arquivos import carregar_json, gravar_json
from vicio_ia.importacao import validar_resposta

# Formato compacto: id, decisão, tema central, confiança, justificativa,
# extras (opcional), concorrentes (opcional), alertas (opcional).
# Ausentes: listas vazias para extras/concorrentes; alerta de candidatura
# ou encaminhamento assistido conforme a decisão já registrada.


def gerar(projeto, saida):
    anotacoes = projeto / "evidencias_assistente"
    registros = [carregar_json(l) for l in (anotacoes / "anotacoes_assistente.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    for linha in (anotacoes / "anotacoes_compactas_assistente.jsonl").read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        x = carregar_json(linha)
        registros.append({"id": x[0], "sugestao_decisao": x[1], "tema_central_id": x[2],
                          "confianca_modelo": x[3], "justificativa": x[4],
                          "extras_ids": x[5] if len(x) > 5 else [],
                          "temas_concorrentes_ids": x[6] if len(x) > 6 else [],
                          "alertas": x[7] if len(x) > 7 else [
                              "candidata_sujeita_a_auditoria" if x[1] == "publicar"
                              else "encaminhamento_assistido_sem_gabarito"]})
    if len(registros) != 329 or len({r["id"] for r in registros}) != 329:
        raise ValueError("Esperadas 329 anotações únicas, excluindo piloto e primeiro lote.")
    indice = {r["id"]: r for r in registros}
    lotes = projeto / "lotes_v3"
    tarefas = []
    for numero in range(2, 35):
        nome = f"lote_{numero:03}"
        pasta = lotes / nome
        manifesto = carregar_json((pasta / "manifesto.json").read_text(encoding="utf-8"))
        temas = carregar_json((pasta / "temas_ativos.json").read_text(encoding="utf-8"))
        ativos = {t["tema_id"] for t in temas if t["status"] == "active"}
        resposta = {"classificacoes": [indice[i] for i in manifesto["ids"]]}
        validar_resposta(resposta, manifesto["ids"], ativos)
        destino = saida / f"{nome}.json"
        if destino.exists():
            raise ValueError(f"Resposta já existe: {destino}. Escolha pasta nova.")
        tarefas.append((destino, resposta))
    usados = {r["id"] for _, p in tarefas for r in p["classificacoes"]}
    if usados != set(indice):
        raise ValueError("Anotações não correspondem aos lotes restantes.")
    saida.mkdir(parents=True, exist_ok=True)
    for destino, resposta in tarefas:
        gravar_json(destino, resposta)
    return {"respostas_formatadas": len(tarefas), "questoes": len(usados),
            "chamadas_api": 0, "nova_inferencia_realizada": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path.cwd())
    p.add_argument("--saida", type=Path, default=Path("respostas_v3_regeneradas"))
    a = p.parse_args()
    print(json.dumps(gerar(a.projeto, a.saida), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
