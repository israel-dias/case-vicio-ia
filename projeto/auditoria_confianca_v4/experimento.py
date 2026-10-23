"""Audita a confiança sem criar rótulos ou exceções para as 559 questões."""
from __future__ import annotations

from collections import Counter
import csv
import importlib.metadata
import json
import math
from pathlib import Path
import time

from compatibilidade_v2 import features as f
from compatibilidade_v2 import runtime as rt
from melhorias_v3 import aprendizado as a
from melhorias_v3.experimento import csv_salvar, gravar, separar, validar_grupos
from melhorias_v3.representacao import NOMES, carregar_catalogo


ORIGEM = {'palavra_assunto_origem', 'origem_compativel', 'origem_reconhecida'}
FORMATO = {'certo_errado', 'assertivas_numeradas', 'numero_alternativas'}
APOIO_DUPLO = {'apoio_enunciado_e_alternativas', 'evidencia_escopo_enunciado_alt'}
NORMAS = {'lei_literal', 'artigo_literal', 'norma_enunciado', 'norma_alternativas',
          'artigo_enunciado', 'artigo_alternativas', 'citacao_sem_correspondencia',
          'ha_norma_explicita', 'ha_artigo_vinculado'}
ENXUTOS = ['media3_completo', 'titulo_enunciado', 'escopo_enunciado', 'escopo_comando',
           'escopo_alternativa_max', 'escopo_alternativa_media', 'norma_enunciado',
           'norma_alternativas', 'artigo_enunciado', 'artigo_alternativas']


def sem(nomes):
    return [n for n in NOMES if n not in nomes]


# Definições anteriores aos resultados. Não há parâmetros por questão ou tema.
VARIANTES = [
    {'nome': 'controle_v3', 'atributos': list(NOMES), 'treino': 'todos_candidatos'},
    {'nome': 'sem_citacao_ausente', 'atributos': sem({'citacao_sem_correspondencia'}), 'treino': 'todos_candidatos'},
    {'nome': 'sem_metadados', 'atributos': sem(ORIGEM), 'treino': 'todos_candidatos'},
    {'nome': 'sem_formato', 'atributos': sem(FORMATO), 'treino': 'todos_candidatos'},
    {'nome': 'sem_apoio_duplo', 'atributos': sem(APOIO_DUPLO), 'treino': 'todos_candidatos'},
    {'nome': 'sem_sinais_normativos', 'atributos': sem(NORMAS), 'treino': 'todos_candidatos'},
    {'nome': 'sem_origem_formato_apoio', 'atributos': sem(ORIGEM | FORMATO | APOIO_DUPLO), 'treino': 'todos_candidatos'},
    {'nome': 'evidencias_enxutas', 'atributos': ENXUTOS, 'treino': 'todos_candidatos'},
    {'nome': 'direto_top1_enxuto', 'atributos': ENXUTOS, 'treino': 'primeiro_candidato'},
]


def validar_variantes(variantes=VARIANTES):
    nomes = [v['nome'] for v in variantes]
    if len(set(nomes)) != len(nomes) or nomes[0] != 'controle_v3':
        raise ValueError('Variantes repetidas ou controle ausente.')
    for v in variantes:
        ns = v['atributos']
        if not ns or len(ns) != len(set(ns)) or not set(ns) <= set(NOMES):
            raise ValueError('Atributos inválidos.')
        if v['treino'] not in {'todos_candidatos', 'primeiro_candidato'}:
            raise ValueError('Objetivo de treino desconhecido.')


def projetar(perfis, variante):
    ix = [NOMES.index(n) for n in variante['atributos']]
    return {i: {**p, 'features_v3': p['features_v3'][:, ix].copy()} for i, p in perfis.items()}


def ajustar_linear_eficiente(x, y, pesos, balancear):
    """Mesma regressão da v3; somas de pesos por classe calculadas uma só vez."""
    x, y, pesos = f.np.asarray(x,dtype=float), f.np.asarray(y,dtype=int), f.np.asarray(pesos,dtype=float)
    if x.ndim!=2 or len(x)!=len(y) or len(y)!=len(pesos) or not len(y):
        raise ValueError('Matriz de treinamento incompatível.')
    if not f.np.isfinite(x).all() or not f.np.isfinite(pesos).all() or (pesos<=0).any():
        raise ValueError('Dados de treinamento inválidos.')
    if len(set(y))==1:
        return f.ajustar_linear(x,y,pesos,balancear=False)
    scaler = f.StandardScaler().fit(x,sample_weight=pesos)
    z = scaler.transform(x)
    if balancear:
        total = float(sum(pesos))
        massas = {c:float(sum(pesos[y==c])) for c in set(y)}
        pesos = pesos * f.np.asarray([total/(2*massas[c]) for c in y])
    lr = f.LogisticRegression(C=1.,solver='liblinear',max_iter=1500,random_state=2026)
    with f.threadpool_limits(limits=2):lr.fit(z,y,sample_weight=pesos)
    return {'dimensao':x.shape[1],'media':scaler.mean_.tolist(),'escala':scaler.scale_.tolist(),
            'coeficientes':lr.coef_[0].tolist(),'intercepto':float(lr.intercept_[0])}


def ajustar(perfis, ys, catalogo, variante):
    if set(perfis) != set(ys) or not perfis:
        raise ValueError('O treino recebeu rótulos de outro grupo.')
    pp = projetar(perfis, variante)
    contagens = Counter(p['hash'] for p in pp.values())
    xx, yy, pesos = [], [], []
    for qid, p in pp.items():
        if variante['treino'] == 'todos_candidatos':
            xx.extend(p['features_v3'])
            yy.extend(int(f.aceito(t,ys[qid],catalogo.temas)) for t in catalogo.familias)
            pesos.extend([1/contagens[p['hash']]]*len(catalogo.familias))
            continue
        k = int(f.ordenar(p['scores'])[0])
        xx.append(p['features_v3'][k])
        yy.append(int(f.aceito(catalogo.familias[k], ys[qid], catalogo.temas)))
        pesos.append(1 / contagens[p['hash']])
    # Alvo direto: o primeiro candidato está certo? Frequência natural das classes.
    return ajustar_linear_eficiente(xx, yy, pesos, balancear=variante['treino']=='todos_candidatos')


def sinais(perfis, modelo, familias, variante):
    pp = projetar(perfis, variante)
    saida = []
    for qid, p in pp.items():
        k = int(f.ordenar(p['scores'])[0])
        valor = float(a.escore_linear(p['features_v3'][[k]], modelo)[0])
        saida.append({'id': qid, 'tema_central_id': familias[k], 'sinal': valor,
                      'elegivel': bool(p['scores'][k] >= .03 or p['scores_novos'][k] >= .03)})
    return saida


def escolher_internamente(politicas):
    # Todos preservam o mesmo tema; empate favorece o controle e depois a ordem fixa.
    return max(politicas, key=lambda n: (politicas[n]['suporte_interno'],
               -next(i for i, v in enumerate(VARIANTES) if v['nome'] == n)))


def decompor(atributos, modelo, calibrador):
    """Decomposição algébrica exata do logit; não é explicação causal."""
    if 'constante' in modelo or 'constante' in calibrador:
        raise ValueError('Modelo constante não tem decomposição por atributo.')
    if len(atributos) != modelo['dimensao']:
        raise ValueError('Atributos incompletos.')
    mult = calibrador['coeficientes'][0] / calibrador['escala'][0]
    intercepto = calibrador['intercepto'] + mult * (modelo['intercepto'] - calibrador['media'][0])
    partes = [(x-u)/s*w*mult for x, u, s, w in zip(
        atributos, modelo['media'], modelo['escala'], modelo['coeficientes'])]
    logit = intercepto + sum(partes)
    p = 1/(1+math.exp(-max(-50., min(50., logit))))
    return {'intercepto_logit': intercepto, 'contribuicoes_logit': partes,
            'logit': logit, 'confianca_reconstruida': p}


def manifesto_valido(pasta):
    p = Path(pasta).resolve()
    manifest = json.loads((p/'manifesto.json').read_text())
    for nome, h in manifest.items():
        arq = (p/nome).resolve()
        if not arq.is_relative_to(p) or rt.sha(arq) != h:
            raise ValueError('Experimento anterior alterado: '+nome)


def diagnosticar(projeto, saida, catalogo, perfis, ys):
    registro = json.loads((projeto/'artefatos/melhorias_v3/modelo.json').read_text())
    modelo = registro['modelos']['todos']
    calib = registro['calibradores']['referencias_fixa']
    ras = [json.loads(l) for l in (projeto/'entrega_experimental_v3/rastreabilidade.jsonl').read_text().splitlines()]
    negativos = Counter()
    exemplos = []
    rows = []
    for r in ras:
        if r['id'] in ys or r['decisao'] != 'revisar':
            continue
        vals = [r['atributos'][n] for n in NOMES]
        d = decompor(vals, modelo, calib)
        if not math.isclose(d['confianca_reconstruida'], r['confianca'], abs_tol=1e-12):
            raise ValueError('A decomposição não reproduz a confiança original.')
        partes = dict(zip(NOMES, d['contribuicoes_logit']))
        for n, v in sorted(partes.items(), key=lambda p:p[1])[:3]:
            if v < 0: negativos[n] += 1
        rows.extend({'id': r['id'], 'atributo': n, 'valor': x, 'coeficiente': c,
                     'contribuicao_logit_calibrado': partes[n], 'confianca_v3': r['confianca']}
                    for n, x, c in zip(NOMES, vals, modelo['coeficientes']))
        if r['id'] in {'Q0568', 'Q0496', 'Q0523', 'Q0492', 'Q0458'}:
            exemplos.append({'id':r['id'], 'tema_sugerido':r['caminho'], 'confianca':r['confianca'],
                'alertas':r['alertas_computados'], **d,
                'maiores_negativos': sorted(partes.items(),key=lambda p:p[1])[:5],
                'maiores_positivos': sorted(partes.items(),key=lambda p:-p[1])[:5]})
    coef = []
    folds = [json.loads(p.read_text())['modelos']['todos'] for p in sorted(
        (projeto/'experimentos/melhorias_v3_001/modelos_folds').glob('fold_*.json'))]
    for j, n in enumerate(NOMES):
        cs = [m['coeficientes'][j] for m in folds]
        coef.append({'atributo':n, 'coeficiente_final':modelo['coeficientes'][j],
            'folds_positivo':sum(x>0 for x in cs),'folds_negativo':sum(x<0 for x in cs),
            'menor_coeficiente_folds':min(cs), 'maior_coeficiente_folds':max(cs)})
    # Correlações apenas entre os atributos dos candidatos efetivamente sugeridos.
    mat = f.np.asarray([p['features_v3'][int(f.ordenar(p['scores'])[0])] for p in perfis.values()])
    sd = mat.std(axis=0); validos = [j for j in range(len(NOMES)) if sd[j]>1e-12]
    cor = f.np.corrcoef(mat[:,validos],rowvar=False)
    pares = sorted([{'atributo_1':NOMES[i], 'atributo_2':NOMES[j], 'correlacao':float(cor[ii,jj])}
                     for ii,i in enumerate(validos) for jj,j in enumerate(validos) if ii<jj and abs(cor[ii,jj])>=.85],
                     key=lambda p:-abs(p['correlacao']))
    csv_salvar(saida/'coeficientes_e_estabilidade.csv',coef)
    csv_salvar(saida/'contribuicoes_384_revisoes.csv',rows)
    gravar(saida/'diagnostico_algebrico.json',{'exemplos':exemplos,'correlacoes_acima_085':pares,
        'frequencia_tres_maiores_contribuicoes_negativas':dict(negativos),
        'nota':'Contribuições relativas à centralização do treino, não pontos percentuais nem causas jurídicas. Atributos correlacionados podem compensar-se.'})
    return coef, exemplos, pares


def executar(projeto, saida):
    inicio = time.perf_counter()
    projeto, saida = Path(projeto).resolve(), Path(saida).resolve()
    if saida.exists(): raise ValueError('Saída existente; escolha outra pasta.')
    validar_variantes()
    antigo = projeto/'experimentos/melhorias_v3_001'
    manifesto_valido(antigo)
    dados = projeto/'dados/anexos'
    protocolo_v3 = json.loads((antigo/'protocolo_previo.json').read_text())
    for nome,h in protocolo_v3['dados_sha256'].items():
        if rt.sha(dados/nome)!=h: raise ValueError('Anexos diferentes dos da v3.')
    for nome,h in protocolo_v3['arquivos_sha256'].items():
        if rt.sha(projeto/nome)!=h: raise ValueError('Código original alterado: '+nome)
    qs, temas, ys = f.carregar(dados)
    if (len(qs),len(temas),len(ys)) != (659,377,100): raise ValueError('Universo diferente do protocolo.')
    folds = json.loads((antigo/'auditoria_folds.json').read_text())
    core = ['auditar_confianca_v4.py','auditoria_confianca_v4/experimento.py','compatibilidade_v2/features.py',
            'melhorias_v3/aprendizado.py','melhorias_v3/representacao.py']
    protocolo = {'versao':'auditoria_confianca_v4_1','variantes':VARIANTES,
        'hipoteses':['Alertas não equivalem a penalidades automáticas.',
          'Remover grupos pode melhorar ou piorar a seleção; todos exigem novo ajuste e calibração.',
          'Treinar diretamente o acerto do primeiro candidato pode diferir de treinar todos os pares questão-tema.'],
        'tema_candidato':'O primeiro candidato lexical da v3 é preservado em todas as variantes.',
        'avaliacao':'Mesmos cinco folds externos e quatro internos; calibração/corte/seleção usam apenas grupos internos.',
        'meta_empirica_interna':.95,'suporte_minimo_interno':10,
        'regra_selecao':'Maior suporte interno sob a meta; empate favorece o controle, depois a ordem fixa.',
        'promocao_automatica_para_entrega':False,'rotulos_das_559_usados':0,
        'exposicao':'Os 100 rótulos e exemplos já foram discutidos; desenvolvimento reutilizado, não teste externo cego.',
        'dados_sha256':protocolo_v3['dados_sha256'],
        'codigo_sha256':{n:rt.sha(projeto/n) for n in core},
        'dependencias':{n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn','threadpoolctl']}}
    gravar(saida/'protocolo_previo.json',protocolo)
    catalogo,_ = carregar_catalogo(projeto)
    # Só os 100 textos rotulados chegam à transformação usada para ajuste/seleção.
    perfis = catalogo.transformar({i:qs[i] for i in sorted(ys)})
    coef, exemplos, pares = diagnosticar(projeto,saida,catalogo,perfis,ys)
    nomes = [v['nome'] for v in VARIANTES]
    previsoes = {n:[] for n in [*nomes,'selecao_interna']}
    auditoria = []
    for fold in folds:
        n = fold['fold'];tr,vl = fold['treino_ids'],fold['avaliacao_ids']
        validar_grupos(perfis,tr,vl,ys)
        print(f'Fold externo {n}/5: remoções avaliadas após novo ajuste e calibração.',flush=True)
        internas = {n:[] for n in nomes}
        for dentro in fold['folds_internos']:
            ti,vi = dentro['treino_ids'],dentro['validacao_ids']
            validar_grupos(perfis,ti,vi,tr)
            for variante in VARIANTES:
                mod = ajustar(separar(perfis,ti),{i:ys[i] for i in ti},catalogo,variante)
                ss = sinais(separar(perfis,vi),mod,catalogo.familias,variante)
                internas[variante['nome']].extend(a.avaliar(ss,{i:ys[i] for i in vi},temas))
        modelos,calibs,politicas = {},{},{}
        for variante in VARIANTES:
            nome = variante['nome']
            calibs[nome] = a.calibrar(internas[nome])
            confs = a.confiancas(internas[nome],calibs[nome])
            politicas[nome] = a.politica(internas[nome],confs)
            modelos[nome] = ajustar(separar(perfis,tr),{i:ys[i] for i in tr},catalogo,variante)
        escolhido = escolher_internamente(politicas)
        registro = {'fold':n,'treino_ids':tr,'avaliacao_ids':vl,
            'selecionado_internamente':escolhido,'modelos':modelos,'calibradores':calibs,'politicas':politicas,
            'protocolo_sha256':rt.sha(saida/'protocolo_previo.json')}
        # Registro anterior à classificação do grupo externo e à consulta de seus acertos.
        gravar(saida/f'modelos_folds/fold_{n}.json',registro)
        externas = {}
        for variante in VARIANTES:
            nome = variante['nome'];ss = sinais(separar(perfis,vl),modelos[nome],catalogo.familias,variante)
            probs = a.confiancas(ss,calibs[nome])
            rows = [{**r,'confianca':p,'decisao':f.decidir(r,p,politicas[nome]),'fold':n}
                    for r,p in zip(ss,probs)]
            externas[nome] = a.avaliar(rows,{i:ys[i] for i in vl},temas)
            previsoes[nome].extend(externas[nome])
        previsoes['selecao_interna'].extend({**r,'variante':escolhido} for r in externas[escolhido])
        auditoria.append({'fold':n,'selecionado':escolhido,'politicas':politicas,
            'treino_ids':tr,'avaliacao_ids':vl})
    resumo = {}
    for nome,rows in previsoes.items():
        rows.sort(key=lambda r:r['id'])
        if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('Previsões incompletas.')
        csv_salvar(saida/f'previsoes_{nome}.csv',rows)
        resumo[nome] = a.resumo(rows)
    # Controle precisa reproduzir a execução preservada, não apenas atingir outra métrica.
    antigas = list(csv.DictReader((antigo/'previsoes_referencias_fixa.csv').open()))
    por_id = {r['id']:r for r in previsoes['controle_v3']}
    for velho in antigas:
        novo = por_id[velho['id']]
        if novo['decisao']!=velho['decisao'] or not math.isclose(novo['confianca'],float(velho['confianca']),abs_tol=1e-11):
            raise ValueError('Controle não reproduz a v3: '+velho['id'])
    gravar(saida/'resumo.json',{'variantes':resumo,'folds':auditoria,
        'limite_oraculo_cobertura_100_temas_fixos':math.floor(resumo['controle_v3']['acertos_top1']/.95)/100,
        'classificacoes_entrega_alteradas':0,'precisao_559_medida':False,
        'segundos':time.perf_counter()-inicio})
    # Modelos finais são diagnósticos. Não geram ou substituem publicacao.csv.
    modelos_finais,calibs_finais,pol_finais = {},{},{}
    for variante in VARIANTES:
        nome = variante['nome']
        modelos_finais[nome] = ajustar(perfis,ys,catalogo,variante)
        calibs_finais[nome] = a.calibrar(previsoes[nome])
        pol_finais[nome] = a.politica(previsoes[nome],a.confiancas(previsoes[nome],calibs_finais[nome]))
    final = escolher_internamente(pol_finais)
    gravar(saida/'modelos_finais_diagnostico.json',{'modelos':modelos_finais,'calibradores':calibs_finais,
        'politicas':pol_finais,'escolha_por_100_oof':final,'uso':'Simulação diagnóstica, sem promoção automática.'})
    # A escolha já está persistida antes de transformar as 559 questões sem rótulo.
    alvo = catalogo.transformar({i:q for i,q in qs.items() if i not in ys})
    anteriores = {r['id']:r for r in map(json.loads,(projeto/'entrega_experimental_v3/rastreabilidade.jsonl').read_text().splitlines())}
    comp = []
    simulacoes = {}
    for variante in VARIANTES:
        nome = variante['nome'];ss = sinais(alvo,modelos_finais[nome],catalogo.familias,variante)
        ps = a.confiancas(ss,calibs_finais[nome]);ct = Counter()
        for r,p in zip(ss,ps):
            decisao = f.decidir(r,p,pol_finais[nome]);ct[decisao]+=1
            ant = anteriores[r['id']]
            if r['tema_central_id']!=ant['tema_central_id']:raise ValueError('A auditoria alterou o tema candidato.')
            comp.append({'id':r['id'],'variante':nome,'tema_central_id':r['tema_central_id'],
                'confianca_v3':ant['confianca'],'decisao_v3':ant['decisao'],
                'confianca_experimental':p,'decisao_experimental':decisao,
                'limiar_experimental':pol_finais[nome]['limiar'],'nao_e_entrega':True})
        simulacoes[nome] = {'questoes':len(ss),'publicar':ct['publicar'],'revisar':ct['revisar'],
            'cobertura':ct['publicar']/len(ss),'precisao_real':None,
            'previsao_media_publicadas':sum(r['confianca_experimental'] for r in comp if r['variante']==nome and r['decisao_experimental']=='publicar')/ct['publicar'] if ct['publicar'] else None}
    csv_salvar(saida/'simulacao_559_variantes.csv',comp)
    gravar(saida/'simulacoes_559.json',{'variantes':simulacoes,'variante_previamente_selecionada':final,
        'nota':'Volume nas 559 não seleciona a variante nem demonstra acerto. Nenhum rótulo jurídico foi criado.'})
    escrever_relatorio(saida,resumo,simulacoes,final,coef,exemplos,pares)
    gravar(saida/'manifesto.json',{str(p.relative_to(saida)):rt.sha(p) for p in sorted(saida.rglob('*'))
                                 if p.is_file() and p.name!='manifesto.json'})
    for n,r in resumo.items(): print(n,json.dumps(r,ensure_ascii=False),flush=True)
    print('Escolha diagnóstica pelos 100 OOF:',final,flush=True)
    print('Nenhuma classificação da entrega foi alterada.',flush=True)
    return resumo


def escrever_relatorio(saida,resultados,simulacoes,final,coef,exemplos,pares):
    txt = ['# Auditoria da confiança — experimento v4','',
        'Objetivo: verificar se os sinais atuais ajudam a separar acertos e erros ou apenas tornam a publicação conservadora. A entrega v3 foi preservada. Não foram respondidas nem rotuladas manualmente as 559 questões avaliadas.','',
        '## O que efetivamente decide','',
        'Os alertas são produzidos depois da decisão. Eles não subtraem pontos fixos. A confiança vem de regressão logística e calibração. Remover o texto de um alerta não muda a decisão. Os atributos correspondentes podem ter pesos positivos ou negativos aprendidos.',
        '', '## Comparação com novo treino e calibração','',
        'Mesmos cinco grupos externos e quatro internos da v3. Em cada grupo, os rótulos externos não entram no treino, calibração, escolha do corte ou seleção da variante. Todos os métodos mantêm as mesmas sugestões de tema. Os 100 rótulos foram vistos anteriormente: este é desenvolvimento comparativo reutilizado, sem avaliação externa nova.',
        '', '| Variante | Atributos | Publicadas/100 | Corretas | Precisão observada | Brier |',
        '|---|---:|---:|---:|---:|---:|']
    for n,r in resultados.items():
        k = 'seleção entre variantes' if n=='selecao_interna' else str(len(next(v['atributos'] for v in VARIANTES if v['nome']==n)))
        p = 'indefinida' if r['precisao_publicadas'] is None else f"{r['precisao_publicadas']:.2%}"
        txt.append(f"| {n} | {k} | {r['publicar']} | {r['acertos_publicadas']} | {p} | {r['brier']:.4f} |")
    acertos=resultados['controle_v3']['acertos_top1'];teto=math.floor(acertos/.95)
    txt += ['',f'As sugestões atuais acertam {acertos}/100 antes da abstenção. Mantendo essas sugestões, mesmo um seletor que soubesse exatamente quais estão corretas publicaria no máximo {teto}/100 sob a meta empírica de 95%. Aumentar somente as probabilidades não corrige as sugestões erradas.',
        '', '## Simulação nas 559 — acerto desconhecido','',
        f'A variante escolhida pelo suporte dos 100 sinais OOF, antes de observar o volume nas 559, foi `{final}`. Essa é uma escolha exploratória; não substitui uma nova avaliação independente.',
        '', '| Variante | Publicar | Revisar | Cobertura | Precisão real |', '|---|---:|---:|---:|---|']
    for n,r in simulacoes.items():txt.append(f"| {n} | {r['publicar']} | {r['revisar']} | {r['cobertura']:.2%} | desconhecida |")
    txt += ['', '## Diagnóstico dos pesos','',
        'O sinal isolado de um coeficiente não demonstra que ele seja necessário, dispensável ou juridicamente correto. As contribuições abaixo são relativas à centralização usada no treino e estão na escala de logit, não em pontos percentuais de confiança. A remoção de atributos foi avaliada com novo ajuste para evitar interpretar uma perturbação artificial do modelo como melhora real.',
        '', '| Atributo | Peso final padronizado | Folds com peso positivo | Folds com peso negativo |','|---|---:|---:|---:|']
    for r in coef:
        if r['atributo'] in ORIGEM|FORMATO|APOIO_DUPLO|{'citacao_sem_correspondencia','palavra_completo','escopo_enunciado'}:
            txt.append(f"| {r['atributo']} | {r['coeficiente_final']:+.4f} | {r['folds_positivo']} | {r['folds_negativo']} |")
    txt += ['', f'Foram encontrados {len(pares)} pares de atributos com correlação absoluta de pelo menos 0,85 entre os primeiros candidatos dos 100 exemplos. Isso sinaliza redundância, sem provar por si só que remover o par melhorará a classificação.',
        '', '## Casos exibidos na conversa','',
        'Estes registros servem apenas para entender a mecânica. Não foram usados como gabarito, exceção por ID ou condição de escolha. Não representam correção jurídica independente.','']
    for e in exemplos:
        txt += [f"### {e['id']} — confiança original {e['confianca']:.2%}",e['tema_sugerido'],'',
                'Maiores contribuições negativas ao logit calibrado: '+', '.join(f'{n} ({v:+.3f})' for n,v in e['maiores_negativos'])+'.','']
    txt += ['## Como interpretar e próximos passos','',
        'Retirar um grupo só é uma melhoria demonstrada nesta amostra se conservar a meta de precisão e melhorar a seleção ou a calibração. Ganhar publicações nas 559, sem seus rótulos, não demonstra qualidade. As tentativas que falham permanecem no relatório.',
        '', 'Não se promove automaticamente um método para a entrega e não se eleva a confiança à mão. As sugestões iniciais e a calibração são problemas distintos. Uma falha persistente na escolha do tema exige melhorar a recuperação ou comparação de candidatos, usando validação e exemplos rotulados adicionais, sem um LLM decidindo os temas avaliados.',
        '', 'Fontes metodológicas: documentação scikit-learn 1.8, interpretação de coeficientes: https://scikit-learn.org/1.8/auto_examples/inspection/plot_linear_model_coefficient_interpretation.html ; validação aninhada: https://scikit-learn.org/1.8/auto_examples/model_selection/plot_nested_cross_validation_iris.html','']
    (saida/'ANALISE.md').write_text('\n'.join(txt),encoding='utf-8')
