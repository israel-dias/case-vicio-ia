# Decisões e diagnóstico da versão 2

Este documento explica as decisões de engenharia. Não contém reclassificação jurídica feita pelo assistente. A precisão das 559 questões sem rótulos é desconhecida.

## Por que manter a compatibilidade fixa

Na CV de desenvolvimento: controle 19/21 publicadas corretas; compatibilidade fixa 20/20; seleção interna 19/20. A candidata fixa foi escolhida após observar a comparação. O resultado não é teste independente da escolha. O tema central da busca foi preservado: as 659 linhas mantêm o mesmo central da v1. Mudaram a confiança e a regra de publicar/revisar.

## O erro da seleção interna: Q0150

A referência oficial aceita 4708. A variante de reordenação escolheu 6728, outro ramo com o mesmo título, e publicou. A variante fixa preservou 4708. O caso foi identificado comparando as previsões calculadas com os rótulos oficiais; não houve alteração manual do ID dessa questão. Não foi criada equivalência global entre os dois ramos.

## Dois candidatos aceitos não exigem revisão automática

Na referência existem nove itens cujo primeiro e segundo candidatos lexicais são aceitos. Na CV, a Q0144 foi publicada mesmo com esses dois candidatos. Os demais ficaram abaixo do corte de compatibilidade do respectivo fold, não por uma proibição de ter dois temas. As políticas por fold são diferentes; as confianças abaixo não devem ser comparadas com o corte final único.

| ID | Decisão na CV fixa | Tema | Confiança na CV |
|---|---|---|---:|
| Q0040 | revisar | 5524 | 0.439545 |
| Q0068 | revisar | 5116 | 0.519576 |
| Q0144 | publicar | 5524 | 0.894482 |
| Q0221 | revisar | 5199 | 0.696141 |
| Q0240 | revisar | 5498 | 0.338237 |
| Q0251 | revisar | 5191 | 0.838485 |
| Q0265 | revisar | 5066 | 0.717998 |
| Q0279 | revisar | 5185 | 0.436621 |
| Q0341 | revisar | 5157 | 0.829723 |

## Casos oficiais fora

O controle publicou indevidamente Q0039 e Q0252 na CV; a variante fixa não publicou nenhum dos oito fora oficiais. Isso não demonstra que saiba excluir automaticamente novas questões. Por isso fora automático está desativado: baixa similaridade não basta para desaparecer uma questão. Não se inventou uma explicação jurídica para os rótulos de fora nem se alterou a folha oficial.

## Regra final e diferença para a CV

O modelo de compatibilidade foi ajustado nos 100 rótulos. O calibrador e o corte final usam seus sinais OOF. O corte 0,8257163701538247 selecionou 27 acertos em 28 registros de desenvolvimento. Esse é um ajuste final, distinto das políticas avaliadas fold a fold, que resultaram em 20/20. Não existe um novo teste externo desse ajuste final.

As 559 questões sem rótulo não participaram do treino, calibração ou escolha do corte. O modelo congelado gerou 152 publicações e 407 revisões nessas questões; a cobertura é 27,1914%. Nas 300 recentes, foram 89 publicações e 211 revisões. A precisão prevista das publicadas nas 559 é 90,3404%, abaixo da meta de 95%. A faixa de sensibilidade não transforma essa previsão em garantia.

## O que ainda limita o resultado

Poucos rótulos para muitos temas; descrições de escopo propostas sem validação jurídica independente; escolha de famílias amplas; ambiguidade entre ramos homônimos; apenas oito exemplos fora; seleção de métodos sobre dados já vistos; calibração com pouca informação; mudança de distribuição nas provas recentes. A melhora da cobertura não prova melhora de acerto nas 559.

A prioridade seguinte é uma amostra nova de rótulos independentes, além de esclarecer limites dos temas. Deve-se avaliar a calibração e a precisão seletiva antes de promover o sistema para produção, sem ajustar o método usando um teste que depois seja apresentado como cego.

## Como explicar ao gestor

A busca de escopos propõe o tema. Um modelo clássico aprende quais sinais sustentam esse enquadramento. Um calibrador estima a chance de acerto e uma regra decide quando abster. O professor corrige os conflitos relevantes e essas correções viram exemplos versionados. A IA ajudou a escrever e preparar; a decisão executável é do sistema.

A limpeza dos novos atributos de compatibilidade remove comentários HTML. A escolha do tema mantém a normalização legada da busca, para preservar o ranking avaliado. Unificar as duas limpezas exige um novo experimento antes de alterar a versão final.
