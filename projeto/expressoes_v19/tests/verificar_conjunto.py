"""Reprodução de quatro estratégias e três guardas sem rótulos ou rede."""
import csv,json,socket,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from expressoes_v19 import modelo as m
from expressoes_v19.guarda import combinar
from classificar_guardas_v19 import executar


def verificar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/expressoes_v19_001';g=projeto/'experimentos/guardas_v19_001'
    antigos=list(csv.DictReader((e/'classificacoes_559_todas_variantes.csv').open()));ga=list(csv.DictReader((g/'classificacoes_559_todas_variantes.csv').open()))
    packs=json.loads((e/'modelos_finais.json').read_text())['modelos'];abrir=Path.open;preparar=m.preparar;capturado={}
    def proteger(path,*a,**kw):
        if path.name=='folha_verdade.csv':raise AssertionError('rótulos')
        return abrir(path,*a,**kw)
    def uma_vez(cat,dic,qs):
        if capturado:raise AssertionError('Preparação duplicada')
        ps=preparar(cat,dic,qs);capturado.update(cat=cat,ps=ps);return ps
    def conferir(rr,ant,campos):
        if len(rr)!=559 or {r['id'] for r in rr}!=set(ant):raise AssertionError('Universo divergente')
        for r in rr:
            a=ant[r['id']]
            for k in campos:
                if str(r[k])!=a[k]:raise AssertionError((r['id'],k,str(r[k]),a[k]))
            if r['confianca']!=float(a['confianca']):raise AssertionError((r['id'],'confianca'))
    with patch.object(Path,'open',proteger),patch.object(socket,'socket',side_effect=AssertionError('rede')), \
         patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')), \
         patch.object(m,'ajustar',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')), \
         patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('fit')),patch.object(m,'preparar',side_effect=uma_vez):
        publicas=executar(projeto,g,e/'questoes_559_sem_rotulos.jsonl',saida,'vocabulario_escopos');resultados={};provas={}
        for v in m.VARIANTES:
            rr=m.aplicar(capturado['ps'][v],packs[v],capturado['cat'],v);resultados[v]=rr
            conferir(rr,{r['id']:r for r in antigos if r['variante']==v},['tema_central_id','decisao','motivo','top5_ids','candidatos_ids'])
            provas[v]={'questoes':len(rr),'publicar':sum(r['decisao']=='publicar' for r in rr),'reproducao_exata':True}
        for v in ['frases_completas','vocabulario_escopos','passagem_cobrada']:
            rr=publicas if v=='vocabulario_escopos' else combinar(resultados['controle_atual'],resultados[v],capturado['cat'].temas)
            conferir(rr,{r['id']:r for r in ga if r['variante']==v},['tema_central_id','decisao','motivo','guarda_disciplina_acionada'])
            provas['guarda_'+v]={'questoes':len(rr),'publicar':sum(r['decisao']=='publicar' for r in rr),'reproducao_exata':True}
    r={'variantes':provas,'previsoes_conferidas':559*len(provas),'rotulos_rede_treino_avaliador_recalibracao_bloqueados':True,'confianca_global_das_guardas_recalibrada':False,'precisao_real_559':None,'promove_entrega':False,'entrada_sha256':sha(e/'questoes_559_sem_rotulos.jsonl')}
    (g/'reproducao_conjunto_verificada.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();verificar(z.projeto,z.saida)
