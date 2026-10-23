# Investigação V19–V23: resultados e decisão

## Resultado principal

As novas tentativas não superaram a composição experimental V18 de suplemento dos comandos literais. Ela conserva **395 publicadas / 559 (70,66%)**, 164 revisões e zero fora. Nas 300 recentes, são 218 publicadas / 300 (72,67%). Nas referências expostas, publicou 52 e acertou 50 (**96,15%**). A composição V16 anterior tinha 394 publicadas / 559 e 48 corretas / 50 publicadas nas referências.

Esses 96,15% não são a precisão das 559, não são um teste cego e não comprovam mínimo populacional de 95%. A composição das rotas também não possui uma calibração global independente. Os 395 itens são a melhor cobertura observada entre essas composições com esse resultado de desenvolvimento; não demonstramos um máximo possível nem promovemos uma nova entrega formal.

## O que foi aplicado

1. **Expressões do catálogo (V19):** reconhecimento de títulos completos, trechos dos escopos e vocábulos distintivos. Ganhos pontuais vieram acompanhados de regressões por contexto e distratores. Não promovido.
2. **Contexto e intensidade (V20):** palavras ambíguas deixam de ser âncoras isoladas; comando, proposições e alternativas têm papéis diferentes; sinais fracos não são normalizados automaticamente para 1; homônimos conservam IDs próprios. Corrigiu as regressões Q0052, Q0058 e Q0315 em relação à V19, mas não melhorou globalmente o controle V18.
3. **E5 preparado (V21):** embeddings multilíngues de 659 questões e 371 nós utilizáveis, preparados sem rótulos. Comparação query/query, query/passage, TF-IDF, caracteres, BM25 e comparador clássico. O melhor comparador acertou 75 temas/100, mas não encontrou uma política de publicação com suporte interno suficiente. Sem promoção.
4. **Apoio contextual semântico (V22):** acrescenta cinco medidas semânticas aos 27 atributos contextuais. Testa manter o tema, reordenar com proteção de comando/ramo e reordenar livremente. O apoio manteve 74 temas corretos/100 e teve 26/27 publicações corretas, mas reduziu demais a cobertura.
5. **Confiança direta (V23):** estima o acerto do candidato por margens e apoios semânticos, sem mudar o tema. As variantes ficaram em 89,29% e 90% de precisão nas publicadas das referências. Não substituem a confiança anterior.

Nenhuma dessas versões usa LLM para escolher o tema ou resolver a questão. O encoder E5 participa somente da preparação versionada. Na inferência, os vetores são recuperados pelo hash do conteúdo, não por uma tabela de respostas associada ao ID. Alterar o texto de um ID conhecido exige nova preparação, em vez de reutilizar silenciosamente o vetor antigo.

## Comparação resumida

| Sistema | Temas aceitos /100 | Corretas/publicadas nas referências | Publicadas /559 | Publicadas /300 recentes |
|---|---:|---:|---:|---:|
| Composição V16 preservada | 70 | 48/50 (96%) | 394 | 218 |
| Suplemento de comando literal V18 | 73 | 50/52 (96,15%) | **395** | **218** |
| Controle contextual V18/V22 | 74 | 36/39 (92,31%) | 139 | 79 |
| E5 como apoio V22 | 74 | 26/27 (96,30%) | 111 | 66 |
| Reordenação com contexto V22 | 72 | 21/22 (95,45%) | 113 | 67 |
| Comparador E5 V21 | 75 | 0/0 (indefinida) | 0 | 0 |
| Confiança direta por margens V23 | 74 | 25/28 (89,29%) | 94 | 54 |
| Confiança direta com seis evidências V23 | 74 | 9/10 (90%) | 87 | 49 |

Os controles, classificadores e composições são diferentes; acertar mais sugestões no total não significa selecionar melhor o subconjunto publicado. As mesmas 100 questões são reutilizadas: as linhas não são amostras independentes. Uma união descritiva de rotas pode aumentar a quantidade e somar erros; não foi ativada como política.

## Diagnóstico que muda a estratégia

- Há **109 famílias ativas**, das quais **64 não têm exemplo central/extra** nas referências. Entre as representadas, **18 têm apenas um exemplo**. O aprendizado por tema tem pouco suporte.
- O controle contextual erra 26/100 sugestões. Oito são referências fora; entre os **18 erros com tema**, **17 têm algum tema aceito no top5**. O principal gargalo restante desse controle está na ordenação e no escopo/convenção, não na ausência generalizada do tema na busca.
- A questão ter um tema reconhecível não torna qualquer ramo homônimo equivalente. A posição do trecho no comando ou no contexto ajuda, mas não elimina essa diferença.
- A ausência de um tema aceito no catálogo não pode ser aprendida só por baixa similaridade. Os exemplos fora exigem esclarecimento do recorte. Não inferimos regras como “pobreza → fora”.

O [caderno dos 26 erros conhecidos](pesquisa_v21/CADERNO_ERROS_CONHECIDOS.md) contém enunciado, comando, todas as alternativas, previsão, referência e cinco candidatos. Não inclui gabaritos inventados nem chama de erradas as sugestões das 559 sem rótulos.

## Exemplos concretos de nuances

- **Q0315:** “trânsito em julgado” apoiou indevidamente Crimes de Trânsito. A correção combina expressão e papel textual; apagar somente a palavra não bastou.
- **Q0058:** uma alternativa sobre internação e medidas de segurança deslocou uma previsão inicialmente aceita. O marcador isolado de uma alternativa não deve apagar a delimitação da pergunta.
- **Q0052:** a narrativa menciona regime fechado, mas as proposições tratam de remição. O regime não deve dominar automaticamente a classificação.
- **Q0274:** a flexão consumado/tentativa recuperou Iter Criminis, pai aceito do central oficial. Continua em revisão na rota própria: um acerto conhecido não autoriza impor confiança alta.
- **Q0208:** o comando trata de autor e partícipe, apesar da narrativa de homicídio. Preservar uma cobrança explícita evita alguns deslocamentos semânticos; a proteção também pode manter um erro inicial, razão pela qual foi avaliada, não presumida correta.

## Verificação e limites

Os novos testes verificam preservação de proposições e negação, comandos específicos, títulos ambíguos, alteração do conteúdo com ID mantido, independência de metadados/ID, hash dos artefatos e separação entre preparação e decisão. Aprovar testes de software não mede acerto jurídico.

A V21 teve as seis variantes reproduzidas exatamente nas 559: **3.354 previsões**, com rede, rótulos, treino, avaliador e recalibração bloqueados, sem importar encoder. A V22 completou a inferência das quatro variantes nas 559 com os mesmos bloqueios; houve retomada após interrupção, preservando modelos e escolhas anteriores. A prova adicional de V22/V23 usa uma amostra determinística, cujo tamanho e escopo estão no arquivo de verificação; não é uma nova avaliação jurídica independente.

A primeira execução V23 tentou consumir o resultado V22 antes de sua conclusão. O código agora verifica a conclusão antes de iniciar. O registro parcial `qualidade_v23_001` está marcado como incompleto e preservado como histórico; os resultados concluídos vêm de `qualidade_v23_002`. As tentativas negativas não foram apagadas para melhorar a aparência do resultado.

Na V23, os candidatos do controle são não supervisionados e iguais ao controle anterior nas 100. Os filtros de elegibilidade herdados vêm dos folds anteriores; a etapa de qualidade é um diagnóstico adicional adaptativo, não uma nova comprovação totalmente isolada. Esse limite reforça a decisão de não a promover.

## Custo, tempo e próximos dados necessários

O custo executado de API foi **US$ 0**. E5 foi executado localmente em CPU, com modelo quantizado de aproximadamente 118 MB e tokenizer de aproximadamente 17 MB; pesos não estão no ZIP. A preparação levou aproximadamente 58 segundos neste ambiente, e a inferência V21 nas 559, aproximadamente 15 segundos. Esses números não são promessa de latência no computador do candidato nem medição ponta a ponta de produção.

Os novos dados mais úteis seriam uma amostra recente com rótulos independentes, escopos aprovados dos homônimos e razões para os oito fora. Isso permitiria selecionar e validar uma política nova. Continuar alterando palavras ou reduzindo cortes com base nas mesmas 100 pode melhorar o ajuste aparente sem melhorar as questões avaliadas.

[Fontes primárias e decisões de pesquisa](pesquisa_v21/FONTES_E_DECISOES.md).
