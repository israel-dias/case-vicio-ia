# Foco referencial: teste da hipótese

As expressões foram usadas exclusivamente no enunciado. Os 659 textos foram processados; 176 têm os marcadores implementados: 21 nos 100 rotulados e 155 nas 559 questões avaliadas pela empresa. A entrega anterior não foi alterada.

A implementação é uma aproximação textual, com expressões regulares e janelas. Não é um analisador semântico completo. Resolve apenas algumas retomadas: procura a última citação próxima ou usa uma frase anterior. Não resolve questões jurídicas, não pesquisa respostas nem chama LLM.

## Hipóteses e comparação

1. Foco exclusivo: a busca compara apenas o trecho extraído quando há apoio no catálogo. Novo ajuste da compatibilidade e da calibração; não publica automaticamente.
2. Foco ponderado: combina 60% da busca original normalizada com 40% da busca no foco normalizada. Preserva as evidências originais e acrescenta três atributos: similaridade do foco, distância ao melhor foco e presença do marcador. Novo ajuste e calibração.
3. Regra absoluta, diagnóstico separado: quando há marcador e algum apoio textual, publica o candidato da busca exclusiva sem corte de confiança. Sem marcador, mantém a decisão do controle. Não é um classificador calibrado para entrega.

Os modelos clássicos são regressões logísticas; os cinco grupos externos e quatro internos foram preservados. Os rótulos externos não entram no treino/calibração daquele grupo. O catálogo e os escopos são fixos. Os 100 rótulos já foram vistos e reutilizados em várias hipóteses: os números são desenvolvimento comparativo, não teste externo cego. Não escolhemos uma variante olhando a quantidade publicada nas 559.

| Variante | Acertos de tema/100, antes da abstenção | Publicadas/100 | Corretas publicadas | Precisão observada |
|---|---:|---:|---:|---:|
| controle_v5 | 66 | 25 | 24 | 96.00% |
| foco_exclusivo | 61 | 16 | 16 | 100.00% |
| foco_ponderado | 66 | 20 | 20 | 100.00% |
| Regra absoluta + controle | — | 36 | 26 | 72.22% |

No subconjunto dos 21 marcadores, a regra absoluta acertou 11 (52,38%). O controle acertava o tema de 16 desses 21 antes da abstenção. Isso testa esta implementação de extração e busca, não todas as possíveis análises gramaticais. Não demonstra que focar o enunciado seja inútil; demonstra que presença de marcador + correspondência textual não basta para liberar.

## Simulação nas 559: acerto desconhecido

| Variante | Publicar | Revisar | Cobertura |
|---|---:|---:|---:|
| Controle v5 | 231 | 328 | 41,32% |
| foco_exclusivo | 163 | 396 | 29.16% |
| foco_ponderado | 180 | 379 | 32.20% |

O foco ponderado liberou duas questões antes em revisão, mas retirou 53 publicações anteriores: saldo de menos 51. O corte final da variante é 0,8499340753. As mudanças de probabilidade também refletem novo ajuste e nova calibração; não são efeito causal isolado de uma expressão. Não houve melhora de cobertura neste teste, nem aferição da precisão real das 559.

## Exemplos recentes: resultado computacional

Estes itens não têm rótulo oficial disponível. Abaixo mostramos a extração e a decisão do sistema, sem confirmar juridicamente o tema ou a resposta. O comando e as alternativas são preservados na evidência original.

### Q0638

Marcelo, analista de sistema de informações em uma repartição pública, estava em uma grande dúvida sobre os crimes praticados por funcionário público contra a administração em geral. A principal dúvida de Marcelo era em relação à conduta típica de “modificar ou alterar, o funcionário, sistema de informações ou programa de informática sem autorização ou solicitação de autoridade competente”. Para efeitos do Código Penal, a prática desta conduta configura o crime de:

Comando: 
A) Concussão.
B) Inserção de dados falsos em sistema de informações.
C) Excesso de exação.
D) Modificação ou alteração não autorizada de sistema de informações.
E) Peculato.

Trecho extraído: conduta típica de “modificar ou alterar, o funcionário, sistema de informações ou programa de informática sem autorização ou solicitação de autoridade competente” modificar ou alterar, o funcionário, sistema de informações ou programa de informática sem autorização ou solicitação de autoridade competente desta conduta configura o crime de modificar ou alterar, o funcionário, sistema de informações ou programa de informática sem autorização ou solicitação de autoridade competente configura o crime de
Controle: revisar, confiança 76.13%, tema 5087.
Foco ponderado: revisar, confiança 82.30%, sugestão computacional Penal > Dos Crimes Contra a Administração Pública.

### Q0508

A respeito da interceptação das comunicações telefônicas, julgue os itens a seguir, com base no entendimento do STF. É possível a prorrogação do prazo de autorização para a interceptação telefônica, mesmo que sucessiva, especialmente quando se tratar de fato complexo que exija investigação diferenciada e contínua.

Comando: 
C) Certo
E) Errado

Trecho extraído: interceptação das comunicações telefônicas
Controle: revisar, confiança 64.98%, tema 4700.
Foco ponderado: revisar, confiança 63.22%, sugestão computacional Direito Penal - Legislação Especial > Interceptação Telefônica.

### Q0555

Em relação ao livramento condicional:

Comando: 
A) A Lei de Execução Penal permite o livramento condicional aos condenados pela prática de feminicídio, salvo nos casos de reincidência.
B) Conforme tese firmada pelo Superior Tribunal de Justiça, o juiz da execução criminal fica impedido de considerar, para fins de concessão do livramento condicional, o histórico prisional e as faltas disciplinares praticadas pelo sentenciado fora do período de 12 meses no Código Penal.
C) A Lei de Execução Penal veda a concessão de livramento condicional ao condenado por crime hediondo ou equiparado, com resultado morte, independentemente de ser primário ou reincidente.
D) O Código Penal veda que o juiz da execução penal condicione a concessão do livramento condicional à reparação do dano causado pela infração.
E) Segundo o Código Penal, é vedado o livramento condicional ao condenado reincidente específico em crimes praticados com violência ou grave ameaça.

Trecho extraído: livramento condicional
Controle: revisar, confiança 28.95%, tema 6734.
Foco ponderado: publicar, confiança 93.78%, sugestão computacional Penal > Teoria da Pena.

### Q0456

No que se refere aos tópicos de Direito Penal, analise os itens a seguir e, ao final, assinale a alternativa correta. I - Lei excepcional, por ter ultratividade, pode ser aplicada a fatos praticados durante sua vigência mesmo após sua revogação. II – No tocante ao tempo do crime, o Código Penal brasileiro adotou a teoria da atividade, que o considera como o momento da conduta comissiva ou omissiva. III – O princípio da legalidade tem como fundamento o princípio nullum crimen, nulla poena sine praevia lege.

Comando: 
A) Apenas o item I é verdadeiro.
B) Apenas o item II é veradeiro.
C) Apenas o item III é verdadeiro.
D) Apenas os itens I e III são verdadeiros.
E) Todos os itens são verdadeiros.

Trecho extraído: tópicos de Direito Penal
Controle: revisar, confiança 54.53%, tema 5180.
Foco ponderado: revisar, confiança 26.92%, sugestão computacional Penal > Introdução ao Estudo do Direito Penal.

### Q0417

Michel Foucault, em seu curso no Collège de France de 1972-1973, intitulado A Sociedade punitiva, mais precisamente na aula de 21 de fevereiro de 1973, sintetiza aquilo a que chama “sociedade punitiva”, como sendo uma sociedade na qual o aparato judiciário desempenharia as seguintes funções:

Comando: 
A) corretivas e penitenciárias.
B) vingativas e dissipadoras.
C) arbitrárias e dissipadoras.
D) corretivas e arbitrárias.
E) vingativas e penitenciárias.

Trecho extraído: uma sociedade na qual o aparato judiciário desempenharia as seguintes funções
Controle: revisar, confiança 31.39%, tema 5185.
Foco ponderado: revisar, confiança 25.80%, sugestão computacional Penal > Dos Crimes Contra a Administração Pública.

### Q0441

A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. Considere a seguinte situação hipotética. Um indivíduo foi condenado a pena privativa de liberdade de dois anos de reclusão, em regime aberto, pela prática do crime de furto qualificado. Irresignada, a defesa apelou para o tribunal de justiça, que deu provimento ao recurso, reconhecendo a causa de diminuição da pena referente ao arrependimento posterior. Assim, a pena privativa de liberdade foi reduzida para 1 ano e 4 meses de reclusão. Nessa situação, cabe ao tribunal de justiça converter o feito em diligência, a fim de que o Ministério Público ofereça a proposta do sursis processual.

Comando: 
C) Certo
E) Errado

Trecho extraído: revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995) arrependimento posterior
Controle: revisar, confiança 70.13%, tema 5199.
Foco ponderado: publicar, confiança 85.85%, sugestão computacional Processo Penal > Procedimento Sumaríssimo.

### Q0395

A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. Ocorrendo a extinção da punibilidade no tocante à pretensão punitiva do Estado, não cabe o ajuizamento de revisão criminal pelo próprio réu ou por procurador legalmente habilitado.

Comando: 
C) Certo
E) Errado

Trecho extraído: revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995)
Controle: revisar, confiança 69.91%, tema 5476.
Foco ponderado: revisar, confiança 57.59%, sugestão computacional Processo Penal > Ações Autônomas de Impugnação.

### Q0511

Considerando o estabelecido no Código de Processo Penal acerca das relações jurisdicionais com autoridades estrangeiras, julgue os itens a seguir. Independe do pagamento das despesas o andamento de carta rogatória que verse sobre crime de ação penal privada.

Comando: 
C) Certo
E) Errado

Trecho extraído: o estabelecido no Código de Processo Penal acerca das relações jurisdicionais com autoridades estrangeiras
Controle: revisar, confiança 20.26%, tema 5063.
Foco ponderado: revisar, confiança 32.19%, sugestão computacional Direito Penal - Legislação Especial > Crimes previstos no CDC.

## Exceções demonstradas com a folha-verdade

Estas questões não contam na nota final. São usadas aqui porque seus rótulos permitem comprovar uma falha, sem pedir ao assistente que invente uma classificação para as 559.

Q0005: “em relação ao crime de furto” introduz o fato do caso; a folha-verdade registra Teoria da Pena. É um contraexemplo concreto a considerar toda referência como nome do tema.
Q0091: “a respeito de aplicação de pena ... medidas de segurança e livramento condicional” é uma introdução coletiva; a folha-verdade registra Lei de Execução Penal. A regra não pode descartar a situação específica posterior.
Q0325: “Considerando as afirmativas abaixo” não nomeia nenhum assunto. As informações temáticas estão nas alternativas, que não podem ser apagadas apenas porque houve um marcador no enunciado.

A lista completa dos dez erros da busca exclusiva nos 21 marcadores está em liberacao_absoluta_100.json e diagnostico_100.csv.

### Q0005 — referência oficial: Penal > Teoria da Pena

Carlos foi denunciado pelo crime de furto qualificado, praticado em 15/5/2022. Após a tramitação regular do processo, o juiz fixou a pena base no mínimo legal, tendo em seguida agravado em 1/6 a pena em face da reincidência, sob o fundamento de que o réu possuía uma condenação anterior transitada em julgado, e impôs o regime fechado para início de cumprimento de pena. Na condenação anterior, Carlos havia recebido o livramento condicional em 27/4/2015, cumprindo-o sem revogações até 27/4/2019, e a decisão que declarou extinta a pena foi proferida em 29/6/2020. Considerando-se a situação hipotética apresentada, bem como a pena e o regime fixados pelo juiz, é correto afirmar que, em relação ao crime de furto qualificado praticado em 15/5/2022, Carlos é

A) reincidente, e o regime inicial cabível é o fechado, visto que o período depurador referente à condenação anterior começou a correr em 27/4/2019.
B) reincidente, e o regime inicial cabível é o fechado, visto que o período depurador referente à condenação anterior começou a correr em 29/6/2020.
C) primário, e o regime inicial cabível é o semiaberto, visto que o período depurador se iniciou em 27/4/2015 e a pena é superior a quatro anos.
D) primário, e o regime cabível é o aberto, visto que o período depurador foi cumprido sem revogação e a pena é inferior a quatro anos.
E) reincidente, e o regime cabível é o semiaberto, visto que, dada a pena aplicada, incide no caso a súmula n.º 269 do STJ.

### Q0091 — referência oficial: Direito Penal - Legislação Especial > Lei de Execução Penal

Em cada item que se segue, é apresentada uma situação hipotética seguida de uma assertiva a ser julgada com base na legislação de regência e na jurisprudência dos tribunais superiores a respeito de aplicação de pena, cominação de penas, regime de penas, medidas de segurança e livramento condicional. Flávio, maior e capaz, condenado a pena de doze anos pela prática de homicídio doloso qualificado, iniciou o cumprimento da pena em regime fechado. Durante a execução da pena, ele apresentou comportamento excelente e colaborativo, por isso, após o período mínimo para a progressão de regime, seu advogado requereu ao juiz a passagem de Flávio para o regime aberto. Nessa situação, o pedido não poderá ser atendido: a progressão do regime prisional de Flávio deverá ser para o regime semiaberto.

C) Certo
E) Errado

### Q0230 — referência oficial: Penal > Teoria do Crime: Culpabilidade

Assinale a opção correta em relação às causas de exclusão de culpabilidade, ao concurso de pessoas, às finalidades das penas e às medidas de segurança.

A) Em relação à embriaguez não acidental, o CP adotou a teoria da actio libera in causa, devendo ser considerado o momento da prática delituosa e não o da ingestão da substância, para aferir a culpabilidade do agente.
B) No erro de proibição indireto, o agente tem perfeita noção da realidade, mas avalia de forma equivocada os limites da norma autorizadora. Tal erro, se escusável, isenta-o de pena; se inescusável, concede-lhe o direito a redução da pena de um sexto a um terço.
C) No ordenamento jurídico brasileiro, a natureza jurídica do concurso de pessoas é justificada pela adoção da teoria monista, na qual inexistem desvios subjetivos de conduta.
D) Segundo a teoria finalista, a pena tem a dupla função de punir o criminoso e prevenir a prática do crime pela reeducação e pela intimidação coletiva.
E) A medida de segurança possui finalidade preventiva e visa ao tratamento dos inimputáveis que demonstrarem, pela prática delitiva, potencialidade para novas ações danosas, razão pela qual não se aplicam os princípios da irretroatividade da lei penal mais grave e da anterioridade a essa espécie de sanção penal.

### Q0325 — referência oficial: Processo Penal > Ação Penal > Denúncia

Considerando as afirmativas abaixo, é CORRETO afirmar que:

A) A extinção da punibilidade, nos casos de transação penal em crimes ambientais de menor potencial ofensivo, dependerá de laudo de constatação de reparação do dano ambiental, enquanto que a realização da suspensão condicional do processo para os crimes ambientais dependerá da prévia composição do dano ambiental.
B) A superveniência de sentença condenatória não esvai a alegação de inépcia da denúncia, pois, como o réu defende-se do fato nela descrito, sempre estará prejudicado o exercício do contraditório e da ampla defesa.
C) A litispendência, pressuposto processual que deve ser analisado para fins de recebimento da denúncia, configura-se quando duas ou mais ações penais forem dirigidas contra o mesmo acusado, com a imputação da prática de condutas e qualificações jurídicas idênticas.
D) A justa causa é exigência legal para o recebimento da denúncia, instauração e processamento da ação penal, consubstanciando-se pela somatória de três componentes essenciais, quais sejam, a tipicidade, a punibilidade e a viabilidade quanto à autoria.
E) Nas ações penais públicas condicionadas à representação da ofendida de que trata a Lei nº 11.340/2006 (Lei Maria da Penha), só será admitida a renúncia à representação perante o juiz, em audiência especialmente designada com tal finalidade, antes do oferecimento da denúncia e ouvido o Ministério Público.

## Recomendação

Tratar a referência gramatical como uma pista de delimitação: procurar o complemento ou antecedente, verificar se ele é específico e se não é um cabeçalho com vários assuntos. “Como sendo” pode exigir preservar o conceito anterior à expressão. “Considerando” pode indicar somente uma condição. Uma lei mencionada ainda precisa corresponder a um escopo e ramo do catálogo. Não eliminar alternativas ou outras assertivas necessárias.

O próximo experimento útil é extrair relações com antecedentes e contrastar cabeçalho coletivo versus item específico, além de melhorar o vocabulário/escopo onde o foco já foi extraído mas a busca não o associa ao tema. Esse refinamento precisa ser genérico e medido, sem exceções por ID. A versão atual v5 permanece preservada: não há evidência para promover esta variante.

Teste executado sem rede/LLM; sete testes do extrator passaram. Aprovação de testes verifica o comportamento programado, não a correção jurídica. Metadados de origem continuam no classificador original como atributos auxiliares; não são lidos pelo extrator. Extras e fora automáticos permanecem desativados. Nenhuma decisão nova foi gravada no publicacao.csv da entrega.
