# Experimento de melhoria v3 — classificação de tópicos

## Sistema e hipóteses

A v2 recuperava temas por correspondência textual e escopos e mantinha o primeiro candidato. Um modelo clássico estimava sua compatibilidade; um calibrador e um corte decidiam entre publicar e revisar. O experimento investigou dois gargalos: pouco uso das referências legais e dificuldade de aproveitar candidatos próximos. Não houve resolução de questões por LLM, alteração de rótulos oficiais ou decisões por ID.

A preparação acrescentou um mapa versionado de 11 normas/códigos e 50 intervalos documentais propostos. A extração separa CP, CPP e códigos militares, associa artigos à norma indicada e conserva a ambiguidade quando falta contexto. Os escopos receberam atributos de palavras, caracteres e flexões por campo. As informações normativas não são vetos nem rótulos. As fontes do Planalto e as premissas constam no JSON preparado; não houve validação jurídica independente de cada associação. A legislação consultada não substitui o contexto histórico da prova.

Foram testadas três variantes: novos atributos com tema fixo; regressão logística treinada com positivos oficiais e candidatos negativos próximos; e um ranking híbrido de busca e compatibilidade. Todos usam C=1, solver liblinear e artefatos congelados. Uma citação em alternativa pode ser contexto ou conteúdo secundário; não determina automaticamente o assunto. Fora automático e extras automáticos permaneceram desativados.

## Uso dos 100 rótulos

A avaliação reutilizou as mesmas cinco divisões externas da v2. Dentro de cada treino externo, quatro divisões internas produziram sinais fora do próprio treino, para calibrar e escolher o corte. Os parâmetros e a política foram salvos antes das previsões externas. O corte exige pelo menos dez publicações internas e 95% de acerto empírico. As 559 questões sem rótulos não participaram do ajuste ou da escolha de pesos e limiares. Os 100 rótulos já eram conhecidos: a CV computacional não constitui novo teste externo cego.

| Método | Top1/100 | Publicadas | Corretas | Precisão |
|---|---:|---:|---:|---:|
| Controle v2 | 66 | 20 | 20 | 100% |
| Referências, tema fixo | 66 | 23 | 22 | 95,65% |
| Candidatos próximos | 70 | 0 | 0 | Indefinida |
| Ranking híbrido | 71 | 11 | 9 | 81,82% |
| Seleção interna por fold | 67 | 26 | 25 | 96,15% |

A união das buscas continha uma referência aceita em 88/100 itens, ante 85/100 no top5 legado. O treino de candidatos próximos melhorou top1, mas não sustentou publicações sob a regra interna. O híbrido introduziu dois erros entre 11 publicações externas. Isso justifica não promovê-los apenas por acertarem mais temas no total.

O ajuste final escolheu referências com tema fixo: nos 100 sinais OOF, seu corte selecionou 31 acertos em 32 itens. Esse é desenvolvimento usado no ajuste, distinto de 22/23 na CV por fold. O Brier dessa variante caiu de 0,1831 no controle para 0,1676. Menor Brier indica melhor qualidade média das probabilidades nesse conjunto conhecido, sem garantia na distribuição nova.

## Resultado da candidata e diagnóstico

Nas 559 questões avaliadas pela empresa, foram 175 publicações e 384 revisões: cobertura de 31,3059%, ante 27,1914% na v2. Houve 68 liberações e 45 bloqueios, ganho líquido de 23. Essas transições não comprovam correções ou erros individuais. Nas 300 recentes, foram 97 publicações (32,3333%), ante 89 na v2. No total de 659, foram 205 publicações e 454 revisões.

A previsão é a média das probabilidades congeladas nas publicadas: 92,8992%, ante 90,3404%. A faixa 78,05%–100% é sensibilidade descritiva baseada em CV, não intervalo de confiança válido para as 559. A cobertura desta população é conhecida exatamente. A precisão real e a meta de 95% não estão comprovadas; a previsão segue abaixo da meta.

A versão escolhida mantém os temas da busca, portanto não resolveu seu principal limite de ordenação. Poucos exemplos por tema, escopos pouco definidos, homônimos em ramos distintos, metadados de origem imprecisos e apenas oito exemplos fora continuam limitando a generalização. Os alertas computados ajudam a inspecionar o mecanismo, sem identificar automaticamente um defeito jurídico. Os casos completos em `analises/melhorias_v3` pertencem às 559 e foram selecionados por mudança de confiança, sem avaliação jurídica do assistente.

## Produção e custo

A classificação congelada de 659 itens levou aproximadamente 15,13 segundos neste ambiente, incluindo preparação. A extrapolação linear para 50 mil resulta em cerca de 19 minutos, sem benchmark real nesse volume e sem estimativa do tempo de treino. Custo de API da classificação: US$ 0; CPU, energia, manutenção e revisão humana não foram precificados. Tokens internos e tempo humano não foram medidos.

Para produção: validar importações e duplicatas; preparar referências e vocabulário versionados; aplicar o modelo congelado; auditar amostras das publicadas e medir erros por ramo e origem; incorporar correções dos professores como treino em uma versão seguinte. Retreinar em ciclos semanais inicialmente, condicionado a rótulos novos e regressões medidas. Promover versões apenas após avaliação em dados novos. A fila atual ainda é grande e exige melhoria antes de operação de escala; não há evidência de viabilidade do esforço humano nesse volume.

## Memo para o professor

Encontramos temas com títulos iguais em ramos diferentes, descrições insuficientes e conteúdos de questões que se confundem com palavras de alternativas. A nova preparação organizou referências legais e melhorou a estimativa do classificador, mas a precisão das questões novas continua desconhecida.

Precisamos de definições curtas dos limites dos temas, especialmente homônimos, e de novas classificações das questões recentes para uma avaliação independente. O professor deve indicar tema central, extras legítimos ou ausência de tema; as correções ficam registradas como exemplos para reduzir o trabalho nas próximas importações.

A fila traz sugestão, candidatos e sinais computados para orientar a consulta. Baixa confiança descreve a incerteza do sistema e não demonstra dificuldade ou defeito jurídico da questão. A prioridade é retirar dessa fila os casos que o modelo puder aprender a classificar com qualidade comprovada em novas amostras.
