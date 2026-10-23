"""Testa comando estrito, passagens integrais e preferência por pares."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from isolamento_v17.metricas import medir,curva_descritiva
from testar_isolamento_v17 import gravar,csv_salvar,sub,controle,dependencias
from contexto_v18 import modelo as m


def trocas(novas,base):
    b={r['id']:r for r in base}
    if {r['id'] for r in novas}!=set(b):
        raise ValueError('Conjuntos diferentes na comparação.')
    alteradas=[r for r in novas if r['tema_central_id']!=b[r['id']]['tema_central_id']]
    c=[r['id'] for r in alteradas if r['correto'] and not b[r['id']]['correto']]
    e=[r['id'] for r in alteradas if not r['correto'] and b[r['id']]['correto']]
    return {'temas_trocados':len(alteradas),'erros_corrigidos':len(c),'acertos_prejudicados':len(e),
            'ids_corrigidos':c,'ids_prejudicados':e,
            'ativacoes_comando':sum(r['identificador_forte_cmd'] for r in novas),
            'narrativas_excluidas':sum(r['narrativa_excluida'] for r in novas)}


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True)
    deps=dependencias(projeto);dados=projeto/'dados/anexos'
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt','experimentos/isolamento_v17_001/resumo.json']}
    gravar(saida/'protocolo_previo.json',{
        'versao':'contexto_v18_1','variantes':m.VARIANTES,'atributos':m.ATRIBUTOS,
        'comando_estrito':'Identificador textual específico do catálogo, incluindo flexões superficiais e expressão composta próxima; comando+alternativas temáticas, narrativa e metadados zerados. Sem identificador, mantém texto integral.',
        'normas':'Citação isolada não ativa. Título normativo, norma específica ou artigo com código podem ativar se repetidos no enunciado. CP/CPP sozinhos são genéricos.',
        'identificadores':'Conserva todos os ramos dos títulos; não resolve homônimos pelo primeiro ID. Ativação não significa confiança mínima nem aprovação.',
        'passagens':'Frases vizinhas com antecedente, cabeçalho com cada proposição, todas as proposições preservadas. Relações de desconhecimento e papéis extraídas como texto, sem resposta nem regra de tema obrigatório.',
        'ranking_estrito':{'fusao_texto_reduzido':.65,'identificador':.35},
        'ranking_com_apoio':{'fusao_integral':.60,'cobranca':.25,'passagens':.15},
        'candidatos':'União top5 fusão e ranking novo, top3 comando, passagens e identificadores. Sem consulta ao rótulo para inserir o positivo.',
        'pares':'Somente candidatos recuperados com rótulo aceito versus concorrentes não aceitos; sem pares quando não há positivo ou há fora. Regressão logística simétrica C=.3, sem intercepto, escalas sem centrar.',
        'calibracao':'Calibra o candidato realmente escolhido sobre previsões internas fora do ajuste. Corte interno com precisão empírica >=95%, suporte >=10. Sem corte por tamanho ou confiança fixa.',
        'avaliacao':'Cinco folds externos originais e quatro internos; duplicatas agrupadas. Seleção interna antes de olhar rótulos externos.',
        'exposicao':'100 referências e exemplos já vistos; desenvolvimento exposto, não novo teste cego.',
        'projeto_sha256':deps,'dados_sha256':{n:sha(dados/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'promove_entrega':False})
    qs,temas,ys=f.carregar(dados)
    if (len(qs),len(temas),len(ys))!=(659,377,100):raise ValueError('Anexos inesperados.')
    cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    print('Preparando as 100 referências: comando, texto integral e passagens.',flush=True)
    pp=m.preparar(cat,dic,sub(qs,ys))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    externas={v:[] for v in [*m.VARIANTES,'selecionado_internamente']};raw={v:[] for v in m.VARIANTES}
    auditoria=[]
    for fold in folds:
        n,tr,vl=fold['fold'],fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(pp['controle_fusao'],tr,vl,ys)
        print(f'Fold {n}/5: treinamento, seleção e calibração internos; avaliação externa separada.',flush=True)
        internas={v:[] for v in m.VARIANTES}
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(pp['controle_fusao'],ti,vi,tr)
            for v in m.VARIANTES:
                mod=m.ajustar(sub(pp[v],ti),sub(ys,ti),cat,v)
                internas[v].extend(a.avaliar(m.sinais(sub(pp[v],vi),mod,cat,v),sub(ys,vi),temas))
        pacotes={v:m.pacote(sub(pp[v],tr),sub(ys,tr),cat,v,internas[v]) for v in m.VARIANTES}
        escolhido=m.escolher(pacotes,internas)
        registro={'fold':n,'treino_ids':tr,'avaliacao_ids':vl,'folds_internos':fold['folds_internos'],
                  'selecionado':escolhido,'modelos':pacotes,'escolha_antes_dos_rotulos_externos':True}
        gravar(saida/f'folds/fold_{n}.json',registro)
        auditoria.append({k:v for k,v in registro.items() if k!='modelos'})
        for v in m.VARIANTES:
            ss=m.sinais(sub(pp[v],vl),pacotes[v]['modelo'],cat,v)
            raw[v].extend(a.avaliar(ss,sub(ys,vl),temas))
            rr=a.avaliar(m.aplicar(sub(pp[v],vl),pacotes[v],cat,v),sub(ys,vl),temas)
            rr=[{**r,'fold':n} for r in rr];externas[v].extend(rr)
            if v==escolhido:externas['selecionado_internamente'].extend(rr)
    ref100=controle(projeto,'avaliacao_desenvolvimento_100.csv')
    resumo={v:{'desenvolvimento_100':medir(rr,ref100),
               'trocas_vs_primeiro_fusao':trocas(rr,externas['controle_fusao'])} for v,rr in externas.items()}
    resumo['controle_v16']={'desenvolvimento_100':medir(ref100)}
    for v,rr in externas.items():
        resumo[v]['diagnostico_recuperacao_100']={
            'com_tema':sum(int(y['fora_da_taxonomia'])==0 for y in ys.values()),
            'aceito_top5':sum(any(f.aceito(t,ys[r['id']],temas) for t in r['top5_ids'].split(';')) for r in rr),
            'aceito_conjunto_candidatos':sum(any(f.aceito(t,ys[r['id']],temas) for t in r['candidatos_ids'].split(';')) for r in rr)}
    finais={v:m.pacote(pp[v],ys,cat,v,raw[v]) for v in m.VARIANTES}
    selecionado=m.escolher(finais,raw)
    gravar(saida/'modelos_finais.json',{'versao':'contexto_v18_1','selecionado':selecionado,'modelos':finais})
    gravar(saida/'escolha_antes_559.json',{'variante_final':selecionado,'fonte':'Somente referências de desenvolvimento; sem seleção pelo volume das 559.','promove_entrega':False})
    gravar(saida/'manifesto_inferencia.json',{'versao':'contexto_v18_1','projeto_sha256':deps,
        'artefatos_sha256':{n:sha(saida/n) for n in ['modelos_finais.json','escolha_antes_559.json']},'promove_entrega':False})
    gravar(saida/'resumo_antes_559.json',resumo);gravar(saida/'auditoria_folds.json',auditoria)
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'avaliacao':v} for v,rr in externas.items() for r in rr])
    csv_salvar(saida/'curvas_descritivas_100.csv',[{**r,'avaliacao':v} for v,rr in externas.items() for r in curva_descritiva(rr)])
    # Registra exceções completas sem transformar exemplos em regras por ID.
    mapa={r['id']:r for r in externas['controle_fusao']}
    excecoes=[]
    for v,rr in externas.items():
        if v=='selecionado_internamente':continue
        for r in rr:
            i=r['id'];antes=mapa[i]
            if r['tema_central_id']!=antes['tema_central_id']:
                p=pp[v][i]
                excecoes.append({'variante':v,'questao':qs[i],'referencia':ys[i],'antes':antes,'depois':r,
                                 'identificacao':p['identificacao'],'rota':p['rota'],'partes':p.get('partes')})
    gravar(saida/'trocas_completas_100.json',excecoes)
    print('Escolha e modelos congelados. Aplicando as cinco opções nas 559 sem rótulo.',flush=True)
    q559={i:q for i,q in qs.items() if i not in ys}
    (saida/'questoes_559_sem_rotulos.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for i,q in sorted(q559.items())),encoding='utf-8')
    alvo=m.preparar(cat,dic,q559);ref559=controle(projeto,'classificacoes_559_todas_variantes.csv');resultados={}
    for v in m.VARIANTES:
        rr=m.aplicar(alvo[v],finais[v],cat,v);resultados[v]=rr
        resumo[v]['alvo_559']=medir(rr,ref559)
        resumo[v]['recentes_300']=medir([r for r in rr if int(r['id'][1:])>=360])
        resumo[v]['antigas_259']=medir([r for r in rr if int(r['id'][1:])<360])
    resumo['selecionado_internamente']['alvo_559']=medir(resultados[selecionado],ref559)
    resumo['selecionado_internamente']['recentes_300']=medir([r for r in resultados[selecionado] if int(r['id'][1:])>=360])
    resumo['controle_v16']['alvo_559']=medir(ref559)
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',[r for rr in resultados.values() for r in rr])
    gravar(saida/'rotas_559.json',{i:{v:{'identificacao':alvo[v][i]['identificacao'],
                                      'rota':alvo[v][i]['rota'],'partes':alvo[v][i].get('partes'),
                                      'excluiu_narrativa':alvo[v][i]['excluiu_narrativa']} for v in m.VARIANTES} for i in alvo['controle_fusao']})
    gravar(saida/'resumo.json',resumo)
    for n,h in deps.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante avaliação: '+n)
    for n,h in preservados.items():
        if sha(projeto/n)!=h:raise ValueError('Controle alterado: '+n)
    gravar(saida/'execucao.json',{'segundos':time.perf_counter()-inicio,'selecionado':selecionado,'chamadas_llm':0,'precisao_real_559':None,'promove_entrega':False})
    for v,r in resumo.items():print(v,json.dumps(r,ensure_ascii=False),flush=True)
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
