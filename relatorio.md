# Classificação de tópicos jurídicos

**Israel Dias | Case Vício - etapa complementar | Versão V24**

Sistema próprio de busca, regras e modelos clássicos. A decisão é regenerada pelo texto, sem modelo de linguagem, encoder, rede ou acesso à folha-verdade durante a inferência. Não utiliza gabaritos para resolver as questões avaliadas.

## Resultado e interpretação

Conjunto | Publicar | Revisar | Fora
659 questões | 454 | 205 | 0
559 avaliadas | 387 | 172 | 0
300 recentes | 214 | 86 | 0

**Cobertura nas 559: 69.23%.** Nas referências, a composição publicou 54 e acertou 54; o controle anterior tinha 50 corretas em 52 publicadas. **A precisão real das 559 é desconhecida.** As referências foram expostas e reutilizadas: esse resultado não comprova generalização nem mínimo populacional de 95%.

## Arquitetura e regra de decisão

1. Validar JSONL/árvore e converter HTML em texto, preservando negação, proposições e alternativas. IDs identificam registros; não escolhem temas. Metadados de origem podem estar errados; a recuperação nova não os usa, mas rotas legadas preservadas ainda têm influência histórica de origem, documentada no código.

2. Recuperar famílias por títulos, escopos preparados, palavras, caracteres e BM25. Escolher um nó utilizável do ramo; não tratar irmãos ou títulos homônimos como equivalentes. Os escopos enriquecidos são propostas, sem homologação jurídica independente.

3. Priorizar comando específico ou cobrança final identificada. Comando genérico deixa de competir; comando informativo sem identificador permanece como apoio. Retomadas recuperam seu objeto no enunciado. Citações só dão prioridade junto de ato compatível; proposições I/II e V/F são preservadas.

4. Aplicar comparador clássico, estimativa de confiança e corte empírico selecionado no desenvolvimento. Identificador não impõe confiança mínima. Revalidar publicações antigas diante de conflito explícito; vetar crime mencionado apenas como contexto sem apoio na cobrança. Incertezas vão à revisão. Não excluir por similaridade baixa.


---

# Experimentos e uso dos 100 rótulos

## O caminho e os becos sem saída

O baseline lexical começou com 28/60 sugestões aceitas. Separação de campos, morfologia, contexto e escopos foram comparados; algumas mudanças reduziram acerto. Preservar publicações elevou a cobertura, mas também perpetuou erros: a classificação de maior cobertura anterior publicava Q0215 em Sentença Penal e Q0252 em Crimes Contra o Patrimônio, embora a primeira tivesse outro ramo oficial e a segunda fosse fora.

Tentativas semânticas, reordenação de candidatos, proteção de ramo e novos estimadores de confiança foram registradas. E5 foi preparado e versionado, mas o comparador semântico e a confiança direta não superaram a composição anterior. Mais atributos, palavras ou um menor corte não foram presumidos melhores. A V24 usa lógica contextual e modelos clássicos, sem depender de E5 na decisão.

A revisão mais recente testa cobrança final com apoio específico, lei como exemplo versus objeto cobrado, retomadas e citação convergente com ato. Q0274 foi recuperada por tentativa/consumação; Q0028 pelo contexto do procedimento e citações; Q0313 pela expressão efeito da condenação. Q0215 teve o tema corrigido e permaneceu em revisão; Q0252 deixou de ser publicada. Nenhuma regra contém IDs de questões.

Na comparação das referências, a composição acrescentou cinco publicações corretas e suspendeu três anteriores: duas erradas e uma correta. Esse custo de revisão adicional foi mantido explícito; não se selecionaram exceções por ID para tornar a amostra perfeita.

## Treino, calibração e seleção

Os 100 rótulos foram divididos nos mesmos cinco folds externos e quatro internos. A nova rota foi ajustada sem o rótulo do fold avaliado; a calibração usou previsões internas fora do ajuste e o corte buscou maior suporte com precisão empírica de 95% e pelo menos dez publicações. Duplicatas são verificadas por conteúdo. A composição usa previsões OOF de controles históricos: é desenvolvimento adaptativo, não uma validação aninhada integral de toda a cadeia histórica.

A composição selecionada teve 78/100 sugestões aceitas e 54/54 publicações corretas nas referências. A escolha e os parâmetros foram registrados antes da aplicação V24 às 559. A régua usada é a oficial: central, extras e ancestrais/descendentes; não se aceitam irmãos por semelhança de nomes.

## Previsão, confiança e cobertura

A previsão global de precisão é 98.21%, pela suavização Beta(1,1) da frequência de acerto das publicadas no desenvolvimento: (acertos+1)/(publicadas+2). É uma estimativa exploratória e não a média das confianças individuais. A faixa de sensibilidade une intervalos binomiais descritivos da composição atual e do controle, considerando a seleção adaptativa; não é um intervalo de confiança válido para as 559.

A confiança individual vem da rota estatística que decidiu o caso; em rotas antigas por identificador, representa um grupo, não verificação jurídica individual. A cobertura é a fração exata publicada neste lote e seu intervalo cobre arredondamento. As 100 referências não entram no denominador das 559. Não se ajustaram as probabilidades manualmente para declarar cumprimento da meta.


---

# Diagnóstico e desenho para produção

## O que continua difícil

Há 109 famílias ativas; 64 não têm exemplo central/extra nas 100 referências e 18 das representadas têm só um exemplo. No controle contextual, 17 de 18 erros com tema já tinham um ramo aceito no top5: faltava escolher melhor entre candidatos. Homônimos em disciplinas diferentes, escopos sem descrição efetiva, narrativas com crime contextual e perguntas com alternativas heterogêneas desafiam a classificação.

Oito referências são fora mesmo com títulos próximos no catálogo. Sem a razão da exclusão, não se aprende uma regra segura de fora. Não se pressupõe erro da equipe nem se inventa equivalência entre ramos. Uma questão curta pode ser inequívoca; não usamos limite de caracteres nem tamanho para elevar confiança. Um gabarito de alternativa não certificaria um ID temático.

## Fluxo semanal de 50 mil questões

Importação valida campos e duplicações, mantém bruto e hash, normaliza conteúdo e registra versão do catálogo. Recuperação lexical/hierárquica seleciona candidatos; regras contextualizadas e comparador clássico estimam compatibilidade. Um corte calibrado em dados recentes separa publicar/revisar, e fora exige evidência de ausência de escopo. A geração de embeddings pode ser uma preparação opcional separada, somente se demonstrar ganho; não é requisito para esta política.

A fila mostra sugestão, candidatos e razão da incerteza, agrupando dúvidas recorrentes de escopo. O professor corrige tema/fora e registra justificativa; o rótulo vira dado versionado, com autoria e data. Reportes de alunos entram como sinais de investigação, não como rótulos automáticos. Uma amostra aleatória das publicadas é revisada para evitar medir apenas os casos difíceis reportados.

Monitorar precisão e cobertura por disciplina, erro de ramo, taxa de fora, confiança versus frequência de acerto e tempo do professor. Uma amostra nova rotulada, mantida fora dos ajustes, compara a versão candidata à vigente. Retreino mensal inicial, ou antes se houver mudança relevante do catálogo/distribuição e rótulos suficientes; promoção exige avaliação e rollback disponível. Volume de correções isoladamente não dispara publicação de modelo novo.

## Custo, modelos e limites operacionais

Modelos de linguagem/assistente apoiaram desenvolvimento e propostas versionadas de vocabulário; identificador exato das conversas históricas não foi registrado. O protótipo usa TF-IDF/BM25 e regressão logística serializada. Custo executado de API de classificação: US$ 0. Assinatura existente não rateada e tokens de conversa não medidos. Não há API ou LLM na inferência V24.

Inferência observada: 9.1 min para 659 itens neste ambiente. Cenário linear, com máquina a US$ 0,10/h (hipótese, não cotação): US$ 1.15/50 mil, ou US$ 0.000023/questão, excluindo armazenamento e revisão. Se a cobertura observada se repetisse e cada revisão levasse 30 s, seriam cerca de 128 h de professor/semana. Agrupar dúvidas de escopo e aprender com correções é essencial. Essas projeções não são SLA; as recentes ainda não têm qualidade rotulada medida.


---

# Memo para o professor

**Assunto: organizar os temas e concentrar a revisão nas dúvidas relevantes**

O sistema procura colocar cada questão no assunto efetivamente exigido do aluno. Identifica quando uma lei ou crime aparece só para contextualizar, observa a pergunta ao final do texto e usa o comando quando ele delimita um assunto específico. Ainda há situações em que os nomes disponíveis não esclarecem qual caminho a plataforma espera.

## O que encontrei

Existem temas com o mesmo nome em disciplinas diferentes, como Lei de Execução Penal. Também há questões com vários institutos nas alternativas ou proposições. O sistema pode reconhecer o conteúdo geral e ainda escolher um caminho diferente do esperado. Alguns exemplos foram marcados como fora apesar de parecerem próximos de títulos existentes; falta saber o limite que motivou essa decisão.

## O que recomendo ajustar nos temas

Para cada tema, uma descrição curta deve dizer o que inclui, o que exclui e como se diferencia dos nomes próximos. Títulos homônimos precisam de um exemplo positivo e um contraexemplo, aprovados pela equipe. Os oito exemplos fora merecem uma justificativa do recorte. Manter os IDs estáveis e registrar mudanças permite atualizar o sistema sem perder o histórico.

## Do que preciso da sua participação

1. Esclarecer grupos de escopos ambíguos, em vez de resolver repetidamente a mesma dúvida em questões isoladas.
2. Corrigir uma amostra nova e variada, incluindo questões recentes, para medir a qualidade fora dos exemplos já utilizados.
3. Na revisão cotidiana, registrar tema central, extras realmente cobrados ou motivo de fora, com uma frase de justificativa quando houver conflito.

## Como isso reduz sua carga

Uma correção bem registrada alimenta o treino e pode resolver uma classe de casos semelhantes. A fila deve priorizar conflitos relevantes e conteúdo sem enquadramento, com as informações necessárias para decidir. Uma pequena amostra das publicadas serve para medir os erros que não aparecem espontaneamente na fila.

Nesta entrega, 387 das 559 questões foram propostas para publicação e 172 para revisão. Os resultados de desenvolvimento melhoraram, mas não permitem garantir que todas as publicadas estejam certas. Sua validação independente de uma nova amostra é o próximo passo para confirmar a precisão e ampliar a publicação com segurança.
