"""Simulação parametrizada de produção; sem conexão, modelo ou cobrança."""
import argparse
import json
from pathlib import Path


def simular(projeto, volume=50000, minutos_revisao=1, custo_hora_professor=None):
    if volume < 1 or minutos_revisao < 0 or (custo_hora_professor is not None and custo_hora_professor < 0):
        raise ValueError("Parâmetros de volume/tempo/custo inválidos.")
    taxas = json.loads((projeto / "docs/CUSTOS_PRODUCAO.json").read_text(encoding="utf-8"))
    unitario = lambda p: (p["entrada_por_questao_assumida"] * p["usd_por_milhao_entrada"]
                          + p["saida_faturada_por_questao_assumida"] * p["usd_por_milhao_saida"]) / 1e6
    p, s = taxas["primeira_passagem"], taxas["segunda_passagem"]
    custo_1 = volume * unitario(p)
    custo_2 = volume * s["fracao_assumida"] * unitario(s)
    resumo = json.loads((projeto / "resumo_entrega.json").read_text(encoding="utf-8"))
    fracao_revisao = resumo["decisoes"]["revisar"] / resumo["questoes"]
    horas = volume * fracao_revisao * minutos_revisao / 60
    return {"tipo": "simulacao_nao_executada", "volume": volume,
            "custo_primeira_passagem_usd": round(custo_1, 4),
            "custo_segunda_passagem_usd": round(custo_2, 4),
            "custo_llm_total_usd": round(custo_1 + custo_2, 4),
            "custo_llm_por_questao_usd": round((custo_1 + custo_2) / volume, 8),
            "taxa_de_revisao_do_case_usada_como_cenario": fracao_revisao,
            "horas_humanas_se_a_taxa_do_case_se_repetir": round(horas, 2),
            "minutos_por_revisao_assumidos": minutos_revisao,
            "custo_humano_usd": None if custo_hora_professor is None else round(horas * custo_hora_professor, 2),
            "tokens_reais_do_chat_medidos": None, "api_executada_no_case_usd": 0,
            "limites": taxas["observacao"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--volume", type=int, default=50000)
    p.add_argument("--minutos-revisao", type=float, default=1)
    p.add_argument("--custo-hora-professor", type=float)
    a = p.parse_args()
    print(json.dumps(simular(Path.cwd(), a.volume, a.minutos_revisao, a.custo_hora_professor),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
