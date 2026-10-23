"""Texto do relatório a partir das métricas, sem julgamento de questões novas."""
import json


def pct(valor):
    return "indefinida" if valor is None else f"{100 * valor:.2f}%"


def p(texto):
    return {"tipo": "paragrafo", "texto": texto}


def h(texto):
    return {"tipo": "subtitulo", "texto": texto}


def tabela(cabecalho, linhas):
    return {"tipo": "tabela", "cabecalho": cabecalho, "linhas": linhas}


def documento(resumo, politica, metodo, teste, classificacao):
    final = resumo["fora_folha_verdade"]; cal = politica["confianca_por_decisao"]
    te = teste["teste"]; dev = metodo["metricas_desenvolvimento"]
    proje = resumo["producao_cenario"]
    intervalo = resumo["previsao"]["precisao_intervalo"]
    paginas = [
        {"titulo": "O sistema e as escolhas", "rotulo": "01 / SISTEMA", "blocos": [
            p("Objetivo: classificar 659 questões, publicar apenas os casos selecionados por uma regra explícita e encaminhar as dúvidas à revisão. A decisão é cálculo local sobre textos, catálogo e parâmetros versionados; nenhum modelo de linguagem escolhe ou valida o tema na inferência."),
            h("Peça por peça"),
            p("A preparação remove HTML e scripts, preserva negação, comando e alternativas e evita repetir o comando já presente no enunciado. IDs e disciplina de origem não são atributos. Assunto de origem tem peso de apoio de 10% no score final; pode estar errado e não funciona como filtro obrigatório."),
            p("O ranking combina TF-IDF de palavras/bigramas, fragmentos de palavras e um índice separado de escopos propostos. Os pesos foram escolhidos no desenvolvimento. A árvore agrega a média dos três maiores scores disponíveis do pai e dos filhos imediatos e sugere temas de nível 1. Não usa disciplinas raiz. Isso perde especificidade, mas respeita o aceite de ancestrais; não funde ramos homônimos."),
            p(f"A política exige escopo proposto, score mínimo 0,05 e margem relativa (primeiro - segundo)/primeiro >= {politica['limiar_margem']:.6f}. O corte foi escolhido na calibração. Extras ficam vazios: candidatos do top5 não comprovam conteúdos adicionais. Sem evidência recuperável, uma nova importação é rejeitada para triagem, sem inventar tema."),
            h("Experimentos no desenvolvimento; mesma reserva preservada"),
            tabela(["Alternativa", "Top1 / 60", "Decisão"], [
                ["Baseline lexical", "28", "Referência inicial"],
                ["Pesos de campos, texto e catálogo", "35", "Manter texto completo e apoio do assunto"],
                ["Embedding genérico multilíngue", "7", "Descartado nesta representação"],
                ["Lexical com vizinho rotulado", "36", "Ganho pequeno; não escolhido"],
                ["Escopos separados + média da família", str(dev['acertos_top1']), "Método congelado"],
            ]),
            p("O encoder ensaiado foi paraphrase-multilingual-MiniLM-L12-v2, em ONNX quantizado. O resultado ruim não demonstra que embeddings sejam inadequados em geral. A separação forte de campos e outras combinações também pioraram. Os resultados e o código dos ensaios permanecem no histórico; não se escolheu modelo pelo preço ou complexidade."),
            p("Autoria assistida: ChatGPT nesta conversa propôs código e 360 descrições; 11 recortes permaneceram sem escopo. Modelo exato e tokens internos não registrados. Não houve validação jurídica independente das descrições. O runtime usa somente biblioteca padrão e não lê rótulos."),
        ]},
        {"titulo": "Rótulos, decisão e previsão", "rotulo": "02 / EVIDÊNCIA", "blocos": [
            p("A divisão original foi mantida: 60 questões para escolher a representação e propor cortes, 20 para escolher o corte e estimar confiança, 20 para avaliar a política fixa. Os 100 rótulos já apareceram na conversa antes da reserva computacional; não é avaliação externa totalmente cega. Duplicatas textuais exatas entre grupos são rejeitadas; paráfrases não são totalmente controladas."),
            tabela(["Grupo", "Acerto top1", "Publicadas certas", "Uso"], [
                ["Desenvolvimento", f"{dev['acertos_top1']}/60", f"{politica['escolha']['dev_acertos']}/{politica['escolha']['dev_publicadas']}", "Escolha da representação"],
                ["Calibração", f"{cal['publicar']['acertos'] + cal['revisar']['acertos']}/20", f"{cal['publicar']['acertos']}/{cal['publicar']['avaliadas']}", "Escolha do corte e confiança"],
                ["Teste fixo", f"{te['acertos_top1_todas']}/20", f"{te['acertos_publicadas']}/{te['publicar']}", "Medição sem ajuste posterior"],
            ]),
            p("O desenvolvimento propôs cortes com pelo menos cinco publicações e 95% de acerto empírico. A calibração escolheu a maior cobertura com pelo menos três publicações e a mesma meta; os mínimos evitam suporte de um único exemplo, mas não certificam precisão. Todos os cortes considerados estão registrados. O corte e a confiança não foram ajustados depois do teste."),
            p(f"Confiança do grupo publicar: {cal['publicar']['media_beta_1_1']:.4f}; revisar: {cal['revisar']['media_beta_1_1']:.4f}. São médias Beta(1 + acertos, 1 + erros) usando somente a calibração. A estimativa é comum a cada grupo, não uma probabilidade individual bem demonstrada. Similaridade e margem não são probabilidades."),
            p(f"No teste: cobertura {pct(te['cobertura'])}, precisão observada das publicadas {pct(te['precisao_publicadas'])}. São apenas {te['publicar']} publicadas. O limite inferior unilateral de 95% é {te['limite_inferior_unilateral_95']:.4f}; o resultado não comprova precisão mínima de 95%. Brier em todas as sugestões: {te['brier_todas']:.4f}."),
            h("Entrega e autoavaliação para a empresa"),
            p(f"Fora da folha-verdade: {final['questoes']} questões, {final['decisoes']['publicar']} publicar, {final['decisoes']['revisar']} revisar e {final['decisoes']['fora']} fora. Cobertura exata: {pct(final['cobertura'])}. A precisão real permanece desconhecida. A confiança da calibração sustenta previsão pontual de {pct(resumo['previsao']['precisao_prevista'])}; faixa de sensibilidade {pct(intervalo[0])} a {pct(intervalo[1])}, informada com suas hipóteses."),
            p("A faixa deriva do intervalo binomial do teste, ampliado se necessário para conter a previsão fixada. Não é garantia de cobertura estatística na distribuição nova. As 300 questões recentes não têm rótulos disponíveis e todos os 100 exemplos são antigos. A cobertura é calculada sobre as 559 decisões conhecidas, com intervalo limitado ao arredondamento; não é uma projeção para qualquer semana futura."),
            p("A régua considera central, extras e ancestrais/descendentes da mesma cadeia; irmãos não são equivalentes por padrão. As oito marcações oficiais de fora foram preservadas, mesmo quando há vocabulário semelhante ao catálogo. Não se usa gabarito de prova ou classificação da etapa 1 como verdade de treinamento."),
        ]},
        {"titulo": "Diagnóstico e operação semanal", "rotulo": "03 / PRODUÇÃO", "blocos": [
            h("Limitações que ainda causam erro"),
            p("Nomes repetidos em ramos diferentes, descrições importadas pouco informativas e recortes como Parte 01/02 sem escopo tornam a árvore ambígua. Contexto narrativo e distratores podem dominar a similaridade, sem representar o conhecimento cobrado. No desenvolvimento, Q0202 ilustra essa troca: a referência é Erro de Tipo, mas o contexto atrai outro ramo. Assertivas I/II/III podem exigir mais de um conteúdo, inclusive para reconhecer proposições falsas."),
            p("São necessários escopos positivos e negativos curtos, critérios claros de fora e exemplos revisados de fronteira. Q0291 e Q0043, do desenvolvimento, têm correspondências lexicais plausíveis e referência oficial fora: isso pede esclarecer a convenção, não substituir o rótulo por opinião. Baixa similaridade não prova fora; esta versão não descarta questões automaticamente."),
            h("50 mil questões por semana: cálculo barato, revisão cara"),
            tabela(["Cenário", "Estimativa"], [
                ["Classificação CPU, projeção linear", f"{proje['tempo_classificacao_50000_segundos']:.2f} s / 50.000"],
                ["API de classificação", "US$ 0; nenhuma chamada"],
                ["Compute a US$ 0,05/h (hipótese)", f"US$ {proje['custo_compute_usd']:.6f}; US$ {proje['custo_compute_por_questao_usd']:.9f}/questão"],
                ["Revisões se a cobertura se repetir", f"{proje['revisoes_50000']:.0f} por semana"],
                ["A 2 min/revisão (hipótese)", f"{proje['horas_revisao_cenario']:.1f} horas por semana"],
            ]),
            p(f"A projeção parte de {classificacao['tempos_segundos']['classificacao']:.4f} s para classificar as 659 questões no ambiente registrado. Não é medição de 50 mil questões únicas nem preço cotado de nuvem. Benchmark repetido é opcional e separado. Custos de armazenamento, operação e pessoas não estão incluídos. Assinatura ChatGPT existente não rateada; custo humano e tempo total de desenvolvimento não instrumentados."),
            p("A baixa cobertura é uma limitação central desta versão: a fila projetada não é sustentável com poucos professores. Antes de produção, ampliar rótulos recentes e de fronteira, definir escopos e medir ganhos de um classificador hierárquico ou ranqueador supervisionado. Somente liberar uma versão que demonstre o equilíbrio requerido entre precisão e cobertura em dados novos."),
            h("Fluxo e aprendizado com o professor"),
            p("Importar em área de preparação; validar HTML, campos e duplicatas; executar a versão congelada; publicar selecionadas; priorizar revisão por conflito e novidade. Salvar correção, justificativa, versão da árvore e origem da prova. Reportes dos alunos viram tickets; uma amostra aleatória das publicadas também é auditada para medir erros que não chegam por reporte."),
            p("Consolidar correções semanalmente. Treinar e recalibrar uma candidata quando houver novo lote de rótulos suficiente para os ramos afetados, inicialmente em revisão mensal; antecipar se houver deriva ou mudança da árvore. Separar treino e teste por concurso/tempo, manter uma reserva recente e comparar em sombra. Atualizar calibrador após o ranking; implantar só com qualidade sustentada e possibilidade de retorno à versão anterior."),
        ]},
        {"titulo": "Memo para o professor", "rotulo": "04 / DECISÕES DE CONTEÚDO", "blocos": [
            p("Professor(a), o objetivo é que a questão apareça no assunto que o aluno precisa conhecer para resolvê-la. Citar uma lei no contexto ou em uma alternativa não basta para definir esse assunto. A solução oferece um tema e separa casos com maior ou menor evidência; ela não substitui sua definição dos limites do catálogo."),
            h("O que encontrei"),
            p("O catálogo contém nomes semelhantes em ramos distintos e descrições que não delimitam o conteúdo. Onze recortes ficaram sem descrição proposta. Também existem questões com vários assuntos efetivamente cobrados e outras em que os temas das alternativas servem apenas para distrair. A máquina ainda pode confundir esses casos."),
            p(f"Nas {final['questoes']} questões avaliadas pela empresa, o sistema separou {final['decisoes']['publicar']} para publicação e {final['decisoes']['revisar']} para revisão. A precisão dessas publicações ainda não foi medida. O teste disponível acertou {te['acertos_publicadas']} publicadas, mas o número é pequeno para assegurar a meta. O volume restante mostra que a solução precisa evoluir antes de operar com 50 mil questões semanais."),
            h("O que recomendo mudar nos temas"),
            p("Para cada tema, registrar em poucas linhas: o que entra, o que não entra e como decidir nos limites com o tema vizinho. Nos títulos iguais, explicar por que há ramos diferentes e se existe conteúdo compartilhado. Não mesclar IDs automaticamente. Nos títulos Parte 01/02, escrever o recorte real."),
            p("Definir quando uma questão é fora mesmo havendo uma correspondência ampla na árvore. Explicar central e extras em questões com assertivas independentes. Não adicionar como extra todo assunto mencionado nos distratores; adicionar quando o conhecimento é necessário para julgar a questão."),
            h("De que preciso de você"),
            p("Priorizar uma amostra de fronteiras e questões recentes, em vez de começar lendo toda a fila. Pedir decisões acompanhadas de uma frase sobre o conteúdo exigido. Esclarecer os recortes sem descrição e os exemplos Q0291/Q0043, rotulados como fora, para que o sistema aprenda a convenção da plataforma sem alterar silenciosamente as referências."),
            p("Cada correção deve virar um exemplo de treinamento com o motivo registrado. Reservar também uma pequena amostra aleatória das publicadas para auditoria: só revisar o que a máquina já considera difícil esconderia erros confiantes. Com esses dados, poderemos aumentar a publicação gradualmente e medir se a precisão continua adequada."),
            p("Não houve validação jurídica independente dos escopos propostos nesta entrega. A aprovação estrutural do código e a reprodução do CSV não certificam o enquadramento jurídico. A contribuição principal desta versão é tornar a regra e suas limitações inspecionáveis e reproduzíveis."),
        ]},
    ]
    return {"titulo": "Case Vício IA - etapa complementar", "autor": "Israel Dias",
            "edicao": "Política congelada após desenvolvimento e calibração; teste sem ajustes",
            "paginas": paginas,
            "fontes": ["Enunciado e anexos oficiais: https://github.com/viciod/case-vicio-ia",
                       "NIST, intervalo binomial: https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm"],
            "nota_paginas": "O PDF gerado a partir deste documento contém quatro páginas, incluindo este memo."}


def markdown(doc):
    linhas = [f"# {doc['titulo']}", "", f"**{doc['autor']}**", "", doc["edicao"], ""]
    for i, pagina in enumerate(doc["paginas"], 1):
        linhas += [f"## {i}. {pagina['titulo']}", ""]
        for bloco in pagina["blocos"]:
            if bloco["tipo"] == "subtitulo":
                linhas += [f"### {bloco['texto']}", ""]
            elif bloco["tipo"] == "tabela":
                linhas += ["| " + " | ".join(bloco["cabecalho"]) + " |",
                           "| " + " | ".join("---" for _ in bloco["cabecalho"]) + " |"]
                linhas += ["| " + " | ".join(map(str, row)) + " |" for row in bloco["linhas"]]
                linhas += [""]
            else:
                linhas += [bloco["texto"], ""]
        if i != len(doc["paginas"]):
            linhas += ["<!-- Quebra de página no PDF -->", ""]
    linhas += ["Fontes: " + " | ".join(doc["fontes"]), ""]
    return "\n".join(linhas)
