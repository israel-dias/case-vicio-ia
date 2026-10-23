# Teste completo nas 559 — complemento da V15

Esta execução excluiu os 100 IDs de referência. São 259 questões antigas fora da referência e 300 recentes. O modelo permanece o já ajustado/calibrado; não houve treino, consulta à folha-verdade ou rede nesta execução. As 12 configurações congeladas foram executadas e reproduzidas exatamente.

**Resultado principal:** 392 publicar, 167 revisar, 0 fora; cobertura 70,13%. Nas 300 recentes: 218 publicar e 82 revisar. Precisão real desconhecida. A média das confianças das publicadas é 88,59%, apenas descritiva, e não comprova precisão de 95%.

Comece por `experimentos/diagnostico_559_v15_001/LEITURA.md`. Os dez exemplos completos estão em `CASOS_PARA_CONFERIR.md` na mesma pasta. A saída inclui uma linha por questão, diagnóstico estruturado de todas as 559 e as sete candidatas concordantes que **não foram liberadas automaticamente**.

O arquivo ZIP é um complemento do pacote **case-vicio-ia-contexto-v15.zip**. Extraia-o dentro da pasta `case-vicio-ia-etapa2-contexto-v15-experimental`, preservando as subpastas. Não é um projeto independente: usa os modelos congelados e as dependências já incluídos na V15.

Para conferir os testes novos:

```bash
python3 -m unittest discover -s testes_diagnostico_559 -v
```

Para repetir a inferência completa, use uma pasta de saída nova:

```bash
python3 diagnosticar_559_v15.py --saida experimentos/diagnostico_559_v15_local
python3 resumir_559_v15.py --saida experimentos/diagnostico_559_v15_local
```

O primeiro comando valida que a entrada contém exatamente os 559 IDs esperados e bloqueia leitura de rótulos, treino, recalibração, escolha de limiares e rede. Os cinco folds usados apenas para identificar os 100 IDs excluídos têm tamanhos 20/20/20/21/19, preservados como no original; não houve nova divisão. O segundo comando organiza os registros salvos, sem classificar ou mudar decisões.

Não substitui `publicacao.csv` ou `previsao.txt`. A entrega oficial do case continua exigindo 659 linhas; a exclusão dos 100 aqui vale para o diagnóstico e para a avaliação. Sem os rótulos das 559, este teste mede comportamento, integridade e cobertura, não acerto jurídico.
