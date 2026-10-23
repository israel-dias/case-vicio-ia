"""Teste diagnóstico: nunca substitui os arquivos de entrega."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from experimento_relacoes_v9.regras import Identificador, VARIANTES, PESO_CONTEXTO, PESO_ALTERNATIVAS, MARGEM_RELATIVA_MINIMA


def gravar(p, valor):
    p.write_text(json.dumps(valor, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def csv_gravar(p, rows):
    with p.open('w', encoding='utf-8', newline='') as arq:
        w=csv.DictWriter(arq, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def taxa_regras(ids, nome, rastros, ys, temas, hashes, excluir=()):
    ex=set(excluir)
    validos=[i for i in ids if hashes[i] not in ex and rastros[i]['variantes'][nome]['acionou']]
    acertos=sum(f.aceito(rastros[i]['variantes'][nome]['tema_regra'],ys[i],temas) for i in validos)
    return {'n':len(validos),'acertos':acertos,'probabilidade_suavizada':(acertos+1)/(len(validos)+2)}


def executar(projeto, saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use uma pasta de saída nova.')
    base=projeto/'experimentos/vocabulario_v8_ranking_001'
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt']}
    saida.mkdir(parents=True)
    protocolo={'variantes':list(VARIANTES),'controle':'v8_vocabulário_somente_busca',
        'regra':'Publicar quando a regra produzir um único candidato; nas outras situações, preservar controle.',
        'relacoes':'Última referência com título/sinônimo conhecido; caso contrário, enunciado efetivo completo.',
        'rodada':4,'ajustes_posteriores':'Preserva rodadas 1-3; Conduta/Resultado só acionam em frases técnicas completas versionadas, conforme orientação do candidato. Palavra ou par genérico não bastam.',
        'considerando_e_marcador':False,'peso_contexto':PESO_CONTEXTO,'peso_alternativas':PESO_ALTERNATIVAS,
        'margem_desambiguacao':MARGEM_RELATIVA_MINIMA,'busca_de_hiperparametros':False,
        'confianca':'Taxa suavizada Beta(1,1) dos acionamentos nos outros folds, excluindo textos duplicados. Não é piso de 80%.',
        'avaliacao':'100 rótulos já expostos; experimento de desenvolvimento, não teste externo cego.',
        'fora_automatico':False,'sem_rotulo_559':'Somente contagens e alterações, sem precisão real.',
        'promove_entrega':False,'chamadas_llm':0,
        'arquivos_preservados_sha256':preservados,
        'codigo_sha256':{n:sha(projeto/n) for n in ['testar_relacoes_v9.py','experimento_relacoes_v9/regras.py']},
        'controle_modelo_sha256':sha(base/'modelo_diagnostico.json'),
        'anexos_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']}}
    gravar(saida/'protocolo_previo.json',protocolo)
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    identificador=Identificador(cat,dic)
    rastros={i:identificador.analisar(q) for i,q in qs.items()}
    gravar(saida/'rastros_659.json',rastros)
    hashes={i:f.campos(q)['hash'] for i,q in qs.items()}
    controle=list(csv.DictReader((base/'previsoes.csv').open()))
    simulacao=list(csv.DictReader((base/'simulacoes_559.csv').open()))
    grupos={}
    for n in range(1,6):
        grupos[str(n)]=json.loads((base/f'folds/fold_{n}.json').read_text())
    todas=[]; novas=[];resumo={}
    for nome in ('controle_v8',*VARIANTES):
        rows=[]
        for b in controle:
            i=b['id'];regra=rastros[i]['variantes'].get(nome, {'acionou':False})
            ativo=regra['acionou'];t=regra['tema_regra'] if ativo else b['tema_central_id']
            suporte=taxa_regras(grupos[b['fold']]['treino_ids'],nome,rastros,ys,temas,hashes,[hashes[i]]) if ativo else None
            rows.append({'id':i,'variante':nome,'fold':b['fold'],'tema_central_id':t,
                'decisao':'publicar' if ativo else b['decisao'],
                'confianca':suporte['probabilidade_suavizada'] if ativo else float(b['confianca']),
                'acionou_regra':ativo,'motivo_regra':regra.get('motivo','controle'),
                'correto':int(f.aceito(t,ys[i],temas)),'fora_oficial':int(ys[i]['fora_da_taxonomia']),
                'tema_controle':b['tema_central_id'],'decisao_controle':b['decisao'],
                'suporte_confianca':suporte['n'] if suporte else '',
                'central_oficial':ys[i]['tema_central_id'],'extras_oficiais':ys[i]['extras_ids']})
        pubs=[r for r in rows if r['decisao']=='publicar'];acionadas=[r for r in rows if r['acionou_regra']]
        resumo[nome]={'avaliadas':100,'acertos_top1':sum(r['correto'] for r in rows),
            'publicar':len(pubs),'acertos_publicadas':sum(r['correto'] for r in pubs),
            'precisao_publicadas':sum(r['correto'] for r in pubs)/len(pubs) if pubs else None,
            'regras_acionadas':len(acionadas),'acertos_regra':sum(r['correto'] for r in acionadas),
            'precisao_regra':sum(r['correto'] for r in acionadas)/len(acionadas) if acionadas else None,
            'publicou_fora_oficial':sum(r['fora_oficial'] for r in pubs),
            'correcoes_tema':sum(r['correto'] and not f.aceito(r['tema_controle'],ys[r['id']],temas) for r in rows),
            'regressoes_tema':sum(not r['correto'] and f.aceito(r['tema_controle'],ys[r['id']],temas) for r in rows)}
        todas.extend(rows)
        taxa=taxa_regras(ys,nome,rastros,ys,temas,hashes) if nome!='controle_v8' else None
        for b in simulacao:
            i=b['id'];regra=rastros[i]['variantes'].get(nome, {'acionou':False});ativo=regra['acionou']
            novas.append({'id':i,'variante':nome,'tema_central_id':regra['tema_regra'] if ativo else b['tema_central_id'],
                'decisao':'publicar' if ativo else b['decisao'],
                'confianca':taxa['probabilidade_suavizada'] if ativo else float(b['confianca']),
                'acionou_regra':ativo,'motivo_regra':regra.get('motivo','controle'),
                'tema_controle':b['tema_central_id'],'decisao_controle':b['decisao']})
        nr=[r for r in novas if r['variante']==nome];np=[r for r in nr if r['decisao']=='publicar']
        resumo[nome]['simulacao_559']={'publicar':len(np),'revisar':559-len(np),'cobertura':len(np)/559,
            'recentes_300_publicadas':sum(int(r['id'][1:])>=360 for r in np),
            'mudancas_tema':sum(r['tema_central_id']!=r['tema_controle'] for r in nr),'precisao_real':None}
    csv_gravar(saida/'avaliacao_100.csv',todas);csv_gravar(saida/'simulacao_559.csv',novas)
    erros=[r for r in todas if r['acionou_regra'] and not r['correto']]
    gravar(saida/'erros_regras_100.json',[dict(r,questao=qs[r['id']],rastro=rastros[r['id']]) for r in erros])
    if any(sha(projeto/n)!=h for n,h in preservados.items()):raise ValueError('Entrega original alterada.')
    gravar(saida/'resumo.json',resumo)
    print(json.dumps(resumo,ensure_ascii=False,indent=2))
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    a=p.parse_args();executar(a.projeto,a.saida)
