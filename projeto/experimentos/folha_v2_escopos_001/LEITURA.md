# Experimento sobre a folha-verdade — versão 2

Este é um experimento independente sobre os 100 rótulos já conhecidos. As 559 questões sem rótulos não foram classificadas. Não é um novo teste externo cego.

Nesta execução, o controle usa os escores do classificador de escopos congelado do projeto informado. As variantes usam exatamente esses mesmos escores como evidência, além dos campos textuais e, quando aplicável, dos vizinhos oficiais de treino. Os folds e a calibração deste experimento são novos; não é uma reprodução do teste reservado antigo. A origem e os hashes estão em protocolo_previo.json.

| Método | Top1/100 | Publicar | Acertos nas publicadas | Precisão | Cobertura | Fora oficial publicada |
|---|---:|---:|---:|---:|---:|---:|
| lexical_margem | 66 | 21 | 19 | 90.48% | 21.00% | 2 |
| compatibilidade_fixa | 66 | 20 | 20 | 100.00% | 20.00% | 0 |
| compatibilidade_ranking | 64 | 2 | 1 | 50.00% | 2.00% | 0 |
| compatibilidade_vizinhos | 66 | 1 | 0 | 0.00% | 1.00% | 0 |
| selecionado_internamente | 65 | 20 | 19 | 95.00% | 20.00% | 0 |

## O que está sendo testado

1. **Régua correta:** tema central, extras e ancestrais/descendentes de cada referência são aceitos. Irmãos não são equivalentes automaticamente.
2. **Compatibilidade:** cada par questão–família recebe um sinal independente. Duas famílias com sinal alto podem coexistir; a margem entre elas deixa de ser veto automático.
3. **Leitura por campos:** enunciado, comando e todas as alternativas são preservados e comparados separadamente. O sistema não conhece a alternativa certa e não confunde essas comparações com uma resolução jurídica.
4. **Exemplos oficiais:** na variante com vizinhos, apenas os rótulos de treino auxiliam o cálculo. O próprio texto e duplicatas normalizadas são excluídos dos vizinhos.
5. **Origem e citações:** disciplina de origem é uma evidência fraca aprendida, nunca um filtro obrigatório. Leis e artigos são extraídos literalmente; uma citação não determina o tema.
6. **Fora:** itens oficiais fora recebem alvos negativos para todas as famílias. O experimento mede publicações indevidas desses itens, mas não ativa exclusão automática com apenas oito exemplos.

## Avaliação e limites

Cada um dos cinco folds externos recebe previsões produzidas com os outros quatro. Dentro do treino externo, quatro folds internos geram sinais fora do próprio treino. Somente esses sinais internos ajustam a confiança, escolhem o corte e selecionam a variante. Textos duplicados ficam no mesmo grupo.

A regra exige pelo menos dez publicações internas com 95% de acerto empírico. Isso é um critério de seleção, não uma comprovação estatística. As probabilidades são estimativas regularizadas; devem ser examinadas com o Brier e os erros externos. O ajuste do calibrador e do corte usa os mesmos sinais internos, portanto a avaliação dessas escolhas é feita nos folds externos.

**A linha `selecionado_internamente` representa a escolha do algoritmo antes de ver cada fold externo.** Escolher depois a linha de melhor resultado produz uma nova decisão de desenvolvimento e exige confirmação em dados novos. Os 100 rótulos já influenciaram discussões anteriores; a validação cruzada não apaga essa exposição.

As famílias candidatas são nós ativos de nível 1, cuja escolha é aceita quando está na cadeia de uma referência oficial. Isso não torna os subtemas irmãos equivalentes. O pacote não atribui extras automaticamente, nem usa nomes encontrados nos distratores como rótulos.

Tempo medido nesta execução: 169.101 s, incluindo preparação, ajustes e avaliação. Não é a latência de classificar uma questão nem uma projeção para 50 mil.

Nenhum `publicacao.csv` ou `previsao.txt` anterior é alterado. O repositório principal só deve adotar a variante após examinar os resultados e registrar uma nova versão. O pacote não garante a meta de 95% nas questões que a empresa guardou.
