"""Prova do runtime V22/V23 numa amostra determinística dos 559 sem rótulos."""
import argparse,builtins,csv,json,socket,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from semantica_v22 import modelo as base,qualidade as m
from classificar_qualidade_v23 import executar


def verificar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/qualidade_v23_002';b=projeto/'experimentos/semantica_v22_001'
    qs=[json.loads(l) for l in (b/'questoes_559_sem_rotulos.jsonl').read_text().splitlines()];amostra=qs[::35]
    entrada=e/'amostra_sem_rotulos.jsonl';entrada.write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in amostra))
    packs=json.loads((b/'modelos_finais.json').read_text())['modelos'];esperados=list(csv.DictReader((b/'classificacoes_559_todas_variantes.csv').open()));eq=list(csv.DictReader((e/'classificacoes_559_todas_variantes.csv').open()))
    preparar=base.preparar;capt={};abrir=Path.open;imp=builtins.__import__
    def coleta(proj,cat,dic,qs):
        pp=preparar(proj,cat,dic,qs);capt.update(cat=cat,pp=pp);return pp
    def protegido(p,*a,**kw):
        if p.name=='folha_verdade.csv':raise AssertionError('rótulos')
        return abrir(p,*a,**kw)
    def sem_encoder(nome,*a,**kw):
        if nome.split('.')[0] in {'onnxruntime','tokenizers','fastembed','sentence_transformers','transformers','torch'}:raise AssertionError('encoder')
        return imp(nome,*a,**kw)
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')),patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')),patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('treino')),patch.object(base.a,'calibrar',side_effect=AssertionError('recalibração')),patch.object(base,'preparar',coleta),patch.object(builtins,'__import__',sem_encoder):
        rr=executar(projeto,e,entrada,saida);n=0
        def comparar(rr,ant):
            for r in rr:
                a=ant[r['id']]
                for k in ['tema_central_id','decisao','motivo']:
                    if r[k]!=a[k]:raise AssertionError((r['id'],k))
                if r['confianca']!=float(a['confianca']):raise AssertionError((r['id'],'confianca'))
        escolhido=json.loads((e/'modelos_finais.json').read_text())['selecionado'];comparar(rr,{r['id']:r for r in eq if r['variante']=='qualidade_direta_'+escolhido});n+=len(rr)
        for v in base.VARIANTES:
            vr=base.aplicar(capt['pp'][v],packs[v],capt['cat'],v);comparar(vr,{r['id']:r for r in esperados if r['variante']==v});n+=len(vr)
    reg={'amostra':len(amostra),'ids':[q['id'] for q in amostra],'previsoes_conferidas':n,'v22_variantes':len(base.VARIANTES),'v23_variante':escolhido,'reproducao_exata':True,'rotulos_rede_treino_avaliador_recalibracao_encoder_bloqueados':True,'escopo':'Amostra determinística, não conferência de todas as 559 nem avaliação de acerto jurídico.'}
    (e/'reproducao_amostral_verificada.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');print(json.dumps(reg,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();verificar(z.projeto,z.saida)
