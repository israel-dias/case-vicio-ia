# Calibração da publicação

O classificador de temas permaneceu fixo. O desenvolvimento propôs limiares de margem relativa; a calibração escolheu o de maior cobertura que atingiu a meta empírica de 95%, com pelo menos 5 publicações no desenvolvimento e 3 na calibração. Esses mínimos evitam selecionar com um único exemplo; não certificam precisão populacional.

Política ativa: **True**. Limiar: **0.6070580985325005**. Na calibração: **3/3** publicadas certas; cobertura **15.0%**. Precisão indefinida quando não há publicadas.

Confiança média suavizada do grupo publicar: **0.8000**. Intervalo binomial descritivo 95%: **[0.29240177382128674, 1.0]**. Ambos usam apenas os resultados da calibração. Ela também escolheu o limiar: há otimismo de seleção. A confirmação seguinte será no teste reservado.

Se nenhum limiar cumprir os critérios, a política se abstém de publicar. Baixa similaridade não prova que a questão está fora da árvore: a versão atual envia esses casos à revisão. Não há descarte automático.

Nenhuma previsão foi feita nas 20 questões de teste nem nas 559 sem rótulo. Não ajuste a representação ou a regra usando o resultado do teste sem registrar que ele deixou de ser reservado.

Intervalos: NIST, https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm . As hipóteses binomiais não resolvem mudança de distribuição ou exposição anterior aos rótulos.
