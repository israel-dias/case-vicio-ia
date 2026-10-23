"""Confiança diretamente no acerto da primeira sugestão não supervisionada."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3.representacao import carregar_catalogo
from semantica_v21.modelo import Busca
from semantica_v22 import qualidade as m
from testar_isolamento_v17 import gravar,csv_salvar,sub,dependencias,controle
from isolamento_v17.metricas import medir


def ler(p,v):
    rr=[r for r in csv.DictReader(p.open()) if r.get('avaliacao',r.get('variante'))==v]
    for r in rr:
        r['elegivel']=r['elegivel']=='True'
        for k in ['correto','fora_oficial','fold']:
            if k in r:r[k]=int(r[k])
    return rr


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();t=time.perf_counter();e=projeto/'experimentos/semantica_v22_001'
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True);deps=dependencias(projeto)
    gravar(saida/'protocolo_previo.json',{'versao':'qualidade_v23_1','variantes':m.VARIANTES,
        'motivacao':'O candidato pode estar certo e o estimador binário por par ter pouca discriminação. Estimar diretamente acerto da sugestão usando margens e apoios independentes do rótulo.',
        'candidato':'Primeiro da busca contextual não supervisionada V18/V22. Não é escolhido pelo classificador de confiança. Validado como idêntico ao controle V20 nas 100.',
        'avaliacao':'CV aninhada com mesmas partições; rótulos expostos; probabilidades ajustadas só nos treinos, corte escolhido com probabilidades internas fora do treino. Sem prova independente.',
        'preservacao':'Homônimos, empate e falta de evidência herdados do controle; sem pisos artificiais; sem alteração de tema ou decisão por ID.',
        'projeto_sha256':deps,'promove_entrega':False})
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto);busca=Busca(projeto,cat,projeto/'artefatos/semantica_v21')
    rows=ler(e/'avaliacao_100.csv','controle_contextual');base20=ler(projeto/'experimentos/contexto_v20_001/avaliacao_100.csv','controle_atual')
    if {r['id']:r['tema_central_id'] for r in rows}!={r['id']:r['tema_central_id'] for r in base20}:raise ValueError('O candidato do controle mudou.')
    if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('Conjunto inesperado.')
    rr={r['id']:r for r in rows};pp=busca.preparar(sub(qs,ys));folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text());ext={v:[] for v in [*m.VARIANTES,'selecionado_internamente']}
    for fold in folds:
        n,tr,vl=fold['fold'],fold['treino_ids'],fold['avaliacao_ids'];internas={v:[] for v in m.VARIANTES};print('Fold',n,flush=True)
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids']
            for v in m.VARIANTES:
                mod=m.ajustar([rr[i] for i in ti],sub(pp,ti),cat,v);ps=m.prever([rr[i] for i in vi],sub(pp,vi),cat,v,mod)
                internas[v].extend({**rr[i],'probabilidade_interna':float(c)} for i,c in zip(vi,ps))
        packs={v:{'modelo':m.ajustar([rr[i] for i in tr],sub(pp,tr),cat,v),'politica':f.escolher_politica(internas[v],[r['probabilidade_interna'] for r in internas[v]],minimo=10),'atributos':m.ATRIBUTOS[v]} for v in m.VARIANTES}
        escolhido=max(m.VARIANTES,key=lambda v:(packs[v]['politica']['suporte_interno'],-m.VARIANTES.index(v)))
        gravar(saida/f'folds/fold_{n}.json',{'treino_ids':tr,'avaliacao_ids':vl,'modelos':packs,'selecionado':escolhido})
        for v in m.VARIANTES:
            vr=[{**r,'fold':n} for r in m.aplicar([rr[i] for i in vl],sub(pp,vl),cat,v,packs[v])];ext[v].extend(vr)
            if v==escolhido:ext['selecionado_internamente'].extend(vr)
    finais={v:{'modelo':m.ajustar(rows,pp,cat,v),'politica':f.escolher_politica(ext[v],[r['confianca'] for r in ext[v]],minimo=10),'atributos':m.ATRIBUTOS[v]} for v in m.VARIANTES}
    escolhido=max(m.VARIANTES,key=lambda v:(finais[v]['politica']['suporte_interno'],-m.VARIANTES.index(v)))
    gravar(saida/'modelos_finais.json',{'modelos':finais,'selecionado':escolhido});gravar(saida/'escolha_antes_559.json',{'selecionado':escolhido,'promove_entrega':False})
    resumo={v:{'desenvolvimento_100':medir(rr,controle(projeto,'avaliacao_desenvolvimento_100.csv'))} for v,rr in ext.items()}
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'avaliacao':v} for v,rr in ext.items() for r in rr]);gravar(saida/'resumo_antes_559.json',resumo)
    for v,r in resumo.items():print(v,json.dumps(r,ensure_ascii=False),flush=True)
    gravar(saida/'manifesto_inferencia.json',{'projeto_sha256':deps,'cache_manifesto_sha256':sha(projeto/'artefatos/semantica_v21/manifesto.json'),'artefatos_sha256':{n:sha(saida/n) for n in ['modelos_finais.json','escolha_antes_559.json']}})
    # As sugestões do alvo são resultados de classificação já calculados
    # pelo controle. Esta tabela só evita repetir a preparação no experimento.
    # O comando de inferência regenera as sugestões pelo texto, sem consultar CSV.
    alvo={i:q for i,q in qs.items() if i not in ys};pa=busca.preparar(alvo);ra=ler(e/'classificacoes_559_todas_variantes.csv','controle_contextual');out=[];ref=controle(projeto,'classificacoes_559_todas_variantes.csv')
    for v in m.VARIANTES:
        vr=m.aplicar(ra,pa,cat,v,finais[v]);out.extend(vr);resumo[v]['alvo_559']=medir(vr,ref);resumo[v]['recentes_300']=medir([r for r in vr if int(r['id'][1:])>=360])
    csv_salvar(saida/'classificacoes_559_todas_variantes.csv',out);gravar(saida/'resumo.json',resumo)
    for n,h in deps.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado: '+n)
    gravar(saida/'execucao.json',{'segundos':time.perf_counter()-t,'promove_entrega':False});return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
