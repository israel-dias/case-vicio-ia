# O que a auditoria da confiança demonstrou

Foi executado um experimento com a versão atual e oito alternativas. Cada alternativa retirou grupos de atributos ou mudou o objetivo do treinamento. Todas passaram por novo treinamento e nova calibração. Nenhuma ganhou pontos de confiança por uma regra escrita à mão.

## Resposta à dúvida

Há sinais dispensáveis ou que merecem reformulação. Entretanto, os resultados não sustentam apagar todos os critérios que parecem reduzir a confiança. Alguns ajudam a evitar publicações erradas. Outros são redundantes e sua remoção mudou pouco o resultado.

Os alertas exibidos são gerados depois da decisão. Apagar a frase de um alerta não muda a confiança. O valor vem da combinação de atributos por um modelo treinado e depois calibrado. “Sem associação normativa”, por exemplo, tem coeficiente positivo no modelo final da v3; não é uma multa automática aplicada à questão.

## Resultado comparável nos 100 exemplos conhecidos

As divisões foram as mesmas da v3: cinco grupos externos, cada um com quatro grupos internos. Em cada rodada, o grupo externo fica fora do treinamento, da calibração e da escolha do corte. São os mesmos 100 exemplos já conhecidos e discutidos; o experimento não é um teste externo novo.

| Experimento | Publicadas | Corretas | Precisão observada | Cobertura |
|---|---:|---:|---:|---:|
| Versão atual | 23 | 22 | 95,65% | 23% |
| Sem sinais de formato | 25 | 24 | 96,00% | 25% |
| Sem metadados de origem | 25 | 24 | 96,00% | 25% |
| Sem o atributo “citação sem correspondência” | 22 | 21 | 95,45% | 22% |
| Sem os dois atributos de apoio simultâneo entre enunciado e alternativas | 23 | 22 | 95,65% | 23% |
| Sem todos os sinais normativos | 24 | 22 | 91,67% | 24% |
| Sem origem, formato e apoio simultâneo | 17 | 17 | 100,00% | 17% |
| Representação reduzida de 39 para 10 atributos | 4 | 4 | 100,00% | 4% |
| Treino direto do acerto do primeiro candidato, com 10 atributos | 16 | 13 | 81,25% | 16% |

Sinais de formato são: indicador Certo/Errado, indicador de assertivas numeradas e quantidade de alternativas. Metadados são disciplina e assunto de origem. Os textos das alternativas foram preservados em todos os experimentos.

Nenhuma das diferenças pequenas prova superioridade estatística. Cada variante foi avaliada sem os rótulos do seu grupo externo, mas as escolhas de hipóteses foram feitas durante desenvolvimento sobre dados já conhecidos.

Um procedimento separado, que escolhe a variante em cada grupo apenas pelas avaliações internas, publicou 40/100, com 38 acertos: 95% observados. Isso avalia o procedimento de seleção entre variantes; não é o resultado de uma única variante fixa nem uma medição de acerto das 559 questões.

## Simulação da candidata sem sinais de formato nas 559

A candidata foi escolhida pelo suporte nos sinais fora do treino dos 100 exemplos, antes de observar seu volume de publicação nas 559. É uma simulação diagnóstica; não substituiu os arquivos de entrega.

| Medida | V3 atual | Candidata sem formato |
|---|---:|---:|
| Publicar | 175 | 231 |
| Revisar | 384 | 328 |
| Cobertura | 31,31% | 41,32% |
| Média das probabilidades nas publicadas | 92,90% | 90,44% |
| Precisão real nas 559 | Desconhecida | Desconhecida |

Ganhar 56 publicações não prova que todas sejam corretas. A candidata ampliou o conjunto selecionado e baixou o corte após nova calibração. A média das probabilidades também caiu. Não é correto dizer que esse experimento comprovou 95% nas 559 ou que aumentou a precisão prevista.

## O obstáculo que a confiança não consegue corrigir

Todas as variantes desta auditoria preservaram os mesmos temas sugeridos. Nos 100 exemplos, essas sugestões acertam 66 questões antes de qualquer decisão de publicação.

Na versão atual, 44 sugestões corretas ficaram retidas para revisão, junto com 33 sugestões incorretas. Portanto, existe conservadorismo a reduzir, mas a fila contém também erros que precisam continuar bloqueados.

Mantendo os mesmos temas, mesmo um seletor que soubesse exatamente onde estão os 66 acertos publicaria no máximo 69 dessas 100 questões com precisão de pelo menos 95%. Publicar 80/100 com os mesmos temas permitiria, no melhor cenário, 66/80 = 82,5% de precisão. Esse cálculo vale para esta amostra; não é um limite conhecido para as 559 sem rótulo.

Por isso, aumentar a confiança de todos os candidatos não resolve. A escolha do tema precisa melhorar junto com a seleção de quais sugestões são suficientemente confiáveis.

## O que aconteceu aos cinco exemplos da conversa

| Questão | Confiança atual | Confiança sem formato | Decisão experimental |
|---|---:|---:|---|
| Q0568 | 60,71% | 61,26% | revisar |
| Q0496 | 36,07% | 34,89% | revisar |
| Q0523 | 41,15% | 41,77% | revisar |
| Q0492 | 44,79% | 50,58% | revisar |
| Q0458 | 83,30% | 82,05% | publicar |

A Q0458 passa na simulação porque o corte foi recalibrado de 83,54% para 77,39%; sua probabilidade individual diminuiu. Isso ilustra por que elevar as porcentagens não é o mesmo que melhorar a política. Não houve validação jurídica desses exemplos nem alteração manual por ID.

## Recomendação

1. Manter a retirada dos sinais de formato como candidata a simplificação. O ganho foi pequeno na comparação por grupos, sem demonstração de superioridade estatística.
2. Reformular o texto do alerta normativo para distinguir informação não mapeada de incompatibilidade. A remoção do atributo, isoladamente, não melhorou a seleção neste experimento.
3. Preservar os sinais normativos úteis: sua remoção completa liberou um item fora da taxonomia e reduziu a precisão observada para 91,67%.
4. Priorizar agora a representação do que a questão pede e a comparação entre temas candidatos. Melhorar apenas a confiança mantém o limite das sugestões atuais.
5. Avaliar novas escolhas com a mesma régua de ramos, sem usar um modelo de linguagem para decidir ou validar os temas das questões avaliadas.

## Onde verificar

- `experimentos/auditoria_confianca_v4_002/ANALISE.md`: relatório técnico completo.
- `resumo.json`, na mesma pasta: métricas das nove variantes e do procedimento de seleção interna.
- `coeficientes_e_estabilidade.csv`: sinais dos pesos nos modelos dos cinco grupos.
- `contribuicoes_384_revisoes.csv`: decomposição exata da confiança original, sem interpretação causal.
- `simulacao_559_variantes.csv`: comparação por questão, com temas preservados.
- `protocolo_previo.json` e `modelos_folds/`: hipóteses e registros anteriores à avaliação de cada grupo externo.

Fontes metodológicas: [interpretação de coeficientes](https://scikit-learn.org/1.8/auto_examples/inspection/plot_linear_model_coefficient_interpretation.html) e [validação cruzada aninhada](https://scikit-learn.org/1.8/auto_examples/model_selection/plot_nested_cross_validation_iris.html), documentação oficial do scikit-learn.
