# Diagnóstico v8: Q0308 e dez revisões

Correção documental: eu errei ao afirmar que a Q0308 ainda recebia Prescrição na v8. O erro era do baseline lexical antigo; os registros atuais consultados sugerem Inquérito Policial. Esta análise não altera o classificador nem os resultados.

## Q0308 completa

Inquérito policial arquivado pelo Ministério Público por ausência de elementos suficientes de informação importa

A) coisa julgada material.
B) ilegitimidade ad causam.
C) ilegitimidade ad processum.
D) ausência de justa causa processual em sentido estrito.
E) prescrição da pretensão punitiva estatal.

Rótulo oficial: Processo Penal > Inquérito Policial > Conclusão e Arquivamento do Inquérito Policial (5501). Sugestão atual: Inquérito Policial (5498), pai aceito pela régua. O gabarito da alternativa não foi usado para esta conferência.

Passos observáveis: limpar o HTML; preservar enunciado por conter informação; não extrair marcador gramatical porque ele não aparece; identificar inquérito policial e inquérito policial arquivado no enunciado; identificar prescrição/prescrição da pretensão punitiva na alternativa E; combinar os apoios por campo; reordenar os temas; estimar confiança com o modelo de compatibilidade e o calibrador congelados.

Enunciado recebe peso 0,65 na busca de vocabulário, comando 0,10 e melhor alternativa 0,25 neste tipo de item. Os dois grupos inquérito e arquivamento geram apoio bruto 0,410878 a Inquérito; a alternativa E gera 0,098367 a Prescrição. A busca final combina 75% da busca v7 normalizada com 25% do vocabulário normalizado.

| Candidato | Busca v7 | Vocabulário normalizado | Busca v8 |
|---|---:|---:|---:|
| Processo Penal > Inquérito Policial | 1.000000 | 1.000000 | 1.000000 |
| Penal > Prescrição | 0.792620 | 0.239407 | 0.654317 |
| Processo Penal > Recursos em Espécies | 0.471994 | 0.000000 | 0.353996 |

Esses escores ordenam candidatos; não são probabilidades. Inquérito já estava em primeiro na v7, e o vocabulário aumentou sua separação em relação a Prescrição. A v8 não é responsável por corrigir esse tema: a correção é anterior.

| Execução | Confiança | Corte | Decisão |
|---|---:|---:|---|
| Avaliação no grupo 1, sem rótulo Q0308 no seu treino | 70,87% | 82,30% | revisar |
| Modelo final, ajustado com os 100 rótulos | 82,70% | 70,10% | publicar |

Os cortes foram definidos pelos dados internos de cada treino, antes de avaliar o grupo correspondente. Não se compara a confiança do grupo 1 ao corte final. O resultado final da Q0308 não é uma nova prova de generalização: seu rótulo participou desse ajuste. Ela está nos 100 excluídos da nota final.

## O motivo efetivo das revisões

As 272 revisões nas 559 tinham elegibilidade verdadeira e confiança abaixo do corte final de 70,1049879859%. Não há bloqueio separado por homônimos, falta de gabarito ou falta de palavra-chave. 67 são Certo/Errado. Em 187 não houve expressão do novo dicionário no texto efetivo; em 208 não houve apoio do novo dicionário ao candidato escolhido. Ausência de apoio novo não subtrai pontos diretamente na variante só na busca: apenas deixa de acrescentar esse canal à recuperação.

Entre as três maiores parcelas negativas da decomposição linear, palavra_completo aparece em 248 revisões, escopo_alternativas em 98, escopo_alternativa_max em 84, char_enunciado em 70 e apoio_enunciado_e_alternativas em 61. Os conjuntos se sobrepõem. São parcelas algébricas na escala de logit em relação à centralização do treino, não causas jurídicas nem pontos percentuais. O peso negativo isolado não prova que retirar o atributo melhorará a classificação; sinais correlacionados podem compensar-se.

## Dez exemplos das 300 questões novas

Seleção ilustrativa em confiança decrescente para mostrar comportamentos recorrentes. Todos estão fora dos 100 rótulos. Os temas são sugestões do sistema, sem confirmação jurídica independente. Nos exemplos Certo/Errado, não foi resolvida a assertiva.

### Q0440 — 69.50% — revisar

Sugestão: Processo Penal > Inquérito Policial.

A respeito do inquérito policial, julgue o item. Eventual vício formal no inquérito policial não contamina a ação penal dele decorrente.

C) Certo
E) Errado

Identificadores novos disparados: inquerito policial.

Inquérito policial foi reconhecido; a busca separa amplamente esse tema do segundo candidato. As parcelas negativas principais do modelo vêm da similaridade lexical do texto completo, da similaridade do foco e dos caracteres do enunciado. Não é empate entre temas nem erro comprovado na questão.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-8.5029), similaridade_foco (-1.3837), char_enunciado (-0.9832).

| Candidato | Busca v8 |
|---|---:|
| Processo Penal > Inquérito Policial | 1.000000 |
| Processo Penal > Ação Penal | 0.109176 |

### Q0369 — 69.31% — revisar

Sugestão: Penal > Lavagem de Dinheiro.

A respeito de lavagem de dinheiro e crimes contra o sistema financeiro nacional, julgue os seguintes itens. O processo e o julgamento dos crimes de lavagem de dinheiro independem do processo e do julgamento dos crimes antecedentes, ainda que praticados em outro país.

C) Certo
E) Errado

Identificadores novos disparados: nenhum dos 53 padrões.

A busca tem dois ramos próximos: Penal > Lavagem de Dinheiro e Legislação Especial > Lavagem de Dinheiro. Nenhuma expressão do dicionário v8 foi disparada: lavagem não integra os 16 grupos novos. Não há bloqueio automático por homônimo; a revisão decorre da confiança abaixo do corte.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-9.5483), char_enunciado (-1.0064), palavra_assunto_origem (-0.9022).

| Candidato | Busca v8 |
|---|---:|
| Penal > Lavagem de Dinheiro | 1.000000 |
| Direito Penal - Legislação Especial > Lavagem de Dinheiro | 0.965633 |

### Q0466 — 68.03% — revisar

Sugestão: Penal > Teoria do Crime: Fato Típico.

São elementos do crime doloso:

A) previsibilidade objetiva e dever de cuidado objetivo.
B) previsibilidade subjetiva e dever de cuidado objetivo.
C) desejo do resultado e assunção do risco de produzi-lo.
D) previsão do resultado pelo agente, mas que não se realize sinceramente a sua produção e especificidade do dolo.
E) elemento subjetivo do tipo e previsibilidade subjetiva.

Identificadores novos disparados: nenhum dos 53 padrões.

Crime doloso e suas descrições não fazem parte dos 53 padrões novos. A busca antiga sugere Fato Típico; o vocabulário não altera a ordem. Similaridade do texto completo, apoio enunciado/alternativas e média lexical das alternativas são as maiores parcelas negativas.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-3.4917), apoio_enunciado_e_alternativas (-1.2486), palavra_alt_media (-0.8594).

| Candidato | Busca v8 |
|---|---:|
| Penal > Teoria do Crime: Fato Típico | 1.000000 |
| Penal > Teoria do Crime: Ilicitude | 0.566396 |

### Q0639 — 67.68% — revisar

Sugestão: Direito Penal - Legislação Especial > Tortura.

Os crimes de tortura são tratados na Lei nº 9.455/1997, que define e estabelece punições para diversas formas de tortura. Com base no referido diploma legal, analise as alternativas e assinale a opção CORRETA:

A) Se resulta lesão corporal de natureza grave ou gravíssima, a pena é de reclusão de dois a oito anos; se resulta morte, a reclusão é de oito a vinte anos.
B) A pena cominada para o crime de tortura é detenção, de quatro a oito anos.
C) Aumenta-se a pena de um sexto até um terço se o crime é cometido por agente público.
D) Constitui crime de tortura, constranger alguém, causando-lhe sofrimento físico ou mental, ainda que sem emprego de violência ou grave ameaça, em razão de discriminação racial ou religiosa.

Identificadores novos disparados: nenhum dos 53 padrões.

Tortura e Lei 9.455/1997 não constam dos 16 grupos do novo dicionário. O classificador anterior ainda recupera Tortura; o dicionário novo não acrescenta apoio. As medidas de apoio entre campos e de texto das alternativas contribuem negativamente no modelo de confiança.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-3.6101), apoio_enunciado_e_alternativas (-1.5002), escopo_alternativas (-1.2271).

| Candidato | Busca v8 |
|---|---:|
| Direito Penal - Legislação Especial > Tortura | 1.000000 |
| Direito Penal - Legislação Especial > Crimes de Racismo | 0.428911 |

### Q0461 — 67.55% — revisar

Sugestão: Processo Penal > Recursos em Espécies.

O acusado “A” e seu advogado são intimados da sentença penal que condenou “A” pelo crime de roubo, numa sexta- feira, dia 17 de janeiro. Nessa situação hipotética, o último dia para interposição do recurso de apelação pela defesa será

A) quarta-feira, 22 de janeiro.
B) sexta-feira, 24 de janeiro.
C) sábado, 1º de fevereiro.
D) segunda-feira, 03 de fevereiro.

Identificadores novos disparados: apelacao, recurso de apelacao.

Apelação e recurso de apelação foram reconhecidos como o mesmo grupo, sem dobrar o apoio. O vocabulário troca o primeiro candidato de Sentença Penal para Recursos em Espécies, pai de Apelação. As alternativas contêm datas e pouco vocabulário temático. A nova busca não dá bônus direto à confiança.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-1.4055), char_enunciado (-0.3327), palavra_alt_media (-0.2727).

| Candidato | Busca v8 |
|---|---:|
| Processo Penal > Recursos em Espécies | 0.948305 |
| Processo Penal > Sentença Penal | 0.750000 |

### Q0524 — 64.99% — revisar

Sugestão: Penal > Prescrição.

Acerca da ação penal, das causas extintivas da punibilidade e da prescrição, julgue o seguinte item. Nos casos de concurso formal ou de continuidade delitiva, a extinção da punibilidade pela prescrição regula-se pela pena imposta a cada um dos crimes isoladamente, afastando o acréscimo decorrente dos respectivos aumentos de pena.

C) Certo
E) Errado

Identificadores novos disparados: prescricao.

Prescrição foi reconhecida. O vocabulário muda a primeira sugestão de Concurso de Crimes para Prescrição. As alternativas Certo/Errado não fornecem texto temático. A confiança ainda recebe parcelas negativas das similaridades do texto/enunciado e da média de escopo das alternativas.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-3.0407), char_enunciado (-0.5343), escopo_alternativa_media (-0.3570).

| Candidato | Busca v8 |
|---|---:|
| Penal > Prescrição | 0.984080 |
| Penal > Concurso de Crimes | 0.750000 |

### Q0473 — 60.40% — revisar

Sugestão: Processo Penal > Inquérito Policial.

Considerando as normas referentes ao inquérito policial, julgue o item a seguir. De acordo com o CPP, qualquer pessoa do povo, ao tomar conhecimento da prática de atos delituosos, deverá comunicá-los à autoridade policial, seja verbalmente, seja por via formal.

C) Certo
E) Errado

Identificadores novos disparados: inquerito policial.

Inquérito policial e o marcador referentes ao foram reconhecidos. Considerando não foi tratado como marcador. A busca destaca Inquérito Policial, mas os pesos da comparação lexical, do foco e dos caracteres do enunciado mantêm a confiança abaixo do corte.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-3.9766), similaridade_foco (-1.3837), char_enunciado (-0.5316).

| Candidato | Busca v8 |
|---|---:|
| Processo Penal > Inquérito Policial | 1.000000 |
| Penal > Abuso de Autoridade | 0.205371 |

### Q0568 — 55.77% — revisar

Sugestão: Penal > Lei Penal no Tempo e no Espaço.

No que concerne ao tempo do crime, a lei penal brasileira adotou a teoria

A) da atividade.
B) da ubiquidade.
C) mista.
D) do resultado.
E) da subsidiariedade.

Identificadores novos disparados: nenhum dos 53 padrões.

O marcador no que concerne ao extrai tempo do crime, mas essa expressão não está no dicionário v8. O tema é sugerido pela busca anterior. Similaridades de texto completo, foco e caracteres do enunciado aparecem como parcelas negativas; isso não prova ambiguidade jurídica.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-5.9771), similaridade_foco (-1.0542), char_enunciado (-0.6140).

| Candidato | Busca v8 |
|---|---:|
| Penal > Lei Penal no Tempo e no Espaço | 1.000000 |
| Penal > Teoria do Crime: Fato Típico | 0.517759 |

### Q0508 — 54.92% — revisar

Sugestão: Direito Penal - Legislação Especial > Interceptação Telefônica.

A respeito da interceptação das comunicações telefônicas, julgue os itens a seguir, com base no entendimento do STF. É possível a prorrogação do prazo de autorização para a interceptação telefônica, mesmo que sucessiva, especialmente quando se tratar de fato complexo que exija investigação diferenciada e contínua.

C) Certo
E) Errado

Identificadores novos disparados: interceptacao das comunicacoes telefonicas.

O padrão identifica interceptação das comunicações telefônicas e dá apoio tanto ao ramo de Legislação Especial quanto ao ramo de Provas em Espécies. A busca mantém Legislação Especial em primeiro. Os campos palavra_completo, similaridade_foco e char_enunciado reduzem algebricamente a confiança. Não há veto por ausência de gabarito.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-6.1976), similaridade_foco (-1.3363), char_enunciado (-0.9745).

| Candidato | Busca v8 |
|---|---:|
| Direito Penal - Legislação Especial > Interceptação Telefônica | 1.000000 |
| Processo Penal > Provas em Espécies | 0.598365 |

### Q0395 — 45.75% — revisar

Sugestão: Processo Penal > Ações Autônomas de Impugnação.

A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. Ocorrendo a extinção da punibilidade no tocante à pretensão punitiva do Estado, não cabe o ajuizamento de revisão criminal pelo próprio réu ou por procurador legalmente habilitado.

C) Certo
E) Errado

Identificadores novos disparados: revisao criminal.

A introdução coletiva foi removida do texto efetivo. O novo padrão revisão criminal troca a primeira sugestão de Prescrição para Ações Autônomas de Impugnação, pai de Revisão Criminal. A confiança da compatibilidade anterior ainda é insuficiente. Não há rótulo oficial disponível para confirmar esse item.

Três maiores parcelas negativas ao logit calibrado: palavra_completo (-2.7488), escopo_alternativas (-0.7439), similaridade_foco (-0.5993).

| Candidato | Busca v8 |
|---|---:|
| Processo Penal > Ações Autônomas de Impugnação | 0.899543 |
| Penal > Prescrição | 0.750000 |

## Os 16 grupos de identificadores novos

Novos aqui significa padrões estruturados acrescentados ao dicionário v8; muitos nomes já constavam dos títulos e descrições anteriores. O arquivo contém 53 padrões, com variações. É dado preparado, sem classificação por ID.

### inquerito — 4 padrões
Alvos por título: Inquérito Policial.

- `\binquerito policial\b`
- `\binvestigacao (?:criminal|preliminar)\b`
- `\bdelegado de policia\b`
- `\bindiciamento\b`

### arquivamento — 2 padrões
Alvos por título: Conclusão e Arquivamento do Inquérito Policial.

- `\binquerito(?: policial)? (?:foi )?arquivad[oa]s?\b`
- `\barquivamento do inquerito\b`

### prescricao — 3 padrões
Alvos por título: Prescrição.

- `\bprescricao\b`
- `\bprazos? prescriciona(?:l|is)\b`
- `\bprescricao da pretensao (?:punitiva|executoria)\b`

### execucao_penal — 7 padrões
Alvos por título: Lei de Execução Penal.

- `\blei de execucao penal\b`
- `\bexecucao (?:criminal|penal|da pena)\b`
- `\bprogressao (?:de|do) regime\b`
- `\bfaltas? graves?\b`
- `\bremicao(?: de pena)?\b`
- `\bdias remidos\b`
- `\btrabalho (?:prisional|do preso)\b`

### livramento — 1 padrões
Alvos por título: Livramento Condicional.

- `\blivramento condicional\b`

### apelacao — 2 padrões
Alvos por título: Apelação.

- `\bapelacao\b`
- `\brecurso de apelacao\b`

### habeas_corpus — 3 padrões
Alvos por título: Habeas Corpus.

- `\bhabeas corpus\b`
- `\bliberdade de (?:locomocao|ir e vir)\b`
- `\bcoacao ilegal\b`

### revisao_criminal — 2 padrões
Alvos por título: Revisão Criminal.

- `\brevisao criminal\b`
- `\breexame do processo ja alcancado pela coisa julgada\b`

### juri — 5 padrões
Alvos por título: Procedimento do Tribunal do Júri.

- `\btribunal do juri\b`
- `\bjuiz presidente\b`
- `\bdesaforamento\b`
- `\bimpronuncia\b`
- `\bpronuncia\b`

### erro_tipo — 3 padrões
Alvos por título: Erro de Tipo.

- `\berro de tipo(?: essencial)?\b`
- `\berro sobre elemento constitutivo do tipo\b`
- `\bfalsa percepcao sobre elementar\b`

### erro_proibicao — 2 padrões
Alvos por título: Erro de Proibição.

- `\berro de proibicao\b`
- `\bdesconhecimento da ilicitude\b`

### interceptacao — 2 padrões
Alvos por título: Interceptação Telefônica; Interceptação Telefônica e Quebra do Sigilo de Dados Telefônicos.

- `\binterceptac(?:ao|oes) (?:das? comunicacoes )?telefonicas?\b`
- `\blei (?:n ?o? )?9 ?296(?: (?:de )?(?:1996|96))?\b`

### juizados — 5 padrões
Alvos por título: Juizado Especial Criminal; Competência dos Juizados Especiais Criminais; Recursos no Âmbito dos Juizados Especiais.

- `\bjuizados? (?:especial|especiais) (?:criminal|criminais)\b`
- `\bjecrim\b`
- `\blei (?:n ?o? )?9 ?099(?: (?:de )?(?:1995|95))?\b`
- `\btransacao penal\b`
- `\bsuspensao condicional do processo\b`

### concussao — 4 padrões
Alvos por título: Concussão e Excesso de Exação.

- `\bconcussao\b`
- `\bexcesso de exacao\b`
- `\bexig(?:ir|e|iu) (?:dinheiro|vantagem indevida)\b`
- `\bexigencia de vantagem indevida\b`

### corrupcao_passiva — 4 padrões
Alvos por título: Corrupção Passiva.

- `\bcorrupcao passiva\b`
- `\bsolicitar ou receber\b`
- `\baceitar promessa\b`
- `\baceitacao de promessa de vantagem indevida\b`

### teorias_criminologicas — 4 padrões
Alvos por título: Teorias Sociológicas Explicativas da Criminalidade; Teorias Criminológicas em Espécie.

- `\bteoria da anomia\b`
- `\bassociacao diferencial\b`
- `\blabeling approach\b`
- `\bescola de chicago\b`

## Conclusão técnica

Os rastros mostram que localizar o assunto e estimar confiança são etapas distintas. Em alguns casos, a busca destaca um candidato e o modelo de compatibilidade ainda produz confiança baixa. Os exemplos não demonstram defeito jurídico das questões. O próximo experimento deve isolar a contribuição dos atributos de confiança e a seleção/calibração, com novo ajuste e avaliação, sem aumentar probabilidades à mão. Não foi alterado nenhum rótulo, parâmetro, corte ou decisão nesta análise.
