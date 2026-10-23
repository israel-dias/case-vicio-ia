# Melhoria da análise da folha-verdade — experimento v2

Este é um pacote novo e independente, reconstruído a partir dos anexos oficiais. **Não é uma cópia do antigo `compatibilidade-vicio.zip`**, cujo arquivo deixou de estar disponível. Os resultados abaixo foram executados novamente com este código.

O objetivo é verificar, por código, se uma classificação fica melhor ao aprender a compatibilidade entre questão e família de temas, respeitando central, extras e hierarquia. O pacote não modifica `publicacao.csv`, `previsao.txt`, os escopos congelados nem os experimentos existentes do projeto principal.

## O que mudou no critério

- **Dois temas plausíveis não significam revisão automática.** Cada família recebe seu próprio sinal; a revisão depende da evidência de acerto e da política aprendida.
- **Central e extras oficiais são aceitos.** Um pai ou filho de qualquer referência também pode contar como certo. Um subtema irmão não é equivalente automaticamente.
- **Enunciado, comando e todas as alternativas entram na análise**, com sinais separados. O sistema não escolhe uma alternativa correta, não recebe gabaritos e não resolve as questões com um LLM.
- **Os exemplos oficiais de treino podem ajudar.** A variante de vizinhos usa apenas os rótulos permitidos no treino da rodada, excluindo o próprio texto e duplicatas.
- **Metadados e citações são evidências fracas.** A disciplina de origem não impõe uma classificação; a citação literal de uma lei ou artigo não determina o tema.
- **Baixa evidência não significa fora.** Os oito itens oficiais fora ajudam a aprender sinais negativos; este experimento não ativa exclusão automática com tão poucos exemplos.

## Resultado já medido

O primeiro cenário usa **somente o catálogo original** dos anexos, sem os escopos enriquecidos do seu projeto anterior. Ele serve como controle independente, não como comparação direta com aquela entrega.

| Método | Acertos de tema/100 | Publicadas | Acertos nas publicadas |
|---|---:|---:|---:|
| Lexical com margem | 48 | 3 | 2 |
| Compatibilidade, tema lexical preservado | 48 | 0 | 0 |
| Compatibilidade para reordenar temas | 51 | 0 | 0 |
| Compatibilidade com vizinhos oficiais | 53 | 0 | 0 |
| Variante escolhida apenas nos folds internos | 53 | 0 | 0 |

**A melhoria no acerto de tema não tornou a publicação automática confiável.** Na seleção interna das variantes novas, nenhum corte reuniu pelo menos dez itens publicados com 95% de acerto empírico. Zero publicações significa precisão indefinida, não 100%. O controle publicou três, mas errou uma. Este cenário não justifica substituir a entrega existente.

As previsões individuais, coeficientes, políticas e divisões estão em `referencia_resultados_v2`. A execução de referência levou aproximadamente 151 segundos neste ambiente. Esse tempo inclui os ajustes repetidos da validação cruzada e não é a latência de inferência de uma questão.

## Instalar e testar

Python 3.12 recomendado, com a sua `.venv` ativada. A partir da pasta principal do seu projeto:

```bash
python3 -m pip install -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s experimento_folha_v2/tests -v
```

As dependências são NumPy, SciPy, scikit-learn e threadpoolctl. Não exige chave de API. Instalar as dependências pode usar internet; o experimento em si não baixa modelos nem acessa serviços externos.

Para reproduzir o cenário independente com os anexos incluídos:

```bash
python3 experimento_folha_v2/experimento.py \
  --saida experimentos/folha_v2_catalogo_001
```

Ou indique explicitamente seus anexos:

```bash
python3 experimento_folha_v2/experimento.py \
  --dados dados/anexos \
  --saida experimentos/folha_v2_catalogo_local_001
```

Use uma pasta de saída nova. A instalação é separada da execução. A repetição das mesmas previsões é reprodução, não outra avaliação independente.

## Testar com os escopos do seu projeto existente

Esse é o cenário necessário para comparar as variantes usando sua base enriquecida. O adaptador espera o projeto da etapa 2, que já possui `calibrar_etapa2.py`, o método congelado e os artefatos de escopos. Ele chama a conferência de integridade existente antes de usar os escores.

```bash
python3 experimento_folha_v2/com_escopos_existentes.py \
  --projeto . \
  --saida experimentos/folha_v2_escopos_001
```

**Este cenário ainda não foi executado com seus arquivos atuais**, que não estavam disponíveis para recuperação. O adaptador tem testes de contrato com arquivos sintéticos; isso não garante que a interface local seja idêntica. Caso a interface divirja, ele interrompe e indica os arquivos necessários para adaptação. Não altere hashes ou regenere os artefatos antigos para contornar um erro.

O controle desse cenário preserva os escores do classificador congelado; as variantes usam esses mesmos escores, além dos sinais por campo e dos vizinhos de treino. Nenhum resultado com os escopos existentes foi inventado ou incluído na tabela anterior. Envie a saída desse comando para analisarmos o resultado.

## Como os 100 rótulos são utilizados

Há cinco folds externos. Cada item é avaliado uma vez com os outros folds no treino. Dentro desse treino, quatro folds internos geram sinais para ajustar a confiança, escolher o corte e selecionar a variante. A regra exige suporte interno mínimo de dez publicações e 95% de acerto empírico. Isso não comprova estatisticamente 95% na população.

Os folds agrupam textos iguais após normalização. Os parâmetros e a política são gravados antes das previsões do fold externo. Os rótulos externos só chegam ao avaliador após essas previsões. No modelo de vizinhos, duplicatas do texto consultado são excluídas, mesmo com outro ID.

Como os 100 rótulos já foram vistos durante o desenvolvimento e as discussões anteriores, **isto é avaliação de desenvolvimento**, não um teste externo inteiramente cego. As 559 questões sem rótulos, incluindo as 300 recentes, não são classificadas por este pacote e sua qualidade não é medida aqui.

A linha `selecionado_internamente` é a avaliação do mecanismo que escolhe uma variante sem ver o fold externo. Escolher a melhor linha depois de olhar a tabela é uma nova escolha de desenvolvimento e precisa de confirmação em dados novos.

## Arquivos

- `modelo.py`: limpeza, árvore, TF-IDF, atributos por campo, compatibilidade e vizinhos.
- `experimento.py`: protocolo, folds, calibração, decisões e avaliação.
- `com_escopos_existentes.py`: adaptador opcional para o projeto local.
- `tests/test_melhoria_folha.py`: proteção contra vazamento, régua incorreta, duplicatas, exclusões indevidas e sobrescrita de saídas.
- `dados/anexos`: cópia dos anexos oficiais recuperados, sem alterações.
- `referencia_resultados_v2`: execução real do cenário com catálogo original.

O pacote não constitui a entrega final atualizada das 659 questões. Seu papel é testar a hipótese antes de decidir se vale substituir alguma parte do sistema existente. O uso de regressão logística e kNN é aprendizado de máquina clássico; nenhum LLM escolhe, vota ou valida as classificações.

## Origem e custos

Dados: `anexos-case-ia.zip` fornecido no processo seletivo. Referência do enunciado: https://github.com/viciod/case-vicio-ia/blob/main/case-ia-classificacao-de-topicos.pdf .

As regras de normalização são código explícito. O vocabulário TF-IDF é ajustado apenas no catálogo; os pesos supervisionados e a calibração usam apenas os rótulos de treino autorizados por cada fold. Não há exceções por ID, gabaritos externos nem votos de um assistente. A escrita do código foi assistida por IA; as previsões são calculadas pelo programa.

Custo de API de classificação executada: US$ 0. Não há medição de tokens da conversa nem rateio da assinatura. Não se estima custo ou tempo de 50 mil questões a partir do tempo total deste experimento.
