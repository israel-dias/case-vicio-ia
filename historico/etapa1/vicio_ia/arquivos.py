import csv
import hashlib
import json
from pathlib import Path


def rejeitar_constante(valor):
    raise ValueError(f"Constante JSON inválida: {valor}")


def carregar_json(texto):
    return json.loads(texto, parse_constant=rejeitar_constante)


def ler_jsonl(caminho: Path) -> list[dict]:
    registros = []
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not linha.strip():
            continue
        try:
            registro = carregar_json(linha)
        except ValueError as exc:
            raise ValueError(f"{caminho.name}, linha {numero}: {exc}") from exc
        if not isinstance(registro, dict):
            raise ValueError(f"{caminho.name}, linha {numero}: esperado objeto JSON.")
        registros.append(registro)
    return registros


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def gravar_json(caminho: Path, valor):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                       encoding="utf-8")


def gravar_jsonl(caminho: Path, registros: list[dict]):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n"
                               for r in registros), encoding="utf-8")


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()
