# Experimento de foco referencial v6

Complemento da pasta `case-vicio-ia-etapa2-flexivel-v5`. Não substitui a entrega.
Contém código, testes, protocolo anterior à execução, modelos diagnósticos,
resultados nos 100 rótulos, extrações dos 659 enunciados e simulações nas 559.

Leia `experimentos/foco_referencial_v6_001/ANALISE.md` para os exemplos completos.
Não use as simulações como um novo CSV de entrega: esta tentativa reduziu a cobertura.

Para reproduzir, extraia este ZIP dentro da pasta do projeto v5 e execute ali:

```bash
python3 -m unittest discover -s foco_referencial_v6/tests -v
python3 avaliar_foco_referencial_v6.py --saida experimentos/foco_referencial_v6_002
```

Use outra pasta de saída se `002` já existir. São usadas as mesmas dependências
instaladas na v5 e os anexos originais. Não há instalação adicional ou chave de API.
A execução local medida demorou aproximadamente 22 segundos; varia por máquina.

A busca exclusiva e a ponderada são hipóteses documentadas, com novo treino e
calibração. A liberação absoluta é apenas um diagnóstico sem probabilidade calibrada.
Os rótulos das 559 não foram consultados; a precisão delas permanece desconhecida.
As regras são gerais e não contêm decisões ou exceções escritas por ID.
