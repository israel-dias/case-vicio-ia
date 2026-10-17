"""Registra revisão assistida explícita do piloto; não mede precisão jurídica."""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from vicio_ia.arquivos import carregar_json, gravar_json, sha256
from vicio_ia.importacao import validar_resposta
from vicio_ia.temas import mesmo_ramo, validar_temas


PARECERES = {
    "Q0017": ("recomendar_revisar", "Conflito de escopo: a questão trata do rito de crimes funcionais; o ID 5533 tem pai Procedimento Ordinário. A v2 reconhece o conflito e ainda sugere publicar. O CPP situa os arts. 513 a 518 entre processos especiais. Manter a sugestão de tema como hipótese e não liberar por coincidência de título.", "CPP, art. 514 e Título II"),
    "Q0029": ("fundamentar_desempate", "O conteúdo se concentra em crimes da Lei 13.869/2019; há IDs 4684 e 6716. A orientação de Carla permite uma escolha fundamentada, mas não fornece equivalência. Registrar critério do objeto e do ramo antes de liberar; não usar o assunto Medida de Segurança como rótulo.", "Conteúdo e catálogo do case"),
    "Q0035": ("manter_candidata", "O enunciado e as alternativas delimitam expressamente Lei Antiterrorismo e há tema específico 4706. Manter como candidata à conferência, sem tratar concordância das rodadas como gabarito.", "Conteúdo e catálogo do case"),
    "Q0036": ("fundamentar_desempate", "Há interação entre audiência do art. 16, Lei Maria da Penha e ação penal. Não basta citar o nome da lei; comparar o objeto processual e os caminhos 4704/6724 e eventuais temas de ação penal. A orientação da empresa não confirma um desses IDs.", "Conteúdo e catálogo do case"),
    "Q0058": ("manter_revisao", "4390 e 4377 não são ancestral/descendente. O conjunto trata de seletividade, pobreza, vitimização e criminalização. Não fixar o núcleo por uma alternativa isolada. O extra 4390 da v2 também requer confirmação do papel efetivamente cobrado.", "Conteúdo e catálogo do case"),
    "Q0059": ("manter_revisao", "A v2 trocou teorias criminológicas por teorias legitimidoras da pena para uma pergunta sobre a crítica de Baratta ao cárcere. Crítica e legitimação não devem ser aproximadas só por menção à pena. O catálogo não fornece definição suficiente para validar a troca; comparar teorias sociológicas e política criminal.", "Conteúdo e catálogo do case"),
    "Q0069": ("manter_candidata", "O enunciado pergunta expressamente por interpretação da norma penal; o tema 5173 corresponde ao objeto. Manter candidata; comando vazio não impediu a identificação da instrução.", "Conteúdo e catálogo do case"),
    "Q0090": ("manter_revisao", "5530 é pai de 5532. A mudança é de granularidade dentro do mesmo ramo, mas as alternativas abrangem procedimentos distintos. O pai ordinário não absorve automaticamente todo procedimento especial ou sumaríssimo.", "Conteúdo e catálogo do case"),
    "Q0106": ("manter_candidata", "O objeto é enquadramento de conduta patrimonial ligada a refeição sem pagamento. O art. 176 está no título de crimes contra o patrimônio. O catálogo não explicita Outras fraudes; 5157 é pai substantivo plausível. Não estender automaticamente o ID Estelionato a todo o capítulo de fraudes.", "Código Penal, título II e art. 176"),
    "Q0116": ("manter_revisao", "A pergunta abrange disposições diferentes da Lei de Drogas; o título Tráfico de Drogas é mais estreito e há dois ramos concorrentes. Distinguir dúvida de escopo e de ID. A confiança 0,97 não resolve esses dois problemas.", "Conteúdo e catálogo do case"),
    "Q0164": ("fundamentar_desempate", "O conteúdo assistencial está na LEP. Contudo, o ID 6734 continua ativo em Processo Penal e foi omitido entre os concorrentes da v2. Antes de manter publicação, registrar por que 4703 representa melhor este objeto. A LEP confirma o assunto, não a preferência taxonômica da empresa.", "LEP, arts. 10 a 27; catálogo do case"),
    "Q0171": ("manter_revisao", "O enunciado é sobre Pacote Anticrime e as alternativas cobrem pena, hediondos, colaboração, perfis genéticos e prescrição/ANPP. Tanto 4693 quanto 5185 representam apenas parte do conjunto. A menção à prescrição existe na alternativa E, mas isso não demonstra que seja o tema central.", "Conteúdo e catálogo do case"),
    "Q0193": ("manter_candidata", "O enunciado e todas as alternativas delimitam colaboração premiada; 5557 é específico. Não substituir esse núcleo pelo assunto de origem Inquérito Policial.", "Conteúdo e catálogo do case"),
    "Q0195": ("manter_candidata", "O enunciado delimita comparação de correntes e escolas criminológicas, e 4373 representa esse conjunto. A candidatura é sustentada pelo conjunto, não por uma palavra de alternativa isolada.", "Conteúdo e catálogo do case"),
    "Q0218": ("manter_candidata", "As alternativas perguntam pela classificação/legalidade da prisão em flagrante: 5518 corresponde ao núcleo. O documento falso é contexto narrativo e não deve desviar o tema central.", "Conteúdo e catálogo do case"),
    "Q0277": ("fundamentar_desempate", "O objeto são crimes previstos no Estatuto da Pessoa Idosa, apesar de metadados de Direito Civil. Os IDs 4696 e 6722 têm grafias diferentes e sobreposição aparente. Registrar a escolha pelo conteúdo e ramo, sem corrigir ou fundir IDs nos anexos.", "Conteúdo e catálogo do case"),
    "Q0299": ("recomendar_revisar", "O enunciado é genérico e as alternativas comparam criminologia crítica, positivismo, retribuição, labelling e finalismo. A v2 sustenta a publicação sobretudo na alternativa sobre labelling. O tema 4388 pode ser hipótese, mas falta justificar o enquadramento da comparação inteira; confiança 0,90 não é prova.", "Conteúdo e catálogo do case"),
    "Q0302": ("manter_candidata", "A narrativa e as alternativas delimitam erro sobre circunstância fática e efeitos no dolo. O tema Erro de Tipo 5224 é candidato específico. Não confundir a confirmação do tópico com resolução de todos os aspectos do caso.", "Conteúdo e catálogo do case"),
    "Q0303": ("manter_revisao", "5180 é pai de 5182, portanto a troca não é necessariamente erro de ramo. O pai pode representar a combinação de conteúdos temporais e espaciais; o filho Espaço não cobre por si só todas as alternativas. Registrar avaliação do escopo antes da decisão final.", "Conteúdo e catálogo do case"),
    "Q0309": ("fundamentar_desempate", "A pergunta pede sanção de dispositivo da Lei 9.605/1998, sustentando o núcleo de crime ambiental. O nome Direito Ambiental na origem não significa fora. Justificar a preferência entre 4688/6717 pelo objeto penal e caminho, sem declarar equivalência recebida da empresa.", "Conteúdo e catálogo do case"),
}


def revisar(projeto, v1_path, v2_path, comparacao_path, saida):
    pasta = projeto / "lotes_v1/piloto"
    manifesto = carregar_json((pasta / "manifesto.json").read_text(encoding="utf-8"))
    temas_path = pasta / "temas_ativos.json"
    if sha256(temas_path) != manifesto["sha256_temas"]:
        raise ValueError("Catálogo diferente do registrado no piloto.")
    temas = validar_temas(carregar_json(temas_path.read_text(encoding="utf-8")))
    ativos = {i for i, t in temas.items() if t["status"] == "active"}
    ler_resposta = lambda p: {r["id"]: r for r in validar_resposta(
        carregar_json(p.read_text(encoding="utf-8-sig")), manifesto["ids"], ativos)}
    v1, v2 = ler_resposta(v1_path), ler_resposta(v2_path)
    comparacao = carregar_json(comparacao_path.read_text(encoding="utf-8-sig"))
    linhas = comparacao["comparacoes"]
    if len(linhas) != len(v1) or len({x["id"] for x in linhas}) != len(v1):
        raise ValueError("Comparação com omissões ou duplicatas.")
    if set(v1) != set(PARECERES) or {x["id"] for x in linhas} != set(v1):
        raise ValueError("Os pareceres documentados são específicos aos vinte IDs deste piloto.")
    for x in linhas:
        if x["id"] not in v1:
            raise ValueError("ID estranho na comparação.")
        a, b = v1[x["id"]], v2[x["id"]]
        for campo, alias in [("sugestao_decisao", "sugestao"), ("tema_central_id", "tema"),
                             ("justificativa", "justificativa"), ("alertas", "alertas")]:
            if x[alias+"_v1"] != a[campo] or x[alias+"_v2"] != b[campo]:
                raise ValueError(f"Comparação não corresponde às respostas: {x['id']} {alias}")
        for versao, r in (("v1", a), ("v2", b)):
            esperado = temas[r["tema_central_id"]]["caminho"] if r["tema_central_id"] else None
            if x["caminho_"+versao] != esperado:
                raise ValueError("Caminho da comparação difere do catálogo.")
        parentesco = (mesmo_ramo(a["tema_central_id"], b["tema_central_id"], temas)
                      if a["tema_central_id"] and b["tema_central_id"] else None)
        if x["temas_no_mesmo_ramo"] != parentesco:
            raise ValueError("Relação entre temas inconsistente na comparação.")
        if (x["mudou_sugestao"] != (a["sugestao_decisao"] != b["sugestao_decisao"])
                or x["mudou_tema_central"] != (a["tema_central_id"] != b["tema_central_id"])):
            raise ValueError("Indicadores da comparação inconsistentes.")
    contagem = lambda rs: {d: sum(r["sugestao_decisao"] == d for r in rs.values())
                           for d in ("publicar", "revisar", "fora")}
    md = [x["id"] for x in linhas if x["mudou_sugestao"]]
    mt = [x["id"] for x in linhas if x["mudou_tema_central"]]
    if (comparacao["questoes"] != 20 or comparacao["sugestoes_v1"] != contagem(v1)
            or comparacao["sugestoes_v2"] != contagem(v2)
            or comparacao["mudancas_sugestao"] != len(md)
            or comparacao["mudancas_tema_central"] != len(mt)):
        raise ValueError("Resumo da comparação inconsistente com seus dados.")
    revisoes = []
    for i in sorted(v1):
        encaminhamento, parecer, referencia = PARECERES[i]
        revisoes.append({"id": i, "resposta_v1": v1[i], "resposta_v2": v2[i],
                         "encaminhamento_assistido": encaminhamento,
                         "parecer_assistido": parecer, "referencia": referencia,
                         "rotulo_juridico_validado": None, "confianca_final": None})
    resumo = {"fase": "revisao_assistida_do_piloto_de_desenvolvimento",
              "verificado_em_utc": datetime.now(timezone.utc).isoformat(),
              "questoes": len(revisoes), "sugestoes_v1": contagem(v1), "sugestoes_v2": contagem(v2),
              "ids_mudanca_decisao": md, "ids_mudanca_tema": mt,
              "ids_com_alguma_mudanca": sorted(set(md) | set(mt)),
              "encaminhamentos_assistidos": dict(Counter(r["encaminhamento_assistido"] for r in revisoes)),
              "precisao_medida": None, "referencia_juridica_independente": False,
              "publicacao_final": False,
              "origem_pareceres": "Assistente nesta conversa, com dados, contexto prévio e referências pontuais; não especialista independente.",
              "nota": "Encaminhamentos não alteram JSONs originais nem constituem classificações finais.",
              "entradas_sha256": {"resposta_v1": sha256(v1_path), "resposta_v2": sha256(v2_path),
                                  "comparacao": sha256(comparacao_path), "catalogo": sha256(temas_path)},
              "revisoes": revisoes}
    if saida.exists() and any(saida.iterdir()):
        raise ValueError("Destino não vazio; escolha nova pasta para preservar a revisão.")
    saida.mkdir(parents=True, exist_ok=True)
    gravar_json(saida / "revisao.json", resumo)
    texto = ["# Revisão assistida do piloto v1/v2", "",
             "Estado: pareceres de desenvolvimento, não gabarito, auditoria independente ou publicação final.", "",
             "## Resultados reais recebidos", "",
             "- v1: 7 candidatas a publicar, 13 para revisar, 0 fora.",
             "- v2: 10 candidatas a publicar, 10 para revisar, 0 fora.",
             f"- Mudanças de decisão: {', '.join(md)}.",
             f"- Mudanças de tema: {', '.join(mt)}.",
             f"- Questões distintas com alguma mudança: {len(set(md) | set(mt))}.",
             "- Precisão jurídica: não medida. Mais candidatas não demonstram melhoria.", "",
             "## Encaminhamentos propostos", "",
             "Sete candidaturas podem seguir à conferência; oito casos têm recomendação de revisão e cinco",
             "exigem fundamentar o desempate. Estes são estados de trabalho, não decisões finais de entrega.", "",
             "| Questão | Decisão v1 → v2 | Tema v1 → v2 | Encaminhamento assistido |",
             "|---|---|---|---|"]
    for r in revisoes:
        a, b = r["resposta_v1"], r["resposta_v2"]
        texto.append(f"| {r['id']} | {a['sugestao_decisao']} → {b['sugestao_decisao']} | "
                     f"{a['tema_central_id']} → {b['tema_central_id']} | {r['encaminhamento_assistido']} |")
    texto += ["", "## Parecer por questão", ""]
    for r in revisoes:
        texto += [f"### {r['id']}", "", r["parecer_assistido"], "",
                  "Base de inspeção: " + r["referencia"] + ".", ""]
    texto += ["## Premissas e limites", "",
              "A orientação de Carla, recebida em 15/10/2026, pede considerar conteúdo, ramo jurídico e",
              "premissas consistentes. Não fornece equivalências de IDs. O caminho completo é relevante.", "",
              "Q0017: o CPP inclui o rito funcional entre processos especiais, enquanto o catálogo coloca",
              "5533 sob Procedimento Ordinário. Isso sustenta revisão do encaixe, não uma alteração da árvore.", "",
              "Q0106: o art. 176 consta no título de crimes contra o patrimônio, sustentando o ramo 5157.", "",
              "Q0164: a LEP sustenta o objeto assistencial, mas não o desempate 4703/6734 da plataforma.", "",
              "Q0303: a mudança é entre pai e filho; não contabilizar como erro confirmado.", "",
              "Os números de confiança das respostas não foram calibrados. A mesma IA rever seu resultado",
              "não cria uma referência independente. Mudaram prompt, contexto e possivelmente modelo.", "",
              "## Referências primárias consultadas em 15/10/2026", "",
              "- [CPP: processos especiais e art. 514](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm)",
              "- [Código Penal: título patrimonial e art. 176](https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm)",
              "- [LEP: assistência, arts. 10 a 27](https://www.planalto.gov.br/ccivil_03/leis/l7210.htm)", "",
              "As fontes legais não certificam IDs, não resolvem todas as alternativas e não são os rótulos ocultos da avaliação.", "",
              "## Próxima execução", "",
              "Usar os lotes v3 com as 339 questões restantes. O piloto permanece separado para consolidar",
              "suas vinte decisões com registro das intervenções. Preservar as duas respostas recebidas.", ""]
    (saida / "REVISAO_ASSISTIDA.md").write_text("\n".join(texto), encoding="utf-8")
    return {k: resumo[k] for k in ("questoes", "encaminhamentos_assistidos", "precisao_medida", "publicacao_final")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, default=Path.cwd())
    p.add_argument("--v1", type=Path, default=Path("piloto-resposta-v1.json"))
    p.add_argument("--v2", type=Path, default=Path("piloto-resposta-v2.json"))
    p.add_argument("--comparacao", type=Path,
                   default=Path("analises/comparacao_v1_v2/comparacao.json"))
    p.add_argument("--saida", type=Path, default=Path("analises/revisao_piloto_v3"))
    a = p.parse_args()
    try:
        resultado = revisar(a.projeto, a.v1, a.v2, a.comparacao, a.saida)
    except (ValueError, KeyError, OSError) as exc:
        p.exit(2, f"Erro: {exc}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
