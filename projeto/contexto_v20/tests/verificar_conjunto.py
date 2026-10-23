"""Compara quatro variantes e gera a vista de confiança preservada offline."""
import csv,json,socket,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from contexto_v20 import modelo as m
from classificar_contexto_preservado_v20 import executar
from isolamento_v17.metricas import medir


def verificar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/contexto_v20_001';g=projeto/'experimentos/contexto_preservado_v20_001'
    anteriores=list(csv.DictReader((e/'classificacoes_559_todas_variantes.csv').open()));packs=json.loads((e/'modelos_finais.json').read_text())['modelos']
    abrir=Path.open;preparar=m.preparar;capturado={}
    def protegido(path,*a,**kw):
        if path.name=='folha_verdade.csv':raise AssertionError('rótulos')
        return abrir(path,*a,**kw)
    def uma_vez(cat,dic,qs):
        if capturado:raise AssertionError('preparação repetida')
        ps=preparar(cat,dic,qs);capturado.update(cat=cat,ps=ps);return ps
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')), \
         patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')), \
         patch.object(m,'ajustar',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')), \
         patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('fit')),patch.object(m,'preparar',side_effect=uma_vez):
        preservadas=executar(projeto,g,e/'questoes_559_sem_rotulos.jsonl',saida);provas={};preds={}
        for v in m.VARIANTES:
            rr=m.aplicar(capturado['ps'][v],packs[v],capturado['cat'],v);preds[v]=rr;ant={r['id']:r for r in anteriores if r['variante']==v}
            if len(rr)!=559 or {r['id'] for r in rr}!=set(ant):raise AssertionError('IDs divergentes')
            for r in rr:
                for k in ['tema_central_id','decisao','motivo','top5_ids','candidatos_ids']:
                    if r[k]!=ant[r['id']][k]:raise AssertionError((v,r['id'],k))
                if r['confianca']!=float(ant[r['id']]['confianca']):raise AssertionError((v,r['id'],'confianca'))
            provas[v]={'questoes':len(rr),'reproducao_exata':True}
        base={r['id']:r for r in preds['controle_atual']}
        # Quando o novo ranking mantém o candidato, o estimador de 27
        # dimensões deve produzir a mesma confiança e decisão do controle.
        mesmos=0
        for r in preservadas:
            if r['tema_central_id']==base[r['id']]['tema_central_id']:
                b=base[r['id']]
                if r['confianca']!=b['confianca'] or r['decisao']!=b['decisao']:raise AssertionError('Confiança mudou sem trocar o candidato.')
                mesmos+=1
    resumo=medir(preservadas,list(base.values()))
    resumo['recentes_300']=medir([r for r in preservadas if int(r['id'][1:])>=360]);resumo['controle_com_mesmo_candidato']=mesmos
    (g/'resumo_559.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    # Cópia da inferência efetiva, não tabela de respostas consultada em runtime.
    import shutil
    shutil.copy2(saida/'classificacoes_experimentais.csv',g/'classificacoes_559.csv')
    reg={'variantes':provas,'previsoes_reproduzidas':559*len(provas),'inferencias_adicionais_estimador_preservado':len(preservadas),
         'mesmo_candidato_implica_mesma_confianca_verificado':mesmos,'rotulos_rede_treino_avaliador_recalibracao_bloqueados':True,'precisao_real_559':None,'promove_entrega':False}
    (g/'verificacao_conjunto.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');print(json.dumps(reg,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();verificar(z.projeto,z.saida)
