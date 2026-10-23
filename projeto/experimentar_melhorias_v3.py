"""Executa o experimento v3, preservando o controle e os anexos."""
import argparse
from pathlib import Path
from compatibilidade_v2 import features as f
from melhorias_v3.experimento import executar

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path(__file__).parent)
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args()
    with f.threadpool_limits(limits=2): executar(args.projeto,args.saida)
