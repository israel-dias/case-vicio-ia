"""Obtém pesos públicos E5 numa revisão fixa; não classifica questões."""
import argparse,hashlib,json,urllib.request
from pathlib import Path

REPO='intfloat/multilingual-e5-small'
REVISAO='614241f622f53c4eeff9890bdc4f31cfecc418b3'
ARQUIVOS={
    'modelo.onnx':('onnx/model_qint8_avx512_vnni.onnx','dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88'),
    'tokenizer.json':('tokenizer.json','0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39'),
    'config.json':('config.json','69137736cab8b8903a07fe8afaafdda25aac55415a12a55d1bffa9f581abf959')}


def executar(saida):
    saida=Path(saida);saida.mkdir(parents=True,exist_ok=True)
    for nome,(remoto,esperado) in ARQUIVOS.items():
        p=saida/nome
        if not p.exists():
            tmp=p.with_suffix('.parcial')
            try:
                with urllib.request.urlopen(f'https://huggingface.co/{REPO}/resolve/{REVISAO}/{remoto}?download=true',timeout=120) as r,tmp.open('wb') as o:
                    while b:=r.read(1024*1024):o.write(b)
                if hashlib.sha256(tmp.read_bytes()).hexdigest()!=esperado:raise ValueError('Download com hash diferente: '+nome)
                tmp.replace(p)
            finally:tmp.unlink(missing_ok=True)
        if hashlib.sha256(p.read_bytes()).hexdigest()!=esperado:raise ValueError('Arquivo local diferente: '+nome)
        print(nome,p.stat().st_size,'bytes; hash verificado.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.saida)
