# Case Vício IA - etapa complementar, versão 2

Classificador de escopos com compatibilidade aprendida e abstenção. **A decisão roda sem LLM, sem rede e sem consultar a folha-verdade.** O código de inferência não usa uma tabela de respostas por ID.

Nas 559 questões avaliadas pela empresa: **152 publicar, 407 revisar e 0 fora**, cobertura **27,19%**. Precisão prevista: **90,34%**; precisão real desconhecida. **A previsão está abaixo da meta de 95%; esta versão não demonstra que a meta foi atingida.**

Na CV de desenvolvimento, a variante fixa acertou 20/20 publicadas, com cobertura de 20%; a seleção interna de variantes acertou 19/20. Os 100 rótulos já foram vistos e usados anteriormente. A variante fixa foi escolhida após olhar a comparação. Esses resultados não são aprovação independente ou garantia para as 559 questões.

## Regenerar o CSV

Com Python 3.12 e ambiente virtual ativo, da raiz deste projeto:

```bash
python3 -m pip install -r requirements-v2.txt
python3 classificar_compatibilidade_v2.py --artefatos artefatos/compatibilidade_v2 --questoes dados/anexos/questoes.jsonl --saida entrega_reproduzida_v2
cmp publicacao.csv entrega_reproduzida_v2/publicacao.csv
```

O classificador lê o modelo congelado e o JSONL e recalcula as decisões. Não lê `folha_verdade.csv`, não acessa a rede e não executa treino supervisionado. O catálogo TF-IDF é reconstruído deterministicamente dos textos preparados. Para uma importação nova, troque o JSONL; preserve os campos. O ID só identifica a saída. Campos sem conteúdo ou ausência completa de candidato interrompem a importação para triagem, em vez de inventar um tema.

## Verificações e entrega completa

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s experimento_folha_v2/tests -v
python3 finalizar_compatibilidade_v2.py --saida entrega_reproduzida_completa_v2
cmp publicacao.csv entrega_reproduzida_completa_v2/publicacao.csv
cmp previsao.txt entrega_reproduzida_completa_v2/previsao.txt
```

Use pastas de saída novas. A consolidação verifica os registros de desenvolvimento, lê os rótulos apenas para conferência e recorte da previsão, e aplica o modelo já congelado. Não escolhe outro corte nem treina o modelo. Aprovar testes verifica o software, não o acerto jurídico das 559.

Para gerar o PDF de quatro páginas a partir do documento paginado:

```bash
python3 -m pip install -r requirements-relatorio.txt
python3 gerar_relatorio_pdf.py --entrada entrega_etapa2_v2/relatorio_paginas.json --saida relatorio_reproduzido_v2.pdf
```

## Como a classificação funciona

1. O classificador congelado de escopos escolhe uma família ativa de nível 1. Títulos iguais em ramos diferentes continuam distintos; disciplina raiz nunca é tema final.
2. O modelo logístico de compatibilidade usa 22 sinais por par questão-família. Enunciado, comando e todas as alternativas são preservados. Metadados são apoio fraco, não filtro obrigatório; citações são extrações literais, não resolução da questão.
3. O calibrador estima a chance de o central escolhido estar certo. Publicar exige score mínimo de 0,03 e confiança acima do corte aprendido. Dois candidatos próximos não exigem revisão automaticamente.
4. Extras não são gerados a partir do top5. Os extras oficiais são usados na convenção de treino e avaliação. Fora automático permanece desativado: há apenas oito exemplos oficiais e baixa similaridade não prova ausência de tema.

O ranking de temas da v1 é preservado. O que muda é a evidência usada para publicar/revisar e a confiança. Confira `entrega_etapa2_v2/resumo_entrega.json` para contagens e transições; não se infere melhora de precisão das 559 apenas pelo aumento de cobertura.

## Uso dos 100 rótulos

Os ensaios históricos e a divisão inicial 60/20/20 estão preservados. A nova CV usa cinco folds externos e quatro internos, mantendo duplicatas no mesmo grupo. A seleção de cortes e variantes usa somente os folds internos de cada rodada. Ainda assim, os rótulos já influenciaram preparação e discussões: é desenvolvimento, não teste externo inteiramente cego.

Depois de escolher a candidata, o modelo final foi treinado nos 100 rótulos e a confiança/corte foram ajustados aos seus sinais OOF. O corte final selecionou 27/28 itens aceitos nesse desenvolvimento; esse número é distinto dos 20/20 da CV. Não houve ajuste usando as 559 sem rótulo. A precisão verdadeira das 300 recentes continua desconhecida.

A previsão é a média das confianças nas publicadas das 559. A faixa é uma sensibilidade descritiva, não garantia populacional. A cobertura do lote é contagem exata; seu intervalo cobre apenas arredondamento. Não se elevou a previsão para 95% para fazê-la coincidir com a meta.

## Arquivos principais

| Arquivo | Conteúdo |
|---|---|
| `publicacao.csv` | As 659 decisões no formato oficial |
| `previsao.txt` | Autoavaliação referente às 559 fora da folha |
| `relatorio.md` / `relatorio.pdf` | Quatro páginas, incluindo memo de uma página |
| `artefatos/compatibilidade_v2` | Catálogo, escopos, coeficientes, calibrador e política; sem rótulos por questão |
| `compatibilidade_v2/runtime.py` | Decisão executada sem LLM e sem rótulos |
| `treinar_compatibilidade_v2.py` | Como os 100 rótulos geraram o artefato |
| `protocolo_final_v2.json` | Escolhas registradas antes do treino e da inferência final |
| `experimentos/folha_v2_escopos_001` | CV recebida e verificada, previsões e parâmetros por fold |
| `entrega_etapa2_v2/rastreabilidade.jsonl` | Evidências, confiança, candidatos e motivo por questão |
| `entrega_etapa2_v2/fila_revisao.csv` | Sugestões para os itens em revisão |
| `entrega_etapa2` | Entrega anterior preservada, sem substituição retrospectiva das métricas |
| `docs/DECISOES_V2.md` | Diagnóstico e escolhas para explicar na apresentação |

Hashes verificam integridade, não verdade jurídica. Os 360 escopos propostos pelo assistente não têm validação jurídica independente. A preparação por IA está separada da classificação: não se usam votos do assistente, gabaritos externos ou respostas da etapa 1 para decidir as novas classificações.

## Reproduzir o treino final

```bash
python3 treinar_compatibilidade_v2.py --saida artefatos/compatibilidade_v2_retreinado
```

Esse comando exige os 100 rótulos e os registros OOF históricos; não é o comando de inferência. Preserva o artefato anterior. Para reconstruir a CV, consulte `experimento_folha_v2/README.md` e indique `--dados dados/anexos`; os resultados são desenvolvimento e repetir a execução não cria uma nova amostra independente.

## Custo, tempo e produção

API de classificação executada: **US$ 0**. Não há chave ou chamada a LLM no runtime. Há dependências NumPy/SciPy/scikit-learn para as operações clássicas de texto e regressão logística. Modelos identificados por tipo, parâmetros, dependências e hashes; identificador exato do assistente da conversa não confirmado, tokens não medidos, assinatura não rateada.

Tempo observado nesta consolidação: aproximadamente **6.740 s** para as 659 classificações, além de **0.147 s** de preparação/leitura. Tempo humano da etapa complementar não foi instrumentado. O JSON separa medições e extrapolações. O custo de compute com tarifa hipotética não é cotação; a revisão humana domina o cenário de 50 mil por semana. Mais rótulos independentes e melhoria de escopos são necessários antes de escalar essa fila.
