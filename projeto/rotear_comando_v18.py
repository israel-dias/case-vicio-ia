"""Recalcula controle V16 e leitura estrita V18 para textos novos, sem rótulos."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import sha
from classificar_roteamento_v15 import verificar
from classificar_ampliacao_v16 import executar as executar_base
from classificar_contexto_v18 import executar as executar_nova
from contexto_v18.roteamento import compor,POLITICAS
from isolamento_v17.metricas import medir


def executar(projeto,questoes,saida,politica='selecionada'):
    projeto,questoes,saida=[Path(x).resolve() for x in [projeto,questoes,saida]]
    if saida.exists():raise ValueError('Use saída nova.')
    estudo=projeto/'experimentos/roteamento_comando_v18_001';ex=projeto/'experimentos/contexto_v18_002'
    reg=json.loads((estudo/'manifesto_roteamento.json').read_text())
    verificar(projeto,reg['projeto_sha256'])
    for arq,h in [(estudo/'escolha_antes_uniao_559.json',reg['escolha_sha256']),
                  (ex/'manifesto_inferencia.json',reg['manifesto_v18_sha256']),
                  (projeto/'experimentos/ampliacao_v15_v16_002/manifesto_ampliacao.json',reg['manifesto_v16_sha256'])]:
        if sha(arq)!=h:raise ValueError('Manifesto de composição alterado.')
    if politica=='selecionada':politica=json.loads((estudo/'escolha_antes_uniao_559.json').read_text())['politica']
    if politica not in POLITICAS:raise ValueError('Nenhuma política elegível ou política desconhecida.')
    base=executar_base(projeto,questoes,saida/'controle_v16')
    nova=executar_nova(projeto,ex,questoes,saida/'comando_v18','comando_estrito')
    rows=sorted(compor(nova,base,politica),key=lambda r:r['id'])
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca','motivo']}|{'extras_ids':''})
    resumo=medir(rows)|{'politica':politica,'precisao_real_559':None,'chamadas_llm':0,'promove_entrega':False,
                       'calibracao_global_da_composicao':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2));return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--questoes',type=Path,default=Path('experimentos/contexto_v18_002/questoes_559_sem_rotulos.jsonl'))
    p.add_argument('--saida',type=Path,required=True);p.add_argument('--politica',choices=['selecionada',*POLITICAS],default='selecionada')
    z=p.parse_args();executar(z.projeto,z.questoes,z.saida,z.politica)
