# Alternativas para verificar o contexto antes de confirmar o candidato

Este documento acrescenta uma pesquisa e um diagnóstico ao experimento V17. As estratégias abaixo são propostas para outro teste; não foram incorporadas à classificação nem usadas para liberar questões. Não há novo resultado de precisão ou cobertura atribuído a elas.

## Evidência local

Nas 100 referências já expostas, o primeiro candidato da fusão V15 foi aceito em 72 questões. Entre as 92 que têm tema, um candidato aceito aparece no top5 em 89. As outras oito referências estão fora da taxonomia e contam como erro se publicadas.

Ao ordenar as referências pela quantidade de palavras do enunciado e dividi-las em quatro grupos iguais:

| Grupo descritivo | Palavras no enunciado | Questões | Primeiro candidato aceito | Tema aceito no top5 |
|---|---:|---:|---:|---:|
| Menores | 3–13 | 25 | 17 | 22 |
| Segundo quarto | 14–27 | 25 | 18 | 23 |
| Terceiro quarto | 29–71 | 25 | 21 | 22 |
| Maiores | 74–225 | 25 | 16 | 22 |

São contagens descritivas, não um efeito causal comprovado nem um corte para produção. O grupo maior contém 25 questões com tema. Dos seus nove erros de primeiro candidato, seis ainda têm tema aceito no top5; três precisam de recuperação melhor ou de um conjunto ampliado de candidatos. Uma reordenação dos mesmos cinco não pode resolver esses três.

A extensão das alternativas também importa: ao considerar a questão completa, as 25 maiores têm 169–347 palavras; o primeiro candidato acerta 16 e o top5 contém tema aceito em 23. Enunciado curto não significa questão curta.

## Exemplos ancorados na folha-verdade

- **Q0208:** a narrativa tem 225 palavras e descreve um homicídio. O comando é a assertiva “Lucas foi o autor de homicídio e Carlos figurou como partícipe do crime”. A busca escolheu 5149 (Crimes contra a Vida), mas já tinha 5071 (Concurso de Pessoas) em segundo. A referência é 5072 (Autores e Partícipes), descendente de 5071. É um caso em que o papel do comando deve ser representado melhor, preservando os fatos necessários para interpretar os papéis dos personagens.
- **Q0202:** a narrativa menciona crime sexual; o comando acrescenta o desconhecimento da menoridade. A referência é 5224 (Erro de Tipo); seu pai 5218 aparece em quarto lugar. A estrutura “quem desconhecia o quê e com que efeito para a conduta” precisa ser representada, em vez de contar apenas os nomes dos crimes. O sistema V15 já contém atributos gerais de desconhecimento e condição da vítima: sua existência não bastou, e repeti-los com mais peso não é uma solução demonstrada.
- **Q0091:** a cobrança diz respeito à execução da pena, mas os candidatos 4703 e 6734 têm o mesmo título em ramos diferentes. Um verificador textual não pode inventar uma distinção de escopo ausente do catálogo preparado. O contexto pode resolver a matéria sem resolver o ID exigido pela empresa.
- **Q0324:** há proposições independentes sobre vários institutos. Selecionar apenas a última, a primeira ou a mais frequente apagaria conhecimentos efetivamente cobrados. A referência aceita também extras de outros ramos. É necessário manter todas as proposições na análise.

Esses exemplos são explicações a partir de rótulos fornecidos, não validações de novas classificações pelo assistente.

## Alternativas pesquisadas e ordem recomendada

### 1. Passagens com papéis e contexto vizinho

Separar o texto em cabeçalho, fatos, comando/assertiva efetivamente julgada, itens e alternativas temáticas. Criar janelas de frases adjacentes, mantendo o texto integral como outra vista. Para cada candidato, registrar os trechos que oferecem apoio e se esse apoio aparece na cobrança ou somente na narrativa.

Uma frase como “nessa situação” precisa continuar ligada ao antecedente. Negações, relações de desconhecimento, condições da vítima, prazos e artigos não devem ser separados das respectivas condutas. Alternativas C/E e combinações I/II/III não fornecem conteúdo temático independente.

A literatura de recuperação de informação descreve o compromisso entre unidades muito grandes, que permitem correspondências espúrias, e unidades muito pequenas, que separam informações necessárias. Por isso a proposta é usar várias granularidades, não truncar o texto ou escolher automaticamente as últimas frases.

Fonte primária: [Manning, Raghavan e Schütze — Choosing a document unit](https://www-nlp.stanford.edu/IR-book/html/htmledition/choosing-a-document-unit-1.html).

### 2. Apoio específico da cobrança, separado do apoio ao cenário

Para cada candidato, medir apoio no comando, nas passagens ligadas ao comando, no caso completo e nos itens independentes. Essas medidas são atributos do comparador; não equivalem a probabilidade de acerto e não autorizam publicação automática.

Este projeto já testou pesos diferentes por campo, foco e trecho final. Apenas repetir essa mistura não é uma hipótese nova. O passo adicional seria representar a ligação entre o trecho cobrado e seu antecedente, registrar essa evidência e comparar o efeito por tipo de estrutura.

Modelos por frequência de palavras não preservam toda a estrutura relacional. Expressões compostas podem ajudar a conservar relações locais, mas não demonstram compreensão completa do caso.

Fonte primária: [scikit-learn — Text feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction).

### 3. Aprendizado de preferência entre candidatos próximos

Treinar, somente nas referências de ajuste, a preferência de um candidato aceito sobre um candidato concorrente do mesmo caso. O objetivo é relativo: distinguir A de B naquela questão. Isso difere do comparador V17, que aprende compatibilidade absoluta com todas as famílias e depois usa esses escores para ordenar.

O treino deve usar os candidatos recuperados sem consultar o rótulo para fabricá-los. Se nenhum candidato é aceito ou a referência é fora, não há par positivo válido naquele conjunto. Esses casos exigem análise da recuperação e da abstenção, sem escolher um falso positivo. Um modelo de ordenação não detecta automaticamente fora da taxonomia nem produz confiança calibrada.

A literatura de learning-to-rank fornece uma base para aprender preferências entre documentos/candidatos. Sua adaptação às questões jurídicas é uma hipótese nossa e ainda precisa de teste controlado.

Fonte primária: [Joachims — Optimizing Search Engines using Clickthrough Data](https://www.cs.cornell.edu/people/tj/publications/joachims_02c.pdf).

### 4. Auditar a preparação semântica antes de descartar embeddings

O experimento semântico anterior teve resultado baixo, mas o cache de vetores e seu manifesto não estão neste pacote. Não é possível atribuir a causa a modelo, idioma, pooling, truncamento, normalização ou alinhamento entre IDs e vetores sem recuperar esses artefatos.

Para textos longos, uma preparação por passagens pode evitar perder informação no limite do encoder. Isso precisaria ser preparado, documentado e congelado antes da classificação, respeitando o case. Não se propõe executar encoder ou LLM na decisão, nem gerar respostas para escolher o tema.

## Próximo experimento proposto

1. Fixar a fusão V15 como controle e declarar duas alterações pequenas antes de medir: evidência por passagens ligadas à cobrança; a mesma evidência com ordenação por pares.
2. Manter texto integral e todas as proposições; não adotar regra por tamanho, ID ou tema conhecido. Não criar diferença fictícia entre IDs homônimos.
3. Permitir candidatos extras recuperados do comando/passagens, registrando quando o tema aceito estava ausente dos cinco originais. A seleção dos extras não consulta rótulos na inferência.
4. Usar os folds originais e agrupamento de duplicatas. Escolher parâmetros e calibrar a confiança dentro do ajuste, depois da escolha do candidato. Não usar o acerto externo para decidir quais trocas manter.
5. Medir primeiro tema aceito, top5, erros corrigidos, acertos perdidos e fora indevidamente publicados. Depois medir precisão versus cobertura, incluindo o grupo de novas publicações. Não ativar uma união só porque aumenta o volume.
6. Manter os rótulos como desenvolvimento exposto. Novas referências independentes, inclusive recentes, continuam necessárias para sustentar alegações mais fortes de qualidade.

## Reproduzir somente o diagnóstico de extensão

```bash
python3 diagnosticar_textos_longos_v18.py --saida analises/contexto_longos_reproduzido
```

O comando compara previsões já salvas com as referências e cria um resumo e dez exemplos completos. Não treina classificador, não escolhe novos temas, não altera confiança e não classifica as 559 sem rótulo.
