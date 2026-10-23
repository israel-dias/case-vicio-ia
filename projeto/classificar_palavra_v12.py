"""Inferência experimental V12 offline, sem folha-verdade, treino ou LLM."""
import argparse
import csv
import json
from pathlib import Path
from compatibilidade_v2.runtime import legado,sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.ranking import aplicar as aplicar_v8
from experimento_atributos_v11 import modelo as v11
from experimento_palavra_v12 import modelo as v12

def verificar_hashes(raiz,arquivos):
    for n,h in arquivos.items():
        p=(raiz/n).resolve()
        if not p.is_relative_to(raiz) or sha(p)!=h: raise ValueError('Código ou artefato alterado: '+n)

def executar(projeto,experimento,questoes,saida,variante,politica='preservar_v11'):
    projeto,experimento,questoes,saida=map(lambda p:Path(p).resolve(),[projeto,experimento,questoes,saida])
    if saida.exists(): raise ValueError('Use uma pasta de saída nova.')
    if variante not in v12.VARIANTES or politica not in ['substituir_com_v9','preservar_v11']: raise ValueError('Variante/política desconhecida.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text())
    verificar_hashes(projeto,reg['projeto_sha256']);verificar_hashes(experimento,reg['experimento_sha256'])
    pack=json.loads((experimento/'modelos_finais.json').read_text())
    cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)}
    pp=v12.preparar(cat,dic,qs);taxa=pack['identificador']['confianca']
    cv9=v11.identificadores(aplicar_v8(pp,pack['controle_v9'],cat),pp,taxa)
    cv11=v12.combinar(v11.identificadores(v12.aplicar(pp,pack['controle_v11'],cat,'controle_v11'),pp,taxa),cv9)
    novas=v11.identificadores(v12.aplicar(pp,pack['variantes'][variante],cat,variante),pp,taxa)
    rows=v12.combinar(novas,cv9)
    if politica=='preservar_v11': rows=v12.combinar(rows,cv11)
    rows.sort(key=lambda r:r['id']);saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rows:
            w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{'extras_ids':'',
                'motivo':f'EXPERIMENTAL: {variante}; {politica}; modelo clássico/identificador, sem gabarito; conferir sugestão.' if r['decisao']=='revisar' else f'EXPERIMENTAL: {variante}; {politica}.'})
    resumo={'variante':variante,'politica':politica,'questoes':len(rows),
        'publicar':sum(r['decisao']=='publicar' for r in rows),'revisar':sum(r['decisao']=='revisar' for r in rows),
        'fora':0,'precisao_real':None,'folha_verdade_consultada':False,'chamadas_llm':0,'treinamento':False,
        'corte_50_testado':False,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/palavra_v12_001'))
    p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'))
    p.add_argument('--variante',choices=list(v12.VARIANTES),required=True)
    p.add_argument('--politica',choices=['substituir_com_v9','preservar_v11'],default='preservar_v11')
    p.add_argument('--saida',type=Path,required=True);z=p.parse_args()
    executar(z.projeto,z.experimento,z.questoes,z.saida,z.variante,z.politica)
