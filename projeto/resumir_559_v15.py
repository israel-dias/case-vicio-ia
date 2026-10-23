"""Relatório dos resultados salvos das 559; não classifica nem ajusta modelos."""
import argparse,json,csv
from collections import Counter
from pathlib import Path
from compatibilidade_v2 import features as f

def pct(v):return f'{100*v:.2f}%'.replace('.',',')
def media(rs):return sum(r['confianca'] for r in rs)/len(rs) if rs else None
def mesmo_ramo(a,b,temas):
    def ancestral(x,y):
        while y:
            if x==y:return True
            y=temas[y]['parent_id']
        return False
    return ancestral(a,b) or ancestral(b,a)
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    resumo=json.loads((saida/'resumo.json').read_text())
    ds=[json.loads(s) for s in (saida/'diagnostico_por_questao.jsonl').read_text().splitlines()]
    excl=set(json.loads((saida/'protocolo_previo.json').read_text())['ids_excluidos'])
    assert len(ds)==len({d['id'] for d in ds})==559 and not excl&{d['id'] for d in ds}
    with (projeto/'dados/anexos/temas.csv').open(encoding='utf-8-sig',newline='') as arq:
        temas={r['tema_id']:{'titulo':r['titulo'],'parent_id':r['parent_id']} for r in csv.DictReader(arq)}
    pub=[d for d in ds if d['decisao']=='publicar'];rev=[d for d in ds if d['decisao']=='revisar']
    perto=[d for d in rev if d['elegivel_foco_v15'] and .65<=d['confianca']<.7]
    altos=[d for d in rev if d['confianca']>=.7]
    candidatos=[d for d in ds if d['candidata_para_investigar']]
    alertas=[d for d in pub if d['publicacao_preservada_v11'] and (not d['elegivel_foco_v15'] or d['tema_central_id']!=d['tema_foco_v15'])]
    divergem_ramo=[d for d in alertas if not mesmo_ramo(d['tema_central_id'],d['tema_foco_v15'],temas)]
    falta_cmd=[d for d in rev if not d['rota']['cmd_usado']]
    cmd_neg=[d for d in falta_cmd if sum(x['contribuicao_logit'] for x in d['decomposicao_foco']['contribuicoes'] if x['atributo'].startswith('cmd_'))<0]
    ce=[d for d in rev if d['rota']['certo_errado']]
    ce_alt_neg=[d for d in ce if sum(x['contribuicao_logit'] for x in d['decomposicao_foco']['contribuicoes'] if x['atributo'].startswith('alt_'))<0]
    sem_itens=[d for d in rev if not d['rota']['itens_usados']]
    def soma_bloco(d,tipo):
        return sum(x['contribuicao_logit'] for x in d['decomposicao_foco']['contribuicoes']
                   if x['atributo'].startswith(tipo+'_') or tipo=='itens' and x['atributo']=='voto_itens')
    itens_neg=[d for d in sem_itens if soma_bloco(d,'itens')<0]
    cal=json.loads((projeto/'experimentos/roteamento_v15_002/modelos_finais.json').read_text())['foco_contextual']['calibrador']
    inclinacao=cal['coeficientes'][0]/cal['escala'][0]
    # A derivada da sigmoide é no máximo 1/4. Limite matemático descritivo
    # com calibrador fixo; não é nova regra de classificação validada.
    limite_alt=max((abs(soma_bloco(d,'alt'))*abs(inclinacao)/4 for d in ce),default=0)
    limite_itens=max((abs(soma_bloco(d,'itens'))*abs(inclinacao)/4 for d in sem_itens),default=0)
    controles={'revisoes_perto_corte_65_70':len(perto),'revisoes_com_confianca_70_ou_mais':len(altos),
        'revisoes_sem_comando_util':len(falta_cmd),'revisoes_sem_comando_com_bloco_cmd_negativo':len(cmd_neg),
        'revisoes_certo_errado':len(ce),'revisoes_certo_errado_com_bloco_alt_negativo':len(ce_alt_neg),
        'revisoes_sem_itens':len(sem_itens),'revisoes_sem_itens_com_bloco_itens_negativo':len(itens_neg),
        'limite_hipotetico_delta_confianca_bloco_alt_ce':limite_alt,
        'limite_hipotetico_delta_confianca_bloco_itens_ausentes':limite_itens,
        'preservadas_com_outro_ramo_sugerido_pelo_foco':len(divergem_ramo),
        'media_confianca_publicadas':media(pub),'media_confianca_revisadas':media(rev),
        'medias_sao_descritivas_nao_precisao_medida':True,
        'nao_altera_decisoes':True}
    (saida/'analise_complementar.json').write_text(json.dumps(controles,ensure_ascii=False,indent=2)+'\n')
    linhas=['# Teste nas 559 questões fora da folha-verdade','',
        'As 100 referências foram excluídas desta execução e de todos os totais abaixo. O modelo usa o aprendizado e a calibração anteriores; não houve novo treino. As 559 foram classificadas por código clássico, com rede, rótulos, treinamento, recalibração e escolha de limiares bloqueados.','',
        'Foram executadas as 12 configurações V15 congeladas. Todas reproduziram exatamente as decisões, os temas e as confianças salvas na rodada 002. Os dados sem rótulo não foram usados para escolher a variante que publica mais.','',
        '**Resultado da configuração principal: foco contextual, corte 70%, preservando V11.**','',
        '| Recorte | Publicar | Revisar | Fora | Cobertura |',
        '|---|---:|---:|---:|---:|']
    for nome,k in [('Antigas fora da referência','antigas_259'),('Recentes','recentes_300'),('Total','total_559')]:
        z=resumo['base_resultados'][k];linhas.append(f'| {nome}: {z["questoes"]} | {z["publicar"]} | {z["revisar"]} | 0 | {pct(z["cobertura"])} |')
    anterior=resumo['controle_v11']['total_559']
    linhas+=['',f'O controle V11 publicava {anterior["publicar"]}/{anterior["questoes"]} ({pct(anterior["cobertura"])}). A versão principal acrescenta {resumo["adicoes_sobre_v11"]} publicações. Não sabemos quantas dessas adições estão corretas. **A precisão real das 559 e dos 300 recentes não foi medida.** Nenhuma questão é marcada automaticamente como fora: ausência de suporte não prova ausência de tema.',
        '',f'A média das confianças registradas nas publicadas é {pct(media(pub))}. É uma média descritiva de decisões oriundas de diferentes vias e calibradores; não é precisão medida nem validação de uma probabilidade conjunta. Também não sustenta declarar 95% nas 559.','',
        '**Por que ficaram para revisão.** Motivos primários, sem dupla contagem:','',
        '| Motivo | Quantidade | Significado |','|---|---:|---|']
    exp={'confianca_abaixo_de_70':'O tema foi sugerido, mas o calibrador retornou menos de 70%. Não significa que a questão esteja errada.',
         'homonimo_com_escopo_nao_resolvido':'O código não distinguiu suficientemente os ramos homônimos.',
         'apoio_textual_abaixo_do_piso':'O candidato não atingiu o piso mínimo de apoio textual.',
         'conteudo_sem_evidencia':'A leitura não encontrou conteúdo informativo suficiente.'}
    for mot,n in resumo['motivos_primarios_revisao'].items():linhas.append(f'| {mot} | {n} | {exp[mot]} |')
    linhas+=['',f'Entre as revisadas, {len(perto)} são elegíveis e estão entre 65% e menos de 70%. Outras {len(altos)} têm confiança de pelo menos 70%, mas continuam bloqueadas. Aproximar-se do corte não prova que a sugestão está certa.','',
        '**O que a decomposição numérica mostrou.**','',
        f'- Das {len(falta_cmd)} revisões sem comando útil na rota, {len(cmd_neg)} têm contribuição total negativa do bloco de atributos do comando.',
        f'- Das {len(ce)} revisões de Certo/Errado, {len(ce_alt_neg)} têm contribuição negativa do bloco de alternativas, embora esse tipo de opção não contenha tema.',
        f'- Das {len(sem_itens)} revisões sem I/II/III, {len(itens_neg)} têm contribuição total negativa do bloco de itens.',
        '- Essas contribuições são calculadas após padronização, em logit, antes da calibração. Não são descontos fixos de pontos percentuais e não demonstram que remover o atributo melhoraria a precisão.',
        '- O detector preserva contexto, mas a representação ainda usa aproximações lexicais. Ele não resolve o conteúdo jurídico nem identifica a alternativa correta.',
        '', '| Atributo entre os cinco contrapesos mais negativos | Revisões em que aparece |',
        '|---|---:|']
    for n,k in list(resumo['contrapesos_entre_cinco_mais_negativos_em_revisoes'].items())[:10]:linhas.append(f'| {n} | {k} |')
    linhas+=['', 'A contagem acima tem sobreposição e não atribui causalidade individual. Uma contribuição negativa isolada pode coexistir com publicação.',
        '',f'**O tamanho do efeito importa:** no modelo atual, retirar hipoteticamente todo o contrapeso das alternativas C/E mudaria a confiança em no máximo {100*limite_alt:.3f} ponto percentual; o bloco de itens ausentes, em no máximo {100*limite_itens:.3f}. São limites matemáticos com calibrador fixo, não novas probabilidades validadas. Outros atributos do mesmo bloco podem compensar um contrapeso individual grande. Logo, a frequência dos sinais negativos não demonstra um grande bloqueio artificial: zerá-los não é a solução principal para a cobertura.', '',
        '**Comparação das variantes, somente nas 559.**','',
        '| Variante / corte / política | Publicar | Revisar | Cobertura |','|---|---:|---:|---:|']
    for nome,mp in resumo['comparacao_variantes'].items():
        z=mp['total_559'];linhas.append(f'| {nome} | {z["publicar"]} | {z["revisar"]} | {pct(z["cobertura"])} |')
    linhas+=['',f'Há {len(candidatos)} questões em revisão na configuração principal para as quais a fusão calibrada publica com o mesmo ID sugerido pelo foco e o foco está elegível. Estão em `candidatas_concordantes_NAO_LIBERADAS.csv`. **Não foram liberadas:** os métodos compartilham catálogo, atributos e histórico; sua concordância não é validação independente nem uma nova probabilidade calibrada.','',
        f'A preservação mantém {len(alertas)} publicações que recebem algum alerta do foco novo (outro ID sugerido ou inelegibilidade); em {len(divergem_ramo)} delas os IDs sugeridos estão em ramos distintos. São divergências entre métodos, **não erros demonstrados**. Pais e filhos do mesmo ramo são tratados como compatíveis nessa descrição. O arquivo `preservadas_com_alerta.csv` permite investigar sem apagar acertos antigos automaticamente.','',
        '**Melhorias recomendadas a partir deste diagnóstico.**','',
        '1. Melhorar a recuperação do conhecimento cobrado: preparar descrições gerais e termos discriminativos dos temas, com foco em conceitos e escopos, preservando as referências ao caso. Comparar o resultado antes de mudar a política. A atual leitura contextual ainda termina em aproximações lexicais; nenhum gabarito inferido por LLM deve escolher ou validar o tema.',
        '2. Esclarecer os escopos dos IDs homônimos. Sem essa informação, escolher o primeiro ID só encobre a dúvida.',
        '3. Revisar a política de preservação com uma regra de conflito entre ramos e uma avaliação rotulada. A preservação indiscriminada retém erros antigos; vetar toda discordância também pode retirar acertos. Não alterar a regra com base apenas no volume das 559.',
        '4. Usar a lista de concordância e as questões perto do corte como prioridade de uma pequena revisão especializada, registrando os rótulos novos. Não reduzir automaticamente o corte nem atribuir certeza à identificação de um título.',
        '5. Testar atributos condicionais para “não se aplica” e recalibrar antes de adotar, sem esperar grande ganho apenas removendo os contrapesos pequenos encontrados aqui. Medir as mudanças em referências novas e representativas, incluindo as 300 recentes. O conjunto sem rótulo permite examinar comportamento e cobertura; não comprovar a meta de 95%.','',
        '**Arquivos e reprodução.**','',
        '- `classificacoes_559.csv`: cada decisão, tema, confiança e motivo, com comparação entre foco e fusão.',
        '- `diagnostico_por_questao.jsonl`: as 559 questões completas, campos utilizados, cinco candidatos e decomposição numérica do foco.',
        '- `CASOS_PARA_CONFERIR.md`: exemplos completos fora das 100, selecionados por motivos observados, sem validação de gabarito.',
        '- `comparacao_variantes_559.csv`: as 12 configurações congeladas, sem os 100 IDs.',
        '- `resumo.json` e `analise_complementar.json`: totais estruturados; precisão real permanece nula.',
        '', 'O CSV oficial do case continua exigindo uma linha para cada uma das 659 questões. A exclusão dos 100 vale para esta análise e para a avaliação, não para remover suas linhas da entrega oficial. Este pacote não substitui `publicacao.csv` nem promove uma configuração nova.','']
    (saida/'LEITURA.md').write_text('\n'.join(linhas)+'\n')
    # Seleção automática por comportamento do programa, não pelo tema que o
    # assistente julgar correto. Não contém IDs excluídos.
    escolhas=[]
    def acrescentar(lista,n):
        if n<=0:return
        for d in lista:
            if d['id'] not in {x['id'] for x in escolhas}:escolhas.append(d);n-=1
            if n<=0:break
    acrescentar(sorted(perto,key=lambda d:-d['confianca']),3)
    acrescentar(sorted(altos,key=lambda d:-d['confianca']),2)
    acrescentar(sorted(candidatos,key=lambda d:-d['confianca_fusao_calibrada']),2)
    acrescentar(sorted(divergem_ramo,key=lambda d:-d['confianca']),2)
    acrescentar(sorted([d for d in pub if not d['publicacao_preservada_v11']],key=lambda d:-d['confianca']),2)
    acrescentar(sorted(rev,key=lambda d:-d['confianca']),max(0,10-len(escolhas)))
    escolhas=escolhas[:10]
    c=['# Dez exemplos fora das 100 referências','',
       'Selecionados por proximidade do corte, bloqueio, concordância ou divergência entre métodos. Os temas são sugestões do programa, sem rótulo de acerto conhecido. A decomposição é do foco V15, inclusive quando a decisão final vem da preservação V11.','']
    for d in escolhas:
        q=d['questao'];rota=d['rota'];comp=d['decomposicao_foco']
        c += [f'## {d["id"]} — {d["decisao"]} — {pct(d["confianca"])}','',
              f'**Tema final sugerido:** {d["tema_central_id"]} — {d["tema_caminho"]}.',
              f'**Motivo:** {d["motivo"]}. Preservado da V11: {d["publicacao_preservada_v11"]}.','',
              '**Enunciado:** '+f.visivel(q['enunciado_html']),'',
              '**Comando:** '+(q.get('comando') or '(vazio)'),'']
        c += [f'- **{a})** {f.visivel(t)}' for a,t in q['alternativas'].items()]
        c += ['',f'**Rota:** {rota["modo"]}; cabeçalho prioritário: {rota["cabecalho_prioritario"]}; retomada: {rota["comando_retoma_enunciado"]}; itens mantidos: {len(rota["itens_usados"])}.',
              f'**Foco novo:** tema {d["tema_foco_v15"]}, confiança {pct(d["confianca_foco_v15"])}, elegível {d["elegivel_foco_v15"]}.',
              f'**Fusão calibrada preservada:** tema {d["tema_fusao_calibrada"]}, confiança {pct(d["confianca_fusao_calibrada"])}, decisão {d["decisao_fusao_calibrada"]}.','',
              '| Candidato do foco | Caminho | Escore de busca (não probabilidade) |','|---|---|---:|']
        for z in d['top5_foco']:c.append(f'| {z["tema_id"]} | {z["caminho"]} | {z["escore_recuperacao"]:.6f} |')
        c+=['','| Contrapeso do foco | Valor do atributo | Contribuição em logit |','|---|---:|---:|']
        for z in comp['contrapesos_maiores']:c.append(f'| {z["atributo"]} | {z["valor"]:.6f} | {z["contribuicao_logit"]:.6f} |')
        c+=['','Esses sinais explicam o cálculo, sem demonstrar se a sugestão temática está certa.','']
    (saida/'CASOS_PARA_CONFERIR.md').write_text('\n'.join(c)+'\n')
    print(json.dumps(controles,ensure_ascii=False,indent=2))
    return controles
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
