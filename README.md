# Case Vício IA — classificação de tópicos com auditoria assistida

Versão auditada em 16/10/2026: **359 questões, 329 publicar, 25 revisar e 5 fora**.
Cobertura: **91,6435%**. Precisão real **não medida**. Previsão subjetiva: **96%**,
com cenário de sensibilidade **85%–99%**, sem garantia de atingir a meta de 95%.

## Rodar a reprodução

Python 3.12 recomendado. O pipeline usa apenas biblioteca padrão, sem chave de API.
Execute dentro desta pasta:

```bash
python -m unittest discover -s tests -v
python importar_todos_v3.py
python finalizar_case.py --saida entrega_reproduzida_v4
```

Use uma pasta de saída nova a cada execução. O importador verifica os 34 lotes v3;
o exportador verifica dados, respostas, histórico e auditoria v4, aplica o reexame
e gera `publicacao.csv`, `previsao.txt`, `resumo_entrega.json` e
`intervencoes_registradas.json`. CSV e previsão devem corresponder aos da raiz.
A v3 original está preservada em `historico/v3`.

**Reproduzir os arquivos salvos não executa nova inferência de IA.** É possível
reproduzir exatamente a consolidação, sem prometer a mesma resposta em uma nova
conversa. Não há classificador autônomo, modelo treinado ou API de inferência neste
protótipo. O julgamento semântico foi produzido por interação com o assistente e
está registrado por questão.

## O que mudou na auditoria

A v3 tinha 229 publicações, 126 revisões e 4 exclusões. Israel questionou a hipótese
de que alternativas de assuntos distintos impediam identificar um núcleo. O prompt
já pedia ler alternativas: a falha também foi de aplicação do critério pelo
assistente, que não investigou suficientemente a resolução antes de se abster.

O reexame leu novamente **todos os 359 enunciados, comandos e conjuntos de
alternativas**, incluindo publicados e excluídos. Identificou o conhecimento da
resolução, separou contexto de cobrança e tratou assertivas independentes como
conteúdos potencialmente distintos. O resultado tem:

- 103 decisões de revisar para publicar;
- 3 de publicar para revisar, por pendências concretas;
- 1 de revisar para fora: Lei 8.137 não foi equiparada ao título restrito a CDC;
- 79 mudanças de tema central e 64 de extras; algumas são refinamentos dentro do
  mesmo ramo e **não significam erros demonstrados da versão anterior**;
- 79 questões com extras sustentados na análise individual.

Uma resposta certa ajuda a identificar o núcleo, mas não certifica um ID do
catálogo. Nos itens com I/II/III, também é necessário julgar as proposições falsas.
Não se adicionam automaticamente todos os nomes encontrados nos distratores. Um filho do tema central pode ser extra quando representa um conhecimento efetivamente exigido; a justificativa individual está registrada para permitir consulta por subtema. Não se presume que classificar no pai faça o item aparecer na busca pelo filho.

A Q0097 foi liberada após discussão com Israel: central 4705 e extra 5067.
A justificativa e a decisão anterior estão em `docs/REVISAO_Q0097.md` e
`historico/v4_antes_Q0097`. Esta mudança não mede aumento de precisão.

Após a Q0097, as 57 revisões foram relidas: **32 liberações adicionais e 25 revisões mantidas**. As escolhas de central e extras e cada pendência remanescente estão em `docs/REAVALIACAO_57_REVISOES.md` e `auditoria_v4/reavaliacao_57.json`; a etapa anterior está em `historico/v4_antes_reavaliacao_57`. A existência de dois temas não exige revisão automática. A precisão real continua não medida.

## Evidência e limites

Foram registradas buscas iniciais para os 359 IDs. Resultados de busca e
correspondências automáticas com PDFs são **pistas**, não gabaritos confirmados.
O registro final distingue:

| Estado da resposta | Questões |
|---|---:|
| Gabarito oficial definitivo confirmado | 2 |
| Gabarito oficial preliminar confirmado | 1 |
| Resposta formulada pelo assistente, sem gabarito oficial confirmado | 326 |
| Resposta não confirmada | 30 |

A consulta pontual a legislação e precedentes é documentada separadamente.
Não se afirma que todos os precedentes indicados foram lidos ou que todos os
fundamentos foram validados. Uma questão pode ter tema inequívoco sem letra
confirmada; quando a dúvida altera o enquadramento ou compromete o conteúdo,
a pendência permanece explícita. O reexame pelo mesmo assistente **não é auditoria
jurídica independente** e não mede aumento de precisão. A empresa possui os
rótulos temáticos usados na avaliação.

## Onde conferir

| Arquivo | Conteúdo |
|---|---|
| `publicacao.csv` | Entrega no formato do case, 359 linhas de dados |
| `previsao.txt` | Previsão subjetiva, intervalos e cobertura |
| `relatorio.md` | Método, diagnóstico, produção e memo para o professor |
| `auditoria_v4/caderno_auditoria.md` | Cada questão completa, resposta/pendência, antes/depois e raciocínio |
| `auditoria_v4/reexame_359.json` | Registro estruturado usado pelo exportador |
| `auditoria_v4/resumo_auditoria.json` | Contagens e transições, sem precisão inventada |
| `auditoria_v4/PROTOCOLO_FINAL.md` | Critérios de tema central, extras e decisão |
| `auditoria_v4/fontes` | Gabaritos confirmados, consultas dirigidas e pistas de pesquisa |
| `docs/INCIDENTE_AUDITORIA_001.md` | Intervenção do candidato e falha identificada |
| `docs/APRESENTAR.md` | Explicação didática do processo e seus limites |
| `historico/v3` | CSV, previsão e documentos da versão anterior |
| `historico/pesquisa_inicial_v4` | Rascunhos exploratórios anteriores ao reexame completo |

Os lotes, prompts e respostas v1/v2/v3 permanecem como histórico. O prompt de
referência não é transcrição integral da conversa. A auditoria v4 foi conduzida
nesta conversa existente, lendo as questões em blocos de trinta; esses blocos
organizam a inspeção, sem representar chamadas isoladas a API. As decisões v4 são
anotações explícitas, não saídas de um algoritmo que generalize para dados novos.

## Fontes, preparação e anotações

Scripts opcionais de pesquisa exigem internet e, para PDFs, Poppler (`pdftotext`).
Eles não participam da reprodução obrigatória dos arquivos de entrega:

```bash
python auditoria_v4/scripts/consultar_normas.py
python auditoria_v4/scripts/baixar_provas_publicas.py --help
```

As fontes podem mudar ou ficar indisponíveis. Os índices preservam URLs e hashes
das obtenções realizadas; os caches de PDFs não são distribuídos. O texto legal
atual não substitui o contexto histórico da prova.

Para editar o reexame: registrar novas decisões nos arquivos de
`auditoria_v4/decisoes`, mantendo o histórico; executar
`python auditoria_v4/scripts/gerar_auditoria.py`; exportar para pasta nova e
conferir as diferenças. Esse script **formata as anotações salvas**, sem inferência.
A atualização de hashes registra uma nova versão, não transforma hipótese em
verdade. O módulo rejeita dados alterados, IDs ausentes, temas inativos/raiz,
IDs repetidos, extras hierarquicamente inadequados ou sem justificativa independente e antes/depois incompatíveis.

Os comandos históricos de preparação e formatação continuam disponíveis:

```bash
python -m vicio_ia preparar --saida dados/processados_regenerados
python gerar_lotes_v3.py --saida lotes_v3_regenerados
python gerar_respostas_salvas.py --saida respostas_v3_regeneradas
```

## Modelos, custo, tempo e previsão

ChatGPT/assistente nesta conversa e uma conversa separada do candidato no piloto.
Identificadores exatos não confirmados. Custo executado de API de classificação:
**US$ 0**. Assinatura existente não rateada; tokens internos não medidos. Tempos de
importação não são latências de inferência e o tempo total não foi instrumentado.

```bash
python simular_custos.py --volume 50000
```

A simulação usa o cenário de preços e tokens registrado em
`docs/CUSTOS_PRODUCAO.json`, separado dos custos reais. Não cobra nem executa API.
Confiança do CSV é julgamento não calibrado sobre o central; em fora, zero é
convenção de ausência de tema. Aprovação de testes não verifica acerto jurídico.

A pasta é uma proposta pronta para a conferência do candidato antes da publicação.
Não foi criada publicação no GitHub nem enviado e-mail pelo assistente.
