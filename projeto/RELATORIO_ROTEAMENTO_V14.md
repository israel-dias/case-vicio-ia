# V14 — teste das regras de leitura e corte de 70%

**Conclusão:** há ganhos locais na identificação do tema, mas nenhuma das novas opções com corte de 70% e preservação da V11 alcançou 95% nas publicadas das 100. A entrega histórica não foi substituída. A V11 preservada continua sendo a referência nesta comparação.

## Propostas implementadas e suas interpretações

As hipóteses incluem: instruções Assinale/Marque e similares como sinais de leitura; prioridade de comando com assunto identificável; Explique apenas no comando, com fallback para norma/artigo literalmente citado; leitura de assertivas I/II/III; maioria dos assuntos sugeridos por item e primeiro item em ausência de maioria; descarte temático de alternativas Certo/Errado, números e combinações; situação hipotética no enunciado ou comando; prioridade das alternativas em caso narrado; atributos de desconhecimento e condição da vítima combinados à evidência lexical de erro; comparação de candidatos e proteção contra homônimos sem distinção de escopo.

Precedência na implementação literal: comando identificável; Explique com norma; Explique sem identificação/norma; itens; Certo/Errado; situação hipotética; caso narrado; instrução; conjunto. Conflitos entre propostas são resolvidos nessa ordem. As combinações de itens são preservadas nos dados originais, mas não adicionam assunto temático. Não se resolve qual combinação é verdadeira. Quando Explique não fornece identificador nem norma, o sistema mantém contexto apenas para sugerir revisão e bloqueia publicação pela rota.

O identificador operacional usa títulos/vocabulário preparado, coincidência de pelo menos dois termos relevantes ou termo raro no catálogo; isso também pode produzir falsos positivos. Não é um analisador sintático ou uma certificação jurídica. Os grupos de assuntos dos itens são estimados pelo recuperador lexical de cada item: grupo mais frequente com pelo menos dois votos vence; sem maioria única, a literal usa o primeiro. A igualdade de títulos usada para contar votos não torna IDs equivalentes na avaliação.

Quatro variantes são comparadas. Literal descarta campos conforme as prioridades; contextual preserva evidência de apoio; comparador treinado reordena todas as famílias com regressão logística; fusão combina 70% do ranking V8 normalizado com 30% do ranking por papéis. Esses 70/30 são pesos de busca, não confiança. A fusão foi acrescentada depois de observar regressão na primeira rodada; é desenvolvimento pós-análise, não hipótese confirmada por teste independente.

Novos modelos usam 27 atributos compactos de texto, comando, alternativas, itens, referências, desconhecimento e contrastes. Não são uma ablação isolada dos 39 atributos V11. Portanto não se atribui toda regressão ou ganho a um marcador específico. Uma comparação adicional, descrita abaixo, mantém o recuperador V8 e varia somente a leitura.

## Método

Mesmos cinco folds externos e quatro internos; cada treino, calibração e corte usa apenas seu grupo interno. A calibração tenta 95% empíricos com suporte mínimo de dez. A regra de corte fixo 70% ignora a exigência de política ativa, mas conserva proteção de conteúdo e homônimos. Novos candidatos não recebem bônus de confiança nem publicação direta só por palavra. Sem LLM ou busca de gabaritos na classificação.

Os 100 rótulos e vários erros já foram vistos repetidamente. Os resultados são de desenvolvimento reutilizado, não teste externo cego. As 559 não têm rótulos disponíveis. A qualidade real nos 300 itens recentes permanece desconhecida.

## Comparação principal: corte 70%, preservando as publicações V11

| Configuração | Publicadas nas 100 | Acertos | Erros | Precisão | Publicadas nas 559 | Cobertura nas 559 |
|---|---:|---:|---:|---:|---:|---:|
| V11 atual, corte original | 40 | 39 | 1 | 97,50% | 361 | 64,58% |
| V11 com corte 70% | 51 | 48 | 3 | 94,12% | 368 | 65,83% |
| Prioridades e descartes propostos | 49 | 46 | 3 | 93.88% | 377 | 67.44% |
| Papéis com contexto preservado | 57 | 51 | 6 | 89.47% | 403 | 72.09% |
| Comparador treinado de candidatos | 51 | 43 | 8 | 84.31% | 370 | 66.19% |
| Fusão conservadora de rankings | 66 | 60 | 6 | 90.91% | 413 | 73.88% |

Preservar mantém também o erro antigo Q0252, já contado. Não se usa o acerto da folha para escolher saídas. A fusão atinge maior cobertura sem rótulo, mas falha na meta observada: 60/66, aproximadamente 90,91%. Não foi promovida pelo volume publicado.

## Sem preservar: resultado das novas versões isoladas

| Variante | Sugestões top1 aceitas /100 | Publicadas com corte70 | Corretas | Precisão publicada | Publicadas com corte calibrado |
|---|---:|---:|---:|---:|---:|
| Prioridades e descartes propostos | 60 | 24 | 19 | 79.17% | 0 |
| Papéis com contexto preservado | 66 | 43 | 36 | 83.72% | 14 |
| Comparador treinado de candidatos | 63 | 29 | 20 | 68.97% | 2 |
| Fusão conservadora de rankings | 74 | 63 | 57 | 90.48% | 32 |

Na literal, nenhum dos grupos encontrou um corte calibrado com o suporte interno exigido. Zero publicadas implica precisão indefinida, não 100%. Os resultados calibrados completos e os cortes de cada grupo estão nos JSONs; a exigência interna não garante o resultado externo.

## Ablação sobre o mesmo recuperador V8

Esta etapa é posterior às duas rodadas principais e avalia apenas top1, sem inferência de precisão publicada. O controle sem atalho tem 70/100, diferente dos 71/100 da V11 com identificadores.

| Texto fornecido ao MESMO recuperador | Top1 aceitas /100 | Corrigidas | Acertos perdidos |
|---|---:|---|---|
| original | 70 | nenhuma | nenhum |
| ce_sem_alternativas | 70 | nenhuma | nenhum |
| somente_comando_identificado | 72 | Q0034, Q0313, Q0319 | Q0275 |
| somente_itens_selecionados | 70 | nenhuma | nenhum |
| roteamento_literal_completo | 67 | Q0034, Q0313, Q0319 | Q0003, Q0201, Q0216, Q0230, Q0275, Q0290 |

Priorizar o comando identificável produziu saldo positivo de duas sugestões (três corrigidas e uma perdida). Retirar Certo/Errado das alternativas não mudou nenhuma sugestão. Aplicar todos os descartes juntos perdeu seis acertos e corrigiu três. Isso dá apoio a uma prioridade contextual limitada, mas não a uma regra universal de exclusão de campos.

## Sucessos locais e limites

Na literal, com corte70 e sem preservar, Q0319 mudou para Concurso de Pessoas (5071), aceito como pai, confiança 70,15%; Q0313 para Teoria da Pena (5199), aceita como pai, 75,02%; Q0316 para Fato Típico (5218), aceito como pai de Erro de Tipo, 89,55%. Esses acertos não validam o conjunto de regras, que teve 19/24 nas publicadas.

No agrupamento de itens houve três escolhas por maioria: Q0150 e Q0251 tiveram sugestões corretas; Q0052 não. Houve três escolhas pelo primeiro: Q0191 correta; Q0124 e Q0324 incorretas. Esses seis casos são poucos. As falhas do agrupador não provam que o conteúdo do primeiro item seja juridicamente incompatível: na Q0324, por exemplo, Contravenções Penais (4686) é extra oficial; o algoritmo errou ao representar o primeiro item como Teoria Geral das Prisões (5584). A hipótese de primeiro item não foi demonstrada segura e não deve substituir leitura do conjunto por conveniência.

## Escopos e fora

As descrições preparadas de LEP 4703/6734 são idênticas; as de Maria da Penha 4704/6724 também. Isso comprova igualdade nos artefatos, não equivalência jurídica nem autorização para escolher um ID por ordem. A proteção contra homônimos bloqueia publicação quando a evidência textual empata e o comparador também não os separa.

A folha contém oito itens fora, sem justificativas individuais. PENDENCIAS_ESCOPO.json conserva as questões e os pontos para esclarecimento, incluindo Q0017, Q0043 e Q0303. Nenhum contato foi enviado. Não se aprendeu pobreza => fora nem uma exclusão manual para acertar a folha. Os rótulos fora permanecem negativos de compatibilidade no treino, como referências fornecidas.

## Evidência e reprodução

18 testes V14 passaram. Uma execução real de inferência reproduziu as 559 da fusão com corte70, sem rede e com a leitura da folha-verdade bloqueada. Código de treino e dados originais preservados; modelos congelados não contêm tabelas por ID. Testes de integridade não validam Direito.

Rodada 001 e seu código estão preservados. Na 002, situação hipotética passou a ser reconhecida também no comando e foi adicionada a fusão conservadora. Nenhum resultado anterior foi apagado.

## Recomendação

Manter a referência V11. Conservar o sinal de comando como hipótese promissora e a normalização de grafia; não substituir a política por corte70 nem por maioria/primeiro automáticos. As sugestões de leitura precisam melhorar a representação e a comparação de temas antes de aumentar a publicação. A próxima validação deve usar rótulos novos e escopos esclarecidos; repetir os mesmos 100 não produz uma confirmação independente.

As exceções completas estão em EXCECOES_REGRAS_V14.md. Comandos estão no README. Nenhuma versão foi enviada à recrutadora ou publicada no GitHub por este pacote.

