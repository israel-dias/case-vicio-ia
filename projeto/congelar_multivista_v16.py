"""Congela os modelos e dependências da inferência V16."""
import argparse,json
from pathlib import Path
from compatibilidade_v2.runtime import sha
def executar(projeto,experimento):
    projeto,experimento=Path(projeto).resolve(),Path(experimento).resolve();dest=experimento/'manifesto_inferencia.json'
    if dest.exists():raise ValueError('Manifesto já existe.')
    prot=json.loads((experimento/'protocolo_previo.json').read_text())
    for n,h in prot['codigo_sha256'].items():
        if sha(projeto/n)!=h:raise ValueError('Código diferente da avaliação: '+n)
    arquivos=[p for p in projeto.rglob('*.py') if '__pycache__' not in p.parts and 'tests' not in p.parts and 'testes_diagnostico_559' not in p.parts]
    arquivos += [p for p in (projeto/'artefatos').rglob('*') if p.is_file()]
    arquivos += [projeto/'vocabulario_v8/dicionario.json',projeto/'melhorias_v3/dados/referencias_normativas_v1.json',projeto/'experimentos/palavra_v12_001/modelos_finais.json']
    obj={'versao':'multivista_v16_1','projeto_sha256':{str(p.relative_to(projeto)):sha(p) for p in sorted(set(arquivos))},
         'experimento_sha256':{n:sha(experimento/n) for n in ['modelos_finais.json','catalogo_preparado.json']},'promove_entrega':False}
    dest.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');print(dest)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.experimento)
