"""Comparadores clássicos; sem rótulos na inferência ou escolha por LLM."""
import re,math
from collections import Counter
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from roteamento_v15 import modelo as v15
from experimento_palavra_v12 import modelo as v12
from mescla_marcadores_v7.texto import foco
from .catalogo import Busca

EXTRAS=['bm25_conjunto','bm25_en','bm25_comando','bm25_fim','bm25_relacao',
        'bm25_alternativas','bm25_itens_media','bm25_itens_max','legado_v8',
        'pos_bm25','pos_legado','apoio_top3','bm25_vantagem']
VARIANTES={'condicional_v15':{'novos':False,'reranking':False,'C':1.},
           'busca_multivista':{'novos':True,'reranking':False,'C':.3},
           'reranking_multivista':{'novos':True,'reranking':True,'C':.3}}
def nomes(v):return v15.NOMES+(EXTRAS if VARIANTES[v]['novos'] else [])
def normalizar(s):return s/max(float(max(s)),1e-12)
def posicoes(s):
    out=f.np.zeros(len(s))
    for pos,k in enumerate(f.ordenar(s)):out[k]=1/(1+pos)
    return out
def preparar(cat,dic,snapshot,qs,com_legado_original=False):
    # Os metadados de importação podem estar errados. Não entram na nova
    # recuperação. O perfil original é opcional e serve só para preservar V11.
    limpas={i:{**q,'disciplina_origem':'','assunto_origem':''} for i,q in qs.items()}
    base=v15.preparar(cat,dic,limpas);recuperacao=v12.preparar(cat,dic,limpas)
    legado=v12.preparar(cat,dic,qs) if com_legado_original else recuperacao
    bm=Busca(cat,snapshot)
    saida={v:{} for v in VARIANTES}
    for i,q in qs.items():
        p=base['foco_contextual'][i];r=p['rota'];n=len(cat.familias);zero=f.np.zeros(n)
        fim=' '.join(re.split(r'(?<=[.!?])\s+',r['en_usado'])[-2:])
        rel=foco(q,cat.temas)['texto_foco'];conjunto=r['texto_efetivo']
        b0=bm.buscar(conjunto);be=bm.buscar(r['en_usado']);bc=bm.buscar(r['cmd_usado']);bf=bm.buscar(fim);br=bm.buscar(rel)
        aa=[bm.buscar(t) for t in r['alts_usadas']];ii=[bm.buscar(t) for t in r['itens_usados']]
        ba=f.np.mean(aa,axis=0) if aa else zero;bi=f.np.mean(ii,axis=0) if ii else zero;bmax=f.np.max(ii,axis=0) if ii else zero
        antigo=normalizar(recuperacao[i]['ranking_vocabulario_reordena']);pf=p['ranking'];
        composto=.60*b0+.20*(br if rel else be)+.20*bf
        ranking=.55*antigo+.25*b0+.10*bf+.10*(br if rel else be)
        rankb=posicoes(composto);ranka=posicoes(antigo);rankf=posicoes(pf)
        apoio=((rankb>=1/3).astype(float)+(ranka>=1/3).astype(float)+(rankf>=1/3).astype(float))/3
        vantagem=b0-max(b0)
        xextra=f.np.column_stack([b0,be,bc,bf,br,ba,bi,bmax,antigo,rankb,ranka,apoio,vantagem])
        mask=f.np.ones_like(p['x'],dtype=bool)
        for j,nome in enumerate(v15.NOMES):
            if nome.startswith('cmd_'):mask[:,j]=bool(r['cmd_usado'])
            if nome.startswith('alt_'):mask[:,j]=bool(aa)
            if nome.startswith('itens_') or nome=='voto_itens':mask[:,j]=bool(ii)
            if nome.startswith('en_'):mask[:,j]=bool(r['en_usado'])
        flags=[True,bool(r['en_usado']),bool(r['cmd_usado']),bool(fim),bool(rel),bool(aa),bool(ii),bool(ii),True,True,True,True,True]
        mextra=f.np.tile(flags,(n,1))
        cand=sorted(set(int(k) for s in [antigo,pf,composto] for k in f.ordenar(s)[:7]))
        for v,cfg in VARIANTES.items():
            saida[v][i]={**p,'x':f.np.column_stack([p['x'],xextra]) if cfg['novos'] else p['x'],
                'mask':f.np.column_stack([mask,mextra]) if cfg['novos'] else mask,
                'ranking':ranking if cfg['novos'] else pf,'candidatos':cand if cfg['novos'] else list(range(n)),
                'legado':legado[i],'vistas':{'fim':fim,'relacao':rel,'bm25_primeiro':cat.familias[int(f.ordenar(composto)[0])]},
                'ranking_semantico':'BM25 lexical, não embeddings ou resolução de respostas'}
    return saida
def ajustar(pp,ys,cat,v):
    if not pp or set(pp)!=set(ys):raise ValueError('Treino vazio ou rótulos externos.')
    cont=Counter(p['hash'] for p in pp.values());xx=[];mm=[];yy=[];ww=[]
    for i,p in pp.items():
        positivos={k for k,t in enumerate(cat.familias) if f.aceito(t,ys[i],cat.temas)}
        ks=sorted(set(p['candidatos'])|positivos) if VARIANTES[v]['novos'] else list(range(len(cat.familias)))
        xx.extend(p['x'][ks]);mm.extend(p['mask'][ks]);yy.extend(int(k in positivos) for k in ks)
        ww.extend([1/(len(ks)*cont[p['hash']])]*len(ks))
    x=f.np.asarray(xx);mask=f.np.asarray(mm);y=f.np.asarray(yy);w=f.np.asarray(ww)
    massa=(mask*w[:,None]).sum(axis=0);massa=f.np.maximum(massa,1e-12)
    media=(x*mask*w[:,None]).sum(axis=0)/massa
    var=(((x-media)**2)*mask*w[:,None]).sum(axis=0)/massa;escala=f.np.sqrt(var);escala[escala<1e-10]=1
    z=f.np.where(mask,(x-media)/escala,0)
    # Preserva a escala de regularização entre ablações, normalizando massa
    # por questão e depois ajustando a média dos pesos para um.
    w=w/max(float(w.mean()),1e-12)
    if len(set(y))<2:
        return {'constante':(float(sum(y))+1)/(len(y)+2),'dimensao':x.shape[1],'condicional':True}
    massas={c:float(sum(w[y==c])) for c in set(y)};pesos=w*f.np.asarray([sum(w)/(2*massas[c]) for c in y])
    lr=f.LogisticRegression(C=VARIANTES[v]['C'],solver='liblinear',max_iter=1500,random_state=2026)
    with f.threadpool_limits(limits=2):lr.fit(z,y,sample_weight=pesos)
    return {'dimensao':x.shape[1],'media':media.tolist(),'escala':escala.tolist(),
        'coeficientes':lr.coef_[0].tolist(),'intercepto':float(lr.intercept_[0]),'condicional':True}
def escores(p,mod):
    if 'constante' in mod:return f.np.full(len(p['x']),math.log(mod['constante']/(1-mod['constante'])))
    z=f.np.where(p['mask'],(p['x']-f.np.asarray(mod['media']))/f.np.asarray(mod['escala']),0)
    return z@f.np.asarray(mod['coeficientes'])+mod['intercepto']
def sinais(pp,mod,cat,v):
    rr=[]
    for i,p in pp.items():
        es=escores(p,mod)
        if VARIANTES[v]['reranking']:k=max(p['candidatos'],key=lambda j:(es[j],-j))
        else:k=int(f.ordenar(p['ranking'])[0])
        t=cat.familias[k];hom=False
        for u in p['homonimos'][t]:
            j=cat.familias.index(u)
            if abs(float(p['sinal_textual'][k]-p['sinal_textual'][j]))<=1e-6 and abs(float(es[k]-es[j]))<.25:hom=True
        ok=bool(not p['rota']['sem_evidencia'] and max(p['x'][k,:4])>=.03 and not hom)
        rr.append({'id':i,'tema_central_id':t,'sinal':float(es[k]),'elegivel':ok,
            'homonimo_nao_resolvido':hom,'via':'v16_'+v,'modo':p['rota']['modo']})
    return rr
def aplicar(pp,pacote,cat,v,corte):
    if pacote['atributos']!=nomes(v):raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pacote['modelo'],cat,v);cs=a.confiancas(ss,pacote['calibrador'])
    return [{**r,'confianca':float(c),'decisao':f.decidir(r,c,pacote['politica']) if corte=='calibrado' else 'publicar' if r['elegivel'] and c>=.7 else 'revisar'} for r,c in zip(ss,cs)]
def mesmo_ramo(t,u,temas):return t in f.pais(u,temas) or u in f.pais(t,temas)
def preservar(novas,antigas,parceiras,temas,com_guarda):
    base={r['id']:r for r in antigas};par={r['id']:r for r in parceiras}
    if set(base)!={r['id'] for r in novas} or set(par)!=set(base):raise ValueError('Conjuntos diferentes.')
    saida=[]
    for r in novas:
        ant=base[r['id']];outra=par[r['id']];herda=ant['decisao']=='publicar';veto=False;mot=''
        if herda and com_guarda:
            hom=bool(r['homonimo_nao_resolvido'] and f.normalizar(temas[ant['tema_central_id']]['titulo'])==f.normalizar(temas[r['tema_central_id']]['titulo']))
            conflito=bool(r['elegivel'] and outra['elegivel'] and r['confianca']>=.7 and outra['confianca']>=.7 and r['tema_central_id']==outra['tema_central_id'] and not mesmo_ramo(ant['tema_central_id'],r['tema_central_id'],temas))
            veto=hom or conflito;mot='homonimo_herdado_sem_escopo' if hom else 'dois_comparadores_sugerem_outro_ramo' if conflito else ''
        z={**(ant if herda else r),'publicacao_preservada':herda,'veto_preservacao':veto,'motivo_veto':mot}
        if veto:z['decisao']='revisar'
        saida.append(z)
    return saida
