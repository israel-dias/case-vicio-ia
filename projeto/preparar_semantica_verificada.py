"""Preparação E5 com verificação dos pesos antes de carregar o encoder."""
import argparse,hashlib
from pathlib import Path
from baixar_encoder_v21 import ARQUIVOS


def verificar_modelo(pasta):
    for nome,(_,esperado) in ARQUIVOS.items():
        p=Path(pasta)/nome
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=esperado:
            raise ValueError('Pesos ou tokenizer diferentes da revisão fixada: '+nome)


def executar(projeto,modelo,saida):
    verificar_modelo(modelo)
    from preparar_semantica_v21 import executar as preparar
    return preparar(projeto,modelo,saida)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--modelo',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.modelo,z.saida)
