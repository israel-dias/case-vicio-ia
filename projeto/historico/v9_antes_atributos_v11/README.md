# Case Vício IA — experimento de relações v9

Experimento isolado; não substitui a entrega. Leia [RELATORIO_RELACOES_V9.md](RELATORIO_RELACOES_V9.md) para método, resultados e limites.

A identificação direta refinada publicou 36/100, acertando 35 temas (97,22% nessa amostra reutilizada). Nas 559 sem rótulo, simula 352 publicadas (62,97%), com precisão real desconhecida. Não há garantia de 95%.

```bash
python3 -m pip install -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s experimento_relacoes_v9/tests -v
python3 testar_relacoes_v9.py --saida experimentos/relacoes_v9_reproduzida
python3 classificar_relacoes_v9.py --variante titulos_diretos --saida classificacao_v9_reproduzida
```

Use saídas novas. A avaliação consulta a folha-verdade; a inferência não consulta rótulos, não treina e não chama LLM. O CSV/previsão da raiz são controles v5 históricos, NÃO resultados v9. Instruções v8 preservadas em historico/v8_antes_relacoes_v9.
