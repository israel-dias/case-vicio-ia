"""Experimento comparativo; não altera nem promove a entrega v5."""
from collections import Counter
import csv
import json
from pathlib import Path
import time

from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.experimento import gravar, csv_salvar, separar, validar_grupos
from melhorias_v3.representacao import NOMES, carregar_catalogo, lexico
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from flexivel_v5.runtime import ATIVOS
from .extracao import extrair


VARIANTES = ('foco_exclusivo', 'foco_ponderado')
PESO_FOCO = .4


def preparar(catalogo, qs):
    perfis = catalogo.transformar(qs)
    for qid, p in perfis.items():
        e = extrair(qs[qid])
        texto = lexico(e['texto_foco'], catalogo.aliases)
        w = (catalogo.escopo_palavras.transform([texto]) @ catalogo.ew.T).toarray()[0]
        c = (catalogo.escopo_caracteres.transform([texto]) @ catalogo.ec.T).toarray()[0]
        docs = .7*w + .3*c
        foco = f.np.asarray([max(docs[js]) for js in catalogo.membros])
        matriz = p['features_v3'][:, [NOMES.index(n) for n in ATIVOS]]
        p['x_foco'] = f.np.column_stack([matriz, foco, foco-max(foco),
                                       f.np.full(len(foco), float(e['presente']))])
        p['extracao_foco'] = e
        p['scores_foco'] = foco
        normal_base = p['scores']/max(max(p['scores']), 1e-12)
        normal_foco = foco/max(max(foco), 1e-12)
        p['ranking_foco_exclusivo'] = foco if max(foco)>0 else p['scores']
        p['ranking_foco_ponderado'] = ((1-PESO_FOCO)*normal_base + PESO_FOCO*normal_foco
                                        if max(foco)>0 else normal_base)
    return perfis


def ajustar(perfis, ys, cat):
    if not perfis or set(perfis)!=set(ys):
        raise ValueError('Treino recebeu rótulos externos ou está vazio.')
    cont = Counter(p['hash'] for p in perfis.values())
    xx, yy, pesos = [], [], []
    for qid, p in perfis.items():
        xx.extend(p['x_foco'])
        yy.extend(int(f.aceito(t,ys[qid],cat.temas)) for t in cat.familias)
        pesos.extend([1/cont[p['hash']]]*len(cat.familias))
    return ajustar_linear_eficiente(xx, yy, pesos, True)


def sinais(perfis, modelo, cat, variante):
    if variante not in VARIANTES:
        raise ValueError('Variante desconhecida.')
    rows=[]
    for qid, p in perfis.items():
        k=int(f.ordenar(p['ranking_'+variante])[0])
        rows.append({'id':qid, 'tema_central_id':cat.familias[k],
                     'sinal':float(a.escore_linear(p['x_foco'][[k]],modelo)[0]),
                     'elegivel':bool(max(p['scores'][k],p['scores_novos'][k],p['scores_foco'][k])>=.03),
                     'marcador_presente':p['extracao_foco']['presente'],
                     'foco':p['extracao_foco']['texto_foco']})
    return rows


def aplicar(perfis, mod, cat, nome, calib, politica):
    ss=sinais(perfis,mod,cat,nome)
    return [{**r,'confianca':p,'decisao':f.decidir(r,p,politica)}
            for r,p in zip(ss,a.confiancas(ss,calib))]


def executar(projeto, saida):
    inicio=time.perf_counter()
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Saída já existe. Escolha outra pasta.')
    qs,temas,ys=f.carregar(projeto/'dados/anexos')
    cat,_=carregar_catalogo(projeto)
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    anteriores={r['id']:r for r in csv.DictReader((projeto/'publicacao.csv').open())}
    if len(qs)!=659 or len(ys)!=100:raise ValueError('Universo inesperado.')
    arquivos=['foco_referencial_v6/extracao.py','foco_referencial_v6/experimento.py',
              'melhorias_v3/representacao.py','compatibilidade_v2/features.py',
              'auditoria_confianca_v4/experimento.py','melhorias_v3/aprendizado.py']
    gravar(saida/'protocolo_previo.json',{
        'hipotese':'Referências gramaticais delimitam um foco, mas não certificam o tema nem o acerto.',
        'variantes':VARIANTES, 'peso_foco_ponderado':PESO_FOCO,
        'similaridade_foco':'.7 palavras/bigramas + .3 caracteres; máximo por família de temas',
        'atributos':ATIVOS+['similaridade_foco','diferenca_melhor_foco','marcador_presente'],
        'retomada':'Última citação na janela anterior de 450 caracteres; senão última frase. Aproximação textual.',
        'avaliacao':'Mesmos 5 folds externos e 4 internos; ajuste e calibração internos. Rótulos já expostos anteriormente.',
        'liberacao_automatica':'Diagnóstico separado: presença de marcador e algum apoio textual publica sem corte.',
        'meta_empirica_interna':.95,'suporte_minimo_interno':10,
        'promove_entrega':False,'rotulos_das_559':0,'chamadas_llm':0,
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'codigo_sha256':{n:sha(projeto/n) for n in arquivos},
        'csv_v5_sha256':sha(projeto/'publicacao.csv')})
    perfis=preparar(cat,{i:qs[i] for i in sorted(ys)})
    previsoes={n:[] for n in VARIANTES}
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(perfis,tr,vl,ys)
        print(f'Foco referencial: fold externo {n}/5.',flush=True)
        internas={nome:[] for nome in VARIANTES}
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids']
            validar_grupos(perfis,ti,vi,tr)
            mod=ajustar(separar(perfis,ti),{i:ys[i] for i in ti},cat)
            for nome in VARIANTES:
                internas[nome].extend(a.avaliar(sinais(separar(perfis,vi),mod,cat,nome),{i:ys[i] for i in vi},temas))
        cs={nome:a.calibrar(internas[nome]) for nome in VARIANTES}
        pols={nome:a.politica(internas[nome],a.confiancas(internas[nome],cs[nome])) for nome in VARIANTES}
        mod=ajustar(separar(perfis,tr),{i:ys[i] for i in tr},cat)
        gravar(saida/f'folds/fold_{n}.json',{'modelo':mod,'calibradores':cs,'politicas':pols,
            'treino_ids':tr,'avaliacao_ids':vl,'protocolo_sha256':sha(saida/'protocolo_previo.json')})
        for nome in VARIANTES:
            rows=aplicar(separar(perfis,vl),mod,cat,nome,cs[nome],pols[nome])
            previsoes[nome].extend({**r,'fold':n} for r in a.avaliar(rows,{i:ys[i] for i in vl},temas))
    controle=list(csv.DictReader((projeto/'experimentos/auditoria_confianca_v4_002/previsoes_sem_formato.csv').open()))
    for r in controle:
        for chave in ['correto','fora_oficial']:r[chave]=int(r[chave])
        r['confianca']=float(r['confianca'])
    resumo={'controle_v5':a.resumo(controle)}
    for nome, rows in previsoes.items():
        rows.sort(key=lambda r:r['id'])
        if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('OOF incompleto.')
        csv_salvar(saida/f'previsoes_{nome}.csv',rows)
        resumo[nome]=a.resumo(rows)
    # A regra absoluta recebe a interpretação operacional mais favorável:
    # só libera quando há marcador E pelo menos algum tema com similaridade.
    absoluto=[];pares=[]
    base={r['id']:r for r in controle}
    for qid,p in perfis.items():
        k=int(f.ordenar(p['ranking_foco_exclusivo'])[0]);tid=cat.familias[k]
        ativo=bool(p['extracao_foco']['presente'] and max(p['scores_foco'])>0)
        if ativo:
            absoluto.append({'id':qid,'tema_central_id':tid,'correto':int(f.aceito(tid,ys[qid],temas)),
                'fora_oficial':int(ys[qid]['fora_da_taxonomia']), 'foco':p['extracao_foco']['texto_foco']})
        pares.append({'id':qid,'marcadores':p['extracao_foco']['marcadores'],
            'foco':p['extracao_foco']['texto_foco'],'tema_controle':base[qid]['tema_central_id'],
            'acerto_controle':base[qid]['correto'],'tema_foco':tid,
            'acerto_foco':int(f.aceito(tid,ys[qid],temas)),**ys[qid]})
    csv_salvar(saida/'diagnostico_100.csv',pares)
    gravar(saida/'liberacao_absoluta_100.json',{'publicacoes_por_marcador':len(absoluto),
        'corretas':sum(r['correto'] for r in absoluto),
        'precisao':sum(r['correto'] for r in absoluto)/len(absoluto) if absoluto else None,
        'questoes':absoluto,'probabilidade_calibrada':False})
    modelos={nome:{'modelo':ajustar(perfis,ys,cat),'calibrador':a.calibrar(previsoes[nome])} for nome in VARIANTES}
    for nome,m in modelos.items():
        m['politica']=a.politica(previsoes[nome],a.confiancas(previsoes[nome],m['calibrador']))
    # Persistência anterior à inferência nas 559. Não se escolhe pelo volume.
    gravar(saida/'modelos_diagnosticos.json',modelos)
    alvo=preparar(cat,{i:q for i,q in qs.items() if i not in ys})
    simulacoes={};todas=[]
    for nome,m in modelos.items():
        rows=aplicar(alvo,m['modelo'],cat,nome,m['calibrador'],m['politica'])
        for r in rows:
            ant=anteriores[r['id']]
            r.update({'variante':nome,'decisao_v5':ant['decisao'],'confianca_v5':float(ant['confianca']),
                      'tema_v5':ant['tema_central_id'],'caminho':temas[r['tema_central_id']]['caminho']})
        todas.extend(rows)
        simulacoes[nome]={'publicar':sum(r['decisao']=='publicar' for r in rows),
            'revisar':sum(r['decisao']=='revisar' for r in rows),
            'revisar_v5_para_publicar':sum(r['decisao_v5']=='revisar' and r['decisao']=='publicar' for r in rows),
            'mudancas_tema':sum(r['tema_v5']!=r['tema_central_id'] for r in rows),
            'com_marcador':sum(r['marcador_presente'] for r in rows),
            'precisao_real':None,'promovida_para_entrega':False}
    csv_salvar(saida/'simulacoes_559.csv',todas)
    gravar(saida/'extracoes_659.json',{i:extrair(q) for i,q in qs.items()})
    gravar(saida/'resumo.json',{'comparacao_100':resumo,'simulacao_559':simulacoes,
         'liberacao_absoluta':{'publicadas':len(absoluto),'corretas':sum(r['correto'] for r in absoluto)},
         'marcadores_100':sum(p['extracao_foco']['presente'] for p in perfis.values()),
         'segundos':time.perf_counter()-inicio,'entrega_v5_preservada':True})
    if sha(projeto/'publicacao.csv')!=json.loads((saida/'protocolo_previo.json').read_text())['csv_v5_sha256']:
        raise ValueError('A entrega anterior foi alterada.')
    for nome,r in resumo.items():print(nome,json.dumps(r,ensure_ascii=False),flush=True)
    print('Simulações nas 559:',json.dumps(simulacoes,ensure_ascii=False),flush=True)
    return resumo
