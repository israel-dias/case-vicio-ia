# V19 — expressões completas, escopos e trecho de cobrança

Esta rodada amplia o teste após a Q0274. A versão anterior recuperou o tema dessa referência por normalização de conceitos compostos, mas não mudou temas ou decisões nas 559. Não substituímos a entrega formal nem criamos exceções por ID.

## Estratégias testadas

1. **Frases completas.** A expressão é procurada na ordem das palavras, admitindo preposições e flexões previstas. “Morte consumada… o agente” não vira “morte do agente”. O sinal pesa 15% na recuperação, sem impor confiança.
2. **Vocabulário dos escopos.** Expressões e termos distintivos são extraídos das descrições já versionadas do catálogo. “Latrocínio” pode apoiar o ramo que descreve Roubo. Uma palavra precisa ter pelo menos sete letras, não estar na lista genérica e ocorrer em apenas uma família do catálogo para ser usada como vocábulo distintivo isolado. Uma derivação adjetiva, como “consumada”, não vira um substantivo jurídico isolado; continua disponível em compostos. Esse conjunto de sinais pesa 25% na recuperação.
3. **Trecho da cobrança.** As mesmas evidências são avaliadas na cobrança explícita; uma retomada do caso inclui a frase anterior. O texto integral permanece apoiando a recuperação. Todas as proposições romanas e V/F são mantidas; alternativas C/E não fornecem palavras temáticas. Essa vista pesa 25% na recuperação.

O restante do peso vem do ranking V18, preservado como apoio. Os novos pesos são de busca entre candidatos; não são pontos percentuais de precisão. As expressões apenas influenciam a escolha. A confiança e a regra de publicação são aprendidas separadamente dentro dos folds. Não há piso automático de 70% ou 80%, publicação só por título nem exclusão por baixa semelhança.

O catálogo mantém IDs e ramos distintos, inclusive em títulos iguais. Os escopos são propostas preparadas, sem validação jurídica independente; um vocábulo raro no catálogo pode ser semanticamente pouco específico. A avaliação dos erros corrigidos e dos acertos prejudicados serve justamente para testar essa hipótese.

## Como foi medido

Usamos as mesmas 100 referências, já expostas e reutilizadas, com cinco folds externos e quatro internos. Duplicatas são agrupadas pelo hash original; a questão avaliada não entra no treino do seu fold. A formulação das hipóteses conhece erros anteriores, portanto esta é validação de desenvolvimento, sem alegação de teste cego.

Os modelos de compatibilidade, calibradores e limiares são ajustados nos treinos internos. As três hipóteses e seus pesos foram fixados antes da avaliação desta rodada. A escolha de uma rota final é registrada antes da aplicação às 559. Nelas mostramos decisões e cobertura, sem precisão real. Os 300 itens recentes não têm rótulos disponíveis.

A régua aceita central, extra oficial, ancestral ou descendente de um deles; irmãos não são equivalentes. As raízes e temas inativos continuam inválidos. Não usamos gabarito resolvido pelo assistente, votos ou validação por LLM. A inferência aplica modelos estatísticos clássicos congelados e não lê a folha-verdade, não treina nem recalibra.

O controle principal desta comparação é a V18 morfológica: 74/100 temas aceitos e 36/39 publicações corretas (92,31%) no desenvolvimento, com 139 publicações nas 559. Esse comparador isolado não substitui o controle composto V16 de 394/559, cuja precisão real permanece desconhecida.

## Resultado observado

| Variante | Tema aceito /100 | Corretas/publicadas | Publicadas /559 |
|---|---:|---:|---:|
| controle_atual | 74 | 36/39 (92.31%) | 139 |
| frases_completas | 72 | 19/21 (90.48%) | 92 |
| vocabulario_escopos | 73 | 26/32 (81.25%) | 94 |
| passagem_cobrada | 73 | 26/31 (83.87%) | 93 |
| selecionado_internamente | 74 | 40/47 (85.11%) | 139 |

As três estratégias diretas pioraram o controle e não foram promovidas. Q0106 e Q0188 foram recuperadas por vocabulário/trecho, mas Q0052, Q0058 e Q0315 perderam o enquadramento correto. Uma menção exata ou um termo raro na descrição não bastam para dizer que esse é o objeto da cobrança.

Na Q0058, a alternativa C cita medidas de segurança e internação, mas o enunciado trata da relação entre sistema penal e pobreza. O novo sinal passou a privilegiar o distrator. Na Q0315, “trânsito em julgado” emprestou o termo isolado “trânsito” a Crimes de Trânsito. Na Q0052, “regime fechado” contextualiza o trabalho e o estudo de uma pessoa presa; a cobrança das assertivas trata de remição, e o marcador levou a Teoria da Pena. Os exemplos completos e as evidências estão em `analises/exemplos_expressoes_v19.json`.

## Proteção por disciplina prevista — diagnóstico adaptativo

Após observar as perdas, testamos manter o controle quando a nova sugestão muda a disciplina por ele prevista. Não usamos a disciplina de origem. Essa composição pode impedir corrigir uma disciplina inicialmente errada, e estar na mesma disciplina não equivale à régua de pai/filho. As confianças são herdadas das rotas, sem calibração global; não são probabilidades validadas para a composição.

| Composição | Tema aceito /100 | Corretas/publicadas | Publicadas /559 |
|---|---:|---:|---:|
| frases_completas + guarda | 73 | 20/21 (95.24%) | 94 |
| vocabulario_escopos + guarda | 76 | 27/32 (84.38%) | 97 |
| passagem_cobrada + guarda | 76 | 27/32 (84.38%) | 97 |

Vocabulário e trecho com a guarda chegaram a 76/100 temas aceitos, mas a precisão das publicadas foi 27/32 (84,38%). A composição de frases ficou em 20/21 (95,24%), com menor cobertura e um acerto de tema perdido. Nenhuma superou a solução composta anterior de 48/50 nas referências e 394/559 publicações sem precisão real conhecida. A rodada termina sem promoção e com uma hipótese adicional para testar: contexto dos termos, fonte do sinal e intensidade absoluta da evidência.
