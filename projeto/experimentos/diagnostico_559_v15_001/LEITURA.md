# Teste nas 559 questões fora da folha-verdade

As 100 referências foram excluídas desta execução e de todos os totais abaixo. O modelo usa o aprendizado e a calibração anteriores; não houve novo treino. As 559 foram classificadas por código clássico, com rede, rótulos, treinamento, recalibração e escolha de limiares bloqueados.

Foram executadas as 12 configurações V15 congeladas. Todas reproduziram exatamente as decisões, os temas e as confianças salvas na rodada 002. Os dados sem rótulo não foram usados para escolher a variante que publica mais.

**Resultado da configuração principal: foco contextual, corte 70%, preservando V11.**

| Recorte | Publicar | Revisar | Fora | Cobertura |
|---|---:|---:|---:|---:|
| Antigas fora da referência: 259 | 174 | 85 | 0 | 67,18% |
| Recentes: 300 | 218 | 82 | 0 | 72,67% |
| Total: 559 | 392 | 167 | 0 | 70,13% |

O controle V11 publicava 361/559 (64,58%). A versão principal acrescenta 31 publicações. Não sabemos quantas dessas adições estão corretas. **A precisão real das 559 e dos 300 recentes não foi medida.** Nenhuma questão é marcada automaticamente como fora: ausência de suporte não prova ausência de tema.

A média das confianças registradas nas publicadas é 88,59%. É uma média descritiva de decisões oriundas de diferentes vias e calibradores; não é precisão medida nem validação de uma probabilidade conjunta. Também não sustenta declarar 95% nas 559.

**Por que ficaram para revisão.** Motivos primários, sem dupla contagem:

| Motivo | Quantidade | Significado |
|---|---:|---|
| confianca_abaixo_de_70 | 150 | O tema foi sugerido, mas o calibrador retornou menos de 70%. Não significa que a questão esteja errada. |
| homonimo_com_escopo_nao_resolvido | 17 | O código não distinguiu suficientemente os ramos homônimos. |

Entre as revisadas, 15 são elegíveis e estão entre 65% e menos de 70%. Outras 2 têm confiança de pelo menos 70%, mas continuam bloqueadas. Aproximar-se do corte não prova que a sugestão está certa.

**O que a decomposição numérica mostrou.**

- Das 146 revisões sem comando útil na rota, 0 têm contribuição total negativa do bloco de atributos do comando.
- Das 37 revisões de Certo/Errado, 37 têm contribuição negativa do bloco de alternativas, embora esse tipo de opção não contenha tema.
- Das 155 revisões sem I/II/III, 155 têm contribuição total negativa do bloco de itens.
- Essas contribuições são calculadas após padronização, em logit, antes da calibração. Não são descontos fixos de pontos percentuais e não demonstram que remover o atributo melhoraria a precisão.
- O detector preserva contexto, mas a representação ainda usa aproximações lexicais. Ele não resolve o conteúdo jurídico nem identifica a alternativa correta.

| Atributo entre os cinco contrapesos mais negativos | Revisões em que aparece |
|---|---:|
| efetivo_palavra | 163 |
| efetivo_titulo | 154 |
| itens_escopo_max | 140 |
| alt_escopo_max | 100 |
| alt_palavra_media | 97 |
| alt_escopo_media | 54 |
| cmd_titulo | 51 |
| cmd_escopo | 17 |
| cmd_palavra | 16 |
| itens_escopo_top2 | 12 |

A contagem acima tem sobreposição e não atribui causalidade individual. Uma contribuição negativa isolada pode coexistir com publicação.

**O tamanho do efeito importa:** no modelo atual, retirar hipoteticamente todo o contrapeso das alternativas C/E mudaria a confiança em no máximo 0.440 ponto percentual; o bloco de itens ausentes, em no máximo 0.034. São limites matemáticos com calibrador fixo, não novas probabilidades validadas. Outros atributos do mesmo bloco podem compensar um contrapeso individual grande. Logo, a frequência dos sinais negativos não demonstra um grande bloqueio artificial: zerá-los não é a solução principal para a cobertura.

**Comparação das variantes, somente nas 559.**

| Variante / corte / política | Publicar | Revisar | Cobertura |
|---|---:|---:|---:|
| contexto_sem_prioridade/calibrado/substituir | 59 | 500 | 10,55% |
| contexto_sem_prioridade/calibrado/preservar_v11 | 362 | 197 | 64,76% |
| contexto_sem_prioridade/70/substituir | 195 | 364 | 34,88% |
| contexto_sem_prioridade/70/preservar_v11 | 388 | 171 | 69,41% |
| foco_contextual/calibrado/substituir | 59 | 500 | 10,55% |
| foco_contextual/calibrado/preservar_v11 | 363 | 196 | 64,94% |
| foco_contextual/70/substituir | 203 | 356 | 36,31% |
| foco_contextual/70/preservar_v11 | 392 | 167 | 70,13% |
| fusao_contextual/calibrado/substituir | 216 | 343 | 38,64% |
| fusao_contextual/calibrado/preservar_v11 | 387 | 172 | 69,23% |
| fusao_contextual/70/substituir | 269 | 290 | 48,12% |
| fusao_contextual/70/preservar_v11 | 401 | 158 | 71,74% |

Há 7 questões em revisão na configuração principal para as quais a fusão calibrada publica com o mesmo ID sugerido pelo foco e o foco está elegível. Estão em `candidatas_concordantes_NAO_LIBERADAS.csv`. **Não foram liberadas:** os métodos compartilham catálogo, atributos e histórico; sua concordância não é validação independente nem uma nova probabilidade calibrada.

A preservação mantém 120 publicações que recebem algum alerta do foco novo (outro ID sugerido ou inelegibilidade); em 115 delas os IDs sugeridos estão em ramos distintos. São divergências entre métodos, **não erros demonstrados**. Pais e filhos do mesmo ramo são tratados como compatíveis nessa descrição. O arquivo `preservadas_com_alerta.csv` permite investigar sem apagar acertos antigos automaticamente.

**Melhorias recomendadas a partir deste diagnóstico.**

1. Melhorar a recuperação do conhecimento cobrado: preparar descrições gerais e termos discriminativos dos temas, com foco em conceitos e escopos, preservando as referências ao caso. Comparar o resultado antes de mudar a política. A atual leitura contextual ainda termina em aproximações lexicais; nenhum gabarito inferido por LLM deve escolher ou validar o tema.
2. Esclarecer os escopos dos IDs homônimos. Sem essa informação, escolher o primeiro ID só encobre a dúvida.
3. Revisar a política de preservação com uma regra de conflito entre ramos e uma avaliação rotulada. A preservação indiscriminada retém erros antigos; vetar toda discordância também pode retirar acertos. Não alterar a regra com base apenas no volume das 559.
4. Usar a lista de concordância e as questões perto do corte como prioridade de uma pequena revisão especializada, registrando os rótulos novos. Não reduzir automaticamente o corte nem atribuir certeza à identificação de um título.
5. Testar atributos condicionais para “não se aplica” e recalibrar antes de adotar, sem esperar grande ganho apenas removendo os contrapesos pequenos encontrados aqui. Medir as mudanças em referências novas e representativas, incluindo as 300 recentes. O conjunto sem rótulo permite examinar comportamento e cobertura; não comprovar a meta de 95%.

**Arquivos e reprodução.**

- `classificacoes_559.csv`: cada decisão, tema, confiança e motivo, com comparação entre foco e fusão.
- `diagnostico_por_questao.jsonl`: as 559 questões completas, campos utilizados, cinco candidatos e decomposição numérica do foco.
- `CASOS_PARA_CONFERIR.md`: exemplos completos fora das 100, selecionados por motivos observados, sem validação de gabarito.
- `comparacao_variantes_559.csv`: as 12 configurações congeladas, sem os 100 IDs.
- `resumo.json` e `analise_complementar.json`: totais estruturados; precisão real permanece nula.

O CSV oficial do case continua exigindo uma linha para cada uma das 659 questões. A exclusão dos 100 vale para esta análise e para a avaliação, não para remover suas linhas da entrega oficial. Este pacote não substitui `publicacao.csv` nem promove uma configuração nova.

