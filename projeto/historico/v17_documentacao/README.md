# Case Vício IA — experimento de isolamento V17

**O experimento não superou o controle anterior.** A V16 permanece como referência experimental com 394 publicadas em 559 (70,48%), sem precisão real medida nessas 559. Os novos comparadores não foram promovidos a entrega.

A V17 mantém a recuperação V15 e seus cinco candidatos e compara: primeiro candidato, reordenação pelos atributos V11 e reordenação pelos atributos V15. Não usa o assistente para escolher ou validar temas.

## Conferir a implementação

Python 3.12. As dependências são as mesmas da rodada anterior. Se necessário, instale `requisitos_v17.txt`.

```bash
python3 -m unittest discover -s isolamento_v17/tests -v
python3 classificar_isolamento_v17.py --saida conferencia_v17
```

Use uma pasta de saída nova. A reprodução aplica modelos estatísticos congelados, sem LLM, rótulos, rede ou treino supervisionado. O índice TF-IDF é reconstruído apenas com o catálogo versionado.

## Resultados

| Opção | Tema aceito /100 | Publicadas nas referências | Corretas | Publicadas /559 |
|---|---:|---:|---:|---:|
| Controle anterior V16 | 70 | 50 | 48 | 394 |
| Primeiro candidato V15 | 72 | 24 | 23 | 216 |
| Reordenar com atributos V11 | 69 | 3 | 2 | 0 |
| Reordenar com atributos V15 | 60 | 10 | 8 | 0 |

As 100 referências são desenvolvimento já exposto; não constituem teste externo cego e não entram nas contagens das 559. A precisão de 48/50 do controle nas referências não é a precisão das 394 publicações no alvo.

**A união que aumentaria a cobertura para 402/559 foi rejeitada:** nas referências ficou em 48/51 (94,12%), abaixo da meta empírica de 95%. Ela não é política ativa.

Leia [LEITURA_V17.md](LEITURA_V17.md) para o método, perdas e correções, motivos de revisão, protocolo, comandos de reprodução do estudo e referências. A antiga documentação está em [historico/v16_documentacao/README.md](historico/v16_documentacao/README.md).

Os arquivos `publicacao.csv` e `previsao.txt` da raiz são controles históricos preservados, não o resultado desta V17 nem uma entrega atualizada para enviar. Nenhum push ou e-mail foi realizado por esta atualização.

## Pesquisa adicional sobre contexto

[PESQUISA_CONTEXTO_V18.md](PESQUISA_CONTEXTO_V18.md) reúne alternativas fundamentadas para uma próxima rodada e um diagnóstico reproduzível dos enunciados longos. É pesquisa e análise das referências; essas propostas ainda não alteram a inferência.
