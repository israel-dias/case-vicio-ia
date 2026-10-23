"""Composição adaptativa: restringe a mudança aos comandos identificados."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import sha
from isolamento_v17.metricas import medir
from testar_isolamento_v17 import controle,gravar,csv_salvar
from contexto_v18.roteamento import POLITICAS,compor


def linhas(path,avaliacao):
    with path.open() as arq:rr=[r for r in csv.DictReader(arq) if r[avaliacao[0]]==avaliacao[1]]
    for r in rr:
        r['confianca']=float(r['confianca'])
        for k in ['correto','fora_oficial','fold']:
            if k in r:r[k]=int(r[k])
        r['identificador_forte_cmd']=r['identificador_forte_cmd']=='True'
    return rr


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);ex=projeto/'experimentos/contexto_v18_002'
    gravar(saida/'protocolo_previo.json',{'versao':'roteamento_comando_v18_1','politicas':POLITICAS,
        'adaptativo':True,'cronologia':'Depois de observar a referência e as saídas individuais V18 nas 559; escolha da composição somente nas 100 antes de calcular sua união no alvo.',
        'comando_prioritario':'Nova regra em todos os casos acionados; controle anterior nos demais.',
        'suplemento_revisoes':'Mantém publicadas antigas; aplica nova regra só às revisões com identificador forte. Não é aplicação universal da regra estrita.',
        'publicacao':'Depende da política calibrada da rota, nunca só do gatilho.',
        'escolha':'Precisão empírica >=95%, suporte >=10; maior publicação na referência. Sem ajustar temas, pesos ou cortes por ID.',
        'precisao_real_alvo':None,'calibracao_global_da_composicao':False,'promove_entrega':False,
        'codigo_sha256':{n:sha(projeto/n) for n in ['contexto_v18/roteamento.py','rotear_comando_v18.py','testar_roteamento_comando_v18.py']}})
    base100=controle(projeto,'avaliacao_desenvolvimento_100.csv')
    novas100=linhas(ex/'avaliacao_100.csv',('avaliacao','comando_estrito'))
    resultado100={p:compor(novas100,base100,p) for p in POLITICAS}
    resumo={p:{'desenvolvimento_100':medir(rr,base100)} for p,rr in resultado100.items()}
    elegiveis=[p for p in POLITICAS if resumo[p]['desenvolvimento_100']['meta_95_na_amostra'] and resumo[p]['desenvolvimento_100']['publicar']>=10]
    escolha=max(elegiveis,key=lambda p:(resumo[p]['desenvolvimento_100']['publicar'],-resumo[p]['desenvolvimento_100']['erros_publicadas'],-POLITICAS.index(p))) if elegiveis else None
    gravar(saida/'escolha_antes_uniao_559.json',{'politica':escolha,'adaptativo':True,'fonte':'Referências já expostas. Volumes das variantes individuais conhecidos; união no alvo ainda não calculada.','promove_entrega':False})
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'composicao':p} for p,rr in resultado100.items() for r in rr])
    base559=controle(projeto,'classificacoes_559_todas_variantes.csv')
    novas559=linhas(ex/'classificacoes_559_todas_variantes.csv',('variante','comando_estrito'))
    todas=[]
    for p in POLITICAS:
        rr=compor(novas559,base559,p);todas.extend({**r,'composicao':p} for r in rr)
        resumo[p]['alvo_559']=medir(rr,base559)
        resumo[p]['recentes_300']=medir([r for r in rr if int(r['id'][1:])>=360])
    csv_salvar(saida/'classificacoes_559_todas_politicas.csv',todas)
    gravar(saida/'resumo.json',resumo)
    gravar(saida/'manifesto_roteamento.json',{
        'versao':'roteamento_comando_v18_1',
        'projeto_sha256':{n:sha(projeto/n) for n in ['contexto_v18/roteamento.py','rotear_comando_v18.py']},
        'escolha_sha256':sha(saida/'escolha_antes_uniao_559.json'),
        'manifesto_v18_sha256':sha(ex/'manifesto_inferencia.json'),
        'manifesto_v16_sha256':sha(projeto/'experimentos/ampliacao_v15_v16_002/manifesto_ampliacao.json'),
        'promove_entrega':False})
    print(json.dumps({'escolha':escolha,'resumo':resumo},ensure_ascii=False,indent=2));return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
