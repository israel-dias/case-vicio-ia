# Leitura contextual V15

Hipóteses de pré-processamento propostas pelo candidato e implementadas em regras gerais. Nenhuma regra depende do ID de uma questão. O programa não pesquisa gabaritos, resolve alternativas por LLM ou altera os rótulos da equipe.

| Situação | Regra de leitura | O que não é concluído automaticamente |
|---|---|---|
| Citação de lei ou artigo | Conservar o trecho e o caso, comando ou proposições a que se refere. Distinguir o código citado. | A citação sozinha não certifica o tema nem resolve seu ramo. |
| Introdução informativa antes de I/II/III | Preservar a introdução e todos os itens. A variante de foco dá peso próprio à introdução. | Quantidade de palavras ou de itens não mede precisão. |
| Introdução curta, mas temática | Preservar delimitadores como “À luz das teorias das penas”. | A frase pode delimitar uma área sem identificar um único ID. |
| Cabeçalho meramente instrucional | Omitir da representação temática, mantendo o texto original no anexo. | Não remover um cabeçalho apenas porque é curto. |
| Cabeçalho que cita só uma norma e depois apresenta itens | Manter a norma como referência compartilhada com os itens. | Não tomar a norma isolada como o objeto efetivamente cobrado. |
| “Explique o procedimento descrito”, “nessa situação” e retomadas semelhantes | Ler o enunciado como antecedente e conservar o comando útil. | Ausência de nome de tema no comando não força revisão. |
| Comando temático explícito | Usar seu sinal junto com o conteúdo preservado. | Não descartar automaticamente o caso ou as alternativas. |
| Itens sobre vários conteúdos | Conservar todos. Média, máximo e apoio dos itens continuam atributos comparáveis. | Não escolher o primeiro item ou a maioria como resposta definitiva. |
| Certo/Errado, números e combinações I/II/III nas alternativas | Não gerar evidência temática dessas opções. | Não resolver a assertiva ou inferir gabarito a partir das letras. |
| Alternativas com conteúdo | Conservar como apoio, inclusive quando a narrativa contextualiza outro assunto. | Não adicionar todos os candidatos como extras. |
| Homônimos em ramos diferentes | Manter os IDs distintos e a proteção para evidência empatada. | Não escolher o menor ID para resolver um escopo desconhecido. |

## Como a prioridade é implementada

O detector usa conteúdo não instrucional, identificadores do catálogo e expressões delimitadoras. Não é um parser jurídico ou sintático completo. Uma introdução é informativa se contém identificadores, três ou mais termos informativos, ou um delimitador temático acompanhado de pelo menos dois termos. Essas são hipóteses operacionais registradas para comparação; não são verdades universais da linguagem. Uma referência normativa isolada não recebe prioridade temática por esse detector.

Na variante `foco_contextual`, com itens e cabeçalho informativo, a recuperação combina 45% do sinal do cabeçalho, 35% do conjunto e 20% da média dos escopos dos itens. Num comando temático independente, combina 55% do comando e 45% do conjunto. Numa retomada, combina 65% do enunciado e 35% do conjunto. Os pesos operam sobre escores de recuperação: **não são percentuais de certeza**. O conteúdo preservado também compõe os atributos do comparador clássico.

`contexto_sem_prioridade` conserva os mesmos campos e atributos, mas usa o ranking do conjunto. `fusao_contextual` combina 70% do ranking histórico V8 e 30% do ranking de foco, após normalização de suas escalas. O mesmo ajuste de compatibilidade pode servir às três variantes porque seus atributos são iguais; os rankings e a calibração são diferentes.

## Decisão e avaliação

O modelo clássico compara famílias de temas. Uma regressão logística de calibração converte o sinal em uma estimativa de acerto usando previsões internas. O corte de 70% e a política calibrada são comparados separadamente. Identificadores não recebem um bônus fixo de confiança. Um empate relevante entre escopos homônimos pode continuar exigindo revisão mesmo acima do corte.

`preservar_v11` conserva as decisões e confianças publicadas pelo controle V11. Não utiliza os rótulos para escolher individualmente qual versão preservar: conserva inclusive seus erros. `substituir` usa somente o modelo novo.

Os 100 rótulos foram vistos e reutilizados em várias rodadas. Os cinco folds externos e quatro internos evitam vazamento direto de rótulos no ajuste de cada fold, mas não tornam esta análise um teste externo cego. Escolher uma configuração após observar vários resultados aumenta o risco de otimismo. A precisão das 559 sem rótulo e das 300 recentes permanece desconhecida. Não há regra automática de `fora` nesta experiência; ausência de sinal não prova ausência de tema.

O controle `auditar_contexto_v15.py` conserva o mesmo recuperador V8 e muda somente os campos lidos. Suas retiradas de contexto são controles de diagnóstico, não recomendações. Ele mede acerto do primeiro candidato, não confiança ou precisão de publicações.
