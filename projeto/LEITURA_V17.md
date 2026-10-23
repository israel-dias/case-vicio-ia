# V17 — isolamento dos comparadores

**Resultado negativo: nenhuma das alterações superou o controle anterior.** O controle V16 continua como referência experimental: 394/559 publicadas, 70,48% de cobertura, precisão real desconhecida. Os CSVs de entrega na raiz são históricos e não foram substituídos por esta rodada.

## O que foi comparado

A busca e seus pesos foram congelados na fusão V15. Cada questão recebeu os mesmos cinco candidatos em todas as opções. O primeiro comparador mantém o primeiro candidato; os outros ordenam os cinco pelo escore aprendido. V11 aqui significa apenas seus 39 atributos, sem a aprovação direta por identificador nem a preservação de publicações antigas. V15 usa 27 atributos. Não houve uso de gabaritos de respostas ou seleção temática por LLM.

As opções usaram o mesmo estimador (regressão logística C=1), balanceamento, peso por texto, famílias de treino, guardas V15 e procedimento de calibração. Os pesos de busca não são probabilidades. A origem foi mantida como na representação histórica, inclusive nos atributos V11; sua neutralização não foi misturada a este teste. Ela não é um rótulo obrigatório nem um veto de disciplina.

## Resultado nas 100 referências de desenvolvimento

Os 100 rótulos já foram reutilizados e discutidos. Cinco folds externos com quatro internos impedem o acesso direto ao rótulo externo durante o ajuste, mas não restauram um teste cego. Há 92 questões com tema e oito fora. Todas as 100 entram nos denominadores de publicação; publicar uma referência fora conta como erro.

| Opção | Primeiro tema aceito /100 | Publicadas | Corretas | Precisão observada |
|---|---:|---:|---:|---:|
| Controle anterior V16 | 70 | 50 | 48 | 96.00% |
| Primeiro candidato V15 | 72 | 24 | 23 | 95.83% |
| Reordenar com atributos V11 | 69 | 3 | 2 | 66.67% |
| Reordenar com atributos V15 | 60 | 10 | 8 | 80.00% |
| Seleção interna | 72 | 24 | 23 | 95.83% |

A busca fixa contém um tema aceito em primeiro lugar em 72/92 referências com tema; entre os cinco primeiros, em 89/92. Encontrar o tema em uma lista não equivale a escolhê-lo corretamente nem mede a precisão entre publicadas.

## O que a reordenação mudou

| Comparador | Trocas de primeiro tema | Erros corrigidos | Acertos transformados em erros |
|---|---:|---:|---:|
| Reordenar com atributos V11 | 26 | 6 | 9 |
| Reordenar com atributos V15 | 30 | 3 | 15 |

O comparador V11 corrigiu seis questões e prejudicou nove; o V15 corrigiu três e prejudicou quinze. Portanto, a presença frequente do tema aceito no top5 não bastou para um bom reordenamento. Isso é uma observação medida. A hipótese de que seria melhor aprender comparações entre candidatos próximos, em vez de compatibilidade absoluta com todas as famílias, precisa de outro experimento isolado; não foi implementada nem validada nesta rodada.

## Aplicação congelada nas 559 fora da folha-verdade

| Opção | Publicar | Revisar | Cobertura | Publicadas nas 300 recentes |
|---|---:|---:|---:|---:|
| Controle anterior V16 | 394 | 165 | 70.48% | 218 |
| Primeiro candidato V15 | 216 | 343 | 38.64% | 122 |
| Reordenar com atributos V11 | 0 | 559 | 0.00% | 0 |
| Reordenar com atributos V15 | 0 | 559 | 0.00% | 0 |

A variante escolhida antes de classificar o alvo foi `primeiro_fusao_v15`. Seu modelo final usa corte aprendido de 0,759185694722967. As políticas finais dos dois reordenadores ficaram inativas: não encontraram um subconjunto com pelo menos dez observações e precisão empírica de 95% na calibração. Isso não significa que todas as 559 sugestões estejam erradas; significa falta de evidência para liberá-las por essa política. Os resultados OOF podem ter algumas publicações porque cada fold tem seu próprio ajuste e corte.

No modelo final escolhido, as 343 revisões se dividem em 274 abaixo do corte e 69 por homônimo não resolvido. Não se marcou fora automaticamente por baixa semelhança. A precisão das 559 e das 300 recentes permanece desconhecida.

## Por que não somar as publicações à versão anterior

A união manteria as publicações antigas e acrescentaria oito nas 559: 402/559, ou 71,91%. Contudo, nas referências ela acrescentou uma publicação errada (Q0202): 48 acertos em 51, ou 94,12%. A união é somente um diagnóstico; não foi ativada nem calibrada como uma nova política. Preservar publicações históricas não certifica que estejam corretas.

Na Q0202, a busca manteve 5102 (Crimes contra a Dignidade Sexual) e também recuperou 5218 entre os cinco candidatos. A referência central é 5224 (Erro de Tipo), descendente de 5218, que seria aceito pela régua. O resultado é uma comparação mecânica com a folha-verdade, não uma nova decisão jurídica do assistente. A predominância de um contexto textual não resolve necessariamente o conhecimento cobrado.

## Isolamento e reprodução

A seleção do comparador e dos cortes em cada fold usa somente os grupos internos. Modelos, calibradores, políticas, hashes e a escolha final são gravados antes das previsões das 559. O modelo final em JSON não guarda questões nem rótulos por ID. Não há aprovação especial para IDs conhecidos, soma fixa de confiança ou corte manual a 70%.

Os mesmos cinco candidatos podem receber decisões diferentes após ajuste em grupos diferentes; o teste mede o procedimento inteiro. A confiança não é similaridade. A calibração usa previsões de comparadores que não foram ajustados naquele item. A escolha do corte consulta a calibração; o fold externo avalia a escolha completa. Como a calibração e a seleção são realizadas com poucos dados, a precisão interna não garante a precisão externa.

`reproducao_verificada.json` registra a conferência das 1.677 previsões das três opções nas 559. O comando público executa a opção selecionada; as outras duas reutilizam a mesma representação real e os parâmetros congelados. São bloqueados rede, leitura da folha-verdade, avaliador de acerto, treino supervisionado e recalibração. TF-IDF é reconstruído apenas sobre o catálogo preparado. Nenhum encoder ou LLM é executado.

## Conferir localmente

```bash
python3 -m unittest discover -s isolamento_v17/tests -v
python3 classificar_isolamento_v17.py --saida conferencia_v17
```

Use sempre uma saída nova. O comando produz `classificacoes_experimentais.csv`, `rastreabilidade.jsonl` e `resumo.json`. Ele não gera uma entrega oficial para envio à recrutadora.

Para reproduzir o estudo de desenvolvimento, que consulta os 100 rótulos e depois aplica as três opções nas 559:

```bash
python3 testar_isolamento_v17.py --saida experimentos/isolamento_v17_reproduzido
```

Para repetir a verificação com bloqueios explícitos:

```bash
python3 isolamento_v17/tests/verificar_reproducao.py --saida experimentos/conferencia_bloqueada_v17
```

## Arquivos principais

- `isolamento_v17/modelo.py`: busca fixa, comparadores, escolha e política.
- `isolamento_v17/metricas.py`: precisão, cobertura, adições, perdas e união descritiva.
- `testar_isolamento_v17.py`: protocolo, ajuste, CV aninhada e aplicação no alvo.
- `classificar_isolamento_v17.py`: inferência congelada para questões novas.
- `experimentos/isolamento_v17_001/avaliacao_100.csv`: referências e previsões fora do ajuste.
- `experimentos/isolamento_v17_001/classificacoes_559_todas_variantes.csv`: 1.677 previsões sem rótulos.
- `experimentos/isolamento_v17_001/diagnostico_trocas.json`: IDs corrigidos e prejudicados, somente nas referências.
- `experimentos/isolamento_v17_001/curvas_descritivas_100.csv`: curvas depois da avaliação, sem novo corte escolhido a partir delas.
- `historico/v16_documentacao`: README anterior e inventário dos 724 arquivos recebidos.

## Referências metodológicas da pesquisa anterior

- [Classificação seletiva e compromisso entre erro e cobertura](https://arxiv.org/abs/1705.08500).
- [Documentação scikit-learn: calibração de probabilidades](https://scikit-learn.org/stable/modules/calibration.html).
- [Documentação scikit-learn: ajuste do limiar de decisão](https://scikit-learn.org/stable/modules/classification_threshold.html).
- [Cawley e Talbot: sobreajuste na seleção de modelos](https://www.jmlr.org/papers/v11/cawley10a.html).

Essas fontes fundamentam o desenho de avaliação. Não certificam os rótulos destas questões. O próximo avanço de evidência exige também referências novas e independentes, incluindo questões recentes, sem usá-las simultaneamente para ajustar e validar a solução.
