# V18 — contexto, cobrança e cabeçalhos gerais

Este é um estudo experimental. Não substitui automaticamente a entrega formal. As 100 referências já foram expostas na conversa e usadas em rodadas anteriores; os resultados são desenvolvimento, mesmo com separação de treino e validação dentro dos folds. As 559 restantes, incluindo as 300 recentes, não têm rótulos disponíveis.

## O problema que motivou a rodada

A Q0208 contém uma narrativa sobre homicídio, mas a cobrança trata de autor e partícipe. O controle de recuperação colocava o ramo correto em segundo lugar. Testamos priorizar a cobrança, preservar passagens ligadas a ela e aprender preferências entre candidatos recuperados. Não usamos a resposta resolvida pelo assistente para escolher, votar ou validar temas.

Um identificador forte escolhe a forma de leitura, não uma confiança mínima. Palavras comuns isoladas não bastam, uma lei não dispensa contexto, títulos iguais em ramos diferentes exigem escopo. Nenhum caso é liberado simplesmente porque apareceu um título.

## Primeira comparação: comando já preenchido

Em `experimentos/contexto_v18_002` estão cinco variantes, os folds, os modelos congelados, os resultados das 100 e as decisões das 559.

| Variante | Tema aceito /100 | Corretas/publicadas nas 100 | Publicadas /559 | Publicadas /300 recentes |
|---|---:|---:|---:|---:|
| Fusão V15, primeiro candidato | 72 | 23/24 (95,83%) | 216 | 122 |
| Comando estrito | 74 | 37/39 (94,87%) | 196 | 113 |
| Passagens com apoio integral | 69 | 10/11 (90,91%) | 175 | 105 |
| Passagens e comparação por pares | 70 | 0/0 (indefinida) | 0 | 0 |
| Comando estrito e pares | 70 | 6/7 (85,71%) | 0 | 0 |

O comando estrito corrigiu Q0208 e Q0316 sem prejudicar outro acerto de tema nesta comparação. Isso não basta para aprovar a política inteira: 37/39 é inferior a 95%. O comparador por pares não recebeu automaticamente o tema oficial entre os candidatos; só pôde aprender com os candidatos realmente recuperados.

A primeira tentativa do detector, em `contexto_v18_001`, associava “impossível” isolado a “crime impossível”. O código daquela tentativa está preservado em `historico/v18_rodada_inicial`; sua correção e a expressão “coautoria” motivaram `_002`. São iterações no desenvolvimento exposto, não novos testes cegos.

## Por que o comando não alcançava as questões recentes

As 300 recentes têm o campo `comando` vazio. Nas 100 referências são 30 vazios; nas 259 antigas fora da folha, 71. A primeira preparação estrutural recuperou cobrança em 133 recentes e encontrou identificador forte em 65 delas. Esses números contam trechos identificados, não acertos jurídicos nem publicações.

A preparação só move texto literal. Não inventa resposta, não escolhe tema e não consulta modelo. O trecho transferido sai da narrativa para não transformar uma única citação legal em falsa citação repetida nos dois campos. Todas as proposições I/II/III são preservadas.

## A falha dos cabeçalhos

Na Q0274, uma introdução enumera crimes, penas, imputabilidade e outros institutos antes de uma assertiva sobre tentativa e latrocínio consumado. A lista não é a cobrança específica. Na Q0230, a única frase introdutória enumera culpabilidade, concurso de pessoas, penas e medidas de segurança; não há uma assertiva específica posterior que autorize escolher um deles só pelo cabeçalho.

Outro falso identificador apareceu na Q0274: “morte consumada, o agente responderá” foi associado a “Morte do agente”. Coocorrência não demonstra essa relação. A correção segura exige expressão contínua para títulos compostos apenas por palavras comuns e mantém relações explícitas como autores e partícipes.

O extrator seguro aceita flexões das preposições, como “em relação às”. Separa uma lista geral da assertiva seguinte, guarda a introdução no rastreio, preserva cabeçalhos normativos necessários e desativa a prioridade de uma lista sem foco. Não escolhe o primeiro assunto, não cria regras por ID e não aumenta a confiança artificialmente.

## Composições com o controle anterior

O controle V16 tem 394 publicações em 559 (70,48%), sendo 218 em 300 recentes. A precisão dessas publicações permanece desconhecida. A composição com o comando literal foi testada em duas políticas: dar prioridade ao comando em todos os casos identificados ou usá-lo apenas para reconsiderar revisões. A segunda preserva as publicações antigas; ela não representa uma regra universal de comando estrito.

| Composição | Corretas/publicadas nas referências | Publicadas /559 | Recentes publicadas |
|---|---:|---:|---:|
| Prioridade universal, comando literal | 48/50 (96%) | 380 | 218 |
| Suplementar revisões, comando literal | 50/52 (96,15%) | 395 | 218 |
| Prioridade universal, primeira extração | 48/50 (96%) | 338 | 187 |
| Suplementar revisões, primeira extração | 51/53 (96,23%) | 394 | 218 |

A única nova publicação do suplemento literal nas 559 é Q0157; sua correção não é conhecida. A primeira extração não acrescentou publicação ao alvo no suplemento. As composições foram formuladas após observar as variantes individuais e não têm calibração global independente; não foram promovidas a entrega.

## Como ler os números

“Tema aceito” aplica a régua da empresa: central, extra oficial, ancestral ou descendente; irmãos não são equivalentes. Não mede a resolução correta da alternativa. “Corretas/publicadas” só pode ser medido nas 100 referências. As decisões nas 559 mostram cobertura, nunca precisão real.

Os limiares e modelos são ajustados dentro dos folds de treino e congelados antes da aplicação ao alvo. As 100 já expostas e as muitas comparações limitam a interpretação. Uma precisão observada de 95% ou mais no desenvolvimento não comprova mínimo populacional nem transferência para provas recentes.

O runtime aplica modelos estatísticos clássicos congelados. Não chama LLM, encoder, internet, avaliador, treinamento supervisionado ou folha-verdade. O índice TF-IDF é reconstruído somente com o catálogo versionado. Os testes de integridade e reprodução não validam o Direito.

## Refinamentos do cabeçalho — sem ocultar as tentativas

A separação inicial do preâmbulo (`comando_foco_v18_001`) manteve 72/100 temas aceitos: corrigir a divisão do texto, isoladamente, não bastou. A versão seguinte (`comando_seguro_v18_001`) também corrigiu a flexão “em relação às” e impediu que palavras comuns próximas fossem tratadas como expressão jurídica. Recuperou Q0230 e passou a 73/100, sem prejudicar outro acerto em relação à primeira extração. Q0274 continua com tema sugerido errado e em revisão.

Na inspeção do alvo, a Q0526 expôs um problema de segmentação: marcadores “( )” introduzem proposições V/F, não um cabeçalho. A versão final desta rodada (`comando_integral_v18_001`) adiciona uma pós-condição: separar o preâmbulo não pode retirar nenhum desses marcadores e suas afirmativas. Se isso ocorrer, usa a extração que conserva o conjunto. A comparação em todas as 659 entradas mostrou mudança somente na Q0526, nenhuma nas 100 referências e nenhuma perda de marcador V/F. O exemplo mantém as três proposições, sem escolher por ID.

A proteção de V/F foi adicionada depois de inspeção de texto sem rótulo do alvo. Isso está documentado como desenvolvimento adaptativo; não apresentamos o alvo como conjunto intocado. Os modelos e limiares continuam sendo ajustados somente nas referências, e a versão final repete o mesmo protocolo de folds.

## Q0274 — diagnóstico da sugestão restante

Na cobrança preparada, a busca ainda dava apoio a Punibilidade: a similaridade lexical/título se apoiava em “morte” e “agente”; uma camada legada de identificadores também considerava o par sem verificar sua relação gramatical. O novo detector já recusava a associação, mas a recuperação legada continuava contribuindo. Não se trata de o sistema ter demonstrado que o agente morreu.

O catálogo contém Iter Criminis, cujo escopo menciona consumação e tentativa, e seu filho Crime Consumado e Tentado. As formas “tentativa”, “tentado”, “consumado” e “consumação” não eram equivalentes para o identificador de título. O vocabulário V8 não encontrou expressão na assertiva preparada dessa questão. Punibilidade ficou com score de recuperação 0,833947; Patrimônio, 0,812298; Iter Criminis, 0,781031. Esses scores não são probabilidades.

A variante `conceitos_v18_001` testa normalização morfológica de compostos do catálogo: exige pelo menos dois termos informativos do título em proximidade e não ativa por um adjetivo sozinho. As formas são dadas por um mapa versionado, aplicado igualmente a qualquer ID. Não se adiciona uma resposta ou decisão manual para a Q0274. A informação da folha-verdade é usada na validação de desenvolvimento, e a formulação da hipótese após observar o erro permanece explícita.

A camada legada não foi reescrita integralmente nesta variante; a nova evidência composta disputa a recuperação pelo mesmo mecanismo de pesos da rota de comando. Portanto, recuperar a Q0274 não provará que todas as associações gramaticais da busca legada foram corrigidas. A publicação depende do modelo e limiar calibrados, não só do conceito identificado.

## Resultado da nova representação na Q0274

Na validação com a questão fora do treino do seu fold, a variante de conceitos passou de Punibilidade (5191, sugestão errada) para Iter Criminis (5175), pai do central oficial Crime Consumado e Tentado (5177). Essa é uma classificação aceita pela régua de pai/filho, sem depender de resolver o C/E. A confiança saiu de 68,20% para 72,92%; a decisão permaneceu revisar porque não atingiu o corte calibrado de 77,01% daquele fold. Esse não é um corte universal para todas as variantes. A melhoria não foi uma alteração manual do CSV.

Em comparação com a extração integral anterior, a variante corrigiu um erro de tema (Q0274) e não prejudicou outro: 73/100 passou a 74/100. Nas publicadas, porém, permaneceu em 36/39 (92,31%), abaixo de 95%. Logo, o ganho na sugestão temática não sustenta promoção da política inteira. A seleção registrada antes do alvo continuou sendo o controle de fusão. A folha-verdade foi usada como referência de desenvolvimento; essas 100 questões não compõem a avaliação competitiva das 559.

## Reprodução técnica

A execução de teste definitiva tem 60 testes aprovados (`testes_v18_definitivos.log`). As verificações de reprodução usam os modelos congelados e bloqueiam leitura da folha-verdade, acesso à rede, avaliador, treinamento supervisionado e recalibração. Comparam tema, decisão, confiança e candidatos por registro; não apenas contagens agregadas.

Os scripts `contexto_v18/tests/verificar_*.py` registram os resultados em `reproducao_verificada.json` dentro de cada experimento. O inventário anterior de 766 arquivos foi preservado byte a byte, com o README antigo arquivado. A aprovação desses testes é de integridade e funcionamento; não certifica a precisão jurídica no alvo.

## Efeito da hipótese morfológica no alvo

A comparação `analises/efeito_conceitos_559_v18.json` confirmou zero mudanças de tema e zero mudanças de decisão nas 559, entre a extração integral e a variante morfológica. Ambas produziram 139 publicações, 420 revisões e nenhuma fora; 79 publicações nas 300 recentes. As probabilidades foram recalculadas com os modelos da respectiva variante. Não se mostrou um ganho de cobertura nem de precisão no alvo. O resultado da Q0274 é um ganho específico de desenvolvimento, não evidência de generalização.

## Quadro final das extrações e conceitos

| Experimento, comando estrito | Tema aceito nas 100 | Corretas/publicadas nas 100 | Publicadas /559 | Publicadas /300 recentes |
|---|---:|---:|---:|---:|
| comando_extraido_v18_001 | 72/100 | 39/42 (92.86%) | 140 | 82 |
| comando_foco_v18_001 | 72/100 | 38/41 (92.68%) | 142 | 81 |
| comando_seguro_v18_001 | 73/100 | 36/39 (92.31%) | 139 | 79 |
| comando_integral_v18_001 | 73/100 | 36/39 (92.31%) | 139 | 79 |
| conceitos_v18_001 | 74/100 | 36/39 (92.31%) | 139 | 79 |

As variantes não substituíram o controle V16 de 394/559. Na variante morfológica, as publicações das 559 descrevem a aplicação da regra, sem medir sua precisão. O controle escolhido em todos esses estudos completos foi controle_fusao (216/559); esse comparador isolado também não substitui o controle composto V16. As composições documentadas são experiências distintas.

Na preparação integral, 127 cobranças e 51 identificadores fortes foram encontrados nas recentes; os números da variante morfológica estão em `analises/comparacao_preparacao_v18.json`. Nenhum desses números conta classificações corretas.
