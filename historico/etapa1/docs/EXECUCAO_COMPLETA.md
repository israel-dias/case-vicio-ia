> Documento histórico de etapa anterior. Para a versão auditada v4, siga o README da raiz.

# Proveniência e sequência da versão consolidada

## O que foi executado

Os anexos originais foram preparados por Python. As respostas do piloto v1 e v2
foram obtidas em conversas, preservadas como arquivos e comparadas. A v2 foi
fornecida pelo candidato; a informação de conversa nova é a declaração dele,
não uma propriedade demonstrável pelos bytes do JSON.

Foi preservado o registro v1 disponível nesta área de trabalho. O registro v2
incluído foi criado nesta cópia com o JSON recebido, identificando essa origem;
seu horário não é o da execução original no computador do candidato. A comparação
JSON enviada pelo candidato também foi preservada para distinguir as proveniências.

O lote v3 001 foi respondido anteriormente nesta conversa e importado pelo
candidato, conforme a saída de terminal que ele compartilhou. Para a versão
completa, o assistente leu e classificou as outras 329 questões nesta mesma
conversa. Não foi feita chamada à API da OpenAI pelo código Python, nem foram
criadas 33 conversas independentes. O contexto prévio pode influenciar todas
essas decisões.

As primeiras trinta dessas 329 anotações estão em
`evidencias_assistente/anotacoes_assistente.jsonl`; as outras 299 estão em
`evidencias_assistente/anotacoes_compactas_assistente.jsonl`. O formato compacto
é explicitamente convertido por `gerar_respostas_salvas.py`. Os comentários do
script documentam os campos e valores padrão. Ele formata julgamentos já feitos;
não deduz classificações, não simula respostas de um modelo e não atende dados
novos. A resposta original do lote 001 é preservada separadamente.

O importador em lote executou 34 importações nesta cópia do projeto. Cada registro
tem o horário da sua própria importação e o modelo informado como não confirmado.
Não são os registros originais produzidos no computador do candidato, tampouco
medidas de tempo de inferência. A resposta bruta, os dados, o prompt de referência
e seus hashes permitem conferir a origem dos registros.

A expressão “Inferência não executada” no manifesto descreve a etapa de geração
do lote, anterior às respostas; não descreve o estado posterior da importação.

As vinte questões do piloto foram consolidadas com decisões assistidas explícitas,
sem nova rodada cega. Um ajuste adicional conservador mudou a Q0298 de fora para
revisar. O arquivo `intervencoes_registradas.json` guarda antes/depois; nenhuma
dessas intervenções constitui gabarito de professor.

## O que o repositório permite reproduzir

- Preparação determinística dos mesmos anexos e construção dos lotes.
- Formatação das anotações salvas, validação e importação com integridade.
- Consolidação dos mesmos 359 IDs e geração do mesmo CSV e previsão.
- Cálculo do cenário de custo de produção, com preços e consumo assumidos.

Uma nova classificação exige nova interação com um modelo. Os prompts salvos
descrevem regras e entradas, mas não contêm todo o histórico do chat nem asseguram
resposta idêntica. O modelo exato e os tokens internos não foram registrados.
Não se atribuiu ao código a capacidade de gerar sozinho essas respostas.

## Conferência antes do envio

O candidato deve ler `relatorio.md`, `docs/APRESENTAR.md` e as justificativas do
CSV, compreender as premissas e executar os comandos do README. A entrega é uma
proposta assistida: não foi certificada por especialista independente. Somente
uma avaliação jurídica independente poderá medir a precisão e verificar a meta.
