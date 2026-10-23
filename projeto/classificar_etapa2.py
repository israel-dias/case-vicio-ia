"""Regenera publicacao.csv ou classifica uma nova importação, sem folha-verdade."""
import argparse
import json
from pathlib import Path

from runtime_etapa2 import executar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artefatos", type=Path, default=Path("entrega_etapa2/modelo"))
    parser.add_argument("--questoes", type=Path, default=Path("dados/anexos/questoes.jsonl"))
    parser.add_argument("--saida", type=Path, default=Path("entrega_reproduzida_etapa2"))
    args = parser.parse_args()
    try:
        r = executar(args.artefatos, args.questoes, args.saida)
    except (ValueError, OSError, KeyError, TypeError) as erro:
        parser.exit(2, f"Erro: {erro}\n")
    print(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
