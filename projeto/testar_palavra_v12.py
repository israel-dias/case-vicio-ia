"""Avalia as quatro hipóteses lexicais e sua combinação; não testa corte 50%."""
import argparse
import csv
import json
import time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.ranking import aplicar as aplicar_v8
from experimento_atributos_v11 import modelo as v11
from experimento_palavra_v12 import modelo as v12

def gravar(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def csv_gravar(p,rows):
    with p.open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def sub(pp,ids): return {i:pp[i] for i in ids}
def modelo(pp,ys,cat,v,internas):
    cal=a.calibrar(internas)
    return {'modelo':v12.ajustar(pp,ys,cat,v),'calibrador':cal,
        'politica':a.politica(internas,a.confiancas(internas,cal)),'atributos':v12.nomes(v)}
def verificar(rows,antigas):
    if {r['id'] for r in rows}!=set(antigas): raise ValueError('IDs do controle diferentes.')
    for r in rows:
        b=antigas[r['id']]
        if (r['tema_central_id'],r['decisao'])!=(b['tema_central_id'],b['decisao']) or abs(float(r['confianca'])-float(b['confianca']))>1e-9:
            raise ValueError('Controle v11 não reproduz: '+r['id'])

def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists(): raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);(saida/'folds').mkdir()
    src=projeto/'experimentos/atributos_v11_001';base=projeto/'experimentos/vocabulario_v8_ranking_001'
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt','experimentos/atributos_v11_001/resumo.json']}
    codigo=['testar_palavra_v12.py','experimento_palavra_v12/modelo.py','classificar_palavra_v12.py','congelar_palavra_v12.py']
    gravar(saida/'protocolo_previo.json',{'variantes':v12.VARIANTES,'atributos_base':v12.BASE,
        'novos_grupos':v12.GRUPOS,'palavra_completo_preservada':True,
        'ranking_fixo':'v8 mais identificadores v9; nenhum bônus de confiança ou LLM',
        'referencia':'V11 sem_apoio_duplo com publicações V9 preservadas',
        'politicas':['substituir_com_v9','preservar_v11'],'meta_empirica':.95,'minimo_interno':10,
        'corte_50_testado':False,'avaliacao':'Mesmos 5 folds externos/4 internos; rótulos externos não participam do ajuste/calibração/corte do fold.',
        'exposicao':'100 rótulos e erros reutilizados; não é teste externo cego.',
        'sem_rotulos_559':True,'selecionar_por_volume_559':False,'promove_entrega':False,
        'codigo_sha256':{n:sha(projeto/n) for n in codigo},
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'folds_sha256':sha(projeto/'experimentos/melhorias_v3_001/auditoria_folds.json'),
        'preservados_sha256':preservados})
    qs,temas,ys=f.carregar(projeto/'dados/anexos')
    if (len(qs),len(ys),len(temas))!=(659,100,377): raise ValueError('Anexos inesperados.')
    cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    pp=v12.preparar(cat,dic,sub(qs,sorted(ys)))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    antigas={r['id']:r for r in csv.DictReader((src/'avaliacao_100.csv').open()) if r['variante']=='sem_apoio_duplo' and r['politica']=='preservar'}
    raw={v:[] for v in v12.VARIANTES};todas=[];controle=[]
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(pp,tr,vl,ys)
        print(f'Fold {n}/5: controle V11, 4 mudanças e combinação.',flush=True)
        internas={v:[] for v in v12.VARIANTES}
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids'];validar_grupos(pp,ti,vi,tr)
            for v in v12.VARIANTES:
                mod=v12.ajustar(sub(pp,ti),sub(ys,ti),cat,v)
                internas[v].extend(a.avaliar(v12.sinais(sub(pp,vi),mod,cat,v),sub(ys,vi),temas))
        modelos={v:modelo(sub(pp,tr),sub(ys,tr),cat,v,internas[v]) for v in v12.VARIANTES}
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'modelos':modelos})
        taxa=v11.estatistica_identificador(pp,ys,temas,tr,vl)['confianca']
        antigo=json.loads((base/f'folds/fold_{n}.json').read_text())['modelo']
        cv9=v11.identificadores(aplicar_v8(sub(pp,vl),antigo,cat),pp,taxa)
        controle_fold=v12.combinar(v11.identificadores(v12.aplicar(sub(pp,vl),modelos['controle_v11'],cat,'controle_v11'),pp,taxa),cv9)
        verificar(controle_fold,{i:antigas[i] for i in vl})
        controle.extend({**r,'fold':n} for r in a.avaliar(controle_fold,sub(ys,vl),temas))
        for v,m in modelos.items():
            rr=v12.aplicar(sub(pp,vl),m,cat,v)
            raw[v].extend({**r,'fold':n} for r in a.avaliar(rr,sub(ys,vl),temas))
            novos=v11.identificadores(rr,pp,taxa)
            substitui=v12.combinar(novos,cv9)
            for pol,rows in [('substituir_com_v9',substitui),('preservar_v11',v12.combinar(substitui,controle_fold))]:
                avaliadas=a.avaliar(rows,sub(ys,vl),temas)
                todas.extend({**r,'variante':v,'politica':pol,'fold':n} for r in avaliadas)
    resumo={v:{pol:v11.medidas([r for r in todas if r['variante']==v and r['politica']==pol],controle) for pol in ['substituir_com_v9','preservar_v11']} for v in v12.VARIANTES}
    finais={v:modelo(pp,ys,cat,v,raw[v]) for v in v12.VARIANTES}
    # Controle final usa precisamente os parâmetros V11 anteriores, já congelados.
    anterior_final=json.loads((src/'modelos_finais.json').read_text())['sem_apoio_duplo']
    for campo in ['modelo','calibrador','politica']:
        if finais['controle_v11'][campo]!=anterior_final[campo]: raise ValueError('Modelo final de controle não reproduz: '+campo)
    taxa=v11.estatistica_identificador(pp,ys,temas,list(ys))
    pack={'variantes':finais,'controle_v9':json.loads((base/'modelo_diagnostico.json').read_text()),'controle_v11':finais['controle_v11'],'identificador':taxa}
    gravar(saida/'modelos_finais.json',pack)
    # Somente após concluir modelos e avaliação nas 100, simular os 559.
    alvo=v12.preparar(cat,dic,{i:q for i,q in qs.items() if i not in ys})
    cv9=v11.identificadores(aplicar_v8(alvo,pack['controle_v9'],cat),alvo,taxa['confianca'])
    cv11=v12.combinar(v11.identificadores(v12.aplicar(alvo,finais['controle_v11'],cat,'controle_v11'),alvo,taxa['confianca']),cv9)
    antigas559={r['id']:r for r in csv.DictReader((src/'simulacao_559.csv').open()) if r['variante']=='sem_apoio_duplo' and r['politica']=='preservar'}
    verificar(cv11,antigas559)
    sim=[]
    for v,m in finais.items():
        novos=v11.identificadores(v12.aplicar(alvo,m,cat,v),alvo,taxa['confianca']);subst=v12.combinar(novos,cv9)
        for pol,rows in [('substituir_com_v9',subst),('preservar_v11',v12.combinar(subst,cv11))]:
            resumo[v][pol]['simulacao_559']=v11.medidas(rows,cv11)
            resumo[v][pol]['simulacao_recentes_300']=v11.medidas([r for r in rows if int(r['id'][1:])>=360])
            sim.extend({**r,'variante':v,'politica':pol} for r in rows)
    csv_gravar(saida/'avaliacao_100.csv',todas);csv_gravar(saida/'simulacao_559.csv',sim)
    gravar(saida/'resumo.json',resumo)
    cb={r['id']:r for r in controle};mudancas=[]
    for r in todas:
        b=cb[r['id']]
        if r['decisao']!=b['decisao']:
            mudancas.append({'variante':r['variante'],'politica':r['politica'],'id':r['id'],
                'antes':b,'depois':r,'questao':qs[r['id']],'oficial':ys[r['id']]})
    gravar(saida/'mudancas_100.json',mudancas)
    for n,h in preservados.items():
        if sha(projeto/n)!=h: raise ValueError('Arquivo anterior alterado: '+n)
    print(json.dumps({'resumo':resumo,'segundos':time.perf_counter()-inicio,'corte_50_testado':False},ensure_ascii=False,indent=2),flush=True)
    return resumo

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
