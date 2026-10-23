"""Infere do texto com contexto novo e estimador antigo, sem LLM, treino ou rótulos."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import legado,validar_linear
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from isolamento_v17.metricas import medir
from contexto_v20 import modelo as m
from contexto_v20.preservado import aplicar

def executar(projeto,experimento,questoes,saida):
    projeto,experimento,questoes,saida=[Path(x).resolve() for x in [projeto,experimento,questoes,saida]]
    if saida.exists():raise ValueError('Use saída nova.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text())
    if reg['versao']!='contexto_preservado_v20_1':raise ValueError('Versão incompatível.')
    verificar(projeto,reg['codigo_sha256']);verificar(experimento,reg['artefatos_sha256'])
    pack=json.loads((experimento/'modelo_preservado.json').read_text());validar_linear(pack['modelo'],len(m.ATRIBUTOS['controle_atual']));validar_linear(pack['calibrador'],1)
    cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)};ps=m.preparar(cat,dic,qs)
    rr=sorted(aplicar(ps['escopos_contextuais'],pack,cat),key=lambda r:r['id']);saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as a:
        w=csv.DictWriter(a,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rr:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca','motivo']}|{'extras_ids':''})
    with (saida/'rastreabilidade.jsonl').open('w',encoding='utf-8') as a:
        for r in rr:a.write(json.dumps({**r,'evidencia_contextual':ps['escopos_contextuais'][r['id']]['evidencia_v19']},ensure_ascii=False)+'\n')
    resumo=medir(rr)|{'estimador_preservado':True,'rotulos_lidos':False,'treino_adicional':False,'chamadas_llm':0,'promove_entrega':False};(saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resumo,ensure_ascii=False));return rr

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,default=Path('experimentos/contexto_preservado_v20_001'));p.add_argument('--questoes',type=Path,default=Path('experimentos/contexto_v20_001/questoes_559_sem_rotulos.jsonl'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.saida)
