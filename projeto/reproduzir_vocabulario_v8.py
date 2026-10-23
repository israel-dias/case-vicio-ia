"""Inferência experimental com vocabulário só na busca: sem treino ou rótulos."""
import argparse
import csv
import json
from pathlib import Path
from compatibilidade_v2.runtime import sha,legado
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.experimento import preparar
from vocabulario_v8.ranking import aplicar


def executar(projeto,experimento,questoes,saida):
    projeto,experimento,questoes,saida=map(lambda x:Path(x).resolve(),[projeto,experimento,questoes,saida])
    if saida.exists():raise ValueError('Saída existente. Escolha outra pasta.')
    reg=json.loads((experimento/'manifesto_reproducao.json').read_text())
    if sha(experimento/'modelo_diagnostico.json')!=reg['modelo_sha256']:raise ValueError('Modelo alterado.')
    for nome,h in reg['codigo_sha256'].items():
        p=(projeto/nome).resolve()
        if not p.is_relative_to(projeto) or sha(p)!=h:raise ValueError('Código ou vocabulário alterado: '+nome)
    mod=json.loads((experimento/'modelo_diagnostico.json').read_text())
    cat,_=carregar_catalogo(projeto)
    d=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)}
    pp=preparar(cat,d,qs)
    rows=aplicar(pp,mod,cat)
    saida.mkdir(parents=True)
    campos=['id','decisao','tema_central_id','extras_ids','confianca','motivo']
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=campos);w.writeheader()
        for r in sorted(rows,key=lambda r:r['id']):
            w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{
                'extras_ids':'','motivo':f"EXPERIMENTAL: vocabulário na busca; corte {mod['politica']['limiar']}."})
    with (saida/'expressoes_detectadas.jsonl').open('w',encoding='utf-8') as arq:
        for i,p in pp.items():arq.write(json.dumps({'id':i,**p['vocabulario']},ensure_ascii=False)+'\n')
    resumo={'questoes':len(rows),'decisoes':{d:sum(r['decisao']==d for r in rows) for d in ['publicar','revisar','fora']},
        'precisao_real':None,'folha_verdade_consultada':False,'treinamento_executado':False,
        'chamadas_llm':0,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/vocabulario_v8_ranking_001'))
    p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'))
    p.add_argument('--saida',type=Path,required=True)
    a=p.parse_args();executar(a.projeto,a.experimento,a.questoes,a.saida)
