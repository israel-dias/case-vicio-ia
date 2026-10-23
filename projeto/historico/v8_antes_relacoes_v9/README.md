# Vício IA — experimento de vocabulário v8

Pacote completo de desenvolvimento: inclui dados, artefatos e histórico anteriores.
Não precisa extrair outros ZIPs por cima. Não é uma nova entrega com precisão validada.

O vocabulário só na busca elevou as sugestões corretas de 67 para 70 nos 100
exemplos e simulou 287 publicações nas 559 (51,34%), contra 289 na v7. A precisão
real das 559 é desconhecida; a média das confianças publicadas é 87,86%.
Os 100 rótulos já eram conhecidos e reutilizados.

**publicacao.csv e previsao.txt da raiz são os controles v5 preservados.**
As saídas v8 são experimentais e ficam em uma nova pasta de simulação.

## Rodar sem treino ou rótulos

Python 3.12. Se necessário, instale as mesmas dependências da v5:

```bash
python3 -m pip install --timeout 180 --retries 10 -r requirements-v2.txt
```

Dentro desta pasta:

```bash
python3 -m unittest discover -s vocabulario_v8/tests -v
python3 reproduzir_vocabulario_v8.py --saida simulacao_local_v8
```

Escolha uma pasta de saída nova. O segundo comando gera
classificacoes_experimentais.csv, expressoes_detectadas.jsonl e resumo.json para
os 659 itens, sem consultar folha-verdade, sem treinar e sem LLM. Não requer API.
Os 659 incluem os 100 usados no ajuste final; não confundir o total com a
avaliação por grupos ou com as 559 avaliadas pela empresa.

## Refazer os experimentos

```bash
python3 avaliar_vocabulario_v8.py --saida experimentos/vocabulario_v8_002
python3 avaliar_ranking_vocabulario_v8.py --saida experimentos/vocabulario_v8_ranking_002
```

Cada execução precisa de saída nova. Os originais estão nas pastas 001.
A segunda comparação foi motivada pelo resultado da primeira: não é teste cego.

## Conferir

- relatorio.md: método, resultados, limites e exemplos completos.
- vocabulario_v8/dicionario.json: 16 grupos e 53 padrões com origem e alvos.
- vocabulario_v8/texto.py: reconhecimento por campo sem inflar sinônimos.
- vocabulario_v8/experimento.py: atributos de vocabulário e reordenação.
- vocabulario_v8/ranking.py: ablação com vocabulário só na busca.
- experimentos/vocabulario_v8_001: protocolos, modelos, acertos e simulações.
- experimentos/vocabulario_v8_ranking_001: comparação isolada e pesos salvos.
- historico/controle_v5_na_raiz: documentos anteriores preservados.

O dicionário foi proposto pelo assistente e versionado como dado de preparação;
nenhuma resposta ou classificação por ID foi acrescentada. O sistema não publica
só por encontrar uma palavra. A avaliação aceita pais/filhos/extras previstos na
folha-verdade. Homônimos em ramos diferentes permanecem separados.
