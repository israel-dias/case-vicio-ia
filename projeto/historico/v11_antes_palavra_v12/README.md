# Case Vício IA — ablação de atributos v11

Experimento isolado. Leia [RELATORIO_ATRIBUTOS_V11.md](RELATORIO_ATRIBUTOS_V11.md) para as nove variantes, duas políticas, exemplos e limites.

A candidata sem_apoio_duplo + preservar passou de 36 publicadas/35 corretas para 40/39 nas 100 reutilizadas. Nas 559 sem rótulo, simula 361 publicações (64,58%), contra 352 (62,97%) da V9. A precisão real nas 559 é desconhecida; não há garantia populacional de 95%.

```bash
python3 -m pip install -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s experimento_atributos_v11/tests -v
python3 testar_atributos_v11.py --saida experimentos/atributos_v11_local
python3 congelar_atributos_v11.py --experimento experimentos/atributos_v11_local
```

Inferência experimental sem rótulos, treino ou LLM:

```bash
python3 classificar_atributos_v11.py --variante sem_apoio_duplo --politica preservar --saida inferencia_v11_local
```

Use saídas novas. O CSV/previsão da raiz são controles históricos v5, não resultados v11. A entrega anterior não foi substituída. A documentação v9 está em historico/v9_antes_atributos_v11.
