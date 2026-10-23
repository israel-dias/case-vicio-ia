# Case Vício IA — experimento de melhorias v3

Esta cópia reúne uma candidata experimental com mapa de referências normativas, atributos textuais adicionais e comparação entre candidatos próximos. A classificação usa modelos clássicos congelados, sem chamar LLM, rede ou ler rótulos durante a inferência.

**Resultado nas 559 questões avaliadas pela empresa:** 175 publicar, 384 revisar, 0 fora; cobertura **31,3059%**. V2: 152 publicar e cobertura 27,1914%. A previsão passou de 90,3404% para **92,8992%**, ainda abaixo da meta. A precisão real dessas questões é desconhecida.

A variante escolhida no ajuste final foi `referencias_fixa`: incorpora os atributos novos e mantém o tema da busca. Na CV conhecida, publicou 23/100, com 22 acertos (95,6522%). A seleção interna entre variantes publicou 26/100 com 25 acertos (96,1538%); essa linha representa o procedimento de seleção por fold, não o resultado isolado da variante final. Os rótulos já foram vistos: não é novo teste cego.

## Reproduzir a candidata congelada

Python 3.12. Dependências iguais às da v2, em `requirements-v2.txt`:

```bash
python3 -m pip install --timeout 180 --retries 10 -r requirements-v2.txt
python3 -m unittest discover -s melhorias_v3/tests -v
python3 finalizar_melhorias_v3.py --saida entrega_local_v3
cmp publicacao.csv entrega_local_v3/publicacao.csv
cmp previsao.txt entrega_local_v3/previsao.txt
```

Use uma pasta de saída nova. A finalização não treina nem escolhe outro corte. Ela aplica o modelo salvo, calcula a previsão excluindo os 100 IDs oficiais e compara com a entrega v2 preservada. A leitura da folha-verdade nesta consolidação serve para conferir os anexos e excluir IDs da previsão, não para decidir temas.

Para classificar um JSONL sem consultar a folha-verdade:

```bash
python3 classificar_melhorias_v3.py --modelo artefatos/melhorias_v3 --questoes dados/anexos/questoes.jsonl --saida classificacao_local_v3
```

O modelo pode receber novos IDs e textos com os mesmos campos. O ID apenas identifica a saída. O sistema não resolve a alternativa correta. Campos sem conteúdo ou ausência de candidato exigem triagem da importação.

## Conferir o trabalho

| Caminho | Conteúdo |
|---|---|
| `publicacao.csv`, `previsao.txt` | Candidata v3, idêntica aos arquivos da entrega experimental |
| `entrega_experimental_v3/` | CSV, previsão, fila de revisão, rastreabilidade, resumo e comparação com a v2 |
| `experimentos/melhorias_v3_001/LEITURA.md` | Comparação das variantes na mesma CV da v2 |
| `experimentos/melhorias_v3_001/modelos_folds/` | Parâmetros e decisões salvos antes das previsões externas |
| `artefatos/melhorias_v3/` | Modelos e calibradores clássicos, políticas e dados preparados |
| `melhorias_v3/dados/referencias_normativas_v1.json` | 11 códigos/normas, 50 intervalos documentais propostos, fontes e limites |
| `analises/melhorias_v3/CASOS_DAS_559.md` | Questões completas selecionadas automaticamente entre as mudanças de decisão |
| `relatorio.md` | Explicação do experimento, limites e memo para o professor |
| `docs/controle_v2/` e `entrega_etapa2_v2/` | Documentos e resultados do controle anterior |

Os alertas da fila são sinais computados, sem parecer jurídico. Uma referência a lei não prova o tema cobrado. Os intervalos documentais são propostas de organização; não receberam validação jurídica independente. CP e CPP e seus artigos são tratados separadamente. Homônimos podem compartilhar evidência, mas seus IDs não são fundidos nem tornam ramos equivalentes.

## Refazer o experimento ou o treino

Esses passos são opcionais; não fazem parte da reprodução obrigatória do CSV:

```bash
python3 experimentar_melhorias_v3.py --saida experimentos/melhorias_v3_local
python3 treinar_melhorias_v3.py --experimento experimentos/melhorias_v3_local --saida artefatos/melhorias_v3_local
```

O experimento mantém cinco folds externos e quatro internos, agrupando duplicatas normalizadas. Só os 100 itens oficiais chegam ao ajuste supervisionado. As regras finais requerem suporte interno mínimo de dez e pelo menos 95% de precisão empírica. Esses requisitos não são uma comprovação estatística. A confiança é calibrada, não similaridade textual.

O estudo compara controle v2, referências com tema fixo, candidatos próximos e ranking híbrido. A escolha final maximiza suporte sob a meta empírica nos sinais OOF; empates consideram acerto top1 e favorecem o controle. Escolher um método após ver resultados conhecidos continua sendo desenvolvimento. A qualidade nas 300 questões recentes ainda não foi medida.

Os 17 testes novos e os 104 testes originais passaram. Testam referências CP/CPP, ordinais e anos, ausência de regra por ID, preservação de negação, integridade, inferência sem rótulos/rede/treino e reprodução. Não verificam o acerto jurídico das 559.

API de classificação: US$ 0. Mesmas dependências da v2; não é necessário comprar API ou instalar outro modelo. Tokens internos e tempo humano não foram instrumentados. Assinatura existente não rateada.
