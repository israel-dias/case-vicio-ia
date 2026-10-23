"""Reproduz a simulação com pesos salvos, sem ler folha-verdade ou treinar."""
import argparse
import csv
import json
from pathlib import Path

from compatibilidade_v2.runtime import sha,legado
from melhorias_v3.representacao import carregar_catalogo
from mescla_marcadores_v7.experimento import preparar,aplicar,VARIANTES


def executar(projeto,experimento,questoes,saida,variante='mescla_condicional'):
    projeto,experimento,questoes,saida=map(lambda x:Path(x).resolve(),[projeto,experimento,questoes,saida])
    if saida.exists():raise ValueError('Saída existente. Escolha uma pasta nova.')
    if variante not in VARIANTES:raise ValueError('Variante inválida.')
    manifesto=json.loads((experimento/'manifesto_para_reproducao.json').read_text())
    if sha(experimento/'modelos_diagnosticos.json')!=manifesto['modelos_sha256']:
        raise ValueError('Modelo diagnóstico alterado.')
    for nome,h in manifesto['codigo_sha256'].items():
        p=(projeto/nome).resolve()
        if not p.is_relative_to(projeto) or sha(p)!=h:raise ValueError('Código alterado: '+nome)
    modelos=json.loads((experimento/'modelos_diagnosticos.json').read_text())
    m=modelos[variante]
    cat,_=carregar_catalogo(projeto)
    qs={q['id']:q for q in legado.ler_questoes(questoes)}
    pp=preparar(cat,qs)
    rows=aplicar(pp,m['modelo'],cat,variante,m['calibrador'],m['politica'])
    saida.mkdir(parents=True)
    campos=['id','decisao','tema_central_id','extras_ids','confianca','motivo']
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as file:
        w=csv.DictWriter(file,fieldnames=campos);w.writeheader()
        for r in sorted(rows,key=lambda r:r['id']):
            w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{
                'extras_ids':'','motivo':f"EXPERIMENTAL: {r['modo']}; corte congelado {m['politica']['limiar']}."})
    resumo={'questoes':len(rows),'variante':variante,
        'decisoes':{d:sum(r['decisao']==d for r in rows) for d in ['publicar','revisar','fora']},
        'precisao_real':None,'folha_verdade_consultada':False,'treinamento_executado':False,
        'chamadas_llm':0,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(resumo,indent=2,ensure_ascii=False))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/mescla_marcadores_v7_002'))
    p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'))
    p.add_argument('--saida',type=Path,required=True)
    p.add_argument('--variante',choices=VARIANTES,default='mescla_condicional')
    a=p.parse_args();executar(a.projeto,a.experimento,a.questoes,a.saida,a.variante)
