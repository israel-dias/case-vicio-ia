"""Modelos clássicos; sem pesos truncados, exceções por ID ou rótulos na inferência."""
from collections import Counter
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from flexivel_v5.runtime import ATIVOS
from mescla_marcadores_v7.experimento import EXTRAS
from vocabulario_v8.experimento import preparar as preparar_v8
from experimento_relacoes_v9.regras import Identificador,TITULOS_GENERICOS_ISOLADOS
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente

ATRIBUTOS = ATIVOS + EXTRAS
# Hipóteses fixadas a partir do diagnóstico v8, não de resultados v11.
REMOCOES = {
    'controle_41': [],
    'sem_palavra_completo': ['palavra_completo'],
    'sem_escopo_alternativas': ['escopo_alternativas'],
    'sem_char_enunciado': ['char_enunciado'],
    'sem_apoio_duplo': ['apoio_enunciado_e_alternativas','evidencia_escopo_enunciado_alt'],
    'sem_atributos_origem': ['palavra_assunto_origem','origem_compativel','origem_reconhecida'],
    'sem_tres_frequentes': ['palavra_completo','escopo_alternativas','escopo_alternativa_max'],
    'sem_seis_frequentes': ['palavra_completo','escopo_alternativas','escopo_alternativa_max',
                            'char_enunciado','apoio_enunciado_e_alternativas','escopo_alternativa_media'],
    'sem_atributos_foco': list(EXTRAS),
}


def indices(nome):
    if nome not in REMOCOES:raise ValueError('Variante desconhecida.')
    if not set(REMOCOES[nome])<=set(ATRIBUTOS):raise ValueError('Atributo desconhecido.')
    return [j for j,n in enumerate(ATRIBUTOS) if n not in REMOCOES[nome]]


def preparar(cat,dic,qs):
    pp=preparar_v8(cat,dic,qs);idt=Identificador(cat,dic)
    for i,p in pp.items():
        cs,hits=idt.encontrar(p['rota']['enunciado_efetivo'])
        generico=any(h['tema'] and f.normalizar(cat.temas[h['tema']]['titulo']) in TITULOS_GENERICOS_ISOLADOS for h in hits)
        p['identificador_direto']=cs[0] if len(cs)==1 and not generico else None
        p['identificador_generico']=generico
    return pp


def matriz_treino(pp,ys,cat):
    if not pp or set(pp)!=set(ys):raise ValueError('Rótulos externos ou treino vazio.')
    cont=Counter(p['hash'] for p in pp.values());x=[];y=[];w=[]
    for i,p in pp.items():
        x.extend(p['x_mescla']);y.extend(int(f.aceito(t,ys[i],cat.temas)) for t in cat.familias)
        w.extend([1/cont[p['hash']]]*len(cat.familias))
    return f.np.asarray(x),f.np.asarray(y),f.np.asarray(w)


def ajustar(dados,nome):
    x,y,w=dados
    return ajustar_linear_eficiente(x[:,indices(nome)],y,w,True)


def sinais(pp,modelo,cat,nome):
    ix=indices(nome);rows=[]
    for i,p in pp.items():
        k=int(f.ordenar(p['ranking_vocabulario_reordena'])[0])
        rows.append({'id':i,'tema_central_id':cat.familias[k],
            'sinal':float(a.escore_linear(p['x_mescla'][[k]][:,ix],modelo)[0]),
            'elegivel':bool(not p['rota']['conteudo_insuficiente'] and max(p['scores'][k],p['scores_novos'][k],p['scores_foco'][k],p['score_vocabulario'][k])>=.03)})
    return rows


def aplicar(pp,m,cat,nome):
    ss=sinais(pp,m['modelo'],cat,nome)
    return [{**r,'confianca':float(c),'decisao':f.decidir(r,c,m['politica'])}
            for r,c in zip(ss,a.confiancas(ss,m['calibrador']))]


def estatistica_identificador(pp,ys,temas,treino,avaliacao=()):
    vetados={pp[i]['hash'] for i in avaliacao}
    validos=[i for i in treino if pp[i]['identificador_direto'] and pp[i]['hash'] not in vetados]
    c=sum(f.aceito(pp[i]['identificador_direto'],ys[i],temas) for i in validos)
    return {'suporte':len(validos),'acertos':c,'confianca':(c+1)/(len(validos)+2)}


def identificadores(rows,pp,confianca):
    return [{**r,'tema_central_id':pp[r['id']]['identificador_direto'] or r['tema_central_id'],
             'decisao':'publicar' if pp[r['id']]['identificador_direto'] else r['decisao'],
             'confianca':confianca if pp[r['id']]['identificador_direto'] else r['confianca'],
             'via':'identificador' if pp[r['id']]['identificador_direto'] else 'modelo'} for r in rows]


def preservar_publicadas(novas,controle):
    if {r['id'] for r in novas}!={r['id'] for r in controle}:raise ValueError('Conjuntos diferentes.')
    base={r['id']:r for r in controle}
    return [{**(base[r['id']] if base[r['id']]['decisao']=='publicar' else r),
             'publicacao_preservada':base[r['id']]['decisao']=='publicar'} for r in novas]


def medidas(rows,controle=None):
    pubs=[r for r in rows if r['decisao']=='publicar'];rotulado=all('correto' in r for r in rows)
    r={'questoes':len(rows),'publicar':len(pubs),'revisar':len(rows)-len(pubs),'cobertura':len(pubs)/len(rows)}
    if rotulado:
        c=sum(int(z['correto']) for z in pubs)
        r.update({'acertos_publicadas':c,'erros_publicadas':len(pubs)-c,
            'precisao_publicadas':c/len(pubs) if pubs else None,
            'acertos_top1':sum(int(z['correto']) for z in rows),
            'brier':sum((z['confianca']-int(z['correto']))**2 for z in rows)/len(rows),
            'meta_95_na_amostra':bool(pubs and c/len(pubs)>=.95)})
    else:r['precisao_real']=None
    if controle:
        base={z['id']:z for z in controle};adicoes=[z for z in pubs if base[z['id']]['decisao']!='publicar']
        r['novas_publicacoes']=len(adicoes)
        r['publicacoes_anteriores_perdidas']=sum(z['decisao']!='publicar' and base[z['id']]['decisao']=='publicar' for z in rows)
        if rotulado:r.update({'novas_corretas':sum(int(z['correto']) for z in adicoes),'novas_erradas':sum(1-int(z['correto']) for z in adicoes)})
    return r
