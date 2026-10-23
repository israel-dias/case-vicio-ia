# Simplificação aplicada na v5

A v5 usa a candidata `sem_formato`, escolhida no experimento anterior ao exame do volume de publicações nas 559. Os parâmetros foram transferidos exatamente do artefato documentado, sem bônus manual de confiança ou exceções por questão.

## Alterações

| Componente | Tratamento |
|---|---|
| Indicador de Certo/Errado | Retirado como atributo preditivo independente |
| Indicador de assertivas I/II/III | Retirado como atributo preditivo independente |
| Número de alternativas | Retirado como atributo preditivo independente |
| Textos do enunciado, comando e alternativas | Preservados |
| Tratamento textual de Certo/Errado | Preservado: as palavras “Certo” e “Errado” não informam por si só o assunto |
| Origem e assunto de origem | Continuam auxiliares, sem veto independente |
| Referências normativas | Preservadas como atributos; remoção completa piorou a precisão observada |
| Alertas de mapeamento e origem | Explicações informativas; não acrescentam bloqueio à política |
| Tema proposto | Mesmo primeiro candidato da busca v3 |
| Extras e fora | Sem inferência automática nesta candidata |

O código calcula a representação de conteúdo compartilhada com a v3, seleciona somente 36 das 39 colunas e utiliza o modelo treinado para essas 36. O novo teste altera apenas as três colunas retiradas e confirma que elas não afetam a predição.

## Política

O corte anterior era 0,8353632589. O novo corte, 0,7738553900, foi escolhido após novo treinamento e calibração no experimento de remoção de atributos. Não se trata de aceitar similaridade de 77% como prova de acerto jurídico. É um parâmetro de seleção aprendido para procurar a meta empírica no conjunto publicado.

Na comparação por cinco grupos externos e quatro internos, com rótulos externos fora do ajuste, a candidata publicou 25/100 e acertou 24: 96% observados. O controle publicou 23/100 e acertou 22: 95,65%. Os dados e hipóteses já eram conhecidos; a diferença é pequena e não demonstra superioridade estatística nem garante a meta nas 559.

O ajuste final usa os 100 rótulos, e o corte final tem 41 acertos em 43 selecionadas nos sinais de desenvolvimento fora do treino. Esse número serve ao ajuste; não substitui os 24/25 da comparação por grupos.

## Resultado nas 559 avaliadas

| Decisão | V3 | V5 |
|---|---:|---:|
| publicar | 175 | 231 |
| revisar | 384 | 328 |
| fora | 0 | 0 |
| cobertura | 31,31% | 41,32% |

Houve 57 passagens de revisar para publicar e uma de publicar para revisar: ganho líquido de 56 publicações. Nenhum tema central foi alterado. As 559 decisões e probabilidades coincidem com a simulação `sem_formato` registrada antes desta promoção.

A previsão de precisão é 90,44%, média das probabilidades das publicadas fora da folha-verdade. A previsão anterior era 92,90%. Ampliar o conjunto publicado incluiu sugestões menos confiáveis e não demonstrou aumento da precisão. O acerto real das 559 e o cumprimento de 95% continuam desconhecidos.

## Por que não flexibilizar tudo

Na mesma comparação, retirar todos os sinais normativos produziu 22 acertos em 24 publicadas: 91,67%, incluindo publicação indevida de um item fora da taxonomia. A versão reduzida de 39 para 10 atributos publicou somente quatro exemplos. Não adotamos essas alternativas.

As sugestões atuais, mantidas em toda esta auditoria, acertam 66/100 antes da abstenção. Há 44 sugestões corretas entre as revisões do controle, mas também 33 incorretas. Portanto, reduzir revisões desnecessárias exige separar esses casos; aumentar todas as probabilidades não corrige os temas inadequados.

O passo seguinte para ganhos maiores é melhorar a representação do conteúdo cobrado e a comparação entre candidatos, com avaliação e sem respostas ou decisões de um LLM sobre as questões avaliadas.

## Conferir

- `flexivel_v5/runtime.py`: classificação congelada, sem rótulos ou rede.
- `preparar_flexivel_v5.py`: criação do artefato a partir do experimento íntegro.
- `experimentos/auditoria_confianca_v4_002`: comparação que fundamentou a mudança.
- `entrega_flexivel_v5/comparacao_com_v3.json`: transições das 559.
- `entrega_flexivel_v5/rastreabilidade.jsonl`: atributos e notas por questão.
- `historico/v3_antes_flexibilizacao`: CSV, previsão e documentos anteriores.
