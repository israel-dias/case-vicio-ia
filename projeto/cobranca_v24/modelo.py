"""Rota de cobrança com parâmetros clássicos e política de composição explícita."""
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from roteamento_v15 import modelo as v15
from contexto_v18 import modelo as original
from contexto_v18.texto import questao_estrita
from .texto import Leitura

VARIANTES=('cobranca_estrita','cobranca_com_apoio')
ATRIBUTOS={v:original.ATRIBUTOS['comando_estrito'] for v in VARIANTES}


def preparar(cat,dic,qs):
    leitor=Leitura(cat);novas={};rr={};ids={}
    for i,q in qs.items():novas[i],rr[i],ids[i]=leitor.preparar(q)
    base=v15.preparar(cat,dic,novas)['fusao_contextual'];estritas={i:questao_estrita(q,ids[i]) for i,q in novas.items() if ids[i]['forte']}
    est=v15.preparar(cat,dic,estritas)['fusao_contextual'] if estritas else {};out={v:{} for v in VARIANTES}
    for i,q in qs.items():
        for v in VARIANTES:
            p=est[i] if v=='cobranca_estrita' and i in est else base[i];ranking=p['ranking']
            if ids[i]['forte']:ranking=.65*original.normalizar(ranking)+.35*original.normalizar(ids[i]['scores'])
            out[v][i]={**p,'hash':f.campos(q)['hash'],'ranking':ranking,
                       'candidatos':original.candidato_indices((ranking,5),(ids[i]['scores'],3)),
                       'identificacao':rr[i],'excluiu_narrativa':bool(v=='cobranca_estrita' and i in est),'leitura_v24':rr[i]}
    return out


def ajustar(pp,ys,cat,v):return original.ajustar(pp,ys,cat,'comando_estrito')
def sinais(pp,mod,cat,v):return [{**r,'variante':v} for r in original.sinais(pp,mod,cat,'comando_estrito')]


def pacote(pp,ys,cat,v,internas):
    cal=a.calibrar(internas)
    return {'modelo':ajustar(pp,ys,cat,v),'calibrador':cal,'politica':a.politica(internas,a.confiancas(internas,cal)),'atributos':ATRIBUTOS[v]}


def aplicar(pp,pack,cat,v):
    if pack['atributos']!=ATRIBUTOS[v]:raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pack['modelo'],cat,v);cs=a.confiancas(ss,pack['calibrador']);out=[]
    for r,c in zip(ss,cs):
        d=f.decidir(r,float(c),pack['politica']);out.append({**r,'confianca':float(c),'decisao':d,'motivo':'' if d=='publicar' else r['motivos_bloqueio'] or ('abaixo_do_limiar_calibrado' if pack['politica']['ativa'] else 'sem_politica_com_suporte')})
    return out


def compor(novas,antigas,qs,leitor,modo):
    if modo not in {'veto_contexto','revalidar_cobranca','substituir'}:raise ValueError('Modo inválido.')
    bm={r['id']:r for r in antigas};out=[]
    for r in novas:
        i=r['id'];b=bm[i];_,trace,d=leitor.preparar(qs[i]);vetado=leitor.contexto_sem_cobranca(qs[i],b['tema_central_id'])
        mesmo=lambda t,u:t in f.pais(u,leitor.cat.temas) or u in f.pais(t,leitor.cat.temas)
        conflito=bool(d['forte'] and len(d['familias'])==1 and not mesmo(b['tema_central_id'],d['familias'][0]))
        if modo=='substituir':z=dict(r);rota='novo_modelo'
        elif b['decisao']=='publicar':
            if modo=='revalidar_cobranca' and conflito:
                z=dict(r);rota='publicacao_anterior_reavaliada_por_cobranca'
            elif modo=='veto_contexto' and conflito:
                z=dict(r);z['decisao']='revisar';z['motivo']='Cobrança explícita aponta outro ramo; publicação anterior suspensa.';rota='veto_conflito_cobranca'
            else:z=dict(b);rota='publicacao_anterior_sem_conflito_detectado'
            if vetado:
                z['decisao']='revisar';z['motivo']='Tema identificado apenas no crime narrado, sem apoio na cobrança; revisar o enquadramento.';rota='veto_contexto_da_publicacao_anterior'
        elif modo=='revalidar_cobranca' and d['forte']:
            z=dict(r);rota='nova_cobranca_especifica'
        else:z=dict(b);rota='controle_anterior'
        z.update(id=i,rota_v24=rota,veto_contexto=vetado,conflito_cobranca=conflito)
        if z['decisao']=='revisar' and not z.get('motivo'):z['motivo']='Enquadramento sugerido sem evidência suficiente para publicação automática.'
        out.append(z)
    return out
