# Vício IA — experimento V12: novos usos de palavra_completo

Esta pasta contém um experimento separado. A entrega histórica e todos os modelos V11 foram preservados. `publicacao.csv` e `previsao.txt` na raiz são controles históricos V5: não são a entrega V12. Nenhuma versão foi publicada ou enviada à recrutadora por este pacote.

Leia `RELATORIO_PALAVRA_V12.md` para resultados, exemplos, perdas e limitações. O corte de publicação em 50% NÃO faz parte desta rodada.

## O que está sendo comparado

O controle é a candidata V11 `sem_apoio_duplo`, com as publicações V9 preservadas. Todas as variantes mantêm `palavra_completo` e o mesmo ranking V8/identificadores V9. Portanto, o experimento mede confiança e publicação/revisão, não melhora de descoberta de temas.

1. `controle_v11`: os mesmos 39 atributos e ajuste anterior.
2. `palavra_relativa`: acrescenta a diferença entre a semelhança global do tema e a maior semelhança de outra família; também usa essa diferença dividida pelo maior dos dois valores. Pode ser negativa. Não é uma regra de veto nem torna temas equivalentes.
3. `palavra_foco`: compara o foco já extraído pela V7 com os documentos lexicais do catálogo original; acrescenta o contraste foco menos texto completo. Sem foco utilizável, ambas as novas colunas são zero. O foco é uma heurística gramatical, não uma resolução da questão.
4. `alternativas_condicionais`: acrescenta duas interações: semelhança do enunciado quando as alternativas não têm conteúdo temático e semelhança das alternativas quando elas têm conteúdo temático. Certo/Errado, números e combinações de assertivas não oferecem temas por si. O texto original continua disponível nos atributos antigos.
5. `regularizacao_03`: mantém os 39 atributos e muda somente a regularização da regressão logística, de C=1 para C=0,3.
6. `combinado`: junta as seis novas colunas e C=0,3.

Não se força coeficiente positivo nem se soma confiança manualmente. Duas políticas são avaliadas: usar a nova versão com o controle V9 (`substituir_com_v9`) ou preservar todas as publicações V11 (`preservar_v11`). Preservar inclui eventuais erros antigos; não consulta a folha-verdade para escolher a saída.

## Reproduzir

Python 3.12 e as dependências já utilizadas:

```bash
python3 -m pip install --timeout 180 --retries 10 -r experimento_folha_v2/requirements.txt
python3 -m unittest discover -s experimento_palavra_v12/tests -v
```

O experimento e os modelos congelados estão incluídos. Para repetir o treinamento e a avaliação completa, use uma pasta nova:

```bash
python3 testar_palavra_v12.py --saida experimentos/palavra_v12_local
python3 congelar_palavra_v12.py --experimento experimentos/palavra_v12_local
```

Inferência com os modelos incluídos, sem folha-verdade, internet ou nova chamada a modelo de linguagem:

```bash
python3 classificar_palavra_v12.py --variante palavra_relativa --politica preservar_v11 --saida inferencia_palavra_v12_local
```

Escolher a variante nesse comando é uma comparação experimental, não uma recomendação de promover a entrega. O relatório informa quais variantes melhoraram ou pioraram. `--experimento experimentos/palavra_v12_local` usa sua nova reprodução; `--questoes caminho/novas.jsonl` aceita outras questões. O padrão lê as 659; os resultados das 559 sem rótulo são apresentados separadamente no relatório. As decisões nas 100 usadas no ajuste final não são uma avaliação independente.

## Evidências

- `experimentos/palavra_v12_001/protocolo_previo.json`: hipóteses, grupos, códigos e hashes fixados antes de avaliar.
- `experimentos/palavra_v12_001/folds`: modelos, cortes, calibradores e listas de treino/avaliação dos cinco folds externos.
- `experimentos/palavra_v12_001/avaliacao_100.csv`: resultados fora do treino de cada fold.
- `experimentos/palavra_v12_001/mudancas_100.json`: questões completas, referência, antes/depois e acertos/erros.
- `experimentos/palavra_v12_001/simulacao_559.csv`: decisões sem rótulos disponíveis; precisão real desconhecida.
- `experimentos/palavra_v12_001/modelos_finais.json`: parâmetros congelados, sem respostas por ID.
- `experimentos/palavra_v12_001/manifesto_inferencia.json`: verificação de código e artefatos.

Os 100 rótulos já foram vistos e usados repetidamente no desenvolvimento. Mesmos cinco folds externos e quatro internos; em cada ajuste, os rótulos do grupo avaliado não participam do treino, calibração ou escolha do corte daquele fold. Isso não apaga a exposição anterior nem transforma o estudo em teste externo cego. Não se escolhe uma variante pelo volume publicado nas 559, que não têm rótulos disponíveis.

Uma tentativa inicial foi interrompida pela checagem de reprodução do controle: a cópia da matriz em outra ordem de memória alterou ligeiramente a convergência numérica do solver. O controle passou a usar precisamente o caminho legado de treino e escore. A tentativa e o código anterior estão preservados em `historico/v12_tentativa_reproducao_controle`; não são resultados válidos para comparar as variantes.
