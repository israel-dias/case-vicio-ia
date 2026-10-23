"""Estima diretamente o acerto do candidato; não escolhe o tema."""
import numpy as np
from compatibilidade_v2 import features as f

VARIANTES=('margens','evidencias')
ATRIBUTOS={'margens':['margem_lexica','margem_semantica','apoio_semantico'],
           'evidencias':['margem_lexica','margem_semantica','apoio_semantico','posicao_lexica','posicao_semantica','identificador_comando']}


def atributos(p,linha,cat,v):
    k=cat.familias.index(linha['tema_central_id']);x=p['x'];r=p['ranks']['lexical_bm25'];s=p['ranks']['e5_query']
    margem=lambda a:float(a[k]-max(a[j] for j in range(len(a)) if j!=k))
    forte=linha.get('identificador_forte_cmd') in {True,'True'}
    valores=[margem(r),margem(s),float(.5*x[k,3]+.5*x[k,4]),float(x[k,8]),float(x[k,9]),float(forte)]
    return valores[:3] if v=='margens' else valores


def ajustar(rows,pp,cat,v):
    if not rows or len(rows)!=len({r['id'] for r in rows}):raise ValueError('Exemplos vazios ou duplicados.')
    if any('correto' not in r for r in rows):raise ValueError('Ajuste exige acertos apenas dos IDs de treino.')
    return f.ajustar_linear([atributos(pp[r['id']],r,cat,v) for r in rows],[int(r['correto']) for r in rows])


def prever(rows,pp,cat,v,mod):
    return f.predizer_linear([atributos(pp[r['id']],r,cat,v) for r in rows],mod).tolist()


def aplicar(rows,pp,cat,v,pack):
    if pack['atributos']!=ATRIBUTOS[v]:raise ValueError('Atributos divergentes.')
    probs=prever(rows,pp,cat,v,pack['modelo']);out=[]
    for r,c in zip(rows,probs):
        b={**r};b['elegivel']=r.get('elegivel') in {True,'True'};d=f.decidir(b,float(c),pack['politica'])
        out.append({**b,'confianca':float(c),'decisao':d,'motivo':'' if d=='publicar' else r.get('motivos_bloqueio') or ('abaixo_do_limiar_estimado' if pack['politica']['ativa'] else 'sem_politica_com_suporte'),'variante':'qualidade_direta_'+v})
    return out
