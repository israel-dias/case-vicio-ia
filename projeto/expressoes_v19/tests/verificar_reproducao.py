"""Confere as três opções no alvo inteiro com leitura de rótulos bloqueada."""
import argparse,csv,json,socket,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from expressoes_v19 import modelo as m
from contexto_v18 import modelo as original
from classificar_expressoes_v19 import executar


def verificar(projeto,experimento,saida):
    projeto,experimento,saida=[Path(x).resolve() for x in [projeto,experimento,saida]]
    anteriores=list(csv.DictReader((experimento/'classificacoes_559_todas_variantes.csv').open()))
    packs=json.loads((experimento/'modelos_finais.json').read_text())
    abrir=Path.open;preparar=m.preparar;capturado={}
    def protegido(path,*args,**kw):
        if path.name=='folha_verdade.csv':raise AssertionError('Tentou ler rótulos')
        return abrir(path,*args,**kw)
    def preparar_uma_vez(cat,dic,qs):
        if capturado:raise AssertionError('Preparação repetida')
        ps=preparar(cat,dic,qs);capturado.update(cat=cat,ps=ps);return ps
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')), \
         patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')), \
         patch.object(m,'ajustar',side_effect=AssertionError('treino')),patch.object(original.a,'calibrar',side_effect=AssertionError('recalibração')), \
         patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('fit supervisionado')),patch.object(m,'preparar',side_effect=preparar_uma_vez):
        escolhidas=executar(projeto,experimento,experimento/'questoes_559_sem_rotulos.jsonl',saida)
        provas={}
        for v in m.VARIANTES:
            rr=escolhidas if v==packs['selecionado'] else m.aplicar(capturado['ps'][v],packs['modelos'][v],capturado['cat'],v)
            ant={r['id']:r for r in anteriores if r['variante']==v}
            if len(rr)!=559 or {r['id'] for r in rr}!=set(ant):raise AssertionError('Conjunto alvo diferente')
            for r in rr:
                a=ant[r['id']]
                for k in ['tema_central_id','decisao','motivo','top5_ids','candidatos_ids']:
                    if r[k]!=a[k]:raise AssertionError((v,r['id'],k))
                if r['confianca']!=float(a['confianca']):raise AssertionError((v,r['id'],'confianca'))
            provas[v]={'questoes':len(rr),'publicar':sum(r['decisao']=='publicar' for r in rr),'reproducao_exata':True}
    reg={'variantes':provas,'previsoes_conferidas':559*len(provas),'rede_rotulos_avaliador_treino_recalibracao_bloqueados':True,
         'selecionada_pelo_comando_publico':packs['selecionado'],'entrada_sha256':sha(experimento/'questoes_559_sem_rotulos.jsonl'),
         'csv_resultante_sha256':sha(saida/'classificacoes_experimentais.csv'),'precisao_real_559':None,'promove_entrega':False}
    (experimento/'reproducao_verificada.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(reg,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--experimento',type=Path,default=Path('experimentos/expressoes_v19_001'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();verificar(z.projeto,z.experimento,z.saida)
