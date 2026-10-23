"""Verificação rápida do formato e dos hashes da entrega salva."""
import csv,hashlib,json
from pathlib import Path
from gerar_entrega import ROOT,validar

def main():
    reg=json.loads((ROOT/'validacao_entrega.json').read_text())
    for nome,h in reg['arquivos_sha256'].items():
        if hashlib.sha256((ROOT/nome).read_bytes()).hexdigest()!=h:raise ValueError('Arquivo alterado: '+nome)
    with (ROOT/'projeto/dados/anexos/temas.csv').open(encoding='utf-8-sig') as arq:
        temas={r['tema_id']:{**r,'nivel':int(r['nivel']),'ativo':r['status'].lower() in {'active','ativo','1'}} for r in csv.DictReader(arq)}
    rows=list(csv.DictReader((ROOT/'publicacao.csv').open()));validar(rows,temas)
    s=json.loads((ROOT/'resumo_entrega.json').read_text())
    print(json.dumps({'formato':'OK','hashes':'OK','questoes':len(rows),'avaliadas':s['fora_folha_verdade'],'recentes':s['recentes_300'],'precisao_real_559':None},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
