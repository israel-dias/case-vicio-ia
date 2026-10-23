# V12 — novos usos de palavra_completo

**Resultado:** houve ganho pequeno, acompanhado de um novo erro de publicação. A combinação preservando V11 publica 45/100, com 43 acertos (95,56%), contra 40/100 com 39 acertos (97,50%). Nas 559 sem rótulo, passa de 361 para 365 publicações (64,58% para 65,30%). Não substitui a entrega automaticamente. O corte de 50% não foi testado.

## Método e preservação

Os seis desenhos (controle, quatro mudanças e combinação) foram fixados no protocolo antes da avaliação. Todos mantêm palavra_completo, o ranking V8 e os identificadores V9. O controle V11 foi reproduzido com os mesmos temas, decisões e confianças nas 100 e nas 559. Não houve bônus de confiança, corte manual de pesos negativos, solução de alternativas por LLM, busca de gabaritos nem exceções por ID.

A regressão logística compara cada questão com as famílias do catálogo. As mudanças afetam a confiança e a decisão, não o ranking de temas. Cada variante foi ajustada, calibrada e recebeu corte próprio apenas com os grupos internos: cinco folds externos, quatro internos, suporte mínimo de dez e meta empírica de 95%. Os 100 rótulos já foram expostos e reutilizados no desenvolvimento. Esta avaliação não é teste externo cego e não certifica 95% nas 559.

`preservar_v11` conserva tema, confiança e decisão de toda publicação V11; se a V11 revisa, considera a nova variante. Conserva também o erro antigo Q0252, que continua contado. A política não consulta o acerto para escolher saídas. `substituir_com_v9` mantém a V9 como primeiro caminho, sem garantir conservar todos os acréscimos V11.

## Comparação nas 100 — preservando V11

| Variante | Publicadas | Corretas | Erros | Precisão publicada | Novas corretas | Novas erradas | Brier (menor melhor) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Controle V11 | 40 | 39 | 1 | 97.50% | 0 | 0 | 0.157969 |
| Vantagem sobre concorrentes | 44 | 42 | 2 | 95.45% | 3 | 1 | 0.156475 |
| Foco versus texto completo | 40 | 39 | 1 | 97.50% | 0 | 0 | 0.158673 |
| Alternativas condicionais | 40 | 39 | 1 | 97.50% | 0 | 0 | 0.159149 |
| Regularização C=0,3 | 44 | 42 | 2 | 95.45% | 3 | 1 | 0.157413 |
| Combinação das melhorias | 45 | 43 | 2 | 95.56% | 4 | 1 | 0.157186 |

O tema top1 permanece compatível com a folha em 71/100 em todas as variantes. Não se deve confundir isso com os 95,56% das 45 publicadas. O número de sugestões erradas não foi reduzido; algumas apenas passaram ou deixaram de passar pelo filtro. A pequena mudança de Brier não demonstra melhora estatisticamente confirmada.

## Simulação nas 559 e nos 300 recentes

| Variante | Publicar, preservando | Revisar | Cobertura | Publicar, sem preservar acréscimos V11 | Perdas V11 nessa opção | Publicar nos 300 recentes, preservando |
|---|---:|---:|---:|---:|---:|---:|
| Controle V11 | 361 | 198 | 64.58% | 361 | 0 | 198 |
| Vantagem sobre concorrentes | 365 | 194 | 65.30% | 362 | 3 | 200 |
| Foco versus texto completo | 361 | 198 | 64.58% | 357 | 4 | 198 |
| Alternativas condicionais | 361 | 198 | 64.58% | 357 | 4 | 198 |
| Regularização C=0,3 | 362 | 197 | 64.76% | 361 | 1 | 198 |
| Combinação das melhorias | 365 | 194 | 65.30% | 363 | 2 | 200 |

A precisão real das 559 e dos 300 recentes é desconhecida. Não se escolheu uma variante pelo volume nessas questões. Os quatro acréscimos nas 559 não têm acerto confirmado e não são os mesmos cinco exemplos rotulados apresentados abaixo.

## Cinco mudanças da combinação nas 100

| ID | Tema sugerido | Confiança V11 → V12 OOF | Corte V12 do fold | Resultado pela folha |
|---|---|---:|---:|---|
| Q0115 | Criminologia > Teorias Sociológicas Explicativas da Criminalidade | 78.47% → 81.41% | 76.19% | Correto |
| Q0169 | Processo Penal > Das Questões e Processos Incidentes | 72.79% → 77.95% | 76.19% | Correto |
| Q0319 | Penal > Teoria do Crime: Fato Típico | 80.00% → 82.33% | 80.75% | ERRO |
| Q0311 | Processo Penal > Comunicação dos Atos Processuais | 84.45% → 84.89% | 83.25% | Correto |
| Q0339 | Processo Penal > Sentença Penal | 82.97% → 86.73% | 83.25% | Correto |

Q0115, Q0169, Q0311 e Q0339 passaram a publicar com tema aceito pela folha. Os pais do tema oficial são aceitos quando estão no mesmo ramo. Na Q0311, a mudança de confiança foi pequena; o corte também mudou. O ganho não é atribuível isoladamente a uma palavra ou a pontos somados à confiança.

**Q0319 é o alerta:** o enunciado trata de co-autoria, mas o ranking preservado sugere Teoria do Crime: Fato Típico (5218). A folha indica Concurso de Pessoas > Autoria Mediata, Colateral e Coautoria (5073). A combinação aumentou a confiança para 82,33%, acima do corte 80,75%, e publicou a sugestão errada. A variante palavra_relativa incorre no mesmo novo erro. O dado original combina assertivas I/II/III com alternativas de classes de crimes; há uma possível inconsistência de formato que merece conferência da fonte. Isso não elimina o erro temático na avaliação nem autoriza corrigir o dado silenciosamente.

A regularização isolada publica outro erro: Q0202 recebe Crimes Contra a Dignidade Sexual, enquanto a folha indica Erro de Tipo. Os acertos novos dessa variante são Q0115, Q0169 e Q0221; Medida de Segurança é aceito na Q0221 porque consta dos extras oficiais.

## Recomendação

Manter a V11 como referência preservada. A combinação é candidata exploratória: acrescenta quatro acertos e um erro nas 100, com ganho de apenas quatro publicações nas 559. Não há evidência suficiente para promovê-la automaticamente. Foco e alternativas condicionais isoladamente não acrescentam publicações; sem preservação, perdem quatro nas 559. Não incorporar essas mudanças isoladas apenas pela plausibilidade da ideia.

O próximo gargalo a investigar é a recuperação do tema, separadamente da confiança: as 29 sugestões incompatíveis com a folha continuam incompatíveis. Mais confiança sobre um tema errado aumenta o risco. O teste de publicar a partir de 50% deve constituir outra rodada, usando as probabilidades já congeladas, registrando erros adicionais e sem reajustar percentuais para produzir a aparência de acerto.

## Integridade e reprodução

Os testes V12 cobrem vantagens entre concorrentes, empates, alternativas numéricas/Certo-Errado/assertivas, preservação do atributo global, foco ausente, ranking fixo, rejeição de rótulos externos, preservação de erros antigos, inferência sem rótulos/rede, novos IDs e alteração de texto sob ID antigo, artefatos adulterados, ausência de tabela por ID, travessia de caminhos e proteção de saídas existentes. Os testes V11 também foram executados. A reprodução completa das 559 para cada variante está em reproducao_verificada.json. Aprovação desses testes não valida Direito.

Uma primeira tentativa foi interrompida porque reconstruir o controle com uma matriz em outra ordem de memória alterou a convergência numérica. A implementação usa agora o mesmo caminho legado no controle e confirma a reprodução antes da comparação. O histórico foi preservado.

Veja LEIA_PRIMEIRO_PALAVRA_V12.md para comandos. As questões completas alteradas estão abaixo e no JSON estruturado; são dados do case, sem alterações e sem escolha manual de novos temas.

## Questões completas das cinco mudanças

### Q0115

Paulo, executivo do mercado financeiro, após um dia estressante de trabalho, foi demitido. O mundo desabara sobre sua cabeça. Pegou seu carro e o que mais queria era chegar em casa. Mas o horário era de rush e o trânsito estava caótico, ainda chovia. No interior de seu carro sentiu o trauma da demissão e só pensava nas dívidas que já estavam para vencer, quando fora acometido de uma sensação terrível: uma mistura de fracasso, com frustração, impotência, medo e etc. Neste instante, sem quê nem porque, apenas querendo chegar em casa, jogou seu carro para o acostamento, onde atropelou um ciclista que por ali trafegava, subiu no passeio onde atropelou um casal que ali se encontrava, andou por mais de 200 metros até bater num poste, desceu do carro meio tonto e não hesitou, agrediu um motoqueiro e subtraiu a motocicleta, evadindo-se em desabalada carreira, rumo à sua casa. Naquele dia, Paulo, um pacato cidadão, pagador de impostos, bom pai de família, representante da classe média-alta daquela metrópole, transformou-se num criminoso perigoso, uma fera que ocupara as notícias dos principais telejornais. Diante do caso narrado, identifique dentre as Teorias abaixo, a que melhor analisa (estuda/explica) o caso.

Comando: Diante do caso narrado, identifique dentre as Teorias abaixo, a que melhor analisa (estuda/explica) o caso.

A) Escola de Chicago.  
B) Teoria da associação diferencial.  
C) Teoria da anomia.  
D) Teoria do<i> labeling approach</i>.  
E) Teoria crítica. 

Sugestão do sistema: Criminologia > Teorias Sociológicas Explicativas da Criminalidade. Referência: Criminologia > Teorias Sociológicas Explicativas da Criminalidade > Teorias Criminológicas em Espécie. Extras: 4385.

### Q0169

A respeito das causas de impedimento e suspeição do juiz, de acordo com o Código de Processo Penal, assinale a alternativa correta.

A) Nos juízos coletivos, não poderão servir no mesmo processo os juízes que forem entre si parentes, consanguíneos ou afins, em linha reta ou colateral, até o quarto grau.
B) O juiz será suspeito, podendo ser recusado por qualquer das partes, se já tiver funcionado como juiz de outra instância, pronunciando-se de fato ou de direito sobre a questão.
C) Ainda que dissolvido o casamento, sem descendentes, que ensejava impedimento ou suspeição, não funcionará como juiz o sogro, o padrasto, o cunhado, o genro ou enteado de quem for parte no processo.
D) O juiz será impedido se for credor ou devedor de qualquer das partes.
E) A suspeição poderá ser reconhecida ou declarada ainda que a parte injurie, de propósito, o juiz.

Sugestão do sistema: Processo Penal > Das Questões e Processos Incidentes. Referência: Processo Penal > Das Questões e Processos Incidentes > Exceção de Suspeição, de Impedimento ou de Incompatibilidade. Extras: nenhum.

### Q0319

A co-autoria é impossível nos crimes:

I. Culposos;

II. Unissubsistentes;

III. Habitual ou de mera conduta.

Comando: Complete a frase indicando em quais crimes a co-autoria é impossível.

A) Comissivos.
B) Omissivos.
C) Próprios.
D) De mão própria.
E) Culposos

Sugestão do sistema: Penal > Teoria do Crime: Fato Típico. Referência: Penal > Concurso de Pessoas > Autoria Mediata, Colateral e Coautoria. Extras: nenhum.

### Q0311

Considere que um oficial de justiça não tenha localizado o réu, para realizar a citação pessoal na ação penal, no endereço que constava dos autos. Nesse caso,

A) o oficial de justiça deverá proceder à citação por hora certa, a
ser cumprida, no máximo, em três dias.
B) o juiz decretará a revelia do réu e dará seguimento à ação
penal.
C) será feita a citação por edital e, caso o réu não compareça, a
ação penal ficará suspensa.
D) será citada a Defensoria Pública para realizar a defesa técnica
do réu.
E) a falta de citação pessoal interromperá o prazo prescricional
até a localização do réu.

Sugestão do sistema: Processo Penal > Comunicação dos Atos Processuais. Referência: Processo Penal > Comunicação dos Atos Processuais > Citação e Contagem dos Prazos. Extras: nenhum.

### Q0339

Assinale a alternativa correta.

A) Qualquer das partes poderá, no prazo de 5 (cinco) dias,  pedir ao juiz que declare a sentença sempre que nela houver obscuridade, contradição, ambiguidade ou omissão.  
B) Ainda  que  preclusa  a  decisão  de  pronúncia,  havendo  circunstância superveniente que altere a classificação do  crime, caberá ao próprio juiz de primeiro grau fazê-la,  respeitado o contraditório 
C) Nos crimes de ação pública, conforme previsão  legal,  não poderá o juiz reconhecer circunstâncias agravantes  que não tenham sido alegadas pelo Ministério Público.  
D) A violação da regra da correlação entre acusação e sentença é causa de nulidade relativa. 

Sugestão do sistema: Processo Penal > Sentença Penal. Referência: Processo Penal > Sentença Penal. Extras: nenhum.

