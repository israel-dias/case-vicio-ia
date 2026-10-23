"""E5 como atributo; comando explícito e ramo limitam o reordenamento."""
from compatibilidade_v2 import features as f
from contexto_v18 import foco_morfologico as base
from contexto_v18 import modelo as original
from melhorias_v3 import aprendizado as a
from semantica_v21.modelo import Busca

VARIANTES=('controle_contextual','semantica_apoio','reranking_com_contexto','reranking_livre')
NOVOS=['e5_integral','e5_foco','e5_passage','margem_e5','posicao_e5']
ATRIBUTOS={v:base.ATRIBUTOS['comando_estrito']+([] if v=='controle_contextual' else NOVOS) for v in VARIANTES}


def preparar(projeto,cat,dic,qs):
    antigos=base.preparar(cat,dic,qs)['comando_estrito']
    novos=Busca(projeto,cat,projeto/'artefatos/semantica_v21').preparar(qs);out={v:{} for v in VARIANTES}
    for i,p in antigos.items():
        e=novos[i];x=e['x'];extra=x[:,[3,4,5,7,9]]
        cand=sorted(set(p['candidatos'])|set(e['candidatos']))
        for v in VARIANTES:
            out[v][i]={**p,'x':p['x'] if v=='controle_contextual' else f.np.column_stack([p['x'],extra]),
                       'candidatos':cand,'trace_semantica':e['trace']}
    return out


def raiz(t,temas):
    return next(p for p in f.pais(t,temas) if temas[p]['nivel']==0)


def ajustar(pp,ys,cat,v):
    # Ajuste binário compartilhado; não treina uma classe por tema raro.
    return original.ajustar(pp,ys,cat,'comando_estrito')


def sinais(pp,mod,cat,v):
    out=[]
    for i,p in pp.items():
        es=a.escore_linear(p['x'],mod);ordem=[int(k) for k in f.ordenar(p['ranking'])];primeiro=ordem[0]
        forte=p['identificacao']['forte'];r=raiz(cat.familias[primeiro],cat.temas)
        if v=='reranking_com_contexto' and not forte:
            candidatos=[k for k in p['candidatos'] if raiz(cat.familias[k],cat.temas)==r]
            k=max(candidatos,key=lambda k:(float(es[k]),float(p['ranking'][k])));rota='reordenar_no_ramo_recuperado'
        elif v=='reranking_livre':
            candidatos=p['candidatos'];k=max(candidatos,key=lambda k:(float(es[k]),float(p['ranking'][k])));rota='reordenamento_sem_guarda'
        else:
            candidatos=[primeiro];k=primeiro;rota='preservar_comando_explicito' if forte else 'preservar_primeiro_recuperado'
        t=cat.familias[k]
        hom=any(abs(float(p['sinal_textual'][k]-p['sinal_textual'][cat.familias.index(u)]))<=1e-6
                and abs(float(es[k]-es[cat.familias.index(u)]))<.25 for u in p['homonimos'][t])
        empate=len(candidatos)>1 and any(j!=k and abs(float(es[j]-es[k]))<1e-10 for j in candidatos)
        motivos=[n for n,b in [('sem_evidencia',p['rota']['sem_evidencia']),('pouco_sinal_textual',max(p['x'][k,:4])<.03),('homonimo_sem_escopo_resolvido',hom),('empate_comparador',empate)] if b]
        preferencia=sorted(candidatos,key=lambda j:(-float(es[j]),-float(p['ranking'][j]))) if len(candidatos)>1 else ordem
        out.append({'id':i,'tema_central_id':t,'sinal':float(es[k]),'elegivel':not motivos,
                    'motivos_bloqueio':';'.join(motivos),'variante':v,'rota':rota,
                    'identificador_forte_cmd':forte,'primeiro_recuperado':cat.familias[primeiro],
                    'top5_ids':';'.join(cat.familias[j] for j in preferencia[:5]),'top5_recuperacao_ids':';'.join(cat.familias[j] for j in ordem[:5])})
    return out


def pacote(pp,ys,cat,v,internas,mod=None):
    cal=a.calibrar(internas)
    return {'modelo':mod if mod is not None else ajustar(pp,ys,cat,v),'calibrador':cal,
            'politica':a.politica(internas,a.confiancas(internas,cal)),'atributos':ATRIBUTOS[v]}


def aplicar(pp,pack,cat,v):
    if pack['atributos']!=ATRIBUTOS[v]:raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pack['modelo'],cat,v);cs=a.confiancas(ss,pack['calibrador']);out=[]
    for r,c in zip(ss,cs):
        d=f.decidir(r,float(c),pack['politica']);out.append({**r,'confianca':float(c),'decisao':d,'motivo':'' if d=='publicar' else r['motivos_bloqueio'] or ('abaixo_do_limiar_calibrado' if pack['politica']['ativa'] else 'sem_politica_com_suporte')})
    return out
