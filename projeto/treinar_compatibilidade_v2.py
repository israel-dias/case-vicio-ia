"""Treino final nos 100 rótulos; sem uso dos 559 para escolher parâmetros."""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import shutil
import tempfile
import time
from pathlib import Path

import calibrar_etapa2 as cal
from compatibilidade_v2 import runtime as rt
from compatibilidade_v2 import features as f


def conferir_experimento(pasta, dados, rotulos, temas):
    manifesto = json.loads((pasta/"manifesto.json").read_text())
    for nome, h in manifesto.items():
        p = (pasta/nome).resolve()
        if not p.is_relative_to(pasta.resolve()) or rt.sha(p) != h:
            raise ValueError("Experimento alterado ou caminho inválido: "+nome)
    protocolo = json.loads((pasta/"protocolo_previo.json").read_text())
    for nome, h in protocolo["dados_sha256"].items():
        if rt.sha(dados/nome) != h:
            raise ValueError("Anexos diferentes dos usados na validação cruzada.")
    raiz = Path(__file__).parent
    for nome, h in protocolo["codigo_sha256"].items():
        if rt.sha(raiz/"experimento_folha_v2"/nome) != h:
            raise ValueError("Código do experimento diferente do registrado.")
    if rt.sha(raiz/"experimento_folha_v2/com_escopos_existentes.py") != protocolo["origem_preparada"]["adaptador_sha256"]:
        raise ValueError("Adaptador do experimento diferente do registrado.")
    if rt.sha(raiz/"compatibilidade_v2/features.py") != protocolo["codigo_sha256"]["modelo.py"]:
        raise ValueError("Atributos de produção diferem do protótipo avaliado.")
    folds = json.loads((pasta/"auditoria_folds.json").read_text())
    por_fold = {a["fold"]: a for a in folds}
    holdouts = [qid for a in folds for qid in a["avaliacao_ids"]]
    if len(holdouts) != 100 or set(holdouts) != set(rotulos):
        raise ValueError("Folds não cobrem os 100 IDs uma única vez.")
    for a in folds:
        treino, val = set(a["treino_ids"]), set(a["avaliacao_ids"])
        if treino & val or treino | val != set(rotulos):
            raise ValueError("Sobreposição ou omissão nos folds.")
        for interno in a["folds_internos"]:
            if (set(interno["treino_ids"]) | set(interno["validacao_ids"])) != treino or set(interno["treino_ids"]) & set(interno["validacao_ids"]):
                raise ValueError("Fold interno incompatível com o treino externo.")
    with (pasta/"previsoes_compatibilidade_fixa.csv").open(encoding="utf-8", newline="") as arq:
        originais = list(csv.DictReader(arq))
    if len(originais) != 100 or {r["id"] for r in originais} != set(rotulos):
        raise ValueError("Previsões OOF incompletas ou repetidas.")
    linhas = []
    for original in originais:
        r = dict(original)
        r["sinal"] = cal.numero(float(r["sinal"]), "sinal OOF")
        if not 0 <= r["sinal"] <= 1 or r["elegivel"] not in {"True", "False"}:
            raise ValueError("Sinal ou elegibilidade OOF inválidos.")
        r["elegivel"] = r["elegivel"] == "True"
        r["correto"] = int(r["correto"])
        fold = por_fold[int(r["fold"])]
        if r["id"] not in fold["avaliacao_ids"] or r["correto"] != int(f.aceito(r["tema_central_id"], rotulos[r["id"]], temas)):
            raise ValueError("Previsão OOF incompatível com referência ou fold.")
        prob = f.confiancas([r], fold["calibradores"]["compatibilidade_fixa"])[0]
        if abs(prob-float(r["confianca"])) > 1e-12 or f.decidir(r, prob, fold["politicas"]["compatibilidade_fixa"]) != r["decisao"]:
            raise ValueError("Previsão OOF não corresponde à política registrada antes do holdout.")
        linhas.append(r)
    return linhas, protocolo


def executar(dados, experimento, saida):
    if saida.exists():
        raise ValueError("Artefato final já existe; use outra pasta.")
    inicio = time.perf_counter()
    raiz = Path(__file__).parent
    metodo_path = raiz/"experimentos/escopos_001/metodo_congelado.json"
    escopos_path = raiz/"artefatos/escopos_v1/escopos.json"
    vocab_path = raiz/"artefatos/escopos_v1/vocabulario_autorado.tsv"
    protocolo_final = json.loads((raiz/"protocolo_final_v2.json").read_text())
    if protocolo_final["metodo"] != "compatibilidade_fixa":
        raise ValueError("Método final diferente do protocolo.")
    metodo, questoes, ys, temas, propostas = cal.conferir_congelamento(dados, metodo_path, escopos_path, vocab_path)
    oof, protocolo_cv = conferir_experimento(experimento, dados, ys, temas)
    # Todo ajuste supervisionado recebe exclusivamente as 100 questões rotuladas.
    catalogo = rt.CatalogoCompatibilidade(temas, propostas, metodo["configuracao"])
    perfis = catalogo.transformar({qid: questoes[qid] for qid in sorted(ys)})
    with f.threadpool_limits(limits=2):
        compat = f.ajustar(perfis, ys, catalogo.familias, temas)
        calibrador = f.calibrador(oof)
        probs = f.confiancas(oof, calibrador)
        politica = f.escolher_politica(oof, probs)
    registro = {"versao": rt.VERSAO, "metodo": "compatibilidade_fixa",
        "configuracao_escopos": metodo["configuracao"], "nomes_atributos": f.NOMES_BASE,
        "familias": catalogo.familias, "compatibilidade": compat, "calibrador": calibrador,
        "politica": politica, "score_minimo": .03, "codigo_sha256": rt.codigos_runtime(),
        "dependencias": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "scikit-learn", "threadpoolctl")},
        "origem": {"rotulos_de_treino": len(ys), "sinais_de_calibracao": "OOF de desenvolvimento, 100 itens",
            "escolha_da_variante": "Após olhar os resultados de desenvolvimento; não é teste independente.",
            "modelo_referencia_sha256": rt.sha(metodo_path), "protocolo_final_sha256": rt.sha(raiz/"protocolo_final_v2.json"),
            "protocolo_cv_sha256": rt.sha(experimento/"protocolo_previo.json"),
            "previsoes_oof_sha256": rt.sha(experimento/"previsoes_compatibilidade_fixa.csv"),
            "llm_na_decisao": False, "ids_questoes_como_atributo": False,
            "tabela_de_respostas_por_questao": False, "sem_rotulo_usados_no_ajuste": 0}}
    rt.validar_parametros(registro)
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".modelo-v2-", dir=saida.parent))
    try:
        for nome, p in zip(rt.DADOS_MODELO, (dados/"temas.csv", escopos_path, vocab_path)):
            shutil.copyfile(p, tmp/nome)
        rt.escrever(tmp/"modelo.json", registro)
        rt.escrever(tmp/"manifesto_modelo.json", {"versao": rt.VERSAO,
            "arquivos_sha256": {p.name: rt.sha(p) for p in sorted(tmp.iterdir())}})
        rt.Runtime(tmp)
        tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    resumo = {"treinadas": 100, "sem_rotulo_usadas_no_ajuste": 0, "politica_final": politica,
        "confiança_media_selecionadas_oof": sum(p for r,p in zip(oof, probs) if f.decidir(r,p,politica)=="publicar")/politica["suporte_interno"] if politica["ativa"] else None,
        "segundos": time.perf_counter()-inicio,
        "nota": "Corte final ajustado nos 100 sinais OOF: métrica descritiva de desenvolvimento, distinta do resultado externo 20/20 da política por fold."}
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    p.add_argument("--experimento", type=Path, default=Path("experimentos/folha_v2_escopos_001"))
    p.add_argument("--saida", type=Path, default=Path("artefatos/compatibilidade_v2"))
    args = p.parse_args()
    try:
        resumo = executar(args.dados, args.experimento, args.saida)
    except (OSError, ValueError, KeyError) as exc:
        p.exit(1, f"Erro: {exc}\n")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
