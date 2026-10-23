"""Avalia composição adaptativa; confianças de origem, sem calibração global."""
import csv,json,argparse
from pathlib import Path
from compatibilidade_v2.runtime import sha
from melhorias_v3.representacao import carregar_catalogo
from isolamento_v17.metricas import medir
from testar_isolamento_v17 import gravar,csv_salvar,dependencias
from expressoes_v19.guarda import combinar

VARIANTES=('frases_completas','vocabulario_escopos','passagem_cobrada')

def ler(p):
    rr=list(csv.DictReader(p.open()))
    for r in rr:
        r['confianca']=float(r['confianca'])
        for k in ['correto','fora_oficial']:
            if k in r:r[k]=int(r[k])
    return rr


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);exp=projeto/'experimentos/expressoes_v19_001';cat,_=carregar_catalogo(projeto)
    deps=dependencias(projeto);gravar(saida/'protocolo_previo.json',{'adaptativo_apos_erros_100':True,'regra':'Conservar previsão V18 quando a nova sugestão troca a disciplina prevista pelo controle. Disciplina de origem não é usada.','variantes':VARIANTES,'confianca_global_recalibrada':False,'limite':'Uma disciplina errada do controle pode ser mantida; não equivale à régua de pai/filho.','promove_entrega':False,'codigo_sha256':deps})
    rr=ler(exp/'avaliacao_100.csv');b=[r for r in rr if r['avaliacao']=='controle_atual'];res={};dev=[]
    for v in VARIANTES:
        novas=[r for r in rr if r['avaliacao']==v];z=combinar(b,novas,cat.temas);dev+=z
        res[v]={'desenvolvimento_100':medir(z,b),'erros_corrigidos':[r['id'] for r in z if r['correto'] and not next(x for x in b if x['id']==r['id'])['correto']],
                'acertos_prejudicados':[r['id'] for r in z if not r['correto'] and next(x for x in b if x['id']==r['id'])['correto']]}
    gravar(saida/'resultado_antes_559.json',res);csv_salvar(saida/'avaliacao_100.csv',dev)
    gravar(saida/'manifesto_inferencia.json',{'versao':'guarda_disciplina_v19_1','codigo_sha256':deps,
        'experimento_base':'experimentos/expressoes_v19_001','artefatos_base_sha256':{n:sha(exp/n) for n in ['modelos_finais.json','manifesto_inferencia.json']},'confianca_global_recalibrada':False,'promove_entrega':False})
    # O resultado das referências fica gravado antes de ler as decisões das 559.
    alvo=ler(exp/'classificacoes_559_todas_variantes.csv');b=[r for r in alvo if r['variante']=='controle_atual'];todos=[]
    for v in VARIANTES:
        z=combinar(b,[r for r in alvo if r['variante']==v],cat.temas);todos+=z
        res[v]['alvo_559']=medir(z,b);res[v]['recentes_300']=medir([r for r in z if int(r['id'][1:])>=360])
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',todos);gravar(saida/'resumo.json',res)
    print(json.dumps(res,ensure_ascii=False,indent=2));return res

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
