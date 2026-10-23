# Como explicar o projeto auditado

## Problema e resultado

A plataforma precisa que a questão apareça no tópico que o aluno está estudando.
O protótipo cobre 359 IDs e propõe 329 publicar, 25 revisar e 5 fora. Cobertura é
91,6435%. A precisão não foi medida. 96% é previsão subjetiva, com sensibilidade
85%–99%; não é promessa, taxa calculada de acertos ou probabilidade calibrada.

## O que o código faz e o que dependeu do assistente

Python preserva/normaliza os dados, verifica temas e IDs, prepara prompts, valida
respostas e aplica intervenções registradas. A interpretação foi feita pelo
assistente, com participação crítica do candidato. O programa não chama API para
classificar dados novos. Sua execução reproduz as respostas e o pós-processamento
que foram salvos; isso é diferente de repetir a inferência ou demonstrar generalização.

## Caminho percorrido

1. Dados recebidos com HTML e metadados possivelmente errados: preservar originais.
2. Limpeza de apresentação e validação da árvore: não reescrever conteúdo jurídico.
3. Piloto de vinte em duas conversas/rodadas, para desenvolver critérios.
4. Classificação v3: 229/126/4, com respostas e decisões salvas.
5. Israel questionou a revisão por diversidade de alternativas e exigiu olhar a
   resolução. O prompt já mandava ler alternativas: a aplicação pelo assistente
   também foi insuficiente. Não atribuir toda falha à falta de detalhes do usuário.
6. Reexame assistido dos 359 IDs: texto completo, comando, alternativas, resolução
   ou pendência, tema central, extras, antes/depois, fontes e limites.
7. Consolidação v4 com 107 mudanças de decisão, 79 centrais e 64 conjuntos de extras.
   Mudança de pai para filho pode ser refinamento, e não erro anterior.
8. Testes e reprodução: validam software, integridade e formato; não acerto jurídico.

## Critérios que devo conseguir explicar

- Contexto narrativo não define o tema: perguntar que conhecimento resolve o item.
- Gabarito pode revelar núcleo em pergunta genérica; ainda é preciso justificá-lo.
- Assertivas devem ser julgadas individualmente, inclusive as falsas.
- Extras são conhecimentos adicionais cobrados. Filhos do central podem ser extras justificados para consulta por subtema; não repetir IDs nem transformar contexto em rótulo.
- Caminho do catálogo importa; não presumir equivalência de títulos em ramos distintos.
- Um pai substantivo pode representar conjunto de filhos; não usar raiz como lixeira.
- Revisar exige dúvida concreta; fora exige ausência de tema ativo compatível.
- Dificuldade não se deduz da diversidade das alternativas.

## Exemplos para abrir durante a apresentação

- Q0171: revisar → publicar, Hediondos. Resposta B sustentada por preliminar oficial;
  o definitivo não foi acessado. Não publicar só porque há uma letra.
- Q0187: Efeitos da Condenação → Penas Privativas. A resposta cobra progressão e
  reparação do dano, e não os efeitos mencionados nos distratores.
- Q0322: RESE → Recursos no Jecrim. Pena máxima de dois anos; rejeição da denúncia
  tem apelação em dez dias. Resolução assistida fundamentada em lei, sem gabarito
  oficial confirmado.
- Q0333: Introdução ao Direito Penal → Escolas Criminológicas. A alternativa
  correta é sobre método positivista; não usar a disciplina dos demais distratores.
- Q0020: cinco assuntos independentes. Mantida revisão, com extras explícitos;
  acertar a combinação não cria um tema central único.
- Q0052: quatro assertivas sobre remição, inclusive duas falsas. Um único tema de
  execução representa o conjunto; não multiplicar extras só por haver quatro itens.
- Q0346: preventiva, Júri e consumo são contextos de poderes do assistente. O núcleo
  comum é Sujeitos do Processo; não adicionar automaticamente esses três assuntos.
- Q0097: E confirmado; após discussão com Israel, publicar no 4705, com 5067 extra.
  Homonímia isolada não impede decisão fundamentada; ver REVISAO_Q0097.md.
- Q0355: E confirmado, mantendo revisão por dúvida concreta sobre alcance Tráfico/uso.
  A letra da prova e o rótulo temático são problemas diferentes.
- Q0359: alteração de 2025 exige sinalizar contexto histórico, sem apagar o original.

A revisão posterior das 57 retidas liberou outras32 por escolha fundamentada de ramo/núcleo, mantendo25 por conteúdo, contexto ou escopo sem correspondência segura. Exemplos: Q0071→4688; Q0337→4684+5470; Q0159→5226+5150+5160. Q0197 mudou de5482 para5499, pois cobra atribuição investigatória. As57 justificativas estão em REAVALIACAO_57_REVISOES.md. Não afirmar que escolher um rótulo entre dois prova acerto.

## O que sabemos e o que falta medir

Foram buscados todos os IDs. Há dois gabaritos definitivos e um preliminar
confirmados; 326 respostas são assistidas sem confirmação oficial e 30 permanecem
não confirmadas. Não dizer que 359 gabaritos foram encontrados ou validados.
Fontes indicadas no parecer e fontes efetivamente conferidas têm registros separados.

A política está mais explícita e corrige falhas identificáveis. Não podemos medir
quanto a precisão melhorou sem rótulos independentes. Um professor deve avaliar
amostra aleatória das publicadas, sem sugestão prévia, além das pendências.
A aprovação dos testes e a consistência do mesmo assistente não substituem isso.

## Produção e custo

O desenho prevê importação, recuperação de candidatos com embeddings, comparação
com classificador treinado quando houver rótulos, LLM em ambiguidades e revisão
humana. Agentes só se houver benefício avaliado. O custo de API no protótipo foi
US$0, com assinatura existente, sem tokens medidos. A simulação de produção é
separada e parametrizada; não apresentar estimativa de tokens como consumo real.

## Demonstração com o visor de auditoria

Abra `visor/index.html` no navegador. O arquivo é gerado com `python gerar_visor.py`,
usando a entrega salva, e permite ler cada questão, comparar a v3 com a entrega atual
e consultar justificativas e evidências. Veja `visor/LEIA-ME.md`.

Roteiro de aproximadamente quatro minutos:

1. Apresentar o problema e distinguir cobertura de precisão. Mostrar 329/25/5,
   cobertura de 91,6435% e a precisão temática ainda não medida.
2. Abrir Q0171 pela lateral: explicar a intervenção sobre o conhecimento da
   resolução e a confirmação apenas preliminar da resposta B.
3. Abrir Q0097 e Antes e depois: justificar 4705 como central e 5067 como
   extra, sem declarar equivalência entre ramos homônimos.
4. Abrir Q0355 e Evidências: demonstrar que E definitivo não elimina a dúvida
   sobre o escopo Tráfico/uso pessoal.
5. Filtrar as 25 revisões e mostrar o parecer e a exportação do recorte.
   Encerrar explicando o que falta medir e o desenho para produção.

## Situação da entrega

O candidato publicou o repositório em
https://github.com/israel-dias/case-vicio-ia, conforme o push confirmado em
17/10/2026. A atualização com o visor deve ser enviada ao mesmo repositório.
O envio do link à recrutadora é uma etapa separada e ainda não foi confirmado.
O tempo total não foi instrumentado; uma estimativa de horas só deve ser
acrescentada pelo candidato, identificada como aproximada.
