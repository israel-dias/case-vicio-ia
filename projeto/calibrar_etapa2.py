"""Aprende uma política de abstenção sem alterar o classificador congelado.

Biblioteca padrão. Desenvolvimento propõe limiares; calibração escolhe um.
Não faz previsões no teste reservado nem nas 559 questões sem rótulo.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import tempfile
import time
from pathlib import Path

import experimento_campos as base
import experimento_escopos as esc
import gerar_escopos as autoria

VERSAO = "calibracao_seletiva_v1"
PROTOCOLO = {
    "qualidade": "(score_top1 - score_top2) / score_top1; zero sem sinal",
    "score_minimo": 0.05,
    "exigir_escopo_proposto": True,
    "meta_empirica": 0.95,
    "minimo_publicadas_desenvolvimento": 5,
    "minimo_publicadas_calibracao": 3,
    "limiares_candidatos": "margens observadas somente no desenvolvimento",
    "desempate": "mais publicações na calibração, mais suporte no desenvolvimento, limiar maior",
    "sem_candidato": "desativar publicação automática; todas seguem para revisão",
    "fora_automatico": False,
    "confianca": "média Beta(1 + acertos, 1 + erros), separada para publicar e revisar, usando só calibração",
    "intervalo": "Clopper-Pearson bilateral 95%; descritivo após seleção, sem garantia pós-seleção",
}


def ler_json(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8-sig"))


def escrever_json(caminho, objeto):
    Path(caminho).write_text(json.dumps(objeto, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")


def numero(valor, nome):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise ValueError(f"{nome} precisa ser um número finito, não booleano.")
    return float(valor)


def validar_contagens(acertos, total):
    if (isinstance(total, bool) or isinstance(acertos, bool)
            or not isinstance(total, int) or not isinstance(acertos, int)
            or not 0 <= acertos <= total):
        raise ValueError("Contagens binomiais inválidas.")


def soma_binomial(inicio, fim, n, p):
    if p == 0:
        return float(inicio == 0)
    if p == 1:
        return float(fim == n)
    return math.fsum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1)
                             - math.lgamma(n - i + 1) + i * math.log(p)
                             + (n - i) * math.log1p(-p))
                     for i in range(inicio, fim + 1))


def limite_inferior(acertos, total, alfa):
    if acertos == 0:
        return 0.
    inferior, superior = 0., 1.
    for _ in range(80):
        p = (inferior + superior) / 2
        if soma_binomial(acertos, total, total, p) < alfa:
            inferior = p
        else:
            superior = p
    return (inferior + superior) / 2


def intervalo_exato(acertos, total, nivel=.95):
    """Intervalo binomial; com zero observações, a proporção não foi medida."""
    validar_contagens(acertos, total)
    nivel = numero(nivel, "nível")
    if not 0 < nivel < 1:
        raise ValueError("Nível precisa estar entre zero e um.")
    if total == 0:
        return [0., 1.]
    alfa = 1 - nivel
    return [limite_inferior(acertos, total, alfa / 2),
            1 - limite_inferior(total - acertos, total, alfa / 2)]


def estatistica(acertos, total):
    validar_contagens(acertos, total)
    return {"acertos": acertos, "avaliadas": total,
            "precisao_empirica": acertos / total if total else None,
            "intervalo_exato_95_descritivo": intervalo_exato(acertos, total),
            "limite_inferior_unilateral_95_descritivo": limite_inferior(acertos, total, .05) if total else 0.,
            "media_beta_1_1": (acertos + 1) / (total + 2)}


def conferir_congelamento(dados, metodo_path, escopos_path, vocabulario_path):
    """Valida a cadeia de preparação; não cria previsões nem altera a divisão."""
    metodo = ler_json(metodo_path)
    cfg = next(c for c in esc.CONFIGURACOES if c["nome"] == esc.METODO_ESCOLHIDO)
    if (metodo.get("versao") != "metodo_catalogo_v1"
            or metodo.get("metodo") != esc.METODO_ESCOLHIDO
            or metodo.get("configuracao") != cfg):
        raise ValueError("Método/configuração diferente do método congelado de escopos.")
    codigos = {Path(p).name: Path(p) for p in (esc.__file__, autoria.__file__, base.__file__)}
    if metodo.get("sha256_codigo") != {n: base.sha256(p) for n, p in codigos.items()}:
        raise ValueError("Código do classificador mudou após o congelamento.")
    arquivos = {n: dados / n for n in ("questoes.jsonl", "temas.csv", "folha_verdade.csv")}
    if metodo.get("sha256_entradas") != {n: base.sha256(p) for n, p in arquivos.items()}:
        raise ValueError("Os anexos diferem dos usados para congelar o método.")
    for campo, caminho in (("sha256_escopos", escopos_path), ("sha256_vocabulario", vocabulario_path)):
        if metodo.get(campo) != base.sha256(caminho):
            raise ValueError("Escopos/vocabulário mudaram após o congelamento.")
    manifesto_original = ler_json(metodo_path.parent / "manifesto_inicial.json")
    base.verificar_hashes_anteriores(manifesto_original, arquivos)
    particao = base.localizar_particao(manifesto_original)
    if {k: sorted(v) for k, v in particao.items()} != {k: sorted(v) for k, v in metodo["particao"].items()}:
        raise ValueError("A divisão não corresponde ao manifesto original; não refaça a partição.")
    if {k: len(v) for k, v in particao.items()} != {
            "desenvolvimento": 60, "calibracao_reservada": 20, "teste_reservado": 20}:
        raise ValueError("Esperada a divisão original 60/20/20.")
    lista = base.ler_csv(arquivos["folha_verdade.csv"])
    rotulos = {r["id"]: r for r in lista}
    if len(lista) != 100 or len(rotulos) != 100:
        raise ValueError("Esperados 100 rótulos únicos.")
    base.validar_particao(particao, rotulos, [{"id": qid} for qid in particao["desenvolvimento"]])
    questoes = {}
    for linha in arquivos["questoes.jsonl"].read_text(encoding="utf-8-sig").splitlines():
        if not linha.strip():
            continue
        q = json.loads(linha)
        if q["id"] in questoes:
            raise ValueError("Questão repetida.")
        questoes[q["id"]] = q
    if set(questoes) != {f"Q{i:04d}" for i in range(1, 660)}:
        raise ValueError("Esperadas 659 questões, Q0001 a Q0659.")
    temas = base.ler_temas(arquivos["temas.csv"])
    propostas = esc.carregar_propostas(temas, arquivos["temas.csv"], escopos_path, vocabulario_path)
    for rotulo in rotulos.values():
        fora = rotulo["fora_da_taxonomia"]
        referencias = base.referencias(rotulo)
        if fora not in {"0", "1"} or (fora == "1" and referencias) or (fora == "0" and not rotulo["tema_central_id"]):
            raise ValueError("Rótulo oficial malformado.")
        for tid in referencias:
            if (tid not in temas or not temas[tid]["ativo"] or temas[tid]["nivel"] == 0
                    or not all(temas[p]["ativo"] for p in base.ancestrais(tid, temas))):
                raise ValueError("Referência oficial ausente, inativa ou raiz.")
    conferir_duplicatas(questoes, particao)
    return metodo, questoes, rotulos, temas, propostas["temas"]


def conferir_duplicatas(questoes, particao):
    grupos_por_hash = {}
    for grupo, ids in particao.items():
        for qid in ids:
            resumo = hashlib.sha256(base.texto_completo(questoes[qid]).encode()).hexdigest()
            if resumo in grupos_por_hash and grupos_por_hash[resumo] != grupo:
                raise ValueError("Duplicata textual entre grupos; preserve a divisão e registre a contaminação antes de avaliar.")
            grupos_por_hash[resumo] = grupo


def evidencias(questao, modelo, propostas):
    """Não recebe rótulo: as evidências são iguais para uma questão nova."""
    ranking = modelo.ranquear(questao)
    if not ranking:
        return {"tema_previsto": "", "score_top1": 0., "score_top2": 0.,
                "segundo_tema_id": "", "margem_relativa": 0., "escopo_proposto": False}
    tid, primeiro = ranking[0]
    segundo_id, segundo = ranking[1] if len(ranking) > 1 else ("", 0.)
    primeiro, segundo = numero(primeiro, "score_top1"), numero(segundo, "score_top2")
    if not 0 <= segundo <= primeiro <= 1 + 1e-12:
        raise ValueError("Ranking inválido para calcular a margem.")
    return {"tema_previsto": tid, "score_top1": primeiro, "score_top2": segundo,
            "segundo_tema_id": segundo_id,
            "margem_relativa": (primeiro - segundo) / primeiro if primeiro else 0.,
            "escopo_proposto": bool(propostas[tid]["descricao_proposta"].strip())}


def avaliar_ids(modelo, ids, questoes, rotulos_grupo, temas, propostas):
    if set(ids) != set(rotulos_grupo):
        raise ValueError("A avaliação deve receber somente os rótulos do grupo solicitado.")
    linhas = []
    for qid in sorted(ids):
        sinais = evidencias(questoes[qid], modelo, propostas)
        tid = sinais["tema_previsto"]
        linhas.append({"id": qid, **sinais, "caminho_previsto": temas[tid]["caminho"] if tid else "",
                       "acerto_top1": base.aceito(tid, rotulos_grupo[qid], temas),
                       "fora_referencia": rotulos_grupo[qid]["fora_da_taxonomia"] == "1"})
    return linhas


def elegivel(linha, limiar):
    margem = numero(linha["margem_relativa"], "margem")
    score = numero(linha["score_top1"], "score_top1")
    if not 0 <= margem <= 1 or not 0 <= score <= 1 + 1e-12:
        raise ValueError("Margem/score fora da faixa.")
    return bool(linha["tema_previsto"] and linha["escopo_proposto"]
                and score >= PROTOCOLO["score_minimo"] and margem > 0
                and margem >= limiar)


def contagem_publicadas(linhas, limiar):
    selecionadas = [r for r in linhas if elegivel(r, limiar)]
    return sum(r["acerto_top1"] for r in selecionadas), len(selecionadas)


def propor_limiares(desenvolvimento):
    limiares = sorted({r["margem_relativa"] for r in desenvolvimento if elegivel(r, 0.)}, reverse=True)
    candidatos = []
    for limiar in limiares:
        c, n = contagem_publicadas(desenvolvimento, limiar)
        if n >= PROTOCOLO["minimo_publicadas_desenvolvimento"] and c / n >= PROTOCOLO["meta_empirica"]:
            candidatos.append({"limiar_margem": limiar, "dev_acertos": c,
                               "dev_publicadas": n, "dev_precisao": c / n})
    return candidatos


def selecionar_limiar(candidatos, calibracao):
    avaliados = []
    for candidato in candidatos:
        c, n = contagem_publicadas(calibracao, candidato["limiar_margem"])
        avaliados.append({**candidato, "cal_acertos": c, "cal_publicadas": n,
                          "cal_precisao": c / n if n else None,
                          "admissivel": n >= PROTOCOLO["minimo_publicadas_calibracao"]
                          and c / n >= PROTOCOLO["meta_empirica"]})
    admissiveis = [c for c in avaliados if c["admissivel"]]
    escolhido = max(admissiveis, key=lambda c: (c["cal_publicadas"], c["dev_publicadas"], c["limiar_margem"])) if admissiveis else None
    return escolhido, avaliados


def construir_politica(desenvolvimento, calibracao):
    escolhido, candidatos = selecionar_limiar(propor_limiares(desenvolvimento), calibracao)
    corte = escolhido["limiar_margem"] if escolhido else None
    selecionadas = [r for r in calibracao if corte is not None and elegivel(r, corte)]
    restantes = [r for r in calibracao if corte is None or not elegivel(r, corte)]
    return {"versao": VERSAO, "protocolo": dict(PROTOCOLO), "ativa": escolhido is not None,
            "limiar_margem": corte, "escolha": escolhido,
            "confianca_por_decisao": {
                "publicar": estatistica(sum(r["acerto_top1"] for r in selecionadas), len(selecionadas)),
                "revisar": estatistica(sum(r["acerto_top1"] for r in restantes), len(restantes))},
            "leitura": "Limiar selecionado com dados da calibração; precisão nela é descritiva e otimista. Teste ainda não executado.",
            "fora": "Desativado: similaridade baixa não prova ausência de tema. Possíveis fora seguem para revisão."}, candidatos


def aplicar_politica(sinais, politica):
    """Não lê ID, gabarito, acerto ou qualquer rótulo para decidir."""
    if politica.get("versao") != VERSAO or politica.get("protocolo") != PROTOCOLO:
        raise ValueError("Versão/protocolo de política incompatível.")
    ativa = politica["ativa"]
    corte = politica["limiar_margem"]
    if not isinstance(ativa, bool) or (ativa and not 0 <= numero(corte, "limiar") <= 1) or (not ativa and corte is not None):
        raise ValueError("Estado/limiar de política inválido.")
    publicar = ativa and elegivel(sinais, corte)
    decisao = "publicar" if publicar else "revisar"
    confianca = politica["confianca_por_decisao"][decisao]["media_beta_1_1"]
    if not 0 < numero(confianca, "confiança") < 1:
        raise ValueError("Confiança suavizada inválida.")
    if publicar:
        motivo = f"Ramo com maior suporte e margem relativa {sinais['margem_relativa']:.3f} >= {corte:.3f}; política selecionada na calibração."
    elif not ativa:
        motivo = "Publicação desativada: nenhum limiar obteve suporte mínimo e meta empírica na calibração; conferir sugestão."
    elif not sinais["tema_previsto"]:
        motivo = "Sem candidato com sinal lexical; requer enquadramento por especialista."
    elif not sinais["escopo_proposto"]:
        motivo = "Recorte do tema sem descrição proposta; confirmar escopo antes de publicar."
    elif sinais["score_top1"] < PROTOCOLO["score_minimo"]:
        motivo = "Pouca evidência textual no catálogo; confirmar conhecimento cobrado e tema."
    else:
        motivo = f"Margem relativa {sinais['margem_relativa']:.3f} < {corte:.3f}; dúvida entre ramos candidatos."
    return {"decisao": decisao, "confianca": confianca, "motivo": motivo}


def salvar_csv(caminho, linhas, campos=None):
    if campos is None:
        campos = list(linhas[0])
    with Path(caminho).open("w", encoding="utf-8", newline="") as arquivo:
        w = csv.DictWriter(arquivo, fieldnames=campos)
        w.writeheader(); w.writerows(linhas)


def executar(dados, metodo_path, escopos_path, vocabulario_path, saida):
    inicio = time.perf_counter()
    if saida.exists():
        raise ValueError("Saída já existe; use outra pasta. A calibração anterior será preservada.")
    metodo, questoes, rotulos, temas, propostas = conferir_congelamento(dados, metodo_path, escopos_path, vocabulario_path)
    modelo = esc.ClassificadorEscopos(temas, propostas, metodo["configuracao"])
    grupos = {}
    for grupo in ("desenvolvimento", "calibracao_reservada"):
        ids = metodo["particao"][grupo]
        grupos[grupo] = avaliar_ids(modelo, ids, questoes, {qid: rotulos[qid] for qid in ids}, temas, propostas)
    dev, cal = grupos["desenvolvimento"], grupos["calibracao_reservada"]
    medido_dev = sum(r["acerto_top1"] for r in dev)
    if medido_dev != metodo["metricas_desenvolvimento"]["acertos_top1"]:
        raise ValueError("O método não reproduziu os acertos de desenvolvimento registrados.")
    politica, candidatos = construir_politica(dev, cal)
    hashes_codigo = {Path(p).name: base.sha256(Path(p)) for p in (__file__, esc.__file__, autoria.__file__, base.__file__)}
    politica.update({"sha256_metodo_congelado": base.sha256(metodo_path),
                     "metodo": metodo["metodo"], "configuracao": metodo["configuracao"],
                     "sha256_codigo": hashes_codigo, "sha256_entradas": metodo["sha256_entradas"],
                     "sha256_escopos": metodo["sha256_escopos"],
                     "sha256_vocabulario": metodo["sha256_vocabulario"], "particao": metodo["particao"],
                     "teste_reservado_avaliado": False})
    saidas = {g: [{**r, **aplicar_politica(r, politica)} for r in linhas] for g, linhas in grupos.items()}
    pubs = politica["confianca_por_decisao"]["publicar"]
    resumo = {"etapa": VERSAO, "metodo_preservado": metodo["metodo"],
              "desenvolvimento": {"questoes": len(dev), "acertos_top1": medido_dev},
              "calibracao": {"questoes": len(cal), "acertos_top1": sum(r["acerto_top1"] for r in cal),
                             "publicar": pubs["avaliadas"], "revisar": len(cal) - pubs["avaliadas"], "fora": 0,
                             "acertos_publicadas": pubs["acertos"], "precisao_publicadas_empirica": pubs["precisao_empirica"],
                             "cobertura": pubs["avaliadas"] / len(cal),
                             "confianca_suavizada_grupo_publicar": pubs["media_beta_1_1"],
                             "intervalo_95_descritivo_publicadas": pubs["intervalo_exato_95_descritivo"]},
              "politica_ativa": politica["ativa"], "limiar_margem_relativa": politica["limiar_margem"],
              "limiares_candidatos_do_desenvolvimento": len(candidatos),
              "teste_reservado": {"questoes": 20, "previsoes_geradas": False},
              "questoes_sem_rotulo": {"questoes": 559, "previsoes_geradas": False},
              "tempo_execucao_segundos": round(time.perf_counter() - inicio, 3),
              "observacoes": [
                  "Método de classificação fixo; limiar selecionado nos 20 itens de calibração.",
                  "Meta de 95% é empírica nos subconjuntos selecionados; não é garantia estatística.",
                  "Intervalo da calibração é descritivo após seleção; não é avaliação independente.",
                  "Confiança é estimativa de acerto com suavização Beta(1,1), não similaridade e não 100%.",
                  "Não se marca fora automaticamente; possíveis ausências da taxonomia seguem para revisão.",
                  "Os 100 rótulos foram vistos anteriormente na conversa; as reservas não são teste externo cego.",
                  "Os 300 itens recentes não têm rótulos disponíveis; sua qualidade ainda não foi medida.",
                  "O próximo passo é avaliar uma vez o teste reservado, sem alterar esta política depois de ver o resultado.",
              ]}
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".calibracao-", dir=saida.parent))
    try:
        escrever_json(temporaria / "politica_congelada.json", politica)
        escrever_json(temporaria / "resumo.json", resumo)
        salvar_csv(temporaria / "desenvolvimento.csv", saidas["desenvolvimento"])
        salvar_csv(temporaria / "calibracao.csv", saidas["calibracao_reservada"])
        campos = ["limiar_margem", "dev_acertos", "dev_publicadas", "dev_precisao", "cal_acertos", "cal_publicadas", "cal_precisao", "admissivel"]
        salvar_csv(temporaria / "candidatos_limiar.csv", candidatos, campos)
        leitura = ("# Calibração da publicação\n\n"
                   "O classificador de temas permaneceu fixo. O desenvolvimento propôs limiares de margem relativa; "
                   "a calibração escolheu o de maior cobertura que atingiu a meta empírica de 95%, com pelo menos "
                   "5 publicações no desenvolvimento e 3 na calibração. Esses mínimos evitam selecionar com um único "
                   "exemplo; não certificam precisão populacional.\n\n"
                   f"Política ativa: **{politica['ativa']}**. Limiar: **{politica['limiar_margem']}**. "
                   f"Na calibração: **{pubs['acertos']}/{pubs['avaliadas']}** publicadas certas; "
                   f"cobertura **{pubs['avaliadas'] / len(cal):.1%}**. Precisão indefinida quando não há publicadas.\n\n"
                   f"Confiança média suavizada do grupo publicar: **{pubs['media_beta_1_1']:.4f}**. "
                   f"Intervalo binomial descritivo 95%: **{pubs['intervalo_exato_95_descritivo']}**. "
                   "Ambos usam apenas os resultados da calibração. Ela também escolheu o limiar: há otimismo de seleção. "
                   "A confirmação seguinte será no teste reservado.\n\n"
                   "Se nenhum limiar cumprir os critérios, a política se abstém de publicar. Baixa similaridade não "
                   "prova que a questão está fora da árvore: a versão atual envia esses casos à revisão. Não há descarte automático.\n\n"
                   "Nenhuma previsão foi feita nas 20 questões de teste nem nas 559 sem rótulo. Não ajuste a representação "
                   "ou a regra usando o resultado do teste sem registrar que ele deixou de ser reservado.\n\n"
                   "Intervalos: NIST, https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm . "
                   "As hipóteses binomiais não resolvem mudança de distribuição ou exposição anterior aos rótulos.\n")
        (temporaria / "LEITURA.md").write_text(leitura, encoding="utf-8")
        manifesto = {"versao": VERSAO, "sha256_metodo": base.sha256(metodo_path), "sha256_codigo": hashes_codigo,
                     "protocolo": PROTOCOLO,
                     "ids_com_previsoes": {g: sorted(metodo["particao"][g]) for g in grupos},
                     "teste_sem_previsoes": True, "sem_rotulos_sem_previsoes": True,
                     "sha256_artefatos": {p.name: base.sha256(p) for p in sorted(temporaria.iterdir())}}
        escrever_json(temporaria / "manifesto.json", manifesto)
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    return resumo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    parser.add_argument("--metodo", type=Path, default=Path("experimentos/escopos_001/metodo_congelado.json"))
    parser.add_argument("--escopos", type=Path, default=Path("artefatos/escopos_v1/escopos.json"))
    parser.add_argument("--vocabulario", type=Path, default=Path("artefatos/escopos_v1/vocabulario_autorado.tsv"))
    parser.add_argument("--saida", type=Path, default=Path("experimentos/calibracao_001"))
    args = parser.parse_args()
    try:
        resumo = executar(args.dados, args.metodo, args.escopos, args.vocabulario, args.saida)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        parser.exit(2, f"Erro: {erro}\n")
    print(json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"Política registrada: {args.saida / 'politica_congelada.json'}")


if __name__ == "__main__":
    main()
