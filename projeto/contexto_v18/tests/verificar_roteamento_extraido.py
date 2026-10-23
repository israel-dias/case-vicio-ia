"""Recalcula e confere as duas composições inteiras com rede/rótulos bloqueados."""
import argparse,csv,json,socket,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from contexto_v18 import modelo as m
from contexto_v18.roteamento import POLITICAS,compor
import rotear_comando_extraido_v18 as rt


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();ex=projeto/'experimentos/roteamento_extraido_v18_001'
    anteriores=list(csv.DictReader((ex/'classificacoes_559_todas_politicas.csv').open()))
    capturado={};abrir=Path.open;fb=rt.executar_base;fn=rt.executar_nova
    def protegido(path,*args,**kw):
        if path.name=='folha_verdade.csv':raise AssertionError('rótulos')
        return abrir(path,*args,**kw)
    def base(*a,**kw):
        r=fb(*a,**kw);capturado['base']=r;return r
    def nova(*a,**kw):
        r=fn(*a,**kw);capturado['nova']=r;return r
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')), \
         patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')), \
         patch.object(m,'ajustar',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')), \
         patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('fit supervisionado')),patch.object(rt,'executar_base',side_effect=base),patch.object(rt,'executar_nova',side_effect=nova):
        selecionada=rt.executar(projeto,projeto/'experimentos/comando_extraido_v18_001/questoes_559_sem_rotulos.jsonl',saida)
        provas={}
        for p in POLITICAS:
            rr=compor(capturado['nova'],capturado['base'],p);ant={r['id']:r for r in anteriores if r['composicao']==p}
            if len(rr)!=559 or {r['id'] for r in rr}!=set(ant):raise AssertionError('IDs diferentes')
            for r in rr:
                for k in ['tema_central_id','decisao']:
                    if r[k]!=ant[r['id']][k]:raise AssertionError((p,r['id'],k))
                if r['confianca']!=float(ant[r['id']]['confianca']):raise AssertionError('Confiança diferente')
            provas[p]={'reproducao_exata':True,'publicar':sum(r['decisao']=='publicar' for r in rr)}
    reg={'politicas':provas,'previsoes_conferidas':1118,'rede_rotulos_avaliador_treino_recalibracao_bloqueados':True,'precisao_real_559':None}
    (ex/'reproducao_verificada.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(reg,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
