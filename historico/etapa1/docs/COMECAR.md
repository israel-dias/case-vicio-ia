> Documento histórico de etapa anterior. Para a versão auditada v4, siga o README da raiz.

# Começar e entender o projeto

## O que esta primeira etapa faz

Imagine as questões como fichas recebidas de várias fontes. Primeiro conferimos
se todas chegaram, se não há IDs repetidos e se é possível ler os textos.
Em seguida montamos o catálogo de temas que ainda podem ser usados.
Só depois entregamos esses dados à IA.

Aqui não estamos decidindo o Direito nem criando um gabarito. Estamos preparando
uma entrada consistente para conseguir analisar as classificações posteriormente.

## Três comandos, três funções

| Comando | Pergunta que resolve |
|---|---|
| preparar | As entradas estão completas e legíveis? |
| lotes | Qual contexto e quais questões serão entregues à IA? |
| importar | A resposta contém todos os IDs e respeita o contrato? |

## O que examinar primeiro

1. README.md: instruções e estado do projeto.
2. dados/processados/diagnostico.md: problemas encontrados automaticamente.
3. docs/DECISOES.md: razões das escolhas.
4. lotes_v1/piloto/questoes.json: vinte questões do primeiro experimento.
5. lotes_v1/piloto/prompt.txt: contexto exato para enviar ao chat.

O catálogo compacto preserva todos os IDs ativos. As raízes ajudam a entender
as disciplinas; não devem ser usadas como depósito genérico de questões.

## Como explicar esta etapa numa entrevista

Comece pelo problema: classificação incorreta faz o aluno estudar o assunto errado.
Explique que preservar os dados permite rastrear o que foi recebido e o que mudou.
Mostre um HTML com quebras de linha e a versão limpa.
Mostre um tema repetido em dois ramos e explique por que o ID também importa.
Mostre que comando vazio não exclui automaticamente a questão.
Por fim, explique que um teste de formato não verifica a correção jurídica.

## O próximo experimento

Classificar o piloto usando o prompt gerado e preservar a resposta real.
Analisar as dúvidas, sem simplesmente aceitar o percentual declarado pela IA.
Registrar o que precisou melhorar. Antes de avaliar a precisão da política,
reservar uma amostra diferente daquela usada para ajustá-la.

## Sobre as visualizações

O relatório e seu memo já servem para expor as conclusões.
Depois das classificações, gráficos simples podem mostrar:

- Questões publicadas, encaminhadas para revisão e fora do catálogo.
- Distribuição por tema ou disciplina prevista.
- Motivos de revisão e sobreposição entre categorias.
- Resultado da auditoria, identificando o tipo de referência utilizada.

Cobertura pode ser contada exatamente a partir das decisões. Precisão depende
de comparar classificações com referência apropriada. Não confundir as duas.
