"""Inferência e diagnóstico nas 559 fora da folha-verdade; sem novos ajustes."""
import argparse,csv,json,math,time
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import legado,sha
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from melhorias_v3 import aprendizado as a
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.ranking import aplicar as aplicar_v8
from roteamento_v15 import modelo as m
from experimento_atributos_v11 import modelo as v11
from experimento_palavra_v12 import modelo as v12

BASE='foco_contextual/70/preservar_v11'
def salvar_json(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def salvar_csv(p,rows):
    if not rows:p.write_text('id\n');return
    with p.open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def ids_excluidos(experimento):
    grupos=[json.loads((experimento/f'folds/fold_{i}.json').read_text())['avaliacao_ids'] for i in range(1,6)]
    ids=[i for g in grupos for i in g]
    # Folds agrupados por duplicatas podem ter tamanhos diferentes; a divisão
    # original é preservada. O contrato é cobertura única dos 100 IDs.
    if any(not g for g in grupos) or len(ids)!=len(set(ids)) or len(ids)!=100:
        raise ValueError('Os cinco grupos não identificam exatamente 100 IDs distintos.')
    return set(ids)
def validar_alvo(qs,excluidos):
    if len(excluidos)!=100:raise ValueError('Esperados 100 IDs de referência excluídos.')
    esperados={f'Q{i:04d}' for i in range(1,660)}-set(excluidos)
    if len(esperados)!=559 or set(qs)!=esperados:
        raise ValueError('A entrada deve conter exatamente as 559 questões fora dos 100 IDs reservados.')
    return {'total':len(qs),'antigas_259':sum(int(i[1:])<360 for i in qs),
            'recentes_300':sum(int(i[1:])>=360 for i in qs),'rotuladas_incluidas':len(set(qs)&set(excluidos))}
def estatistica(rows):
    n=len(rows);pub=sum(r['decisao']=='publicar' for r in rows)
    return {'questoes':n,'publicar':pub,'revisar':n-pub,'fora':0,
            'cobertura':pub/n if n else None,'precisao_real':None}
def motivo_foco(r,p,cat):
    if r['decisao']=='publicar':return 'publicar'
    k=cat.familias.index(r['tema_central_id'])
    if p['rota']['sem_evidencia']:return 'conteudo_sem_evidencia'
    if max(p['x'][k,:4])<.03:return 'apoio_textual_abaixo_do_piso'
    if r['homonimo_nao_resolvido']:return 'homonimo_com_escopo_nao_resolvido'
    if r['confianca']<.7:return 'confianca_abaixo_de_70'
    raise ValueError('Revisão sem causa contabilizada.')
def decompor(x,modelo,nomes):
    if 'constante' in modelo:return {'constante':modelo['constante'],'contribuicoes':[]}
    valores=((x-f.np.asarray(modelo['media']))/f.np.asarray(modelo['escala']))*f.np.asarray(modelo['coeficientes'])
    todas=[{'atributo':n,'valor':float(v),'contribuicao_logit':float(c)} for n,v,c in zip(nomes,x,valores)]
    sinal=float(sum(valores)+modelo['intercepto'])
    return {'intercepto':modelo['intercepto'],'sinal_reconstruido':sinal,
            'contribuicoes':todas,'apoios_maiores':sorted(todas,key=lambda r:-r['contribuicao_logit'])[:5],
            'contrapesos_maiores':sorted(todas,key=lambda r:r['contribuicao_logit'])[:5],
            'unidade':'logit do comparador; não pontos percentuais de confiança'}
def caminho(t,temas):
    partes=[]
    while t:
        tema=temas[t];partes.append(tema['titulo']);t=tema['parent_id']
    return ' > '.join(reversed(partes))
def executar(projeto,experimento,questoes,saida):
    projeto,experimento,questoes,saida=map(lambda x:Path(x).resolve(),[projeto,experimento,questoes,saida])
    if saida.exists():raise ValueError('Use uma pasta de saída nova.')
    inicio=time.perf_counter();reg=json.loads((experimento/'manifesto_inferencia.json').read_text())
    verificar(projeto,reg['projeto_sha256']);verificar(experimento,reg['experimento_sha256'])
    excluidos=ids_excluidos(experimento)
    qs={q['id']:q for q in legado.ler_questoes(questoes)};recorte=validar_alvo(qs,excluidos)
    saida.mkdir(parents=True)
    salvar_json(saida/'protocolo_previo.json',{'recorte':recorte,'ids_excluidos':sorted(excluidos),
        'entrada_sha256':sha(questoes),'codigo_diagnostico_sha256':sha(Path(__file__)),
        'manifesto_inferencia_sha256':sha(experimento/'manifesto_inferencia.json'),
        'politicas':'As 12 variantes V15 previamente congeladas; nenhuma ajustada nas 559.',
        'base_relatorio':BASE,'selecionar_por_cobertura_559':False,
        'proibicoes':['leitura da folha-verdade','ajuste','calibração','seleção de limiar','rede','chamadas LLM'],
        'concordancia':'Lista de investigação; mesmo tema sugerido por foco e fusão não mede acerto independente.',
        'publicacao_anterior':'Preservar V11 também conserva seus erros e possíveis conflitos novos.',
        'promove_entrega':False})
    # Além de os módulos de inferência não precisarem de rótulos/rede, este
    # diagnóstico bloqueia essas operações para detectar regressões.
    real=Path.open
    def aberto(p,*args,**kwargs):
        if p.name=='folha_verdade.csv':raise AssertionError('Leitura de rótulos bloqueada.')
        return real(p,*args,**kwargs)
    with ExitStack() as guardas:
        for alvo in [(f,'carregar'),(f,'aceito'),(m,'ajustar'),(v12,'ajustar'),(v11,'ajustar'),(a,'calibrar'),(f,'escolher_politica')]:
            guardas.enter_context(patch.object(*alvo,side_effect=AssertionError('Ajuste/rótulos bloqueados.')))
        guardas.enter_context(patch.object(Path,'open',aberto))
        guardas.enter_context(patch('socket.create_connection',side_effect=AssertionError('Rede bloqueada.')))
        guardas.enter_context(patch('socket.socket.connect',side_effect=AssertionError('Rede bloqueada.')))
        cat,_=carregar_catalogo(projeto)
        dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
        print('Preparando somente as 559 questões; rede e rótulos bloqueados.',flush=True)
        pp=m.preparar(cat,dic,qs)
        modelos=json.loads((experimento/'modelos_finais.json').read_text())
        pack=json.loads((projeto/'experimentos/palavra_v12_001/modelos_finais.json').read_text())
        antigo=v12.preparar(cat,dic,qs);taxa=pack['identificador']['confianca']
        cv9=v11.identificadores(aplicar_v8(antigo,pack['controle_v9'],cat),antigo,taxa)
        cv11=v12.combinar(v11.identificadores(v12.aplicar(antigo,pack['controle_v11'],cat,'controle_v11'),antigo,taxa),cv9)
        todos={};resumos={}
        for v,mo in modelos.items():
            for corte in ['calibrado','70']:
                novas=m.aplicar(pp[v],mo,cat,v,corte)
                for politica,rr in [('substituir',novas),('preservar_v11',v11.preservar_publicadas(novas,cv11))]:
                    chave='/'.join([v,corte,politica]);todos[chave]={r['id']:r for r in rr}
                    resumos[chave]={'total_559':estatistica(rr),
                        'antigas_259':estatistica([r for r in rr if int(r['id'][1:])<360]),
                        'recentes_300':estatistica([r for r in rr if int(r['id'][1:])>=360])}
        print('12 configurações congeladas executadas. Diagnosticando revisões e conflitos.',flush=True)
        base=todos[BASE];foco=todos['foco_contextual/70/substituir'];fusao=todos['fusao_contextual/calibrado/preservar_v11']
        motivo=Counter();por_atributo=Counter();diagnosticos=[];csvbase=[];candidatas=[];conflitos=[]
        for i in sorted(qs):
            r=base[i];p=pp['foco_contextual'][i];z=foco[i]
            k=cat.familias.index(z['tema_central_id']);mot='publicacao_preservada_v11' if r.get('publicacao_preservada') else motivo_foco(z,p,cat)
            if r['decisao']=='revisar':motivo[mot]+=1
            comp=decompor(p['x'][k],modelos['foco_contextual']['modelo'],m.NOMES)
            assert math.isclose(comp['sinal_reconstruido'],z['sinal'],abs_tol=1e-9)
            if r['decisao']=='revisar':
                por_atributo.update(t['atributo'] for t in comp['contrapesos_maiores'] if t['contribuicao_logit']<0)
            par=fusao[i];mesmo=par['tema_central_id']==z['tema_central_id']
            candidata=bool(r['decisao']=='revisar' and par['decisao']=='publicar' and mesmo and z['elegivel'])
            principais=[{'tema_id':cat.familias[int(j)],'caminho':caminho(cat.familias[int(j)],cat.temas),
                         'escore_recuperacao':float(p['ranking'][j])} for j in f.ordenar(p['ranking'])[:5]]
            d={'id':i,'grupo':'recentes_300' if int(i[1:])>=360 else 'antigas_259',
               'decisao':r['decisao'],'tema_central_id':r['tema_central_id'],
               'tema_caminho':caminho(r['tema_central_id'],cat.temas),'confianca':r['confianca'],
               'motivo':mot,'publicacao_preservada_v11':bool(r.get('publicacao_preservada')),
               'tema_foco_v15':z['tema_central_id'],'confianca_foco_v15':z['confianca'],
               'elegivel_foco_v15':z['elegivel'],'homonimo_nao_resolvido_foco_v15':z['homonimo_nao_resolvido'],
               'decisao_fusao_calibrada':par['decisao'],'tema_fusao_calibrada':par['tema_central_id'],
               'confianca_fusao_calibrada':par['confianca'],
               'concordancia_exata_foco_fusao':mesmo,'candidata_para_investigar':candidata}
            csvbase.append(d)
            if candidata:candidatas.append(d)
            if r.get('publicacao_preservada') and (not z['elegivel'] or r['tema_central_id']!=z['tema_central_id']):conflitos.append(d)
            diagnosticos.append({**d,'questao':qs[i],'rota':p['rota'],'top5_foco':principais,'decomposicao_foco':comp,
                'decomposicao_explicita':'Explica o sinal do FOCO V15; não explica a confiança herdada da V11.'})
        faixas=Counter()
        for r in base.values():
            lo=min(90,int(float(r['confianca'])*10)*10);faixas[f'{lo:02d}-{lo+10:03d}']+=1
        por_modo={modo:estatistica([base[i] for i,p in pp['foco_contextual'].items() if p['rota']['modo']==modo])
                  for modo in sorted({p['rota']['modo'] for p in pp['foco_contextual'].values()})}
        delta=[r for i,r in base.items() if r['decisao']=='publicar' and next(x for x in cv11 if x['id']==i)['decisao']!='publicar']
        resumo={'recorte':recorte,'base':BASE,'base_resultados':resumos[BASE],
                'controle_v11':{'total_559':estatistica(cv11),'recentes_300':estatistica([r for r in cv11 if int(r['id'][1:])>=360])},
                'adicoes_sobre_v11':len(delta),'motivos_primarios_revisao':dict(motivo.most_common()),
                'contrapesos_entre_cinco_mais_negativos_em_revisoes':dict(por_atributo.most_common()),
                'faixas_confianca_final':dict(sorted(faixas.items())),
                'por_modo_leitura':por_modo,'comparacao_variantes':resumos,
                'candidatas_concordantes_sem_liberacao':len(candidatas),
                'publicacoes_preservadas_com_alerta_do_foco':len(conflitos),
                'precisao_real_559':None,'precisao_real_300':None,
                'validacao':'Somente integridade/reprodução/inferência; acerto jurídico não medido.',
                'guardas':{'rede_bloqueada':True,'rotulos_bloqueados':True,'treino_calibracao_limiares_bloqueados':True},
                'segundos':time.perf_counter()-inicio,'promove_entrega':False}
        # Confere igualdade com a experiência anterior sem usar rótulos.
        previa=list(csv.DictReader((experimento/'simulacao_559.csv').open()))
        for chave,mapa in todos.items():
            v,c,pol=chave.split('/')
            esperado={r['id']:r for r in previa if (r['variante'],r['corte'],r['politica'])==(v,c,pol)}
            if set(esperado)!=set(mapa):raise ValueError('IDs divergentes da experiência congelada.')
            for i,r in mapa.items():
                if (str(r['tema_central_id']),r['decisao'],r['confianca'])!=(esperado[i]['tema_central_id'],esperado[i]['decisao'],float(esperado[i]['confianca'])):
                    raise ValueError('Reprodução divergente: '+chave+' '+i)
        resumo['reproducao_exata_12_configuracoes']=True
        salvar_json(saida/'resumo.json',resumo)
        salvar_csv(saida/'classificacoes_559.csv',csvbase)
        salvar_csv(saida/'candidatas_concordantes_NAO_LIBERADAS.csv',candidatas)
        salvar_csv(saida/'preservadas_com_alerta.csv',conflitos)
        salvar_csv(saida/'comparacao_variantes_559.csv',[{'configuracao':chave,**r} for chave,mp in todos.items() for r in mp.values()])
        with (saida/'diagnostico_por_questao.jsonl').open('w',encoding='utf-8') as arq:
            for d in diagnosticos:arq.write(json.dumps(d,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({k:resumo[k] for k in ['recorte','base_resultados','motivos_primarios_revisao','candidatas_concordantes_sem_liberacao','publicacoes_preservadas_com_alerta_do_foco','reproducao_exata_12_configuracoes','segundos']},ensure_ascii=False,indent=2),flush=True)
    return resumo
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/roteamento_v15_002'))
    p.add_argument('--questoes',type=Path,default=Path('experimentos/roteamento_v15_002/questoes_559_sem_rotulos.jsonl'))
    p.add_argument('--saida',type=Path,required=True);z=p.parse_args()
    executar(z.projeto,z.experimento,z.questoes,z.saida)
