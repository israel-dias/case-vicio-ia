import argparse
from pathlib import Path
from foco_referencial_v6.experimento import executar

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Testa foco gramatical sem alterar a entrega anterior.')
    parser.add_argument('--projeto',type=Path,default=Path('.'))
    parser.add_argument('--saida',type=Path,required=True)
    args=parser.parse_args()
    executar(args.projeto,args.saida)
