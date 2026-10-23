# Erros conhecidos e nuances — diagnóstico de desenvolvimento

As 100 referências estão expostas. Este documento compara previsões com os rótulos fornecidos; não usa LLM para resolver ou validar as 559 avaliadas. Uma sugestão errada numa referência não gera uma exceção por ID no classificador.

O controle contextual teve 74 temas aceitos/100. Dos 26 desacertos, oito são referências fora da taxonomia; dos 18 com tema, 17 têm um ramo aceito já entre os cinco candidatos. Isso aponta sobretudo uma falha de ordenação e de convenção/escopo, não uma ausência geral do tema na busca.

A ordem abaixo é somente de leitura. As correções de código são testadas em todos os exemplos; reconhecer um erro neste caderno não prova que uma regra o corrigiu nem autoriza um novo rótulo manual para o alvo.

## Q0002 — Ausência da taxonomia conforme referência

**Controle:** Direito Penal - Legislação Especial > Crimes contra o Sistema Financeiro; revisar; confiança estimada 45.92%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Inquérito Policial; tema não aceito; revisar.

**Enunciado:** Segundo Vera Regina Pereira de Andrade, a clientela do sistema penal é constituída de pobres, porque

**Comando:** Complete a frase de acordo com o autor.

- **A)** têm uma maior tendência a delinqüir.

- **B)** possuem uma cultura de nível inferior.

- **C)** não tiveram a devida educação.

- **D)** são naturalmente propensos à violência.

- **E)** têm maiores chances de serem criminalizados.

**Cinco candidatos do controle:** 4689: Direito Penal - Legislação Especial > Crimes contra o Sistema Financeiro; 4385: Criminologia > Teorias Sociológicas Explicativas da Criminalidade; 4384: Criminologia > Teorias Legitimidoras da Pena; 5087: Penal > Dos Crimes Contra a Administração Pública; 4709: Direito Penal - Legislação Especial > Violência contra Criança e Adolescente

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0017 — Ausência da taxonomia conforme referência

**Controle:** Processo Penal > Procedimento Ordinário; revisar; confiança estimada 61.80%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Procedimento Ordinário; tema não aceito; revisar.

**Enunciado:** No processo e julgamento dos crimes de responsabilidade dos funcionários públicos,

**Comando:** Complete a frase ou responda conforme o contexto do processo penal.

- **A)** nos crimes afiançáveis e inafiançáveis, após a denúncia, o juiz ordenará a notificação do acusado para responder por escrito, dentro do prazo de 15 (quinze) dias.

- **B)** nos crimes inafiançáveis, após a denúncia, o juiz ordenará a notificação do acusado para responder por escrito, dentro do prazo de 15 (quinze) dias.

- **C)** nos crimes afiançáveis e inafiançáveis, o eventual recebimento da denúncia é feito depois da notificação do acusado e, caso existente, de sua resposta.

- **D)** nos crimes afiançáveis, o eventual recebimento da denúncia é feito depois da notificação do acusado e, caso existente, de sua resposta.

- **E)** a falta de notificação do acusado para, se quiser, responder à acusação causa nulidade absoluta, conforme súmulas do Superior Tribunal de Justiça e do Supremo Tribunal Federal.

**Cinco candidatos do controle:** 5530: Processo Penal > Procedimento Ordinário; 5466: Processo Penal > Ação Penal; 5524: Processo Penal > Procedimento do Tribunal do Júri; 5583: Processo Penal > Sujeitos do Processo; 5543: Processo Penal > Provas em Espécies

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0028 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Comunicação dos Atos Processuais; revisar; confiança estimada 59.84%.

**Referência:** Processo Penal > Procedimento do Tribunal do Júri > Impronúncia, Desclassificação, Absolvição Sumária e Pronúncia. Extras oficiais: 5526.

**Comparador E5:** Processo Penal > Procedimento do Tribunal do Júri; tema aceito; revisar.

**Enunciado:** O Código de Processo Penal, em seu art. 406, estabelece que o juiz, ao receber a denúncia ou a queixa, ordenará a citação do acusado para responder a acusação, por escrito, no prazo de dez dias. O art. 409, do mesmo diploma legal, determina que, apresentada a defesa, o juiz ouvirá o Ministério Público ou o querelante sobre preliminares e documentos, em cinco dias. Por sua vez, segundo o parágrafo primeiro, do art. 421, do referido Estatuto Processual, ainda que preclusa a decisão de pronúncia, havendo circunstância superveniente que altere a classificação do crime, o juiz ordenará a remessa dos autos ao Ministério Público.

**Comando:** Analise as disposições mencionadas e explique o procedimento adotado pelo juiz em cada etapa processual descrita.

- **C)** Certo

- **E)** Errado

**Cinco candidatos do controle:** 5487: Processo Penal > Comunicação dos Atos Processuais; 5524: Processo Penal > Procedimento do Tribunal do Júri; 5466: Processo Penal > Ação Penal; 5530: Processo Penal > Procedimento Ordinário; 5583: Processo Penal > Sujeitos do Processo

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0039 — Ausência da taxonomia conforme referência

**Controle:** Direito Penal - Legislação Especial > Crimes contra a Economia Popular; revisar; confiança estimada 70.13%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Direito Penal - Legislação Especial > Crimes contra a Economia Popular; tema não aceito; revisar.

**Enunciado:** Suponha que todos os revendedores de gás liquefeito de petróleo (GLP) ajustem artificialmente preço final de venda do produto em determinada localidade. A esse respeito, é correto afirmar que

**Comando:** Assinale a alternativa correta.

- **A)** o ajuste é comum e em nada influencia na concorrência entre as empresas.

- **B)** há, em princípio, um ilícito penal a ser apurado que se subsumi ao crime contra o consumidor.

- **C)** o fato descrito encarta-se como crime contra a ordem econômica.

- **D)** a relação de consumo é afetada pela conduta descrita; portanto, há contravenção praticada contra a economia popular.

- **E)** a investigação a respeito do caso ficará a cargo da Polícia Federal, em virtude de que a União possui o monopólio de distribuição do GLP no Brasil.

**Cinco candidatos do controle:** 4687: Direito Penal - Legislação Especial > Crimes contra a Economia Popular; 5087: Penal > Dos Crimes Contra a Administração Pública; 5079: Penal > Dos Crimes Contra a Administração Judicial; 5218: Penal > Teoria do Crime: Fato Típico; 5134: Penal > Dos Crimes contra a Organização do Trabalho, a Propriedade Imaterial e ao Sentimento Religioso

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0043 — Ausência da taxonomia conforme referência

**Controle:** Penal > Teoria da Pena; revisar; confiança estimada 70.11%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Penal > Teoria da Pena; tema não aceito; revisar.

**Enunciado:** Sobre a fixação da pena, tem-se o seguinte:

**Comando:** Complete o estudo sobre a fixação da pena.

- **A)** a existência de circunstância atenuante pode conduzir à redução da pena abaixo do mínimo legal.

- **B)** pelo critério trifásico, adotado pelo Código Penal, o juiz, na segunda fase, deverá apreciar as causas de aumento e de diminuição da parte geral e especial.

- **C)** o estabelecimento do valor de dias-multa independe da condição econômica do condenado.

- **D)** em caso de reincidência, fixada a pena em patamar inferior a 4 (quatro) anos, o condenado poderá iniciar o cumprimento da pena em regime semiaberto, desde que as circunstâncias judiciais o recomendem.

**Cinco candidatos do controle:** 5199: Penal > Teoria da Pena; 6727: Penal > Teoria da Pena (Parte 2); 6726: Penal > Teoria da Pena (Parte 1); 5572: Processo Penal > Sentença Penal; 4384: Criminologia > Teorias Legitimidoras da Pena

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0061 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Lei de Execução Penal; revisar; confiança estimada 73.33%.

**Referência:** Direito Penal - Legislação Especial > Lei de Execução Penal. Extras oficiais: nenhum.

**Comparador E5:** Direito Penal - Legislação Especial > Lei de Execução Penal; tema aceito; revisar.

**Enunciado:** Sobre a falta grave no processo de execução criminal, é correto afirmar:

**Comando:** Assinale a alternativa correta.

- **A)** a falta grave abrange o descumprimento em regime aberto das condições impostas.

- **B)** a falta grave não abrange o condenado a pena restritiva de direito que descumpre, injustificadamente, a restrição imposta.

- **C)** a decisão judicial que reconhece a falta grave faz com que seja obrigatório o exame criminológico em eventual pedido de progressão de regime.

- **D)** a decisão judicial que reconhece a falta grave implica na perda de, no mínimo, de 1/3 dos dias remidos.

- **E)** a decisão judicial que reconhece a falta grave interrompe a contagem do período para fins de comutação e indulto.

**Cinco candidatos do controle:** 6734: Processo Penal > Lei de Execução Penal; 4703: Direito Penal - Legislação Especial > Lei de Execução Penal; 5199: Penal > Teoria da Pena; 5191: Penal > Punibilidade; 5560: Processo Penal > Recursos em Espécies

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0077 — Escolha errada com ramo aceito disponível no top5

**Controle:** Direito Penal - Legislação Especial > Crimes Eleitorais; revisar; confiança estimada 62.85%.

**Referência:** Penal > Lei Penal no Tempo e no Espaço > Conflito Aparente de Normas. Extras oficiais: nenhum.

**Comparador E5:** Direito Penal - Legislação Especial > Genocídio; tema não aceito; revisar.

**Enunciado:** Considere os artigos abaixo. Em seguida, marque a alternativa CORRETA: Artigo 1º da Lei 2.889/1956: “Quem, com a intenção de destruir, no todo ou em parte, grupo nacional, étnico, racial ou religioso, como tal”: a) matar membros do grupo; Será punido: Com as penas do art. 121, § 2º, do Código Penal, no caso da letra “a”; Artigo 309 do Código Eleitoral: “Votar ou tentar votar mais de uma vez, ou em lugar de outrem”: Pena - reclusão de até três anos.

**Comando:** Marque a alternativa CORRETA.

- **A)** Norma penal em branco heterogênea homovitelina é aquela em que o complemento do preceito primário da norma advém da mesma fonte formal de produção.

- **B)** Norma penal em branco heterogênea heterovitelina é aquela em que o complemento do preceito primário da norma advém de diversa fonte formal de produção .

- **C)** Assim dispunha o artigo 214 do Código Penal Brasileiro: “Constranger alguém, mediante violência ou grave ameaça a praticar ou a permitir que com ele se pratique ato libidinoso diverso da conjunção carnal”. Considerando que tal dispositivo foi inteiramente revogado pela Lei 12.015/2009 é correto afirmar que, nesse caso, específico operou-se Abolitio Criminis.

- **D)** O art. 1º da Lei 2.889/1956 é exemplo de norma penal em branco ao avesso ou invertida. O artigo 309 do Código Eleitoral é, por sua vez, exemplo de crime de atentado ou de empreendimento.

- **E)** Compete ao Supremo Tribunal Federal a concessão de exequatur às cartas rogatórias.

**Cinco candidatos do controle:** 4692: Direito Penal - Legislação Especial > Crimes Eleitorais; 4698: Direito Penal - Legislação Especial > Genocídio; 5170: Penal > Introdução ao Estudo do Direito Penal; 5180: Penal > Lei Penal no Tempo e no Espaço; 5191: Penal > Punibilidade

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0087 — Ausência da taxonomia conforme referência

**Controle:** Processo Penal > Prisões em Espécie; revisar; confiança estimada 64.61%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Direito Penal - Legislação Especial > Lei de Execução Penal; tema não aceito; revisar.

**Enunciado:** De acordo com a jurisprudência do Superior Tribunal de Justiça, a prisão domiciliar na execução penal

**Comando:** Complete a frase ou responda sobre a prisão domiciliar na execução penal conforme a jurisprudência do Superior Tribunal de Justiça.

- **A)** possui rol taxativo previsto no art. 117 da Lei de Execução Penal.

- **B)** é cabível apenas para sentenciado que cumpre pena no regime aberto.

- **C)** depende de exame criminológico favorável para condenados reincidentes.

- **D)** deve utilizar o marco etário de 60 anos em razão do disposto no Estatuto do Idoso.

- **E)** é cabível excepcionalmente em regime fechado para mãe cujo cuidado do filho seja imprescindível.

**Cinco candidatos do controle:** 5517: Processo Penal > Prisões em Espécie; 6734: Processo Penal > Lei de Execução Penal; 4703: Direito Penal - Legislação Especial > Lei de Execução Penal; 6722: Penal > Estatuto do Idoso - Crimes; 5560: Processo Penal > Recursos em Espécies

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0090 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Procedimento do Tribunal do Júri; revisar; confiança estimada 67.71%.

**Referência:** Processo Penal > Procedimento Ordinário. Extras oficiais: nenhum.

**Comparador E5:** Direito Penal - Legislação Especial > Juizado Especial Criminal; tema não aceito; revisar.

**Enunciado:** Assinale a alternativa CORRETA.

**Comando:** (vazio)

- **A)** Em havendo reunião de processos perante o juízo comum ou o tribunal do júri, decorrentes da aplicação das regras de conexão e continência, não serão observados os institutos da transação penal e da composição dos danos civis, em relação aos crimes de menor potencial ofensivo.

- **B)** Em razão de a Lei n° 9.099/95 admitir a aplicação subsidiária das disposições do Código de Processo Penal, o juiz determinará a suspensão do processo e do curso do prazo prescricional sempre que, nos crimes submetidos ao procedimento traçado por aquela lei, o acusado, citado por edital, não comparecer e nem constituir advogado.

- **C)** No direito processual penal brasileiro, a réplica à resposta à acusação não se constitui em uma regra prevista expressamente para todas as modalidades de procedimentos existentes, podendo ser encontrada no procedimento aplicável aos processos de competência do Tribunal do Júri e no procedimento para os processos perante o Superior Tribunal de Justiça e o Supremo Tribunal Federal.

- **D)** De acordo com o Código de Processo Penal, nos processos submetidos ao rito comum ordinário, a denúncia ou queixa serão rejeitadas quando forem manifestamente ineptas, quando faltar pressuposto processual ou condição da ação para o exercício da ação penal, quando faltar justa causa para o oferecimento da ação penal e quando o fato narrado evidentemente não constitui crime.

- **E)** Tendo o funcionário público cometido o crime de racismo no exercício de sua função, e estando a denúncia ou queixa em devida ordem, o juiz mandará autuá-la e ordenará a notificação do acusado, para responder por escrito, dentro do prazo de quinze dias.

**Cinco candidatos do controle:** 5524: Processo Penal > Procedimento do Tribunal do Júri; 5539: Processo Penal > Procedimento Sumaríssimo; 5530: Processo Penal > Procedimento Ordinário; 5560: Processo Penal > Recursos em Espécies; 5466: Processo Penal > Ação Penal

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0091 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Lei de Execução Penal; revisar; confiança estimada 67.73%.

**Referência:** Direito Penal - Legislação Especial > Lei de Execução Penal. Extras oficiais: nenhum.

**Comparador E5:** Penal > Teoria da Pena; tema não aceito; revisar.

**Enunciado:** Em cada item que se segue, é apresentada uma situação hipotética seguida de uma assertiva a ser julgada com base na legislação de regência e na jurisprudência dos tribunais superiores a respeito de aplicação de pena, cominação de penas, regime de penas, medidas de segurança e livramento condicional. Flávio, maior e capaz, condenado a pena de doze anos pela prática de homicídio doloso qualificado, iniciou o cumprimento da pena em regime fechado. Durante a execução da pena, ele apresentou comportamento excelente e colaborativo, por isso, após o período mínimo para a progressão de regime, seu advogado requereu ao juiz a passagem de Flávio para o regime aberto. Nessa situação, o pedido não poderá ser atendido: a progressão do regime prisional de Flávio deverá ser para o regime semiaberto.

**Comando:** Julgue a assertiva apresentada na situação hipotética.

- **C)** Certo

- **E)** Errado

**Cinco candidatos do controle:** 6734: Processo Penal > Lei de Execução Penal; 4703: Direito Penal - Legislação Especial > Lei de Execução Penal; 5199: Penal > Teoria da Pena; 6727: Penal > Teoria da Pena (Parte 2); 6726: Penal > Teoria da Pena (Parte 1)

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0099 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Das Lesões Corporais; revisar; confiança estimada 64.34%.

**Referência:** Penal > Dos Crimes Contra a Administração Pública > Resistência, Desobediência e Desacato. Extras oficiais: nenhum.

**Comparador E5:** Penal > Das Lesões Corporais; tema não aceito; revisar.

**Enunciado:** Filomena, camelô Irregular, é flagrada por dois agentes da fiscalização municipal, ocasião em que estes anunciam que irão lavrar um auto de infração e apreender sua mercadoria, levando-a ao depósito público, de onde poderá vir a ser retirada posteriormente, mediante pagamentos devidos, tudo conforme o previsto na legislação. Inconformada com o fato, Filomena passa a agredir fisicamente os fiscais, no intuito de impedir que levem sua mercadoria, porém eles reagem, usando força corporal nos limites necessários para conter Filomena. Como resultado, Filomena e os fiscais ficam levemente feridos, sendo a mercadoria devidamente apreendida. Diante do caso narrado, é correto afirmar que:

**Comando:** Diante do caso narrado, é correto afirmar que:

- **A)** Filomena praticou o delito de resistência, ao passo que os fiscais cometeram o delito de lesão corporal leve;

- **B)** Filomena praticou o delito de resistência, na modalidade tentada, ao passo que os fiscais não cometeram crime algum, pois agiram amparados em excludente de ilicitude;

- **C)** Filomena praticou o delito de resistência qualificada, ao passo que os fiscais não cometeram crime algum, pois agiram amparados em excludente de ilicitude;

- **D)** Filomena praticou os delitos de resistência e lesões corporais leves, ao passo que os fiscais não cometeram crime algum, pois agiram amparados em excludente de ilicitude;

- **E)** Filomena praticou os delitos de resistências, na modalidade tentada, e lesões corporais leves, ao passo que os fiscais cometeram os crimes de lesão corporal leve e abuso de autoridade.

**Cinco candidatos do controle:** 5077: Penal > Das Lesões Corporais; 4684: Direito Penal - Legislação Especial > Abuso de Autoridade; 6716: Penal > Abuso de Autoridade; 5228: Penal > Teoria do Crime: Ilicitude; 5087: Penal > Dos Crimes Contra a Administração Pública

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0106 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Dos Crimes contra o Estado Democrático de Direito; revisar; confiança estimada 56.99%.

**Referência:** Penal > Dos Crimes Contra o Patrimônio > Apropriação indébita. Extras oficiais: 5166.

**Comparador E5:** Penal > Dos Crimes Contra o Patrimônio; tema aceito; revisar.

**Enunciado:** Que delito praticam os estudantes de Direito com o chamado “pendura”, nas comemorações da instalação dos cursos jurídicos no País?

**Comando:** Responda qual é o delito praticado pelos estudantes de Direito com o chamado “pendura” nas comemorações da instalação dos cursos jurídicos no País.

- **A)** Nenhum crime foi praticado, por se tratar de fato atípico.

- **B)** Crime de dano qualificado, por motivo egoístico.

- **C)** Delito de fraude, consistente em tomar refeições em restaurante, sem dispor de recursos para pagar as despesas.

- **D)** Estelionato privilegiado, devido ao pequeno valor do prejuízo causado à vítima.

**Cinco candidatos do controle:** 5155: Penal > Dos Crimes contra o Estado Democrático de Direito; 5157: Penal > Dos Crimes Contra o Patrimônio; 4368: Criminologia > Criminologia no Estado Democrático de Direito; 5560: Processo Penal > Recursos em Espécies; 5543: Processo Penal > Provas em Espécies

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0111 — Escolha errada com ramo aceito disponível no top5

**Controle:** Criminologia > Teoria Geral da Criminologia; revisar; confiança estimada 65.62%.

**Referência:** Criminologia > Etapas Evolutivas e Escolas Criminológicas. Extras oficiais: nenhum.

**Comparador E5:** Criminologia > Etapas Evolutivas e Escolas Criminológicas; tema aceito; revisar.

**Enunciado:** Sobre a escola positivista da criminologia, é correto afirmar:

**Comando:** Assinale a alternativa correta.

- **A)** A escola positivista ainda não chega a considerar a concepção da pena como meio de defesa social, que é própria de escolas mais modernas da criminologia.

- **B)** Sua recepção no Brasil recebeu contornos racistas, notadamente no trabalho antropológico de Nina Rodrigues.

- **C)** É uma escola criminológica ultrapassada e que já influenciou a legislação penal brasileira, mas que após a Constituição Federal de 1988 não conta mais com institutos penais influenciados por esta corrente.

- **D)** Por ter enveredado pela sociologia criminal, Enrico Ferri não é considerado um autor da escola positivista, que possui viés médico e antropológico.

- **E)** O método positivista negava a importância da pesquisa empírica, que possivelmente a levaria a resultados diversos daqueles encontrados pelos seus autores.

**Cinco candidatos do controle:** 4380: Criminologia > Teoria Geral da Criminologia; 4384: Criminologia > Teorias Legitimidoras da Pena; 4371: Criminologia > Etapas Evolutivas e Escolas Criminológicas; 5530: Processo Penal > Procedimento Ordinário; 4385: Criminologia > Teorias Sociológicas Explicativas da Criminalidade

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0188 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Teoria do Crime: Culpabilidade; revisar; confiança estimada 66.06%.

**Referência:** Penal > Teoria do Crime: Ilicitude. Extras oficiais: 5233.

**Comparador E5:** Penal > Teoria do Crime: Ilicitude; tema aceito; revisar.

**Enunciado:** Segundo sua classificação doutrinária dominante, o chamado ofendículo pode mais precisamente caracterizar situação de exclusão de

**Comando:** Complete a frase sobre a caracterização do ofendículo segundo a doutrina dominante.

- **A)** antijuridicidade.

- **B)** tipicidade.

- **C)** periculosidade.

- **D)** culpabilidade.

- **E)** punibilidade.

**Cinco candidatos do controle:** 5211: Penal > Teoria do Crime: Culpabilidade; 5228: Penal > Teoria do Crime: Ilicitude; 5218: Penal > Teoria do Crime: Fato Típico; 5191: Penal > Punibilidade; 5584: Processo Penal > Teoria Geral das Prisões

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0202 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Dos Crimes Contra a Dignidade Sexual; revisar; confiança estimada 72.59%.

**Referência:** Penal > Teoria do Crime: Fato Típico > Erro de Tipo. Extras oficiais: nenhum.

**Comparador E5:** Penal > Dos Crimes Contra a Dignidade Sexual; tema não aceito; revisar.

**Enunciado:** Tício e Mévio são amigos, desde a infância. Enquanto Tício tem facilidade para se relacionar, Mévio é tímido, nunca tendo se relacionado. No aniversário de Mévio, Tício decide contratar uma profissional do sexo. Contudo, ele pede para a moça não contar nada ao amigo e, simula um encontro fortuito, dos dois, em um bar. O plano de Tício dá certo. Mévio e a moça contratada passam a noite juntos, no quarto de um flat, onde ela disse residir. Pela manhã, contudo, Mévio é acordado, por policiais, em uma operação de combate à exploração sexual de criança e adolescente, sendo acusado de manter relação sexual com menor de 18 anos, em situação de prostituição (art. 218, B, parágrafo 2º, inciso I, do CP), já que a moça conta com apenas 17 anos de idade.

**Comando:** Diante da situação hipotética e considerando que Tício também não sabia da menoridade da pessoa contratada,

- **A)** A conduta de Mévio é atípica, vez que o ato de manter relação sexual com pessoa em situação de prostituição, adulta ou menor, não é punível.

- **B)** A conduta de Mévio é atípica, vez que o ato de manter relação sexual com pessoa em situação de prostituição somente é punível, se a vítima for menor de 14 anos.

- **C)** A conduta de Mévio é atípica, vez que ele desconhecia a condição de prostituição e, sobretudo, menoridade da vítima.

- **D)** A conduta de Mévio, embora típica, em razão do desconhecimento da condição de prostituição e menoridade, é punida a título de culpa.

- **E)** A conduta de Mévio é atípica, vez desconhecer a condição de prostituição e menoridade da vítima, mas Tício, que a contratou, incorreu no crime do artigo 218-B, caput, do CP.

**Cinco candidatos do controle:** 5102: Penal > Dos Crimes Contra a Dignidade Sexual; 4709: Direito Penal - Legislação Especial > Violência contra Criança e Adolescente; 5530: Processo Penal > Procedimento Ordinário; 5218: Penal > Teoria do Crime: Fato Típico; 5543: Processo Penal > Provas em Espécies

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0249 — Ramo aceito ausente do top5

**Controle:** Penal > Dos Crimes Contra a Administração Judicial; revisar; confiança estimada 56.59%.

**Referência:** Processo Penal > Das Questões e Processos Incidentes > Exceção de Suspeição, de Impedimento ou de Incompatibilidade. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Sujeitos do Processo; tema não aceito; revisar.

**Enunciado:** O Estatuto Processual Penal prevê que o juiz não poderá exercer jurisdição no processo em que: a) tiver funcionado seu cônjuge ou parente, consanguíneo ou afim, em linha reta ou colateral até o terceiro grau, inclusive, como defensor ou advogado, órgão do Ministério Público, autoridade policial, auxiliar da justiça ou perito; b) ele próprio houver desempenhado qualquer dessas funções ou servido como testemunha; c) tiver funcionado como juiz de outra instância, pronunciando-se, de fato ou de direito, sobre a questão; d) ele próprio ou seu cônjuge ou parente, consanguíneo ou afim em linha reta ou colateral até o terceiro grau, inclusive, for parte ou diretamente interessado no feito. Nos juízos coletivos, não poderão servir no mesmo processo os juízes que forem entre si parentes, consanguíneos ou afins, em linha reta ou colateral até o terceiro grau, inclusive.

**Comando:** Processo Penal

- **C)** Certo

- **E)** Errado

**Cinco candidatos do controle:** 5079: Penal > Dos Crimes Contra a Administração Judicial; 5583: Processo Penal > Sujeitos do Processo; 5560: Processo Penal > Recursos em Espécies; 5498: Processo Penal > Inquérito Policial; 6733: Processo Penal > Competência (Parte 2)

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0252 — Ausência da taxonomia conforme referência

**Controle:** Penal > Teoria da Pena; publicar; confiança estimada 81.76%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Penal > Teoria da Pena; tema não aceito; revisar.

**Enunciado:** João, maior de setenta anos de idade ao tempo do fato, foi condenado pelo crime de estelionato à pena privativa de liberdade de quatro anos e três meses de reclusão em regime inicial semiaberto e, ainda, ao pagamento de cinquenta dias-multa, fixado o valor de um vinte avos do salário mínimo vigente. Nessa situação hipotética, conforme o CPP,

**Comando:** Assinale a alternativa correta.

- **A)** caso o presidente da República conceda a João graça parcial, o benefício não poderá ser recusado.

- **B)** o juiz poderá, a requerimento do réu, demonstradas as circunstâncias que o justifiquem, permitir que o pagamento da pena de multa se faça em parcelas mensais.

- **C)** João terá direito ao livramento condicional, preenchidos os requisitos, e somente este ou o seu advogado poderá requerê-lo ao juízo da execução penal, tendo em vista a natureza personalíssima da pena.

- **D)** o requisito temporal do livramento condicional será reduzido pela metade, em razão de João contar com mais de setenta anos de idade na data do fato.

**Cinco candidatos do controle:** 5199: Penal > Teoria da Pena; 4703: Direito Penal - Legislação Especial > Lei de Execução Penal; 6734: Processo Penal > Lei de Execução Penal; 5560: Processo Penal > Recursos em Espécies; 5157: Penal > Dos Crimes Contra o Patrimônio

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0286 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Concurso de Crimes; revisar; confiança estimada 46.56%.

**Referência:** Penal > Teoria da Pena > Primeira Fase da Dosimetria: Circunstâncias Judiciais. Extras oficiais: 5203;5204.

**Comparador E5:** Penal > Concurso de Pessoas; tema não aceito; revisar.

**Enunciado:** No cálculo da pena:

**Comando:** No cálculo da pena:

- **A)** A redução pela menoridade do acusado deve incidir após o acréscimo pelo crime continuado.

- **B)** O aumento pelo concurso formal deve preceder a diminuição pela confissão espontânea.

- **C)** O acréscimo pela má antecedência do acusado deve incidir antes da redução pela tentativa.

- **D)** O aumento pela reincidência deve ser posterior à redução pela participação de menor importância.

**Cinco candidatos do controle:** 5066: Penal > Concurso de Crimes; 5071: Penal > Concurso de Pessoas; 5543: Processo Penal > Provas em Espécies; 5199: Penal > Teoria da Pena; 5128: Penal > Dos Crimes Contra a Liberdade Pessoal

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0291 — Ausência da taxonomia conforme referência

**Controle:** Processo Penal > Inquérito Policial; publicar; confiança estimada 78.77%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Inquérito Policial; tema não aceito; revisar.

**Enunciado:** Quando se tratar de crimes relativos ao tráfico de drogas, o prazo para a conclusão do inquérito policial é de 30 dias, se o indiciado estiver preso e de 90 dias, se estiver solto, podendo ser duplicados, mediante pedido justificado da autoridade de polícia judiciária.

**Comando:** Explique os prazos para a conclusão do inquérito policial em crimes relativos ao tráfico de drogas.

- **C)** Certo

- **E)** Errado

**Cinco candidatos do controle:** 5498: Processo Penal > Inquérito Policial; 6728: Penal > Tráfico de Drogas; 4708: Direito Penal - Legislação Especial > Tráfico de Drogas; 5087: Penal > Dos Crimes Contra a Administração Pública; 5487: Processo Penal > Comunicação dos Atos Processuais

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0303 — Ausência da taxonomia conforme referência

**Controle:** Penal > Lei Penal no Tempo e no Espaço; revisar; confiança estimada 67.40%.

**Referência:** Fora da taxonomia segundo a referência. Extras oficiais: nenhum.

**Comparador E5:** Penal > Lei Penal no Tempo e no Espaço; tema não aceito; revisar.

**Enunciado:** Com relação à aplicação da lei penal, assinale a opção correta.

**Comando:** Assinale a opção correta.

- **A)** As frações de dia são computadas como um dia integral de pena nas penas privativas de liberdade e nas restritivas de direitos.

- **B)** O direito penal, quanto ao tempo do crime, considera praticado o crime no momento do seu resultado.

- **C)** A sentença estrangeira, quando a aplicação da lei brasileira produz as mesmas consequências, poderá ser homologada no Brasil para todos os efeitos, exceto para obrigar o condenado à reparação do dano.

- **D)** Ficam sujeitos à lei brasileira os crimes contra o patrimônio ou a fé pública do DF, de estado, de município, de empresa pública, sociedade de economia mista, autarquia ou fundação instituída pelo poder público, embora cometidos no estrangeiro, sendo o agente punido segundo a lei brasileira, ainda que absolvido no estrangeiro.

- **E)** Não é aplicável a lei brasileira aos crimes praticados a bordo de aeronaves ou embarcações estrangeiras de propriedade privada, ainda que achando-se aquelas em pouso no território nacional ou em vôo no espaço aéreo correspondente, e estas em porto ou mar territorial do Brasil.

**Cinco candidatos do controle:** 5180: Penal > Lei Penal no Tempo e no Espaço; 5505: Processo Penal > Lei Processual no Tempo e no Espaço; 5199: Penal > Teoria da Pena; 5063: Penal > Ação Penal; 5466: Processo Penal > Ação Penal

Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.

## Q0313 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Ação Penal; revisar; confiança estimada 76.32%.

**Referência:** Penal > Teoria da Pena > Efeitos da Condenação Penais e Extrapenais. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Ação Penal; tema não aceito; revisar.

**Enunciado:** A condenação tem como efeito genérico tornar certa a obrigação de reparar o dano. Esse efeito é automático, não precisa ser expressamente pronunciado pelo juiz na sentença condenatória e destina-se a formar título executivo judicial para a propositura de ação civil ex delicto.

**Comando:** Explique o efeito genérico da condenação no que se refere à obrigação de reparar o dano.

- **C)** Certo

- **E)** Errado

**Cinco candidatos do controle:** 5466: Processo Penal > Ação Penal; 5572: Processo Penal > Sentença Penal; 5199: Penal > Teoria da Pena; 5157: Penal > Dos Crimes Contra o Patrimônio; 6727: Penal > Teoria da Pena (Parte 2)

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0320 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Dos Crimes Contra a Administração Judicial; publicar; confiança estimada 77.16%.

**Referência:** Processo Penal > Provas em Espécies > Prova Testemunhal. Extras oficiais: nenhum.

**Comparador E5:** Penal > Dos Crimes Contra a Administração Judicial; tema não aceito; revisar.

**Enunciado:** O Direito Processual Penal, doutrinariamente, elenca as espécies de testemunhas. Dentre elas há a chamada testemunha fedatária.

**Comando:** Marque abaixo a sentença CORRETA acerca da referida espécie

- **A)** é a testemunha que depõe sobre algum fato que ouviu dizer.

- **B)** é a testemunha que depõe sobre a regularidade de algum ato praticado no inquérito ou no processo.

- **C)** é a pessoa que foi indicada por outra testemunha, não sendo computada no número máximo de testemunhas.

- **D)** trata-se dos casos em que a Lei de Drogas e a Lei do crime organizado autorizam os agentes de polícia a se infiltrarem para obterem informações acerca desses crimes.

**Cinco candidatos do controle:** 5079: Penal > Dos Crimes Contra a Administração Judicial; 5498: Processo Penal > Inquérito Policial; 5505: Processo Penal > Lei Processual no Tempo e no Espaço; 4708: Direito Penal - Legislação Especial > Tráfico de Drogas; 5543: Processo Penal > Provas em Espécies

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0323 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Provas em Espécies; revisar; confiança estimada 56.26%.

**Referência:** Processo Penal > Teoria Geral das Provas > Princípios Relativos à Prova Penal. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Teoria Geral das Provas; tema aceito; revisar.

**Enunciado:** Acerca de provas, instrumentos legais de obtenção de prova e procedimento probatório, assinale a opção correta

**Comando:** Assinale a opção correta

- **A)** No sistema processual brasileiro, admite-se prova emprestada, desde que produzida em face das mesmas partes e submetida ao duplo contraditório, ou seja, a observância deste no processo originário será renovada no processo para o qual tiver sido transladada. Por essa razão, não se admitem, no processo penal, os elementos informativos produzidos em inquérito civil, por constituir procedimento não contraditório, assim como não são admitidas as transcrições das interceptações telefônicas autorizadas em ação penal diversa.

- **B)** O interrogatório é considerado hodierna e majoritariamente como meio de defesa. Caso o réu encontre-se preso, cumprirá ao magistrado realizar o ato processual em sala própria, no estabelecimento em que estiver recolhido o réu, assegurando a publicidade interna do ato, ou então ordenar a requisição do preso para participar da audiência de instrução e julgamento, ainda que este tenha manifestado desejo de ser dispensado do ato, ratificado pela defesa, em razão do direito de presença ser indisponível.

- **C)** O sistema processual penal brasileiro assegura ao investigado ou ao réu o direito de não produzir provas contra si mesmo, em qualquer fase da persecução penal, e, desse modo, o investigado ou o réu não poderão ser compelidos a se submeter a procedimentos invasivos, como, por exemplo, o reconhecimento pessoal ou a reconstituição simulada dos fatos.

- **D)** O sistema processual penal brasileiro autoriza a produção antecipada de provas, desde que observados o binômio da urgência e relevância, a adequação ao momento da persecução penal, a legitimação do órgão acusatório e a proporcionalidade da medida. Tem-se como exemplo autorizador a informação acerca do risco de morte de testemunhas ameaçadas por associação criminosa, com possibilidade de perecimento dos depoimentos relevantes

- **E)** Na obtenção da colaboração premiada, a lei de regência limita o acesso dos defensores aos autos, especialmente no que se refere às diligências em andamento, e impõe o dever de o investigado delator firmar compromisso de dizer a verdade do que souber e do que lhe for perguntado, sendo o depoimento mantido em sigilo até o recebimento da denúncia

**Cinco candidatos do controle:** 5543: Processo Penal > Provas em Espécies; 5530: Processo Penal > Procedimento Ordinário; 5590: Processo Penal > Teoria Geral das Provas; 6735: Processo Penal > Provas em Espécie; 5580: Processo Penal > Sistemas e Princípios Processuais Penais

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0324 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Medida de Segurança; revisar; confiança estimada 65.13%.

**Referência:** Direito Penal - Legislação Especial > Lei de Execução Penal. Extras oficiais: 4686;6734.

**Comparador E5:** Penal > Medida de Segurança; tema não aceito; revisar.

**Enunciado:** É certo afirmar: I. A pena de prisão simples deve ser cumprida, sem rigor penitenciário, em estabelecimento especial ou seção especial de prisão comum, em regime semiaberto ou aberto. II. As penas acessórias previstas no Código Penal são a perda da função pública eletiva ou de nomeação, as interdições de direitos e a publicidade da sentença. III. No caso da semi-imputabilidade, a periculosidade é presumida a partir da verificação, por meio da realização de exame pericial, do estado de doença ou perturbação mental, bem como de desenvolvimento mental incompleto ou retardado do indivíduo no instante da prática do fato delituoso. Nesse caso, o juiz pode aplicar medida de segurança, devendo fundamentar a sua decisão demonstrando a existência da periculosidade. IV. O trabalho do preso será remunerado, não podendo ser inferior a três quartos do salário mínimo, estando sujeito ao regime da Consolidação das Leis do Trabalho.

**Comando:** Analisando as proposições, pode-se afirmar:

- **A)** Todas as proposições estão corretas.

- **B)** Somente as proposições II e III estão corretas.

- **C)** Somente as proposições I e III estão corretas.

- **D)** Somente as proposições I e IV estão corretas.

**Cinco candidatos do controle:** 5184: Penal > Medida de Segurança; 4703: Direito Penal - Legislação Especial > Lei de Execução Penal; 6734: Processo Penal > Lei de Execução Penal; 5572: Processo Penal > Sentença Penal; 5199: Penal > Teoria da Pena

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0325 — Escolha errada com ramo aceito disponível no top5

**Controle:** Penal > Lei Maria da Penha; revisar; confiança estimada 29.61%.

**Referência:** Processo Penal > Ação Penal > Denúncia. Extras oficiais: 4704;5494;5541.

**Comparador E5:** Processo Penal > Ação Penal; tema aceito; revisar.

**Enunciado:** Considerando as afirmativas abaixo, é CORRETO afirmar que:

**Comando:** (vazio)

- **A)** A extinção da punibilidade, nos casos de transação penal em crimes ambientais de menor potencial ofensivo, dependerá de laudo de constatação de reparação do dano ambiental, enquanto que a realização da suspensão condicional do processo para os crimes ambientais dependerá da prévia composição do dano ambiental.

- **B)** A superveniência de sentença condenatória não esvai a alegação de inépcia da denúncia, pois, como o réu defende-se do fato nela descrito, sempre estará prejudicado o exercício do contraditório e da ampla defesa.

- **C)** A litispendência, pressuposto processual que deve ser analisado para fins de recebimento da denúncia, configura-se quando duas ou mais ações penais forem dirigidas contra o mesmo acusado, com a imputação da prática de condutas e qualificações jurídicas idênticas.

- **D)** A justa causa é exigência legal para o recebimento da denúncia, instauração e processamento da ação penal, consubstanciando-se pela somatória de três componentes essenciais, quais sejam, a tipicidade, a punibilidade e a viabilidade quanto à autoria.

- **E)** Nas ações penais públicas condicionadas à representação da ofendida de que trata a Lei nº 11.340/2006 (Lei Maria da Penha), só será admitida a renúncia à representação perante o juiz, em audiência especialmente designada com tal finalidade, antes do oferecimento da denúncia e ouvido o Ministério Público.

**Cinco candidatos do controle:** 6724: Penal > Lei Maria da Penha; 4704: Direito Penal - Legislação Especial > Lei Maria da Penha; 5539: Processo Penal > Procedimento Sumaríssimo; 4701: Direito Penal - Legislação Especial > Juizado Especial Criminal; 5466: Processo Penal > Ação Penal

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.

## Q0338 — Escolha errada com ramo aceito disponível no top5

**Controle:** Processo Penal > Provas em Espécies; revisar; confiança estimada 62.80%.

**Referência:** Processo Penal > Teoria Geral das Provas. Extras oficiais: nenhum.

**Comparador E5:** Processo Penal > Provas em Espécies; tema não aceito; revisar.

**Enunciado:** Com relação às regras de provas do Código de Processo Penal, é correto afirmar que:

**Comando:** Assinale a alternativa correta.

- **A)** A circunstância conhecida e provada que, tendo relação com o fato, autorize, por indução, concluir-se a existência de outra ou outras circunstâncias, no âmbito do processo penal, não possui valor legal, uma vez que decorre do princípio da não culpabilidade a proibição de presunção.

- **B)** São características da confissão no processo penal a retratabilidade, a indivisibilidade e a relatividade do valor.

- **C)** As pessoas proibidas de depor em razão da profissão poderão fazê-lo se, desobrigadas pela parte interessada, quiserem dar o seu testemunho, neste caso, porém, não deverão prestar compromisso.

- **D)** Somente quanto ao estado das pessoas serão observadas as restrições à prova estabelecidas na lei civil.

- **E)** Na falta de perito oficial, o exame de corpo delito deverá ser realizado por um profissional idôneo, nomeado pelo juiz, que tenha habilitação técnica relacionada com a natureza do exame.

**Cinco candidatos do controle:** 5543: Processo Penal > Provas em Espécies; 5580: Processo Penal > Sistemas e Princípios Processuais Penais; 5590: Processo Penal > Teoria Geral das Provas; 4694: Direito Penal - Legislação Especial > Crimes previstos no CDC; 5560: Processo Penal > Recursos em Espécies

A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.
