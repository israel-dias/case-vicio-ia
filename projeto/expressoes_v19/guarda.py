"""Composição diagnóstica por disciplina prevista, sem presumir acerto do controle."""

def raiz(t,temas):
    vistos=set()
    while temas[t]['parent_id']:
        if t in vistos:raise ValueError('Ciclo na taxonomia.')
        vistos.add(t);t=temas[t]['parent_id']
    return t


def combinar(base,novas,temas):
    if {r['id'] for r in base}!={r['id'] for r in novas}:raise ValueError('Conjuntos diferentes.')
    anteriores={r['id']:r for r in base};out=[]
    for n in novas:
        b=anteriores[n['id']]
        mesma=bool(n['tema_central_id'] and b['tema_central_id'] and raiz(n['tema_central_id'],temas)==raiz(b['tema_central_id'],temas))
        escolhido=n if mesma else b
        out.append({**escolhido,'variante':n['variante'],'guarda_disciplina_acionada':not mesma,
                    'tema_proposto_antes_da_guarda':n['tema_central_id'],
                    'confianca_global_recalibrada':False})
    return out
