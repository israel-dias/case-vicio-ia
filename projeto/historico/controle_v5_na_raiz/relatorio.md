# Classificação de tópicos — etapa complementar, v5

## Sistema e decisões

O sistema precisa publicar questões no ramo adequado, preservando precisão e reduzindo revisão humana. A v5 produz 659 decisões: 271 publicar, 388 revisar e nenhuma fora. Descontados os 100 exemplos da folha-verdade, são 231/559 publicadas: cobertura de 41,32%. A precisão real dessas 559 é desconhecida; a previsão é 90,44%. A meta de 95% ainda não está comprovada.

A preparação remove marcação HTML e conteúdo de script sem apagar negações, comandos ou alternativas. A busca TF-IDF compara títulos e escopos preparados e versionados. Os candidatos são famílias da árvore, evitando publicar em disciplinas raiz. A representação inclui semelhanças por campo e extração literal de normas e artigos, distinguindo códigos diferentes.

A decisão combina regressão logística com calibração logística. O modelo estima a compatibilidade do primeiro candidato da busca; esta alteração não mudou os temas. A inferência usa artefatos locais, sem ler rótulos, consultar a internet ou chamar LLM. Os IDs apenas identificam as saídas.

## Os 100 rótulos e o caminho experimental

Os rótulos oficiais são temas centrais, extras e indicações de fora da taxonomia, sem decisões de publicar/revisar. Aplicamos a régua que aceita central, extras e seus ancestrais ou descendentes, mas não irmãos automaticamente. Grupos de textos duplicados não atravessam treino e avaliação.

Experimentos anteriores compararam busca lexical, campos separados, representações semânticas, vizinhos e escopos preparados. Nem todos melhoraram o resultado. A etapa recente investigou a hipótese de que muitos atributos estariam tornando a confiança excessivamente conservadora.

O experimento de remoção comparou a versão anterior com oito alternativas, preservando os mesmos temas. Em cada um dos cinco grupos externos, o treinamento, a calibração e a escolha do corte usam somente os quatro grupos internos. Os 100 exemplos já eram conhecidos e discutidos: a comparação é desenvolvimento reutilizado, não teste externo novo.

| Candidata | Publicadas/100 | Corretas | Precisão observada |
|---|---:|---:|---:|
| Controle v3 | 23 | 22 | 95,65% |
| Sem sinais de formato | 25 | 24 | 96,00% |
| Sem metadados de origem | 25 | 24 | 96,00% |
| Sem todos os sinais normativos | 24 | 22 | 91,67% |
| Redução de 39 para 10 atributos | 4 | 4 | 100,00% |

Adotamos a candidata sem três atributos de formato: Certo/Errado, assertivas numeradas e quantidade de alternativas. Ela havia sido escolhida pelo suporte nos sinais fora do treino dos 100, antes de observar seu volume nas 559. Os textos e o tratamento de conteúdo foram preservados. A pequena diferença não demonstra superioridade estatística. O resultado de 24/25 da candidata fixa não deve ser confundido com o resultado de um procedimento que escolhe variantes em cada grupo.

O corte final recalibrado é 0,7738553900. Seu ajuste tem 41 acertos em 43 selecionadas nos sinais de desenvolvimento. Isso não transforma o número de ajuste em uma avaliação independente. Nas 559, houve 57 liberações e uma passagem inversa, ganho líquido de 56 publicações, sem alterações de tema.

## Diagnóstico e previsão

Os alertas exibidos são descrições posteriores à decisão; não descontam pontos fixos. A falta de associação em nosso mapa normativo pode indicar uma lacuna do mapa, sem demonstrar incompatibilidade jurídica. Origem e assunto são auxiliares e podem estar errados. Normas ajudaram a bloquear erros: sua remoção completa publicou inclusive um item oficialmente fora da taxonomia.

As sugestões iniciais acertam 66/100 antes da abstenção. Entre as revisões do controle existem 44 sugestões corretas e 33 incorretas. Aumentar todas as probabilidades liberaria os dois grupos; melhorar a comparação entre candidatos é necessário para ganhos maiores.

A previsão de 90,44% é a média das probabilidades congeladas das publicadas fora da folha-verdade. A faixa de sensibilidade é aproximadamente 79,65%–99,90%, baseada no intervalo binomial descritivo da comparação por grupos e ampliada se necessário para conter a previsão. Ela não é um intervalo de confiança válido para as 559: exposição prévia, seleção, dependência entre grupos e distribuição diferente continuam limitações. A cobertura de 41,32% é conhecida neste lote.

## Produção

A importação deve validar esquema, duplicações e integridade de conteúdo. Catálogo, escopos, parâmetros e política precisam de versão. O serviço de classificação recebe questões novas e devolve tema, confiança e justificativa operacional sem LLM na decisão. Possíveis ausências da taxonomia seguem para revisão; baixa similaridade isolada não determina fora. Extras não são derivados automaticamente dos candidatos próximos.

Uma execução classificou 659 em 14,16 segundos, com custo de API de classificação de US$ 0. A extrapolação linear daria cerca de 18 minutos para 50 mil; não é um teste de carga. Hardware, paralelismo e custo de operação devem ser medidos. Com a cobertura observada, cerca de 59% seguiriam para revisão; esse esforço humano ainda seria um gargalo relevante.

Correções do professor e reportes confirmados devem formar dados de treino com proveniência. Publicações precisam de amostras aleatórias auditadas para medir precisão e erros por ramo, junto com tempo de revisão e mudança de distribuição. Um ciclo inicial de reavaliação semanal pode ser ajustado à chegada de rótulos suficientes. Novas versões exigem comparação antes da promoção e possibilidade de retorno à anterior.

## Memo para o professor

A v5 reduziu revisões, mas o sistema ainda não substitui sua avaliação. A fila inclui temas possivelmente adequados com estimativa conservadora e sugestões potencialmente inadequadas. Ela não representa necessariamente defeitos nas próprias questões.

Precisamos de exemplos adicionais dos ramos em que o sistema erra e de critérios claros para temas com títulos semelhantes em disciplinas diferentes. Definições curtas de escopo, exemplos de inclusão e exclusão e referências normativas ajudam mais do que simplesmente renomear os temas.

Recomendamos começar por uma amostra aleatória de publicações e outra de revisões, incluindo as 300 questões importadas. Registre o tema correto e o motivo das correções. Essas decisões permitirão medir a qualidade e melhorar o modelo sem precisar revisar toda a base a cada rodada. A finalidade é concentrar seu tempo nas dúvidas relevantes e transformar cada correção em evidência para a próxima versão.
