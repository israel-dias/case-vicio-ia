# Case Vício IA - classificação com compatibilidade

**Israel Dias**

Versão 2 | Dados oficiais, seleção documentada e decisão sem LLM

## 1. Sistema e decisões

Objetivo: classificar questões por tópico e publicar somente quando houver evidência suficiente. A versão combina busca lexical com escopos versionados e um classificador de compatibilidade treinado nos 100 rótulos oficiais. Nenhum modelo de linguagem escolhe, vota ou valida as classificações; o código calcula as decisões.

### Dados, busca e árvore

Os anexos contêm 659 questões e 377 temas. Há 371 nós ativos não raiz e 109 famílias de nível 1. A árvore e os IDs são preservados, inclusive títulos iguais em ramos distintos. Nos atributos de compatibilidade, o HTML é convertido em texto, mantendo negações, comando e todas as alternativas, removendo comentários, scripts e estilos. A busca de escopos mantém sua normalização legada. Não se busca gabarito nem se usa a auditoria assistida da etapa 1 como rótulo de treino.

O classificador de escopos já congelado escolhe a família: 30% de similaridade de palavras, 10% de caracteres, 10% do assunto de origem e 50% do índice de escopos propostos; a família agrega pela média dos três maiores scores disponíveis. A escolha de nível 1 usa a tolerância a ancestrais da régua e perde especificidade. Não se escolhe disciplina raiz nem se transformam os cinco candidatos em extras.

### Compatibilidade e regra de decisão

Um modelo logístico compartilha 22 atributos entre pares questão-família: evidências por campo, sinais de alternativas, formato de assertivas, citações literais e metadados fracos. O alvo vem da folha oficial: central, extras e nós da mesma cadeia são aceitos; irmãos não são equivalentes automaticamente. Itens oficiais fora geram alvos negativos para todas as famílias.

A variante final mantém o tema da busca e aprende quando abster. Uma segunda função logística transforma o sinal bruto em estimativa de acerto. A publicação exige score textual mínimo de 0,03 e confiança acima do corte aprendido. Dois temas próximos não são veto automático. Revisão informa o sinal insuficiente ou a confiança abaixo do corte. Não há exclusão automática: similaridade baixa não demonstra ausência de tema.

### Autoria e artefatos

Código e 360 descrições de escopo tiveram autoria assistida; 11 recortes permaneceram sem descrição proposta. Não houve validação jurídica independente desses textos. Prompts, vocabulário, versões e experiências ficam no histórico. A autoria do código não se confunde com as previsões: estas são executadas pelo programa, sem chave de API e sem consulta aos rótulos durante a inferência.

<!-- Quebra de página no PDF -->

## 2. Rótulos e avaliação

| Etapa | Amostra | Resultado |
| --- | --- | --- |
| Baseline lexical | 60 de desenvolvimento | 28 acertos de tema; controle inicial |
| Embedding ensaiado | 60 de desenvolvimento | 7 acertos nesta preparação; não adotado |
| Escopos separados | 60 de desenvolvimento | 40 acertos; base mantida na v2 |
| CV: controle com margem | 100, cinco folds | 19/21 publicadas corretas; cobertura 21% |
| CV: compatibilidade fixa | 100, cinco folds | 20/20 publicadas corretas; cobertura 20% |
| CV: seleção interna | 100, cinco folds | 19/20 publicadas corretas; cobertura 20% |

A divisão histórica 60/20/20 foi preservada. Os novos experimentos usam cinco folds externos e quatro internos; cada item externo fica fora do treino supervisionado da rodada. Os sinais internos ajustam a confiança, o corte e a seleção de variante. Textos duplicados normalizados permanecem no mesmo grupo; no método de vizinhos, o próprio texto é excluído.

A reordenação com compatibilidade e a variante de vizinhos não melhoraram o resultado de publicação. A seleção interna errou a Q0150 ao trocar 4708 por 6728, em outro ramo; a referência oficial aceita 4708. A variante fixa preservou 4708. É uma comparação com o rótulo oficial, não uma resolução jurídica feita pelo assistente.

Escolhi a variante fixa após observar a comparação. Portanto, seus 20/20 são evidência de desenvolvimento, não uma aprovação independente da escolha. Todos os 100 rótulos já haviam influenciado discussões e preparação; a separação computacional não elimina essa exposição. A seleção interna é a avaliação do mecanismo de escolha anterior ao fold externo, com 19/20.

Para a versão final, a compatibilidade usa os 100 rótulos, e o calibrador/corte usam seus sinais fora do treino (OOF). O corte final é 0.825716, com 27/28 itens aceitos no desenvolvimento selecionado. Esse ajuste final é distinto das políticas de cada fold; não recebeu um novo teste externo.

Os 100 rótulos são agora dados de desenvolvimento e ajuste final. As 559 questões guardadas pela empresa não entram no treino ou na escolha do corte. Nenhum ID funciona como atributo ou exceção. O artefato contém coeficientes, catálogo e parâmetros, sem tabela de respostas por questão.

<!-- Quebra de página no PDF -->

## 3. Entrega e produção

| Recorte | Publicar / revisar | Cobertura |
| --- | --- | --- |
| Todas: 659 | 175 / 484 | 26,56% |
| Avaliação: 559 sem rótulo | 152 / 407 | 27,19% |
| Importação recente: 300 | 89 / 211 | 29,67% |

Precisão prevista nas publicadas das 559: 90,34%. Faixa de sensibilidade: 75,13% a 100,00%. A precisão real permanece desconhecida, e a previsão central está abaixo da meta de 95%. Os 20 acertos observados na CV não autorizam prometer 100% neste lote.

A previsão é a média das confianças do modelo congelado. A faixa reúne intervalos binomiais descritivos de 20/20 e 19/20; não corrige a dependência entre folds, a escolha posterior da variante nem a mudança para concursos recentes. Não é intervalo de confiança válido para a precisão das 559. A cobertura deste lote é contagem exata; seu intervalo apenas cobre arredondamento.

### Custo e gargalo para 50 mil por semana

Nesta execução: 6.740 s para classificar 659 e 0.147 s de preparação/leitura. API de classificação: US$ 0; assinatura da conversa não rateada, tokens internos não medidos e tempo humano da etapa 2 não instrumentado. Não é custo total zero.

Extrapolação linear: 511.4 s de classificação por 50 mil. Com tarifa ilustrativa de US$ 0,05/h, seria US$ 0.00000014 por questão em compute. Não é cotação de nuvem nem teste de 50 mil questões únicas. A mesma cobertura projetaria 36404 revisões; a dois minutos por item, 1213 horas humanas. A revisão, não o custo de API, inviabiliza essa escala na configuração atual.

Em produção: validar importação e duplicações; executar busca e compatibilidade congeladas; registrar sinais; encaminhar incertezas e reportes de alunos; professor confirma correções. Auditar também amostras aleatórias das publicadas e erros por ramo. Acompanhar precisão seletiva, cobertura, Brier, casos fora e tempo de revisão. Reavaliar semanalmente novos rótulos e mudança de distribuição; retreinar/recalibrar com dados suficientes, versionar e exigir validação em dados novos antes de promover a versão.

<!-- Quebra de página no PDF -->

## 4. Memo para o professor

Professor(a), o sistema sugere onde uma questão deve aparecer para o aluno. A resposta correta ajuda a interpretar o conhecimento cobrado, mas não foi procurada na internet nem atribuída por um assistente nesta etapa. Aprendemos a convenção de classificação a partir dos 100 exemplos fornecidos pela equipe.

### O que encontrei

Na folha oficial, 39 questões têm temas extras, 22 cobrem famílias distintas e sete atravessam disciplinas. Assim, dois assuntos plausíveis não tornam uma questão defeituosa nem exigem revisão por si só. Ao mesmo tempo, títulos iguais em ramos diferentes não tornam os IDs intercambiáveis. O erro da Q0150 ilustra uma troca de ramo que a referência não aceita.

As descrições atuais frequentemente repetem nomes e informações de importação, sem dizer o que pertence ou não ao tópico. Há temas amplos, poucos exemplos por tema e oito questões oficialmente fora da árvore. Uma semelhança de título não explica por que uma questão é fora; não alterei esses rótulos nem inventei uma justificativa jurídica.

### O que recomendo mudar nos temas

Para cada tópico, registrar uma frase de escopo, exclusões e dois ou três exemplos representativos. Priorizar homônimos e fronteiras entre ramos: Lei de Execução Penal (4703 e 6734) e Tráfico de Drogas (4708 e 6728), por exemplo. Preservar os IDs durante a discussão; só criar equivalências com confirmação da equipe. Definir também quando uma questão de várias assertivas merece extras e como tratar conteúdos que a árvore não representa.

### Do que preciso da equipe

A entrega tem 407 revisões entre as 559 sem rótulos. Isso ainda é muito para um fluxo semanal. Peço uma revisão dirigida dos limites de escopo, dos exemplos de fora e de uma amostra nova de publicadas, além das correções habituais. Não peço reclassificar os 659 itens para desenvolver o sistema. Esclarecimentos que atendam a vários itens devem virar descrições e exemplos versionados, evitando dúvidas repetidas.

Cada correção confirmada deve registrar tema central, extras, motivo, versão da árvore e responsável. Reportes dos alunos precisam de confirmação antes de virar treino. Com novos exemplos independentes poderemos medir se a precisão realmente chega a 95% e aumentar a publicação sem transferir erros ao aluno. Esta versão entrega uma decisão reproduzível e seus limites, não uma certificação de acerto jurídico.

Fontes: Enunciado e anexos oficiais: https://github.com/viciod/case-vicio-ia | NIST e-Handbook: intervalo binomial; faixas nesta entrega são apenas descritivas
