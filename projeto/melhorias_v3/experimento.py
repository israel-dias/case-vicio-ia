"""CV aninhada com as mesmas divisões da v2; os 559 não chegam ao ajuste."""
from __future__ import annotations

import csv
import importlib.metadata
import json
from pathlib import Path
import time

from compatibilidade_v2 import features as f
from compatibilidade_v2 import runtime as rt
from . import aprendizado as a
from .representacao import carregar_catalogo,NOMES


def gravar(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def csv_salvar(path,rows):
    campos=sorted(set().union(*(r.keys() for r in rows)))
    with path.open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=campos);w.writeheader()
        w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)


def separar(perfis,ids):
    return {i:perfis[i] for i in sorted(ids)}


def validar_grupos(perfis,treino,teste,universo):
    if set(treino)&set(teste) or set(treino)|set(teste)!=set(universo):
        raise ValueError('Partição sobreposta ou incompleta.')
    if {perfis[i]['hash'] for i in treino}&{perfis[i]['hash'] for i in teste}:
        raise ValueError('Texto duplicado entre treino e avaliação.')


def ajustar(perfis,ys,catalogo):
    return {'todos':a.ajustar(perfis,ys,catalogo.familias,catalogo.temas,False),
            'proximos':a.ajustar(perfis,ys,catalogo.familias,catalogo.temas,True)}


def ler_controle(pasta):
    rows=list(csv.DictReader((pasta/'previsoes_compatibilidade_fixa.csv').open(encoding='utf-8')))
    for r in rows:
        for n in ['sinal','confianca','score_lexical']:r[n]=float(r[n])
        for n in ['correto','fora_oficial','fold']:r[n]=int(r[n])
        r['elegivel']=r['elegivel']=='True'
    return rows


def executar(projeto,saida):
    inicio=time.perf_counter();projeto=Path(projeto).resolve();saida=Path(saida).resolve()
    if saida.exists():raise ValueError('Saída existente; use uma pasta nova.')
    dados=projeto/'dados/anexos';antigo=projeto/'experimentos/folha_v2_escopos_001'
    from treinar_compatibilidade_v2 import conferir_experimento
    qs,temas,ys=f.carregar(dados)
    if (len(qs),len(temas),len(ys))!=(659,377,100):raise ValueError('Anexos diferentes do protocolo.')
    conferir_experimento(antigo,dados,ys,temas)
    folds=json.loads((antigo/'auditoria_folds.json').read_text())
    controle=ler_controle(antigo)
    arquivos=['melhorias_v3/representacao.py','melhorias_v3/aprendizado.py','melhorias_v3/experimento.py',
              'melhorias_v3/dados/referencias_normativas_v1.json','compatibilidade_v2/features.py',
              'compatibilidade_v2/runtime.py', 'experimentos/folha_v2_escopos_001/auditoria_folds.json']
    protocolo={'versao':'melhorias_v3_1','hipoteses':['Mapa documental de normas e artigos associado aos escopos.','Atributos textuais adicionais normalizados por campo.','Treino de candidatos próximos com positivos oficiais e negativos próximos.'],
        'metodos':['controle_v2',*a.METODOS,'selecionado_internamente'],
        'mesmos_folds_v2':True,'folds_externos':5,'folds_internos':4,
        'metas':{'precisao_empirica_interna':.95,'minimo_publicacoes_internas':10},
        'modelo':'Regressão logística C=1, liblinear; calibração logística monotônica sobre escore linear.',
        'ids_como_atributo':False,'llm_na_decisao':False,'rotulos_sem_rotulo_usados':0,
        'exposicao':'Desenvolvimento: os 100 rótulos e exemplos avaliados já foram discutidos. Não é novo teste cego.',
        'atributos':NOMES,'dados_sha256':{n:rt.sha(dados/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'arquivos_sha256':{n:rt.sha(projeto/n) for n in arquivos},
        'dependencias':{n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn','threadpoolctl']}}
    gravar(saida/'protocolo_previo.json',protocolo)
    catalogo,base_rt=carregar_catalogo(projeto)
    perfis=catalogo.transformar({i:qs[i] for i in sorted(ys)})
    previsoes={'controle_v2':controle,**{n:[] for n in a.METODOS},'selecionado_internamente':[]}
    audit=[]
    for fold in folds:
        n=fold['fold'];print(f'Fold externo {n}/5: ajuste em 80; avaliação em 20.',flush=True)
        tr,vl=fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(perfis,tr,vl,ys)
        internas={nome:[] for nome in a.METODOS}
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids']
            validar_grupos(perfis,ti,vi,tr)
            mods=ajustar(separar(perfis,ti),{i:ys[i] for i in sorted(ti)},catalogo)
            ss=a.sinais(separar(perfis,vi),mods,catalogo.familias)
            for nome in a.METODOS:internas[nome].extend(a.avaliar(ss[nome],{i:ys[i] for i in vi},temas))
        cs={};pol={};metricas={}
        for nome in a.METODOS:
            cs[nome]=a.calibrar(internas[nome]);ps=a.confiancas(internas[nome],cs[nome])
            pol[nome]=a.politica(internas[nome],ps)
            metricas[nome]={'suporte':pol[nome]['suporte_interno'],'acertos_top1':sum(r['correto'] for r in internas[nome])}
        # O controle foi ajustado nos mesmos grupos internos na execução original.
        pol['controle_v2']=fold['politicas']['compatibilidade_fixa']
        metricas['controle_v2']={'suporte':pol['controle_v2']['suporte_interno'],
                                'acertos_top1':pol['controle_v2']['acertos_top1_internos']}
        nomes=['controle_v2',*a.METODOS]
        escolhido=max(nomes,key=lambda v:(metricas[v]['suporte'],metricas[v]['acertos_top1'],-nomes.index(v)))
        mods=ajustar(separar(perfis,tr),{i:ys[i] for i in sorted(tr)},catalogo)
        registro={'fold':n,'treino_ids':tr,'avaliacao_ids':vl,'folds_internos':fold['folds_internos'],
                  'selecionado':escolhido,'calibradores':cs,'politicas':pol,'modelos':mods,
                  'protocolo_sha256':rt.sha(saida/'protocolo_previo.json')}
        # Persistido antes de gerar ou consultar o acerto das previsões externas.
        gravar(saida/f'modelos_folds/fold_{n}.json',registro)
        ss=a.sinais(separar(perfis,vl),mods,catalogo.familias)
        externas={}
        for nome in a.METODOS:
            ps=a.confiancas(ss[nome],cs[nome])
            rows=[{**r,'fold':n,'confianca':p,'decisao':f.decidir(r,p,pol[nome])} for r,p in zip(ss[nome],ps)]
            externas[nome]=a.avaliar(rows,{i:ys[i] for i in vl},temas)
            previsoes[nome].extend(externas[nome])
        selecionadas=[r for r in controle if r['fold']==n] if escolhido=='controle_v2' else externas[escolhido]
        previsoes['selecionado_internamente'].extend({**r,'variante':escolhido} for r in selecionadas)
        audit.append({k:v for k,v in registro.items() if k!='modelos'})
    resultados={}
    for nome,rows in previsoes.items():
        if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('OOF incompleto.')
        rows.sort(key=lambda r:r['id']);csv_salvar(saida/f'previsoes_{nome}.csv',rows)
        resultados[nome]=a.resumo(rows)
    diagnostico={'avaliadas':100,'sem_rotulo_classificadas':0,
        'com_norma_extraida':sum(bool(p['refs_extraidas']['enunciado_comando']['normas'] or any(r['normas'] for r in p['refs_extraidas']['alternativas'])) for p in perfis.values()),
        'com_artigo_vinculado':sum(bool(p['refs_extraidas']['enunciado_comando']['artigos'] or any(r['artigos'] for r in p['refs_extraidas']['alternativas'])) for p in perfis.values()),
        'top5_legacy_com_referencia':sum(any(f.aceito(catalogo.familias[k],ys[i],temas) for k in map(int,f.ordenar(p['scores'])[:5])) for i,p in perfis.items()),
        'uniao_candidatos_com_referencia':sum(any(f.aceito(catalogo.familias[k],ys[i],temas) for k in a.candidatos(p)) for i,p in perfis.items())}
    gravar(saida/'resumo.json',{'metodos':resultados,'diagnostico':diagnostico,'segundos':time.perf_counter()-inicio})
    gravar(saida/'auditoria_folds.json',audit)
    cab=['# Experimento v3 — referências e candidatos próximos','',
         'Resultados de desenvolvimento nos 100 rótulos conhecidos, com as mesmas divisões da v2. Não é teste externo cego. As 559 questões avaliadas pela empresa não foram usadas no treino ou escolha das regras.','',
         '| Variante | Acertos top1/100 | Publicadas | Corretas | Precisão | Cobertura | Brier |','|---|---:|---:|---:|---:|---:|---:|']
    for nome,r in resultados.items():
        prec='indefinida' if r['precisao_publicadas'] is None else f"{r['precisao_publicadas']:.2%}"
        cab.append(f"| {nome} | {r['acertos_top1']} | {r['publicar']} | {r['acertos_publicadas']} | {prec} | {r['cobertura']:.2%} | {r['brier']:.4f} |")
    cab+=['','A seleção interna escolhe a variante com mais publicações internas sob a meta empírica de 95% e suporte mínimo de dez. Empates usam acerto top1 e favorecem o controle. A política fica salva antes da avaliação externa.',
          '', 'As normas e intervalos são associações documentais propostas; não são parecer jurídico. A citação é um atributo auxiliar. Homônimos não são fundidos. Nenhuma questão tem uma resposta ou decisão escrita à mão.',
          '', 'A variante fixa preserva o tema da busca e testa apenas os novos atributos. As outras duas podem trocar o candidato. Fora automático e extras automáticos continuam desativados.',
          '', 'O resultado das 559 depende da execução do modelo final e sua precisão permanece desconhecida. Repetir esta execução reproduz o mesmo experimento; não produz nova evidência independente.','']
    (saida/'LEITURA.md').write_text('\n'.join(cab),encoding='utf-8')
    gravar(saida/'manifesto.json',{str(p.relative_to(saida)):rt.sha(p) for p in sorted(saida.rglob('*')) if p.is_file() and p.name!='manifesto.json'})
    for nome,r in resultados.items():print(nome,json.dumps(r,ensure_ascii=False),flush=True)
    return resultados
