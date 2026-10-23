"""Inferência V15 sem rótulos, rede ou modelo de linguagem."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import legado,sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from roteamento_v15 import modelo as m
from experimento_atributos_v11 import modelo as v11
from experimento_palavra_v12 import modelo as v12
from vocabulario_v8.ranking import aplicar as aplicar_v8

def verificar(raiz,arquivos):
    for n,h in arquivos.items():
        p=(raiz/n).resolve()
        if not p.is_relative_to(raiz) or sha(p)!=h:raise ValueError('Código/artefato alterado: '+n)
def executar(projeto,experimento,questoes,saida,variante,corte,politica):
    projeto,experimento,questoes,saida=map(lambda p:Path(p).resolve(),[projeto,experimento,questoes,saida])
    if saida.exists():raise ValueError('Use saída nova.')
    if variante not in m.VARIANTES or corte not in ['calibrado','70'] or politica not in ['substituir','preservar_v11']:raise ValueError('Configuração inválida.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text());verificar(projeto,reg['projeto_sha256']);verificar(experimento,reg['experimento_sha256'])
    cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)};pp=m.preparar(cat,dic,qs)
    modelos=json.loads((experimento/'modelos_finais.json').read_text());rows=m.aplicar(pp[variante],modelos[variante],cat,variante,corte)
    if politica=='preservar_v11':
        pack=json.loads((projeto/'experimentos/palavra_v12_001/modelos_finais.json').read_text());old=v12.preparar(cat,dic,qs);taxa=pack['identificador']['confianca']
        cv9=v11.identificadores(aplicar_v8(old,pack['controle_v9'],cat),old,taxa)
        cv11=v12.combinar(v11.identificadores(v12.aplicar(old,pack['controle_v11'],cat,'controle_v11'),old,taxa),cv9)
        rows=v11.preservar_publicadas(rows,cv11)
    rows.sort(key=lambda r:r['id']);saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{'extras_ids':'',
            'motivo':f'EXPERIMENTAL V15: {variante}; corte {corte}; {politica}; '+('escopo homônimo não resolvido.' if r.get('homonimo_nao_resolvido') else 'sugestão do sistema clássico.')})
    resumo={'variante':variante,'corte':corte,'politica':politica,'questoes':len(rows),'publicar':sum(r['decisao']=='publicar' for r in rows),
        'revisar':sum(r['decisao']=='revisar' for r in rows),'fora':0,'precisao_real':None,
        'folha_verdade_consultada':False,'treinamento':False,'rede':False,'chamadas_llm':0,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resumo,ensure_ascii=False,indent=2));return rows
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,default=Path('experimentos/roteamento_v15_002'))
    p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'));p.add_argument('--saida',type=Path,required=True)
    p.add_argument('--variante',choices=list(m.VARIANTES),required=True);p.add_argument('--corte',choices=['calibrado','70'],default='calibrado');p.add_argument('--politica',choices=['substituir','preservar_v11'],default='substituir')
    z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.saida,z.variante,z.corte,z.politica)
