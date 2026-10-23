# Conferir os sinais de confiança

Este pacote contém a v3 preservada e uma auditoria adicional. Comece por `PARECER_CONFIANCA.md`. A auditoria é um experimento; o `publicacao.csv` e o `previsao.txt` da raiz continuam sendo os da v3.

Python 3.12. Use as mesmas dependências da v3:

```bash
python3 -m pip install --timeout 180 --retries 10 -r requirements-v2.txt
python3 -m unittest discover -s auditoria_confianca_v4/tests -v
```

Para repetir a auditoria, escolha uma pasta de saída que ainda não exista:

```bash
python3 auditar_confianca_v4.py --saida experimentos/auditoria_confianca_reproduzida
```

O comando não chama API, não cria respostas de prova e não altera a entrega. Os 100 rótulos entram somente nos grupos apropriados de treinamento e avaliação. Depois de congelar as candidatas, o comando simula as regras nas 559 sem consultar seus rótulos. Essas simulações não medem precisão real.

Os resultados originais estão em `experimentos/auditoria_confianca_v4_002`. O número 002 identifica a execução concluída: a primeira tentativa foi interrompida durante o primeiro grupo por lentidão. Foi otimizado o cálculo repetido das massas das classes, preservando as equações, hipóteses e variantes. Um teste verifica equivalência numérica com o ajuste original, e o experimento verifica que o controle reproduz as probabilidades e decisões da v3.

Para conferir que a entrega v3 permanece reproduzível:

```bash
python3 finalizar_melhorias_v3.py --saida entrega_v3_conferida
cmp publicacao.csv entrega_v3_conferida/publicacao.csv
cmp previsao.txt entrega_v3_conferida/previsao.txt
```

A aprovação dos testes confirma contratos do código e reprodução. Não confirma o acerto jurídico das 559 questões.
