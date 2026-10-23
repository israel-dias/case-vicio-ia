"""Desenvolvimento V24; congela escolha antes de inferir as 559 avaliadas."""
import argparse,csv,json,time
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3.experimento import validar_grupos
from vocabulario_v8.texto import Dicionario
from testar_isolamento_v17 import gravar,csv_salvar,sub,dependencias
from isolamento_v17.metricas import medir
from cobranca_v24 import modelo as m
from cobranca_v24.texto import Leitura

MODOS=('revalidar_cobranca','veto_contexto','substituir')


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();t=time.perf_counter()
    if saida.exists():raise ValueError('Use saída nova.')
    deps=dependencias(projeto);deps['cobranca_v24/expressoes.json']=sha(projeto/'cobranca_v24/expressoes.json');saida.mkdir(parents=True)
    gravar(saida/'protocolo_previo.json',{'versao':'cobranca_v24_1','variantes':m.VARIANTES,'composicoes':MODOS,
        'regras':'Cobrança final contextualizada, comandos genéricos fora da competição, retomadas, citação+ato; todas as proposições preservadas. Penal é disciplina, não identificador suficiente. Publicações anteriores passam por veto de contexto e conflito explícito.',
        'avaliacao':'100 rótulos expostos. Mesmos folds externos/internos para ajuste da nova rota. A composição usa controles OOF históricos: desenvolvimento adaptativo, não teste independente nem calibração global nova.',
        'selecao':'Antes de inferir o alvo; exigir precisão empírica >=95% e >=10 publicadas, maximizar quantidade e acertos. Se nenhuma composição cumprir, selecionar a mais precisa com aviso explícito, sem inventar garantia.',
        'equivalencia':'Somente régua oficial: central, extras e ancestrais/descendentes. Sem equivalência entre irmãos ou homônimos por opinião.',
        'projeto_sha256':deps,'promove_entrega':False})
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto);leitor=Leitura(cat);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    base=[r for r in csv.DictReader((projeto/'experimentos/roteamento_comando_v18_001/avaliacao_100.csv').open()) if r['composicao']=='suplemento_revisoes']
    for r in base:
        r['confianca']=float(r['confianca']);r['correto']=int(r['correto']);r['fora_oficial']=int(r['fora_oficial'])
    bm={r['id']:r for r in base};print('Preparando as 100; sem classificação do alvo nesta etapa.',flush=True);pp=m.preparar(cat,dic,sub(qs,ys))
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text());ext={v:[] for v in m.VARIANTES};raw={v:[] for v in m.VARIANTES};comp={(v,modo):[] for v in m.VARIANTES for modo in MODOS}
    for fold in folds:
        n,tr,vl=fold['fold'],fold['treino_ids'],fold['avaliacao_ids'];validar_grupos(pp[m.VARIANTES[0]],tr,vl,ys);internas={v:[] for v in m.VARIANTES};print('Fold',n,flush=True)
        for di in fold['folds_internos']:
            ti,vi=di['treino_ids'],di['validacao_ids'];validar_grupos(pp[m.VARIANTES[0]],ti,vi,tr)
            for v in m.VARIANTES:
                mod=m.ajustar(sub(pp[v],ti),sub(ys,ti),cat,v);internas[v].extend(a.avaliar(m.sinais(sub(pp[v],vi),mod,cat,v),sub(ys,vi),temas))
        packs={v:m.pacote(sub(pp[v],tr),sub(ys,tr),cat,v,internas[v]) for v in m.VARIANTES};gravar(saida/f'folds/fold_{n}.json',{'modelos':packs,'treino_ids':tr,'avaliacao_ids':vl})
        for v in m.VARIANTES:
            raw[v].extend(a.avaliar(m.sinais(sub(pp[v],vl),packs[v]['modelo'],cat,v),sub(ys,vl),temas))
            novas=[{**r,'fold':n} for r in m.aplicar(sub(pp[v],vl),packs[v],cat,v)];ext[v].extend(a.avaliar(novas,sub(ys,vl),temas))
            for modo in MODOS:comp[v,modo].extend(a.avaliar(m.compor(novas,[bm[i] for i in vl],sub(qs,vl),leitor,modo),sub(ys,vl),temas))
    resumo={'controle_anterior':medir(base)}
    for v,rr in ext.items():resumo[v]=medir(rr)
    for (v,modo),rr in comp.items():resumo[v+'/'+modo]=medir(rr,base)
    opcoes=list(comp);eleg=[k for k in opcoes if resumo['/'.join(k)]['publicar']>=10 and (resumo['/'.join(k)]['precisao_desenvolvimento'] or 0)>=.95]
    if eleg:escolha=max(eleg,key=lambda k:(resumo['/'.join(k)]['publicar'],resumo['/'.join(k)]['acertos_publicadas'],-opcoes.index(k)))
    else:escolha=max(opcoes,key=lambda k:(resumo['/'.join(k)]['precisao_desenvolvimento'] or 0,resumo['/'.join(k)]['publicar'],-opcoes.index(k)))
    finais={v:m.pacote(pp[v],ys,cat,v,raw[v]) for v in m.VARIANTES};gravar(saida/'modelos_finais.json',{'versao':'cobranca_v24_1','modelos':finais,'selecionado':{'variante':escolha[0],'modo':escolha[1]},'cumpre_meta_na_referencia':bool(eleg)})
    gravar(saida/'escolha_antes_559.json',{'variante':escolha[0],'modo':escolha[1],'cumpre_meta_na_referencia':bool(eleg),'criterio':'Somente desenvolvimento exposto antes da aplicação às 559.','calibracao_global_independente':False})
    csv_salvar(saida/'avaliacao_100.csv',[{**r,'avaliacao':v} for v,rr in ext.items() for r in rr]+[{**r,'avaliacao':v+'/'+modo} for (v,modo),rr in comp.items() for r in rr]);gravar(saida/'resumo_100.json',resumo)
    gravar(saida/'leituras_100.json',{i:pp[m.VARIANTES[0]][i]['leitura_v24'] for i in ys})
    gravar(saida/'manifesto_inferencia.json',{'projeto_sha256':deps,'artefatos_sha256':{n:sha(saida/n) for n in ['modelos_finais.json','escolha_antes_559.json']},'dados_sha256':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv']}})
    for n,h in deps.items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado durante estudo: '+n)
    gravar(saida/'execucao.json',{'segundos':time.perf_counter()-t,'inferencias_559':0});print(json.dumps({'selecionado':escolha,'resumo':resumo},ensure_ascii=False,indent=2))
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
