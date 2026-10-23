"""Estudo semântico em referências expostas, sem usar os 559 para seleção."""
import argparse,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from testar_isolamento_v17 import gravar,csv_salvar,sub,dependencias,controle
from isolamento_v17.metricas import medir
from semantica_v21 import modelo as m


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);deps=dependencias(projeto);dados=projeto/'dados/anexos';cache=projeto/'artefatos/semantica_v21'
    gravar(saida/'protocolo_previo.json',{'versao':'semantica_v21_1','variantes':m.VARIANTES,'adaptativo':True,
        'avaliacao':'Validação cruzada aninhada em 100 referências expostas; não é teste externo independente.',
        'origem':'E5 query/query e query/passage preparados sem rótulos; TF-IDF e BM25 do catálogo; comparador clássico compartilhado e calibrador sigmoide.',
        'regras':'Sem gabarito ou escolha do LLM. Sem exceção por ID, sem confiança mínima artificial. Não marca fora por similaridade baixa.',
        'selecao':'Suporte interno com precisão empírica de pelo menos 95%, depois acertos top1, empate favorece lexical. Antes de prever as 559.',
        'projeto_sha256':deps,'cache_manifesto_sha256':sha(cache/'manifesto.json'),'promove_entrega':False})
    qs,temas,ys=f.carregar(dados);cat,_=carregar_catalogo(projeto);busca=m.Busca(projeto,cat,cache);pp=busca.preparar(sub(qs,ys))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text());ext={v:[] for v in [*m.VARIANTES,'selecionado_internamente']};raw={v:[] for v in m.VARIANTES}
    escolher=lambda packs,rr:max(m.VARIANTES,key=lambda v:(packs[v]['politica']['suporte_interno'],sum(r['correto'] for r in rr[v]),-m.VARIANTES.index(v)))
    for fold in folds:
        n,tr,vl=fold['fold'],fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(pp,tr,vl,ys);print(f'Fold {n}/5: rótulos externos isolados de ajuste e calibração.',flush=True)
        internas={v:[] for v in m.VARIANTES}
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(pp,ti,vi,tr);mod=m.ajustar(sub(pp,ti),sub(ys,ti),cat)
            for v in m.VARIANTES:internas[v].extend(a.avaliar(m.sinais(sub(pp,vi),mod,cat,v),sub(ys,vi),temas))
        mod=m.ajustar(sub(pp,tr),sub(ys,tr),cat);packs={v:m.pacote(sub(pp,tr),sub(ys,tr),cat,v,internas[v],mod) for v in m.VARIANTES};escolhido=escolher(packs,internas)
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'selecionado':escolhido,'modelos':packs})
        for v in m.VARIANTES:
            raw[v].extend(a.avaliar(m.sinais(sub(pp,vl),mod,cat,v),sub(ys,vl),temas))
            rr=[{**r,'fold':n} for r in a.avaliar(m.aplicar(sub(pp,vl),packs[v],cat,v),sub(ys,vl),temas)];ext[v].extend(rr)
            if escolhido==v:ext['selecionado_internamente'].extend(rr)
    mod=m.ajustar(pp,ys,cat);finais={v:m.pacote(pp,ys,cat,v,raw[v],mod) for v in m.VARIANTES};escolhido=escolher(finais,raw)
    gravar(saida/'modelos_finais.json',{'modelos':finais,'selecionado':escolhido,'versao':'semantica_v21_1'})
    gravar(saida/'escolha_antes_559.json',{'selecionado':escolhido,'promove_entrega':False})
    resumo={v:{'desenvolvimento_100':medir(rr,controle(projeto,'avaliacao_desenvolvimento_100.csv'))} for v,rr in ext.items()}
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'avaliacao':v} for v,rr in ext.items() for r in rr]);gravar(saida/'resumo_antes_559.json',resumo)
    gravar(saida/'manifesto_inferencia.json',{'projeto_sha256':deps,'cache_manifesto_sha256':sha(cache/'manifesto.json'),'artefatos_sha256':{n:sha(saida/n) for n in ['modelos_finais.json','escolha_antes_559.json']}})
    for v,r in resumo.items():print(v,json.dumps(r,ensure_ascii=False),flush=True)
    print('Modelos e seleção congelados; aplicando nas 559 sem rótulos.',flush=True)
    alvo={i:q for i,q in qs.items() if i not in ys};ps=busca.preparar(alvo);ref=controle(projeto,'classificacoes_559_todas_variantes.csv');rrs=[]
    for v in m.VARIANTES:
        rr=m.aplicar(ps,finais[v],cat,v);rrs.extend(rr);resumo[v]['alvo_559']=medir(rr,ref);resumo[v]['recentes_300']=medir([r for r in rr if int(r['id'][1:])>=360])
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',rrs);gravar(saida/'resumo.json',resumo)
    (saida/'questoes_559_sem_rotulos.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for i,q in sorted(alvo.items())))
    gravar(saida/'traces_100.json',{i:p['trace'] for i,p in pp.items()});gravar(saida/'traces_559.json',{i:p['trace'] for i,p in ps.items()})
    for n,h in deps.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante avaliação: '+n)
    gravar(saida/'execucao.json',{'segundos':time.perf_counter()-inicio,'promove_entrega':False});return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
