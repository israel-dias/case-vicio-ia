"""Cria registro de integridade para uma execução completa, sem retreinar."""
import argparse
import json
from pathlib import Path
from compatibilidade_v2.runtime import sha


def executar(projeto,experimento):
    projeto,experimento=Path(projeto).resolve(),Path(experimento).resolve()
    p=experimento/'manifesto_inferencia.json'
    if p.exists():raise ValueError('Manifesto já existe; preserve o congelamento anterior.')
    protocolo=json.loads((experimento/'protocolo_previo.json').read_text())
    for n,h in protocolo['codigo_sha256'].items():
        if sha(projeto/n)!=h:raise ValueError('Código alterado desde a avaliação: '+n)
    reg={'versao':'atributos_v11_1','codigo_sha256':{n:sha(projeto/n) for n in [
        'experimento_atributos_v11/modelo.py','classificar_atributos_v11.py','experimento_relacoes_v9/regras.py']},
        'artefatos_sha256':{n:sha(experimento/n) for n in ['modelos_finais.json','estatistica_identificador.json']},
        'promove_entrega':False}
    p.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');print(p)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.experimento)
