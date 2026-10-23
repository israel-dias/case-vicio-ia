# Experimento v9: títulos, relações e alternativas

Esta pasta contém um experimento completo. Os arquivos publicacao.csv e previsao.txt da raiz permanecem como controles históricos v5; NÃO foram substituídos pelos resultados v9. Não há nova entrega promovida.

## O que foi testado

1. Reconhecer títulos ativos do catálogo e sinônimos preparados no enunciado efetivo. Nós filhos fornecem evidência para a família pai; homônimos de ramos diferentes continuam separados.
2. Preferir a última referência com candidato conhecido: sobre, acerca de, a respeito de, em relação a, referente a, quanto a, no que se refere/diz respeito/concerne/tange e no tocante a. Retomadas como essa conduta e como sendo reutilizam o extrator v7. Considerando não é marcador.
3. Quando a mesma expressão aponta para caminhos diferentes, comparar 60% de semelhança do contexto com 40% da média das alternativas, exigindo margem relativa de 15%. Esses números são parâmetros experimentais fixos, não probabilidades.
4. Se a regra produz candidato, a hipótese experimental publica por essa via; senão mantém o controle v8. Certo/Errado e combinações I/II não fornecem conteúdo temático substituto. Não há resolução de alternativas nem gabaritos gerados por LLM.

## Duas rodadas preservadas

A primeira rodada aceitou títulos como Conduta e Resultado isoladamente e tentou desempatar quaisquer assuntos. Produziu erros: o encontro literal de uma palavra não equivale ao entendimento da pergunta. Seus arquivos e código permanecem em experimentos/relacoes_v9_001 e historico/relacoes_v9_rodada1.

Após observar os resultados, a segunda rodada removeu esses dois acionadores genéricos, encerrou complementos de referência na vírgula e limitou a desambiguação automática aos caminhos acionados pela mesma expressão. Trata-se de refinamento posterior com os mesmos dados, não de teste externo novo. Os resultados abaixo são da rodada 2.

## Resultados nas 100 questões

| Variante | Publicadas | Corretas | Precisão publicada | Acerto top1 em todas |
|---|---:|---:|---:|---:|
| Controle v8 | 16 | 16 | 100.00% | 70/100 |
| Título/sinônimo único | 36 | 35 | 97.22% | 71/100 |
| Prioridade às relações | 37 | 35 | 94.59% | 70/100 |
| Relações + desambiguação | 37 | 35 | 94.59% | 70/100 |

As regras novas foram avaliadas contra todos os 100 rótulos, inclusive os oito fora da taxonomia. O rótulo oficial não é consultado para aceitar/rejeitar cada classificação. O controle é a previsão do fold externo de cada questão. A regra foi preparada sem IDs, mas seus refinamentos foram motivados por erros conhecidos. Os resultados são evidência de desenvolvimento reutilizado, não validação independente.

A variante de título único acionou em 25 questões, acertando 24 (96%). Em combinação com o controle publicou 36, acertando 35 (97,22%). Ambas as contagens incluem os acionamentos sobre questões que o controle já publicava; não se somam 25 e 16.

## Simulação nas 559 questões sem rótulo

| Variante | Publicar | Revisar | Cobertura | Publicadas entre as 300 recentes |
|---|---:|---:|---:|---:|
| Controle v8 | 287 | 272 | 51.34% | 158 |
| Título/sinônimo único | 352 | 207 | 62.97% | 195 |
| Prioridade às relações | 357 | 202 | 63.86% | 196 |
| Relações + desambiguação | 362 | 197 | 64.76% | 198 |

A precisão real nas 559 e nas 300 recentes é desconhecida. A variante com maior volume não foi promovida à entrega. Não atribuímos 80%, 95% ou 100% por simples encontro de uma palavra.

## Casos para entender o resultado

- Q0245: a respeito da prescrição identifica Prescrição 5185; a regra direta publica e coincide com a referência.
- Q0308: Inquérito Policial 5498 é o pai do tema oficial 5501; a regra direta publica corretamente. O controle OOF revisava, mas a inferência final v8 já publicava: são avaliações diferentes.
- Q0034: habeas corpus recupera a família Ações Autônomas de Impugnação 5476, pai do oficial 5477. Corrige a sugestão Inquérito Policial do controle.
- Q0061: falta grave e execução criminal apontam para 4703 e 6734. Ambos receberam apoio de contexto 0.2671938126 e de alternativas 0.1268032721; a média ponderada é 0.2110375964 para ambos. Não há informação discriminante nesses vetores para resolver o empate. Permanece a decisão do controle. Esses valores são similaridades, não probabilidades.
- Q0005: em relação ao crime de furto qualificado aciona Furto/Penais Patrimoniais, mas a referência central é Teoria da Pena 5199. A expressão se refere ao crime que contextualiza a análise da pena/reincidência. As variantes com prioridade à relação publicam um erro; a de título único não sobrepõe a decisão pois há vários candidatos no enunciado completo.
- Q0252: estelionato aparece no contexto de condenação; a pergunta e as alternativas tratam de consequências da pena. A regra direta publica Patrimônio 5157, mas a referência é fora. Esse é o único erro nas 36 publicadas pela variante de título único. Não foi excluído do cálculo.
- Q0291: a regra reconhece candidatos ligados a tráfico e inquérito. Não os considera homônimos da mesma expressão para desempate automático. Permanece em revisão, sem consultar seu rótulo fora.
- Q0508 (sem rótulo): interceptação das comunicações telefônicas aponta para 4700 e a família 5543. A comparação favorece 4700 e a variante de desambiguação publica experimentalmente. Como as alternativas são Certo/Errado, não forneceram apoio temático; a diferença veio do contexto. Não há confirmação oficial do enquadramento.
- Q0638 (sem rótulo): Conduta deixou de acionar o tema Fato Típico na segunda rodada; sem outro identificador preparado, mantém o controle. A citação de uma prática precisa de descrição temática mais específica, não de um atalho pela palavra conduta.

## Confiança e limites

A decisão de publicar diretamente é a hipótese que este experimento mede; não foi condicionada a confiança artificial de 80%. Para permitir inspeção, a confiança da regra é uma taxa agregada suavizada Beta(1,1). Nas 100, usa os acionamentos dos outros folds, excluindo textos normalizados duplicados do item avaliado. Nas 559, usa os acionamentos das 100: 25/27 = 92,59% na variante de título único e 25/28 = 89,29% nas duas de relações. Não é probabilidade individual comprovada, certificação jurídica ou garantia populacional. As previsões de fallback conservam as confianças do controle.

Esta avaliação mostra que a identificação direta tem potencial, mas o encerramento automático por qualquer marcador não funciona de maneira geral. A prioridade recomendada para estudo é confirmar que o identificador se refere à cobrança e medir regras por tipos de formulação. O refinamento deve ser validado com questões novas rotuladas, preservando os erros atuais no histórico.

## Execução

Python 3.12 e as dependências de experimento_folha_v2/requirements.txt. Execute dentro desta pasta:

```bash
python3 -m unittest discover -s experimento_relacoes_v9/tests -v
python3 testar_relacoes_v9.py --saida experimentos/relacoes_v9_reproduzida
python3 classificar_relacoes_v9.py --variante titulos_diretos --saida classificacao_v9_reproduzida
```

Use pastas de saída novas. O primeiro comando testa as regras. O segundo avalia as 100 e simula as 559; somente o avaliador consulta a folha-verdade. O terceiro faz inferência a partir do JSONL, catálogo e artefatos congelados, sem consultar rótulos, sem retreinar e sem chamar modelo de linguagem. Pode receber --questoes caminho/novas_questoes.jsonl; não consulta previsões salvas por ID. Nos casos resolvidos pela regra, pula o cálculo de compatibilidade/confiança v8. As métricas desta comparação não são uma medição de latência de produção.

O teste de reprodução das 559 executou a inferência bloqueando a função de carregamento de rótulos e abertura de conexão: tema, decisão e confiança corresponderam aos registros simulados.

## Arquivos para inspeção

- experimento_relacoes_v9/regras.py: regras e parâmetros.
- experimento_relacoes_v9/artefato_regra.json: estatística agregada da regra, sem rótulos por ID.
- experimentos/relacoes_v9_002/protocolo_previo.json: configuração e hashes registrados antes da rodada 2.
- experimentos/relacoes_v9_002/avaliacao_100.csv: previsões, referência e comparação por questão.
- experimentos/relacoes_v9_002/simulacao_559.csv: previsões experimentais sem precisão inventada.
- experimentos/relacoes_v9_002/rastros_659.json: títulos, expressões, alternativas e comparação de candidatos.
- experimentos/relacoes_v9_002/erros_regras_100.json: todos os erros acionados pelas regras com questão completa.

O README/relatório v8 anterior está em historico/v8_antes_relacoes_v9. Os dados e modelos anteriores foram preservados.
