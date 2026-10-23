# Incidente de auditoria 001 — conteúdo exigido para resolver a questão

## Descoberta

Em 16/10/2026, Israel questionou a revisão da Q0171. O assistente havia usado a
variedade de matérias nas alternativas como justificativa insuficiente para
identificar um núcleo. Israel observou que a resposta correta e o conhecimento
que a sustenta podem fornecer um tema específico, mesmo em enunciado genérico.

## Problema constatado

O prompt já pedia leitura de enunciado, comando e alternativas. Entretanto,
a análise não investigou suficientemente a resolução desta questão antes de
concluir que ela deveria permanecer em revisão. O problema não foi simplesmente
falta de instruções do candidato: houve uma aplicação incompleta do critério
pelo assistente e uma heurística excessivamente restritiva.

## Evidência inicial

A Q0171 corresponde à questão 40 da prova tipo 2 verde da FGV/DPE-RJ de 2021.
A prova oficial, a legislação e o gabarito preliminar oficial sustentam B, sobre
hediondez de modalidade de roubo. O gabarito definitivo foi localizado como link,
mas não pôde ser lido na consulta inicial. Resposta B não é gabarito do ID interno
da plataforma: a preferência pelo tema 4693 continua uma interpretação assistida.

## Mudança de método

Reexaminar todas as 359 decisões, incluindo publicadas, revisões e exclusões.
Pesquisar resposta/gabarito; registrar correspondência da questão e alternativas,
banca/tipo/número quando disponíveis, situação preliminar/definitiva, fonte e
limitações. Distinguir informação de gabarito de interpretação legal assistida.
Confrontar o conhecimento da resolução com todo o caminho do tema e possíveis
concorrentes. Não classificar por palavra do enunciado nem apenas pela letra.

Mistura de assuntos não é veto automático à publicação. Resposta única também
não garante enquadramento único. Questões incompletas, ambiguidade de resposta,
alterações legais, escopo indefinido e conflito taxonômico exigem tratamento próprio.

## Papel da auditoria e relato para entrevista

Israel identificou uma insuficiência de critério, apresentou um contraexemplo
e exigiu verificação com evidências. Isso é auditoria do processo e participação
na definição do comportamento esperado, sem alegar que realizou uma validação
jurídica especializada de todas as questões.

Instruções melhores reduzem ambiguidades, mas não asseguram perfeição da IA.
Fontes podem estar incorretas, desatualizadas ou corresponder a outra versão da
prova. Auditoria exige conferir evidências e registrar divergências e limites.
Esta etapa, feita pelo mesmo assistente, não se torna avaliação independente.

O relato posterior deve distinguir: versão inicial, falha identificada pelo
candidato, caso que a demonstrou, evidência consultada, regra alterada, casos
efetivamente reavaliados e efeito real nas decisões. Só informar contagens e
métricas que tenham sido produzidas e verificadas na versão revisada.

## Como explicar a intervenção

O aprendizado foi revisar o critério e a sua aplicação: identificar o conhecimento necessário para resolver a questão, em vez de classificar por palavras do enunciado ou rejeitar automaticamente alternativas de assuntos distintos. O candidato não precisa alegar formação jurídica para explicar como identificou essa falha no processo.

Gabarito de prova e gabarito temático são coisas diferentes. A letra informa qual opção a banca aceitou; ainda é necessário decidir qual conteúdo a questão exercita e qual caminho do catálogo o representa. Uma opção que combina assertivas ou diz “nenhuma das anteriores” pode exigir vários conhecimentos.

Para a entrevista, apoiar cada afirmação em evidências: decisão anterior; intervenção do candidato; fonte consultada; proposta após o reexame; alteração efetivamente incorporada, se houver. A reavaliação da Q0171 está em REAVALIACAO_Q0171.md, com fontes primárias e ressalva sobre o gabarito preliminar.

## Estado inicial deste registro em 16/10/2026

Foram executadas buscas iniciais para os 359 IDs e novas tentativas para quatro erros de serviço. Isso é cobertura de pesquisa, não confirmação de 359 respostas. Há 90 rascunhos individuais de reexame e uma análise fundamentada da Q0171. Os demais ainda não têm validação completa individual registrada.

Nenhuma destas propostas foi integrada ao publicacao.csv da entrega v3. A situação continua 229 publicar, 126 revisar e 4 fora; precisão medida não disponível. Esta etapa não autoriza declarar que a classificação alcançou 95% ou 100% de precisão.

## Encerramento do reexame assistido v4

Os 359 IDs foram relidos e receberam parecer individual com resposta assistida ou pendência explícita. A versão incorporada contém 329 publicar, 25 revisar e 5 fora. Os registros canônicos atuais estão em `auditoria_v4/reexame_359.json` e o caderno completo em `auditoria_v4/caderno_auditoria.md`; o estado exploratório anterior está preservado no histórico.

Foram 107 mudanças de decisão: 103 revisar→publicar, 3 publicar→revisar e 1 revisar→fora. Houve 79 alterações de central e 64 de extras; algumas são refinamentos dentro de ramo já correto. Não apresentar todos esses ajustes como erros comprovados da v3. A cobertura passou de 63,7883% para 91,6435%, o que não mede aumento de precisão.

Dois gabaritos definitivos e um preliminar foram confirmados; 326 respostas são assistidas sem confirmação oficial e 30 não foram confirmadas. Nenhum desses estados equivale a rótulo temático de especialista. A melhora constatável é de explicitação do método, cobertura dos registros e correção de falhas com evidência pontual; a precisão real continua não medida.

## Aplicação posterior às revisões remanescentes

Após Q0097, as57 revisões foram relidas. Houve32 liberações e25 retenções com razões específicas. A intervenção de Israel corrigiu excesso de abstenção por homonímia ou conteúdos complementares. Escolher central+extras não garante o rótulo oculto; a precisão segue não medida. Ver REAVALIACAO_57_REVISOES.md e o histórico v4_antes_reavaliacao_57.
