"""Compara preparação explícita de cobrança com controle original preservado."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from isolamento_v17.metricas import medir
from testar_isolamento_v17 import gravar,csv_salvar,sub,controle,dependencias
from testar_contexto_v18 import trocas
from expressoes_v19 import modelo as m


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);deps=dependencias(projeto);dados=projeto/'dados/anexos'
    gravar(saida/'protocolo_previo.json',{'versao':'expressoes_v19_1','variantes':m.VARIANTES,
        'adaptativo':True,'motivo':'Ampliação após erros da folha de desenvolvimento: três hipóteses fixadas antes da comparação desta rodada; referências já expostas.',
        'regras':'Frases completas, vocábulos distintivos e escopos no trecho de cobrança. Texto completo preservado como apoio. I/II e V/F completos. Sem respostas ou exceções por ID.',
        'controle':'V18 morfológica preservada; três estratégias fixas de evidências literais do catálogo. Pesos de recuperação 15%/25%, não probabilidades.',
        'avaliacao':'Mesmos folds e calibração internos, referências já expostas; não é teste externo cego.',
        'projeto_sha256':deps,'dados_sha256':{n:sha(dados/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']},'promove_entrega':False})
    qs,temas,ys=f.carregar(dados);cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    print('Preparação com cobrança extraída: estudo nas 100 referências.',flush=True)
    pp=m.preparar(cat,dic,sub(qs,ys));folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    externas={v:[] for v in [*m.VARIANTES,'selecionado_internamente']};raw={v:[] for v in m.VARIANTES}
    for fold in folds:
        n,tr,vl=fold['fold'],fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(pp['controle_atual'],tr,vl,ys)
        print(f'Fold {n}/5: preparação por estrutura, ajuste e calibração separados.',flush=True)
        internas={v:[] for v in m.VARIANTES}
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(pp['controle_atual'],ti,vi,tr)
            for v in m.VARIANTES:
                mod=m.ajustar(sub(pp[v],ti),sub(ys,ti),cat,v)
                internas[v].extend(a.avaliar(m.sinais(sub(pp[v],vi),mod,cat,v),sub(ys,vi),temas))
        packs={v:m.pacote(sub(pp[v],tr),sub(ys,tr),cat,v,internas[v]) for v in m.VARIANTES};escolhido=m.escolher(packs,internas)
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'selecionado':escolhido,'modelos':packs})
        for v in m.VARIANTES:
            raw[v].extend(a.avaliar(m.sinais(sub(pp[v],vl),packs[v]['modelo'],cat,v),sub(ys,vl),temas))
            rr=[{**r,'fold':n} for r in a.avaliar(m.aplicar(sub(pp[v],vl),packs[v],cat,v),sub(ys,vl),temas)]
            externas[v].extend(rr)
            if escolhido==v:externas['selecionado_internamente'].extend(rr)
    ref100=controle(projeto,'avaliacao_desenvolvimento_100.csv')
    resumo={v:{'desenvolvimento_100':medir(rr,ref100),'trocas':trocas(rr,externas['controle_atual'])} for v,rr in externas.items()}
    finais={v:m.pacote(pp[v],ys,cat,v,raw[v]) for v in m.VARIANTES};escolhido=m.escolher(finais,raw)
    gravar(saida/'modelos_finais.json',{'versao':'expressoes_v19_1','selecionado':escolhido,'modelos':finais})
    gravar(saida/'escolha_antes_559.json',{'selecionado':escolhido,'adaptativo':True,'fonte':'Referências expostas, antes do alvo com esta preparação.','promove_entrega':False})
    gravar(saida/'manifesto_inferencia.json',{'versao':'expressoes_v19_1','projeto_sha256':deps,
        'artefatos_sha256':{n:sha(saida/n) for n in ['modelos_finais.json','escolha_antes_559.json']},'promove_entrega':False})
    gravar(saida/'resumo_antes_559.json',resumo)
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'avaliacao':v} for v,rr in externas.items() for r in rr])
    gravar(saida/'preparacao_100.json',{i:pp['controle_atual'][i]['extracao_comando'] for i in ys})
    print('Modelos congelados; aplicando preparação e classificação nas 559.',flush=True)
    alvo={i:q for i,q in qs.items() if i not in ys}
    (saida/'questoes_559_sem_rotulos.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for i,q in sorted(alvo.items())),encoding='utf-8')
    ps=m.preparar(cat,dic,alvo);ref559=controle(projeto,'classificacoes_559_todas_variantes.csv');resultados={}
    for v in m.VARIANTES:
        rr=m.aplicar(ps[v],finais[v],cat,v);resultados[v]=rr
        resumo[v]['alvo_559']=medir(rr,ref559);resumo[v]['recentes_300']=medir([r for r in rr if int(r['id'][1:])>=360])
    resumo['selecionado_internamente']['alvo_559']=medir(resultados[escolhido],ref559)
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',[r for rr in resultados.values() for r in rr])
    gravar(saida/'preparacao_559.json',{i:{'extracao':ps['controle_atual'][i]['extracao_comando'],
                                       'evidencia_v19':ps['controle_atual'][i]['evidencia_v19'],
                                       'identificacao':ps['controle_atual'][i]['identificacao'],
                                       'rota':ps['controle_atual'][i]['rota']} for i in alvo})
    gravar(saida/'resumo.json',resumo)
    for n,h in deps.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante avaliação: '+n)
    gravar(saida/'execucao.json',{'segundos':time.perf_counter()-inicio,'promove_entrega':False})
    for v,r in resumo.items():print(v,json.dumps(r,ensure_ascii=False),flush=True)
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
