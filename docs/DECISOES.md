# Registro de decisões — etapa 1

## D01 — Pipeline assistido pela assinatura existente

Motivo: preferência do candidato por usar a assinatura já paga e evitar compra
de créditos. A empresa permite ferramentas próprias e decisões manuais registradas.
Efeito: inferência interativa; preparação e importação automatizadas.
Limite: não se trata de classificação autônoma por API. Uma futura integração
programática precisa ser explicitamente identificada e testada.

## D02 — Biblioteca padrão nesta primeira etapa

A proposta inicial mencionava Beautiful Soup, Pydantic e SDK de provedor.
Para começar sem instalações nem rede, a versão 0.1 usa HTMLParser, json, csv,
argparse, hashlib e unittest. Os testes cobrem negações, HTML inline, parágrafos,
alternativas e o contrato de importação.
Se o tratamento de HTML ou os schemas crescerem, compararemos a troca por
Beautiful Soup e Pydantic com exemplos reais. Nenhuma biblioteca é requisito
do case; a mudança de abordagem foi registrada antes da classificação.

## D03 — Originais preservados

As quatro entradas são copiadas sem edição. Preparação grava em pasta separada.
Hashes vinculam a versão utilizada. Os IDs continuam sendo os fornecidos pela empresa.

## D04 — Metadados são pistas

Origem não é rótulo oficial. Alias de Direito Penal para Penal e de Direito
Processual Penal para Processo Penal serve somente à inspeção e ao sorteio do
piloto. Não determina o tema nem a decisão publicar/revisar/fora.
Disciplina externa ao catálogo recebe um alerta, não uma decisão fora automática.

## D05 — Manter ambiguidades da árvore

Dois temas inativos não são elegíveis. Temas homônimos em ramos diferentes não
são fundidos. Oito grupos de títulos repetidos e vinte temas sem descrição
serão examinados durante os experimentos.
Ancestral/descendente é diferente de tema irmão, independentemente da semelhança
do nome. A função mesmo_ramo existe para essa comparação estrutural.

## D06 — Catálogo compacto como primeira experiência

Todos os temas ativos aparecem com ID, pai, nível e caminho no prompt.
As descrições completas ficam no arquivo do lote, mas não são incorporadas
ao prompt inicial. Isso é uma hipótese de simplificação, não resultado de avaliação.
Compararemos uma versão com descrições antes de escolher o formato final.
Se anexos adicionais forem fornecidos ao modelo, criar outra versão do lote e
registrar o novo contexto efetivamente enviado.

## D07 — Piloto de desenvolvimento

Vinte questões, com seed 42, distribuídas entre as quatro origens normalizadas
e um grupo de outros metadados. A seleção é baseada em origem, que pode estar
errada; não representa distribuição de classes jurídicas reais.
O piloto não é referência oficial nem amostra independente para medir uma
política ajustada nele. Definiremos a avaliação separada antes de calibrar a política.

## D08 — Confiança e publicação permanecem preliminares

confianca_modelo é autoavaliação não calibrada. Nenhuma sugestão de publicar
vira publicação final automaticamente. Falta definir avaliação e política.
Em fora, confiança null é uma convenção interna para evitar inventar uma chance
de um tema central inexistente. O valor exigido no CSV final será definido e
explicado antes da exportação; não se apresenta este JSON como formato final.

## D09 — Custos e tokens

No importador, custo_api_executado_usd é zero e tokens_api_medidos é null.
Não foram feitas chamadas pagas. Não se atribui custo exato à assinatura nem
se presume um modelo de API equivalente ao chat.
Uma estimativa futura contará os textos disponíveis e indicará o modelo,
o preço, os tokens não observáveis e as hipóteses de processamento.

## D10 — Dashboard posterior

As entregas solicitadas e a qualidade vêm primeiro. Um painel pode ajudar a
expor cobertura, revisão, temas ambíguos e resultados da auditoria depois
da classificação. Mostrar indicadores vazios ou inventados não acrescenta evidência.
