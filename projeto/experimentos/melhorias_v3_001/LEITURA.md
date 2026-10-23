# Experimento v3 — referências e candidatos próximos

Resultados de desenvolvimento nos 100 rótulos conhecidos, com as mesmas divisões da v2. Não é teste externo cego. As 559 questões avaliadas pela empresa não foram usadas no treino ou escolha das regras.

| Variante | Acertos top1/100 | Publicadas | Corretas | Precisão | Cobertura | Brier |
|---|---:|---:|---:|---:|---:|---:|
| controle_v2 | 66 | 20 | 20 | 100.00% | 20.00% | 0.1831 |
| referencias_fixa | 66 | 23 | 22 | 95.65% | 23.00% | 0.1676 |
| candidatos_proximos | 70 | 0 | 0 | indefinida | 0.00% | 0.2149 |
| ranking_hibrido | 71 | 11 | 9 | 81.82% | 11.00% | 0.1806 |
| selecionado_internamente | 67 | 26 | 25 | 96.15% | 26.00% | 0.1578 |

A seleção interna escolhe a variante com mais publicações internas sob a meta empírica de 95% e suporte mínimo de dez. Empates usam acerto top1 e favorecem o controle. A política fica salva antes da avaliação externa.

As normas e intervalos são associações documentais propostas; não são parecer jurídico. A citação é um atributo auxiliar. Homônimos não são fundidos. Nenhuma questão tem uma resposta ou decisão escrita à mão.

A variante fixa preserva o tema da busca e testa apenas os novos atributos. As outras duas podem trocar o candidato. Fora automático e extras automáticos continuam desativados.

O resultado das 559 depende da execução do modelo final e sua precisão permanece desconhecida. Repetir esta execução reproduz o mesmo experimento; não produz nova evidência independente.
