# Vício IA — experimento de roteamento V14

**Nenhuma configuração nova com corte de 70% demonstrou atingir 95% nas publicadas das 100.** Esta pasta é experimental e preserva a entrega anterior. `publicacao.csv` e `previsao.txt` da raiz são controles históricos V5; não são entrega V14.

Comece por `RELATORIO_ROTEAMENTO_V14.md`. As exceções têm questões completas em `EXCECOES_REGRAS_V14.md`. As limitações de escopo e os oito fora oficiais estão em `roteamento_v14/PENDENCIAS_ESCOPO.json`.

A rodada 002 inclui suas hipóteses de comando, Explique, instruções, I/II/III, maioria/primeiro item, Certo/Errado, caso narrado, situação hipotética, referências normativas, desconhecimento e condição da vítima. Compara descarte literal, contexto preservado, reordenação treinada e fusão conservadora. Identificação é heurística textual, não certeza jurídica. As alternativas numéricas/Certo-Errado não recebem evidência temática. Os originais foram preservados.

Os mesmos 100 rótulos foram reutilizados em vários estudos. Há cinco grupos externos e quatro internos, mas isso não torna o resultado teste externo cego. A precisão das 559 e dos 300 recentes é desconhecida.

## Conferir o pacote

Python 3.12 e as dependências já usadas:

```bash
python3 -m pip install --timeout 180 --retries 10 -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s roteamento_v14/tests -v
```

## Reproduzir o estudo completo

Use uma pasta nova. Não é necessário retreinar para consultar os resultados já incluídos.

```bash
python3 testar_roteamento_v14.py --saida experimentos/roteamento_v14_local
python3 congelar_roteamento_v14.py --experimento experimentos/roteamento_v14_local
python3 auditar_regras_v14.py --saida experimentos/ablacao_leitura_v14_local
```

O último comando é diagnóstico separado: mantém o recuperador V8 e compara somente as mudanças de leitura nas 100. Não mede confiança e não publica questões. Para reproduzir esta ablação exata, lê as rotas da rodada 002 incluída; isso está declarado em seu protocolo.

## Inferência experimental sem rótulos ou rede

```bash
python3 classificar_roteamento_v14.py --variante fusao_conservadora --corte 70 --politica substituir --saida inferencia_v14_local
```

Esse comando é para examinar uma hipótese que NÃO foi aprovada para substituir a entrega. `--questoes caminho/novas.jsonl` aceita outros IDs e textos. `--politica preservar_v11` conserva as publicações da referência, incluindo eventuais erros. `--corte calibrado` utiliza os cortes internos congelados em vez de 70%. `--experimento experimentos/roteamento_v14_local` usa sua reprodução.

O padrão classifica as 659 questões. As 100 utilizadas no ajuste final recebem previsões de treino nesse comando: não confunda essas previsões com as OOF do relatório. O teste de reprodução incluído verifica as 559 sem rótulo; a classificação não consulta a folha-verdade, retreina ou chama LLM.

## Registros

- `experimentos/roteamento_v14_002/protocolo_previo.json`: variantes, parâmetros e hashes.
- `experimentos/roteamento_v14_002/avaliacao_100.csv`: avaliações por grupo, cortes e políticas.
- `experimentos/roteamento_v14_002/simulacao_559.csv`: resultados sem rótulo.
- `experimentos/roteamento_v14_002/campos_659.json`: campos incluídos e descartados em cada rota.
- `experimentos/roteamento_v14_002/excecoes_regras_100.json`: divergências da literal, com questão e referência.
- `experimentos/roteamento_v14_002/folds`: modelos, calibradores e cortes por grupo.
- `experimentos/roteamento_v14_002/modelos_finais.json`: parâmetros, sem tabela de respostas por ID.
- `experimentos/roteamento_v14_002/reproducao_verificada.json`: conferência offline das 559.
- `experimentos/ablacao_leitura_v14_001`: comparação com o mesmo recuperador anterior.
- `experimentos/roteamento_v14_001` e `historico/v14_rodada_inicial`: tentativa inicial e seu código, preservados.

A rodada 002 corrigiu o reconhecimento de situação hipotética também no comando e acrescentou a fusão após a regressão inicial. A ablação veio depois. Essas etapas são desenvolvimento adaptativo nos mesmos dados, sem alegação de nova validação independente. Não houve alteração de gabaritos nem envio à recrutadora ou publicação pelo assistente.
