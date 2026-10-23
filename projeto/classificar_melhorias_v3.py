"""Classifica um JSONL usando apenas os artefatos congelados da v3."""
import argparse
import json
from pathlib import Path
from melhorias_v3.runtime import executar

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',type=Path,default=Path('artefatos/melhorias_v3'))
    p.add_argument('--questoes',type=Path,default=Path('dados/anexos/questoes.jsonl'))
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(executar(args.modelo,args.questoes,args.saida),ensure_ascii=False,indent=2))
