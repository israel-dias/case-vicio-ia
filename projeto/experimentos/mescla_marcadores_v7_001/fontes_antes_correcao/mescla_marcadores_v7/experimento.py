"""Mescla condicional v7: novos campos efetivos, treino e calibração offline."""
from collections import Counter
import csv
import json
from pathlib import Path
import time

from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from melhorias_v3.experimento import gravar,csv_salvar,separar,validar_grupos
from melhorias_v3.representacao import NOMES,carregar_catalogo,lexico
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from flexivel_v5.runtime import ATIVOS
from .texto import rotear,foco

VARIANTES=('roteamento_sem_foco','mescla_condicional')
EXTRAS=['similaridade_foco','diferenca_melhor_foco','foco_utilizavel','norma_foco','artigo_foco']
PESO_FOCO=.4


def preparar(cat,qs):
    preparadas={};rotas={}
    for qid,q in qs.items():preparadas[qid],rotas[qid]=rotear(q,cat.temas)
    perfis=cat.transformar(preparadas)
    for qid,p in perfis.items():
        r=rotas[qid];e=foco(preparadas[qid],cat.temas)
        # Agrupamento usa o texto original, jamais o rótulo nem o ID.
        p['hash']=f.campos(qs[qid])['hash']
        texto=lexico(e['texto_foco'],cat.aliases)
        w=(cat.escopo_palavras.transform([texto])@cat.ew.T).toarray()[0]
        c=(cat.escopo_caracteres.transform([texto])@cat.ec.T).toarray()[0]
        docs=.7*w+.3*c
        fs=f.np.asarray([max(docs[js]) for js in cat.membros])
        refs=cat.referencias.extrair(e['texto_foco'])
        apoios=f.np.asarray([cat.referencias.apoio(refs,t,cat.temas) for t in cat.familias])
        p['x_rota']=p['features_v3'][:,[NOMES.index(n) for n in ATIVOS]]
        p['x_mescla']=f.np.column_stack([p['x_rota'],fs,fs-max(fs),
                f.np.full(len(fs),float(e['presente'])),apoios])
        norm_base=p['scores']/max(max(p['scores']),1e-12)
        norm_foco=fs/max(max(fs),1e-12)
        p['ranking_roteamento_sem_foco']=p['scores']
        p['ranking_mescla_condicional']=(.6*norm_base+.4*norm_foco if max(fs)>0 else norm_base)
        p['scores_foco']=fs;p['rota']=r;p['foco']=e
    return perfis


def matriz(p,nome):
    if nome not in VARIANTES:raise ValueError('Variante desconhecida.')
    return p['x_rota'] if nome=='roteamento_sem_foco' else p['x_mescla']


def ajustar(perfis,ys,cat,nome):
    if not perfis or set(perfis)!=set(ys):raise ValueError('Treino vazio ou rótulos externos.')
    cont=Counter(p['hash'] for p in perfis.values())
    xx=[];yy=[];pesos=[]
    for i,p in perfis.items():
        xx.extend(matriz(p,nome))
        yy.extend(int(f.aceito(t,ys[i],cat.temas)) for t in cat.familias)
        pesos.extend([1/cont[p['hash']]]*len(cat.familias))
    return ajustar_linear_eficiente(xx,yy,pesos,True)


def sinais(perfis,mod,cat,nome):
    rows=[]
    for i,p in perfis.items():
        k=int(f.ordenar(p['ranking_'+nome])[0]);t=cat.familias[k]
        rows.append({'id':i,'tema_central_id':t,
            'sinal':float(a.escore_linear(matriz(p,nome)[[k]],mod)[0]),
            'elegivel':bool(not p['rota']['conteudo_insuficiente'] and
                max(p['scores'][k],p['scores_novos'][k],p['scores_foco'][k] if nome=='mescla_condicional' else 0)>=.03),
            'modo':p['rota']['modo'],'motivo_rota':p['rota']['motivo'],
            'cabecalho_removido':bool(p['rota']['cabecalho_removido']),
            'foco_utilizavel':p['foco']['presente'],'texto_foco':p['foco']['texto_foco']})
    return rows


def aplicar(perfis,mod,cat,nome,calib,pol):
    ss=sinais(perfis,mod,cat,nome)
    return [{**r,'confianca':p,'decisao':f.decidir(r,p,pol)}
            for r,p in zip(ss,a.confiancas(ss,calib))]


def executar(projeto,saida):
    inicio=time.perf_counter();projeto=Path(projeto).resolve();saida=Path(saida).resolve()
    if saida.exists():raise ValueError('Saída existente. Preserve o histórico usando outra pasta.')
    qs,temas,ys=f.carregar(projeto/'dados/anexos')
    if (len(qs),len(ys),len(temas))!=(659,100,377):raise ValueError('Anexos diferentes do protocolo.')
    cat,_=carregar_catalogo(projeto)
    folds=json.loads((projeto/'experimentos/melhorias_v3_001/auditoria_folds.json').read_text())
    codigo=['mescla_marcadores_v7/texto.py','mescla_marcadores_v7/experimento.py',
        'avaliar_mescla_v7.py','compatibilidade_v2/features.py','melhorias_v3/representacao.py',
        'melhorias_v3/aprendizado.py','auditoria_confianca_v4/experimento.py']
    hashes={n:sha(projeto/n) for n in codigo}
    entradas={n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv','folha_verdade.csv']}
    preservados={n:sha(projeto/n) for n in ['publicacao.csv','previsao.txt']}
    gravar(saida/'protocolo_previo.json',{
        'variantes':VARIANTES,'considerando_como_marcador':False,'peso_foco':PESO_FOCO,
        'zero_enunciado':'Instrução sem conteúdo temático residual, ou lista de pelo menos duas famílias literais sem caso/assertivas, com alternativas temáticas. Apaga também comando e metadados no texto efetivo.',
        'excecao_alternativas':'Certo/Errado e combinações de I/II/III não substituem o conteúdo do enunciado.',
        'mescla':'Cabeçalho seguido de itens é removido; como sendo preserva antecedente; conduta abaixo usa contexto posterior; referências a listas e predicados incompletos não viram foco exclusivo.',
        'modelo':'Regressão logística C=1, liblinear; compatibilidade de todos os candidatos; calibração logística monotônica.',
        'atributos_roteamento':ATIVOS,'atributos_mescla':ATIVOS+EXTRAS,
        'meta_empirica_interna':.95,'suporte_minimo_interno':10,
        'avaliacao':'Mesmos 5 folds externos e 4 internos, sem rótulos externos no treino/calibração de cada fold.',
        'exposicao':'Rótulos e erros anteriores já conhecidos. Novo desenvolvimento reutilizado; não teste externo cego.',
        'escolha_de_variante_pelo_volume_559':False,'promove_entrega':False,
        'codigo_sha256':hashes,'dados_sha256':entradas,'entrega_preservada_sha256':preservados,
        'folds_sha256':sha(projeto/'experimentos/melhorias_v3_001/auditoria_folds.json'),
        'rotulos_das_559':0,'chamadas_llm':0})
    perfis=preparar(cat,{i:qs[i] for i in sorted(ys)})
    pred={n:[] for n in VARIANTES}
    for fold in folds:
        n=fold['fold'];tr,vl=fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(perfis,tr,vl,ys)
        print(f'Mescla condicional: fold externo {n}/5.',flush=True)
        internas={nome:[] for nome in VARIANTES}
        for dentro in fold['folds_internos']:
            ti,vi=dentro['treino_ids'],dentro['validacao_ids']
            validar_grupos(perfis,ti,vi,tr)
            for nome in VARIANTES:
                mod=ajustar(separar(perfis,ti),{i:ys[i] for i in ti},cat,nome)
                internas[nome].extend(a.avaliar(sinais(separar(perfis,vi),mod,cat,nome),{i:ys[i] for i in vi},temas))
        calibs={nome:a.calibrar(internas[nome]) for nome in VARIANTES}
        pols={nome:a.politica(internas[nome],a.confiancas(internas[nome],calibs[nome])) for nome in VARIANTES}
        mods={nome:ajustar(separar(perfis,tr),{i:ys[i] for i in tr},cat,nome) for nome in VARIANTES}
        gravar(saida/f'folds/fold_{n}.json',{'modelos':mods,'calibradores':calibs,'politicas':pols,
            'treino_ids':tr,'avaliacao_ids':vl,'protocolo_sha256':sha(saida/'protocolo_previo.json')})
        for nome in VARIANTES:
            rows=aplicar(separar(perfis,vl),mods[nome],cat,nome,calibs[nome],pols[nome])
            pred[nome].extend({**r,'fold':n} for r in a.avaliar(rows,{i:ys[i] for i in vl},temas))
    resumo={}
    for nome,rows in pred.items():
        rows.sort(key=lambda r:r['id'])
        if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('Previsões OOF incompletas.')
        csv_salvar(saida/f'previsoes_{nome}.csv',rows);resumo[nome]=a.resumo(rows)
    # Dois modelos diagnósticos, sem seleção entre eles com base nas 559.
    modelos={}
    for nome in VARIANTES:
        cal=a.calibrar(pred[nome])
        modelos[nome]={'modelo':ajustar(perfis,ys,cat,nome),'calibrador':cal,
            'politica':a.politica(pred[nome],a.confiancas(pred[nome],cal))}
    gravar(saida/'modelos_diagnosticos.json',modelos)
    alvo=preparar(cat,{i:q for i,q in qs.items() if i not in ys})
    anteriores={r['id']:r for r in csv.DictReader((projeto/'publicacao.csv').open())}
    simulacoes={};todas=[]
    for nome,m in modelos.items():
        rows=aplicar(alvo,m['modelo'],cat,nome,m['calibrador'],m['politica'])
        for r in rows:
            ant=anteriores[r['id']]
            r.update({'variante':nome,'tema_v5':ant['tema_central_id'],'decisao_v5':ant['decisao'],
                'confianca_v5':float(ant['confianca']),'caminho':temas[r['tema_central_id']]['caminho']})
        todas.extend(rows)
        simulacoes[nome]={'publicar':sum(r['decisao']=='publicar' for r in rows),
            'revisar':sum(r['decisao']=='revisar' for r in rows),'fora':0,
            'revisar_para_publicar':sum(r['decisao']=='publicar' and r['decisao_v5']=='revisar' for r in rows),
            'publicar_para_revisar':sum(r['decisao']=='revisar' and r['decisao_v5']=='publicar' for r in rows),
            'mudancas_tema':sum(r['tema_central_id']!=r['tema_v5'] for r in rows),
            'precisao_real':None,'promovida_para_entrega':False}
    csv_salvar(saida/'simulacoes_559.csv',todas)
    audit={i:{'rota':p['rota'],'foco':p['foco']} for i,p in {**perfis,**alvo}.items()}
    gravar(saida/'campos_efetivos_659.json',audit)
    contagens={}
    for nome,pp in [('100_rotulados',perfis),('559_avaliados',alvo)]:
        contagens[nome]={'alternativas_exclusivas':sum(p['rota']['peso_textual_enunciado']==0 for p in pp.values()),
            'cabecalho_removido':sum(bool(p['rota']['cabecalho_removido']) for p in pp.values()),
            'foco_utilizavel':sum(p['foco']['presente'] for p in pp.values()),
            'conteudo_insuficiente':sum(p['rota']['conteudo_insuficiente'] for p in pp.values())}
    resultado={'comparacao_100':resumo,'simulacao_559':simulacoes,'roteamento':contagens,
        'segundos':time.perf_counter()-inicio,'entrega_alterada':False,
        'precisao_559_medida':False,'codigo_sha256':hashes}
    gravar(saida/'resumo.json',resultado)
    for nome,h in preservados.items():
        if sha(projeto/nome)!=h:raise ValueError('Entrega anterior foi alterada.')
    for nome,h in hashes.items():
        if sha(projeto/nome)!=h:raise ValueError('Código alterado durante a execução.')
    for nome,h in entradas.items():
        if sha(projeto/'dados/anexos'/nome)!=h:raise ValueError('Anexo alterado durante a execução.')
    print(json.dumps(resultado,ensure_ascii=False,indent=2),flush=True)
    return resultado
