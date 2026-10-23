"""Contexto lexical, campos e intensidade absoluta da evidência."""
from compatibilidade_v2 import features as f
from contexto_v18 import foco_morfologico as base
from contexto_v18 import modelo as original
from expressoes_v19 import modelo as v19
from .evidencia import Evidencia

a=v19.a

def misturar(base,sinal):
    peso=.25*min(1,float(max(sinal)))
    return (1-peso)*base+.25*sinal

VARIANTES=('controle_atual','ambiguidades_contextuais','campos_sem_amplificar','escopos_contextuais')
ATRIBUTOS={v:list(base.ATRIBUTOS['comando_estrito'])+([] if v=='controle_atual' else v19.NOVOS) for v in VARIANTES}


def preparar(cat,dic,qs):
    pp=base.preparar(cat,dic,qs)['comando_estrito'];ev=Evidencia(cat);eh=Evidencia(cat,homonimos=True);out={v:{} for v in VARIANTES}
    for i,q in qs.items():
        p=pp[i];b=v19.normal(p['ranking']);contexto=ev.campos(q)
        es={'ambiguidades_contextuais':ev.preparar(q),'campos_sem_amplificar':contexto,'escopos_contextuais':eh.campos(q)}
        for v in VARIANTES:
            e=contexto if v=='controle_atual' else es[v]
            n=.25*e['titulo']+.4*e['escopo']+.35*e['raro']
            if v=='controle_atual':rank=b
            elif v=='ambiguidades_contextuais':rank=.75*b+.25*v19.normal(n)
            else:
                # Uma evidência pequena mantém intensidade pequena. O peso
                # total só chega a 25% quando o apoio absoluto chega a 1.
                rank=misturar(b,n)
            extra=f.np.column_stack([e[k] for k in ['titulo','escopo','raro','foco_titulo','foco_escopo','foco_raro']])
            out[v][i]={**p,'x':p['x'] if v=='controle_atual' else f.np.column_stack([p['x'],extra]),
                       'ranking':rank,'candidatos':original.candidato_indices((rank,5),(p['ranking'],5),(n,3)),
                       'evidencia_v19':e['trace']}
    return out

ajustar=v19.ajustar
sinais=v19.sinais


def pacote(pp,ys,cat,variante,internas,mod=None):
    cal=v19.a.calibrar(internas)
    return {'modelo':mod if mod is not None else ajustar(pp,ys,cat,variante),'calibrador':cal,
            'politica':v19.a.politica(internas,v19.a.confiancas(internas,cal)),'atributos':ATRIBUTOS[variante]}


def aplicar(pp,pack,cat,variante):
    if pack['atributos']!=ATRIBUTOS[variante]:raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pack['modelo'],cat,variante);cs=v19.a.confiancas(ss,pack['calibrador']);out=[]
    for r,c in zip(ss,cs):
        d=f.decidir(r,float(c),pack['politica']);motivo='' if d=='publicar' else r['motivos_bloqueio'] or ('sem_politica_com_suporte' if not pack['politica']['ativa'] else 'abaixo_do_limiar_calibrado')
        out.append({**r,'confianca':float(c),'decisao':d,'motivo':motivo})
    return out


def escolher(pacotes,internas):
    return max(VARIANTES,key=lambda v:(pacotes[v]['politica']['suporte_interno'],sum(int(r['correto']) for r in internas[v]),-VARIANTES.index(v)))
