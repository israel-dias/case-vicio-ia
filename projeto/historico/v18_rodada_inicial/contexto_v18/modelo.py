"""Leitura estrita, apoio por passagens e aprendizado de preferência por pares."""
from collections import Counter
import math
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from roteamento_v15 import modelo as v15
from roteamento_v15.texto import Leitor
from .texto import Identificadores, questao_estrita, passagens

EXTRAS = ['identificador_cmd', 'pass_escopo_max', 'pass_escopo_top2',
          'pass_palavra_max', 'pass_palavra_top2', 'ligada_escopo', 'ligada_palavra',
          'relacao_escopo', 'relacao_palavra', 'cmd_menos_cenario',
          'acordo_cmd_ligada', 'ranking_cmd', 'ranking_passagens', 'posicao_fusao']
VARIANTES = ('controle_fusao', 'comando_estrito', 'passagens_apoio', 'passagens_pares', 'estrito_pares')
PARES = {'passagens_pares', 'estrito_pares'}
ATRIBUTOS = {v: list(v15.NOMES)+(EXTRAS if v in {'passagens_apoio', *PARES} else []) for v in VARIANTES}


def normalizar(s):
    return s/max(float(max(s)), 1e-12)


def candidato_indices(*scores):
    out = set()
    for s, n in scores:
        if max(s)>0:
            out.update(int(k) for k in f.ordenar(s)[:n])
    # A sugestão de formato não libera um item sem evidência; a guarda veta.
    return sorted(out) if out else [int(f.ordenar(scores[0][0])[0])]


def vistas(q, p, ident, leitor):
    partes = passagens(q, leitor)
    n = len(leitor.cat.familias)
    zero = f.np.zeros((n, 7))
    xx = [leitor.pontuar(t) for t in partes['janelas']]
    scopes = f.np.asarray([z[:,2] for z in xx]) if xx else f.np.zeros((1,n))
    words = f.np.asarray([z[:,0] for z in xx]) if xx else f.np.zeros((1,n))
    sm = scopes.max(axis=0); st = f.np.mean(f.np.sort(scopes, axis=0)[-2:], axis=0)
    wm = words.max(axis=0); wt = f.np.mean(f.np.sort(words, axis=0)[-2:], axis=0)
    ligada = leitor.pontuar(partes['ligado'])
    rel = leitor.pontuar(partes['texto_relacoes'])
    cmd = leitor.pontuar(partes['rota']['cmd_usado'])
    en = leitor.pontuar(partes['rota']['en_usado'])
    rc = leitor.ranking_texto(partes['rota']['cmd_usado'])
    rp = .6*leitor.ranking_texto(partes['ligado']) + .2*sm + .2*leitor.ranking_texto(partes['texto_relacoes'])
    idscore = normalizar(ident['scores'])
    cobranca = .65*normalizar(rc)+.35*idscore if ident['forte'] else .5*normalizar(rc)+.5*normalizar(rp)
    ranking = .6*normalizar(p['ranking'])+.25*cobranca+.15*normalizar(rp)
    pos = f.np.zeros(n)
    for j,k in enumerate(f.ordenar(p['ranking'])):
        pos[int(k)] = 1/(j+1)
    x = f.np.column_stack([p['x'], ident['scores']/4, sm, st, wm, wt,
                          ligada[:,2], ligada[:,0], rel[:,2], rel[:,0],
                          cmd[:,2]-en[:,2], f.np.minimum(cmd[:,2], ligada[:,2]), rc, rp, pos])
    cand = candidato_indices((p['ranking'],5), (ranking,5), (rc,3), (rp,3), (ident['scores'],3))
    return {**p, 'x':x, 'ranking':ranking, 'candidatos':cand,
            'partes':partes, 'identificacao': {k:v for k,v in ident.items() if k!='scores'}}


def preparar(cat, dic, qs):
    leitor = Leitor(cat, dic)
    detector = Identificadores(cat)
    ids = {i:detector.analisar(q) for i,q in qs.items()}
    base = v15.preparar(cat, dic, qs)['fusao_contextual']
    alteradas = {i:questao_estrita(q, ids[i]) for i,q in qs.items() if ids[i]['forte']}
    mod = v15.preparar(cat, dic, alteradas)['fusao_contextual'] if alteradas else {}
    out = {v:{} for v in VARIANTES}
    for i,q in qs.items():
        b = base[i]
        p = {**b, 'candidatos':[int(k) for k in f.ordenar(b['ranking'])[:5]],
             'identificacao': {k:v for k,v in ids[i].items() if k!='scores'}, 'excluiu_narrativa':False}
        estrito = {**(mod[i] if i in mod else b), 'hash':b['hash'],
                   'identificacao':p['identificacao'], 'excluiu_narrativa':i in mod}
        if i in mod:
            estrito['ranking'] = .65*normalizar(estrito['ranking'])+.35*normalizar(ids[i]['scores'])
        estrito['candidatos'] = candidato_indices((estrito['ranking'],5), (ids[i]['scores'],3))
        apoio = vistas(q,b,ids[i],leitor) | {'hash':b['hash'], 'excluiu_narrativa':False}
        eq = alteradas.get(i,q)
        est_pares = vistas(eq,estrito,ids[i],leitor) | {'hash':b['hash'], 'excluiu_narrativa':i in mod}
        out['controle_fusao'][i] = p
        out['comando_estrito'][i] = estrito
        out['passagens_apoio'][i] = apoio
        out['passagens_pares'][i] = apoio
        out['estrito_pares'][i] = est_pares
    return out


def ajustar(pp,ys,cat,variante):
    if not pp or set(pp)!=set(ys):
        raise ValueError('Treino vazio ou rótulos externos.')
    cont=Counter(p['hash'] for p in pp.values())
    xx=[];yy=[];ww=[]
    if variante in PARES:
        usadas=0
        for i,p in pp.items():
            bons=[k for k in p['candidatos'] if f.aceito(cat.familias[k],ys[i],cat.temas)]
            ruins=[k for k in p['candidatos'] if not f.aceito(cat.familias[k],ys[i],cat.temas)]
            pares=[(j,k) for j in bons for k in ruins]
            if not pares:
                continue
            usadas+=1
            peso=1/(len(pares)*2*cont[p['hash']])
            for j,k in pares:
                d=p['x'][j]-p['x'][k]
                xx.extend([d,-d]);yy.extend([1,0]);ww.extend([peso,peso])
        if not xx:
            return {'dimensao':len(ATRIBUTOS[variante]),'constante':.5,'tipo':'pares_sem_suporte','questoes_com_pares':0}
        x=f.np.asarray(xx);y=f.np.asarray(yy);w=f.np.asarray(ww)
        # Diferenças são simétricas. Escala sem centrar preserva a comparação.
        escala=f.np.sqrt(f.np.average(x*x,axis=0,weights=w));escala[escala<1e-10]=1
        w=w/f.np.mean(w)
        lr=f.LogisticRegression(C=.3,fit_intercept=False,solver='liblinear',max_iter=1500,random_state=2026)
        with f.threadpool_limits(limits=2):
            lr.fit(x/escala,y,sample_weight=w)
        return {'dimensao':x.shape[1],'media':[0.]*x.shape[1],'escala':escala.tolist(),
                'coeficientes':lr.coef_[0].tolist(),'intercepto':0.,'tipo':'pares',
                'questoes_com_pares':usadas,'pares_simetrizados':len(y)}
    for i,p in pp.items():
        xx.extend(p['x']);yy.extend(int(f.aceito(t,ys[i],cat.temas)) for t in cat.familias)
        ww.extend([1/cont[p['hash']]]*len(cat.familias))
    return ajustar_linear_eficiente(xx,yy,ww,True)


def sinais(pp,modelo,cat,variante):
    out=[]
    for i,p in pp.items():
        es=a.escore_linear(p['x'],modelo)
        k=max(p['candidatos'],key=lambda j:(float(es[j]),float(p['ranking'][j]))) if variante in PARES else int(f.ordenar(p['ranking'])[0])
        t=cat.familias[k]
        hom=any(abs(float(p['sinal_textual'][k]-p['sinal_textual'][cat.familias.index(u)]))<=1e-6
                and abs(float(es[k]-es[cat.familias.index(u)]))<.25 for u in p['homonimos'][t])
        empate=bool(variante in PARES and any(j!=k and abs(float(es[j]-es[k]))<=1e-10 for j in p['candidatos']))
        motivos=[n for n,b in [('sem_evidencia',p['rota']['sem_evidencia']),
                                ('pouco_sinal_textual',max(p['x'][k,:4])<.03),
                                ('homonimo_sem_escopo_resolvido',hom),
                                ('empate_comparador_sem_preferencia',empate)] if b]
        ordem=[int(j) for j in f.ordenar(p['ranking'])]
        preferencia=sorted(p['candidatos'],key=lambda j:(-float(es[j]),-float(p['ranking'][j]))) if variante in PARES else ordem
        out.append({'id':i,'tema_central_id':t,'sinal':float(es[k]),'elegivel':not motivos,
                    'homonimo_nao_resolvido':bool(hom),'motivos_bloqueio':';'.join(motivos),
                    'empate_comparador':empate,
                    'identificador_forte_cmd':p['identificacao']['forte'],
                    'origem_identificador':p['identificacao']['origem'],
                    'narrativa_excluida':p['excluiu_narrativa'],
                    'primeiro_recuperado':cat.familias[ordem[0]],
                    'top5_ids':';'.join(cat.familias[j] for j in preferencia[:5]),
                    'top5_recuperacao_ids':';'.join(cat.familias[j] for j in ordem[:5]),
                    'candidatos_ids':';'.join(cat.familias[j] for j in p['candidatos']),
                    'variante':variante})
    return out


def pacote(pp,ys,cat,variante,internas,mod=None):
    cal=a.calibrar(internas)
    return {'modelo':mod if mod is not None else ajustar(pp,ys,cat,variante),
            'calibrador':cal,'politica':a.politica(internas,a.confiancas(internas,cal)),
            'atributos':ATRIBUTOS[variante]}


def aplicar(pp,pack,cat,variante):
    if pack['atributos']!=ATRIBUTOS[variante]:
        raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pack['modelo'],cat,variante);cs=a.confiancas(ss,pack['calibrador'])
    out=[]
    for r,c in zip(ss,cs):
        d=f.decidir(r,float(c),pack['politica'])
        motivo='' if d=='publicar' else r['motivos_bloqueio'] or ('sem_politica_com_suporte' if not pack['politica']['ativa'] else 'abaixo_do_limiar_calibrado')
        out.append({**r,'confianca':float(c),'decisao':d,'motivo':motivo})
    return out


def escolher(pacotes,internas):
    return max(VARIANTES,key=lambda v:(pacotes[v]['politica']['suporte_interno'],
                                      sum(int(r['correto']) for r in internas[v]),-VARIANTES.index(v)))
