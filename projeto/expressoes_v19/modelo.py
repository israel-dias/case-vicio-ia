"""Compara evidência composta com controle V18; confiança aprendida, sem piso."""
from collections import Counter
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from contexto_v18 import foco_morfologico as anterior
from contexto_v18 import modelo as origem
from .evidencia import Evidencia

VARIANTES=('controle_atual','frases_completas','vocabulario_escopos','passagem_cobrada')
NOVOS=['titulo_coerente','expressao_escopo','vocabulo_distintivo','titulo_no_foco','escopo_no_foco','vocabulo_no_foco']
ATRIBUTOS={v:list(anterior.ATRIBUTOS['comando_estrito'])+([] if v=='controle_atual' else NOVOS) for v in VARIANTES}


def normal(x):return x/max(float(max(x)),1e-12)


def preparar(cat,dic,qs):
    base=anterior.preparar(cat,dic,qs)['comando_estrito'];ev=Evidencia(cat);out={v:{} for v in VARIANTES}
    for i,q in qs.items():
        p=base[i];e=ev.preparar(q);b=normal(p['ranking'])
        sinais={'frases_completas':e['titulo'],
                'vocabulario_escopos':.25*e['titulo']+.40*e['escopo']+.35*e['raro'],
                'passagem_cobrada':.25*e['foco_titulo']+.40*e['foco_escopo']+.35*e['foco_raro']}
        for v in VARIANTES:
            extra=f.np.column_stack([e[k] for k in ['titulo','escopo','raro','foco_titulo','foco_escopo','foco_raro']])
            novo=f.np.zeros(len(b)) if v=='controle_atual' else normal(sinais[v])
            peso=0 if v=='controle_atual' else .15 if v=='frases_completas' else .25
            rank=(1-peso)*b+peso*novo
            out[v][i]={**p,'x':p['x'] if v=='controle_atual' else f.np.column_stack([p['x'],extra]),
                       'ranking':rank,'candidatos':origem.candidato_indices((rank,5),(p['ranking'],5),(novo,3)),
                       'evidencia_v19':e['trace']}
    return out


def ajustar(pp,ys,cat,variante):
    if not pp or set(pp)!=set(ys):raise ValueError('Treino vazio ou rótulos de outro grupo.')
    cont=Counter(p['hash'] for p in pp.values());xx=[];yy=[];ww=[]
    for i,p in pp.items():
        xx.extend(p['x']);yy.extend(int(f.aceito(t,ys[i],cat.temas)) for t in cat.familias);ww.extend([1/cont[p['hash']]]*len(cat.familias))
    return ajustar_linear_eficiente(xx,yy,ww,True)


def sinais(pp,modelo,cat,variante):
    out=[]
    for i,p in pp.items():
        es=a.escore_linear(p['x'],modelo);k=int(f.ordenar(p['ranking'])[0]);t=cat.familias[k]
        hom=any(abs(float(p['sinal_textual'][k]-p['sinal_textual'][cat.familias.index(u)]))<=1e-6 and abs(float(es[k]-es[cat.familias.index(u)]))<.25 for u in p['homonimos'][t])
        motivos=[n for n,b in [('sem_evidencia',p['rota']['sem_evidencia']),('pouco_sinal_textual',max(p['x'][k,:4])<.03),('homonimo_sem_escopo_resolvido',hom)] if b]
        ordem=[int(j) for j in f.ordenar(p['ranking'])]
        out.append({'id':i,'tema_central_id':t,'sinal':float(es[k]),'elegivel':not motivos,'homonimo_nao_resolvido':bool(hom),
                    'motivos_bloqueio':';'.join(motivos),'empate_comparador':False,'identificador_forte_cmd':p['identificacao']['forte'],
                    'origem_identificador':p['identificacao']['origem'],'narrativa_excluida':p['excluiu_narrativa'],
                    'primeiro_recuperado':t,'top5_ids':';'.join(cat.familias[j] for j in ordem[:5]),
                    'top5_recuperacao_ids':';'.join(cat.familias[j] for j in ordem[:5]),
                    'candidatos_ids':';'.join(cat.familias[j] for j in p['candidatos']),'variante':variante})
    return out


def pacote(pp,ys,cat,variante,internas,mod=None):
    cal=a.calibrar(internas)
    return {'modelo':mod if mod is not None else ajustar(pp,ys,cat,variante),'calibrador':cal,
            'politica':a.politica(internas,a.confiancas(internas,cal)),'atributos':ATRIBUTOS[variante]}


def aplicar(pp,pack,cat,variante):
    if pack['atributos']!=ATRIBUTOS[variante]:raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pack['modelo'],cat,variante);cs=a.confiancas(ss,pack['calibrador']);out=[]
    for r,c in zip(ss,cs):
        d=f.decidir(r,float(c),pack['politica']);motivo='' if d=='publicar' else r['motivos_bloqueio'] or ('sem_politica_com_suporte' if not pack['politica']['ativa'] else 'abaixo_do_limiar_calibrado')
        out.append({**r,'confianca':float(c),'decisao':d,'motivo':motivo})
    return out


def escolher(pacotes,internas):
    return max(VARIANTES,key=lambda v:(pacotes[v]['politica']['suporte_interno'],sum(int(r['correto']) for r in internas[v]),-VARIANTES.index(v)))
