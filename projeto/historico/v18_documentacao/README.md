# Case Vício IA — contexto e cobrança V18 (experimental)

Esta atualização testa a prioridade do comando e corrige a preparação que confundia cabeçalhos gerais com uma cobrança específica. Também testa o reconhecimento de conceitos compostos que recuperou o tema da Q0274. Inclui o código, os modelos congelados, as comparações e exemplos completos. **Os CSVs da raiz continuam históricos; não são uma nova entrega formal.**

**Resultado da investigação:** Q0274 passou de Punibilidade para Iter Criminis, aceito pela régua de pai/filho. A variante chegou a 74/100 temas aceitos, mas ficou em 36/39 publicações corretas (92,31%); não foi promovida. Nas 559, a alteração morfológica não mudou temas nem decisões.

As 100 referências são desenvolvimento já exposto. As 559 questões fora da folha, incluindo as 300 recentes, não têm precisão real medida. Um identificador forte altera a leitura, sem impor confiança mínima nem publicação automática.

## Conferir a correção

Python 3.12; as dependências estão em `requisitos_v17.txt`.

```bash
python3 -m unittest discover -s contexto_v18/tests -v
python3 classificar_conceitos_v18.py --variante comando_estrito --saida conferencia_conceitos_v18
```

Use uma pasta de saída nova. O comando aplica modelos estatísticos congelados às 559 questões e gera `classificacoes_experimentais.csv`, rastreabilidade e resumo. Não consulta LLM, encoder, rótulos ou internet e não treina nem recalibra. O índice TF-IDF é reconstruído somente com o catálogo versionado. Essa variante é uma comparação explícita, não uma política aprovada para enviar.

Para reproduzir a rota escolhida pelo estudo, omita `--variante comando_estrito`. A escolha foi registrada antes da classificação das 559 e pode continuar sendo o controle original, mesmo que uma alteração corrija exemplos específicos.

## O que ler

- [RESULTADOS_CONTEXTO_V18.md](RESULTADOS_CONTEXTO_V18.md): comparação completa, critérios, resultados e limites.
- [EXEMPLOS_CONTEXTO_V18.md](EXEMPLOS_CONTEXTO_V18.md): Q0230, Q0274, Q0208 e Q0316 completas, com antes/depois.
- `contexto_v18/foco_morfologico.py`: versão adicional com as proteções de cabeçalho, V/F, palavras comuns e conceitos compostos.
- `experimentos/conceitos_v18_001`: protocolo, modelos, validação nas 100, decisões nas 559 e prova de reprodução. `comando_integral_v18_001` guarda a comparação sem a normalização de conceitos.
- `VALIDACAO_V18.json`: testes, verificações de reprodução e preservação do projeto anterior.
- [historico/v17_documentacao/README.md](historico/v17_documentacao/README.md): documentação anterior preservada.

## Demais experimentos desta rodada

O projeto conserva a tentativa inicial, a correção dos identificadores, a extração inicial e seus refinamentos. Cada pasta possui protocolo e resultados próprios; não some seus acertos como se fossem amostras independentes.

```bash
python3 classificar_contexto_v18.py --variante comando_estrito --saida conferencia_comando_literal
python3 rotear_comando_v18.py --saida conferencia_suplemento_literal
```

A composição de suplemento literal tem 395 publicações em 559, uma a mais que o controle V16. A correção dessa nova publicação é desconhecida. Não foi promovida a entrega nem recebe uma precisão global comprovada.

## Reexecutar o estudo

```bash
python3 testar_conceitos_v18.py --saida experimentos/conceitos_reproduzidos
```

Esse comando lê a folha-verdade para refazer treino e validação dentro dos folds e depois aplica modelos congelados às 559. Ele é diferente do comando de inferência acima. Os identificadores e as regras não contêm exceções por ID de questão. Guardar os protocolos e os resultados anteriores mantém explícita a evolução do método; não torna o desenvolvimento exposto um teste cego.

Não foi feito push no GitHub nem enviado e-mail por esta atualização.

## Investigação adicional da Q0274

A pedido do candidato, a Q0274 também motivou uma variante que aproxima flexões em conceitos compostos: “consumado/consumada/consumação” e “tentado/tentativa”, entre outras formas versionadas. O alvo é o título preparado do catálogo, não uma resposta calculada pelo assistente. Uma palavra comum isolada continua insuficiente, e listas gerais não ativam essa prioridade. O código está em `contexto_v18/foco_morfologico.py`; o estudo e o runtime estão em `testar_conceitos_v18.py` e `classificar_conceitos_v18.py`.

```bash
python3 classificar_conceitos_v18.py --variante comando_estrito --saida conferencia_conceitos_v18
```

Consulte os resultados no relatório V18 antes de escolher essa variante. A correção de uma referência conhecida não autoriza presumir acerto nas 559.
