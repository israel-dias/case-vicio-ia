"""Análise adaptativa: preservar a V15 atual e testar os suplementos V16."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import sha
from experimento_atributos_v11.modelo import medidas
from multivista_v16 import modelo as m
from testar_multivista_v16 import gravar,csv_salvar,referencia,PARCEIRA

def ler_novas(p):
    rows=list(csv.DictReader(p.open()))
    for r in rows:
        r['confianca']=float(r['confianca']);r['elegivel']=r['elegivel']=='True'
        r['homonimo_nao_resolvido']=r['homonimo_nao_resolvido']=='True'
        for n in ['correto','fora_oficial','fold']:
            if n in r:r[n]=int(r[n])
    return rows
def compor(rows,base,temas):
    saidas=[];res={};ordem=[]
    for corte in ['calibrado','70']:
        novas={v:[r for r in rows if (r['variante'],r['corte'],r['politica'])==(v,corte,'substituir')] for v in m.VARIANTES}
        for v in m.VARIANTES:
            for pol,guarda in [('preservar_v15',False),('preservar_v15_com_guarda',True)]:
                rr=m.preservar(novas[v],base,novas[PARCEIRA[v]],temas,guarda);chave='/'.join([v,corte,pol]);ordem.append(chave)
                res[chave]=medidas(rr,base)
                res[chave]['vetos_preservacao']=sum(r['veto_preservacao'] for r in rr)
                saidas.extend({**r,'variante':v,'corte':corte,'politica':pol} for r in rr)
    return saidas,res,ordem
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/multivista_v16_001'
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True)
    gravar(saida/'protocolo_previo.json',{'natureza':'Análise adaptativa posterior à rodada V16 inicial. Preserva V15 atual, em vez de apenas V11.',
        'exposicao':'Os resultados anteriores, inclusive volumes individuais das 559, já foram vistos. Não é teste externo cego.',
        'cortes':['calibrado','70'],'politicas':['preservar_v15','preservar_v15_com_guarda'],
        'ajuste_ou_calibracao_nova':False,'escolher_por_volume_559':False,
        'criterio':'Nas 100 de desenvolvimento: precisão empírica >=95%, suporte>=10; maximizar publicações e acertos; desempate pela ordem fixa. Só depois compor as 559.',
        'codigo_sha256':sha(Path(__file__)),'modelos_v16_sha256':sha(e/'modelos_finais.json'),'promove_entrega':False})
    temas={r['tema_id']:r for r in csv.DictReader((projeto/'dados/anexos/temas.csv').open())}
    base=referencia(projeto,'experimentos/roteamento_v15_002/avaliacao_100.csv','foco_contextual','preservar_v11','70')
    rs,ds,ordem=compor(ler_novas(e/'avaliacao_desenvolvimento_100.csv'),base,temas)
    eleg=[k for k in ordem if ds[k]['publicar']>=10 and (ds[k]['precisao_publicadas'] or 0)>=.95]
    escolha=max(eleg,key=lambda k:(ds[k]['publicar'],ds[k]['acertos_publicadas'],-ordem.index(k))) if eleg else None
    gravar(saida/'escolha_antes_uniao_559.json',{'configuracao':escolha,'fonte':'Composição nas 100; volumes individuais V16 das 559 já conhecidos.','promove_entrega':False})
    csv_salvar(saida/'avaliacao_desenvolvimento_100.csv',rs)
    base559=referencia(projeto,'experimentos/roteamento_v15_002/simulacao_559.csv','foco_contextual','preservar_v11','70')
    ss,alvo,_=compor(ler_novas(e/'classificacoes_559_todas_variantes.csv'),base559,temas)
    resumo={}
    for k in ordem:
        v,c,pol=k.split('/');rr=[r for r in ss if (r['variante'],r['corte'],r['politica'])==(v,c,pol)]
        resumo[k]={'desenvolvimento_100':ds[k],'alvo_559':alvo[k],
                   'recentes_300':medidas([r for r in rr if int(r['id'][1:])>=360])}
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',ss);gravar(saida/'resumo.json',resumo)
    gravar(saida/'manifesto_ampliacao.json',{'projeto_sha256':{n:sha(projeto/n) for n in ['ampliar_multivista_v16.py','classificar_ampliacao_v16.py','experimentos/roteamento_v15_002/modelos_finais.json']},
        'base_v16_manifesto_sha256':sha(e/'manifesto_inferencia.json'),'promove_entrega':False})
    print(json.dumps({'escolha':escolha,'resultado':resumo.get(escolha)},ensure_ascii=False,indent=2));return resumo
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
