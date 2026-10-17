# Case Vício IA — classificação de questões jurídicas

Protótipo de classificação assistida por IA para organizar **359 questões** na árvore de tópicos da Vício / Método VDE. A decisão considera o conhecimento necessário para resolver a questão e o caminho do tema no catálogo, com justificativas individuais para publicar, revisar ou deixar fora do recorte.

**Regra adotada no projeto:** publicar quando o conteúdo e o caminho escolhido estiverem suficientemente sustentados; revisar quando permanecer uma dúvida relevante sobre o enquadramento. O tempo do professor deve ser dedicado às pendências que exigem sua intervenção.

## Resultado da entrega

Classificação auditada em **16/10/2026**. Documentação reorganizada em **17/10/2026**.

| Indicador | Resultado |
|---|---:|
| Questões classificadas | **359** |
| Publicar | **329** |
| Revisar | **25** |
| Fora do recorte | **5** |
| Cobertura de publicação: 329/359 | **91,6435%** |
| Precisão temática medida | **Não disponível** |

A previsão entregue é **96%**, com cenários subjetivos de **85%–99%**. Não houve avaliação com os rótulos temáticos dos especialistas: a meta de **95% de precisão permanece não comprovada**. Cobertura é a proporção publicada; precisão é a proporção de classificações corretas entre as publicadas.

Entrega: [publicacao.csv](publicacao.csv), [previsao.txt](previsao.txt) e [relatorio.md](relatorio.md).

## As principais decisões do projeto

| Decisão | Critério e motivo |
|---|---|
| **Classificar pelo conhecimento da resolução** | Ler enunciado, comando e todas as alternativas; identificar o que o aluno precisa saber. Um assunto citado na narrativa pode ser apenas contexto. A resposta e o raciocínio necessário ajudam a identificar o núcleo. |
| **Não revisar automaticamente alternativas de assuntos diferentes** | A diversidade das opções, isoladamente, não impede reconhecer o conteúdo cobrado. Também não permite inferir a dificuldade da questão. É necessário investigar a resolução. |
| **Avaliar todas as assertivas, inclusive as falsas** | Em itens I/II/III ou de julgamento, os conhecimentos necessários para rejeitar proposições também integram o objeto da questão. A combinação indicada na resposta não elimina esses conteúdos. |
| **Escolher central e extras com funções distintas** | O central representa o núcleo; extras representam conhecimentos adicionais efetivamente exigidos. Não se adicionam todos os temas mencionados na narrativa ou nos distratores. |
| **Comparar o caminho completo dos temas** | Títulos iguais em ramos diferentes não demonstram equivalência. A escolha depende de conteúdo, disciplina e escopo. A homonímia, sozinha, também não obriga revisão: é possível escolher e justificar um caminho. |
| **Reservar a revisão para uma pendência concreta** | Ramo sem solução, conteúdo ausente, possível problema na resposta, contexto temporal ou escopo insuficiente justificam revisão. Dois conteúdos complementares podem ser representados por central e extra. |
| **Usar fora quando faltar tema ativo compatível** | Dificuldade ou falta de gabarito não bastam para excluir. A decisão depende da comparação com a árvore disponível e mantém a questão nos dados originais. |
| **Separar julgamento semântico de validação técnica** | O assistente apoia a interpretação; Python valida e consolida os registros. Formato válido, hashes consistentes e testes aprovados não demonstram acerto jurídico. |

Na régua do case, o tema atribuído pelos especialistas e seus ancestrais ou descendentes no mesmo ramo são aceitos; outro subtema irmão conta como erro. Isso não autoriza escolher uma raiz ou um tema genérico para esconder uma dúvida. O pipeline rejeita temas raiz e inativos.

Um filho do central pode ser extra quando representa um conhecimento adicional efetivamente exigido e há justificativa individual. Essa decisão registra o conteúdo com maior detalhe, sem presumir que a classificação no pai garanta a busca pelo filho.

Critérios completos: [protocolo da auditoria](auditoria_v4/PROTOCOLO_FINAL.md).

A orientação recebida no processo seletivo reforçou essa análise: o título isolado não determina equivalência; é necessário avaliar o ramo do Direito, o conteúdo específico e registrar as premissas nos casos ambíguos. A regra de não revisar automaticamente por homonímia é uma decisão metodológica deste projeto, não uma citação literal do enunciado.

## A intervenção do candidato e a mudança de método

Durante a conferência, **Israel questionou a abstenção baseada na diversidade de assuntos das alternativas**. A pergunta que orientou a mudança foi: **qual conhecimento o aluno precisa dominar para resolver a questão?** A Q0171 serviu como contraexemplo: investigar sua resolução permitiu identificar um núcleo específico.

O prompt já solicitava a leitura das alternativas. A falha incluiu uma aplicação incompleta dessa instrução pelo assistente e uma regra de abstenção excessivamente restritiva. A correção exigiu reexaminar o conteúdo, e não apenas reformular o prompt.

A intervenção teve quatro efeitos documentados:

1. **Reexame de todos os 359 IDs**, incluindo questões antes publicadas, revisões e fora do recorte.
2. **Separação entre contexto narrativo e conhecimento cobrado**, considerando resolução, alternativas e assertivas falsas.
3. **Reavaliação dos temas homônimos**, com escolha fundamentada quando possível e manutenção de dúvidas relevantes.
4. **Registro das premissas e das alterações por questão**, preservando os estados anteriores.

Essa participação foi uma auditoria do processo e dos critérios. A interpretação jurídica continuou assistida; não houve validação jurídica independente de todo o conjunto. O incidente, a evidência e a mudança de método estão em [INCIDENTE_AUDITORIA_001.md](docs/INCIDENTE_AUDITORIA_001.md).

## Exemplos que mostram os critérios em prática

| Questão | Decisão final | Por quê |
|---|---|---|
| **Q0171** | Publicar — **Crimes Hediondos (4693)** | Apesar das alternativas de assuntos diferentes, a resolução identifica a hediondez de modalidade de roubo. Prova e gabarito oficial **preliminar** sustentam B. [Análise](docs/REAVALIACAO_Q0171.md). |
| **Q0353** | Publicar — **Audiência de Instrução e Julgamento (5535)** | A prescrição motiva a urgência na narrativa; a solução cobra concentração da prova oral em audiência, preservando a defesa. Resposta assistida, sem gabarito oficial confirmado. |
| **Q0337** | Publicar — **Abuso de Autoridade (4684)**; extra **Ação Penal Pública Incondicionada (5470)** | Para julgar a terceira assertiva, inclusive rejeitá-la, é necessário conhecer a natureza da ação penal. O extra representa uma cobrança efetiva. |
| **Q0097** | Publicar — **Organizações Criminosas (4705)**; extra **Concurso Material (5067)** | Escolheu-se Legislação Especial pelo conteúdo da Lei 12.850; concurso material integra a resolução. O homônimo de outro ramo não foi tratado como equivalente nem como impedimento automático. E tem gabarito definitivo; o ID é uma escolha fundamentada. [Decisão](docs/REVISAO_Q0097.md). |
| **Q0355** | Revisar — sugestão **Tráfico de Drogas (4708)** | Há gabarito definitivo E, mas o objeto é porte para consumo pessoal. A resposta confirmada não esclarece se o módulo Tráfico abrange esse conteúdo. A dúvida é de escopo. |
| **Q0219** | Revisar — sugestão **Participação (5074)** | A situação hipotética referenciada não veio nos dados. Falta conteúdo necessário para resolver e apresentar a questão completa ao aluno. |
| **Q0298** | Fora do recorte | A cobrança é da Lei 8.137; o nó ativo 4694 delimita crimes previstos no CDC, outro diploma. Adotou-se uma leitura restrita desse escopo, sem ampliar silenciosamente o catálogo. |

Após a Q0097, as 57 revisões remanescentes foram relidas: **32 passaram a publicar e 25 permaneceram em revisão**, com razões específicas. Consulte [a reavaliação completa](docs/REAVALIACAO_57_REVISOES.md), [os registros estruturados](auditoria_v4/reavaliacao_57.json) e [os pareceres de todos os itens](auditoria_v4/caderno_auditoria.md).

## Processo e evolução dos resultados

1. **Preparação:** preservação dos originais, normalização do HTML sem reescrever o conteúdo e validação da árvore. São 377 temas, dos quais 375 ativos.
2. **Piloto de 20 questões:** duas rodadas para desenvolver instruções e inspecionar decisões. Suas diferenças não foram tratadas como precisão medida nem como avaliação independente.
3. **Classificação inicial:** 339 itens restantes em 34 lotes v3, consolidados com os 20 do piloto.
4. **Auditoria assistida:** releitura dos 359 itens, pesquisa de fontes e respostas quando disponíveis e registro da resolução ou pendência. Depois, revisão dirigida da Q0097 e das 57 revisões remanescentes.
5. **Exportação:** validação dos registros, aplicação da auditoria e geração dos arquivos finais, mantendo o histórico.

| Etapa | Publicar | Revisar | Fora | Cobertura |
|---|---:|---:|---:|---:|
| Consolidação v3 | 229 | 126 | 4 | 63,7883% |
| Primeiro reexame completo v4 | 296 | 58 | 5 | 82,4513% |
| Liberação da Q0097 | 297 | 57 | 5 | 82,7298% |
| Reavaliação das 57 revisões — entrega atual | **329** | **25** | **5** | **91,6435%** |

Da v3 à entrega atual, ocorreram **107 mudanças de decisão**: 103 de revisar para publicar, três de publicar para revisar e uma de revisar para fora. Houve 79 mudanças de central e 64 de extras; parte representa refinamentos dentro do mesmo ramo, sem demonstrar erro anterior. A entrega contém 79 questões com extras.

O aumento constatado é de cobertura; a precisão real não foi medida. Estados anteriores: [v3](historico/v3), [antes da Q0097](historico/v4_antes_Q0097) e [antes da reavaliação das 57 revisões](historico/v4_antes_reavaliacao_57).

## Evidências e estimativa de precisão

Há duas referências distintas: **o gabarito da prova**, que informa a resposta aceita pela banca, e **o rótulo temático**, que informa o tema escolhido pelos especialistas da plataforma. Pesquisar o primeiro ajuda a interpretar a questão, mas não fornece o segundo.

| Estado da resposta registrado | Questões |
|---|---:|
| Gabarito oficial definitivo confirmado | 2 |
| Gabarito oficial preliminar confirmado | 1 |
| Resposta formulada pelo assistente, sem gabarito oficial confirmado | 326 |
| Resposta não confirmada | 30 |

Foram registradas buscas iniciais para os 359 IDs. Resultados de busca e correspondências automáticas com PDFs permanecem **pistas** até a confirmação. Consultas pontuais a legislação e precedentes são documentadas separadamente; os fundamentos indicados não foram todos verificados. O texto legal atual não substitui o contexto histórico da prova.

Uma questão pode ter conteúdo temático identificável sem letra confirmada. Se a dúvida sobre a resposta alterar o enquadramento ou comprometer a integridade do item, a pendência permanece explícita. Confirmar a letra também não elimina uma dúvida sobre o catálogo, como mostra a Q0355.

A previsão de **96%** é qualitativa: considera resolução, compatibilidade do caminho e abstenção nas pendências. A faixa **85%–99%** representa cenários subjetivos de sensibilidade, não um intervalo de confiança. A previsão não foi elevada com as liberações e não tem validação quantitativa independente.

As confianças do CSV são julgamentos não calibrados sobre o central; em fora, zero é convenção de ausência de tema. Concordância com o mesmo assistente, buscas e testes não medem precisão jurídica. Medir e calibrar exige uma referência temática independente. Premissas: [previsao.txt](previsao.txt) e [PREMISSAS_PREVISAO.json](docs/PREMISSAS_PREVISAO.json).

## Reproduzir a entrega

**Python 3.12 recomendado.** A reprodução usa somente a biblioteca padrão e dispensa chave de API. Dentro da pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m unittest discover -s tests -v
python importar_todos_v3.py
python finalizar_case.py --saida entrega_reproduzida

cmp publicacao.csv entrega_reproduzida/publicacao.csv
cmp previsao.txt entrega_reproduzida/previsao.txt
```

Use um **diretório de saída novo** a cada exportação. Os comandos `cmp` não exibem saída quando os arquivos são idênticos. A ativação acima é para Linux/macOS.

O importador verifica os 34 lotes v3; zero novas importações é esperado quando as execuções salvas já existem. O exportador valida dados, respostas e histórico, aplica a auditoria e gera `publicacao.csv`, `previsao.txt`, `resumo_entrega.json` e `intervencoes_registradas.json`. A suíte atual contém **28 testes**, voltados às regras técnicas e à reprodução.

**Essa execução reproduz a consolidação das decisões salvas.** A interpretação semântica foi produzida em interações com o ChatGPT e registrada por questão. O protótipo não executa nova inferência, não contém modelo treinado e não classifica autonomamente dados novos. Uma nova conversa pode produzir respostas diferentes.

## Organização e rastreabilidade

| Arquivo ou pasta | Papel no projeto |
|---|---|
| [publicacao.csv](publicacao.csv) | Entrega final, com 359 linhas de dados |
| [previsao.txt](previsao.txt) | Previsão, cenários e cobertura conhecida |
| [relatorio.md](relatorio.md) | Método, diagnóstico, proposta de produção e memo para o professor |
| [dados/originais](dados/originais) | Arquivos recebidos, preservados como fonte |
| [vicio_ia](vicio_ia) e [tests](tests) | Preparação, validação, importação e testes |
| [lotes_v3](lotes_v3) e [respostas_v3](respostas_v3) | Lotes, prompts e respostas salvas; v1/v2 também preservadas |
| [auditoria_v4/decisoes](auditoria_v4/decisoes) | Anotações explícitas das decisões semânticas |
| [reexame_359.json](auditoria_v4/reexame_359.json) | Registro estruturado usado pelo exportador |
| [caderno_auditoria.md](auditoria_v4/caderno_auditoria.md) | Questões completas, resposta ou pendência, análise e comparação com a v3 |
| [resumo_auditoria.json](auditoria_v4/resumo_auditoria.json) | Contagens e transições entre decisões |
| [auditoria_v4/fontes](auditoria_v4/fontes) | Gabaritos confirmados, consultas dirigidas e limites das fontes |
| [docs/APRESENTAR.md](docs/APRESENTAR.md) | Explicação didática para apresentação |
| [historico](historico) | Versões anteriores e registros exploratórios |

O prompt de referência não é a transcrição integral das conversas. A auditoria v4 ocorreu em uma conversa existente, com inspeção em blocos de trinta questões. Esses blocos organizaram a leitura e não representam chamadas isoladas a uma API.

## Tecnologias, custo e evolução para produção

**Python e biblioteca padrão** reduziram o preparo do ambiente e permitiram verificações sem dependências adicionais. **ChatGPT pela assinatura existente** apoiou a interpretação e a reavaliação. O escopo foi concentrado na classificação, nos registros de decisão e na entrega exigida pelo case.

Identificadores exatos dos modelos não foram confirmados. O piloto incluiu esta conversa e uma conversa separada do candidato. Custo executado de **API de classificação: US$ 0**; assinatura existente não rateada e tokens internos não medidos. O tempo total não foi instrumentado, e tempos de importação não são latências de inferência.

Para consultar o cenário de produção de 50 mil questões por semana:

```bash
python simular_custos.py --volume 50000
```

Os preços e tokens hipotéticos estão em [CUSTOS_PRODUCAO.json](docs/CUSTOS_PRODUCAO.json). O comando simula custos, sem executar ou cobrar API. A proposta de operação em escala, incluindo alternativas de modelos e revisão especializada, está no [relatório](relatorio.md); ela não foi implementada como serviço neste protótipo.

<details>
<summary>Pesquisa opcional, preparação e atualização das anotações</summary>

Os scripts de pesquisa exigem internet e, para PDFs, Poppler (`pdftotext`). Não participam da reprodução obrigatória:

```bash
python auditoria_v4/scripts/consultar_normas.py
python auditoria_v4/scripts/baixar_provas_publicas.py --help
```

As fontes podem mudar ou ficar indisponíveis. Os índices preservam URLs e hashes das obtenções registradas; os caches de PDFs não são distribuídos.

Para alterar uma decisão, registre a justificativa em `auditoria_v4/decisoes`, preserve o histórico e confira a coerência dos demais registros da etapa antes de regenerar:

```bash
python auditoria_v4/scripts/gerar_auditoria.py
python finalizar_case.py --saida entrega_reproduzida_nova
```

O gerador formata as anotações salvas; não faz inferência. Compare a nova saída antes de substituir a entrega da raiz. Atualizar hashes registra uma versão, sem validar seu mérito jurídico.

O módulo rejeita dados alterados, IDs ausentes ou repetidos, temas inativos/raiz, relações hierárquicas inválidas, extras sem a justificativa independente exigida e registros anteriores incompatíveis.

Comandos históricos de preparação e formatação:

```bash
python -m vicio_ia preparar --saida dados/processados_regenerados
python gerar_lotes_v3.py --saida lotes_v3_regenerados
python gerar_respostas_salvas.py --saida respostas_v3_regeneradas
```

</details>
