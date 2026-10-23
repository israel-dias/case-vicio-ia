"""V15 mais suplemento V16, com cálculo real para textos novos e sem rótulos."""
import argparse,csv,json
from pathlib import Path
from classificar_roteamento_v15 import verificar
from compatibilidade_v2.runtime import legado,sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.ranking import aplicar as aplicar_v8
from experimento_atributos_v11 import modelo as v11
from experimento_palavra_v12 import modelo as v12
from roteamento_v15 import modelo as v15
from multivista_v16 import modelo as m

def executar(projeto,questoes,saida,ampliacao=None):
    projeto,questoes,saida=map(lambda x:Path(x).resolve(),[projeto,questoes,saida])
    ampliacao=Path(ampliacao).resolve() if ampliacao else projeto/'experimentos/ampliacao_v15_v16_002'
    if saida.exists():raise ValueError('Use saída nova.')
    e=projeto/'experimentos/multivista_v16_001';reg=json.loads((e/'manifesto_inferencia.json').read_text());amp=json.loads((ampliacao/'manifesto_ampliacao.json').read_text())
    verificar(projeto,reg['projeto_sha256']);verificar(e,reg['experimento_sha256']);verificar(projeto,amp['projeto_sha256'])
    if sha(e/'manifesto_inferencia.json')!=amp['base_v16_manifesto_sha256']:raise ValueError('Manifesto base diferente.')
    cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    snapshot=json.loads((e/'catalogo_preparado.json').read_text());qs={q['id']:q for q in legado.ler_questoes(questoes)}
    pp=m.preparar(cat,dic,snapshot,qs,com_legado_original=True)
    pack=json.loads((projeto/'experimentos/palavra_v12_001/modelos_finais.json').read_text());old={i:p['legado'] for i,p in pp['condicional_v15'].items()};taxa=pack['identificador']['confianca']
    cv9=v11.identificadores(aplicar_v8(old,pack['controle_v9'],cat),old,taxa)
    cv11=v12.combinar(v11.identificadores(v12.aplicar(old,pack['controle_v11'],cat,'controle_v11'),old,taxa),cv9)
    anterior=json.loads((projeto/'experimentos/roteamento_v15_002/modelos_finais.json').read_text())['foco_contextual']
    # O perfil condicional tem os mesmos 27 atributos/mesmo ranking do foco
    # V15. A máscara nova só é aplicada no modelo V16, não ao reaplicar V15.
    base=v11.preservar_publicadas(v15.aplicar(pp['condicional_v15'],anterior,cat,'foco_contextual','70'),cv11)
    novo=json.loads((e/'modelos_finais.json').read_text())['busca_multivista']
    suplemento=m.aplicar(pp['busca_multivista'],novo,cat,'busca_multivista','calibrado')
    rows=v11.preservar_publicadas(suplemento,base);rows.sort(key=lambda r:r['id']);saida.mkdir(parents=True)
    campos=['id','decisao','tema_central_id','extras_ids','confianca','motivo']
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=campos);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{'extras_ids':'','motivo':'EXPERIMENTAL: preservada V15' if r.get('publicacao_preservada') else 'EXPERIMENTAL: suplemento BM25 V16 calibrado'})
    with (saida/'base_v15_recalculada.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=['id','decisao','tema_central_id','confianca']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in sorted(base,key=lambda r:r['id']))
    resumo={'questoes':len(rows),'publicar':sum(r['decisao']=='publicar' for r in rows),'revisar':sum(r['decisao']=='revisar' for r in rows),'fora':0,
        'base_v15_publicadas':sum(r['decisao']=='publicar' for r in base),
        'precisao_real':None,'rotulos_lidos':False,'retreino':False,'chamadas_llm':0,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resumo,ensure_ascii=False,indent=2));return rows
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--questoes',type=Path,default=Path('experimentos/roteamento_v15_002/questoes_559_sem_rotulos.jsonl'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.questoes,z.saida)
