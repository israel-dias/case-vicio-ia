# Case Vício IA — classificação assistida de tópicos

Proposta de entrega: **359 decisões, 229 publicar, 126 revisar e 4 fora**.
Cobertura: **63,7883%**. Precisão jurídica **não medida**; previsão subjetiva
registrada antes da avaliação: 96%, cenário de sensibilidade 85%-99%.
Não há gabarito independente nem garantia de atingir 95%.

## Executar a reprodução

Python 3.12 recomendado. Somente biblioteca padrão; sem chave, dependências,
servidor ou chamadas pagas. Execute dentro desta pasta, onde está este README:

```bash
python -m unittest discover -s tests -v
python importar_todos_v3.py
python finalizar_case.py --saida entrega_reproduzida
```

O importador verifica as 34 execuções já incluídas, sem sobrescrevê-las. Se
ausentes, cria seus registros a partir das respostas salvas, com horário real
da importação. Não executa nova inferência. A última etapa produz
`entrega_reproduzida/publicacao.csv`, `previsao.txt`, `resumo_entrega.json` e
`intervencoes_registradas.json`. O CSV e a previsão devem corresponder aos
arquivos de referência na raiz. Para repetir, use outra pasta vazia de saída.

Os arquivos da raiz são a versão consolidada para revisão do candidato.
Não foram publicados no GitHub nem enviados à recrutadora pelo assistente.

## Como a classificação aconteceu

1. Python preservou os anexos, limpou a apresentação do texto e validou a árvore.
2. Um piloto de vinte questões foi analisado duas vezes: v1 nesta conversa com
   contexto prévio; v2 em outra conversa pelo candidato, com modelo não registrado.
3. As divergências foram inspecionadas e a orientação da recrutadora foi registrada.
4. Critérios v3 foram usados nas 339 questões restantes, em 34 lotes.
   As classificações foram produzidas pelo assistente nesta conversa existente,
   com leitura das questões, inspeção do catálogo e referências pontuais.
5. As anotações explícitas foram formatadas em JSON, importadas e verificadas.
   A formatação por Python não é chamada a modelo nem classificação por palavras-chave.
6. As vinte decisões do piloto e um ajuste final foram consolidados em arquivos
   próprios, com antes/depois registrados. A Q0298 passou de fora para revisar
   por dúvida entre o escopo do CDC e da Lei 8.137, evitando exclusão definitiva.
7. O exportador reúne exatamente 359 IDs, exige temas ativos, proíbe publicar
   em raízes de disciplina e produz o CSV e a autoavaliação.

**Limite de reprodução:** respostas salvas tornam o pós-processamento reproduzível.
Gerar respostas novas requer interação com um modelo. O projeto atual não é um
classificador autônomo por API nem treina um modelo supervisionado.

## Modelos, custo e tempo

Foram usados o ChatGPT/assistente da conversa e outra conversa do candidato.
Os identificadores exatos não foram confirmados. Não atribuímos essas execuções
a nomes de modelos da API. Os prompts salvos são referência das regras/dados;
não representam a transcrição integral do contexto da conversa existente.

Custo executado de API de classificação: US$ 0. Tokens internos medidos: não
disponíveis. A assinatura existente não foi rateada. Tempos de importação são
horários de registro, não latências de inferência. O tempo total de trabalho
humano/chat não foi instrumentado; não há benchmark de inferência.

```bash
python simular_custos.py --volume 50000
```

Essa simulação de produção usa preços e hipóteses separados das execuções reais.
Não gera cobrança. Consulte `docs/CUSTOS_PRODUCAO.json` e o relatório.

## Arquivos da entrega

| Arquivo | Função |
|---|---|
| `publicacao.csv` | Uma decisão por questão, no formato do case |
| `previsao.txt` | Previsão subjetiva e cobertura exata, com pressupostos |
| `relatorio.md` | Método, diagnóstico, produção e memo para o professor |
| `intervencoes_registradas.json` | Antes/depois da consolidação assistida |
| `resumo_entrega.json` | Contagens, proveniência por ID e hashes |
| `docs/APRESENTAR.md` | Explicação didática e limites para a apresentação |
| `evidencias_assistente` | Anotações reais, decisões do piloto e ajuste final |
| `execucoes/v3` | Respostas originais, prompts de referência e registros |

Os valores de confiança são julgamentos subjetivos não calibrados. Em `fora`,
CSV usa confiança 0 e tema vazio: 0 indica ausência de tema central, não certeza
da exclusão. O JSON interno conserva confiança null para esse caso.
Os IDs do catálogo e grafias recebidas foram preservados.

## Regenerar preparação, lotes e respostas salvas

O pacote já inclui os arquivos. Use destinos novos para preservar as versões:

```bash
python -m vicio_ia preparar --saida dados/processados_regenerados
python gerar_lotes_v3.py --saida lotes_v3_regenerados
python gerar_respostas_salvas.py --saida respostas_v3_regeneradas
```

O último comando apenas formata as 329 anotações explícitas do assistente dos
lotes 002–034. O lote 001 tem sua resposta original em `respostas_v3/lote_001.json`.
Não apresenta tabela fixa como classificador que generalize para dados novos.
Para nova inferência, utilize cada prompt e registre contexto/modelo/resposta.
Não misture esse novo experimento com as respostas de referência.

## Publicar o repositório

Depois da conferência do candidato, esta pasta pode ser a raiz do repositório
público solicitado. Inclua os arquivos da entrega, código, dados do case e
evidências necessárias à reprodução. Não inclua ambiente virtual, credenciais
ou conversas pessoais. O envio à recrutadora é o link desse repositório.
O arquivo `docs/DECISOES.md` registra as decisões iniciais; as posteriores estão
em `docs/CRITERIOS_V3.md`, no relatório e no registro de intervenções.
