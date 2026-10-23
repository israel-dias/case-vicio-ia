# Auditoria da confiança — experimento v4

Objetivo: verificar se os sinais atuais ajudam a separar acertos e erros ou apenas tornam a publicação conservadora. A entrega v3 foi preservada. Não foram respondidas nem rotuladas manualmente as 559 questões avaliadas.

## O que efetivamente decide

Os alertas são produzidos depois da decisão. Eles não subtraem pontos fixos. A confiança vem de regressão logística e calibração. Remover o texto de um alerta não muda a decisão. Os atributos correspondentes podem ter pesos positivos ou negativos aprendidos.

## Comparação com novo treino e calibração

Mesmos cinco grupos externos e quatro internos da v3. Em cada grupo, os rótulos externos não entram no treino, calibração, escolha do corte ou seleção da variante. Todos os métodos mantêm as mesmas sugestões de tema. Os 100 rótulos foram vistos anteriormente: este é desenvolvimento comparativo reutilizado, sem avaliação externa nova.

| Variante | Atributos | Publicadas/100 | Corretas | Precisão observada | Brier |
|---|---:|---:|---:|---:|---:|
| controle_v3 | 39 | 23 | 22 | 95.65% | 0.1676 |
| sem_citacao_ausente | 38 | 22 | 21 | 95.45% | 0.1679 |
| sem_metadados | 36 | 25 | 24 | 96.00% | 0.1742 |
| sem_formato | 36 | 25 | 24 | 96.00% | 0.1671 |
| sem_apoio_duplo | 37 | 23 | 22 | 95.65% | 0.1693 |
| sem_sinais_normativos | 30 | 24 | 22 | 91.67% | 0.1730 |
| sem_origem_formato_apoio | 31 | 17 | 17 | 100.00% | 0.1746 |
| evidencias_enxutas | 10 | 4 | 4 | 100.00% | 0.1881 |
| direto_top1_enxuto | 10 | 16 | 13 | 81.25% | 0.1893 |
| selecao_interna | seleção entre variantes | 40 | 38 | 95.00% | 0.1578 |

As sugestões atuais acertam 66/100 antes da abstenção. Mantendo essas sugestões, mesmo um seletor que soubesse exatamente quais estão corretas publicaria no máximo 69/100 sob a meta empírica de 95%. Aumentar somente as probabilidades não corrige as sugestões erradas.

## Simulação nas 559 — acerto desconhecido

A variante escolhida pelo suporte dos 100 sinais OOF, antes de observar o volume nas 559, foi `sem_formato`. Essa é uma escolha exploratória; não substitui uma nova avaliação independente.

| Variante | Publicar | Revisar | Cobertura | Precisão real |
|---|---:|---:|---:|---|
| controle_v3 | 175 | 384 | 31.31% | desconhecida |
| sem_citacao_ausente | 175 | 384 | 31.31% | desconhecida |
| sem_metadados | 197 | 362 | 35.24% | desconhecida |
| sem_formato | 231 | 328 | 41.32% | desconhecida |
| sem_apoio_duplo | 231 | 328 | 41.32% | desconhecida |
| sem_sinais_normativos | 117 | 442 | 20.93% | desconhecida |
| sem_origem_formato_apoio | 189 | 370 | 33.81% | desconhecida |
| evidencias_enxutas | 167 | 392 | 29.87% | desconhecida |
| direto_top1_enxuto | 53 | 506 | 9.48% | desconhecida |

## Diagnóstico dos pesos

O sinal isolado de um coeficiente não demonstra que ele seja necessário, dispensável ou juridicamente correto. As contribuições abaixo são relativas à centralização usada no treino e estão na escala de logit, não em pontos percentuais de confiança. A remoção de atributos foi avaliada com novo ajuste para evitar interpretar uma perturbação artificial do modelo como melhora real.

| Atributo | Peso final padronizado | Folds com peso positivo | Folds com peso negativo |
|---|---:|---:|---:|
| palavra_completo | -2.0314 | 0 | 5 |
| palavra_assunto_origem | -0.4567 | 0 | 5 |
| apoio_enunciado_e_alternativas | -0.4337 | 0 | 5 |
| origem_compativel | +1.4075 | 5 | 0 |
| origem_reconhecida | +0.3562 | 4 | 1 |
| certo_errado | -1.2028 | 0 | 5 |
| assertivas_numeradas | +0.3517 | 5 | 0 |
| numero_alternativas | -1.4129 | 1 | 4 |
| escopo_enunciado | -0.3561 | 0 | 5 |
| citacao_sem_correspondencia | +0.0567 | 4 | 1 |
| evidencia_escopo_enunciado_alt | +0.0568 | 2 | 3 |

Foram encontrados 11 pares de atributos com correlação absoluta de pelo menos 0,85 entre os primeiros candidatos dos 100 exemplos. Isso sinaliza redundância, sem provar por si só que remover o par melhorará a classificação.

## Casos exibidos na conversa

Estes registros servem apenas para entender a mecânica. Não foram usados como gabarito, exceção por ID ou condição de escolha. Não representam correção jurídica independente.

### Q0458 — confiança original 83.30%
Penal > Teoria do Crime: Fato Típico

Maiores contribuições negativas ao logit calibrado: palavra_completo (-2.112), escopo_alternativa_max (-0.692), escopo_alternativas (-0.672), palavra_alternativas (-0.628), apoio_enunciado_e_alternativas (-0.506).

### Q0492 — confiança original 44.79%
Penal > Concurso de Crimes

Maiores contribuições negativas ao logit calibrado: palavra_completo (-1.701), palavra_alternativas (-0.755), escopo_alternativa_max (-0.392), escopo_alternativas (-0.347), numero_alternativas (-0.186).

### Q0496 — confiança original 36.07%
Penal > Punibilidade

Maiores contribuições negativas ao logit calibrado: palavra_completo (-1.070), escopo_alternativas (-0.603), escopo_alternativa_max (-0.586), lei_literal (-0.568), apoio_enunciado_e_alternativas (-0.406).

### Q0523 — confiança original 41.15%
Penal > Punibilidade

Maiores contribuições negativas ao logit calibrado: palavra_completo (-1.159), certo_errado (-0.691), escopo_enunciado (-0.370), origem_compativel (-0.214), palavra_alt_max (-0.152).

### Q0568 — confiança original 60.71%
Penal > Lei Penal no Tempo e no Espaço

Maiores contribuições negativas ao logit calibrado: palavra_completo (-4.524), escopo_enunciado (-0.742), escopo_alternativa_max (-0.314), escopo_alternativas (-0.296), numero_alternativas (-0.186).

## Como interpretar e próximos passos

Retirar um grupo só é uma melhoria demonstrada nesta amostra se conservar a meta de precisão e melhorar a seleção ou a calibração. Ganhar publicações nas 559, sem seus rótulos, não demonstra qualidade. As tentativas que falham permanecem no relatório.

Não se promove automaticamente um método para a entrega e não se eleva a confiança à mão. As sugestões iniciais e a calibração são problemas distintos. Uma falha persistente na escolha do tema exige melhorar a recuperação ou comparação de candidatos, usando validação e exemplos rotulados adicionais, sem um LLM decidindo os temas avaliados.

Fontes metodológicas: documentação scikit-learn 1.8, interpretação de coeficientes: https://scikit-learn.org/1.8/auto_examples/inspection/plot_linear_model_coefficient_interpretation.html ; validação aninhada: https://scikit-learn.org/1.8/auto_examples/model_selection/plot_nested_cross_validation_iris.html
