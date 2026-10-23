# Experimento V16 — resultado, limites e próxima hipótese

**A atualização isolada não melhorou a V15.** A melhor configuração elegível da primeira rodada, escolhida na referência antes de classificar as 559, publicou 382/559. Depois, uma análise adaptativa preservou a versão atual V15 e usou a busca nova apenas como suplemento: 394/559, duas publicações adicionais. As 300 recentes permaneceram com 218 publicações.

Nenhum resultado foi transformado em entrega oficial. As 100 referências não entram nos totais das 559; continuam necessárias ao treino, à calibração e à avaliação de desenvolvimento. Seus rótulos e vários erros foram vistos repetidamente nesta conversa. Não há teste externo cego e a precisão das 559 continua desconhecida.

## O que foi implementado

1. **Normalização condicional dos campos.** Alternativas C/E e blocos I/II/III ausentes são marcados como não aplicáveis. Média e escala são estimadas apenas onde o campo se aplica. Na entrada do modelo, um campo não aplicável recebe valor padronizado zero. Não se zeram pesos negativos ou se inventa confiança.
2. **Catálogo organizado para BM25 hierárquico.** Usa títulos e descrições já preparados, associando cada documento à sua família. O IDF é calculado por família para não tratar subtemas repetidos como evidência independente. Todos os IDs são preservados. O preparador recebe apenas o catálogo; não consulta questões ou rótulos. Não inventa diferenças de escopo entre homônimos.
3. **Busca em várias vistas.** Conjunto, enunciado, comando, trecho final, trechos dos marcadores de relação, alternativas temáticas e todos os itens. Nenhuma vista resolve gabaritos ou elimina automaticamente o contexto. O conjunto completo permanece disponível.
4. **Comparador clássico com candidatos próximos.** A busca fixa e a reordenação treinada usam uma união dos sete primeiros candidatos de três recuperadores. O treino inclui também os temas aceitos da referência, apenas nos dados de ajuste. A reordenação só usa os candidatos disponíveis na inferência.
5. **Origens neutralizadas nos atributos novos.** Os testes detectaram que a busca legada podia variar com metadados de origem. Esses campos foram neutralizados na nova representação, pois podem estar errados. Apenas a preservação histórica continua usando o comportamento legado.
6. **Preservação com guarda.** Foram testados vetos por homônimo não resolvido e por dois comparadores fortes sugerirem o mesmo outro ramo. A guarda foi medida separadamente, sem afirmar que discordância prova erro.

As variantes foram declaradas antes do estudo. Os mesmos cinco folds externos e quatro internos foram mantidos, com agrupamento de duplicatas. O ajuste de cada fold e sua calibração não recebem os rótulos do fold avaliado. Esse isolamento não apaga a exposição histórica aos 100 rótulos.

## Resultado nas 559, excluindo as 100

| Configuração | Publicar | Revisar | Cobertura | Publicadas nas 300 recentes |
|---|---:|---:|---:|---:|
| V15 anterior | 392 | 167 | 70,13% | 218 |
| V16 condicional a 70%, preservando V11 | 382 | 177 | 68,34% | 212 |
| Busca multivista a 70%, preservando V11 | 383 | 176 | 68,52% | 208 |
| Reordenação multivista a 70%, preservando V11 | 372 | 187 | 66,55% | 201 |
| V16 condicional a 70%, preservando V11 com guarda | 345 | 214 | 61,72% | 190 |
| **V15 + busca V16 calibrada** | **394** | **165** | **70,48%** | **218** |
| V15 + busca V16 a 70% | 407 | 152 | 72,81% | 222 |

A última linha publica mais, mas foi rejeitada: obteve apenas 50 acertos em 55 publicações na referência exposta (90,91%). O volume das 559 não foi usado para escolher uma configuração mais permissiva.

No suplemento escolhido, as 259 antigas fora da referência ficam com 176 publicações e 83 revisões (67,95%). Nas 300 recentes são 218 publicações e 82 revisões (72,67%). Não há exclusão automática por baixa similaridade. Nenhuma dessas contagens mede acerto jurídico.

## Por que a primeira rodada não foi adotada

A normalização condicional e a nova calibração mantiveram 47/49 publicações corretas nas 100 de desenvolvimento, mas reduziram o volume das 559. Não foi apenas retirar uma pequena contribuição de um modelo fixo: os pesos e o calibrador foram reaprendidos. Por isso, as confianças podem mudar em toda a distribuição.

A busca multivista acertou 69/100 primeiros temas sem preservação, contra 61/100 do foco isolado. Contudo, a fusão V15 anterior já acertava 72/100: a busca nova **não superou o melhor recuperador anterior**. A reordenação treinada ficou em 66/100. Melhorar em relação a um controle mais fraco não basta para declarar avanço global.

Preservando V11, a busca multivista a 70% teve 46/51 publicações corretas (90,20%); a reordenação teve 44/49 (89,80%). A guarda retirou um acerto e nenhum erro dessas duas variantes na referência, mantendo a precisão abaixo da meta. Nas 559, seus vetos também reduzem muito a cobertura, mas não sabemos quantos retiram erros ou acertos. **Não foi adotada como regra geral.**

Os resultados completos das 18 configurações estão em `experimentos/multivista_v16_001/resumo.json` e no CSV correspondente. A primeira seleção, anterior às previsões das 559, foi `condicional_v15/70/preservar_v11`. Seu campo `cumpre_comparacao_v15` inclui uma condição adicional conservadora de não aumentar o número absoluto de erros; essa condição é um diagnóstico extra, não a régua do case, que usa a fração de acertos. A escolha principal entre candidatos continua usando precisão empírica >=95% e cobertura na referência.

## Comparação adicional: manter a V15 atual

A primeira rodada preservava apenas V11. Isso permitia perder publicações que a V15 já acrescentara. A análise seguinte preservou a V15 completa, mantendo também seus erros, e comparou os suplementos congelados. Nenhum tema foi escolhido manualmente por ID e nenhum modelo foi retreinado nessa composição.

É uma análise **posterior aos primeiros resultados**: os volumes individuais das 559 já eram conhecidos. A escolha entre composições foi registrada usando as 100 antes de compor os totais de união das 559. Isso é transparente, mas não constitui seleção cega ou avaliação independente.

| Referência de desenvolvimento | Corretas/publicadas | Precisão empírica |
|---|---:|---:|
| V15 anterior | 47/49 | 95,92% |
| V15 + busca V16 calibrada | 48/50 | 96,00% |

O novo acerto de desenvolvimento é Q0179, cujo rótulo fornecido é 4368. Essa linha não entra na avaliação das 559. Nas 559, as duas adições são Q0095 e Q0256; seu acerto é desconhecido. Nenhuma publicação V15 foi retirada pela composição escolhida.

Os dados completos das 12 composições estão em `experimentos/ampliacao_v15_v16_002`. A composição inicial equivalente foi preservada em `_001`. A fonte de análise é `ampliar_multivista_v16.py`; a inferência real é `classificar_ampliacao_v16.py`. Este último recalcula as decisões em textos novos, inclusive com IDs nunca vistos, usando modelos congelados — não consulta os CSVs de previsões para responder por ID.

## O que esse teste permite concluir

- As mudanças foram implementadas e os resultados negativos ficaram preservados.
- O ganho final é **marginal: duas questões nas 559 e nenhuma nas 300 recentes**. Não deve ser vendido como solução do problema de cobertura.
- Os 96% pertencem às 50 publicações da referência exposta, não às 394 publicações sem rótulo. A precisão real continua não medida.
- A árvore continua com homônimos cujo escopo específico da empresa não é inferível apenas por títulos e descrições compartilhadas.
- Procurar indefinidamente pesos e cortes no mesmo conjunto pode adaptar o sistema à referência sem melhorar dados novos.

## Próximo teste recomendado

Separar recuperação de candidatos e decisão de confiança. Comparar o melhor recuperador já existente com um comparador de compatibilidade estável, em vez de mudar simultaneamente busca, atributos, seleção de negativos e calibração. A V16 mostrou que o comparador novo não superou os controles; isso justifica uma ablação mais isolada.

Também é necessário avaliar novas referências, especialmente dos itens recentes, para medir generalização. Se não houver rótulos adicionais disponíveis no prazo do case, o relatório deve assumir essa limitação. Nenhuma mudança no corte, por si só, comprova o requisito de 95%.

O pacote contém reprodução por código, testes de leitura/máscara/preservação e registros por questão. Testes técnicos não certificam acerto jurídico. A entrega oficial continua exigindo 659 linhas, embora as 100 referências não entrem nos totais de avaliação.
