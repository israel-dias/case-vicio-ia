# V20 — contexto das expressões e confiança preservada

Esta rodada responde às perdas observadas na V19. Encontrar uma palavra ou uma expressão no texto não demonstra que ela é a cobrança. Mantemos a entrega formal e o controle composto V16 preservados; esta pasta reúne experimentos reproduzíveis.

## O que foi alterado

- **Palavras ambíguas.** Trânsito, fechado, aberto e internação, entre outros qualificadores, deixam de ser âncoras isoladas. Expressões completas continuam disponíveis: “crimes de trânsito” é diferente de “trânsito em julgado”; “regime fechado” não foi apagado do texto.
- **Fonte do sinal.** Um comando com identificador temático ganha prioridade na evidência. As alternativas contribuem por média e com peso limitado; uma menção isolada em um distrator perde força. Nas assertivas C/E, as alternativas não fornecem conteúdo temático. Todos os itens I/II e V/F são preservados; seus conteúdos têm prioridade na nova vista e o cabeçalho permanece como apoio. O texto integral continua sustentando o ranking anterior.
- **Intensidade da evidência.** Um apoio pequeno não é dividido por ele mesmo para virar 1. O novo peso só alcança 25% quando o apoio absoluto é máximo; não há confiança mínima automática.
- **Títulos homônimos.** Um vocábulo presente apenas em famílias de mesmo título pode apoiar cada uma delas. Os IDs e os caminhos continuam separados, sem desempate pela ordem do ID. Isso evita que um termo como remição seja ignorado apenas por aparecer em duas entradas homônimas de Execução Penal.

As regras são gerais, versionadas e não contêm exceções por ID de questão. Não resolvem alternativas nem consultam LLM. O conjunto de expressões provém dos títulos e escopos existentes; os escopos preparados não têm validação jurídica independente.

## Comparação nas 100 referências

| Opção | Tema aceito /100 | Corretas/publicadas | Precisão nas publicadas |
|---|---:|---:|---:|
| Controle V18 morfológico | 74 | 36/39 | 92,31% |
| Só proteger palavras ambíguas | 74 | 26/32 | 81,25% |
| Campos e intensidade absoluta | 74 | 13/16 | 81,25% |
| Campos, intensidade e escopos homônimos | 74 | 13/15 | 86,67% |
| Recuperação contextual com estimador anterior preservado | 74 | 36/39 | 92,31% |

O conjunto completo recuperou Q0052, Q0058 e Q0315 em relação às regressões da V19, sem trocar os temas escolhidos pelo controle V18 nas 100. Também deixou de recuperar Q0106 e Q0188, que eram ganhos pontuais da V19. Portanto, eliminou aquelas regressões, sem demonstrar ganho global de classificação.

A estratégia que apenas remove palavras ambíguas não basta: retirou “trânsito” como apoio a Crimes de Trânsito, mas Q0315 passou a outra sugestão errada. É necessário tratar o papel do trecho e a intensidade do apoio, além da palavra isolada.

## Por que preservar o estimador anterior

As novas seis medidas mudaram o modelo de confiança e sua calibração mesmo quando o tema final permaneceu igual. A versão completa manteve os mesmos 74 temas aceitos, mas passou a publicar apenas 15 referências, com 13 corretas. A melhora pretendida na leitura não justificava atribuir ao mesmo candidato uma nova confiança pior sustentada.

Por isso testamos separar as duas coisas: a recuperação usa o contexto novo, enquanto a compatibilidade e a confiança usam as mesmas 27 dimensões e os mesmos parâmetros do controle. Verificamos antes da aplicação ao alvo que as 100 escolhas temáticas são idênticas às do controle. O exportador não altera notas manualmente, não inventa piso de 70% ou 80% e não aprende com o resultado das 559.

Essa preservação é um experimento adaptativo. A igualdade nas 100 referências expostas não comprova validade em dados novos nem mínimo de 95%. Se a representação futura alterar as escolhas de desenvolvimento, a reutilização da calibração precisa ser reavaliada; o congelador rejeita uma diferença nessas 100 escolhas.

A Q0274 permanece em Iter Criminis (5175), pai do central oficial Crime Consumado e Tentado (5177), aceito pela régua. A vista preservada mantém a confiança anterior de 72,92% e a revisão; identificar o tema corretamente em uma referência conhecida não autoriza publicação forçada.

## Critérios de leitura e avaliação

As 100 referências já foram expostas na conversa e em experimentos anteriores. Usamos os mesmos cinco folds externos e quatro internos, com exclusão da questão avaliada e de duplicatas do treino, mas sem alegação de teste cego. As hipóteses desta rodada conhecem erros do desenvolvimento. A escolha de uma rota é registrada antes de aplicar essa rodada às 559.

As 559 questões fora da folha, incluindo as 300 recentes, não têm rótulos disponíveis. Só medimos nelas decisões, cobertura e mudanças. A precisão real permanece desconhecida. O acerto aplica central, extras oficiais e ancestrais/descendentes; irmãos não equivalem. A meta de 95% continua sem comprovação nesta nova rota.

## Arquivos e reprodução

`testar_contexto_v20.py` refaz os experimentos com as referências; `congelar_contexto_preservado_v20.py` verifica a condição para manter o estimador; `classificar_contexto_preservado_v20.py` classifica texto novo com parâmetros congelados, sem rede, rótulos, treino ou LLM. O modelo não é uma tabela por ID.

O comando de inferência cria CSV experimental, rastreabilidade e resumo em uma pasta nova. Ele não sobrescreve o `publicacao.csv` da raiz, que continua sendo um controle histórico, nem promove automaticamente a rota para envio.

## Resultado no alvo e conferência concluída

A rota de estimador preservado publicou 140/559, com 80/300 nas recentes. Em 547 itens, o candidato ficou igual ao controle e a igualdade de confiança/decisão foi verificada; as 12 trocas restantes não têm acerto medido. A prova reproduziu exatamente 2.236 previsões das quatro variantes e gerou 559 inferências adicionais da rota preservada, com rótulos, rede, treino, avaliador e recalibração bloqueados. Isso confirma reprodução, não precisão jurídica. Registros em `experimentos/contexto_preservado_v20_001/verificacao_conjunto.json`.
