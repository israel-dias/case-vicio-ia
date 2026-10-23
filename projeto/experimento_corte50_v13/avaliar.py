"""Teste isolado de corte 50% sobre probabilidades congeladas; sem retreino."""
import argparse
import csv
import json
import math
from pathlib import Path
import hashlib

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ler(p):
    with Path(p).open(encoding='utf-8',newline='') as arq:return list(csv.DictReader(arq))
def gravar(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csv_gravar(p,rows):
    with Path(p).open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def booleano(v):
    if v is True or v=='True':return True
    if v is False or v=='False':return False
    raise ValueError('Elegibilidade inválida.')
def aplicar(rows,corte=.5):
    if isinstance(corte,bool) or not isinstance(corte,(int,float)) or not math.isfinite(corte) or not 0<=corte<=1:raise ValueError('Corte inválido.')
    ids=[r['id'] for r in rows]
    if not rows or len(ids)!=len(set(ids)):raise ValueError('IDs duplicados ou conjunto vazio.')
    novas=[]
    for r in rows:
        if isinstance(r['confianca'],bool):raise ValueError('Confiança inválida.')
        c=float(r['confianca'])
        if not math.isfinite(c) or not 0<=c<=1:raise ValueError('Confiança inválida.')
        if r['decisao'] not in ['publicar','revisar','fora']:raise ValueError('Decisão inválida.')
        elegivel=booleano(r['elegivel'])
        d=r['decisao'] if r['decisao'] in ['publicar','fora'] else 'publicar' if elegivel and c>=corte else 'revisar'
        novas.append({**r,'decisao_antes':r['decisao'],'decisao':d,'corte_experimental':corte})
    return novas
def medidas(rows,antes):
    pubs=[r for r in rows if r['decisao']=='publicar'];base={r['id']:r for r in antes}
    novas=[r for r in pubs if base[r['id']]['decisao']!='publicar']
    rotulado=all('correto' in r for r in rows)
    z={'questoes':len(rows),'publicar':len(pubs),'revisar':sum(r['decisao']=='revisar' for r in rows),
       'cobertura':len(pubs)/len(rows),'novas_publicacoes':len(novas),'precisao_real':None}
    if rotulado:
        ac=sum(int(r['correto']) for r in pubs)
        z.update({'acertos_publicadas':ac,'erros_publicadas':len(pubs)-ac,
            'precisao_publicadas':ac/len(pubs) if pubs else None,
            'novas_corretas':sum(int(r['correto']) for r in novas),
            'novas_erradas':sum(1-int(r['correto']) for r in novas),
            'precisao_acrescimos':sum(int(r['correto']) for r in novas)/len(novas) if novas else None,
            'meta_95_na_amostra':bool(pubs and ac/len(pubs)>=.95)})
    return z
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);origem=projeto/'experimentos/palavra_v12_001'
    entradas=['avaliacao_100.csv','simulacao_559.csv','modelos_finais.json']
    hashes={n:sha(origem/n) for n in entradas}
    gravar(saida/'protocolo_previo.json',{'corte':.5,'hipotese':'Aumentar publicação com confiança >=50%, sem alterar tema ou probabilidade.',
        'regra':'Preserva publicar e fora anteriores; somente revisões elegíveis e confiança >=0,5 podem mudar. A política interna ativa/corte V12 não impede essa nova regra experimental.',
        'retreino':False,'recalibracao':False,'consulta_rotulo_para_decidir':False,'ajuste_por_id':False,
        'escolha_corte_por_resultado':False,'promove_entrega':False,
        'limite':'Resultados nas mesmas 100 reutilizadas, sem avaliação independente das 559.',
        'codigo_sha256':sha(Path(__file__)),'entradas_sha256':hashes})
    rows100=ler(origem/'avaliacao_100.csv');rows559=ler(origem/'simulacao_559.csv')
    variantes=list(dict.fromkeys(r['variante'] for r in rows100));resultado={};aa=[];bb=[]
    for v in variantes:
        a=[r for r in rows100 if r['variante']==v and r['politica']=='preservar_v11']
        b=[r for r in rows559 if r['variante']==v and r['politica']=='preservar_v11']
        if len(a)!=100 or len(b)!=559:raise ValueError('Conjuntos inesperados.')
        na,nb=aplicar(a),aplicar(b)
        for x,y in zip(a,na):assert x['confianca']==y['confianca'] and x['tema_central_id']==y['tema_central_id']
        for x,y in zip(b,nb):assert x['confianca']==y['confianca'] and x['tema_central_id']==y['tema_central_id']
        resultado[v]={'antes_100':medidas(a,a),'corte50_100':medidas(na,a),
            'antes_559':medidas(b,b),'corte50_559':medidas(nb,b),
            'corte50_300_recentes':medidas([r for r in nb if int(r['id'][1:])>=360],[r for r in b if int(r['id'][1:])>=360])}
        aa.extend(na);bb.extend(nb)
    csv_gravar(saida/'avaliacao_100_corte50.csv',aa);csv_gravar(saida/'simulacao_559_corte50.csv',bb)
    gravar(saida/'resumo.json',resultado)
    for n,h in hashes.items():
        if sha(origem/n)!=h:raise ValueError('Origem alterada.')
    print(json.dumps(resultado,ensure_ascii=False,indent=2));return resultado

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
