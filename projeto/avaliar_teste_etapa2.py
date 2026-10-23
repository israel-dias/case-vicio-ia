"""Avalia a política congelada nas 20 questões de teste, sem aprender com elas.

Biblioteca padrão, sem rede ou modelo de linguagem. Não classifica as 559
questões sem rótulo e não modifica método, política ou dados anteriores.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import calibrar_etapa2 as cal

VERSAO = "teste_politica_fixa_v1"
ARTEFATOS_CALIBRACAO = {
    "politica_congelada.json", "resumo.json", "desenvolvimento.csv",
    "calibracao.csv", "candidatos_limiar.csv", "LEITURA.md",
}


def validar_artefatos(pasta, manifesto, nomes):
    registrados = manifesto.get("sha256_artefatos")
    if not isinstance(registrados, dict) or set(registrados) != set(nomes):
        raise ValueError("Manifesto com arquivos ausentes, extras ou não reconhecidos.")
    for nome, esperado in registrados.items():
        if Path(nome).name != nome or not isinstance(esperado, str):
            raise ValueError("Nome/hash de artefato inválido.")
        caminho = pasta / nome
        if not caminho.is_file() or cal.base.sha256(caminho) != esperado:
            raise ValueError(f"Artefato alterado ou ausente: {nome}")


def ler_registros_calibracao(caminho, ids_esperados):
    linhas = cal.base.ler_csv(caminho)
    if len(linhas) != len(ids_esperados) or {r["id"] for r in linhas} != set(ids_esperados):
        raise ValueError("CSV de calibração/desenvolvimento não corresponde à divisão congelada.")
    for r in linhas:
        for campo in ("acerto_top1", "fora_referencia", "escopo_proposto"):
            if r[campo] not in {"True", "False"}:
                raise ValueError(f"Booleano inválido no campo {campo}.")
            r[campo] = r[campo] == "True"
        for campo in ("score_top1", "score_top2", "margem_relativa", "confianca"):
            r[campo] = cal.numero(float(r[campo]), campo)
    return linhas


def conferir_politica(politica_path, metodo_path, metodo):
    """Confere a política e seu aprendizado salvo; não usa rótulos do teste."""
    pasta = politica_path.parent
    if politica_path.name != "politica_congelada.json":
        raise ValueError("Use o arquivo politica_congelada.json gerado na calibração.")
    manifesto = cal.ler_json(pasta / "manifesto.json")
    validar_artefatos(pasta, manifesto, ARTEFATOS_CALIBRACAO)
    politica = cal.ler_json(politica_path)
    codigos = {Path(p).name: cal.base.sha256(Path(p))
               for p in (cal.__file__, cal.esc.__file__, cal.autoria.__file__, cal.base.__file__)}
    if (manifesto.get("versao") != cal.VERSAO
            or politica.get("versao") != cal.VERSAO
            or politica.get("protocolo") != cal.PROTOCOLO
            or manifesto.get("protocolo") != cal.PROTOCOLO):
        raise ValueError("Versão/protocolo diferente da calibração congelada.")
    if politica.get("sha256_codigo") != codigos or manifesto.get("sha256_codigo") != codigos:
        raise ValueError("Código da política mudou depois da calibração.")
    hash_metodo = cal.base.sha256(metodo_path)
    if politica.get("sha256_metodo_congelado") != hash_metodo or manifesto.get("sha256_metodo") != hash_metodo:
        raise ValueError("A política pertence a outro congelamento de método.")
    for campo in ("metodo", "configuracao", "sha256_entradas", "sha256_escopos", "sha256_vocabulario", "particao"):
        if politica.get(campo) != metodo.get(campo):
            raise ValueError(f"Política incompatível com o método: {campo}")
    esperados = {g: sorted(metodo["particao"][g]) for g in ("desenvolvimento", "calibracao_reservada")}
    if (manifesto.get("ids_com_previsoes") != esperados
            or manifesto.get("teste_sem_previsoes") is not True
            or manifesto.get("sem_rotulos_sem_previsoes") is not True
            or politica.get("teste_reservado_avaliado") is not False):
        raise ValueError("O registro da calibração não preserva as reservas previstas.")
    # Recalcula somente as contas sobre registros já salvos, sem novas previsões.
    dev = ler_registros_calibracao(pasta / "desenvolvimento.csv", metodo["particao"]["desenvolvimento"])
    calibracao = ler_registros_calibracao(pasta / "calibracao.csv", metodo["particao"]["calibracao_reservada"])
    reconstruida, _ = cal.construir_politica(dev, calibracao)
    for campo in reconstruida:
        if politica.get(campo) != reconstruida[campo]:
            raise ValueError(f"Política diverge dos registros de calibração: {campo}")
    for grupo, linhas in (("desenvolvimento", dev), ("calibracao_reservada", calibracao)):
        for r in linhas:
            esperado = cal.aplicar_politica(r, politica)
            if any(r[campo] != esperado[campo] for campo in ("decisao", "confianca", "motivo")):
                raise ValueError(f"Decisão salva diverge da política: {grupo}/{r['id']}")
    return politica


def resumir_teste(linhas, politica):
    """Mede o resultado de uma regra já pronta; nunca escolhe outro limiar."""
    if not linhas:
        raise ValueError("Teste vazio.")
    publicadas = [r for r in linhas if r["decisao"] == "publicar"]
    acertos = sum(r["acerto_top1"] for r in publicadas)
    estatistica = cal.estatistica(acertos, len(publicadas))
    total = len(linhas)
    grupos = defaultdict(list)
    for r in linhas:
        grupos[r["ramo_referencia"]].append(r)
    por_ramo = {}
    for ramo, registros in sorted(grupos.items()):
        pubs = [r for r in registros if r["decisao"] == "publicar"]
        por_ramo[ramo] = {"questoes": len(registros), "acertos_top1": sum(r["acerto_top1"] for r in registros),
                          "publicadas": len(pubs), "publicadas_corretas": sum(r["acerto_top1"] for r in pubs)}
    brier = math.fsum((r["confianca"] - float(r["acerto_top1"])) ** 2 for r in linhas) / total
    p = estatistica["precisao_empirica"]
    return {"questoes": total, "acertos_top1_todas": sum(r["acerto_top1"] for r in linhas),
            "acerto_top1_todas": sum(r["acerto_top1"] for r in linhas) / total,
            "publicar": len(publicadas), "revisar": sum(r["decisao"] == "revisar" for r in linhas),
            "fora": sum(r["decisao"] == "fora" for r in linhas),
            "cobertura": len(publicadas) / total, "acertos_publicadas": acertos,
            "erros_publicadas": len(publicadas) - acertos,
            "precisao_publicadas": p,
            "intervalo_binomial_95_publicadas": estatistica["intervalo_exato_95_descritivo"],
            "limite_inferior_unilateral_95": estatistica["limite_inferior_unilateral_95_descritivo"],
            "meta_95_atingida_na_amostra": p >= .95 if p is not None else None,
            "minimo_95_sustentado_por_limite_unilateral": estatistica["limite_inferior_unilateral_95_descritivo"] >= .95,
            "confianca_publicar_fixada_na_calibracao": politica["confianca_por_decisao"]["publicar"]["media_beta_1_1"],
            "brier_todas": brier, "por_ramo_referencia": por_ramo}


def executar(dados, metodo_path, politica_path, escopos_path, vocabulario_path, saida):
    inicio = time.perf_counter()
    if saida.exists():
        raise ValueError("Saída já existe; preserve a primeira avaliação. Reproduzir o mesmo teste não cria nova evidência independente.")
    metodo, questoes, rotulos, temas, propostas = cal.conferir_congelamento(dados, metodo_path, escopos_path, vocabulario_path)
    politica = conferir_politica(politica_path, metodo_path, metodo)
    hashes_codigo = {Path(p).name: cal.base.sha256(Path(p))
                     for p in (__file__, cal.__file__, cal.esc.__file__, cal.autoria.__file__, cal.base.__file__)}
    antes = {"sha256_politica": cal.base.sha256(politica_path),
             "sha256_metodo": cal.base.sha256(metodo_path), "sha256_codigo": hashes_codigo,
             "configuracao": metodo["configuracao"], "limiar_margem": politica["limiar_margem"],
             "confianca_por_decisao": politica["confianca_por_decisao"],
             "ids_teste": sorted(metodo["particao"]["teste_reservado"]),
             "procedimento": "Gerar uma avaliação fixa, sem ajuste de parâmetros depois de consultar o resultado."}
    # Preserva o registro antes de gerar a primeira previsão no teste.
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".teste-", dir=saida.parent))
    try:
        cal.escrever_json(temporaria / "congelamento_antes_teste.json", antes)
        modelo = cal.esc.ClassificadorEscopos(temas, propostas, metodo["configuracao"])
        ids = metodo["particao"]["teste_reservado"]
        linhas = cal.avaliar_ids(modelo, ids, questoes, {qid: rotulos[qid] for qid in ids}, temas, propostas)
        avaliadas = []
        for r in linhas:
            g = rotulos[r["id"]]
            avaliadas.append({**r, **cal.aplicar_politica(r, politica),
                              "central_referencia": g["tema_central_id"], "extras_referencia": g["extras_ids"],
                              "ramo_referencia": g["tema_central_caminho"].split(" > ")[0] if g["fora_da_taxonomia"] == "0" else "FORA"})
        medicao = resumir_teste(avaliadas, politica)
        resumo = {"etapa": VERSAO, "metodo": metodo["metodo"], "limiar_preservado": politica["limiar_margem"],
                  "teste": medicao, "metodo_ou_politica_alterados": False,
                  "questoes_sem_rotulo": {"questoes": 559, "previsoes_geradas": False},
                  "tempo_execucao_segundos": round(time.perf_counter() - inicio, 3),
                  "observacoes": [
                      "Regra e confiança foram verificadas e registradas antes de classificar o teste.",
                      "O teste não escolheu limiares, pesos, descrições ou exceções por ID.",
                      "Aprovação na amostra e comprovação estatística de precisão mínima são coisas distintas.",
                      "Com zero publicadas, a precisão é indefinida; não é 100%.",
                      "A confiança do CSV continua sendo a estimada na calibração, inclusive após ver o teste.",
                      "Os 100 rótulos foram vistos na conversa; não é teste externo inteiramente cego.",
                      "Todos os rótulos são de questões antigas; o teste não mede a qualidade nas 300 novas.",
                      "Repetir a mesma avaliação congelada é reprodução; não é uma nova amostra independente.",
                  ]}
        cal.salvar_csv(temporaria / "teste.csv", avaliadas)
        cal.escrever_json(temporaria / "resumo.json", resumo)
        acerto = medicao["precisao_publicadas"]
        texto_precisao = f"{acerto:.2%}" if acerto is not None else "indefinida (nenhuma publicação)"
        leitura = ("# Teste da política congelada\n\n"
                   f"Foram avaliadas **{medicao['questoes']}** questões de teste. "
                   f"O sistema publicou **{medicao['publicar']}**, com **{medicao['acertos_publicadas']}** acertos "
                   f"e **{medicao['erros_publicadas']}** erros. Precisão nas publicadas: **{texto_precisao}**. "
                   f"Cobertura: **{medicao['cobertura']:.2%}**.\n\n"
                   f"Intervalo binomial 95%: **{medicao['intervalo_binomial_95_publicadas']}**. "
                   f"O limite inferior unilateral 95% é **{medicao['limite_inferior_unilateral_95']:.4f}**. "
                   "O intervalo pressupõe observações comparáveis e independentes; não corrige a exposição anterior "
                   "aos rótulos nem a mudança para concursos novos. A quantidade de exemplos é pequena.\n\n"
                   "A representação, o limiar e as estimativas de confiança não foram alterados. "
                   "Se o resultado for insuficiente, registre a limitação. Usar este teste para escolher outro método "
                   "o transforma em desenvolvimento e exige uma nova avaliação para sustentar generalização.\n\n"
                   "Nenhuma previsão foi gerada nas 559 questões sem rótulo neste comando. O próximo passo é aplicar "
                   "a mesma regra a todas as 659 questões e preparar os arquivos de entrega, com previsão explícita "
                   "para as 559 avaliadas pela empresa.\n")
        (temporaria / "LEITURA.md").write_text(leitura, encoding="utf-8")
        if cal.base.sha256(politica_path) != antes["sha256_politica"] or cal.base.sha256(metodo_path) != antes["sha256_metodo"]:
            raise ValueError("Método ou política foram alterados durante a avaliação.")
        manifesto = {"versao": VERSAO, "sha256_politica": antes["sha256_politica"],
                     "sha256_metodo": antes["sha256_metodo"], "sha256_codigo": hashes_codigo,
                     "sha256_entradas": metodo["sha256_entradas"], "ids_com_previsoes": sorted(ids),
                     "sem_rotulos_sem_previsoes": True, "sem_ajuste_pelo_teste": True,
                     "sha256_artefatos": {p.name: cal.base.sha256(p) for p in sorted(temporaria.iterdir())}}
        cal.escrever_json(temporaria / "manifesto.json", manifesto)
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    return resumo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    parser.add_argument("--metodo", type=Path, default=Path("experimentos/escopos_001/metodo_congelado.json"))
    parser.add_argument("--politica", type=Path, default=Path("experimentos/calibracao_001/politica_congelada.json"))
    parser.add_argument("--escopos", type=Path, default=Path("artefatos/escopos_v1/escopos.json"))
    parser.add_argument("--vocabulario", type=Path, default=Path("artefatos/escopos_v1/vocabulario_autorado.tsv"))
    parser.add_argument("--saida", type=Path, default=Path("experimentos/teste_001"))
    args = parser.parse_args()
    try:
        resumo = executar(args.dados, args.metodo, args.politica, args.escopos, args.vocabulario, args.saida)
    except (ValueError, OSError, KeyError, TypeError) as erro:
        parser.exit(2, f"Erro: {erro}\n")
    print(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"Leitura: {args.saida / 'LEITURA.md'}")


if __name__ == "__main__":
    main()
