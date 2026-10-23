# Ablação v11: quais atributos de confiança vale retirar?

## Resultado principal

Retirar atributos porque frequentemente têm contribuição negativa não é uma estratégia suficiente. A retirada isolada de palavra_completo, o negativo mais frequente, perde cinco publicações corretas na avaliação por folds. Algumas remoções são úteis como complemento à V9, preservando publicações anteriores.

A variante sem_apoio_duplo com política preservar é uma candidata de estudo: passa de 36 publicadas/35 corretas para 40 publicadas/39 corretas nas 100. Acrescenta quatro sugestões corretas, sem novos erros observados nessa amostra. Nas 559 sem rótulo, simula 361 publicações, contra 352 do controle. Não prova precisão de 95% nas novas.

As quatro novas publicações são poucas para validar generalização. A variante foi destacada após comparar nove configurações no mesmo desenvolvimento reutilizado; não é uma escolha confirmada em teste externo independente. As 100 questões e seus rótulos já haviam sido expostos. A precisão real nas 559 é desconhecida. Nenhuma entrega foi substituída.

## O que foi preservado

- Mesmo catálogo, ranking de temas da v8 e identificadores não genéricos da v9.
- Nenhum limite de caracteres na nova decisão. As hipóteses de tamanho rejeitadas na V10 não foram incorporadas.
- Frases envolvendo títulos genéricos Conduta/Resultado propõem candidatos, mas não autorizam publicação direta; passam pela comparação contextual/modelo.
- Mesmos cinco folds externos e quatro internos. Não se utilizam os rótulos externos no treino/calibração/corte daquele fold.
- Nenhuma confiança somada à mão, nenhum coeficiente negativo truncado e nenhuma exceção por ID.
- Sem busca de gabaritos ou LLM para escolher/validar os temas. As decisões de inferência usam lógica e modelos clássicos congelados.

## O que contribuição negativa significa

Ela é parte da conta do modelo, relativa à média dos dados de treino; não é uma regra jurídica nem um veto. Um atributo pode contribuir negativamente em uma questão correta e ser compensado por outras evidências. Não se converte essa parcela em pontos percentuais de confiança.

No controle, excluindo os 25 casos resolvidos por identificador, há 36 revisadas com sugestão correta, 28 revisadas com sugestão incorreta e 11 publicadas corretas pelo modelo. O atributo palavra_completo aparece entre as três contribuições negativas mais fortes em 32/36, 25/28 e 10/11 desses grupos, respectivamente. Portanto sua presença negativa é frequente também em publicações corretas.

char_enunciado mede semelhança por trechos de caracteres, não tamanho ou limite de caracteres. sem_atributos_origem retira três colunas do comparador; não remove necessariamente os metadados da recuperação legada. sem_atributos_foco retira cinco colunas do comparador; o foco continua presente no ranking preservado.

## Remoções e novo ajuste

Foram registradas antes de executar v11: controle; retirada de palavra_completo; escopo_alternativas; char_enunciado; apoio duplo; três atributos de origem; três frequentes; seis frequentes; cinco atributos de foco. O diagnóstico v8 motivou os grupos frequentes. A lista exata está em experimento_atributos_v11/modelo.py e no protocolo.

Cada remoção foi seguida por novo ajuste dos parâmetros e por nova calibração/corte. Os atributos restantes podem mudar de peso. Isso evita o erro de apagar uma parcela negativa e manter uma confiança artificialmente elevada. A meta interna permaneceu 95% empírica com mínimo de dez selecionadas.

## Duas políticas avaliadas

1. Substituir: usa somente o novo comparador e os identificadores preservados. Pode ganhar ou perder publicações do controle.
2. Preservar: se o controle já publica, mantém tema, decisão e confiança. Se o controle revisa, considera a nova versão. A política não consulta acerto oficial para escolher em inferência. Essa combinação também precisa ser avaliada como um sistema completo.

Preservar publicações não equivale a preservar apenas acertos: mantém também o erro conhecido Q0252 do atalho v9, já contado na avaliação. Não foi criada uma exceção por esse ID.

## Resultados da política preservar nas 100

| Remoção | Publicadas | Corretas | Precisão publicada | Novas corretas | Novas erradas |
|---|---:|---:|---:|---:|---:|
| Controle V9 (41 atributos) | 36 | 35 | 97.22% | 0 | 0 |
| Sem similaridade por palavras do texto completo | 36 | 35 | 97.22% | 0 | 0 |
| Sem similaridade conjunta dos escopos nas alternativas | 38 | 37 | 97.37% | 2 | 0 |
| Sem similaridade por caracteres no enunciado | 36 | 35 | 97.22% | 0 | 0 |
| Sem duas medidas de apoio simultâneo | 40 | 39 | 97.50% | 4 | 0 |
| Sem três atributos de origem | 40 | 39 | 97.50% | 4 | 0 |
| Sem três negativos frequentes do diagnóstico anterior | 39 | 38 | 97.44% | 3 | 0 |
| Sem seis negativos frequentes do diagnóstico anterior | 39 | 38 | 97.44% | 3 | 0 |
| Sem cinco atributos de foco no comparador | 39 | 38 | 97.44% | 3 | 0 |

O tema top1 das sugestões permanece igual em todas as variantes: 71/100 aceitas depois do atalho. O teste mede a decisão de publicar/revisar e a confiança; não demonstra melhora na descoberta de temas.

## Retirada isolada e perdas

| Remoção | Publicadas usando só a nova versão | Publicações anteriores perdidas | Publicadas preservando controle |
|---|---:|---:|---:|
| Controle V9 (41 atributos) | 36 | 0 | 36 |
| Sem similaridade por palavras do texto completo | 31 | 5 | 36 |
| Sem similaridade conjunta dos escopos nas alternativas | 38 | 0 | 38 |
| Sem similaridade por caracteres no enunciado | 35 | 1 | 36 |
| Sem duas medidas de apoio simultâneo | 37 | 3 | 40 |
| Sem três atributos de origem | 36 | 4 | 40 |
| Sem três negativos frequentes do diagnóstico anterior | 35 | 4 | 39 |
| Sem seis negativos frequentes do diagnóstico anterior | 33 | 6 | 39 |
| Sem cinco atributos de foco no comparador | 39 | 0 | 39 |

Na versão sem apoio duplo, substituir isoladamente daria 37 publicações e perderia três publicações antigas; a união preserva essas três e chega a 40. Isso atende à ideia de acrescentar uma possibilidade de aprovação sem desfazer as publicações anteriores.

## Simulação nas 559 sem rótulo, preservando controle

| Remoção | Publicar | Revisar | Cobertura | Publicações novas |
|---|---:|---:|---:|---:|
| Controle V9 (41 atributos) | 352 | 207 | 62.97% | 0 |
| Sem similaridade por palavras do texto completo | 358 | 201 | 64.04% | 6 |
| Sem similaridade conjunta dos escopos nas alternativas | 352 | 207 | 62.97% | 0 |
| Sem similaridade por caracteres no enunciado | 356 | 203 | 63.69% | 4 |
| Sem duas medidas de apoio simultâneo | 361 | 198 | 64.58% | 9 |
| Sem três atributos de origem | 357 | 202 | 63.86% | 5 |
| Sem três negativos frequentes do diagnóstico anterior | 362 | 197 | 64.76% | 10 |
| Sem seis negativos frequentes do diagnóstico anterior | 382 | 177 | 68.34% | 30 |
| Sem cinco atributos de foco no comparador | 359 | 200 | 64.22% | 7 |

A variante sem seis frequentes publica mais nas 559, mas isso não demonstra maior qualidade. Não foi escolhida automaticamente pelo volume sem rótulo. A candidata sem apoio duplo muda apenas duas colunas, tem quatro novas corretas na amostra e preserva as publicações da V9. Ainda precisa de validação independente.

## Quatro exemplos liberados pela candidata

| ID | Tema sugerido e aceito pela folha | Confiança anterior OOF | Nova confiança OOF |
|---|---|---:|---:|
| Q0277 | Estatuto do Idoso — Crimes | 79,57% | 83,86% |
| Q0066 | Etapas Evolutivas e Escolas Criminológicas | 84,66% | 85,96% |
| Q0150 | Tráfico de Drogas | 96,05% | 95,41% |
| Q0345 | Crimes Contra a Dignidade Sexual, pai do tema oficial | 89,66% | 87,46% |

As duas últimas confianças diminuíram, mas passaram a publicar porque a nova calibração/corte tornou ativa a política do fold 3, antes desativada. Não é uma soma de pontos de confiança. Na Q0277, o novo corte do fold 1 é 80,67%, e a confiança 83,86% o supera. No fold 3, o corte é 82,32%.

As sugestões erradas da Q0058, Q0061 e Q0320 permanecem em revisão na candidata. Elas não foram liberadas apenas para aumentar cobertura.

## O que foi retirado em sem_apoio_duplo

O novo comparador passa de 41 para 39 atributos, retirando:

- apoio_enunciado_e_alternativas;
- evidencia_escopo_enunciado_alt.

São medidas que combinam apoio de enunciado e alternativas. Os demais atributos de enunciado, alternativas, escopos, foco e referências continuam disponíveis. Não significa ignorar alternativas. Na política preservar, o comparador original completo também continua funcionando como primeiro caminho; os dois sinais não impedem que o comparador complementar aprove uma revisão.

Essa ablação é compatível com a hipótese de que algumas evidências precisam estar concentradas no enunciado ou nas alternativas, sem exigir apoio simultâneo forte. A comparação não prova uma causa jurídica nem que esses dois atributos sejam universalmente ruins.

## Limites da confiança e da avaliação

O Brier agregado na política preservar foi aproximadamente 0,15410 no controle e 0,15797 em sem_apoio_duplo (menor é melhor). Ou seja, houve ganho de cobertura observada nas 100, mas não melhora desse indicador agregado de probabilidades. Não devemos ocultar esse tradeoff.

A precisão publicada de 97,50% corresponde a 39/40 nas 100 reutilizadas; o acerto de todas as sugestões continua 71/100. São medidas com denominadores diferentes. A meta no conjunto sem rótulo não foi comprovada. Os modelos não produziram gabarito de alternativas.

## Como reproduzir

Python 3.12 e dependências já usadas em experimento_folha_v2/requirements.txt. Use saídas novas.

```bash
python3 -m unittest discover -s experimento_atributos_v11/tests -v
python3 testar_atributos_v11.py --saida experimentos/atributos_v11_local
python3 congelar_atributos_v11.py --experimento experimentos/atributos_v11_local
```

Inferência experimental com os modelos já incluídos:

```bash
python3 classificar_atributos_v11.py --variante sem_apoio_duplo --politica preservar --saida inferencia_v11_local
```

--questoes caminho/novas_questoes.jsonl aceita questões novas sem rótulos e sem tabela de respostas por ID. --experimento permite usar uma nova reprodução congelada. --politica substituir permite comparar o uso isolado. O classificador não consulta folha-verdade, não treina e não usa rede/LLM.

O comando de avaliação consulta a folha-verdade somente para treinamento/calibração/avaliação das 100 nos grupos apropriados. Os IDs são usados para particionar e registrar resultados, não como atributo ou exceção de inferência.

## Onde conferir

- experimentos/atributos_v11_001/protocolo_previo.json: hipóteses, grupos retirados e hashes.
- experimentos/atributos_v11_001/frequencia_negativos.csv: diagnóstico separado por acerto/erro.
- experimentos/atributos_v11_001/diagnostico_contribuicoes.json: contribuições algébricas por questão.
- experimentos/atributos_v11_001/avaliacao_100.csv: todas as variantes e políticas nos folds.
- experimentos/atributos_v11_001/mudancas_100.json: questões completas com antes/depois e referência.
- experimentos/atributos_v11_001/simulacao_559.csv: hipóteses nas questões sem rótulo.
- experimentos/atributos_v11_001/modelos_finais.json: parâmetros congelados, sem rótulos por ID.
- classificar_atributos_v11.py: inferência reproduzível.

Os arquivos publicacao.csv e previsao.txt da raiz continuam sendo controles históricos v5; NÃO são resultados v11. A entrega anterior, os modelos e os registros v9 foram preservados. Os resultados v11 são experimentais.
