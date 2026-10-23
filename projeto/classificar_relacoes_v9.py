"""Inferência experimental v9, inclusive para questões novas; sem rótulos ou rede."""
import argparse
import csv
import json
from pathlib import Path
from compatibilidade_v2.runtime import legado, sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.experimento import preparar
from vocabulario_v8.ranking import aplicar
from experimento_relacoes_v9.regras import Identificador, VARIANTES


def executar(projeto, questoes, saida, variante, artefato):
    projeto,questoes,saida,artefato=map(lambda p:Path(p).resolve(),[projeto,questoes,saida,artefato])
    if saida.exists():raise ValueError('Use uma pasta de saída nova.')
    if variante not in VARIANTES:raise ValueError('Variante desconhecida.')
    registro=json.loads(artefato.read_text())
    for n,h in registro['codigo_sha256'].items():
        p=(projeto/n).resolve()
        if not p.is_relative_to(projeto) or sha(p)!=h:raise ValueError('Código v9 alterado: '+n)
    base=projeto/'experimentos/vocabulario_v8_ranking_001'
    manifest=json.loads((base/'manifesto_reproducao.json').read_text())
    if sha(base/'modelo_diagnostico.json')!=manifest['modelo_sha256']:raise ValueError('Modelo v8 alterado.')
    for n,h in manifest['codigo_sha256'].items():
        p=(projeto/n).resolve()
        if not p.is_relative_to(projeto) or sha(p)!=h:raise ValueError('Código v8 alterado: '+n)
    modelo=json.loads((base/'modelo_diagnostico.json').read_text())
    cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    ident=Identificador(cat,dic)
    qs={q['id']:q for q in legado.ler_questoes(questoes)}
    traces={i:ident.analisar(q) for i,q in qs.items()}
    diretas={i:r['variantes'][variante] for i,r in traces.items() if r['variantes'][variante]['acionou']}
    pendentes={i:q for i,q in qs.items() if i not in diretas}
    # O cálculo de compatibilidade/calibração v8 é pulado nas regras diretas.
    resto=aplicar(preparar(cat,dic,pendentes),modelo,cat) if pendentes else []
    confianca=registro['variantes'][variante]['probabilidade_suavizada']
    rows=[{'id':i,'decisao':'publicar','tema_central_id':r['tema_regra'],
           'confianca':confianca,'motivo':r['motivo']} for i,r in diretas.items()]
    rows.extend({'id':r['id'],'decisao':r['decisao'],'tema_central_id':r['tema_central_id'],
                 'confianca':r['confianca'],'motivo':'controle_v8'} for r in resto)
    rows.sort(key=lambda r:r['id'])
    saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (saida/'rastros.json').write_text(json.dumps(traces,ensure_ascii=False,indent=2)+'\n')
    resumo={'variante':variante,'questoes':len(rows),'regras_diretas':len(diretas),
        'publicar':sum(r['decisao']=='publicar' for r in rows),'revisar':sum(r['decisao']=='revisar' for r in rows),
        'folha_verdade_consultada':False,'chamadas_llm':0,'treinamento':False,
        'precisao_real':None,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'))
    p.add_argument('--artefato',type=Path,default=Path('experimento_relacoes_v9/artefato_regra.json'))
    p.add_argument('--variante',choices=VARIANTES,default='titulos_diretos');p.add_argument('--saida',type=Path,required=True)
    a=p.parse_args();executar(a.projeto,a.questoes,a.saida,a.variante,a.artefato)
