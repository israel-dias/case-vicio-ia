"""Só preserva a calibração após verificar igualdade de escolhas nas 100 referências."""
import csv,json,argparse
from pathlib import Path
from compatibilidade_v2.runtime import sha
from testar_isolamento_v17 import gravar,csv_salvar,dependencias

def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/contexto_v20_001'
    if saida.exists():raise ValueError('Use saída nova.')
    rr=list(csv.DictReader((e/'avaliacao_100.csv').open()));base={r['id']:r for r in rr if r['avaliacao']=='controle_atual'};ctx={r['id']:r for r in rr if r['avaliacao']=='escopos_contextuais'}
    if len(base)!=100 or set(base)!=set(ctx) or any(base[i]['tema_central_id']!=ctx[i]['tema_central_id'] for i in base):raise ValueError('Escolhas diferentes: não reutilize a calibração sem nova avaliação.')
    saida.mkdir(parents=True)
    modelo=json.loads((e/'modelos_finais.json').read_text())['modelos']['controle_atual'];gravar(saida/'modelo_preservado.json',modelo)
    gravar(saida/'protocolo_previo.json',{'adaptativo':True,'motivo':'Efeito da representação isolado dos novos atributos de confiança. Escolhas iguais nas 100; mesmas 27 dimensões de entrada do controle.','escolhas_iguais_nas_100':True,'estimador_e_calibrador_preservados':True,'treino_adicional':False,'usa_rotulos_559':False,'promove_entrega':False,'limite':'Igualdade em referências expostas não garante transferência para dados novos; não comprova meta de 95%.'})
    csv_salvar(saida/'avaliacao_100_herdada.csv',[{**r,'variante':'escopos_contextuais_estimador_preservado','confianca_herdada_do_controle':True} for r in base.values()])
    deps=dependencias(projeto);gravar(saida/'manifesto_inferencia.json',{'versao':'contexto_preservado_v20_1','codigo_sha256':deps,'artefatos_sha256':{n:sha(saida/n) for n in ['modelo_preservado.json','protocolo_previo.json']},'promove_entrega':False})
    print(json.dumps({'escolhas_iguais':len(base),'treino_adicional':False,'promove_entrega':False}));return modelo

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
