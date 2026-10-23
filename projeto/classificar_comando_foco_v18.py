"""Inferência com cobrança extraída estruturalmente, sem LLM ou rótulos."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import legado,validar_linear
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from isolamento_v17.metricas import medir
from contexto_v18 import foco as m


def executar(projeto,experimento,questoes,saida,variante='selecionado'):
    projeto,experimento,questoes,saida=[Path(x).resolve() for x in [projeto,experimento,questoes,saida]]
    if saida.exists():raise ValueError('Use saída nova.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text())
    if reg['versao']!='comando_foco_v18_1':raise ValueError('Versão incompatível.')
    verificar(projeto,reg['projeto_sha256']);verificar(experimento,reg['artefatos_sha256'])
    packs=json.loads((experimento/'modelos_finais.json').read_text())
    if variante=='selecionado':variante=packs['selecionado']
    if variante not in m.VARIANTES:raise ValueError('Variante desconhecida.')
    pack=packs['modelos'][variante];validar_linear(pack['modelo'],len(m.ATRIBUTOS[variante]));validar_linear(pack['calibrador'],1)
    cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)};ps=m.preparar(cat,dic,qs)
    rows=sorted(m.aplicar(ps[variante],pack,cat,variante),key=lambda r:r['id']);saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca','motivo']}|{'extras_ids':''})
    with (saida/'rastreabilidade.jsonl').open('w',encoding='utf-8') as arq:
        for r in rows:
            p=ps[variante][r['id']]
            arq.write(json.dumps({**r,'extracao':p['extracao_comando'],'identificacao':p['identificacao'],'rota':p['rota']},ensure_ascii=False)+'\n')
    resumo=medir(rows)|{'variante':variante,'rotulos_lidos':False,'treino_supervisionado':False,'chamadas_llm':0,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2),flush=True);return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/comando_foco_v18_001'))
    p.add_argument('--questoes',type=Path,default=Path('experimentos/comando_foco_v18_001/questoes_559_sem_rotulos.jsonl'))
    p.add_argument('--saida',type=Path,required=True);p.add_argument('--variante',choices=['selecionado',*m.VARIANTES],default='selecionado')
    z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.saida,z.variante)
