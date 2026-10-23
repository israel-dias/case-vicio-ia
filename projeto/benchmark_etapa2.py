"""Mede carga repetindo textos reais; não é avaliação de 50 mil questões únicas."""
import argparse
import json
import platform
import time
from collections import Counter
from pathlib import Path

from runtime_etapa2 import Runtime, ler_questoes, cal


def medir(artefatos, questoes_path, volume, saida, tarifa_usd_hora=.05):
    if saida.exists():
        raise ValueError("Arquivo de benchmark já existe; preserve a medição anterior.")
    if isinstance(volume, bool) or not isinstance(volume, int) or volume < 1:
        raise ValueError("Volume precisa ser inteiro positivo.")
    tarifa_usd_hora = cal.numero(tarifa_usd_hora, "tarifa")
    if tarifa_usd_hora < 0:
        raise ValueError("Tarifa negativa.")
    inicio = time.perf_counter()
    runtime = Runtime(artefatos); questoes = ler_questoes(questoes_path)
    pronto = time.perf_counter(); decisoes = Counter()
    for i in range(volume):
        linha, _ = runtime.classificar(questoes[i % len(questoes)])
        decisoes[linha["decisao"]] += 1
    fim = time.perf_counter()
    try:
        import resource
        pico_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if platform.system() == "Linux" else None
    except ImportError:
        pico_kib = None
    resultado = {"tipo": "carga repetida; sem avaliação de acerto", "textos_unicos": len(questoes),
                 "predicoes": volume, "preparacao_segundos": pronto - inicio,
                 "classificacao_segundos": fim - pronto, "total_segundos": fim - inicio,
                 "questoes_por_segundo": volume / (fim - pronto), "pico_rss_kib_linux": pico_kib,
                 "cenario_tarifa_usd_hora": tarifa_usd_hora,
                 "custo_compute_cenario_usd": (fim - inicio) / 3600 * tarifa_usd_hora,
                 "custo_compute_cenario_por_questao_usd": (fim - inicio) / 3600 * tarifa_usd_hora / volume,
                 "custo_api_classificacao_usd": 0, "decisoes_na_carga_repetida": dict(decisoes),
                 "sha256_modelo": cal.base.sha256(Path(artefatos) / "modelo.json"),
                 "sha256_questoes": cal.base.sha256(questoes_path),
                 "ambiente": {"python": platform.python_version(), "sistema": platform.system(), "arquitetura": platform.machine()},
                 "limites": ["Tarifa é hipótese ilustrativa, não cotação de provedor.",
                             "Sem escrita de CSV durante a carga; inclui a classificação, validação e criação do registro por item.",
                             "Repetições medem desempenho, não generalização ou qualidade em 50 mil questões novas.",
                             "Não inclui revisão humana, armazenamento, monitoramento, energia ou preparação histórica de artefatos."]}
    saida.parent.mkdir(parents=True, exist_ok=True)
    cal.escrever_json(saida, resultado)
    return resultado


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artefatos", type=Path, default=Path("entrega_etapa2/modelo"))
    p.add_argument("--questoes", type=Path, default=Path("dados/anexos/questoes.jsonl"))
    p.add_argument("--volume", type=int, default=50000)
    p.add_argument("--tarifa-usd-hora", type=float, default=.05)
    p.add_argument("--saida", type=Path, default=Path("experimentos/carga_50000.json"))
    a = p.parse_args()
    try:
        r = medir(a.artefatos, a.questoes, a.volume, a.saida, a.tarifa_usd_hora)
    except (ValueError, OSError, KeyError, TypeError) as e:
        p.exit(2, f"Erro: {e}\n")
    print(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
