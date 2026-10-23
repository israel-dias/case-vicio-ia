import argparse
from pathlib import Path
from vocabulario_v8.experimento import executar

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Testa expressões temáticas sem substituir a entrega.')
    p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args();executar(args.projeto,args.saida)
