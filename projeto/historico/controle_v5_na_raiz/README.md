# Case Vício IA — classificação de tópicos, etapa complementar

Versão v5: **271 publicar, 388 revisar, 0 fora nas 659 questões**. Nas **559 avaliadas**, excluindo a folha-verdade: **231 publicar e 328 revisar**, cobertura **41,32%**. Precisão prevista **90,44%**; precisão real **não medida**. A meta de 95% nas questões avaliadas não foi comprovada.

## Reproduzir a entrega

Python 3.12. O modelo está congelado e a classificação não exige chave de API ou acesso à internet. Instale as dependências apenas se necessário:

```bash
python3 -m pip install --timeout 180 --retries 10 -r requirements-v2.txt
python3 -m unittest discover -s flexivel_v5/tests -v
python3 finalizar_flexivel_v5.py --saida entrega_reproduzida_v5
cmp publicacao.csv entrega_reproduzida_v5/publicacao.csv
cmp previsao.txt entrega_reproduzida_v5/previsao.txt
```

Use uma saída nova em cada execução. Se os dois `cmp` não imprimirem nada e encerrarem com código zero, os arquivos são idênticos aos da raiz. O exportador confere os anexos originais, classifica as 659 e exclui os 100 rótulos apenas do denominador da previsão. As classificações são feitas sem ler a folha-verdade.

Para classificar um JSONL novo no mesmo formato, sem folha-verdade:

```bash
python3 classificar_flexivel_v5.py --questoes novas_questoes.jsonl --saida nova_classificacao
```

## Simplificação aplicada

Foram retirados três atributos preditivos independentes: indicador de Certo/Errado, indicador de assertivas numeradas e número de alternativas. O modelo usa 36 das 39 colunas anteriores. Os textos continuam completos. Referências normativas, conteúdo e estrutura da árvore continuam disponíveis. Os alertas de mapeamento e origem são informativos, sem bloqueios adicionais à política.

A mudança usa o experimento documentado em `experimentos/auditoria_confianca_v4_002`, que comparou a versão anterior com oito alternativas. Nos 100 exemplos conhecidos, em cinco grupos externos com quatro internos, a candidata teve **24 acertos em 25 publicadas (96%)**, contra **22 em 23 (95,65%)** no controle. A diferença é pequena, e os dados já foram expostos durante desenvolvimento. Esse resultado não garante 95% nas 559.

O corte final recalibrado é 0,7738553900. Não foi escolhido para liberar questões específicas. O tema central permanece o primeiro candidato da busca anterior; nenhum tema foi trocado nesta simplificação. A v5 liberou 57 revisões e devolveu uma publicação à revisão, ganho líquido de 56. Os detalhes estão em [docs/FLEXIBILIZACAO_V5.md](docs/FLEXIBILIZACAO_V5.md).

## Pipeline e origem dos artefatos

1. Limpeza de HTML preservando enunciado, negação, comando e alternativas.
2. Busca lexical sobre títulos e escopos versionados, agregando temas em famílias sem publicar em disciplinas raiz.
3. Representação textual por campo e extração literal de leis e artigos.
4. Regressão logística treinada para estimar a compatibilidade do candidato com a questão.
5. Calibração logística e corte de publicação aprendidos nos sinais de desenvolvimento fora do treino.
6. Exportação de decisões, confiança, previsão e rastreabilidade.

O modelo usado é `sem_formato`, previamente escolhido pelo suporte nos sinais dos 100 antes de observar a quantidade publicada nas 559. O artefato não guarda respostas ou temas por ID de questão. Os rótulos temáticos da empresa são usados no treinamento e na avaliação, com a régua de central, extras e ancestrais/descendentes. Irmãos não são fundidos.

Para recriar o artefato congelado em outra pasta, sem alterar a avaliação original:

```bash
python3 preparar_flexivel_v5.py --saida artefatos/flexivel_v5_reproduzido
```

Para repetir a auditoria comparativa:

```bash
python3 auditar_confianca_v4.py --saida experimentos/auditoria_reproduzida
```

O código do experimento, as divisões, os modelos de cada grupo e os hashes ficam registrados. A repetição reproduz o procedimento; não cria nova evidência independente.

## Onde conferir

| Arquivo | Conteúdo |
|---|---|
| `publicacao.csv` | 659 decisões no formato do case |
| `previsao.txt` | Previsão para as 559, com faixa de sensibilidade e explicação |
| `relatorio.md` | Sistema, uso dos rótulos, diagnóstico, produção e memo |
| `artefatos/flexivel_v5` | Parâmetros, catálogo, escopos e referências congelados |
| `flexivel_v5/runtime.py` | Classificação sem LLM, rótulos ou treinamento supervisionado |
| `entrega_flexivel_v5/rastreabilidade.jsonl` | Atributos, confiança e notas de cada questão |
| `entrega_flexivel_v5/comparacao_com_v3.json` | Transições e preservação dos temas |
| `experimentos/auditoria_confianca_v4_002` | Comparações com remoção de atributos |
| `historico/v3_antes_flexibilizacao` | CSV, previsão e documentos da v3 |
| `historico/auditoria_v4` | Parecer e documentos anteriores à promoção da candidata |

## Modelos, custo, tempo e limites

A decisão usa busca TF-IDF, regressão logística e calibração logística, com NumPy, SciPy e scikit-learn nas versões de `requirements-v2.txt`. O assistente ajudou a escrever código e organizar dados de escopo; seu identificador exato não foi registrado. Não houve resolução por LLM, escolha ou validação manual de temas das 559 nesta versão.

Custo executado de API na classificação: **US$ 0**. A assinatura existente não foi rateada; tokens e tempo total de desenvolvimento não foram instrumentados. Uma execução local classificou as 659 em aproximadamente **14,16 segundos**, incluindo preparação. Esse tempo não é latência de um LLM nem benchmark de produção.

A faixa de precisão é descritiva e não constitui intervalo de confiança válido para o acerto das 559. A cobertura é conhecida para este lote. O método mantém as limitações da escolha inicial de tema, não produz extras automaticamente e encaminha possíveis ausências de taxonomia à revisão. Não usa gabaritos de alternativas nem respostas inferidas por IA.

Os testes verificam contratos, integridade, ausência de rótulos na inferência, independência de IDs e reprodução dos arquivos. Não verificam acerto jurídico. O experimento investigou uma simplificação e não demonstrou que todas as revisões restantes sejam desnecessárias.
