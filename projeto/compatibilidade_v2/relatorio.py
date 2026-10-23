"""Relatório conciso de quatro páginas; métricas recebidas da consolidação."""
from __future__ import annotations

import relatorio_etapa2 as anterior


def p(t):
    return {"tipo": "paragrafo", "texto": t}


def sub(t):
    return {"tipo": "subtitulo", "texto": t}


def tabela(cab, linhas):
    return {"tipo": "tabela", "cabecalho": cab, "linhas": linhas}


def pct(x):
    return f"{100*x:.2f}%".replace(".", ",")


def documento(r):
    alvo, recentes = r["fora_folha_verdade"], r["recentes_300"]
    prev, politica, cv = r["previsao"], r["politica_final"], r["cv_desenvolvimento"]
    prod, tempos = r["producao_cenario"], r["tempos"]
    paginas = [
      {"titulo": "Sistema e decisões", "rotulo": "1. CONSTRUÇÃO", "blocos": [
        p("Objetivo: classificar questões por tópico e publicar somente quando houver evidência suficiente. A versão combina busca lexical com escopos versionados e um classificador de compatibilidade treinado nos 100 rótulos oficiais. Nenhum modelo de linguagem escolhe, vota ou valida as classificações; o código calcula as decisões."),
        sub("Dados, busca e árvore"),
        p("Os anexos contêm 659 questões e 377 temas. Há 371 nós ativos não raiz e 109 famílias de nível 1. A árvore e os IDs são preservados, inclusive títulos iguais em ramos distintos. Nos atributos de compatibilidade, o HTML é convertido em texto, mantendo negações, comando e todas as alternativas, removendo comentários, scripts e estilos. A busca de escopos mantém sua normalização legada. Não se busca gabarito nem se usa a auditoria assistida da etapa 1 como rótulo de treino."),
        p("O classificador de escopos já congelado escolhe a família: 30% de similaridade de palavras, 10% de caracteres, 10% do assunto de origem e 50% do índice de escopos propostos; a família agrega pela média dos três maiores scores disponíveis. A escolha de nível 1 usa a tolerância a ancestrais da régua e perde especificidade. Não se escolhe disciplina raiz nem se transformam os cinco candidatos em extras."),
        sub("Compatibilidade e regra de decisão"),
        p("Um modelo logístico compartilha 22 atributos entre pares questão-família: evidências por campo, sinais de alternativas, formato de assertivas, citações literais e metadados fracos. O alvo vem da folha oficial: central, extras e nós da mesma cadeia são aceitos; irmãos não são equivalentes automaticamente. Itens oficiais fora geram alvos negativos para todas as famílias."),
        p("A variante final mantém o tema da busca e aprende quando abster. Uma segunda função logística transforma o sinal bruto em estimativa de acerto. A publicação exige score textual mínimo de 0,03 e confiança acima do corte aprendido. Dois temas próximos não são veto automático. Revisão informa o sinal insuficiente ou a confiança abaixo do corte. Não há exclusão automática: similaridade baixa não demonstra ausência de tema."),
        sub("Autoria e artefatos"),
        p("Código e 360 descrições de escopo tiveram autoria assistida; 11 recortes permaneceram sem descrição proposta. Não houve validação jurídica independente desses textos. Prompts, vocabulário, versões e experiências ficam no histórico. A autoria do código não se confunde com as previsões: estas são executadas pelo programa, sem chave de API e sem consulta aos rótulos durante a inferência."),
      ]},
      {"titulo": "Rótulos e avaliação", "rotulo": "2. EVIDÊNCIA", "blocos": [
        tabela(["Etapa", "Amostra", "Resultado"], [
          ["Baseline lexical", "60 de desenvolvimento", "28 acertos de tema; controle inicial"],
          ["Embedding ensaiado", "60 de desenvolvimento", "7 acertos nesta preparação; não adotado"],
          ["Escopos separados", "60 de desenvolvimento", "40 acertos; base mantida na v2"],
          ["CV: controle com margem", "100, cinco folds", "19/21 publicadas corretas; cobertura 21%"],
          ["CV: compatibilidade fixa", "100, cinco folds", "20/20 publicadas corretas; cobertura 20%"],
          ["CV: seleção interna", "100, cinco folds", "19/20 publicadas corretas; cobertura 20%"],
        ]),
        p("A divisão histórica 60/20/20 foi preservada. Os novos experimentos usam cinco folds externos e quatro internos; cada item externo fica fora do treino supervisionado da rodada. Os sinais internos ajustam a confiança, o corte e a seleção de variante. Textos duplicados normalizados permanecem no mesmo grupo; no método de vizinhos, o próprio texto é excluído."),
        p("A reordenação com compatibilidade e a variante de vizinhos não melhoraram o resultado de publicação. A seleção interna errou a Q0150 ao trocar 4708 por 6728, em outro ramo; a referência oficial aceita 4708. A variante fixa preservou 4708. É uma comparação com o rótulo oficial, não uma resolução jurídica feita pelo assistente."),
        p("Escolhi a variante fixa após observar a comparação. Portanto, seus 20/20 são evidência de desenvolvimento, não uma aprovação independente da escolha. Todos os 100 rótulos já haviam influenciado discussões e preparação; a separação computacional não elimina essa exposição. A seleção interna é a avaliação do mecanismo de escolha anterior ao fold externo, com 19/20."),
        p(f"Para a versão final, a compatibilidade usa os 100 rótulos, e o calibrador/corte usam seus sinais fora do treino (OOF). O corte final é {politica['limiar']:.6f}, com {politica['acertos_internos']}/{politica['suporte_interno']} itens aceitos no desenvolvimento selecionado. Esse ajuste final é distinto das políticas de cada fold; não recebeu um novo teste externo."),
        p("Os 100 rótulos são agora dados de desenvolvimento e ajuste final. As 559 questões guardadas pela empresa não entram no treino ou na escolha do corte. Nenhum ID funciona como atributo ou exceção. O artefato contém coeficientes, catálogo e parâmetros, sem tabela de respostas por questão."),
      ]},
      {"titulo": "Entrega e produção", "rotulo": "3. LIMITES E EVOLUÇÃO", "blocos": [
        tabela(["Recorte", "Publicar / revisar", "Cobertura"], [
          ["Todas: 659", f"{r['total']['decisoes']['publicar']} / {r['total']['decisoes']['revisar']}", pct(r['total']['cobertura'])],
          ["Avaliação: 559 sem rótulo", f"{alvo['decisoes']['publicar']} / {alvo['decisoes']['revisar']}", pct(alvo['cobertura'])],
          ["Importação recente: 300", f"{recentes['decisoes']['publicar']} / {recentes['decisoes']['revisar']}", pct(recentes['cobertura'])],
        ]),
        p(f"Precisão prevista nas publicadas das 559: {pct(prev['precisao_prevista'])}. Faixa de sensibilidade: {pct(prev['precisao_intervalo'][0])} a {pct(prev['precisao_intervalo'][1])}. A precisão real permanece desconhecida, e a previsão central está abaixo da meta de 95%. Os 20 acertos observados na CV não autorizam prometer 100% neste lote."),
        p("A previsão é a média das confianças do modelo congelado. A faixa reúne intervalos binomiais descritivos de 20/20 e 19/20; não corrige a dependência entre folds, a escolha posterior da variante nem a mudança para concursos recentes. Não é intervalo de confiança válido para a precisão das 559. A cobertura deste lote é contagem exata; seu intervalo apenas cobre arredondamento."),
        sub("Custo e gargalo para 50 mil por semana"),
        p(f"Nesta execução: {tempos['classificacao']:.3f} s para classificar 659 e {tempos['leitura_e_preparacao']:.3f} s de preparação/leitura. API de classificação: US$ 0; assinatura da conversa não rateada, tokens internos não medidos e tempo humano da etapa 2 não instrumentado. Não é custo total zero."),
        p(f"Extrapolação linear: {prod['classificacao_segundos_extrapolados']:.1f} s de classificação por 50 mil. Com tarifa ilustrativa de US$ 0,05/h, seria US$ {prod['compute_usd_por_questao_extrapolado']:.8f} por questão em compute. Não é cotação de nuvem nem teste de 50 mil questões únicas. A mesma cobertura projetaria {prod['revisoes_projetadas']:.0f} revisões; a dois minutos por item, {prod['horas_revisao_projetadas']:.0f} horas humanas. A revisão, não o custo de API, inviabiliza essa escala na configuração atual."),
        p("Em produção: validar importação e duplicações; executar busca e compatibilidade congeladas; registrar sinais; encaminhar incertezas e reportes de alunos; professor confirma correções. Auditar também amostras aleatórias das publicadas e erros por ramo. Acompanhar precisão seletiva, cobertura, Brier, casos fora e tempo de revisão. Reavaliar semanalmente novos rótulos e mudança de distribuição; retreinar/recalibrar com dados suficientes, versionar e exigir validação em dados novos antes de promover a versão."),
      ]},
      {"titulo": "Memo para o professor", "rotulo": "4. DIREITO E TAXONOMIA", "blocos": [
        p("Professor(a), o sistema sugere onde uma questão deve aparecer para o aluno. A resposta correta ajuda a interpretar o conhecimento cobrado, mas não foi procurada na internet nem atribuída por um assistente nesta etapa. Aprendemos a convenção de classificação a partir dos 100 exemplos fornecidos pela equipe."),
        sub("O que encontrei"),
        p("Na folha oficial, 39 questões têm temas extras, 22 cobrem famílias distintas e sete atravessam disciplinas. Assim, dois assuntos plausíveis não tornam uma questão defeituosa nem exigem revisão por si só. Ao mesmo tempo, títulos iguais em ramos diferentes não tornam os IDs intercambiáveis. O erro da Q0150 ilustra uma troca de ramo que a referência não aceita."),
        p("As descrições atuais frequentemente repetem nomes e informações de importação, sem dizer o que pertence ou não ao tópico. Há temas amplos, poucos exemplos por tema e oito questões oficialmente fora da árvore. Uma semelhança de título não explica por que uma questão é fora; não alterei esses rótulos nem inventei uma justificativa jurídica."),
        sub("O que recomendo mudar nos temas"),
        p("Para cada tópico, registrar uma frase de escopo, exclusões e dois ou três exemplos representativos. Priorizar homônimos e fronteiras entre ramos: Lei de Execução Penal (4703 e 6734) e Tráfico de Drogas (4708 e 6728), por exemplo. Preservar os IDs durante a discussão; só criar equivalências com confirmação da equipe. Definir também quando uma questão de várias assertivas merece extras e como tratar conteúdos que a árvore não representa."),
        sub("Do que preciso da equipe"),
        p(f"A entrega tem {alvo['decisoes']['revisar']} revisões entre as 559 sem rótulos. Isso ainda é muito para um fluxo semanal. Peço uma revisão dirigida dos limites de escopo, dos exemplos de fora e de uma amostra nova de publicadas, além das correções habituais. Não peço reclassificar os 659 itens para desenvolver o sistema. Esclarecimentos que atendam a vários itens devem virar descrições e exemplos versionados, evitando dúvidas repetidas."),
        p("Cada correção confirmada deve registrar tema central, extras, motivo, versão da árvore e responsável. Reportes dos alunos precisam de confirmação antes de virar treino. Com novos exemplos independentes poderemos medir se a precisão realmente chega a 95% e aumentar a publicação sem transferir erros ao aluno. Esta versão entrega uma decisão reproduzível e seus limites, não uma certificação de acerto jurídico."),
      ]},
    ]
    return {"titulo": "Case Vício IA - classificação com compatibilidade", "autor": "Israel Dias",
        "edicao": "Versão 2 | Dados oficiais, seleção documentada e decisão sem LLM",
        "paginas": paginas, "fontes": ["Enunciado e anexos oficiais: https://github.com/viciod/case-vicio-ia",
            "NIST e-Handbook: intervalo binomial; faixas nesta entrega são apenas descritivas"],
        "nota_paginas": "Quatro páginas, incluindo o memo na última."}


def markdown(doc):
    return anterior.markdown(doc)


def readme(r):
    a, p = r["fora_folha_verdade"], r["previsao"]
    return f"""# Case Vício IA - etapa complementar, versão 2

Classificador de escopos com compatibilidade aprendida e abstenção. **A decisão roda sem LLM, sem rede e sem consultar a folha-verdade.** O código de inferência não usa uma tabela de respostas por ID.

Nas 559 questões avaliadas pela empresa: **{a['decisoes']['publicar']} publicar, {a['decisoes']['revisar']} revisar e {a['decisoes']['fora']} fora**, cobertura **{pct(a['cobertura'])}**. Precisão prevista: **{pct(p['precisao_prevista'])}**; precisão real desconhecida. **A previsão está abaixo da meta de 95%; esta versão não demonstra que a meta foi atingida.**

Na CV de desenvolvimento, a variante fixa acertou 20/20 publicadas, com cobertura de 20%; a seleção interna de variantes acertou 19/20. Os 100 rótulos já foram vistos e usados anteriormente. A variante fixa foi escolhida após olhar a comparação. Esses resultados não são aprovação independente ou garantia para as 559 questões.

## Regenerar o CSV

Com Python 3.12 e ambiente virtual ativo, da raiz deste projeto:

```bash
python3 -m pip install -r requirements-v2.txt
python3 classificar_compatibilidade_v2.py --artefatos artefatos/compatibilidade_v2 --questoes dados/anexos/questoes.jsonl --saida entrega_reproduzida_v2
cmp publicacao.csv entrega_reproduzida_v2/publicacao.csv
```

O classificador lê o modelo congelado e o JSONL e recalcula as decisões. Não lê `folha_verdade.csv`, não acessa a rede e não executa treino supervisionado. O catálogo TF-IDF é reconstruído deterministicamente dos textos preparados. Para uma importação nova, troque o JSONL; preserve os campos. O ID só identifica a saída. Campos sem conteúdo ou ausência completa de candidato interrompem a importação para triagem, em vez de inventar um tema.

## Verificações e entrega completa

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s experimento_folha_v2/tests -v
python3 finalizar_compatibilidade_v2.py --saida entrega_reproduzida_completa_v2
cmp publicacao.csv entrega_reproduzida_completa_v2/publicacao.csv
cmp previsao.txt entrega_reproduzida_completa_v2/previsao.txt
```

Use pastas de saída novas. A consolidação verifica os registros de desenvolvimento, lê os rótulos apenas para conferência e recorte da previsão, e aplica o modelo já congelado. Não escolhe outro corte nem treina o modelo. Aprovar testes verifica o software, não o acerto jurídico das 559.

Para gerar o PDF de quatro páginas a partir do documento paginado:

```bash
python3 -m pip install -r requirements-relatorio.txt
python3 gerar_relatorio_pdf.py --entrada entrega_etapa2_v2/relatorio_paginas.json --saida relatorio_reproduzido_v2.pdf
```

## Como a classificação funciona

1. O classificador congelado de escopos escolhe uma família ativa de nível 1. Títulos iguais em ramos diferentes continuam distintos; disciplina raiz nunca é tema final.
2. O modelo logístico de compatibilidade usa 22 sinais por par questão-família. Enunciado, comando e todas as alternativas são preservados. Metadados são apoio fraco, não filtro obrigatório; citações são extrações literais, não resolução da questão.
3. O calibrador estima a chance de o central escolhido estar certo. Publicar exige score mínimo de 0,03 e confiança acima do corte aprendido. Dois candidatos próximos não exigem revisão automaticamente.
4. Extras não são gerados a partir do top5. Os extras oficiais são usados na convenção de treino e avaliação. Fora automático permanece desativado: há apenas oito exemplos oficiais e baixa similaridade não prova ausência de tema.

O ranking de temas da v1 é preservado. O que muda é a evidência usada para publicar/revisar e a confiança. Confira `entrega_etapa2_v2/resumo_entrega.json` para contagens e transições; não se infere melhora de precisão das 559 apenas pelo aumento de cobertura.

## Uso dos 100 rótulos

Os ensaios históricos e a divisão inicial 60/20/20 estão preservados. A nova CV usa cinco folds externos e quatro internos, mantendo duplicatas no mesmo grupo. A seleção de cortes e variantes usa somente os folds internos de cada rodada. Ainda assim, os rótulos já influenciaram preparação e discussões: é desenvolvimento, não teste externo inteiramente cego.

Depois de escolher a candidata, o modelo final foi treinado nos 100 rótulos e a confiança/corte foram ajustados aos seus sinais OOF. O corte final selecionou {r['politica_final']['acertos_internos']}/{r['politica_final']['suporte_interno']} itens aceitos nesse desenvolvimento; esse número é distinto dos 20/20 da CV. Não houve ajuste usando as 559 sem rótulo. A precisão verdadeira das 300 recentes continua desconhecida.

A previsão é a média das confianças nas publicadas das 559. A faixa é uma sensibilidade descritiva, não garantia populacional. A cobertura do lote é contagem exata; seu intervalo cobre apenas arredondamento. Não se elevou a previsão para 95% para fazê-la coincidir com a meta.

## Arquivos principais

| Arquivo | Conteúdo |
|---|---|
| `publicacao.csv` | As 659 decisões no formato oficial |
| `previsao.txt` | Autoavaliação referente às 559 fora da folha |
| `relatorio.md` / `relatorio.pdf` | Quatro páginas, incluindo memo de uma página |
| `artefatos/compatibilidade_v2` | Catálogo, escopos, coeficientes, calibrador e política; sem rótulos por questão |
| `compatibilidade_v2/runtime.py` | Decisão executada sem LLM e sem rótulos |
| `treinar_compatibilidade_v2.py` | Como os 100 rótulos geraram o artefato |
| `protocolo_final_v2.json` | Escolhas registradas antes do treino e da inferência final |
| `experimentos/folha_v2_escopos_001` | CV recebida e verificada, previsões e parâmetros por fold |
| `entrega_etapa2_v2/rastreabilidade.jsonl` | Evidências, confiança, candidatos e motivo por questão |
| `entrega_etapa2_v2/fila_revisao.csv` | Sugestões para os itens em revisão |
| `entrega_etapa2` | Entrega anterior preservada, sem substituição retrospectiva das métricas |
| `docs/DECISOES_V2.md` | Diagnóstico e escolhas para explicar na apresentação |

Hashes verificam integridade, não verdade jurídica. Os 360 escopos propostos pelo assistente não têm validação jurídica independente. A preparação por IA está separada da classificação: não se usam votos do assistente, gabaritos externos ou respostas da etapa 1 para decidir as novas classificações.

## Reproduzir o treino final

```bash
python3 treinar_compatibilidade_v2.py --saida artefatos/compatibilidade_v2_retreinado
```

Esse comando exige os 100 rótulos e os registros OOF históricos; não é o comando de inferência. Preserva o artefato anterior. Para reconstruir a CV, consulte `experimento_folha_v2/README.md` e indique `--dados dados/anexos`; os resultados são desenvolvimento e repetir a execução não cria uma nova amostra independente.

## Custo, tempo e produção

API de classificação executada: **US$ 0**. Não há chave ou chamada a LLM no runtime. Há dependências NumPy/SciPy/scikit-learn para as operações clássicas de texto e regressão logística. Modelos identificados por tipo, parâmetros, dependências e hashes; identificador exato do assistente da conversa não confirmado, tokens não medidos, assinatura não rateada.

Tempo observado nesta consolidação: aproximadamente **{r['tempos']['classificacao']:.3f} s** para as 659 classificações, além de **{r['tempos']['leitura_e_preparacao']:.3f} s** de preparação/leitura. Tempo humano da etapa complementar não foi instrumentado. O JSON separa medições e extrapolações. O custo de compute com tarifa hipotética não é cotação; a revisão humana domina o cenário de 50 mil por semana. Mais rótulos independentes e melhoria de escopos são necessários antes de escalar essa fila.
"""
