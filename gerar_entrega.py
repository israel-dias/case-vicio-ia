"""Regenera a entrega oficial a partir dos anexos, sem LLM, rede ou rótulos."""
import argparse,csv,json,math,shutil,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'projeto'))
from verificar_inferencia_v24 import verificar
from compatibilidade_v2 import features as f


def validar(linhas,temas):
    ids=set()
    for r in linhas:
        if not r['id'] or r['id'] in ids:raise ValueError('ID vazio ou duplicado.')
        ids.add(r['id']);d=r['decisao'];t=r['tema_central_id']
        if d not in {'publicar','revisar','fora'}:raise ValueError('Decisão inválida.')
        if d=='fora' and t or d!='fora' and not f.elegivel(t,temas):raise ValueError('Tema central inválido.')
        if d in {'revisar','fora'} and not r['motivo'].strip():raise ValueError('Motivo ausente.')
        p=float(r['confianca'])
        if not math.isfinite(p) or not 0<=p<=1:raise ValueError('Confiança inválida.')
        for extra in filter(None,r['extras_ids'].split(';')):
            if not f.elegivel(extra,temas):raise ValueError('Extra inválido.')
    if len(ids)!=659:raise ValueError('Entrega exige 659 IDs únicos.')


def exportar(motor,saida):
    motor,saida=Path(motor),Path(saida)
    if (saida/'publicacao.csv').exists():raise ValueError('Saída final já existe.')
    linhas=list(csv.DictReader((motor/'publicacao.csv').open(encoding='utf-8')))
    with (ROOT/'projeto/dados/anexos/temas.csv').open(encoding='utf-8-sig') as arq:
        temas={r['tema_id']:{**r,'nivel':int(r['nivel']),'ativo':r['status'].lower() in {'active','ativo','1'}} for r in csv.DictReader(arq)}
    validar(linhas,temas);saida.mkdir(parents=True,exist_ok=True)
    rastros={r['id']:r for r in map(json.loads,(motor/'inferencia/rastreabilidade.jsonl').read_text().splitlines())}
    for r in linhas:
        if r['decisao']!='revisar':continue
        tr=rastros[r['id']]
        if tr.get('veto_contexto'):r['motivo']='Tema aparece apenas no crime narrado, sem apoio na cobranca; confirmar o enquadramento.'
        elif tr.get('conflito_cobranca'):r['motivo']='Cobranca explicita diverge do enquadramento anterior; confirmar o ramo sugerido.'
        elif tr.get('homonimo_nao_resolvido') or 'homonimo' in r['motivo']:r['motivo']='Titulo homonimo em outro ramo; escopo ainda nao resolvido.'
        elif 'sem_evidencia' in str(tr.get('motivos_bloqueio','')):r['motivo']='Conteudo disponivel insuficiente para sustentar um topico com seguranca.'
        else:r['motivo']='Confirmar o enquadramento sugerido; evidencia insuficiente para publicacao automatica.'
    campos=['id','decisao','tema_central_id','extras_ids','confianca','motivo']
    with (saida/'publicacao.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=campos);w.writeheader()
        for r in linhas:w.writerow({**r,'confianca':f"{float(r['confianca']):.8f}"})
    for nome in ['previsao.txt','resumo_entrega.json','prova_inferencia_sem_modelo_linguagem.json']:
        shutil.copy2(motor/nome,saida/nome)
    shutil.copy2(motor/'inferencia/rastreabilidade.jsonl',saida/'rastreabilidade.jsonl')
    reg={'arquivos_sha256':{n:hashlib.sha256((saida/n).read_bytes()).hexdigest() for n in ['publicacao.csv','previsao.txt','resumo_entrega.json','rastreabilidade.jsonl']},'659_ids_unicos':True,'confianca_formatada_8_casas_sem_alterar_decisao':True}
    (saida/'validacao_entrega.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(json.loads((saida/'resumo_entrega.json').read_text()),ensure_ascii=False,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',type=Path,required=True);z=p.parse_args();saida=z.saida.resolve()
    if (saida/'publicacao.csv').exists():raise ValueError('Use pasta de saída nova.')
    verificar(ROOT/'projeto',saida/'motor');exportar(saida/'motor',saida)


if __name__=='__main__':main()
