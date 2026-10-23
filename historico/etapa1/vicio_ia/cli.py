"""Execução local; sem chamadas pagas ou credenciais."""
import argparse
import json
from pathlib import Path
from . import __version__
from .arquivos import gravar_json, gravar_jsonl, ler_csv, ler_jsonl, sha256
from .diagnostico import diagnosticar, markdown_diagnostico
from .importacao import importar
from .lotes import gerar_lotes
from .preparacao import normalizar_nome, preparar_questoes
from .temas import validar_temas


def preparar(originais: Path, saida: Path, quantidade: int) -> dict:
    if (saida.resolve() == originais.resolve()
            or saida.resolve() in originais.resolve().parents
            or originais.resolve() in saida.resolve().parents):
        raise ValueError("A saída deve ficar separada dos dados originais.")
    entradas = ["questoes.jsonl", "temas.csv", "LEIA-ME.md", "entrega_modelo.csv"]
    hashes_entrada = {n: sha256(originais / n) for n in entradas}
    temas = ler_csv(originais / "temas.csv")
    validar_temas(temas)
    questoes = ler_jsonl(originais / "questoes.jsonl")
    preparados = preparar_questoes(questoes, {normalizar_nome(t["disciplina"]) for t in temas})
    if len(preparados) != quantidade or {q["id"] for q in preparados} != {
            f"Q{i:04}" for i in range(1, quantidade + 1)}:
        raise ValueError(f"Esperadas {quantidade} questões com IDs consecutivos Q0001 em diante.")
    ativos = [t for t in temas if t["status"] == "active"]
    diagnostico = diagnosticar(questoes, preparados, temas)
    saida.mkdir(parents=True, exist_ok=True)
    gravar_jsonl(saida / "questoes_preparadas.jsonl", preparados)
    gravar_json(saida / "temas_ativos.json", ativos)
    gravar_json(saida / "diagnostico.json", diagnostico)
    (saida / "diagnostico.md").write_text(markdown_diagnostico(diagnostico), encoding="utf-8")
    gravar_json(saida / "manifesto.json", {
        "versao_pipeline": __version__, "entradas_sha256": hashes_entrada,
        "saidas_sha256": {n: sha256(saida / n) for n in
                         ("questoes_preparadas.jsonl", "temas_ativos.json",
                          "diagnostico.json", "diagnostico.md")},
        "questoes": len(preparados), "temas_ativos": len(ativos), "publicacao_final": False,
    })
    return {"questoes_preparadas": len(preparados), "temas_ativos": len(ativos),
            "destino": str(saida), "classificacoes_realizadas": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="Case Vício IA — preparação e análise assistida")
    parser.add_argument("--version", action="version", version=__version__)
    comandos = parser.add_subparsers(dest="comando", required=True)
    p = comandos.add_parser("preparar", help="Limpar e validar os anexos originais")
    p.add_argument("--originais", type=Path, default=Path("dados/originais"))
    p.add_argument("--saida", type=Path, default=Path("dados/processados"))
    p.add_argument("--quantidade", type=int, default=359)
    l = comandos.add_parser("lotes", help="Gerar prompt e arquivos de cada lote")
    l.add_argument("--processados", type=Path, default=Path("dados/processados"))
    l.add_argument("--saida", type=Path, default=Path("lotes"))
    l.add_argument("--tamanho", type=int, default=10)
    l.add_argument("--piloto", type=int, default=20)
    l.add_argument("--seed", type=int, default=42)
    i = comandos.add_parser("importar", help="Registrar uma resposta real do chat")
    i.add_argument("--lote", type=Path, required=True)
    i.add_argument("--resposta", type=Path, required=True)
    i.add_argument("--saida", type=Path, required=True)
    i.add_argument("--modelo", required=True)
    i.add_argument("--nota", default="")
    args = parser.parse_args()
    try:
        if args.comando == "preparar":
            resultado = preparar(args.originais, args.saida, args.quantidade)
        elif args.comando == "lotes":
            resultado = gerar_lotes(args.processados, args.saida, args.tamanho, args.piloto, args.seed)
        else:
            resultado = importar(args.lote, args.resposta, args.saida, args.modelo, args.nota)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0
