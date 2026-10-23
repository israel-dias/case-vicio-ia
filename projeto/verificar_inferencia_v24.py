"""Executa entrega completa com rede, rótulos, treino e encoder bloqueados."""
import argparse,builtins,json,socket,sys
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from cobranca_v24 import modelo as m
from finalizar_cobranca_v24 import executar


def verificar(projeto,saida):
    abrir=Path.open;importar=builtins.__import__
    def protegido(p,*a,**kw):
        if p.name=='folha_verdade.csv':raise AssertionError('Folha-verdade não pode ser lida na inferência.')
        return abrir(p,*a,**kw)
    def sem_encoder(nome,*a,**kw):
        if nome.split('.')[0] in {'torch','transformers','sentence_transformers','fastembed','onnxruntime','tokenizers'}:raise AssertionError('Encoder não pode participar da decisão.')
        return importar(nome,*a,**kw)
    with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')),patch.object(f,'carregar',side_effect=AssertionError('leitura de rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')),patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')),patch.object(builtins,'__import__',sem_encoder):
        resumo=executar(projeto,saida)
    reg={'questoes':resumo['total']['questoes'],'alvo':resumo['fora_folha_verdade']['questoes'],'rótulos_rede_treino_avaliador_recalibracao_encoder_bloqueados':True,'modelo_llm_chamadas':0,'meta_95_real_comprovada':False}
    (Path(saida)/'prova_inferencia_sem_modelo_linguagem.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();verificar(z.projeto,z.saida)
