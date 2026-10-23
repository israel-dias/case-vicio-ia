import argparse
from pathlib import Path
from vocabulario_v8.ranking import executar

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Avalia vocabulário só na busca, com nova calibração.')
    p.add_argument('--projeto',type=Path,default=Path('.'))
    p.add_argument('--saida',type=Path,required=True)
    a=p.parse_args();executar(a.projeto,a.saida)
