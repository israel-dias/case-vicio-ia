"""Inferência V24 a partir do texto, com checkpoints e sem rótulos ou LLM."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2.runtime import legado,sha
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from rotear_comando_v18 import executar as executar_base
from cobranca_v24 import modelo as m
from cobranca_v24.texto import Leitura
from testar_isolamento_v17 import gravar


def executar(projeto,questoes,saida,experimento=None,bloco=40):
    projeto,questoes,saida=map(lambda p:Path(p).resolve(),[projeto,questoes,saida]);e=Path(experimento).resolve() if experimento else projeto/'experimentos/cobranca_v24_002';t=time.perf_counter()
    if bloco<1:raise ValueError('Bloco deve ser positivo.')
    reg=json.loads((e/'manifesto_inferencia.json').read_text());verificar(projeto,reg['projeto_sha256']);verificar(e,reg['artefatos_sha256'])
    packs=json.loads((e/'modelos_finais.json').read_text());v=packs['selecionado']['variante'];modo=packs['selecionado']['modo'];pack=packs['modelos'][v]
    qs={q['id']:q for q in legado.ler_questoes(questoes)};cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias);leitor=Leitura(cat)
    check=saida/'checkpoints';protocolo={'questoes_sha256':sha(questoes),'manifesto_sha256':sha(e/'manifesto_inferencia.json'),'codigo_inferencia_sha256':sha(Path(__file__)),'bloco':bloco}
    if (saida/'classificacoes.csv').exists():raise ValueError('Inferência já concluída; use uma saída nova.')
    check.mkdir(parents=True,exist_ok=True)
    if (check/'protocolo.json').exists():
        if json.loads((check/'protocolo.json').read_text())!=protocolo:raise ValueError('Checkpoints de outra execução.')
    else:gravar(check/'protocolo.json',protocolo)
    ids=sorted(qs);todas=[];traces=[]
    for n,inicio in enumerate(range(0,len(ids),bloco),1):
        grupo=ids[inicio:inicio+bloco];p=check/f'bloco_{n:03}.json'
        if p.exists():
            salvas=json.loads(p.read_text());rr=salvas['previsoes'];tt=salvas['leituras']
            if len(rr)!=len(grupo) or {r['id'] for r in rr}!=set(grupo):raise ValueError('Checkpoint incompleto.')
        else:
            entradas={i:qs[i] for i in grupo};arq=check/f'entrada_{n:03}.jsonl';arq.write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in entradas.values()))
            antigas=executar_base(projeto,arq,check/f'base_{n:03}')
            pp=m.preparar(cat,dic,entradas);novas=m.aplicar(pp[v],pack,cat,v);rr=m.compor(novas,antigas,entradas,leitor,modo)
            tt=[{'id':i,**pp[v][i]['leitura_v24']} for i in grupo];gravar(p,{'previsoes':rr,'leituras':tt})
        todas.extend(rr);traces.extend(tt);print(f'V24: {min(inicio+bloco,len(ids))}/{len(ids)} questões classificadas; checkpoint salvo.',flush=True)
    campos=['id','decisao','tema_central_id','extras_ids','confianca','motivo']
    with (saida/'classificacoes.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=campos);w.writeheader()
        for r in sorted(todas,key=lambda r:r['id']):w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{'extras_ids':'','motivo':r.get('motivo','')})
    (saida/'rastreabilidade.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sorted(todas,key=lambda r:r['id'])))
    (saida/'leituras.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in traces))
    gravar(saida/'resumo.json',{'questoes':len(todas),'publicar':sum(r['decisao']=='publicar' for r in todas),'revisar':sum(r['decisao']=='revisar' for r in todas),'fora':0,'rotulos_lidos':False,'chamadas_llm':0,'retreino':False,'segundos':time.perf_counter()-t,'variante':v,'modo':modo,'precisao_real_alvo':None})
    return todas


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'));p.add_argument('--saida',type=Path,required=True);p.add_argument('--experimento',type=Path);p.add_argument('--bloco',type=int,default=40);z=p.parse_args();executar(z.projeto,z.questoes,z.saida,z.experimento,z.bloco)
