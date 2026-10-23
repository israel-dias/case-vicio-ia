# Case Vício IA - etapa complementar

Israel Dias. Sistema próprio de classificação com busca lexical, regras contextuais e modelos clássicos congelados. **A decisão roda sem modelo de linguagem, encoder, rede ou leitura de rótulos.**

| Recorte | Questões | Publicar | Revisar | Fora | Cobertura |
|---|---:|---:|---:|---:|---:|
| Entrega completa | 659 | 454 | 205 | 0 | 68.89% |
| Fora da folha-verdade | 559 | 387 | 172 | 0 | 69.23% |
| Concursos recentes | 300 | 214 | 86 | 0 | 71.33% |

Nas referências expostas, a composição selecionada publicou **54 e acertou 54**, com 78/100 sugestões aceitas. O controle tinha 50 corretas em 52 publicadas. **A precisão real das 559 é desconhecida.** As 100 referências foram vistas e reutilizadas; a composição de controles históricos não é teste independente nem calibração global comprovada. Não há garantia de mínimo de 95% nas avaliadas.

## Arquivos de entrega

- `publicacao.csv`: 659 linhas, uma por questão, no formato do LEIA-ME.
- `previsao.txt`: previsão e intervalos somente nas 559, com método e limites.
- `relatorio.pdf`: quatro páginas, incluindo memo de uma página para o professor.
- `relatorio.md`: conteúdo textual do relatório.
- `gerar_entrega.py`: comando principal de regeneração, com conferência de formato.
- `conferir_entrega.py`: conferência rápida dos arquivos salvos.
- `rastreabilidade.jsonl`: rota, conflito ou veto e probabilidades efetivamente usadas.
- `projeto/`: código, anexos, artefatos, estudos e histórico. Os arquivos desta raiz são a entrega atual; os relatórios e CSVs dentro de `projeto` documentam versões anteriores.

## Instalar e conferir rapidamente

Python 3.12 recomendado, com venv própria:

```bash
python3 -m pip install -r requirements.txt
python3 conferir_entrega.py
python3 -m unittest discover -s projeto/cobranca_v24/tests -v
```

## Regenerar do zero

```bash
python3 gerar_entrega.py --saida entrega_reproduzida
cmp publicacao.csv entrega_reproduzida/publicacao.csv
cmp previsao.txt entrega_reproduzida/previsao.txt
```

Use uma pasta de saída nova. O comando aplica modelos clássicos congelados ao texto dos anexos. Não usa tabelas de respostas por ID, LLM, gabarito de alternativa, embeddings ou API na decisão V24. TF-IDF é reconstruído somente do catálogo versionado. Os IDs das 100 referências são usados apenas para delimitar os recortes estatísticos; seus rótulos não são lidos na inferência.

Os checkpoints guardam resultados já calculados da mesma execução. A retomada só aceita entrada, código e artefatos compatíveis. O CSV final padroniza a confiança em oito casas e traduz os motivos técnicos para mensagens curtas, sem mudar tema ou decisão. Os testes de software e a prova de inferência não medem acerto jurídico.

## Critérios e principais decisões

1. Sem comando específico, procurar a cobrança nas últimas unidades do enunciado. A prioridade exige expressão temática contextualizada: `Penal` sozinho identifica uma disciplina, não um tópico válido.
2. Instrução genérica não compete com o conteúdo. Um comando informativo sem identificador permanece como apoio. Retomadas, como “referida espécie”, recuperam o objeto no enunciado.
3. Artigo ou lei isolados não decidem o tema. Citações convergentes precisam de ato compatível; norma usada como exemplo não equivale ao conhecimento cobrado.
4. Todas as proposições I/II e V/F são preservadas. Alternativas C/E não fornecem evidência temática. Não há corte por tamanho nem confiança mínima imposta por palavra.
5. Publicações antigas são reavaliadas diante de conflito de cobrança ou crime apenas contextual. Isso retirou duas publicações erradas nas referências; também suspendeu uma correta e acrescentou cinco corretas.
6. A avaliação mantém a régua oficial: central, extras e ancestrais/descendentes. Irmãos e homônimos em ramos distintos não viram equivalentes por semelhança ou por opinião. Possíveis divergências de escopo são documentadas para discussão.

Os padrões estão em `projeto/cobranca_v24/expressoes.json`; a lógica, em `texto.py` e `modelo.py`. São propostas gerais derivadas do catálogo e do diagnóstico conhecido, não exceções por ID. Os escopos enriquecidos não têm homologação jurídica independente.

## Experimentos, treino e modelos

A versão final é `projeto/experimentos/cobranca_v24_004`. Modelos, política e escolha foram congelados antes da aplicação V24 às 559. Os cinco folds externos e quatro internos ajustam/calibram a rota nova sem o rótulo do fold avaliado; a composição usa controles OOF históricos e continua desenvolvimento adaptativo. A tentativa 003 falhou numa dependência de leitura e não foi usada; o código foi corrigido e testado na execução 004. Nenhuma tentativa incompleta é a entrega atual.

Para refazer o estudo das referências, dentro de `projeto`:

```bash
python3 testar_cobranca_v24.py --saida experimentos/cobranca_reproduzida
```

Este comando lê rótulos para treino/avaliação e é diferente do runtime. Os experimentos anteriores, inclusive os que pioraram, permanecem documentados. E5 foi uma preparação opcional testada e não foi promovido a esta decisão. O assistente ajudou no desenvolvimento e em propostas versionadas de termos; o identificador exato dos modelos de conversa históricos não foi confirmado. Não escolhe nem valida os temas avaliados em tempo de execução.

## Custo, tempo e produção

Custo executado de API de classificação: **US$ 0**. Assinatura existente não rateada; tokens de conversa não medidos. O tempo da execução está em `resumo_execucao_observada.json`, dependente desta máquina. O relatório separa custo de CPU, revisão humana e um cenário hipotético para 50 mil questões; não apresenta cenário como orçamento ou SLA.

A previsão global usa frequência de acerto das publicadas no desenvolvimento com suavização Beta(1,1), e não a média das confianças individuais. A faixa é de sensibilidade após desenvolvimento adaptativo, não intervalo de confiança válido para as 559. A cobertura é conhecida para este lote, sem extrapolação automática para novas semanas.

## Publicar o repositório

Copie o conteúdo desta pasta para a raiz do repositório já clonado e registre a nova etapa em um commit. Mantenha os anexos, artefatos e a pasta `projeto` versionados para permitir regeneração. O assistente não realizou push nem enviou e-mail.

## Primeira etapa

A entrega original de 359 questões, incluindo o visor, está preservada em [historico/etapa1](historico/etapa1/README.md). Os arquivos na raiz representam a etapa complementar atual.
