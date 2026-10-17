# Classificação de tópicos — Vício / Método VDE

16/10/2026. Protótipo e reexame assistidos pelo ChatGPT; sem validação jurídica
independente. O julgamento do candidato incluiu questionar e corrigir o critério.

## 1. Método, experimentos e resultado

O objetivo é publicar no ramo correto com precisão mínima de 95%, maximizando
cobertura. A proposta atual contém **329 publicar, 25 revisar e 5 fora** em 359 IDs:
cobertura **91,6435%**. Precisão real não medida; a meta permanece não comprovada.

Usei Python para preparar, validar e consolidar; a interpretação foi assistida
pela assinatura existente do ChatGPT. Respostas, prompts de referência e ajustes
ficam registrados. Não há inferência autônoma por API. Reproduzir a consolidação
salva não reproduz necessariamente uma nova resposta do serviço.

O piloto de vinte itens teve duas rodadas: v1 sugeriu 7 publicações/13 revisões;
v2, 10/10. Houve cinco mudanças de decisão e cinco de tema. Contexto, instruções e
possivelmente modelo diferiram: isso foi desenvolvimento, não avaliação independente.
A v3 consolidou 229 publicações, 126 revisões e 4 exclusões.

Israel identificou que diversidade de assuntos nas alternativas não basta para
negar um núcleo. O prompt já pedia lê-las; houve também aplicação insuficiente do
critério pelo assistente, sem investigar adequadamente a resolução. Reexaminei
os 359 itens, incluindo publicados e excluídos, pelo conhecimento necessário à
resposta. O protocolo e cada parecer estão em `auditoria_v4`.

Foram 103 revisões liberadas, 3 publicações retidas e 1 revisão excluída. Mudaram
79 centrais e 64 conjuntos de extras; refinamento no mesmo ramo não é erro anterior
comprovado. Maior cobertura também não demonstra maior precisão.

Após a Q0097, Israel pediu aplicar o critério às 57 revisões restantes. A releitura
liberou mais 32 e manteve 25 por pendências específicas. A escolha entre homônimos
passou a ser premissa explícita, sem equivalência automática; conteúdos complementares
podem ser central e extra. O registro de todas as 57 decisões preserva o estágio anterior.

## 2. Critérios e evidência

Leio texto completo, comando e alternativas; separo cenário de cobrança e formulo
a resolução ou uma pendência explícita. A resposta correta orienta o núcleo, mas
não substitui o conjunto nem escolhe sozinha o ID. Em assertivas independentes,
também importam os conhecimentos para rejeitar as falsas. Extras só representam
conteúdos efetivamente cobrados, sem colecionar palavras de distratores.

Comparo título, caminho e status. Um pai substantivo pode cobrir filhos realmente
exigidos; raiz e genérico sem escopo não escondem dúvida. Irmãos não são equivalentes.
Homônimos em ramos diferentes exigem análise própria. Publico enquadramentos
sustentados; reviso dúvidas concretas de ramo, conteúdo ou integridade; fora exige
ausência de tema ativo compatível. Dificuldade não é inferida da diversidade temática.

Houve busca inicial para cada ID; isso não confirma respostas. A evidência registra
**2 gabaritos definitivos**, **1 preliminar**, **326 respostas assistidas sem gabarito
oficial confirmado** e **30 respostas não confirmadas**. Tema pode ser inequívoco
sem letra confirmada; dúvida que muda o enquadramento permanece em revisão.
Fontes legais foram consultadas pontualmente; os fundamentos indicados não são
apresentados como todos verificados. O mesmo assistente não é avaliador independente.

Na Q0171, prova FGV/DPE-RJ 2021, tipo 2, questão 40, e preliminar oficial sustentam
B: hediondez. Passou de revisar para publicar no 4693; definitivo não acessível.
Na Q0322, arts. 12/39 da Lei 13.869 e 61/82 da Lei 9.099 sustentam apelação em dez
dias no Jecrim, corrigindo o RESE assumido anteriormente. A letra é resolução
assistida, não gabarito oficial confirmado. Q0097 e Q0355 têm E no definitivo FGV/TJSE.
Após discussão com Israel, Q0097 foi liberada no 4705, com 5067 extra: a homonímia
isolada não obriga revisão. Q0355 mantém pendência concreta sobre Tráfico/uso.

## 3. Diagnóstico e previsão

São 377 temas, 375 ativos. Preservam-se originais, HTML normalizado sem reescrever
conteúdo, negações e alternativas, com hashes e validação da árvore. Há 94 comandos
vazios, oito grupos de títulos repetidos, vinte descrições ausentes e 335 descrições
de importação que pouco delimitam escopo. Não copio metadados de origem como verdade.

Problemas concretos: Q0219 sem cenário; Q0319 com lista desconectada das opções;
Q0023/Q0331 com possíveis múltiplas incorreções; Q0359 com regra do Estatuto da
Pessoa Idosa afetada pela Lei 15.163/2025. Esses casos precisam de contexto/fonte,
sem atualização silenciosa. As exclusões são cartel sem tema ativo, prescrição de
PAD, ITCD, crimes esportivos e consumo da Lei 8.137: não equiparei este último ao
nó explicitamente limitado a crimes previstos no CDC.

A previsão permanece **96%**, cenário subjetivo **85%–99%**. É julgamento qualitativo
após o reexame, não reestimação estatística. Considera filtro de núcleo/caminho e
abstenção nas pendências, mas não tem referência quantitativa independente. A faixa
admite descumprir a meta e não é intervalo de confiança. Confianças não calibradas,
concordância do assistente, buscas e testes não medem precisão.

Para medir, pediria rótulos a professor em amostra aleatória das publicadas, sem
mostrar sugestões, e separadamente nos casos difíceis. Uma amostra usada para
ajustar a política não vira teste independente. Registrar adjudicação, erros por
ramo e calibração em avaliação posterior. Código reproduz formato e proveniência,
não assegura verdade jurídica nem generalização a novos dados.

## 4. Produção — 50 mil questões semanais

Importação teria fila, validação, hash/deduplicação, contexto preservado e taxonomia
versionada. Embeddings recuperariam candidatos e exemplos; não decidiriam
 equivalência. Com rótulos revisados suficientes, compararia classificador menor e
LLM em conjunto temporal separado. O LLM receberia questão, candidatos e escopos.
Um orquestrador determinístico encaminharia conflitos e conteúdo incompleto ao
professor. Agentes de pesquisa só entrariam com ganho demonstrado em avaliação.
Não treinaria usando respostas do próprio modelo como verdade.

Cenário ilustrativo salvo em `docs/CUSTOS_PRODUCAO.json`, preços consultados em
15/10/2026: 3.000 tokens de entrada/300 de saída no GPT-5.4 mini: US$0,0036/item;
segunda passagem em 10%, GPT-5.4, 5.000/600: mais US$0,00215/item do fluxo. Total
**US$0,00575/item ou US$287,50/semana**, sem busca, embeddings, infraestrutura,
repetições e professores. São hipóteses de produção, não modelos ou consumo
identificados deste chat. API de classificação executada: **US$0**; assinatura não
rateada; tokens e tempo total não medidos. Horário de importação não é latência.

Se a taxa de revisão deste recorte se repetisse, seriam aproximadamente 3.482
itens/semana: a um minuto por item, 58,0 horas humanas. É cenário, não previsão
validada. Mediria precisão amostral por ramo, cobertura, tempo de revisão, exclusões
incorretas, drift e reportes de alunos. Erros confirmados realimentariam catálogo e
avaliação versionada; manteria auditoria das publicadas e rollback de política.

## 5. Memo ao professor — uma página

A questão pode mencionar uma lei apenas como cenário. Precisamos identificar o
conhecimento que permite resolvê-la. Nas questões de assertivas, mais de um assunto
pode ser necessário, inclusive para rejeitar proposições falsas. Os extras devem
representar esses conhecimentos, sem associar o aluno a todo assunto mencionado.

A proposta contém 329 publicações, 25 revisões com pendências específicas e 5 casos
sem tema ativo compatível. A consulta a gabarito ajuda, mas não certifica o ID da
plataforma. Precisamos confirmar ramos homônimos, limites dos módulos Tráfico/uso
e procedimento especial e a abrangência de títulos vinculados a um diploma.

Recomendo exemplos de inclusão/exclusão por tema, definição das “Partes” e revisão
do posicionamento de Defesa Preliminar. Não proponho fundir homônimos sem examinar
sua função pedagógica. Itens com cenário ausente, possível concatenação ou regra
historicamente superada devem ser corrigidos/versionados, preservando sua origem.

Peço conferência das pendências e uma amostra aleatória independente das publicadas.
Isso permitirá estimar precisão, detectar erros correlacionados e ajustar a política.
A intervenção de Israel melhorou o critério de auditoria; não equivale a revisão
jurídica especializada das 359 questões nem comprova 95% ou 100% de acerto.

Fontes: anexos e orientação de Carla; URLs específicas em
`auditoria_v4/fontes/gabaritos_confirmados.json`, `conferencias_dirigidas.json` e
`normas_consultadas.json`; registro de preços em `docs/CUSTOS_PRODUCAO.json`.
As fontes sustentam fundamentos pontuais, não os rótulos internos dos especialistas.
