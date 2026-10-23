"""Classifica qualquer JSONL compatível, sem rótulos, rede ou chamada a LLM."""
import argparse
import json
from pathlib import Path
from flexivel_v5.runtime import executar

if __name__=='__main__':
    root=Path(__file__).parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',type=Path,default=root/'artefatos/flexivel_v5')
    p.add_argument('--questoes',type=Path,required=True)
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args();print(json.dumps(executar(args.modelo,args.questoes,args.saida),ensure_ascii=False,indent=2))
