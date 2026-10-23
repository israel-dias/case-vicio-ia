"""Inferência com artefatos congelados, sem rótulos e sem LLM."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import re
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path

import runtime_etapa2 as legado
from . import features as f

cal = legado.cal
VERSAO = "runtime_compatibilidade_fixa_v2"
DADOS_MODELO = ("temas.csv", "escopos.json", "vocabulario_autorado.tsv")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def escrever(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")


def codigos_runtime():
    raiz = Path(__file__).resolve().parents[1]
    nomes = ("compatibilidade_v2/runtime.py", "compatibilidade_v2/features.py", "classificar_compatibilidade_v2.py",
             "runtime_etapa2.py", "calibrar_etapa2.py", "experimento_campos.py", "experimento_escopos.py", "gerar_escopos.py")
    return {n: sha(raiz/n) for n in nomes}


def validar_linear(mod, dimensao):
    if mod.get("dimensao") != dimensao or isinstance(mod.get("dimensao"), bool):
        raise ValueError("Dimensão do modelo incompatível com os atributos.")
    if "constante" in mod:
        p = cal.numero(mod["constante"], "probabilidade constante")
        if not 0 < p < 1:
            raise ValueError("Probabilidade constante fora de 0 a 1.")
        return
    for nome in ("media", "escala", "coeficientes"):
        valores = mod.get(nome)
        if not isinstance(valores, list) or len(valores) != dimensao:
            raise ValueError("Parâmetros do modelo incompletos.")
        for v in valores:
            cal.numero(v, nome)
    if any(v <= 0 for v in mod["escala"]):
        raise ValueError("Escala precisa ser positiva.")
    cal.numero(mod["intercepto"], "intercepto")


def validar_parametros(registro):
    if registro.get("versao") != VERSAO or registro.get("metodo") != "compatibilidade_fixa":
        raise ValueError("Versão/método do artefato incompatível.")
    if registro.get("nomes_atributos") != f.NOMES_BASE:
        raise ValueError("Atributos diferem dos usados no treinamento.")
    validar_linear(registro["compatibilidade"], len(f.NOMES_BASE))
    validar_linear(registro["calibrador"], 1)
    if "coeficientes" in registro["calibrador"] and registro["calibrador"]["coeficientes"][0] < 0:
        raise ValueError("Calibrador não monotônico.")
    politica = registro["politica"]
    if not isinstance(politica.get("ativa"), bool):
        raise ValueError("Política inválida.")
    n, c = politica["suporte_interno"], politica["acertos_internos"]
    cal.validar_contagens(c, n)
    if politica["ativa"]:
        limite = cal.numero(politica["limiar"], "limiar")
        if not 0 <= limite <= 1 or n < 10 or c/n < .95:
            raise ValueError("Corte sem o suporte empírico previsto.")
    elif politica["limiar"] is not None or n or c:
        raise ValueError("Política desativada com parâmetros preenchidos.")
    if registro.get("score_minimo") != .03:
        raise ValueError("Score mínimo diferente do protocolo de desenvolvimento.")
    cfg = next(x for x in cal.esc.CONFIGURACOES if x["nome"] == cal.esc.METODO_ESCOLHIDO)
    if registro["configuracao_escopos"] != cfg:
        raise ValueError("Configuração do classificador de escopos divergente.")


class CatalogoCompatibilidade(f.Catalogo):
    def __init__(self, temas, propostas, configuracao):
        super().__init__(temas)
        self.classificador_escopos = cal.esc.ClassificadorEscopos(temas, propostas, configuracao)

    def transformar(self, questoes):
        perfis = super().transformar(questoes)
        for qid, q in questoes.items():
            scores = self.classificador_escopos.pontuar(q)
            if not set(scores) <= set(self.familias):
                raise ValueError("Classificador de escopos retornou candidatos de outra granularidade.")
            valores = f.np.asarray([scores.get(t, 0.) for t in self.familias])
            if not f.np.isfinite(valores).all() or (valores < 0).any():
                raise ValueError("Escores inválidos.")
            perfis[qid]["scores"] = valores
            perfis[qid]["features"][:, 0] = valores
        return perfis


class Runtime:
    def __init__(self, pasta):
        self.pasta = Path(pasta)
        manifesto = json.loads((self.pasta/"manifesto_modelo.json").read_text())
        esperado = {*DADOS_MODELO, "modelo.json"}
        if set(manifesto.get("arquivos_sha256", {})) != esperado:
            raise ValueError("Manifesto do modelo incompleto.")
        for nome, h in manifesto["arquivos_sha256"].items():
            if sha(self.pasta/nome) != h:
                raise ValueError("Artefato alterado: "+nome)
        self.registro = json.loads((self.pasta/"modelo.json").read_text())
        validar_parametros(self.registro)
        if self.registro["codigo_sha256"] != codigos_runtime():
            raise ValueError("Código diferente do registrado no modelo congelado.")
        for n, v in self.registro["dependencias"].items():
            if importlib.metadata.version(n) != v:
                raise ValueError(f"Dependência {n} diferente de {v}; use requirements-v2.txt.")
        self.temas = cal.base.ler_temas(self.pasta/"temas.csv")
        props = cal.esc.carregar_propostas(self.temas, self.pasta/"temas.csv", self.pasta/"escopos.json",
                                         self.pasta/"vocabulario_autorado.tsv")["temas"]
        self.catalogo = CatalogoCompatibilidade(self.temas, props, self.registro["configuracao_escopos"])
        if self.registro["familias"] != self.catalogo.familias:
            raise ValueError("Famílias do modelo diferem do catálogo.")

    def classificar(self, questao):
        qid = questao.get("id")
        if not isinstance(qid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", qid):
            raise ValueError("ID inválido para identificar a saída.")
        perfil = self.catalogo.transformar({"registro": questao})["registro"]
        ordem = f.ordenar(perfil["scores"])
        k = int(ordem[0])
        score = float(perfil["scores"][k])
        if score <= 0:
            raise ValueError(f"{qid}: sem candidato recuperável; exige triagem de importação.")
        tid = self.catalogo.familias[k]
        bruto = float(f.predizer_linear(perfil["features"][[k]], self.registro["compatibilidade"])[0])
        prob = f.confiancas([{"sinal": bruto}], self.registro["calibrador"])[0]
        sinal = {"elegivel": score >= self.registro["score_minimo"]}
        politica = self.registro["politica"]
        decisao = f.decidir(sinal, prob, politica)
        if decisao == "publicar":
            motivo = f"Compatibilidade calibrada {prob:.3f} >= corte {politica['limiar']:.3f}; tema preservado pelo classificador de escopos."
        elif not sinal["elegivel"]:
            motivo = f"Pouca evidência textual: score {score:.3f} < mínimo {self.registro['score_minimo']:.3f}; conferir sugestão."
        elif not politica["ativa"]:
            motivo = "Nenhum corte com suporte mínimo e meta empírica; conferir sugestão."
        else:
            motivo = f"Compatibilidade calibrada {prob:.3f} < corte {politica['limiar']:.3f}; evidência insuficiente para publicar."
        linha = {"id": qid, "decisao": decisao, "tema_central_id": tid, "extras_ids": "",
                 "confianca": f"{prob:.8f}", "motivo": motivo}
        registro = {"id": qid, "tema_central_id": tid, "caminho": self.temas[tid]["caminho"],
                    "decisao": decisao, "confianca": prob, "compatibilidade_bruta": bruto,
                    "score_escopos": score, "limiar": politica["limiar"], "elegivel": sinal["elegivel"],
                    "motivo": motivo, "sha256_texto": perfil["hash"],
                    "atributos": dict(zip(f.NOMES_BASE, map(float, perfil["features"][k]))),
                    "top5_escopos": [{"tema_id": self.catalogo.familias[int(j)], "score": float(perfil["scores"][int(j)])}
                                      for j in ordem[:5]],
                    "extras": "Não inferidos automaticamente a partir de candidatos."}
        return linha, registro


def executar(artefatos, questoes_path, saida):
    inicio = time.perf_counter()
    saida = Path(saida)
    if saida.exists():
        raise ValueError("Saída já existe; escolha outra para preservar o histórico.")
    h_entrada = sha(questoes_path)
    runtime = Runtime(artefatos)
    questoes = legado.ler_questoes(questoes_path)
    preparado = time.perf_counter()
    linhas, rastros = [], []
    with f.threadpool_limits(limits=2):
        for q in sorted(questoes, key=lambda q: q["id"]):
            linha, rastro = runtime.classificar(q)
            linhas.append(linha); rastros.append(rastro)
    classificado = time.perf_counter()
    legado.validar_entrega(linhas, runtime.temas, [q["id"] for q in questoes])
    if sha(questoes_path) != h_entrada:
        raise ValueError("Arquivo de questões alterado durante a classificação.")
    contagens = Counter(r["decisao"] for r in linhas)
    resumo = {"versao": VERSAO, "questoes": len(linhas), "precisao_real": None,
              "decisoes": {d: contagens[d] for d in ("publicar", "revisar", "fora")},
              "cobertura_total": contagens["publicar"]/len(linhas), "chamadas_llm": 0,
              "rotulos_consultados_na_inferencia": False, "ajuste_supervisionado_na_inferencia": False,
              "custo_api_classificacao_usd": 0,
              "tempos_segundos": {"leitura_e_preparacao": preparado-inicio, "classificacao": classificado-preparado},
              "ambiente": {"python": platform.python_version(), "sistema": platform.system(), "arquitetura": platform.machine()}}
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".classificacao-v2-", dir=saida.parent))
    try:
        cal.salvar_csv(tmp/"publicacao.csv", linhas, legado.CAMPOS_ENTREGA)
        with (tmp/"rastreabilidade.jsonl").open("w", encoding="utf-8") as arq:
            for r in rastros:
                arq.write(json.dumps(r, ensure_ascii=False, allow_nan=False)+"\n")
        escrever(tmp/"resumo_classificacao.json", resumo)
        escrever(tmp/"manifesto_classificacao.json", {"modelo_sha256": sha(Path(artefatos)/"modelo.json"),
            "questoes_sha256": h_entrada, "codigo_sha256": codigos_runtime(),
            "arquivos_sha256": {p.name: sha(p) for p in sorted(tmp.iterdir())}})
        tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return resumo
