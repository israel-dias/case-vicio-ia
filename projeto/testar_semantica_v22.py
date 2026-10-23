"""Estudo aninhado de integração: novas evidências sem pisos de confiança."""
import argparse,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from testar_isolamento_v17 import gravar,csv_salvar,sub,dependencias,controle
from isolamento_v17.metricas import medir
from semantica_v22 import modelo as m


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();inicio=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);deps=dependencias(projeto);dados=projeto/'dados/anexos';cache=projeto/'artefatos/semantica_v21'
    gravar(saida/'protocolo_previo.json',{'versao':'semantica_v22_1','variantes':m.VARIANTES,'adaptativo':True,
        'avaliacao':'Mesmos folds aninhados; 100 referências já expostas. Estudo de desenvolvimento, não confirmação independente.',
        'mudancas':'E5 passa a apoiar os 27 atributos contextuais; opção de manter a cobrança explícita do comando e limitar reranking à disciplina inferida pelo conteúdo. Não usa disciplina de origem.',
        'regras':'Homônimos e empate continuam explícitos. Nenhum piso artificial de confiança. Mesma calibração e suporte interno mínimo 10.',
        'selecao':'Suporte interno com precisão empírica >=95%, depois acertos top1. Escolha antes das 559; todos os resultados preservados.',
        'projeto_sha256':deps,'cache_manifesto_sha256':sha(cache/'manifesto.json'),'promove_entrega':False})
    qs,temas,ys=f.carregar(dados);cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    print('Preparação contextual e semântica das 100 referências.',flush=True);pp=m.preparar(projeto,cat,dic,sub(qs,ys))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text());ext={v:[] for v in [*m.VARIANTES,'selecionado_internamente']};raw={v:[] for v in m.VARIANTES}
    escolher=lambda packs,rr:max(m.VARIANTES,key=lambda v:(packs[v]['politica']['suporte_interno'],sum(r['correto'] for r in rr[v]),-m.VARIANTES.index(v)))
    for fold in folds:
        n,tr,vl=fold['fold'],fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(pp['controle_contextual'],tr,vl,ys);print(f'Fold {n}/5.',flush=True);internas={v:[] for v in m.VARIANTES}
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(pp['controle_contextual'],ti,vi,tr)
            mods={v:m.ajustar(sub(pp[v],ti),sub(ys,ti),cat,v) for v in ['controle_contextual','semantica_apoio']}
            for v in m.VARIANTES:
                mod=mods['controle_contextual' if v=='controle_contextual' else 'semantica_apoio'];internas[v].extend(a.avaliar(m.sinais(sub(pp[v],vi),mod,cat,v),sub(ys,vi),temas))
        mods={v:m.ajustar(sub(pp[v],tr),sub(ys,tr),cat,v) for v in ['controle_contextual','semantica_apoio']}
        packs={v:m.pacote(sub(pp[v],tr),sub(ys,tr),cat,v,internas[v],mods['controle_contextual' if v=='controle_contextual' else 'semantica_apoio']) for v in m.VARIANTES};escolhido=escolher(packs,internas)
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'selecionado':escolhido,'modelos':packs})
        for v in m.VARIANTES:
            raw[v].extend(a.avaliar(m.sinais(sub(pp[v],vl),packs[v]['modelo'],cat,v),sub(ys,vl),temas));rr=[{**r,'fold':n} for r in a.avaliar(m.aplicar(sub(pp[v],vl),packs[v],cat,v),sub(ys,vl),temas)];ext[v].extend(rr)
            if escolhido==v:ext['selecionado_internamente'].extend(rr)
    mods={v:m.ajustar(pp[v],ys,cat,v) for v in ['controle_contextual','semantica_apoio']};finais={v:m.pacote(pp[v],ys,cat,v,raw[v],mods['controle_contextual' if v=='controle_contextual' else 'semantica_apoio']) for v in m.VARIANTES};escolhido=escolher(finais,raw)
    gravar(saida/'modelos_finais.json',{'modelos':finais,'selecionado':escolhido,'versao':'semantica_v22_1'});gravar(saida/'escolha_antes_559.json',{'selecionado':escolhido,'promove_entrega':False})
    resumo={v:{'desenvolvimento_100':medir(rr,controle(projeto,'avaliacao_desenvolvimento_100.csv'))} for v,rr in ext.items()}
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'avaliacao':v} for v,rr in ext.items() for r in rr]);gravar(saida/'resumo_antes_559.json',resumo)
    gravar(saida/'manifesto_inferencia.json',{'projeto_sha256':deps,'cache_manifesto_sha256':sha(cache/'manifesto.json'),'artefatos_sha256':{n:sha(saida/n) for n in ['modelos_finais.json','escolha_antes_559.json']}})
    for v,r in resumo.items():print(v,json.dumps(r,ensure_ascii=False),flush=True)
    print('Escolha congelada antes das 559.',flush=True);alvo={i:q for i,q in qs.items() if i not in ys};ps=m.preparar(projeto,cat,dic,alvo);ref=controle(projeto,'classificacoes_559_todas_variantes.csv');rrs=[]
    for v in m.VARIANTES:
        rr=m.aplicar(ps[v],finais[v],cat,v);rrs.extend(rr);resumo[v]['alvo_559']=medir(rr,ref);resumo[v]['recentes_300']=medir([r for r in rr if int(r['id'][1:])>=360])
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',rrs);gravar(saida/'resumo.json',resumo)
    (saida/'questoes_559_sem_rotulos.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for i,q in sorted(alvo.items())))
    for n,h in deps.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante avaliação: '+n)
    gravar(saida/'execucao.json',{'segundos':time.perf_counter()-inicio,'promove_entrega':False});return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
