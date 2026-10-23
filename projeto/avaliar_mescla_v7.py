import argparse
from pathlib import Path
from mescla_marcadores_v7.experimento import executar

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Testa enunciado zero e marcadores condicionais sem alterar a entrega.')
    p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args()
    executar(args.projeto,args.saida)
