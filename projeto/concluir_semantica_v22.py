"""Conclui a inferência congelada V22 em blocos recuperáveis, sem rótulos."""
import argparse,csv,json,socket,time
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import legado,sha
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from semantica_v22 import modelo as m
from testar_isolamento_v17 import gravar,csv_salvar,controle
from isolamento_v17.metricas import medir


def executar(projeto,experimento,questoes,bloco=40):
    projeto,experimento,questoes=map(lambda p:Path(p).resolve(),[projeto,experimento,questoes]);t=time.perf_counter()
    if (experimento/'execucao.json').exists():raise ValueError('Experimento já concluído; use o comando de inferência para reproduzir.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text());verificar(projeto,reg['projeto_sha256']);verificar(experimento,reg['artefatos_sha256'])
    if sha(projeto/'artefatos/semantica_v21/manifesto.json')!=reg['cache_manifesto_sha256']:raise ValueError('Cache diferente.')
    qs={q['id']:q for q in legado.ler_questoes(questoes)}
    if len(qs)!=559:raise ValueError('A conclusão deste experimento exige os 559 itens sem rótulos.')
    packs=json.loads((experimento/'modelos_finais.json').read_text())['modelos'];check=experimento/'checkpoints_inferencia';check.mkdir(exist_ok=True)
    chave={'questoes_sha256':sha(questoes),'modelos_sha256':sha(experimento/'modelos_finais.json'),'codigo_sha256':sha(Path(__file__)),'bloco':bloco}
    if (check/'protocolo.json').exists():
        if json.loads((check/'protocolo.json').read_text())!=chave:raise ValueError('Checkpoint de outra execução.')
    else:gravar(check/'protocolo.json',chave)
    abrir=Path.open
    def protegido(p,*a,**kw):
        if p.name=='folha_verdade.csv':raise AssertionError('Rótulos indisponíveis na inferência.')
        return abrir(p,*a,**kw)
    resultados=[];ids=sorted(qs);novos=0
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')),patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')),patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')):
        cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
        for j,inicio in enumerate(range(0,len(ids),bloco),1):
            grupo=ids[inicio:inicio+bloco];p=check/f'bloco_{j:03}.json'
            if p.exists():
                rr=json.loads(p.read_text())
                if len(rr)!=len(grupo)*len(m.VARIANTES) or {r['id'] for r in rr}!=set(grupo):raise ValueError('Checkpoint incompleto.')
            else:
                pp=m.preparar(projeto,cat,dic,{i:qs[i] for i in grupo});rr=[r for v in m.VARIANTES for r in m.aplicar(pp[v],packs[v],cat,v)];gravar(p,rr);novos+=1
            resultados.extend(rr);print(f'Bloco {j}: {min(inicio+bloco,len(ids))}/{len(ids)} itens; salvo.',flush=True)
    resumo=json.loads((experimento/'resumo_antes_559.json').read_text());ref=controle(projeto,'classificacoes_559_todas_variantes.csv')
    for v in m.VARIANTES:
        rr=[r for r in resultados if r['variante']==v];resumo[v]['alvo_559']=medir(rr,ref);resumo[v]['recentes_300']=medir([r for r in rr if int(r['id'][1:])>=360])
    csv_salvar(experimento/'classificacoes_559_todas_variantes.csv',resultados);gravar(experimento/'resumo.json',resumo)
    (experimento/'questoes_559_sem_rotulos.jsonl').write_text(''.join(json.dumps(qs[i],ensure_ascii=False)+'\n' for i in ids))
    gravar(experimento/'verificacao_inferencia.json',{'questoes':len(qs),'previsoes':len(resultados),'blocos':math_ceil(len(qs),bloco),'novos_blocos':novos,'rotulos_rede_treino_avaliador_recalibracao_bloqueados':True,'encoder_carregado':False,'promove_entrega':False})
    gravar(experimento/'execucao.json',{'segundos_conclusao_inferencia':time.perf_counter()-t,'conclusao_por_checkpoint':True,'modelos_e_politicas_preservados':True,'promove_entrega':False});return resumo


def math_ceil(n,d):return (n+d-1)//d


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,default=Path('experimentos/semantica_v22_001'));p.add_argument('--questoes',type=Path,default=Path('experimentos/semantica_v21_001/questoes_559_sem_rotulos.jsonl'));p.add_argument('--bloco',type=int,default=40);z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.bloco)
