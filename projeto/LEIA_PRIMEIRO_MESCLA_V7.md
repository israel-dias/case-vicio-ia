# Experimento v7 — mescla de marcadores e alternativas

Este ZIP é um complemento para o projeto `case-vicio-ia-etapa2-flexivel-v5`.
Extraia seu conteúdo dentro dessa pasta. Requer os anexos e artefatos da v5;
não exige novas dependências, API, LLM ou pagamento.

Leia `experimentos/mescla_marcadores_v7_002/ANALISE.md` para resultados,
limitações e exemplos com enunciados e alternativas completos.
A tentativa 001 foi preservada com seu código e a explicação da correção.

Dentro da pasta do projeto:

```bash
python3 -m unittest discover -s mescla_marcadores_v7/tests -v
python3 reproduzir_mescla_v7.py --saida simulacao_local_v7
```

Esse segundo comando usa os pesos salvos e gera
`simulacao_local_v7/classificacoes_experimentais.csv` para os 659 itens.
Não lê a folha-verdade e não executa treino. Escolha outra pasta se já existir.

Para refazer também o experimento de treino e avaliação por grupos:

```bash
python3 avaliar_mescla_v7.py --saida experimentos/mescla_marcadores_v7_003
```

Use sempre uma pasta nova. A execução medida do experimento foi de cerca de
30 segundos neste ambiente, com variação esperada conforme a máquina.

## Como interpretar

A mescla acertou 67 sugestões nos 100 rótulos; 16/16 publicadas na avaliação
por grupos foram corretas. Nas 559, simula 289 publicações (51,70%), com
precisão real desconhecida e média das confianças de 86,84%. O novo corte é
mais baixo: parte do volume adicional vem da política, não de maior confiança.
Não há comprovação da meta de 95% nas 559. Este pacote não substitui a entrega.
`publicacao.csv` e `previsao.txt` do projeto permanecem como estavam.
