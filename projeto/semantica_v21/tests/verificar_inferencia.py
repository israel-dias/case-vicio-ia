"""Reproduz as seis variantes V21 nos 559 com rede/rótulos/encoder bloqueados."""
import csv,json,socket,sys,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from compatibilidade_v2 import features as f
from semantica_v21 import modelo as m
from classificar_semantica_v21 import executar


def verificar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/semantica_v21_001';capturado={};preparar=m.Busca.preparar;t=time.perf_counter()
    orig=list(csv.DictReader((e/'classificacoes_559_todas_variantes.csv').open()));packs=json.loads((e/'modelos_finais.json').read_text())['modelos'];abrir=Path.open
    def protegido(p,*a,**kw):
        if p.name=='folha_verdade.csv':raise AssertionError('rótulos')
        return abrir(p,*a,**kw)
    def salvar(self,qs):
        pp=preparar(self,qs);capturado.update(pp=pp,cat=self.cat);return pp
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')),patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')),patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')),patch.object(m.Busca,'preparar',salvar):
        executar(projeto,e,e/'questoes_559_sem_rotulos.jsonl',saida);provas={}
        for v in m.VARIANTES:
            rr=m.aplicar(capturado['pp'],packs[v],capturado['cat'],v);esperados={r['id']:r for r in orig if r['variante']==v}
            if {r['id'] for r in rr}!=set(esperados):raise AssertionError('IDs divergentes')
            for r in rr:
                b=esperados[r['id']]
                for k in ['tema_central_id','decisao','motivo','top5_ids']:
                    if r[k]!=b[k]:raise AssertionError((v,r['id'],k))
                if r['confianca']!=float(b['confianca']):raise AssertionError('Confiança diferente.')
            provas[v]=len(rr)
    if 'onnxruntime' in sys.modules or 'tokenizers' in sys.modules:raise AssertionError('Encoder importado.')
    reg={'variantes':provas,'previsoes_reproduzidas':sum(provas.values()),'reproducao_exata':True,'rotulos_rede_treino_avaliador_recalibracao_encoder_ausentes':True,'segundos':time.perf_counter()-t}
    (e/'reproducao_verificada.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');print(json.dumps(reg,ensure_ascii=False,indent=2))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();verificar(z.projeto,z.saida)
