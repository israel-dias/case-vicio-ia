# Vício IA — experimento multivista V16

**Resultado: ganho pequeno.** A V16 isolada não superou a V15. Preservando a V15 atual e usando a busca V16 calibrada como suplemento, o experimento passa de **392 para 394 publicações nas 559** (70,48%), sem retirar publicações anteriores. As **300 recentes continuam com 218 publicações**. Precisão real das 559 desconhecida.

Na referência de desenvolvimento reutilizada, o suplemento passa de 47/49 para 48/50 publicações corretas (96%). Esse resultado **não comprova 95% nos dados novos**. A comparação adicional é adaptativa e foi motivada pelo resultado negativo da primeira V16; ambos os históricos estão preservados.

Comece por `RELATORIO_MULTIVISTA_V16.md`. As duas questões adicionais completas e os resultados que não funcionaram estão documentados. `publicacao.csv` e `previsao.txt` da raiz continuam sendo controles históricos; este pacote não os substitui nem promove uma entrega.

## Conferir a V16

Python 3.12 e as dependências já usadas na V15:

```bash
python3 -m pip install --timeout 180 --retries 10 -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s multivista_v16/tests -v
```

## Reproduzir as 559 com modelos salvos

Use uma pasta de saída nova. Não é necessário treinar para executar:

```bash
python3 classificar_ampliacao_v16.py --saida inferencia_ampliacao_v16_local
```

O comando recalcula os atributos dos textos, aplica V11, V15 e o suplemento V16 e gera `classificacoes_experimentais.csv`, `base_v15_recalculada.csv` e `resumo.json`. Não lê a folha-verdade nem respostas por ID, não treina, não recalibra e não chama LLM. Pode receber outro JSONL com `--questoes`. A entrada padrão contém somente as 559 fora da referência; a entrega oficial continua exigindo as 659 linhas.

Os novos atributos ignoram disciplina e assunto de origem; a preservação legada mantém o comportamento histórico. O classificador é um protótipo clássico, com buscas textuais TF-IDF/BM25. Não há entendimento jurídico garantido ou resolução das alternativas.

## Reproduzir o estudo de desenvolvimento

```bash
python3 testar_multivista_v16.py --saida experimentos/multivista_v16_local
python3 congelar_multivista_v16.py --experimento experimentos/multivista_v16_local
python3 ampliar_multivista_v16.py --saida experimentos/ampliacao_v15_v16_local
```

O primeiro comando refaz o treino e a avaliação exposta nas 100, e depois classifica as 559. O terceiro **compõe as previsões de desenvolvimento já registradas na rodada de referência `multivista_v16_001`**, para reproduzir a análise adaptativa incluída; ele não executa nova inferência e isso não substitui o comando de classificação acima. A referência dessa composição é `ampliacao_v15_v16_002`; a análise inicial equivalente está preservada em `_001`.

## Histórico V15

Esta atualização implementa a leitura contextual pedida pelo candidato: **lei vinculada ao caso; introduções informativas preservadas em I/II/III, mesmo curtas; “explique o procedimento descrito” retomando o enunciado**. Nenhuma alternativa é resolvida por LLM. Não há decisão por ID, seleção automática do primeiro item ou bônus fixo de confiança.

Comece por `RELATORIO_CONTEXTO_V15.md` e `roteamento_v15/PROTOCOLO_LEITURA.md`. Os exemplos completos e seus resultados estão em `CASOS_CONTEXTO_V15.md`. O material V14 abaixo é histórico.

**Resultado experimental:** `foco_contextual`, corte de 70%, preservando as publicações V11, acertou **47 das 49 publicadas** nas 100 reutilizadas (95,92%). A simulação nas 559 sem rótulo publica **392/559 (70,13%)**, incluindo **218/300 recentes**. A precisão dessas 559 é desconhecida. Esses números não certificam a meta em dados novos; a configuração foi comparada depois de várias rodadas no mesmo conjunto. Ela conserva inclusive erros antigos.

**Esta pasta não promove uma nova entrega.** `publicacao.csv` e `previsao.txt` da raiz continuam sendo os controles históricos V5. Os arquivos novos têm nomes experimentais e não substituem automaticamente sua submissão.

## Conferir a atualização V15

Python 3.12 e as dependências já utilizadas:

```bash
python3 -m pip install --timeout 180 --retries 10 -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s roteamento_v15/tests -v
```

## Rodar o modelo salvo, sem rótulos ou rede

Para reproduzir as **559** decisões da experiência, use a entrada sem rótulos incluída e uma pasta de saída nova:

```bash
python3 classificar_roteamento_v15.py --questoes experimentos/roteamento_v15_002/questoes_559_sem_rotulos.jsonl --variante foco_contextual --corte 70 --politica preservar_v11 --saida inferencia_v15_local
```

O comando gera `classificacoes_experimentais.csv` e `resumo.json`. Não chama modelo de linguagem, não lê a folha-verdade e não retreina. Para novos dados, troque `--questoes` por outro JSONL no mesmo formato. IDs e metadados de origem não são atributos da leitura nova. Com a entrada padrão de 659 questões, haverá também previsões para os 100 itens usados no ajuste final; essas previsões **não são** a avaliação fora de amostra registrada nas tabelas.

## Repetir a experiência de desenvolvimento

Não é necessário repetir o treino para consultar os resultados incluídos. Se quiser reproduzi-lo, use diretórios novos:

```bash
python3 testar_roteamento_v15.py --saida experimentos/roteamento_v15_local
python3 congelar_roteamento_v15.py --experimento experimentos/roteamento_v15_local
python3 auditar_contexto_v15.py --saida experimentos/ablacao_contexto_v15_local
```

A rodada de referência é `experimentos/roteamento_v15_002`. A rodada inicial e suas fontes estão preservadas; a correção seguinte manteve a lei do cabeçalho junto dos itens, sem torná-la um identificador suficiente. As mudanças em resultados após retreino e recalibração estão registradas, não tratadas como uma nova amostra.

## Histórico V14

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
