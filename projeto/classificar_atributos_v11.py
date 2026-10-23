"""Inferência v11: classificador clássico congelado, sem rótulos/LLM/rede."""
import argparse
import csv
import json
from pathlib import Path
from compatibilidade_v2.runtime import legado,sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.ranking import aplicar as aplicar_v8
from experimento_atributos_v11.modelo import preparar,aplicar,identificadores,preservar_publicadas,REMOCOES,ATRIBUTOS,indices


def executar(projeto,experimento,questoes,saida,variante,politica='preservar'):
    projeto,experimento,questoes,saida=map(lambda p:Path(p).resolve(),[projeto,experimento,questoes,saida])
    if saida.exists():raise ValueError('Use uma pasta de saída nova.')
    if variante not in REMOCOES or politica not in {'preservar','substituir'}:raise ValueError('Variante/política desconhecida.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text())
    for n,h in reg['codigo_sha256'].items():
        p=(projeto/n).resolve()
        if not p.is_relative_to(projeto) or sha(p)!=h:raise ValueError('Código alterado: '+n)
    for n,h in reg['artefatos_sha256'].items():
        p=(experimento/n).resolve()
        if not p.is_relative_to(experimento) or sha(p)!=h:raise ValueError('Artefato alterado: '+n)
    base=projeto/'experimentos/vocabulario_v8_ranking_001'
    old=json.loads((base/'manifesto_reproducao.json').read_text())
    if sha(base/'modelo_diagnostico.json')!=old['modelo_sha256']:raise ValueError('Modelo de controle alterado.')
    for n,h in old['codigo_sha256'].items():
        p=(projeto/n).resolve()
        if not p.is_relative_to(projeto) or sha(p)!=h:raise ValueError('Dependência v8 alterada: '+n)
    mod=json.loads((experimento/'modelos_finais.json').read_text())[variante]
    if mod['atributos']!=[ATRIBUTOS[j] for j in indices(variante)]:raise ValueError('Atributos incompatíveis.')
    taxa=json.loads((experimento/'estatistica_identificador.json').read_text())['confianca']
    cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)}
    pp=preparar(cat,dic,qs)
    controle=identificadores(aplicar_v8(pp,json.loads((base/'modelo_diagnostico.json').read_text()),cat),pp,taxa)
    novas=identificadores(aplicar(pp,mod,cat,variante),pp,taxa)
    rows=preservar_publicadas(novas,controle) if politica=='preservar' else novas
    rows.sort(key=lambda r:r['id']);saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca']}|{
            'extras_ids':'','motivo':f"EXPERIMENTAL: {variante}; política {politica}; "+('publicação do controle preservada.' if r.get('publicacao_preservada') else 'decisão pelo modelo/identificador.')})
    resumo={'variante':variante,'politica':politica,'questoes':len(rows),
        'publicar':sum(r['decisao']=='publicar' for r in rows),'revisar':sum(r['decisao']=='revisar' for r in rows),
        'publicacoes_preservadas':sum(r.get('publicacao_preservada',False) for r in rows),
        'folha_verdade_consultada':False,'treinamento':False,'chamadas_llm':0,
        'precisao_real':None,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/atributos_v11_001'))
    p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'))
    p.add_argument('--saida',type=Path,required=True);p.add_argument('--variante',choices=list(REMOCOES),required=True)
    p.add_argument('--politica',choices=['preservar','substituir'],default='preservar')
    z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.saida,z.variante,z.politica)
