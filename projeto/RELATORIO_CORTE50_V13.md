# V13 — teste de publicação a partir de 50%

**Conclusão: rejeitar o corte de 50% para a entrega.** Ele aumenta o número de publicações, mas a precisão observada fica entre 74,47% e 76,09% nas seis variantes. Nenhuma alcança os 95% exigidos pelo case. As políticas V11/V12 e os arquivos históricos não foram substituídos.

## O que foi alterado

Somente a decisão de revisões elegíveis com confiança maior ou igual a 0,5. Publicações anteriores e eventuais decisões fora são preservadas. Tema, extras, sinal e confiança não são modificados; não houve retreino, recalibração, consulta a LLM nem ajuste por ID. Uma política interna V12 desativada deixa de impedir a publicação nessa hipótese: essa é precisamente a flexibilização em teste. A elegibilidade mínima de conteúdo continua valendo. Nos conjuntos reais desta rodada, não há publicações prévias abaixo de 50%.

O corte foi especificado pelo candidato antes de verificar estes resultados. Os 100 itens e rótulos já foram reutilizados no desenvolvimento; esta comparação é descritiva e pareada sobre as probabilidades OOF salvas, não uma nova avaliação independente. As 559 não têm rótulos disponíveis.

## Resultado nas 100 — avaliação por grupos

| Sistema | Publicadas antes | Precisão antes | Publicadas com 50% | Acertos | Erros | Precisão com 50% | Novos acertos | Novos erros |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V11 atual | 40 | 97.50% | 93 | 70 | 23 | 75.27% | 31 | 22 |
| Vantagem lexical | 44 | 95.45% | 93 | 70 | 23 | 75.27% | 28 | 21 |
| Foco lexical | 40 | 97.50% | 93 | 70 | 23 | 75.27% | 31 | 22 |
| Alternativas condicionais | 40 | 97.50% | 94 | 70 | 24 | 74.47% | 31 | 23 |
| Regularização C=0,3 | 44 | 95.45% | 92 | 70 | 22 | 76.09% | 28 | 20 |
| V12 combinado | 45 | 95.56% | 92 | 70 | 22 | 76.09% | 27 | 20 |

Na V11, as 53 publicações adicionais contêm 31 acertos e 22 erros: 58,49% de precisão apenas nos acréscimos. Na V12 combinada, as 47 adicionais contêm 27 acertos e 20 erros: 57,45% nos acréscimos. A cobertura maior foi obtida aceitando muitas sugestões de tema erradas; o corte não conserta o ranking.

## Simulação sem rótulo

| Sistema | Publicadas antes nas 559 | Com 50% | Revisar com 50% | Cobertura com 50% | Publicadas nos 300 recentes |
|---|---:|---:|---:|---:|---:|
| V11 atual | 361 | 429 | 130 | 76.74% | 231 |
| Vantagem lexical | 365 | 430 | 129 | 76.92% | 234 |
| Foco lexical | 361 | 439 | 120 | 78.53% | 238 |
| Alternativas condicionais | 361 | 429 | 130 | 76.74% | 231 |
| Regularização C=0,3 | 362 | 429 | 130 | 76.74% | 230 |
| V12 combinado | 365 | 435 | 124 | 77.82% | 236 |

Os 435 itens publicados pela V12 combinada correspondem a 77,82% das 559. Esse número é cobertura, não precisão. Não se pode atribuir 76,09% de precisão real às 559: esse valor foi observado nas 100 antigas, e pode mudar nas 300 recentes. O resultado observado já basta para não recomendar o corte de 50% neste sistema.

## Exemplos de sugestões erradas liberadas pelo corte

| Questão | Confiança V12 combinada | Sugestão errada | Referência temática |
|---|---:|---|---|
| Q0061 | 67,20% | Lei de Execução Penal no ramo Processo Penal (6734) | Lei de Execução Penal no ramo Legislação Especial (4703) |
| Q0202 | 72,58% | Crimes Contra a Dignidade Sexual (5102) | Erro de Tipo (5224) |

Q0319 também é publicada com o corte de 50%, mas já havia sido liberada incorretamente pela combinação V12; por isso não conta como erro novo em relação a essa combinação. Na comparação com a V11, sua publicação é nova e errada. Q0058 e Q0320 continuam abaixo de 50% e em revisão; isso não torna confiáveis as demais sugestões que superaram o corte.

## Decisão e próximo problema

Não adotar 50%. Preservar a referência anterior. As melhorias lexicais V12 deram ganho modesto, com um erro adicional; baixar o corte ampliou fortemente os erros. O próximo estudo útil é corrigir a recuperação e a desambiguação dos temas com critérios gerais, mantendo avaliação separada e sem exceções por ID. Não aumentar manualmente as confianças das sugestões para atingir percentuais desejados.

## Reproduzir

Execute dentro da pasta do projeto:
```bash
python3 -m unittest discover -s experimento_corte50_v13/tests -v
python3 experimento_corte50_v13/avaliar.py --saida experimentos/corte50_v13_local
```

O comando lê os resultados V12 já congelados. Gera protocolo, resumo, avaliação das 100 e simulação das 559; não faz nova inferência. `aplicar()` pode receber linhas com tema/confiança/elegibilidade sem rótulos; `correto` só é consultado em `medidas()` para avaliar registros rotulados. Não substitui publicacao.csv nem previsao.txt.

Arquivos principais: experimentos/corte50_v13_001/resumo.json, avaliacao_100_corte50.csv, simulacao_559_corte50.csv e protocolo_previo.json. As oito verificações cobrem o limite exato de 50%, elegibilidade, preservação de saídas anteriores, contagem de erros, confiança inválida, repetição de IDs, precisão indefinida sem publicações, proteção de saída e ausência de rede.

