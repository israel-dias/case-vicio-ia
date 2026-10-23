"""Desenvolvimento V16 separado; as 100 não entram nos totais das 559."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from experimento_atributos_v11.modelo import medidas
from multivista_v16 import modelo as m
from multivista_v16.catalogo import compilar

POLITICAS=['substituir','preservar_v11','preservar_com_guarda']
PARCEIRA={'condicional_v15':'reranking_multivista','busca_multivista':'reranking_multivista','reranking_multivista':'busca_multivista'}
def gravar(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csv_salvar(p,rows):
    with p.open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def sub(d,ids):return {i:d[i] for i in ids}
def referencia(p,arquivo,v,pol=None,corte=None):
    rr=list(csv.DictReader((p/arquivo).open()))
    rr=[r for r in rr if r['variante']==v and (pol is None or r['politica']==pol) and (corte is None or r.get('corte')==corte)]
    for r in rr:
        r['confianca']=float(r['confianca']);r['elegivel']=r.get('elegivel')=='True'
        for k in ['correto','fora_oficial','fold']:
            if k in r:r[k]=int(r[k])
    if len(rr)!=len({r['id'] for r in rr}):raise ValueError('Referência repetida.')
    return rr
def pacote(pp,ys,cat,v,internas):
    cal=a.calibrar(internas)
    return {'modelo':m.ajustar(pp,ys,cat,v),'calibrador':cal,
        'politica':a.politica(internas,a.confiancas(internas,cal)),'atributos':m.nomes(v)}
def politicas(novas,controle,temas):
    out={}
    for v,rows in novas.items():
        out[(v,'substituir')]=rows
        for nome,guarda in [('preservar_v11',False),('preservar_com_guarda',True)]:
            out[(v,nome)]=m.preservar(rows,controle,novas[PARCEIRA[v]],temas,guarda)
    return out
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True)
    arquivos=['testar_multivista_v16.py','classificar_multivista_v16.py',*['multivista_v16/'+n for n in ['catalogo.py','modelo.py','__init__.py']]]
    protegidos={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt','roteamento_v15/texto.py','roteamento_v15/modelo.py']}
    gravar(saida/'protocolo_previo.json',{'versao':'v16_1','variantes':m.VARIANTES,
        'atributos':{v:m.nomes(v) for v in m.VARIANTES},'cortes':['calibrado','70'],'politicas':POLITICAS,
        'objetivo':'Campos ausentes com z=0 após padronização aplicável; BM25 hierárquico em várias vistas; comparador com candidatos difíceis; preservação com conflito.',
        'BM25':{'k1':1.2,'b':.75,'idf_por_familia':True,'novos_rotulos':False},
        'busca_pesos':{'legado_v8':.55,'bm25_conjunto':.25,'bm25_fim':.10,'bm25_relacao_ou_enunciado':.10},
        'candidatos':'União dos sete primeiros de V8, foco V15 e BM25; positivos também disponíveis apenas no treino.',
        'guarda':'Homônimo herdado não resolvido; ou dois comparadores elegíveis com confiança >=70% sugerem o mesmo outro ramo. Não usa acerto por ID.',
        'escolha':'Somente comparação de desenvolvimento nas 100: precisão empírica >=95%, suporte >=10; maximizar publicações, desempate por acertos e ordem fixa. Nunca escolher pelo volume das 559.',
        'referencia_para_substituir':'Além da régua, publicar pelo menos 49 nas 100 e não aumentar erros em relação ao foco V15 preservado (2). Mesmo cumprindo isso, permanece experimental.',
        'exposicao':'100 rótulos vistos e reutilizados; desenvolvimento exposto, não teste externo cego.',
        'ajuste':'Cinco folds externos originais e quatro internos; ajuste e calibração sem rótulos do fold avaliado.',
        'homonimos':'Não foram inventadas diferenças de escopo que os anexos não fornecem.',
        'origens':'Disciplina e assunto de origem neutralizados em todas as novas vistas e atributos. Só o perfil legado original, na preservação V11, continua usando seus dados históricos.',
        'codigo_sha256':{n:sha(projeto/n) for n in arquivos},
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['temas.csv','questoes.jsonl','folha_verdade.csv']},
        'protegidos_sha256':protegidos,'promove_entrega':False})
    cat,_=carregar_catalogo(projeto)
    propostas=json.loads((projeto/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
    snapshot=compilar(cat,propostas);gravar(saida/'catalogo_preparado.json',snapshot)
    # O catálogo é compilado ANTES de carregar questões ou rótulos.
    qs,temas,ys=f.carregar(projeto/'dados/anexos')
    if (len(qs),len(ys),len(temas))!=(659,100,377):raise ValueError('Anexos inesperados.')
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    ref100=referencia(projeto,'experimentos/palavra_v12_001/avaliacao_100.csv','controle_v11','preservar_v11');refmap={r['id']:r for r in ref100}
    v15ref=referencia(projeto,'experimentos/roteamento_v15_002/avaliacao_100.csv','foco_contextual','preservar_v11','70')
    print('V16: preparando as 100 para ajuste e comparação de desenvolvimento.',flush=True)
    ps=m.preparar(cat,dic,snapshot,sub(qs,sorted(ys)))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text());todas=[];raw={v:[] for v in m.VARIANTES}
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(ps['condicional_v15'],tr,vl,ys)
        print(f'Fold {n}/5: ajustar, calibrar internamente e avaliar sem alterar pesos.',flush=True)
        internas={v:[] for v in m.VARIANTES}
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(ps['condicional_v15'],ti,vi,tr)
            mods={}
            for v,cfg in m.VARIANTES.items():
                chave='novo' if cfg['novos'] else 'condicional'
                if chave not in mods:mods[chave]=m.ajustar(sub(ps[v],ti),sub(ys,ti),cat,v)
                internas[v].extend(a.avaliar(m.sinais(sub(ps[v],vi),mods[chave],cat,v),sub(ys,vi),temas))
        modelos={v:pacote(sub(ps[v],tr),sub(ys,tr),cat,v,internas[v]) for v in m.VARIANTES}
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'modelos':modelos})
        for v,mo in modelos.items():raw[v].extend({**r,'fold':n} for r in a.avaliar(m.sinais(sub(ps[v],vl),mo['modelo'],cat,v),sub(ys,vl),temas))
        for corte in ['calibrado','70']:
            novos={v:m.aplicar(sub(ps[v],vl),mo,cat,v,corte) for v,mo in modelos.items()}
            for (v,pol),rows in politicas(novos,[refmap[i] for i in vl],temas).items():
                todas.extend({**r,'variante':v,'corte':corte,'politica':pol,'fold':n} for r in a.avaliar(rows,sub(ys,vl),temas))
    resumo={};ordem=[]
    for v in m.VARIANTES:
        for corte in ['calibrado','70']:
            for pol in POLITICAS:
                chave='/'.join([v,corte,pol]);ordem.append(chave)
                rr=[r for r in todas if (r['variante'],r['corte'],r['politica'])==(v,corte,pol)]
                assert len(rr)==len({r['id'] for r in rr})==100
                z=medidas(rr,v15ref);z['vetos_preservacao']=sum(bool(r.get('veto_preservacao')) for r in rr)
                z['fora_oficial_publicadas']=sum(r['fora_oficial'] for r in rr if r['decisao']=='publicar')
                resumo[chave]={'desenvolvimento_100':z}
    elegiveis=[k for k in ordem if resumo[k]['desenvolvimento_100']['publicar']>=10 and (resumo[k]['desenvolvimento_100']['precisao_publicadas'] or 0)>=.95]
    escolha=max(elegiveis,key=lambda k:(resumo[k]['desenvolvimento_100']['publicar'],resumo[k]['desenvolvimento_100']['acertos_publicadas'],-ordem.index(k))) if elegiveis else None
    passa=bool(escolha and resumo[escolha]['desenvolvimento_100']['publicar']>=49 and resumo[escolha]['desenvolvimento_100']['erros_publicadas']<=2)
    gravar(saida/'escolha_antes_559.json',{'configuracao':escolha,'cumpre_comparacao_v15':passa,'elegiveis':elegiveis,'fonte_escolha':'Somente desenvolvimento_100, antes das previsões nas 559.','promove_entrega':False})
    finais={v:pacote(ps[v],ys,cat,v,raw[v]) for v in m.VARIANTES};gravar(saida/'modelos_finais.json',finais)
    csv_salvar(saida/'avaliacao_desenvolvimento_100.csv',todas)
    print('Modelos e escolha registrados. Agora classificando somente as 559 fora da referência.',flush=True)
    q559={i:q for i,q in qs.items() if i not in ys};alvo=m.preparar(cat,dic,snapshot,q559)
    ref559=referencia(projeto,'experimentos/palavra_v12_001/simulacao_559.csv','controle_v11','preservar_v11')
    v15alvo=referencia(projeto,'experimentos/roteamento_v15_002/simulacao_559.csv','foco_contextual','preservar_v11','70')
    simul=[]
    for corte in ['calibrado','70']:
        novos={v:m.aplicar(alvo[v],mo,cat,v,corte) for v,mo in finais.items()}
        for (v,pol),rows in politicas(novos,ref559,temas).items():
            chave='/'.join([v,corte,pol]);z=resumo[chave]
            z['alvo_559']=medidas(rows,v15alvo);z['recentes_300']=medidas([r for r in rows if int(r['id'][1:])>=360])
            z['vetos_preservacao_559']=sum(bool(r.get('veto_preservacao')) for r in rows)
            z['media_confiancas_publicadas']=sum(r['confianca'] for r in rows if r['decisao']=='publicar')/max(1,sum(r['decisao']=='publicar' for r in rows))
            simul.extend({**r,'variante':v,'corte':corte,'politica':pol} for r in rows)
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',simul);gravar(saida/'resumo.json',resumo)
    gravar(saida/'referencias.json',{'v15_100':medidas(v15ref),'v15_559':medidas(v15alvo),'v11_100':medidas(ref100),'v11_559':medidas(ref559)})
    gravar(saida/'rotas_559.json',{i:alvo['busca_multivista'][i]['rota'] for i in alvo['busca_multivista']})
    for n,h in protegidos.items():
        if sha(projeto/n)!=h:raise ValueError('Arquivo anterior alterado: '+n)
    print(json.dumps({'escolha':escolha,'cumpre_comparacao_v15':passa,'resumo':resumo,'segundos':time.perf_counter()-inicio},ensure_ascii=False,indent=2),flush=True)
    return resumo
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
