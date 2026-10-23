# Case Vício IA — investigação de contexto, busca e confiança V23

Atualização experimental concluída em 22/10/2026. Reúne as correções de contexto V19/V20, a pesquisa e os experimentos semânticos V21/V22 e a análise de confiança V23. **Nenhuma nova versão foi promovida à entrega formal. Os CSVs da raiz são controles históricos.**

A melhor composição experimental preservada publica **395/559 (70,66%)**, com **50 acertos em 52 publicadas nas 100 referências (96,15%)**. Nas 300 recentes, publica 218. A precisão real nas 559 é desconhecida; as referências já foram expostas e reutilizadas e a composição não tem calibração global independente. Não há garantia de atingir 95% nas questões avaliadas.

Os testes novos não superaram essa composição. O apoio semântico teve 26/27 publicações corretas nas referências (96,30%), mas publicou só 111/559. O comparador semântico acertou 75 temas/100, porém não obteve uma política de publicação com suporte suficiente. A confiança direta também ficou abaixo da meta nas referências. Preservamos tentativas e perdas para justificar a decisão.

## O diagnóstico principal

Em 17 dos 18 erros de tema do controle contextual, um ramo aceito já estava entre os cinco candidatos: o gargalo restante está sobretudo em escolher o candidato adequado. Há 109 famílias ativas, mas 64 não têm exemplo central/extra nas 100 referências; 18 das famílias representadas têm só um exemplo. Os oito exemplos fora exigem esclarecimento do recorte, não regras improvisadas de exclusão.

- [RESULTADOS_INVESTIGACAO_V23.md](RESULTADOS_INVESTIGACAO_V23.md): critérios aplicados, comparações, decisão e limites.
- [pesquisa_v21/CADERNO_ERROS_CONHECIDOS.md](pesquisa_v21/CADERNO_ERROS_CONHECIDOS.md): os 26 desacertos conhecidos do controle, com questões completas, referência e cinco candidatos.
- [pesquisa_v21/FONTES_E_DECISOES.md](pesquisa_v21/FONTES_E_DECISOES.md): fontes primárias consultadas e como motivaram os testes.
- [RESULTADOS_V19.md](RESULTADOS_V19.md) e [RESULTADOS_V20.md](RESULTADOS_V20.md): expressões, contexto e confiança preservada.
- `VALIDACAO_V23.json`: testes, reprodução e preservação dos arquivos anteriores.

## Instalar e conferir

Python 3.12. Execute dentro desta pasta, preferencialmente em uma venv própria:

```bash
python3 -m pip install -r requisitos_v17.txt
python3 -m unittest discover -s semantica_v21/tests -v
```

O pacote contém os vetores E5 já preparados. Não é necessário instalar encoder ou baixar pesos para classificar. Testes de software não comprovam acerto jurídico.

## Reproduzir a melhor composição experimental preservada

```bash
python3 rotear_comando_v18.py --saida conferencia_suplemento_v18
```

O comando regenera controle e rota de comando pelo texto, com modelos clássicos congelados. Produz `classificacoes_experimentais.csv` e um resumo na pasta nova. Usa os 559 fora da folha; não substitui automaticamente `publicacao.csv` nem gera uma nova entrega formal de 659 linhas. A composição e seus limites estão no relatório.

## Reproduzir os experimentos novos

```bash
python3 classificar_semantica_v21.py --saida conferencia_semantica_v21
python3 classificar_semantica_v22.py --variante semantica_apoio --saida conferencia_apoio_v22
python3 classificar_qualidade_v23.py --saida conferencia_qualidade_v23
```

Use uma saída inexistente em cada execução. Cada comando aplica sua própria política congelada; as contagens serão diferentes porque são variantes, não atualizações cumulativas de cobertura. Nenhum deles consulta rótulos, usa rede, treina, recalibra ou chama encoder/LLM. O índice lexical é reconstruído apenas com o catálogo. A V21 é a mais rápida para conferir a separação entre embeddings em cache e decisão.

O cache é indexado pelo hash do texto preparado. Trocar ID ou origem não muda a decisão; alterar o conteúdo exige preparação prévia de novos vetores. Não há tabela de temas corretos por ID.

## Refazer treino e avaliação de desenvolvimento

```bash
python3 testar_semantica_v21.py --saida experimentos/semantica_v21_reproduzida
python3 testar_semantica_v22.py --saida experimentos/semantica_v22_reproduzida
python3 testar_qualidade_v23.py --saida experimentos/qualidade_v23_reproduzida
```

Esses comandos leem as referências para treinar e avaliar dentro das partições e depois congelam a política antes de inferir o alvo. São diferentes dos comandos de inferência. O experimento V23 usa os resultados concluídos de V22 como controle de sugestões não supervisionadas; as sugestões são regeneradas pelo texto no runtime. Seus filtros herdados e a exposição prévia das referências impedem tratá-lo como confirmação independente.

## Preparação opcional do E5

Somente para reconstruir o cache, separadamente da decisão:

```bash
python3 -m pip install -r semantica_v21/requirements_preparacao.txt
python3 baixar_encoder_v21.py --saida modelos/e5_small
python3 preparar_semantica_verificada.py --modelo modelos/e5_small --saida artefatos/semantica_v21_regenerada
```

O download usa revisão e hashes fixos. A preparação não lê folha-verdade nem escolhe temas; gera vetores com prefixos, normalização e janelas documentadas. O custo executado de API foi US$ 0. A preparação levou cerca de 58 s e a inferência V21 nas 559, cerca de 15 s neste ambiente; o tempo no computador do candidato pode ser diferente. Os pesos não são distribuídos no ZIP.

## Histórico e rastreabilidade

Os arquivos anteriores estão preservados, inclusive as tentativas que pioraram os resultados. A documentação V18 anterior permanece em `historico/v18_documentacao/README.md`. A primeira execução V23 ficou incompleta por dependência ainda não concluída; está marcada como tal, com seu código original preservado. Os resultados válidos dessa etapa estão em `experimentos/qualidade_v23_002`. V22 concluiu a inferência com checkpoints recuperáveis e a escolha anterior preservada.

Não foram enviados e-mail nem alterações ao GitHub. A pasta é um conjunto de experimentos para conferir e decidir o próximo passo, com limites explícitos; não equivale a uma nova precisão jurídica comprovada.
