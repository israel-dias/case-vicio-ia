import csv,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[2]
qs=[json.loads(s) for s in (p/'dados/processados/questoes_preparadas.jsonl').read_text().splitlines()]
ant={r['id']:r for r in csv.DictReader((p/'historico/v3/publicacao.csv').open())}
for q in qs[int(sys.argv[1])-1:int(sys.argv[2])]:
 print('\n'+q['id']+' | ANTES '+ant[q['id']]['decisao']+' '+ant[q['id']]['tema_central_id']+' EXTRAS '+ant[q['id']]['extras_ids'])
 print(q['enunciado'])
 if q['comando'] and q['comando'] not in q['enunciado']:print('COMANDO:',q['comando'])
 for k,v in q['alternativas'].items():print(k+': '+v)
 if q['alertas_preparacao']:print('ALERTAS',q['alertas_preparacao'])
