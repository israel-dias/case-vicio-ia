"""Recalcula o CSV a partir do JSONL e do modelo congelado, sem LLM ou rótulos."""
import argparse
import json
from pathlib import Path
from compatibilidade_v2 import runtime


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artefatos", type=Path, default=Path("artefatos/compatibilidade_v2"))
    p.add_argument("--questoes", type=Path, default=Path("dados/anexos/questoes.jsonl"))
    p.add_argument("--saida", type=Path, required=True)
    args = p.parse_args()
    try:
        r = runtime.executar(args.artefatos, args.questoes, args.saida)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        p.exit(1, f"Erro: {exc}\n")
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
