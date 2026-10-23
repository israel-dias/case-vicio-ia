# Classificação de tópicos — Vício / Método VDE

Versão consolidada de 15/10/2026. Preparação, classificação e redação assistidas
pelo ChatGPT. Não houve validação por especialista independente.

## 1. Problema, hipóteses e método

O objetivo é publicar questões no ramo adequado com precisão mínima de 95%,
maximizando cobertura. O erro de publicação é mais caro que encaminhar dúvida
ao professor. A entrega propõe **229 publicar, 126 revisar e 4 fora**, em 359 IDs
únicos: cobertura **63,7883%**. Precisão real ainda não foi medida.

A primeira hipótese foi que conteúdo, caminho hierárquico e possibilidade de
abstenção seriam suficientes para um protótipo pequeno e auditável. Usei fluxo
assistido pela assinatura existente: Python prepara, valida e registra; o chat
interpreta; respostas e intervenções ficam salvas. Não há inferência autônoma
por API. Reproduzir o pós-processamento não reproduz necessariamente uma nova
resposta do serviço, cujo modelo exato não foi registrado.

O piloto de vinte questões foi executado duas vezes. A v1 sugeriu 7 publicações
e 13 revisões; a v2, 10 e 10. Houve cinco mudanças de decisão e cinco de tema,
em nove IDs distintos. Não considero isso ganho medido: instruções, contexto
e possivelmente modelo diferiram. O piloto serviu ao desenvolvimento, não foi
usado como conjunto independente de avaliação.

Descartados: copiar os assuntos de origem; unir homônimos; publicar apenas por
confiança alta; preencher limites de “Parte 1/Parte 2” por intuição; selecionar
o núcleo por uma alternativa isolada. Na Q0017, o título “Defesa Preliminar”
parece adequado, mas o pai ordinário conflita com o rito especial: voltou à revisão.
Aumentar indiscriminadamente o prompt com descrições repetidas tampouco resolve
limites semânticos ausentes. A v3 incorpora essas observações e a orientação de
Carla: considerar conteúdo/ramo e registrar premissas, sem equivalências presumidas.

## 2. Diagnóstico dos anexos e da taxonomia

São 359 questões e 377 temas, dos quais 375 ativos. IDs, pais, níveis e ausência
de ciclos foram verificados. Os originais foram preservados e vinculados por
SHA-256. A limpeza remove apresentação HTML e normaliza espaços/escapes sem
reescrever texto, negações ou alternativas. Campo comando vazio não causa descarte:
há 94 ocorrências, algumas com a instrução no enunciado.

O catálogo tem oito grupos de títulos repetidos e vinte descrições ausentes.
Outras 335 descrições seguem prefixos de importação, frequentemente indicando
posição e quantidade, sem delimitar o conteúdo. Grafias distintas também podem
encobrir sobreposição, como os temas de crimes contra idosos.

As dificuldades principais são: metadados de origem incorretos; categorias em
ramos diferentes com títulos semelhantes; subdivisões “Parte” sem definição;
enunciados genéricos com alternativas de vários assuntos; e contexto ausente,
como a Q0219. As quatro exclusões finais são Q0039 (cartel/ordem econômica sem
tema ativo correspondente), Q0113 (prescrição disciplinar administrativa),
Q0142 (isenção de ITCD) e Q0168 (crimes esportivos). Na Q0298, a fronteira entre
consumo na Lei 8.137 e o tema “crimes previstos no CDC” ficou em revisão, não fora.

Um pai substantivo é usado quando representa de fato a combinação de filhos ou
quando falta filho correspondente. Exemplo: Q0106 no ramo patrimonial, sem filho
explícito de “Outras fraudes”. Raízes de disciplinas não foram usadas para publicar.
Irmãos não são equivalentes; ancestral e descendente têm relação diferente.
As premissas de preferência por ramo processual estruturado aparecem nas justificativas.

## 3. Publicação, previsão e limites

O JSON contém sugestão, tema, extras, justificativa, concorrentes e alertas. O
importador exige uma resposta por ID, temas ativos e tipos válidos, preservando
resposta original e prompt de referência. Essa validação não verifica Direito.
As 339 questões fora do piloto foram lidas e classificadas pelo assistente nesta
conversa, em 34 lotes. As vinte decisões do piloto e o ajuste Q0298 estão registrados
separadamente, com antes/depois. O candidato precisa compreender e conferir esse
julgamento assistido; não foi realizada auditoria humana independente.

A previsão ex ante é **96%**, com cenário subjetivo **85%-99%**. O orçamento
hipotético de erro é 2% de identificação do núcleo, 1% de escopo/ramo e 1% residual.
São premissas, não frequências observadas; podem se sobrepor. A faixa admite
descumprir a meta e não limita o risco real. Não é intervalo de confiança, média
de autoavaliação validada, nem demonstração de precisão. A confiança no CSV é
subjetiva e não calibrada. Em fora, zero significa ausência de tema central.

Sem rótulos independentes, o passo mais valioso é uma amostra aleatória das
publicadas avaliada por professor sem acesso à sugestão inicial, além de análise
separada dos casos difíceis. Não ajustar a política e depois chamar a mesma amostra
de teste. Registrar adjudicação e erros por ramo; só então calibrar probabilidades,
intervalos e limiar de publicação. Concordância entre rodadas não substitui isso.

## 4. Produção com 50 mil questões por semana

Integraria o fluxo de importação com fila, validação de esquema, normalização,
hash de conteúdo, deduplicação e versionamento de taxonomia. Embeddings serviriam
para recuperar candidatos e casos parecidos, sem decidir equivalência. Com rótulos
revisados suficientes, compararia classificador supervisionado menor com LLM em
conjunto temporal separado. O LLM receberia questão, candidatos e limites de escopo;
conflitos, imagem/contexto ausente e baixa evidência iriam à revisão.

O orquestrador pode ser determinístico. Agentes de pesquisa só seriam acrescentados
se uma avaliação demonstrasse benefício em dúvidas com fontes. Não treinaria nem
calibraria um modelo com as próprias respostas tratadas como verdade.

Exemplo de orçamento de API, não executado: 3.000 tokens de entrada e 300 de saída
faturada por item no GPT-5.4 mini custariam US$ 0,0036 por questão. Uma segunda
passagem em 10% dos casos, com GPT-5.4, 5.000/600 tokens, acrescentaria US$ 0,00215
por questão do fluxo. Total: **US$ 287,50/semana**, ou **US$ 0,00575/questão**,
sem embeddings, infraestrutura, buscas, repetição ou professores. Preços consultados
em 15/10/2026; tokens são hipóteses, incluindo raciocínio faturado quando aplicável.
Não são os modelos identificados nem o consumo medido deste chat.

No case, API executada custou US$ 0; assinatura existente não foi rateada e tokens
internos não foram medidos. Tempo total humano/chat não foi instrumentado. Os
horários dos registros são de importação; não representam latência do modelo.

Se a taxa atual de revisão se repetisse, seriam cerca de 17.549 questões/semana;
a um minuto por questão, aproximadamente 292,5 horas humanas. Esse cenário torna
prioritária a definição dos temas. Mediria continuamente precisão por ramo nas
publicadas, cobertura, taxa/tempo de revisão, exclusões incorretas, drift e reportes
de alunos. Erros confirmados realimentariam o catálogo e uma base de avaliação
versionada, com rollback de política/modelo e auditoria amostral mesmo nos casos fáceis.

## 5. Memo para o professor

O problema principal não está apenas no texto das questões. Há temas que parecem
iguais, mas ficam em lugares diferentes, e outros que não explicam o que incluem.
Uma máquina ou pessoa pode reconhecer o assunto e ainda escolher o ID errado.

Recomendo definir exemplos de inclusão/exclusão para os temas sobrepostos,
explicar o conteúdo de cada “Parte” e revisar o posicionamento de “Defesa Preliminar”.
Não proponho fundir IDs sem avaliar seu uso pedagógico. Quando dois temas realmente
representarem o mesmo conteúdo, é melhor declarar a relação e preservar um histórico
de migração, evitando referências quebradas.

As 126 sugestões de revisão informam motivos concretos: dúvida de ramo, mistura
de matérias, limite ausente ou contexto incompleto. As quatro questões fora precisam
de confirmação da lacuna ou de novo tema, não de encaixe em categoria genérica.
Também precisamos conferir a fronteira CDC/Lei 8.137 antes de excluir a Q0298.

Peço uma pequena referência independente com enquadramentos e justificativas,
incluindo amostra aleatória das 229 publicadas. Ela permitirá identificar erros que
o mesmo assistente tende a repetir, estimar melhor a precisão e reduzir a fila com
segurança. A meta de 95% continua sendo o critério; não foi comprovada nesta entrega.

### Referências

Anexos do case; orientação de Carla em 15/10/2026; [CPP](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm),
[Código Penal](https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm),
[LEP](https://www.planalto.gov.br/ccivil_03/leis/l7210.htm) e
[Lei 8.137](https://www.planalto.gov.br/ccivil_03/leis/l8137.htm), consultas pontuais.
Preços: [GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini) e
[GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4), 15/10/2026.
As fontes legais sustentam assuntos, não os IDs internos ou todo o gabarito.
