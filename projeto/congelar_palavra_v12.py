"""Congela resultados/artefatos V12 para inferência independente dos rótulos."""
import argparse
import json
from pathlib import Path
from compatibilidade_v2.runtime import sha

def executar(projeto,experimento):
    projeto,experimento=Path(projeto).resolve(),Path(experimento).resolve()
    destino=experimento/'manifesto_inferencia.json'
    if destino.exists(): raise ValueError('Manifesto já existe.')
    protocolo=json.loads((experimento/'protocolo_previo.json').read_text())
    for n,h in protocolo['codigo_sha256'].items():
        if sha(projeto/n)!=h: raise ValueError('Código diferente da avaliação: '+n)
    arquivos=[p for p in projeto.rglob('*.py') if '__pycache__' not in p.parts and 'tests' not in p.parts]
    arquivos += [p for p in (projeto/'artefatos').rglob('*') if p.is_file()]
    arquivos += [projeto/'vocabulario_v8/dicionario.json',projeto/'melhorias_v3/dados/referencias_normativas_v1.json']
    registro={'versao':'palavra_v12_1','projeto_sha256':{str(p.relative_to(projeto)):sha(p) for p in sorted(set(arquivos))},
        'experimento_sha256':{'modelos_finais.json':sha(experimento/'modelos_finais.json')},
        'folha_verdade_na_inferencia':False,'corte_50_testado':False,'promove_entrega':False}
    destino.write_text(json.dumps(registro,ensure_ascii=False,indent=2)+'\n');print(destino)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.experimento)
