"""Rotas sem acesso a rótulos; forte é um gatilho de leitura, não de publicação."""
POLITICAS=('comando_prioritario','suplemento_revisoes')


def compor(novas,base,politica):
    if politica not in POLITICAS:raise ValueError('Política desconhecida.')
    bm={r['id']:r for r in base}
    if len(bm)!=len(base) or len(novas)!=len(bm) or {r['id'] for r in novas}!=set(bm):
        raise ValueError('Conjuntos diferentes ou IDs repetidos.')
    out=[]
    for r in novas:
        a=bm[r['id']]
        forte=r['identificador_forte_cmd']
        if not isinstance(forte,bool):raise ValueError('Gatilho de comando precisa ser booleano.')
        usa=forte and (politica=='comando_prioritario' or a['decisao']!='publicar')
        z={**(r if usa else a),'rota_nova_aplicada':usa,'gatilho_comando':forte,
           'politica_roteamento':politica,'origem_decisao':'comando_estrito_v18' if usa else 'controle_v16'}
        if 'motivo' not in z:z['motivo']='Controle anterior preservado; rota de comando não aplicada.' if z['decisao']=='revisar' else ''
        out.append(z)
    return out
