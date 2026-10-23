"""Teste isolado de expressões temáticas, mantendo as regras v7 congeladas."""
from collections import Counter
import csv
import json
from pathlib import Path
import time

from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.experimento import gravar,csv_salvar,separar,validar_grupos
from melhorias_v3.representacao import carregar_catalogo
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from mescla_marcadores_v7 import experimento as v7
from .texto import Dicionario

VARIANTES=('vocabulario_fixo','vocabulario_reordena')
NOMES=['vocabulario_enunciado','vocabulario_comando','vocabulario_alt_max',
       'vocabulario_alt_media','vocabulario_alt_fracao','vocabulario_busca','vocabulario_margem']
PESO_VOCABULARIO=.25


def preparar(cat,dicionario,qs):
    pp=v7.preparar(cat,qs)
    for qid,p in pp.items():
        x,busca,rastro=dicionario.atributos(qs[qid])
        p['x_v8']=f.np.column_stack([p['x_mescla'],x])
        p['vocabulario']=rastro;p['score_vocabulario']=busca
        anterior=p['ranking_mescla_condicional']
        normal=anterior/max(max(anterior),1e-12)
        novo=busca/max(max(busca),1e-12)
        p['ranking_vocabulario_fixo']=anterior
        p['ranking_vocabulario_reordena']=.75*normal+.25*novo if max(busca)>0 else normal
    return pp


def ajustar(perfis,ys,cat):
    if not perfis or set(perfis)!=set(ys):raise ValueError('Treino vazio ou rótulos de outro grupo.')
    cont=Counter(p['hash'] for p in perfis.values());xx=[];yy=[];pesos=[]
    for i,p in perfis.items():
        xx.extend(p['x_v8']);yy.extend(int(f.aceito(t,ys[i],cat.temas)) for t in cat.familias)
        pesos.extend([1/cont[p['hash']]]*len(cat.familias))
    return ajustar_linear_eficiente(xx,yy,pesos,True)


def sinais(perfis,modelo,cat,nome):
    if nome not in VARIANTES:raise ValueError('Variante desconhecida.')
    rows=[]
    for i,p in perfis.items():
        k=int(f.ordenar(p['ranking_'+nome])[0])
        rows.append({'id':i,'tema_central_id':cat.familias[k],
            'sinal':float(a.escore_linear(p['x_v8'][[k]],modelo)[0]),
            'elegivel':bool(not p['rota']['conteudo_insuficiente'] and
                max(p['scores'][k],p['scores_novos'][k],p['scores_foco'][k],p['score_vocabulario'][k])>=.03),
            'modo':p['rota']['modo'],'apoio_vocabulario':float(p['score_vocabulario'][k])})
    return rows


def aplicar(perfis,m,cat,nome):
    ss=sinais(perfis,m['modelo'],cat,nome)
    return [{**r,'confianca':p,'decisao':f.decidir(r,p,m['politica'])}
            for r,p in zip(ss,a.confiancas(ss,m['calibrador']))]


def executar(projeto,saida):
    inicio=time.perf_counter();projeto=Path(projeto).resolve();saida=Path(saida).resolve()
    if saida.exists():raise ValueError('Saída existente. Use outra pasta.')
    antigo=projeto/'experimentos/mescla_marcadores_v7_002'
    protocolo_v7=json.loads((antigo/'protocolo_previo.json').read_text())
    for n,h in protocolo_v7['codigo_sha256'].items():
        if sha(projeto/n)!=h:raise ValueError('Código de controle v7 alterado: '+n)
    qs,temas,ys=f.carregar(projeto/'dados/anexos')
    if (len(qs),len(ys),len(temas))!=(659,100,377):raise ValueError('Universo diferente.')
    cat,_=carregar_catalogo(projeto)
    dados=json.loads((projeto/'vocabulario_v8/dicionario.json').read_text())
    dic=Dicionario(dados,temas,cat.familias)
    folds_path=projeto/'experimentos/melhorias_v3_001/auditoria_folds.json'
    folds=json.loads(folds_path.read_text())
    codigo=['vocabulario_v8/dicionario.json','vocabulario_v8/texto.py','vocabulario_v8/experimento.py',
        'avaliar_vocabulario_v8.py',*protocolo_v7['codigo_sha256']]
    hashes={n:sha(projeto/n) for n in codigo}
    preservar={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt']}
    gravar(saida/'protocolo_previo.json',{'variantes':VARIANTES,'peso_ranking_vocabulario':PESO_VOCABULARIO,
        'dicionario':dados,'resolucao_de_titulos':dic.grupos,'atributos_novos':NOMES,
        'frequencias_das_659_usadas_como_peso':False,
        'alvos':'Famílias de nível 1. Descrições de filhos viram evidência do respectivo pai, sem fusão de ramos.',
        'avaliacao':'Mesmos 5 grupos externos e 4 internos; calibração e corte internos. Rótulos já expostos, desenvolvimento reutilizado.',
        'meta_empirica_interna':.95,'suporte_minimo_interno':10,'chamadas_llm_na_classificacao':0,
        'publicacao_por_palavra_chave':False,'promove_entrega':False,'usa_rotulos_559':False,
        'codigo_sha256':hashes,'folds_sha256':sha(folds_path),
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'entrega_preservada_sha256':preservar,
        'controle_v7_modelos_sha256':sha(antigo/'modelos_diagnosticos.json')})
    perfis=preparar(cat,dic,{i:qs[i] for i in sorted(ys)})
    pred={n:[] for n in VARIANTES}
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(perfis,tr,vl,ys)
        print(f'Vocabulário v8: fold externo {n}/5.',flush=True)
        internas={nome:[] for nome in VARIANTES}
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids']
            validar_grupos(perfis,ti,vi,tr)
            mod=ajustar(separar(perfis,ti),{i:ys[i] for i in ti},cat)
            for nome in VARIANTES:
                internas[nome].extend(a.avaliar(sinais(separar(perfis,vi),mod,cat,nome),{i:ys[i] for i in vi},temas))
        calibradores={nome:a.calibrar(internas[nome]) for nome in VARIANTES}
        politicas={nome:a.politica(internas[nome],a.confiancas(internas[nome],calibradores[nome])) for nome in VARIANTES}
        mod=ajustar(separar(perfis,tr),{i:ys[i] for i in tr},cat)
        modelos={nome:{'modelo':mod,'calibrador':calibradores[nome],'politica':politicas[nome]} for nome in VARIANTES}
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'modelos':modelos,
                                          'protocolo_sha256':sha(saida/'protocolo_previo.json')})
        for nome in VARIANTES:
            pred[nome].extend({**r,'fold':n} for r in a.avaliar(aplicar(separar(perfis,vl),modelos[nome],cat,nome),{i:ys[i] for i in vl},temas))
    resumo={}
    for nome,rows in pred.items():
        rows.sort(key=lambda r:r['id'])
        if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('Previsões incompletas.')
        csv_salvar(saida/f'previsoes_{nome}.csv',rows);resumo[nome]=a.resumo(rows)
    controle100=list(csv.DictReader((antigo/'previsoes_mescla_condicional.csv').open()))
    for r in controle100:
        for k in ['correto','fora_oficial']:r[k]=int(r[k])
        r['confianca']=float(r['confianca'])
    resumo['controle_v7']=a.resumo(controle100)
    mod=ajustar(perfis,ys,cat)
    finais={}
    for nome in VARIANTES:
        cal=a.calibrar(pred[nome]);finais[nome]={'modelo':mod,'calibrador':cal,
            'politica':a.politica(pred[nome],a.confiancas(pred[nome],cal))}
    gravar(saida/'modelos_diagnosticos.json',finais)
    # Volume das 559 não seleciona regra, limiar, vocabulário ou variante.
    alvo=preparar(cat,dic,{i:q for i,q in qs.items() if i not in ys})
    controle={r['id']:r for r in csv.DictReader((antigo/'simulacoes_559.csv').open()) if r['variante']=='mescla_condicional'}
    simulacoes={};todas=[]
    for nome,m in finais.items():
        rows=aplicar(alvo,m,cat,nome)
        for r in rows:
            ant=controle[r['id']]
            r.update({'variante':nome,'tema_v7':ant['tema_central_id'],'decisao_v7':ant['decisao'],
                'confianca_v7':float(ant['confianca']),'caminho':temas[r['tema_central_id']]['caminho']})
        todas.extend(rows);pubs=[r for r in rows if r['decisao']=='publicar']
        simulacoes[nome]={'publicar':len(pubs),'revisar':len(rows)-len(pubs),'fora':0,
            'cobertura':len(pubs)/len(rows),'media_confiancas_publicadas':sum(r['confianca'] for r in pubs)/len(pubs) if pubs else None,
            'limiar':m['politica']['limiar'],
            'revisar_para_publicar':sum(r['decisao']=='publicar' and r['decisao_v7']=='revisar' for r in rows),
            'publicar_para_revisar':sum(r['decisao']=='revisar' and r['decisao_v7']=='publicar' for r in rows),
            'mudancas_tema':sum(r['tema_central_id']!=r['tema_v7'] for r in rows),
            'recentes_300_publicadas':sum(int(r['id'][1:])>=360 for r in pubs),
            'precisao_real':None,'promovida_para_entrega':False}
    csv_salvar(saida/'simulacoes_559.csv',todas)
    gravar(saida/'expressoes_detectadas_659.json',{i:p['vocabulario'] for i,p in {**perfis,**alvo}.items()})
    antes={r['id']:r for r in controle100}
    mudancas=[]
    for nome,rows in pred.items():
        for r in rows:
            ant=antes[r['id']]
            if r['tema_central_id']!=ant['tema_central_id']:
                mudancas.append({'id':r['id'],'variante':nome,'tema_v7':ant['tema_central_id'],'correto_v7':ant['correto'],
                                 'tema_v8':r['tema_central_id'],'correto_v8':r['correto']})
    csv_salvar(saida/'mudancas_tema_100.csv',mudancas)
    resultado={'comparacao_100':resumo,'simulacoes_559':simulacoes,'grupos_vocabulario':len(dic.grupos),
        'padroes_vocabulario':sum(len(g['padroes']) for g in dic.grupos),
        'questoes_com_vocabulario':sum(any(p['score_vocabulario']>0) for p in {**perfis,**alvo}.values()),
        'segundos':time.perf_counter()-inicio,'entrega_alterada':False,'precisao_559_medida':False}
    gravar(saida/'resumo.json',resultado)
    for n,h in preservar.items():
        if sha(projeto/n)!=h:raise ValueError('Entrega alterada.')
    for n,h in hashes.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante execução.')
    print(json.dumps(resultado,ensure_ascii=False,indent=2),flush=True)
    return resultado
