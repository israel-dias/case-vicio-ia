"""Ablação posterior: vocabulário só na busca, sem sete atributos novos.

A comparação foi motivada pelo resultado v8_001; não é hipótese cega nova.
A compatibilidade de 41 atributos da v7 é preservada, mas o calibrador e a
política são refeitos para os candidatos recuperados pela busca modificada.
"""
import csv
import json
from pathlib import Path
import time
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.experimento import gravar,csv_salvar,separar,validar_grupos
from melhorias_v3.representacao import carregar_catalogo
from mescla_marcadores_v7 import experimento as v7
from .texto import Dicionario
from .experimento import preparar


def sinais(perfis,mod,cat):
    rows=[]
    for i,p in perfis.items():
        k=int(f.ordenar(p['ranking_vocabulario_reordena'])[0])
        rows.append({'id':i,'tema_central_id':cat.familias[k],
            'sinal':float(a.escore_linear(p['x_mescla'][[k]],mod)[0]),
            'elegivel':bool(not p['rota']['conteudo_insuficiente'] and
                max(p['scores'][k],p['scores_novos'][k],p['scores_foco'][k],p['score_vocabulario'][k])>=.03)})
    return rows


def aplicar(pp,m,cat):
    ss=sinais(pp,m['modelo'],cat)
    return [{**r,'confianca':p,'decisao':f.decidir(r,p,m['politica'])}
            for r,p in zip(ss,a.confiancas(ss,m['calibrador']))]


def executar(projeto,saida):
    inicio=time.perf_counter();projeto=Path(projeto).resolve();saida=Path(saida).resolve()
    if saida.exists():raise ValueError('Saída já existe.')
    base=projeto/'experimentos/mescla_marcadores_v7_002'
    qs,temas,ys=f.carregar(projeto/'dados/anexos')
    cat,_=carregar_catalogo(projeto)
    dados=json.loads((projeto/'vocabulario_v8/dicionario.json').read_text())
    dic=Dicionario(dados,temas,cat.familias)
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    original=json.loads((base/'protocolo_previo.json').read_text())
    for n,h in original['codigo_sha256'].items():
        if sha(projeto/n)!=h:raise ValueError('Controle v7 alterado.')
    arquivos=['vocabulario_v8/dicionario.json','vocabulario_v8/texto.py','vocabulario_v8/experimento.py',
              'vocabulario_v8/ranking.py','avaliar_ranking_vocabulario_v8.py',*original['codigo_sha256']]
    hashes={n:sha(projeto/n) for n in arquivos}
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt']}
    gravar(saida/'protocolo_previo.json',{'hipotese':'Vocabulário modifica somente a recuperação de candidatos. Compatibilidade mantém os 41 atributos v7; nova calibração e corte.',
        'motivacao':'Ablação posterior ao experimento vocabulario_v8_001; resultados prévios conhecidos.',
        'novo_teste_externo':False,'novos_rotulos_559':False,'promove_entrega':False,
        'meta_empirica_interna':.95,'minimo_interno':10,'peso_vocabulario_ranking':.25,
        'codigo_sha256':hashes,'modelos_v7_sha256':sha(base/'modelos_diagnosticos.json'),
        'entrega_preservada_sha256':preservados,
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'folds_sha256':sha(projeto/'experimentos/melhorias_v3_001/auditoria_folds.json')})
    pp=preparar(cat,dic,{i:qs[i] for i in sorted(ys)});previsoes=[]
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(pp,tr,vl,ys)
        print(f'Vocabulário só na busca: fold externo {n}/5.',flush=True)
        internas=[]
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids']
            validar_grupos(pp,ti,vi,tr)
            mod=v7.ajustar(separar(pp,ti),{i:ys[i] for i in ti},cat,'mescla_condicional')
            internas.extend(a.avaliar(sinais(separar(pp,vi),mod,cat),{i:ys[i] for i in vi},temas))
        cal=a.calibrar(internas);pol=a.politica(internas,a.confiancas(internas,cal))
        anterior=json.loads((base/f'folds/fold_{n}.json').read_text())
        if anterior['treino_ids']!=tr or anterior['avaliacao_ids']!=vl:raise ValueError('Partições diferentes da v7.')
        m={'modelo':anterior['modelos']['mescla_condicional'],'calibrador':cal,'politica':pol}
        gravar(saida/f'folds/fold_{n}.json',{'modelo':m,'treino_ids':tr,'avaliacao_ids':vl})
        previsoes.extend({**r,'fold':n} for r in a.avaliar(aplicar(separar(pp,vl),m,cat),{i:ys[i] for i in vl},temas))
    previsoes.sort(key=lambda r:r['id'])
    if len(previsoes)!=100 or {r['id'] for r in previsoes}!=set(ys):raise ValueError('OOF incompleto.')
    csv_salvar(saida/'previsoes.csv',previsoes)
    cal=a.calibrar(previsoes)
    mod=json.loads((base/'modelos_diagnosticos.json').read_text())['mescla_condicional']['modelo']
    final={'modelo':mod,'calibrador':cal,'politica':a.politica(previsoes,a.confiancas(previsoes,cal))}
    gravar(saida/'modelo_diagnostico.json',final)
    alvo=preparar(cat,dic,{i:q for i,q in qs.items() if i not in ys})
    rows=aplicar(alvo,final,cat)
    controle={r['id']:r for r in csv.DictReader((base/'simulacoes_559.csv').open()) if r['variante']=='mescla_condicional'}
    for r in rows:
        ant=controle[r['id']]
        r.update({'tema_v7':ant['tema_central_id'],'decisao_v7':ant['decisao'],
                  'confianca_v7':float(ant['confianca']),'caminho':temas[r['tema_central_id']]['caminho']})
    csv_salvar(saida/'simulacoes_559.csv',rows)
    pubs=[r for r in rows if r['decisao']=='publicar']
    resultado={'avaliacao_100':a.resumo(previsoes),
        'simulacao_559':{'publicar':len(pubs),'revisar':len(rows)-len(pubs),'fora':0,'cobertura':len(pubs)/len(rows),
             'limiar':final['politica']['limiar'],
             'media_confiancas_publicadas':sum(r['confianca'] for r in pubs)/len(pubs) if pubs else None,
             'mudancas_tema':sum(r['tema_central_id']!=r['tema_v7'] for r in rows),'precisao_real':None},
        'segundos':time.perf_counter()-inicio,'entrega_alterada':False}
    gravar(saida/'resumo.json',resultado)
    for n,h in preservados.items():
        if sha(projeto/n)!=h:raise ValueError('Entrega anterior alterada.')
    for n,h in hashes.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante avaliação.')
    print(json.dumps(resultado,ensure_ascii=False,indent=2),flush=True)
    return resultado
