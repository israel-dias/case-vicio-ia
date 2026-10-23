"""Inferência contextual com sinais E5 em cache, sem encoder ou treino."""
import argparse,csv,json,time
from pathlib import Path
from classificar_roteamento_v15 import verificar
from compatibilidade_v2.runtime import legado,sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from semantica_v22 import modelo as m


def executar(projeto,experimento,questoes,saida,variante=None):
    projeto,experimento,questoes,saida=map(lambda p:Path(p).resolve(),[projeto,experimento,questoes,saida]);inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text());verificar(projeto,reg['projeto_sha256']);verificar(experimento,reg['artefatos_sha256'])
    if sha(projeto/'artefatos/semantica_v21/manifesto.json')!=reg['cache_manifesto_sha256']:raise ValueError('Cache diferente.')
    packs=json.loads((experimento/'modelos_finais.json').read_text());v=variante or packs['selecionado']
    if v not in m.VARIANTES:raise ValueError('Variante inválida.')
    qs={q['id']:q for q in legado.ler_questoes(questoes)};cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    pp=m.preparar(projeto,cat,dic,qs);rr=m.aplicar(pp[v],packs['modelos'][v],cat,v)
    saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',newline='',encoding='utf-8') as g:
        w=csv.DictWriter(g,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in sorted(rr,key=lambda r:r['id']):w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca','motivo']}|{'extras_ids':''})
    (saida/'rastreabilidade.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sorted(rr,key=lambda r:r['id'])))
    resumo={'questoes':len(rr),'publicar':sum(r['decisao']=='publicar' for r in rr),'revisar':sum(r['decisao']=='revisar' for r in rr),'fora':0,'variante':v,'rotulos_lidos':False,'retreino':False,'encoder_carregado':False,'chamadas_llm':0,'segundos':time.perf_counter()-inicio,'precisao_real_559':None,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resumo,ensure_ascii=False,indent=2));return rr


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,default=Path('experimentos/semantica_v22_001'));p.add_argument('--questoes',type=Path,default=Path('experimentos/semantica_v22_001/questoes_559_sem_rotulos.jsonl'));p.add_argument('--saida',type=Path,required=True);p.add_argument('--variante',choices=m.VARIANTES);z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.saida,z.variante)
