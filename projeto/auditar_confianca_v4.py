"""Compara a retirada de sinais suspeitos sem modificar a entrega v3."""
import argparse
from pathlib import Path
from auditoria_confianca_v4.experimento import executar
from compatibilidade_v2 import features as f

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path(__file__).parent)
    p.add_argument('--saida',type=Path,required=True)
    args = p.parse_args()
    with f.threadpool_limits(limits=2):
        executar(args.projeto,args.saida)
