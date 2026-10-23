"""Ablação na V9: novo treino/calibração, temas e positivos preservados na união."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import time
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.ranking import aplicar as aplicar_v8
from auditoria_confianca_v4.experimento import decompor
from experimento_atributos_v11.modelo import ATRIBUTOS,REMOCOES,preparar,matriz_treino,ajustar,sinais,aplicar,estatistica_identificador,identificadores,preservar_publicadas,medidas,indices


def gravar(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def csv_gravar(p,rows):
    with p.open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)


def sub(pp,ids):return {i:pp[i] for i in ids}


def diagnosticar(pp,ys,cat,base,controle,saida):
    cont={'revisadas_corretas':Counter(),'revisadas_erradas':Counter(),'publicadas_corretas_modelo':Counter()}
    totais=Counter();exemplos=[];coef={n:[] for n in ATRIBUTOS}
    for n in range(1,6):
        m=json.loads((base/f'folds/fold_{n}.json').read_text())['modelo']
        for k,v in zip(ATRIBUTOS,m['modelo']['coeficientes']):coef[k].append(v)
    for r in controle:
        i=r['id'];p=pp[i]
        if p['identificador_direto']:continue
        grupo='publicadas_corretas_modelo' if r['decisao']=='publicar' and r['correto'] else 'revisadas_corretas' if r['correto'] else 'revisadas_erradas'
        totais[grupo]+=1;k=cat.familias.index(r['tema_central_id'])
        m=json.loads((base/f"folds/fold_{r['fold']}.json").read_text())['modelo']
        if 'constante' in m['calibrador']:continue
        d=decompor(p['x_mescla'][k],m['modelo'],m['calibrador'])
        assert abs(d['confianca_reconstruida']-r['confianca'])<1e-10
        pares=sorted(zip(ATRIBUTOS,d['contribuicoes_logit']),key=lambda z:z[1])
        for n,v in pares[:3]:
            if v<0:cont[grupo][n]+=1
        exemplos.append({'id':i,'grupo':grupo,'confianca':r['confianca'],'negativos':pares[:5],'positivos':pares[-5:]})
    tabela=[]
    for n in ATRIBUTOS:
        tabela.append({'atributo':n,**{g:cont[g][n] for g in cont},
            'folds_coeficiente_positivo':sum(c>0 for c in coef[n]),'folds_coeficiente_negativo':sum(c<0 for c in coef[n])})
    tabela.sort(key=lambda r:-(r['revisadas_corretas']+r['revisadas_erradas']))
    csv_gravar(saida/'frequencia_negativos.csv',tabela)
    gravar(saida/'diagnostico_contribuicoes.json',{'denominadores':dict(totais),'exemplos':exemplos,
        'interpretacao':'Três maiores contribuições negativas no logit, relativas à centralização do treino. Não são pontos percentuais nem causas jurídicas; sinais correlacionados podem compensar-se.'})


def executar(projeto,saida):
    inicio=time.perf_counter();projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);base=projeto/'experimentos/vocabulario_v8_ranking_001'
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt']}
    gravar(saida/'protocolo_previo.json',{'remocoes':REMOCOES,'atributos_controle':ATRIBUTOS,
        'peso_negativo_nao_e_erro':True,'truncar_coeficientes_ou_somar_confianca':False,
        'hipoteses':'Retirar atributos isolados/grupos que aparecem em contribuições negativas; conferir ganho e erros após novo ajuste.',
        'tema_candidato':'Mesmo ranking v8 e identificador v9 em todas as variantes. Sem limite de caracteres.',
        'genericos':'Frase específica propõe candidato; não publica diretamente por Conduta/Resultado.',
        'avaliacao':'Cinco folds externos e quatro internos; treino/calibração/corte por variante sem rótulos externos.',
        'meta_empirica':.95,'minimo_interno':10,
        'politicas':['substituir_comparador','preservar_publicacoes_controle_e_adicionar'],
        'selecionar_por_volume_nas_559':False,'promove_entrega':False,
        'exposicao':'100 rótulos já vistos e reutilizados; não é teste externo cego.',
        'codigo_sha256':{n:sha(projeto/n) for n in ['testar_atributos_v11.py','experimento_atributos_v11/modelo.py']},
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'preservados_sha256':preservados})
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    pp=preparar(cat,dic,sub(qs,sorted(ys)))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    nomes=list(REMOCOES);cr=[];previsoes={n:[] for n in nomes};raw={n:[] for n in nomes};auditoria=[]
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids']
        print(f'Fold {n}/5: {len(nomes)-1} remoções + controle; novos modelos/calibração.',flush=True)
        intern={v:[] for v in nomes}
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids']
            assert not set(ti)&set(vi) and set(ti)|set(vi)==set(tr)
            assert not {pp[i]['hash'] for i in ti}&{pp[i]['hash'] for i in vi}
            dados=matriz_treino(sub(pp,ti),sub(ys,ti),cat)
            for v in nomes:
                mod=ajustar(dados,v)
                intern[v].extend(a.avaliar(sinais(sub(pp,vi),mod,cat,v),sub(ys,vi),temas))
        antigo=json.loads((base/f'folds/fold_{n}.json').read_text())
        assert antigo['treino_ids']==tr and antigo['avaliacao_ids']==vl
        freq=estatistica_identificador(pp,ys,temas,tr,vl)
        c=identificadores(aplicar_v8(sub(pp,vl),antigo['modelo'],cat),pp,freq['confianca'])
        c=[{**r,'fold':n} for r in a.avaliar(c,sub(ys,vl),temas)];cr.extend(c)
        dados=matriz_treino(sub(pp,tr),sub(ys,tr),cat);modelos={}
        for v in nomes:
            cal=a.calibrar(intern[v]);pol=a.politica(intern[v],a.confiancas(intern[v],cal))
            mod=antigo['modelo']['modelo'] if v=='controle_41' else ajustar(dados,v)
            m={'modelo':mod,'calibrador':cal,'politica':pol,'atributos':[ATRIBUTOS[j] for j in indices(v)]};modelos[v]=m
            rows=aplicar(sub(pp,vl),m,cat,v)
            raw[v].extend({**r,'fold':n} for r in a.avaliar(rows,sub(ys,vl),temas))
            novas=identificadores(rows,pp,freq['confianca'])
            novas=a.avaliar(novas,sub(ys,vl),temas)
            for politica,r2 in [('substituir',novas),('preservar',preservar_publicadas(novas,c))]:
                previsoes[v].extend({**r,'fold':n,'politica':politica,'variante':v} for r in r2)
        (saida/'folds').mkdir(exist_ok=True);gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'modelos':modelos})
        auditoria.append({'fold':n,'treino_ids':tr,'avaliacao_ids':vl})
    anterior={r['id']:r for r in csv.DictReader((projeto/'experimentos/relacoes_v9_004/avaliacao_100.csv').open()) if r['variante']=='titulos_diretos'}
    assert len(cr)==100
    for r in cr:
        b=anterior[r['id']];assert (r['decisao'],r['tema_central_id'])==(b['decisao'],b['tema_central_id'])
        assert abs(r['confianca']-float(b['confianca']))<1e-10
    diagnosticar(pp,ys,cat,base,cr,saida)
    tudo=[];resumo={};modelos_finais={};dados=matriz_treino(pp,ys,cat)
    for v in nomes:
        resumo[v]={}
        for politica in ['substituir','preservar']:
            rr=[r for r in previsoes[v] if r['politica']==politica]
            assert len(rr)==100 and {r['id'] for r in rr}==set(ys)
            for r in rr:
                b=next(c for c in cr if c['id']==r['id']);assert r['tema_central_id']==b['tema_central_id']
            resumo[v][politica]=medidas(rr,cr);tudo.extend(rr)
        cal=a.calibrar(raw[v]);pol=a.politica(raw[v],a.confiancas(raw[v],cal))
        modelo=json.loads((base/'modelo_diagnostico.json').read_text())['modelo'] if v=='controle_41' else ajustar(dados,v)
        modelos_finais[v]={'modelo':modelo,'calibrador':cal,'politica':pol,'atributos':[ATRIBUTOS[j] for j in indices(v)]}
    # As 559 só entram após fechar todas as avaliações e modelos nas 100.
    alvo=preparar(cat,dic,{i:q for i,q in qs.items() if i not in ys})
    freq=estatistica_identificador(pp,ys,temas,list(ys))
    basefinal=json.loads((base/'modelo_diagnostico.json').read_text())
    cf=identificadores(aplicar_v8(alvo,basefinal,cat),alvo,freq['confianca'])
    sim=[]
    for v,m in modelos_finais.items():
        novas=identificadores(aplicar(alvo,m,cat,v),alvo,freq['confianca'])
        for politica,rr in [('substituir',novas),('preservar',preservar_publicadas(novas,cf))]:
            resumo[v][politica]['simulacao_559']=medidas(rr,cf)
            sim.extend({**r,'variante':v,'politica':politica} for r in rr)
    csv_gravar(saida/'avaliacao_100.csv',tudo);csv_gravar(saida/'simulacao_559.csv',sim)
    gravar(saida/'modelos_finais.json',modelos_finais);gravar(saida/'resumo.json',resumo)
    gravar(saida/'controle_v9_100.json',cr);gravar(saida/'controle_v9_559.json',cf)
    gravar(saida/'estatistica_identificador.json',freq)
    mudancas=[];mapa={r['id']:r for r in cr}
    for r in tudo:
        b=mapa[r['id']]
        if r['decisao']!=b['decisao']:
            mudancas.append({'id':r['id'],'variante':r['variante'],'politica':r['politica'],
                'antes':b,'depois':r,'questao':qs[r['id']],'oficial':ys[r['id']]})
    gravar(saida/'mudancas_100.json',mudancas)
    for n,h in preservados.items():assert sha(projeto/n)==h
    print(json.dumps({'resumo':resumo,'segundos':time.perf_counter()-inicio,'promove_entrega':False},ensure_ascii=False,indent=2))
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
