# Resultado da leitura contextual V15

As alterações solicitadas foram implementadas e testadas. Corrigiram a política de leitura, mas **não resolveram todos os erros de interpretação temática**. O código usa regras textuais e modelos clássicos; preservar um contexto útil não significa que a representação consiga compreendê-lo como um especialista.

## Regras adicionadas

1. Lei e artigo são lidos com o conteúdo a que se referem. O comando não é reduzido a uma string de norma. Um cabeçalho normativo também permanece ligado às proposições seguintes.
2. Questões com I/II/III conservam a introdução informativa e todos os itens. Uma instrução genérica pode ser omitida. Não há limiar de caracteres que reprove questões curtas.
3. Cabeçalhos curtos, mas temáticos, recebem prioridade de recuperação — por exemplo, “À luz das teorias das penas”, na Q0124. Essa expressão delimita o campo, sem resolver sozinha o ID do catálogo.
4. Comandos com “explique” e referências a procedimentos, situações ou disposições descritas retomam o enunciado. A ausência de identificador no comando não bloqueia a classificação se houver conteúdo em outro campo.
5. Alternativas C/E, numéricas e combinações de itens não fornecem temas. Alternativas com conteúdo continuam disponíveis como apoio. Não há gabarito gerado por IA nem descarte automático de toda a narrativa.
6. Todos os itens são mantidos. Primeiro item e maioria deixam de ser regras definitivas. Homônimos continuam separados por ramo; a proteção contra escopo empatado permanece.

O protocolo detalhado, os pesos de recuperação e seus limites estão em `roteamento_v15/PROTOCOLO_LEITURA.md`. Identificadores são heurísticas; a confiança continua sendo calculada pelo modelo calibrado, sem bônus fixo.

## Como foi comparado

Foram mantidos os mesmos cinco folds externos e quatro internos, agrupando duplicatas. O modelo de cada fold, sua calibração e sua política usam apenas seus dados de ajuste. O método final é ajustado nos 100 e só depois gera as sugestões nas 559 sem rótulo.

Os **100 rótulos já foram vistos e reutilizados repetidamente**, inclusive para formular hipóteses. Portanto, esta é uma comparação de desenvolvimento exposta, com risco de otimismo por seleção de variantes. Não é teste externo cego. As 559, incluindo os 300 itens recentes, não têm precisão medida.

Comparamos leitura integral, foco contextual e fusão com o ranking V8, cada uma com corte calibrado ou corte de 70%, usando o modelo novo sozinho ou preservando as publicações V11. A preservação é feita sem consultar o acerto individual; também mantém erros do controle.

## Resultados completos nas 100 reutilizadas e simulação nas 559

As colunas “certas/publicadas” e “precisão” dizem respeito **apenas às 100**. A última coluna é volume de publicações sugeridas nas **559**, sem medição de acerto.

| Variante | Corte | Política | Certas/publicadas nas 100 | Precisão nas publicadas | Publicadas nas 559 |
|---|---|---|---:|---:|---:|
| Contexto sem prioridade | Calibrado | Só novo | 9/11 | 81,82% | 59 |
| Contexto sem prioridade | Calibrado | Preservar V11 | 42/44 | 95,45% | 362 |
| Contexto sem prioridade | 70% | Só novo | 26/30 | 86,67% | 195 |
| Contexto sem prioridade | 70% | Preservar V11 | 46/49 | 93,88% | 388 |
| Foco contextual | Calibrado | Só novo | 13/16 | 81,25% | 59 |
| Foco contextual | Calibrado | Preservar V11 | 44/47 | 93,62% | 363 |
| Foco contextual | 70% | Só novo | 28/31 | 90,32% | 203 |
| **Foco contextual** | **70%** | **Preservar V11** | **47/49** | **95,92%** | **392** |
| Fusão contextual | Calibrado | Só novo | 23/24 | 95,83% | 216 |
| Fusão contextual | Calibrado | Preservar V11 | 44/46 | 95,65% | 387 |
| Fusão contextual | 70% | Só novo | 51/55 | 92,73% | 269 |
| Fusão contextual | 70% | Preservar V11 | 57/61 | 93,44% | 401 |

O controle V11 publicava 40/100, com 39 corretas (97,50%), e 361/559 (64,58%). O foco contextual a 70%, preservando V11, publica 49/100, com 47 corretas (95,92%), e 392/559 (70,13%). São **nove adições nas 100: oito corretas e uma errada**. A antiga publicação errada Q0252 permanece, pois preservar não é selecionar com o gabarito.

No alvo sem rótulo, são **31 publicações adicionais**, 167 revisões e nenhuma exclusão automática. Entre os 300 recentes, 218 seriam publicados (72,67%) e 82 revisados. Essas frações são decisões observadas, não precisão prevista. Não se deve transferir os 95,92% das 100 diretamente para as 559 ou para uma semana futura.

Na V14, a fusão com corte 70% e preservação tinha 60/66 publicações corretas nas 100 (90,91%), embora publicasse 413/559. A nova leitura não deve ser vendida como ganho em todas as métricas: ela pode liberar menos e errar menos no subconjunto selecionado. O primeiro candidato da nova fusão acerta 72/100, contra 74/100 na fusão V14. Já o foco contextual sozinho acerta 61/100 no primeiro candidato; a preservação é relevante para seu desempenho final.

## Controle que mantém o mesmo recuperador

Na ablação de leitura, mantendo o recuperador V8, o original acerta 70/100 e os campos contextuais V15 acertam 71/100: Q0319 é corrigida, sem acerto perdido nessa comparação. Ao remover os cabeçalhos informativos, volta a 70/100. Remover antecedentes dos comandos deixa 71/100 nesse controle; portanto, **este conjunto não demonstra ganho global dessa regra específica**, embora seja uma salvaguarda de leitura e evite a exclusão indevida do conteúdo na Q0028.

Essa ablação não mede publicação ou confiança. Seus resultados não devem ser confundidos com os dos modelos recalibrados da tabela.

## Exemplos que impedem uma conclusão exagerada

- **Q0052:** a situação de trabalho e estudo na prisão e os quatro itens estão preservados. A fusão sugere corretamente 4703, mas mantém revisão por homônimo não resolvido. O foco sozinho ainda sugere 5134 incorretamente. Preservar contexto não corrigiu sua recuperação em todas as variantes.
- **Q0124:** o cabeçalho curto sobre teorias das penas recebe prioridade e os cinco itens permanecem. A fusão acerta 4384; o foco sozinho sugere 5199, de outro ramo, e revisa. A publicação correta na política preservada vem do controle V11, não pode ser atribuída como nova conquista da V15.
- **Q0028:** “explique o procedimento” retoma o enunciado e seus artigos. A leitura foi corrigida, mas as variantes novas ainda não escolhem um ramo aceito. Continua revisão; é um erro de recuperação a estudar, não falta de texto na entrada.
- **Q0275:** a Lei 9.099/1995 não apaga o caso sobre citação. A fusão a 70% sugere e publica corretamente 4701; o foco também sugere 4701, mas permanece abaixo do corte.
- **Q0215:** a nova política de foco preservado publica incorretamente 5572 (Sentença Penal). A referência é 5201 (Penas Privativas de Liberdade). É a nova publicação errada, não um problema omitido do relatório.
- **Q0252:** a publicação antiga 5157 é preservada, embora a referência oficial seja fora da taxonomia. Não se inventou uma justificativa jurídica de “fora” ausente nos anexos para corrigir esse caso por ID.

Os textos completos e as previsões estão em `CASOS_CONTEXTO_V15.md`.

## O que se recomenda agora

Manter essas correções de contexto como hipóteses versionadas. Para os próximos estudos, usar o foco a 70% com preservação como uma opção experimental promissora, comparada com a fusão calibrada. **Não promover automaticamente nenhuma como entrega definitiva ou como sistema com 95% comprovados.** Uma nova amostra rotulada, principalmente dos itens recentes e das novas publicações, é necessária para estimar a qualidade de generalização. Também é preciso esclarecer os escopos duplicados de LEP e as justificativas dos oito “fora” oficiais.

Os testes verificam contratos de leitura, integridade e reprodução sem rótulos ou rede. Eles não verificam conhecimento jurídico nem certificam a precisão das questões sem referência.
