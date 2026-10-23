"""Comparação de candidatos com modelos clássicos, sem exceção por ID."""
from __future__ import annotations

import math
from collections import Counter

from compatibilidade_v2 import features as f

METODOS=('referencias_fixa','candidatos_proximos','ranking_hibrido')


def candidatos(perfil):
    a=f.ordenar(perfil['scores'])[:5]
    b=f.ordenar(perfil['scores_novos'])[:5]
    return sorted(set(map(int,a))|set(map(int,b)))


def ajustar(perfis, ys, familias, temas, proximos):
    if not perfis or set(perfis)!=set(ys):
        raise ValueError('O ajuste exige somente os rótulos dos textos de treino.')
    contagens=Counter(p['hash'] for p in perfis.values())
    xx=[];yy=[];pesos=[]
    for qid,p in perfis.items():
        positivos={k for k,t in enumerate(familias) if f.aceito(t,ys[qid],temas)}
        ks=sorted(positivos|set(candidatos(p))) if proximos else list(range(len(familias)))
        # Mesma massa total por texto, independentemente do número de candidatos.
        peso=len(familias)/(len(ks)*contagens[p['hash']])
        xx.extend(p['features_v3'][ks]);yy.extend(int(k in positivos) for k in ks)
        pesos.extend([peso]*len(ks))
    return f.ajustar_linear(xx,yy,pesos,balancear=True)


def escore_linear(x, modelo):
    x=f.np.asarray(x,dtype=float)
    if x.ndim!=2 or x.shape[1]!=modelo['dimensao'] or not f.np.isfinite(x).all():
        raise ValueError('Atributos de inferência inválidos.')
    if 'constante' in modelo:
        p=modelo['constante']
        if not 0<p<1: raise ValueError('Constante fora de 0 a 1.')
        return f.np.full(len(x),math.log(p/(1-p)))
    z=(x-f.np.asarray(modelo['media']))/f.np.asarray(modelo['escala'])
    valores=z@f.np.asarray(modelo['coeficientes'])+modelo['intercepto']
    if not f.np.isfinite(valores).all(): raise ValueError('Escore não finito.')
    return valores


def sinais(perfis, modelos, familias):
    resultados={n:[] for n in METODOS}
    for qid,p in perfis.items():
        fixo=int(f.ordenar(p['scores'])[0]);ks=candidatos(p)
        escores=escore_linear(p['features_v3'],modelos['proximos'])
        prob=f.predizer_linear(p['features_v3'],modelos['proximos'])
        maximo=max(float(max(p['scores_novos'])),1e-12)
        hibrido=.65*p['scores_novos']/maximo+.35*prob
        j=max(ks,key=lambda k:(escores[k],-k))
        h=max(ks,key=lambda k:(hibrido[k],-k))
        fixa=float(escore_linear(p['features_v3'][[fixo]],modelos['todos'])[0])
        for nome,k,sinal in [('referencias_fixa',fixo,fixa),('candidatos_proximos',j,float(escores[j])),('ranking_hibrido',h,float(escores[h]))]:
            resultados[nome].append({'id':qid,'tema_central_id':familias[k],'indice':k,
                'sinal':sinal,'elegivel':bool(p['scores'][k]>=.03 or p['scores_novos'][k]>=.03),
                'score_legacy':float(p['scores'][k]),'score_referencias':float(p['scores_novos'][k]),
                'primeiro_legacy':familias[fixo], 'candidatos':[familias[k] for k in ks]})
    return resultados


def calibrar(linhas):
    if not linhas: raise ValueError('Calibração vazia.')
    y=[r['correto'] for r in linhas]
    mod=f.ajustar_linear([[r['sinal']] for r in linhas],y)
    if 'coeficientes' in mod and mod['coeficientes'][0]<0:
        return {'dimensao':1,'constante':(sum(y)+1)/(len(y)+2)}
    return mod


def confiancas(linhas,mod):
    return f.predizer_linear([[r['sinal']] for r in linhas],mod).tolist()


def avaliar(linhas,ys,temas):
    if len(linhas)!=len(ys) or {r['id'] for r in linhas}!=set(ys):
        raise ValueError('Avaliador recebeu rótulos externos ou previsões incompletas.')
    return [{**r,'correto':int(f.aceito(r['tema_central_id'],ys[r['id']],temas)),
             'fora_oficial':int(ys[r['id']]['fora_da_taxonomia'])} for r in linhas]


def politica(linhas,cs):
    return f.escolher_politica(linhas,cs,minimo=10)


def escolher(politicas,linhas):
    nomes=['controle_v2',*METODOS]
    # Empate favorece o controle. Não usa a quantidade publicada nas 559.
    def criterio(n):
        return (politicas[n]['suporte_interno'],sum(r['correto'] for r in linhas[n]),-nomes.index(n))
    return max(nomes,key=criterio)


def resumo(linhas):
    pubs=[r for r in linhas if r['decisao']=='publicar'];n=len(pubs)
    c=sum(r['correto'] for r in pubs)
    return {'avaliadas':len(linhas),'acertos_top1':sum(r['correto'] for r in linhas),
        'publicar':n,'revisar':len(linhas)-n,'fora':0,'acertos_publicadas':c,
        'erros_publicadas':n-c,'precisao_publicadas':c/n if n else None,
        'cobertura':n/len(linhas),'fora_oficial_publicadas':sum(r['fora_oficial'] for r in pubs),
        'brier':sum((r['confianca']-r['correto'])**2 for r in linhas)/len(linhas),
        'meta_95_na_amostra':bool(n and c/n>=.95),'meta_95_populacional_comprovada':False}
