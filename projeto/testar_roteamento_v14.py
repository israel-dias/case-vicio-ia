"""Desenvolvimento V14: roteamento proposto, comparação de candidatos e corte 70%."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from experimento_atributos_v11.modelo import medidas,preservar_publicadas
from roteamento_v14 import modelo as m

def gravar(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csv_salvar(p,rows):
    with p.open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def sub(pp,ids):return {i:pp[i] for i in ids}
def carregar_ref(p,n):
    rows=list(csv.DictReader((p/'experimentos/palavra_v12_001'/n).open()))
    rr=[r for r in rows if r['variante']=='controle_v11' and r['politica']=='preservar_v11']
    for r in rr:
        r['confianca']=float(r['confianca']);r['elegivel']=r['elegivel']=='True'
        for k in ['correto','fora_oficial','fold']:
            if k in r:r[k]=int(r[k])
    return rr
def modelo(pp,ys,cat,internas):
    cal=a.calibrar(internas)
    return {'modelo':m.ajustar(pp,ys,cat),'calibrador':cal,'politica':a.politica(internas,a.confiancas(internas,cal)),'atributos':m.NOMES}
def com70(rows):return [{**r,'decisao':'publicar' if r['decisao']=='publicar' or r['elegivel'] and r['confianca']>=.7 else 'revisar'} for r in rows]
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);(saida/'folds').mkdir()
    arquivos=['testar_roteamento_v14.py','roteamento_v14/texto.py','roteamento_v14/modelo.py','classificar_roteamento_v14.py','congelar_roteamento_v14.py']
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt','experimentos/palavra_v12_001/resumo.json']}
    gravar(saida/'protocolo_previo.json',{'variantes':m.VARIANTES,'atributos':m.NOMES,
        'meta_empirica_interna':.95,'suporte_minimo':10,'cortes':['calibrado','70'],'corte70':.7,
        'politicas':['substituir','preservar_v11'],'ramos_homonimos_equivalentes':False,
        'regras':'Comando identificável antes de explique/norma, itens, CE, hipótese, caso narrado, instrução e conjunto. Literal descarta campos; contextual conserva. Maioria de itens por grupo de título é hipótese, não resposta oficial. Empate sem maioria usa primeiro item somente na literal.',
        'reordenacao':'Comparador treinado avalia todas as famílias ativas. Novos atributos não incluem ID, disciplina/assunto de origem ou gabarito. Fusão reutiliza o ranking legado V8, que mantém sua preparação histórica.',
        'rodada':2,'alteracoes_pos_rodada1':'Reconhecer situação hipotética também no comando; acrescentar fusão conservadora 70% ranking V8 + 30% ranking por papéis. Rodada inicial e código preservados. Esses pesos são escores de busca, não confiança ou percentuais de precisão.',
        'fora':'Não cria regra automática de exclusão. Rótulos fora contam como negativos de compatibilidade no treino, não justificam exclusões por palavra.',
        'avaliacao':'Mesmos 5 folds externos e 4 internos. Não mistura rótulos externos no ajuste, calibração e corte do fold.',
        'exposicao':'100 rótulos e vários erros já vistos e reutilizados; não é teste externo cego.',
        'escolha_pelo_volume559':False,'promove_entrega':False,
        'codigo_sha256':{n:sha(projeto/n) for n in arquivos},
        'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},
        'preservados_sha256':preservados})
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto)
    if (len(qs),len(ys),len(temas))!=(659,100,377):raise ValueError('Anexos inesperados.')
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    print('Preparando papéis das 100 questões; ainda sem classificar as 559.',flush=True)
    ps=m.preparar(cat,dic,sub(qs,sorted(ys)));ref=carregar_ref(projeto,'avaliacao_100.csv');refmap={r['id']:r for r in ref}
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text());raw={v:[] for v in m.VARIANTES};todas=[]
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(ps['usuario_literal'],tr,vl,ys)
        print(f'Fold {n}/5: literal, contexto e comparador; calibração interna separada.',flush=True)
        internas={v:[] for v in m.VARIANTES}
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(ps['usuario_literal'],ti,vi,tr)
            mods={}
            for v in m.VARIANTES:
                origem='contextual' if not m.VARIANTES[v]['literal'] else 'literal'
                if origem not in mods:mods[origem]=m.ajustar(sub(ps[v],ti),sub(ys,ti),cat)
                internas[v].extend(a.avaliar(m.sinais(sub(ps[v],vi),mods[origem],cat,v),sub(ys,vi),temas))
        modelos={v:modelo(sub(ps[v],tr),sub(ys,tr),cat,internas[v]) for v in m.VARIANTES}
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'modelos':modelos})
        for v,mo in modelos.items():
            ss=m.sinais(sub(ps[v],vl),mo['modelo'],cat,v)
            raw[v].extend({**r,'fold':n} for r in a.avaliar(ss,sub(ys,vl),temas))
            for corte in ['calibrado','70']:
                novos=m.aplicar(sub(ps[v],vl),mo,cat,v,corte)
                for politica,rr in [('substituir',novos),('preservar_v11',preservar_publicadas(novos,[refmap[i] for i in vl]))]:
                    todas.extend({**r,'variante':v,'corte':corte,'politica':politica,'fold':n} for r in a.avaliar(rr,sub(ys,vl),temas))
    resumo={v:{} for v in m.VARIANTES}
    for v in m.VARIANTES:
        for corte in ['calibrado','70']:
            for pol in ['substituir','preservar_v11']:
                rr=[r for r in todas if r['variante']==v and r['corte']==corte and r['politica']==pol]
                assert len(rr)==100 and {r['id'] for r in rr}==set(ys)
                z=medidas(rr,ref);z['fora_oficial_publicadas']=sum(r['fora_oficial'] for r in rr if r['decisao']=='publicar')
                resumo[v][corte+'_'+pol]=z
    finais={v:modelo(ps[v],ys,cat,raw[v]) for v in m.VARIANTES}
    gravar(saida/'modelos_finais.json',finais)
    # Diagnósticos completos antes de entrar nas 559: não são exceções de inferência.
    ex=[]
    for r in todas:
        if r['variante']=='usuario_literal' and r['corte']=='calibrado' and r['politica']=='substituir' and not r['correto']:
            ex.append({'id':r['id'],'previsao':r,'rota':ps['usuario_literal'][r['id']]['rota'],'questao':qs[r['id']],'referencia':ys[r['id']]})
    gravar(saida/'excecoes_regras_100.json',ex)
    print('Modelos e avaliação nas 100 concluídos. Simulando as 559 sem rótulo.',flush=True)
    alvo=m.preparar(cat,dic,{i:q for i,q in qs.items() if i not in ys});ref559=carregar_ref(projeto,'simulacao_559.csv');sim=[]
    for v,mo in finais.items():
        for corte in ['calibrado','70']:
            novos=m.aplicar(alvo[v],mo,cat,v,corte)
            for pol,rr in [('substituir',novos),('preservar_v11',preservar_publicadas(novos,ref559))]:
                z=resumo[v][corte+'_'+pol];z['simulacao_559']=medidas(rr,ref559)
                z['recentes_300']=medidas([r for r in rr if int(r['id'][1:])>=360])
                sim.extend({**r,'variante':v,'corte':corte,'politica':pol} for r in rr)
    bases={'referencia_v11':{'100':medidas(ref),'559':medidas(ref559)},'referencia_v11_corte70':{'100':medidas(com70(ref),ref),'559':medidas(com70(ref559),ref559)}}
    gravar(saida/'referencias.json',bases)
    csv_salvar(saida/'avaliacao_100.csv',todas);csv_salvar(saida/'simulacao_559.csv',sim);gravar(saida/'resumo.json',resumo)
    gravar(saida/'campos_659.json',{i:{'literal':ps['usuario_literal'][i]['rota'],'contextual':ps['contexto_preservado'][i]['rota']} for i in ps['usuario_literal']}|{i:{'literal':alvo['usuario_literal'][i]['rota'],'contextual':alvo['contexto_preservado'][i]['rota']} for i in alvo['usuario_literal']})
    for n,h in preservados.items():
        if sha(projeto/n)!=h:raise ValueError('Arquivo anterior alterado: '+n)
    print(json.dumps({'resumo':resumo,'referencias':bases,'segundos':time.perf_counter()-inicio},ensure_ascii=False,indent=2),flush=True)
    return resumo

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
