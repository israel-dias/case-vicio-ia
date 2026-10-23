"""Classificador congelado de tópicos: nenhuma leitura de rótulos na inferência.

Os artefatos guardam catálogo, escopos, pesos, corte e duas probabilidades
aprendidas na calibração. Não guardam uma tabela questão -> decisão.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path

import calibrar_etapa2 as cal

VERSAO = "runtime_seletivo_catalogo_v1"
CAMPOS_ENTREGA = ["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"]
ARQUIVOS_DADOS = ("temas.csv", "escopos.json", "vocabulario_autorado.tsv")


def codigos_runtime():
    caminhos = [Path(__file__), Path(__file__).with_name("classificar_etapa2.py"),
                Path(cal.__file__), Path(cal.esc.__file__), Path(cal.autoria.__file__), Path(cal.base.__file__)]
    return {p.name: cal.base.sha256(p) for p in caminhos}


def politica_minima(politica):
    campos = ("versao", "protocolo", "ativa", "limiar_margem", "escolha", "confianca_por_decisao")
    return {k: politica[k] for k in campos}


def conferir_parametros(metodo, politica):
    esperado = next(c for c in cal.esc.CONFIGURACOES if c["nome"] == cal.esc.METODO_ESCOLHIDO)
    if metodo != esperado or politica.get("versao") != cal.VERSAO or politica.get("protocolo") != cal.PROTOCOLO:
        raise ValueError("Configuração/protocolo não corresponde ao classificador congelado.")
    if not isinstance(politica.get("ativa"), bool):
        raise ValueError("Estado de política inválido.")
    if politica["ativa"]:
        corte = cal.numero(politica["limiar_margem"], "limiar")
        escolha = politica["escolha"]
        if not 0 < corte <= 1 or not isinstance(escolha, dict) or escolha.get("limiar_margem") != corte:
            raise ValueError("Corte de publicação não corresponde à escolha registrada.")
        for prefixo, minimo in (("dev", 5), ("cal", 3)):
            c, n = escolha[f"{prefixo}_acertos"], escolha[f"{prefixo}_publicadas"]
            cal.validar_contagens(c, n)
            if n < minimo or c / n < cal.PROTOCOLO["meta_empirica"]:
                raise ValueError("O corte não possui o suporte empírico registrado.")
    elif politica.get("limiar_margem") is not None or politica.get("escolha") is not None:
        raise ValueError("Política desativada com corte/escolha preenchidos.")
    totais = 0
    for decisao in ("publicar", "revisar"):
        s = politica["confianca_por_decisao"][decisao]
        esperado_s = cal.estatistica(s["acertos"], s["avaliadas"])
        if s != esperado_s:
            raise ValueError("Confiança diverge das contagens e da suavização registradas.")
        totais += s["avaliadas"]
    if totais != 20:
        raise ValueError("Confianças devem vir das 20 questões de calibração.")


def preparar_artefatos(temas_path, escopos_path, vocabulario_path, metodo, politica, metodo_path, politica_path, destino):
    if destino.exists():
        raise ValueError("Pasta de artefatos já existe; preserve a versão anterior.")
    conferir_parametros(metodo["configuracao"], politica)
    destino.mkdir(parents=True)
    fontes = dict(zip(ARQUIVOS_DADOS, (temas_path, escopos_path, vocabulario_path)))
    for nome, fonte in fontes.items():
        shutil.copyfile(fonte, destino / nome)
    modelo = {"versao": VERSAO, "configuracao": metodo["configuracao"],
              "politica": politica_minima(politica), "sha256_codigo": codigos_runtime(),
              "sha256_dados": {n: cal.base.sha256(destino / n) for n in ARQUIVOS_DADOS},
              "origem": {"sha256_metodo_congelado": cal.base.sha256(metodo_path),
                         "sha256_politica_congelada": cal.base.sha256(politica_path),
                         "aprendizado": "Pesos escolhidos no desenvolvimento; corte e confiança na calibração; teste não altera parâmetros.",
                         "escopos": "Propostos pelo assistente e versionados; sem validação jurídica independente.",
                         "classificacao": "TF-IDF, similaridade, árvore e regra de abstenção; nenhuma chamada a LLM.",
                         "ids_de_questoes_como_atributo": False,
                         "rotulos_ou_respostas_por_questao_no_modelo": False}}
    cal.escrever_json(destino / "modelo.json", modelo)
    return modelo


class Runtime:
    def __init__(self, pasta):
        self.pasta = Path(pasta)
        self.registro = cal.ler_json(self.pasta / "modelo.json")
        if self.registro.get("versao") != VERSAO:
            raise ValueError("Versão de artefato de inferência desconhecida.")
        if self.registro.get("sha256_codigo") != codigos_runtime():
            raise ValueError("Código diferente do registrado no artefato de inferência.")
        registrados = self.registro.get("sha256_dados")
        if (not isinstance(registrados, dict) or set(registrados) != set(ARQUIVOS_DADOS)
                or registrados != {n: cal.base.sha256(self.pasta / n) for n in ARQUIVOS_DADOS}):
            raise ValueError("Catálogo, escopos ou vocabulário diferem dos artefatos de inferência.")
        self.politica = self.registro["politica"]
        conferir_parametros(self.registro["configuracao"], self.politica)
        self.temas = cal.base.ler_temas(self.pasta / "temas.csv")
        self.propostas = cal.esc.carregar_propostas(self.temas, self.pasta / "temas.csv",
                                                   self.pasta / "escopos.json", self.pasta / "vocabulario_autorado.tsv")["temas"]
        self.modelo = cal.esc.ClassificadorEscopos(self.temas, self.propostas, self.registro["configuracao"])

    def classificar(self, questao):
        qid = questao.get("id")
        if not isinstance(qid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", qid):
            raise ValueError("ID ausente ou inválido para a saída; ele não é atributo de classificação.")
        texto = cal.base.texto_completo(questao)
        if not texto.strip():
            raise ValueError(f"{qid}: questão sem conteúdo textual recuperável; tratar na importação.")
        sinais = cal.evidencias(questao, self.modelo, self.propostas)
        if not sinais["tema_previsto"]:
            raise ValueError(f"{qid}: nenhum candidato recuperado; exige triagem de importação, sem inventar tema ou marcar fora.")
        decisao = cal.aplicar_politica(sinais, self.politica)
        tid = sinais["tema_previsto"]
        linha = {"id": qid, "decisao": decisao["decisao"], "tema_central_id": tid,
                 "extras_ids": "", "confianca": f"{decisao['confianca']:.8f}", "motivo": decisao["motivo"]}
        registro = {"id": qid, **sinais, "caminho_sugerido": self.temas[tid]["caminho"],
                    "decisao": decisao["decisao"], "confianca": decisao["confianca"],
                    "sha256_texto_normalizado": hashlib.sha256(texto.encode()).hexdigest(),
                    "extras": "Não inferidos automaticamente a partir do top5."}
        return linha, registro


def ler_questoes(caminho):
    questoes, vistos = [], set()
    with Path(caminho).open(encoding="utf-8-sig") as arquivo:
        for numero_linha, linha in enumerate(arquivo, 1):
            if not linha.strip():
                continue
            q = json.loads(linha)
            if not isinstance(q, dict) or not isinstance(q.get("id"), str):
                raise ValueError(f"Linha {numero_linha}: objeto/id inválido.")
            if q["id"] in vistos:
                raise ValueError(f"ID repetido: {q['id']}")
            vistos.add(q["id"]); questoes.append(q)
    if not questoes:
        raise ValueError("Arquivo de questões vazio.")
    return questoes


def validar_entrega(linhas, temas, ids_esperados):
    if len(linhas) != len(ids_esperados) or {r["id"] for r in linhas} != set(ids_esperados):
        raise ValueError("Entrega não cobre cada ID exatamente uma vez.")
    for r in linhas:
        if list(r) != CAMPOS_ENTREGA or r["decisao"] not in {"publicar", "revisar", "fora"}:
            raise ValueError("Colunas ou decisão fora do contrato do CSV.")
        confianca = cal.numero(float(r["confianca"]), "confiança")
        if not 0 <= confianca <= 1:
            raise ValueError("Confiança fora de 0 a 1.")
        if r["decisao"] == "fora":
            if r["tema_central_id"] or r["extras_ids"]:
                raise ValueError("Fora não pode carregar tema.")
        elif not r["tema_central_id"]:
            raise ValueError("Publicar/revisar exige sugestão de tema central.")
        for tid in [r["tema_central_id"]] + r["extras_ids"].split(";"):
            if tid and (tid not in temas or not temas[tid]["ativo"] or temas[tid]["nivel"] == 0
                        or not all(temas[z]["ativo"] for z in cal.base.ancestrais(tid, temas))):
                raise ValueError("Tema ausente, inativo ou raiz na entrega.")
        if r["decisao"] in {"revisar", "fora"} and not r["motivo"].strip():
            raise ValueError("Revisar/fora exige motivo.")


def executar(artefatos, questoes_path, saida):
    inicio = time.perf_counter()
    if saida.exists():
        raise ValueError("Saída já existe; use uma pasta nova para preservar os resultados.")
    entradas_hash = cal.base.sha256(questoes_path)
    runtime = Runtime(artefatos)
    questoes = ler_questoes(questoes_path)
    preparado = time.perf_counter()
    linhas, registros = [], []
    for q in sorted(questoes, key=lambda x: x["id"]):
        linha, registro = runtime.classificar(q)
        linhas.append(linha); registros.append(registro)
    classificado = time.perf_counter()
    validar_entrega(linhas, runtime.temas, [q["id"] for q in questoes])
    contagens = Counter(r["decisao"] for r in linhas)
    resumo = {"versao": VERSAO, "questoes": len(linhas),
              "decisoes": {k: contagens[k] for k in ("publicar", "revisar", "fora")},
              "cobertura_total": contagens["publicar"] / len(linhas),
              "precisao_real": None, "rotulos_consultados_na_inferencia": False,
              "chamadas_a_llm": 0, "custo_api_classificacao_usd": 0,
              "tempos_segundos": {"leitura_e_preparacao": preparado - inicio,
                                   "classificacao": classificado - preparado},
              "ambiente": {"python": platform.python_version(), "sistema": platform.system(), "arquitetura": platform.machine()}}
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".classificacao-", dir=saida.parent))
    try:
        cal.salvar_csv(temporaria / "publicacao.csv", linhas, CAMPOS_ENTREGA)
        with (temporaria / "rastreabilidade.jsonl").open("w", encoding="utf-8") as arquivo:
            for r in registros:
                arquivo.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n")
        resumo["tempos_segundos"]["total_ate_gravacao"] = time.perf_counter() - inicio
        cal.escrever_json(temporaria / "resumo_classificacao.json", resumo)
        if cal.base.sha256(questoes_path) != entradas_hash:
            raise ValueError("Questões alteradas durante a classificação.")
        manifesto = {"versao": VERSAO, "sha256_questoes": entradas_hash,
                     "sha256_modelo": cal.base.sha256(Path(artefatos) / "modelo.json"),
                     "sha256_codigo": codigos_runtime(), "rotulos_usados": False,
                     "sha256_artefatos": {p.name: cal.base.sha256(p) for p in sorted(temporaria.iterdir())}}
        cal.escrever_json(temporaria / "manifesto_classificacao.json", manifesto)
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    return resumo
