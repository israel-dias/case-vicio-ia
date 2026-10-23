# Vocabulário v8 — resultado experimental

Não é uma nova entrega com precisão validada. Os arquivos publicacao.csv e previsao.txt da raiz continuam sendo controles v5 preservados. Nenhuma classificação jurídica ou resposta por ID foi escrita pelo assistente para as 559 avaliadas.

## O que mudou

Dicionário com 16 grupos e 53 padrões, proposto como preparação de dados a partir dos títulos, escopos e expressões discutidas. Contém nomes de assuntos, descrições de conduta e leis citadas. Não foi validado por especialista jurídico independente. As frequências das 659 não são pesos de acerto. Houve apoio do dicionário em 241 itens.

As regras v7 são mantidas: considerando não é marcador; enunciado genérico pode ser zerado; Certo/Errado não substitui o enunciado; introduções, retomadas e definições recebem o tratamento documentado. O dicionário lê os campos após o roteamento e não lê metadados de origem. Sinônimos, padrões sobrepostos e repetições do mesmo grupo contam uma vez por campo. Homônimos não são fundidos.

Opções testadas: (1) preservar a busca v7 e acrescentar sete atributos de vocabulário à confiança; (2) acrescentar esses atributos e reordenar a busca; (3) usar o vocabulário somente na busca e preservar a compatibilidade v7 de 41 atributos, refazendo a calibração e o corte. A terceira ablação foi proposta depois do resultado das duas primeiras; não foi hipótese cega inicial.

A busca modificada combina 75% da busca v7 normalizada com 25% do apoio do vocabulário normalizado. O apoio separa enunciado, comando e alternativas. No campo efetivo zerado o texto não participa. Certo/Errado usa o conteúdo temático do enunciado. Nenhuma expressão autoriza publicação sozinha.

Os candidatos continuam sendo famílias de nível 1: expressões de filhos ajudam o pai, sem escolher automaticamente o subtema. Por exemplo, concussão e corrupção passiva ajudam a mesma família de crimes contra a Administração Pública; este teste não demonstra separação automática entre esses filhos.

## Avaliação nos 100 exemplos

Mesmos cinco grupos externos e quatro internos. Cada grupo externo usa pesos, calibrador e corte ajustados sem seus rótulos. Todos os rótulos já foram expostos e reutilizados: é desenvolvimento comparativo, não teste externo novo. Meta de corte: 95% empírica nos dados internos, com suporte mínimo de dez.

| Opção | Sugestões corretas/100 | Publicadas por grupos | Corretas publicadas | Brier |
|---|---:|---:|---:|---:|
| Controle v7 | 67 | 16 | 16 | 0.1677 |
| Vocabulário fixo | 67 | 13 | 13 | 0.1720 |
| Busca e novos atributos | 70 | 14 | 14 | 0.1706 |
| Vocabulário só na busca | 70 | 16 | 16 | 0.1678 |

Os 100 incluem 8 referências fora. O protótipo não decide fora automaticamente; elas não recebem acerto top1 de tema, embora possam ser encaminhadas para revisão. Dezesseis publicações acertadas não comprovam precisão mínima de 95% nas 559.

## Onde o vocabulário ajudou

Q0052: a expressão remição e os termos de execução ajudaram a trocar Teoria da Pena (Parte 1) por Lei de Execução Penal, de acordo com a referência oficial. Q0290: a lei 9.099/1995 e Juizados Especiais ajudaram a trocar Ação Penal por Juizado Especial Criminal. Q0315: prescrição ajudou a trocar Crimes de Trânsito por Prescrição. São os três erros que passaram a acertos.

Q0265 mudou de Concurso de Crimes para Prescrição, mas o primeiro já era aceito como extra oficial: não é erro corrigido. Outros dois erros continuaram erros. Não houve acerto que passou a erro nesses seis temas alterados. Correção sobre Q0308: os registros v7/v8 consultados já sugerem Inquérito Policial (5498), aceito como pai do rótulo oficial 5501. Na avaliação por grupos v8 ela ficou em revisão (70,87% abaixo do corte do grupo 1, 82,30%). Na reprodução final, ajustada com os 100 rótulos, ficou publicar (82,70% acima de 70,10%). O relato anterior confundiu o erro do baseline antigo com o estado atual; não houve mudança de classificação nesta correção documental.

### Q0052
Uma pessoa presa em regime fechado, definitivamente condenada, prestou 300 dias de trabalho prisional intra muros, bem como, simultaneamente, teve frequência escolar de 200 horas, concluindo atividade de ensino médio ao longo do cumprimento da pena. Cada 12 (doze) horas foram divididas em 3 (três) dias de estudo. Esse indivíduo I. tem direito à remição de pena, à razão de 1 (um) dia de pena a cada 3 (três) dias de trabalho. II. tem direito à remição de pena, à razão de 1 (um) dia de pena a cada 12 (doze) horas de frequência escolar. III. tem direito à remição de pena, com o acréscimo de 1/3 (um terço) de toda a remição conquistada durante o cumprimento da pena devido à conclusão do ensino médio. IV. em caso da prática de falta grave, obrigatoriamente, perderá 1/3 (um terço) da remição conquistada, recomeçando a contagem a partir da data da infração disciplinar.

A) II, III e IV.
B) I e III.
C) I e II.
D) III e IV.
E) I, II e IV.

Referência oficial: Direito Penal - Legislação Especial > Lei de Execução Penal.
V7: Penal > Teoria da Pena (Parte 1).
V8 só na busca: Direito Penal - Legislação Especial > Lei de Execução Penal.

### Q0290
No que diz respeito ao preceituado na Lei nº 9.099/1995, a qual disciplina os Juizados especiais criminais, assinale a alternativa incorreta.

A) A ação penal relativa ao crime de lesão corporal dolosa, em todas as suas modalidades, será pública incondicionada, já o crime de lesão culposa, terá como correspondente a ação penal pública condicionada à representação da vítima ou de seu representante legal
B) Na fase preliminar, a autoridade policial que tomar conhecimento da ocorrência deverá lavrar termo circunstanciado e o encaminhar imediatamente ao Juizado, com o autor do fato e a vítima, providenciando as requisições dos exames periciais necessários
C) A citação será pessoal e far-se-á no próprio Juizado, sempre que possível, ou por mandado
D) Os atos processuais serão públicos e poderão realizar-se em horário noturno, conforme dispuserem as normas de organização judiciária
E) Todas as provas serão produzidas na audiência de instrução e julgamento, podendo o Juiz limitar ou excluir as que considerar excessivas, impertinentes ou protelatórias

Referência oficial: Direito Penal - Legislação Especial > Juizado Especial Criminal.
V7: Processo Penal > Ação Penal.
V8 só na busca: Direito Penal - Legislação Especial > Juizado Especial Criminal.

### Q0315
Paulo, nascido em 15/8/1996, foi denunciado em 24/5/2020, pela prática do crime de roubo majorado tentado, que teria sido praticado em 7/4/2016. Recebida a denúncia em 30/5/2020, Paulo foi condenado a uma pena de 2 anos e 9 meses pela prática delitiva em 20/10/2021, tendo a condenação transitado em julgado em 1/12/2021. Nessa situação, a prescrição, segundo a jurisprudência atual do STF,

A) já teria ocorrido antes do oferecimento da denúncia.
B) ocorrerá em 2 anos após o trânsito em julgado da condenação, quer para a defesa quer para a acusação.
C) ocorrerá em 4 anos após o trânsito em julgado da condenação, tanto para a defesa quanto para a acusação.
D) ocorrerá em 6 anos após o trânsito em julgado da condenação para a defesa e para a acusação.
E) ocorrerá em 8 anos após o trânsito em julgado da condenação, tanto para a defesa quanto para a acusação.

Referência oficial: Penal > Prescrição.
V7: Direito Penal - Legislação Especial > Crimes de Trânsito.
V8 só na busca: Penal > Prescrição.

## Simulação nas 559 — precisão desconhecida

| Opção | Publicar | Revisar | Cobertura | Média das confianças publicadas |
|---|---:|---:|---:|---:|
| Controle v7 | 289 | 270 | 51,70% | 86,84% |
| Vocabulário fixo | 132 | 427 | 23.61% | 92.98% |
| Busca e novos atributos | 132 | 427 | 23.61% | 93.68% |
| Vocabulário só na busca | 287 | 272 | 51.34% | 87.86% |

As sete novas medidas de confiança não trouxeram vantagem suficiente neste ensaio: maior corte e menos cobertura. A variante só na busca isolou o benefício na recuperação, mantendo aproximadamente o volume da v7. Seu corte final é 70,10%; a média das probabilidades publicadas é 87,86%, ainda abaixo de 95%. A média vem de um calibrador com pouco suporte, não mede acerto real. O volume nas 559 não escolheu palavras/pesos/limiar antes das simulações.

## Verificação e continuidade

16 testes passaram: expressão com palavras intercaladas, lei com pontuação, singular/plural, homônimos, ID não utilizado como atributo, metadados fora do dicionário, script invisível, roteamento zerado, repetições sem inflação e ausência dos sete novos atributos na ablação. Testes não comprovam acerto jurídico.

A reprodução com pesos salvos processou 659 itens com leitor de rótulos e rede bloqueados, sem treinar ou chamar LLM. As 559 decisões, temas e confianças corresponderam à simulação. As previsões dos 100 no ajuste final não devem ser confundidas com a avaliação por grupos. Custo API zero; experimentos medidos em aproximadamente 34 e 31 segundos neste ambiente.

A hipótese de vocabulário merece continuidade na busca, com um ganho pequeno observado na amostra. Ainda é necessário melhorar a calibração e avaliar em dados com rótulos novos. Não se elevam confianças à mão. Não se promove este pacote experimental para uma entrega alegando precisão mínima de 95%.
