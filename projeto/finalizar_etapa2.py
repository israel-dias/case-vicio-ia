"""Gera as 659 linhas, a previsão e o relatório com a política já testada.

Nenhum ajuste de tema, limiar ou confiança é feito usando o teste ou as 559
questões sem rótulo. O PDF é um complemento opcional, gerado em outro comando.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path

import avaliar_teste_etapa2 as teste_mod
import runtime_etapa2 as rt
import relatorio_etapa2 as rel

cal = rt.cal
VERSAO = "entrega_complementar_v1"
ARTEFATOS_TESTE = {"congelamento_antes_teste.json", "resumo.json", "teste.csv", "LEITURA.md"}


def conferir_teste(pasta, metodo_path, politica_path, metodo, politica, rotulos, temas):
    manifesto = cal.ler_json(pasta / "manifesto.json")
    teste_mod.validar_artefatos(pasta, manifesto, ARTEFATOS_TESTE)
    codigos = {Path(p).name: cal.base.sha256(Path(p)) for p in (
        teste_mod.__file__, cal.__file__, cal.esc.__file__, cal.autoria.__file__, cal.base.__file__)}
    if (manifesto.get("versao") != teste_mod.VERSAO
            or manifesto.get("sha256_codigo") != codigos
            or manifesto.get("sha256_politica") != cal.base.sha256(politica_path)
            or manifesto.get("sha256_metodo") != cal.base.sha256(metodo_path)
            or manifesto.get("sha256_entradas") != metodo["sha256_entradas"]
            or manifesto.get("ids_com_previsoes") != sorted(metodo["particao"]["teste_reservado"])
            or manifesto.get("sem_ajuste_pelo_teste") is not True
            or manifesto.get("sem_rotulos_sem_previsoes") is not True):
        raise ValueError("O teste registrado não corresponde ao método e à política atuais.")
    antes = cal.ler_json(pasta / "congelamento_antes_teste.json")
    if (antes.get("configuracao") != metodo["configuracao"]
            or antes.get("limiar_margem") != politica["limiar_margem"]
            or antes.get("confianca_por_decisao") != politica["confianca_por_decisao"]
            or antes.get("sha256_codigo") != codigos
            or antes.get("sha256_politica") != cal.base.sha256(politica_path)):
        raise ValueError("O registro anterior ao teste não confere.")
    linhas = teste_mod.ler_registros_calibracao(pasta / "teste.csv", metodo["particao"]["teste_reservado"])
    for r in linhas:
        g = rotulos[r["id"]]
        caminho = g["tema_central_caminho"].split(" > ")[0] if g["fora_da_taxonomia"] == "0" else "FORA"
        if (r["acerto_top1"] != cal.base.aceito(r["tema_previsto"], g, temas)
                or r["central_referencia"] != g["tema_central_id"]
                or r["extras_referencia"] != g["extras_ids"] or r["ramo_referencia"] != caminho):
            raise ValueError("Resultado de teste diverge da referência oficial.")
        esperado = cal.aplicar_politica(r, politica)
        if any(r[c] != esperado[c] for c in ("decisao", "confianca", "motivo")):
            raise ValueError("O teste não aplicou a política congelada.")
    resultado = cal.ler_json(pasta / "resumo.json")
    if (resultado.get("etapa") != teste_mod.VERSAO
            or resultado.get("teste") != teste_mod.resumir_teste(linhas, politica)
            or resultado.get("metodo_ou_politica_alterados") is not False):
        raise ValueError("Resumo do teste não reproduz as contas dos 20 registros.")
    return resultado


def contagem(linhas):
    c = Counter(r["decisao"] for r in linhas)
    return {"questoes": len(linhas), "decisoes": {k: c[k] for k in ("publicar", "revisar", "fora")},
            "cobertura": c["publicar"] / len(linhas) if linhas else 0.}


def prever(linhas, ids_rotulados, teste):
    alvo = [r for r in linhas if r["id"] not in ids_rotulados]
    publicadas = [r for r in alvo if r["decisao"] == "publicar"]
    p = math.fsum(float(r["confianca"]) for r in publicadas) / len(publicadas) if publicadas else 0.
    ci = list(teste["teste"]["intervalo_binomial_95_publicadas"]) if teste["teste"]["publicar"] else [0., 1.]
    ci = [min(ci[0], p), max(ci[1], p)] if publicadas else [0., 1.]
    cobertura = len(publicadas) / len(alvo) if alvo else 0.
    return {"precisao_prevista": p, "precisao_intervalo": ci,
            "cobertura_prevista": cobertura, "cobertura_intervalo_exato": [cobertura, cobertura],
            "publicadas_no_alvo": len(publicadas), "questoes_no_alvo": len(alvo),
            "precisao_definida": bool(publicadas),
            "origem_precisao": "Média das confianças fixadas na calibração; não atualizada pelo teste.",
            "origem_intervalo": "Faixa de sensibilidade baseada no intervalo binomial do teste, ampliada para conter a previsão. Não é garantia para a distribuição nova.",
            "origem_cobertura": "Fração exata das 559 decisões conhecidas, não estimativa de semanas futuras."}


def limite_texto(valor, superior=False):
    escala = 10 ** 8
    valor = (math.ceil(valor * escala) if superior else math.floor(valor * escala)) / escala
    return f"{valor:.8f}"


def texto_previsao(previsao, politica, teste):
    pi, co = previsao["precisao_intervalo"], previsao["cobertura_prevista"]
    te = teste["teste"]
    return (
        f"precisao_prevista: {previsao['precisao_prevista']:.8f}\n"
        f"precisao_intervalo: {limite_texto(pi[0])}-{limite_texto(pi[1], True)}\n"
        f"cobertura_prevista: {co:.8f}\n"
        f"cobertura_intervalo: {limite_texto(co)}-{limite_texto(co, True)}\n\n"
        f"Universo: {previsao['questoes_no_alvo']} questões fora da folha-verdade; "
        f"{previsao['publicadas_no_alvo']} selecionadas para publicar. As 100 rotuladas foram excluídas.\n"
        "A previsão de precisão é a média das probabilidades de acerto das publicadas, congeladas na calibração. "
        "A estimativa Beta(1 + acertos, 1 + erros) usa prior uniforme e a calibração selecionou também o corte: há otimismo de seleção e pouca evidência.\n"
        f"Na calibração: {politica['confianca_por_decisao']['publicar']['acertos']}/"
        f"{politica['confianca_por_decisao']['publicar']['avaliadas']} publicadas corretas. "
        f"No teste com regra fixa: {te['acertos_publicadas']}/{te['publicar']}. "
        "O teste não foi usado para atualizar as probabilidades ou escolher outro corte.\n"
        "A faixa de precisão é uma sensibilidade baseada no intervalo binomial exato de 95% do teste, ampliada se necessário para conter a previsão fixada. "
        "Não é uma garantia de 95% para a precisão final: pressupõe comparabilidade dos itens e não corrige exposição prévia aos rótulos, seleção de modelos ou mudança de distribuição.\n"
        "A cobertura deste lote é conhecida depois de gerar as decisões. Seu intervalo só reflete arredondamento de oito casas decimais, "
        "sem incerteza amostral sobre quantas decisões foram publicar. Não representa cobertura esperada para qualquer importação futura.\n"
        "As 300 questões recentes não têm rótulos disponíveis. A precisão verdadeira das 559 continua desconhecida, e a meta de 95% ainda não foi demonstrada.\n"
        + ("Sem publicadas, a precisão é indefinida; zero na primeira linha é apenas convenção de formato.\n" if not previsao["precisao_definida"] else "")
    )


def readme(resumo, saida):
    alvo, te = resumo["fora_folha_verdade"], resumo["teste"]
    modelo = (saida / "modelo").as_posix()
    return f"""# Case Vício IA - etapa complementar

Classificador lexical com escopos versionados, hierarquia e política de abstenção. **A decisão roda sem modelo de linguagem e sem consultar a folha-verdade.** Python 3.12 recomendado; o CSV usa apenas biblioteca padrão.

Nas 559 questões avaliadas pela empresa: **{alvo['decisoes']['publicar']} publicar, {alvo['decisoes']['revisar']} revisar, {alvo['decisoes']['fora']} fora**, cobertura **{rel.pct(alvo['cobertura'])}**. Precisão verdadeira desconhecida. No teste de 20 itens: **{te['acertos_publicadas']}/{te['publicar']}** publicadas aceitas, cobertura **{rel.pct(te['cobertura'])}**. A amostra é pequena; não comprova precisão mínima de 95%. A baixa cobertura também limita a utilização em produção.

## Regenerar publicacao.csv

Execute da raiz do projeto, onde estão os módulos Python e `dados/anexos`. O artefato preparado fica em `{modelo}`:

```bash
python3 classificar_etapa2.py --artefatos {modelo} --questoes dados/anexos/questoes.jsonl --saida entrega_reproduzida_etapa2
cmp publicacao.csv entrega_reproduzida_etapa2/publicacao.csv
```

O primeiro comando **calcula novamente o ranking e as decisões**. Não reproduz uma tabela de respostas. `folha_verdade.csv` não é entrada desse comando, e o artefato não guarda IDs ou rótulos por questão. Para uma importação nova, troque `--questoes` por outro JSONL com os mesmos campos. IDs só identificam a saída. Use uma pasta de saída nova em cada reprodução.

Se os arquivos de entrega ainda estiverem somente em `{saida.as_posix()}`, compare com `{(saida/'publicacao.csv').as_posix()}` em vez do CSV da raiz. Modelo, código e textos preparados são conferidos por SHA-256; isso verifica integridade, não verdade jurídica.

## Reproduzir a consolidação e os documentos

```bash
python3 -m unittest discover -s tests -v
python3 finalizar_etapa2.py --saida entrega_reproduzida_completa
```

Esse comando verifica o método congelado, a calibração e o teste já registrados; prepara o artefato de inferência; classifica as 659 questões; gera CSV, previsão, relatório Markdown, documento paginado e rastreabilidade. Não refaz seleção de parâmetros. Tempos variam; CSV e previsão devem ser idênticos para as mesmas entradas e política. As probabilidades da calibração permanecem fixas depois do teste.

Para gerar o PDF de quatro páginas (complemento de apresentação; não participa da classificação):

```bash
python3 -m pip install -r requirements-relatorio.txt
python3 gerar_relatorio_pdf.py --entrada {saida.as_posix()}/relatorio_paginas.json --saida {saida.as_posix()}/relatorio.pdf
```

O relatório Markdown também é entrega válida. O código de PDF usa ReportLab, separado do runtime de classificação.

## Como o método foi escolhido

1. Baseline lexical: 28/60 no desenvolvimento. Comparações de campos, palavras e caracteres: melhor controle 35/60.
2. Embedding genérico multilíngue: 7/60 nesta preparação; lexical com vizinho rotulado: 36/60. Resultados negativos foram preservados; não significam que toda abordagem semântica seja ruim.
3. Escopos propostos em índice separado e média dos scores do pai/filhos: 40/60. O método sugere nível 1, perde detalhe e usa a tolerância a ancestrais da régua; nunca usa a disciplina raiz.
4. Desenvolvimento propõe cortes; calibração escolhe corte e estima confiança; teste mede a política fixa. A divisão original 60/20/20 não foi refeita. Todos os 100 rótulos já apareceram na conversa: a reserva computacional não equivale a teste externo inteiramente cego.

Os resultados, prompts de preparação, código e metadados dos ensaios ficam nas pastas originais `experimentos`, `artefatos` e nos módulos `experimento_*`. O prompt de referência é uma descrição do procedimento, não uma transcrição integral da conversa. O classificador final não depende do cache de embeddings descartado.

## Arquivos e limites

| Arquivo | Finalidade |
|---|---|
| `publicacao.csv` | 659 linhas, formato oficial |
| `previsao.txt` | Previsão e cobertura das 559 fora da folha-verdade |
| `relatorio.md` / `relatorio.pdf` | Sistema, rótulos, diagnóstico, produção e memo |
| `{saida.as_posix()}/modelo` | Artefatos usados no comando de regeneração |
| `{saida.as_posix()}/rastreabilidade.jsonl` | Sinais e caminho sugerido de cada decisão; sem validação por LLM |
| `{saida.as_posix()}/resumo_entrega.json` | Contagens, previsão, tempo e projeção de produção |
| `{saida.as_posix()}/manifesto_entrega.json` | Hashes das entradas, política e saídas |
| `experimentos/calibracao_001` / `experimentos/teste_001` | Política, métricas e registro anterior à avaliação |

Os 377 temas incluem dois inativos e quatro disciplinas raiz; 371 nós são candidatos ativos não raiz. As descrições de 360 foram propostas pelo assistente; 11 recortes permaneceram sem escopo. Não se mesclam títulos iguais em ramos distintos. A hierarquia e os IDs originais foram preservados. Extras não são preenchidos a partir dos cinco primeiros candidatos. Baixa similaridade não prova `fora`: não há descarte automático nesta versão. Conteúdo sem candidato recuperável interrompe uma importação para triagem.

Na inferência são usados enunciado, comando, alternativas e assunto de origem como apoio de 10% no score. ID e disciplina de origem não são atributos. Não se busca gabarito de prova, não se usam as respostas manuais da etapa 1 como rótulos e não se resolvem as 559 questões com o assistente. As decisões da etapa complementar saem do algoritmo. A exposição histórica aos textos e rótulos é registrada como limitação.

## Modelos, autoria, custo e tempo

Método final: TF-IDF, similaridade cosseno, agregação da árvore e limiar de margem; confiança por grupo com suavização Beta(1,1). Código e escopos tiveram autoria assistida nesta conversa; identificador exato do modelo não confirmado, tokens internos não medidos, sem validação jurídica independente. Modelo de embedding apenas ensaiado: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, ONNX quantizado, com preparação opcional documentada no histórico.

API de classificação: **US$ 0**. Assinatura existente não rateada. O custo total não é zero: revisão humana, infraestrutura e manutenção precisam ser orçados. Tempo local para as 659 classificações: aproximadamente **{resumo['tempos_execucao']['classificacao']:.4f} s**, com **{resumo['tempos_execucao']['leitura_e_preparacao']:.4f} s** de leitura/preparação na medição registrada; confira ambiente e fases no JSON. O tempo humano da etapa complementar não foi instrumentado.

```bash
python3 benchmark_etapa2.py --artefatos {modelo} --questoes dados/anexos/questoes.jsonl --volume 50000 --saida experimentos/carga_50000.json
```

O benchmark repete os textos do lote para medir desempenho; não mede qualidade em 50 mil questões únicas. A tarifa padrão de US$ 0,05/h é uma hipótese ilustrativa parametrizável, não cotação de nuvem. A fila de revisão projetada é o principal gargalo. O relatório descreve coleta de correções, auditoria aleatória de publicadas e condições para retreino/recalibração antes de produção.
"""


def executar(dados, metodo_path, politica_path, teste_dir, escopos_path, vocabulario_path, saida):
    if saida.exists():
        raise ValueError("Pasta de entrega já existe; use outra para preservar a versão anterior.")
    metodo, questoes, rotulos, temas, propostas = cal.conferir_congelamento(dados, metodo_path, escopos_path, vocabulario_path)
    politica = teste_mod.conferir_politica(politica_path, metodo_path, metodo)
    teste = conferir_teste(teste_dir, metodo_path, politica_path, metodo, politica, rotulos, temas)
    if not politica["ativa"]:
        raise ValueError("Política sem publicação ativa; registre essa limitação e prepare o relatório específico antes de exportar.")
    hashes_antes = {n: cal.base.sha256(dados / n) for n in ("questoes.jsonl", "temas.csv", "folha_verdade.csv")}
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".entrega-", dir=saida.parent))
    try:
        rt.preparar_artefatos(dados / "temas.csv", escopos_path, vocabulario_path, metodo, politica,
                              metodo_path, politica_path, temporaria / "modelo")
        classificacao = rt.executar(temporaria / "modelo", dados / "questoes.jsonl", temporaria / "_classificacao")
        for p in (temporaria / "_classificacao").iterdir():
            shutil.move(str(p), temporaria / p.name)
        (temporaria / "_classificacao").rmdir()
        linhas = cal.base.ler_csv(temporaria / "publicacao.csv")
        rt.validar_entrega(linhas, temas, sorted(questoes))
        por_id = {r["id"]: r for r in linhas}
        # Confere reprodução nos 100 rótulos depois da inferência, nunca como atributos.
        registros_anteriores = (cal.base.ler_csv(politica_path.parent / "desenvolvimento.csv")
                               + cal.base.ler_csv(politica_path.parent / "calibracao.csv")
                               + cal.base.ler_csv(teste_dir / "teste.csv"))
        for anterior in registros_anteriores:
            r = por_id[anterior["id"]]
            if (r["tema_central_id"] != anterior["tema_previsto"] or r["decisao"] != anterior["decisao"]
                    or abs(float(r["confianca"]) - float(anterior["confianca"])) > 5.1e-9):
                raise ValueError("A inferência não reproduziu a política dos registros congelados.")
        ids_rotulados = set(rotulos)
        alvo = [r for r in linhas if r["id"] not in ids_rotulados]
        antigos = [r for r in alvo if int(r["id"][1:]) <= 359]
        recentes = [r for r in alvo if int(r["id"][1:]) >= 360]
        if len(alvo) != 559 or len(antigos) != 259 or len(recentes) != 300:
            raise ValueError("Recortes de avaliação diferentes de 559 = 259 antigas + 300 recentes.")
        previsao = prever(linhas, ids_rotulados, teste)
        tempo = classificacao["tempos_segundos"]
        t50000 = tempo["classificacao"] * 50000 / len(linhas)
        cobertura = contagem(alvo)["cobertura"]
        revisoes = (1 - cobertura) * 50000
        resumo = {"versao": VERSAO, "total": contagem(linhas), "fora_folha_verdade": contagem(alvo),
                  "antigas_fora_folha": contagem(antigos), "recentes_300": contagem(recentes),
                  "rotuladas_100": contagem([r for r in linhas if r["id"] in ids_rotulados]),
                  "registros_congelados_conferidos": len(registros_anteriores),
                  "precisao_real_559": None, "previsao": previsao, "teste": teste["teste"],
                  "tempos_execucao": tempo, "ambiente_execucao": classificacao["ambiente"],
                  "producao_cenario": {"volume_semanal": 50000, "tempo_classificacao_50000_segundos": t50000,
                                       "origem_tempo": "Extrapolação linear da classificação das 659; não benchmark de 50 mil únicas.",
                                       "tarifa_compute_usd_hora_hipotetica": .05,
                                       "custo_compute_usd": t50000 / 3600 * .05,
                                       "custo_compute_por_questao_usd": t50000 / 3600 * .05 / 50000,
                                       "revisoes_50000": revisoes, "segundos_por_revisao_hipoteticos": 120,
                                       "horas_revisao_cenario": revisoes * 120 / 3600},
                  "limites": ["Precisão mínima de 95% não demonstrada; poucas publicadas no teste.",
                              "Confiança não alterada pelo teste; probabilidades por grupo, com suporte pequeno.",
                              "Os 100 rótulos e textos já apareceram na conversa; não é teste externo inteiramente cego.",
                              "Sem rótulos recentes; mudança de distribuição não quantificada.",
                              "Não há detector automático de fora; alta carga de revisão limita produção.",
                              "Autoria assistida de escopos e código; sem validação jurídica independente."]}
        cal.escrever_json(temporaria / "resumo_entrega.json", resumo)
        (temporaria / "previsao.txt").write_text(texto_previsao(previsao, politica, teste), encoding="utf-8")
        doc = rel.documento(resumo, politica, metodo, teste, classificacao)
        cal.escrever_json(temporaria / "relatorio_paginas.json", doc)
        (temporaria / "relatorio.md").write_text(rel.markdown(doc), encoding="utf-8")
        (temporaria / "README.md").write_text(readme(resumo, saida), encoding="utf-8")
        atuais = {n: cal.base.sha256(dados / n) for n in hashes_antes}
        if atuais != hashes_antes:
            raise ValueError("Anexos alterados durante a geração da entrega.")
        arquivos = [p for p in temporaria.rglob('*') if p.is_file()]
        manifesto = {"versao": VERSAO, "sha256_entradas": hashes_antes,
                     "sha256_metodo": cal.base.sha256(metodo_path), "sha256_politica": cal.base.sha256(politica_path),
                     "sha256_teste_manifesto": cal.base.sha256(teste_dir / "manifesto.json"),
                     "sha256_codigo": {**rt.codigos_runtime(), Path(__file__).name: cal.base.sha256(Path(__file__)),
                                       Path(rel.__file__).name: cal.base.sha256(Path(rel.__file__)),
                                       Path(teste_mod.__file__).name: cal.base.sha256(Path(teste_mod.__file__))},
                     "nao_ajustado_apos_teste": True, "classificacoes_manuais_aplicadas_nesta_versao": 0,
                     "sha256_artefatos": {p.relative_to(temporaria).as_posix(): cal.base.sha256(p) for p in sorted(arquivos)}}
        cal.escrever_json(temporaria / "manifesto_entrega.json", manifesto)
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    p.add_argument("--metodo", type=Path, default=Path("experimentos/escopos_001/metodo_congelado.json"))
    p.add_argument("--politica", type=Path, default=Path("experimentos/calibracao_001/politica_congelada.json"))
    p.add_argument("--teste", type=Path, default=Path("experimentos/teste_001"))
    p.add_argument("--escopos", type=Path, default=Path("artefatos/escopos_v1/escopos.json"))
    p.add_argument("--vocabulario", type=Path, default=Path("artefatos/escopos_v1/vocabulario_autorado.tsv"))
    p.add_argument("--saida", type=Path, default=Path("entrega_etapa2"))
    a = p.parse_args()
    try:
        r = executar(a.dados, a.metodo, a.politica, a.teste, a.escopos, a.vocabulario, a.saida)
    except (ValueError, OSError, KeyError, TypeError) as e:
        p.exit(2, f"Erro: {e}\n")
    print(json.dumps({k: r[k] for k in ("total", "fora_folha_verdade", "recentes_300", "precisao_real_559", "previsao")}, ensure_ascii=False, indent=2))
    print(f"Entrega gerada em: {a.saida}")


if __name__ == "__main__":
    main()
