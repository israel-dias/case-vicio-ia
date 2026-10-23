# Experimento v7: marcadores condicionais e alternativas

Este é um novo teste, com a entrega v5 preservada. O objetivo foi retirar “considerando” da lista de marcadores e escolher quais campos devem alimentar a classificação. Não resolve questões nem usa LLM para escolher ou validar temas.

## Regras implementadas

| Situação | Campos usados |
|---|---|
| Enunciado e comando são apenas instruções sem conteúdo temático | Só alternativas. Enunciado, comando e metadados de origem vazios no texto efetivo |
| Cabeçalho com lista de assuntos distintos, sem caso ou lei específica, e alternativas temáticas | Só alternativas |
| Introdução ampla seguida de uma assertiva/caso informativo | Retira a introdução ampla e preserva o corpo |
| “Como sendo” | Preserva também o conceito definido antes do marcador |
| “Essa prática/conduta” | Procura citação ou janela anterior; “conduta abaixo” procura contexto posterior |
| “Considerando” | Não é marcador de foco. Uma lei ou fato informativo na mesma frase continua disponível |
| Alternativas Certo/Errado ou apenas I/II/III | Não substituem o conteúdo do enunciado |
| Homônimos em ramos diferentes | Não são contados como dois assuntos distintos pelo detector de listas; os IDs continuam separados na classificação e avaliação |

Definição operacional de enunciado indefinido: instrução sem conteúdo temático residual ou cabeçalho de lista de assuntos sem caso/lei específica. Não é um oráculo de compreensão: não considera todo caso concreto sem título literal como vazio. Os padrões e o vocabulário usados estão no código, sem regras por ID.

Zerar o enunciado significa impedir que seu TEXTO participe da busca e dos atributos, também retirando comando e origem que poderiam reintroduzi-lo. A estrutura ainda decide o roteamento. Os modelos normalizam atributos e têm interceptos: um atributo bruto zero não obriga sua parcela algébrica centralizada a ser zero. Isso não reintroduz palavras descartadas; a invariância dos escores foi testada com enunciados genéricos diferentes e as mesmas alternativas.

As alternativas são analisadas integralmente. O sistema não sabe automaticamente qual é a alternativa correta e não usa respostas escritas por um LLM. As retomadas são aproximações por regras e janelas, não análise semântica perfeita.

## Como o teste foi executado

Mesmos cinco grupos externos e quatro internos das versões anteriores. O ajuste e a calibração de cada grupo usam somente seus dados de treino internos. Os 100 rótulos e resultados anteriores já foram expostos; esta é uma nova rodada de desenvolvimento, não avaliação externa cega. Dois métodos foram fixados antes da execução: roteamento sem foco e mescla condicional (60% da busca original normalizada + 40% do foco normalizado, quando utilizável).

Na mescla, o modelo recebe os 36 atributos da v5 mais cinco sinais: similaridade do foco, diferença ao melhor foco, presença de foco utilizável e apoios de norma/artigo extraídos do foco. A compatibilidade e a calibração são ajustadas novamente. Não se eleva a confiança à mão nem se publica só pela presença do marcador.

## Correção durante a implementação

A execução 001 revelou dois defeitos na detecção de listas: contava homônimos como assuntos distintos e podia descartar uma pergunta específica que mencionava dois assuntos. A execução 002 exige estrutura de cabeçalho, distingue nomes de IDs, preserva leis específicas e narrativas. Os testes de regressão foram acrescentados. Resultados e código da primeira tentativa estão preservados em experimentos/mescla_marcadores_v7_001. Essa inspeção orientou o ajuste; os resultados não são uma comparação cega de versões.

## Resultado nos 100 rótulos

| Versão | Sugestões corretas/100 | Publicadas na avaliação por grupos | Corretas publicadas | Precisão observada |
|---|---:|---:|---:|---:|
| Controle v5 | 66 | 25 | 24 | 96,00% |
| mescla_condicional | 67 | 16 | 16 | 100.00% |
| roteamento_sem_foco | 67 | 22 | 21 | 95.45% |

O ganho de sugestões corretas foi de somente 1/100. A mescla acertou as 16 publicadas nos grupos externos, mas publicou menos do que o controle (25). Dezesseis acertos não provam precisão mínima de 95% na população nem nas questões recentes.

## Simulação nas 559 avaliadas pela empresa

| Versão | Publicar | Revisar | Cobertura | Média das confianças publicadas |
|---|---:|---:|---:|---:|
| Controle v5 | 231 | 328 | 41,32% | 90,44% |
| mescla_condicional | 289 | 270 | 51.70% | 86.84% |
| roteamento_sem_foco | 227 | 332 | 40.61% | 90.31% |

A mescla passou 72 revisões para publicação e 14 publicações para revisão: saldo +58. Mudou 28 sugestões de tema. Nas 300 recentes, publicou 162 e revisou 138. Foram zerados enunciado/comando/origem em 18 das 559, removidos 16 cabeçalhos amplos e encontrados 125 focos utilizáveis. Os grupos podem se sobrepor.

O corte final da mescla caiu para 0.67951634, escolhido pelo procedimento nos 100 sinais OOF: 48 acertos em 50 selecionados. Na v5, o corte era 0,77385539. A redução não foi fixada à mão, mas é parte importante do aumento de volume; não se pode atribuir todas as novas publicações a uma melhoria semântica.

A média de confiança de 86,84% está abaixo da meta de 95%. Essa média também depende de um calibrador com pouco suporte. O resultado não permite afirmar que as 289 publicações atingem a meta. Não se promove esta simulação automaticamente nem se altera publicacao.csv/previsao.txt da entrega. Mais publicações, isoladamente, não demonstram melhora de qualidade.

## Casos completos para conferir o comportamento

As sugestões abaixo são saídas do sistema sem rótulo oficial disponível; não são validação jurídica feita pelo assistente.

### Q0543

Em matéria processual penal, é correto afirmar que:

Comando original: 
A) É nulo o julgamento da apelação se, após a manifestação nos autos da renúncia do único defensor, o réu não foi previamente intimado para constituir outro.
B) Independente de transitado em julgado o ato judicial que se alega tenha desrespeitado decisão do Supremo Tribunal Federal, caberá reclamação à presidência desta corte.
C) As questões prejudiciais devolutivas obrigatórias são as que tratam de controvérsias sérias e fundadas sobre o estado civil das pessoas ou propriedade de bens imóveis, devendo ser, obrigatoriamente, suspenso o processo criminal até o trânsito em julgado da sentença que trata da controvérsia.
D) Constitui nulidade relativa a falta de intimação do denunciado para oferecer contrarrazões ao recurso interposto da rejeição da denúncia, bastando para supri-la a nomeação de defensor dativo.
E) Desde que fundamentado, é permitido o uso de algemas em mulheres grávidas durante os atos médico-hospitalares preparatórios para a realização do parto e durante o trabalho de parto, bem como em mulheres durante o período de puerpério imediato.

Rota: alternativas_exclusivas; peso textual do enunciado 0; motivo instrucao_sem_tema.
Cabeçalho removido: nenhum
Foco utilizável: nenhum
Controle: revisar, tema 5560, confiança 19.44%.
Mescla: revisar, sugestão Processo Penal > Procedimento Ordinário, confiança 24.56%.

### Q0659

A respeito do crime de lavagem de dinheiro e dos crimes contra o sistema financeiro nacional e contra a fé pública, assinale a opção correta à luz do entendimento do STF.

Comando original: 
A) Em face dos princípios da especialidade e subsidiariedade, na falsificação de procurações, de reconhecimento de firmas e de documentos do BACEN, as condutas criminais serão subsumidas pelo crime-fim: negociação do título falso.
B) Ao delito de emissão de vinte e cinco moedas falsas nos valores de dois reais é aplicável o princípio da insignificância, em face da inexistência de grave prejuízo ao sistema financeiro e da observância de princípios constitucionais aplicáveis aos crimes.
C) Para a configuração do crime de lavagem ou ocultação de valores, é imprescindível o especial elemento subjetivo, sob pena de exclusão da tipicidade.
D) Para a instauração da ação penal ou para o ato de recebimento da denúncia de crime de lavagem de dinheiro, faz-se necessária a certeza quanto aos crimes antecedentes, uma vez que a tipificação está atrelada aos bens, direitos ou valores ocultados provenientes, direta ou indiretamente, de um dos crimes antecedentes previstos em lei.
E) O recebimento de dinheiro em espécie que o réu saiba ser de origem criminosa, mediante mecanismos de ocultação e dissimulação da natureza, origem, localização, destinação e propriedade dos valores, com auxílio dos agentes envolvidos no pagamento do dinheiro, caracteriza crime contra o sistema financeiro nacional.

Rota: alternativas_exclusivas; peso textual do enunciado 0; motivo lista_de_assuntos_sem_caso.
Cabeçalho removido: nenhum
Foco utilizável: nenhum
Controle: publicar, tema 6723, confiança 83.03%.
Mescla: publicar, sugestão Penal > Lavagem de Dinheiro, confiança 86.59%.

### Q0638

Marcelo, analista de sistema de informações em uma repartição pública, estava em uma grande dúvida sobre os crimes praticados por funcionário público contra a administração em geral. A principal dúvida de Marcelo era em relação à conduta típica de “modificar ou alterar, o funcionário, sistema de informações ou programa de informática sem autorização ou solicitação de autoridade competente”. Para efeitos do Código Penal, a prática desta conduta configura o crime de:

Comando original: 
A) Concussão.
B) Inserção de dados falsos em sistema de informações.
C) Excesso de exação.
D) Modificação ou alteração não autorizada de sistema de informações.
E) Peculato.

Rota: enunciado_preservado; peso textual do enunciado 1; motivo conteudo_informativo.
Cabeçalho removido: nenhum
Foco utilizável: conduta típica de “modificar ou alterar, o funcionário, sistema de informações ou programa de informática sem autorização ou solicitação de autoridade competente”
Controle: revisar, tema 5087, confiança 76.13%.
Mescla: publicar, sugestão Penal > Dos Crimes Contra a Administração Pública, confiança 69.46%.

### Q0508

A respeito da interceptação das comunicações telefônicas, julgue os itens a seguir, com base no entendimento do STF. É possível a prorrogação do prazo de autorização para a interceptação telefônica, mesmo que sucessiva, especialmente quando se tratar de fato complexo que exija investigação diferenciada e contínua.

Comando original: 
C) Certo
E) Errado

Rota: enunciado_preservado; peso textual do enunciado 1; motivo conteudo_informativo.
Cabeçalho removido: nenhum
Foco utilizável: interceptação das comunicações telefônicas
Controle: revisar, tema 4700, confiança 64.98%.
Mescla: revisar, sugestão Direito Penal - Legislação Especial > Interceptação Telefônica, confiança 52.21%.

### Q0555

Em relação ao livramento condicional:

Comando original: 
A) A Lei de Execução Penal permite o livramento condicional aos condenados pela prática de feminicídio, salvo nos casos de reincidência.
B) Conforme tese firmada pelo Superior Tribunal de Justiça, o juiz da execução criminal fica impedido de considerar, para fins de concessão do livramento condicional, o histórico prisional e as faltas disciplinares praticadas pelo sentenciado fora do período de 12 meses no Código Penal.
C) A Lei de Execução Penal veda a concessão de livramento condicional ao condenado por crime hediondo ou equiparado, com resultado morte, independentemente de ser primário ou reincidente.
D) O Código Penal veda que o juiz da execução penal condicione a concessão do livramento condicional à reparação do dano causado pela infração.
E) Segundo o Código Penal, é vedado o livramento condicional ao condenado reincidente específico em crimes praticados com violência ou grave ameaça.

Rota: enunciado_preservado; peso textual do enunciado 1; motivo conteudo_informativo.
Cabeçalho removido: nenhum
Foco utilizável: livramento condicional
Controle: revisar, tema 6734, confiança 28.95%.
Mescla: publicar, sugestão Penal > Teoria da Pena, confiança 89.46%.

### Q0441

A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. Considere a seguinte situação hipotética. Um indivíduo foi condenado a pena privativa de liberdade de dois anos de reclusão, em regime aberto, pela prática do crime de furto qualificado. Irresignada, a defesa apelou para o tribunal de justiça, que deu provimento ao recurso, reconhecendo a causa de diminuição da pena referente ao arrependimento posterior. Assim, a pena privativa de liberdade foi reduzida para 1 ano e 4 meses de reclusão. Nessa situação, cabe ao tribunal de justiça converter o feito em diligência, a fim de que o Ministério Público ofereça a proposta do sursis processual.

Comando original: 
C) Certo
E) Errado

Rota: enunciado_preservado; peso textual do enunciado 1; motivo conteudo_informativo.
Cabeçalho removido: A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. 
Foco utilizável: arrependimento posterior
Controle: revisar, tema 5199, confiança 70.13%.
Mescla: revisar, sugestão Penal > Iter Criminis, confiança 8.48%.

### Q0395

A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. Ocorrendo a extinção da punibilidade no tocante à pretensão punitiva do Estado, não cabe o ajuizamento de revisão criminal pelo próprio réu ou por procurador legalmente habilitado.

Comando original: 
C) Certo
E) Errado

Rota: enunciado_preservado; peso textual do enunciado 1; motivo conteudo_informativo.
Cabeçalho removido: A respeito de revisão criminal, habeas corpus e suspensão condicional do processo (Lei n.º 9.099/1995), julgue os itens subseqüentes. 
Foco utilizável: pretensão punitiva do Estado, não cabe o ajuizamento de revisão criminal pelo próprio réu ou por procurador legalmente habilitado
Controle: revisar, tema 5476, confiança 69.91%.
Mescla: publicar, sugestão Penal > Prescrição, confiança 71.52%.

Na Q0638, a confiança da mescla é 69,46%, abaixo dos 76,13% da v5, mas o novo corte de 67,95% libera o item. Não é exemplo de aumento de confiança: é exemplo de mudança da política. Na Q0508 o foco foi localizado, mas a confiança continua baixa. Na Q0543 o enunciado genérico foi zerado e mesmo assim o sistema se abstém: escolher o campo mais útil não garante identificar o tema.

## Verificações e reprodução

25 testes passaram, cobrindo roteamento, homônimos, leis específicas, narrativa, negação, scripts, proibição de marcadores nas alternativas, invariância por ID e não reintrodução do texto zerado. Testes funcionais não provam acerto jurídico.

A reprodução com pesos salvos processou 659 itens sem ler folha-verdade, sem treino e sem chamada a LLM. Nas 559, todas as decisões, temas e confianças corresponderam à simulação registrada. O total dos 659 também inclui os 100 usados no ajuste final: não confundir suas previsões ajustadas com os resultados por grupos externos da tabela acima.

Próxima investigação: analisar a calibração e o efeito da mudança de corte, além dos erros de associação ao catálogo. Os resultados atuais apoiam continuar investigando a hipótese, mas não substituir a entrega por alegação de precisão de 95%. Nenhuma anotação jurídica por ID foi criada.
