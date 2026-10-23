"""Gera a entrega da candidata sem formato e compara com a v3 preservada."""
import argparse
import csv
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING
import json
from pathlib import Path

from compatibilidade_v2 import runtime as base
from flexivel_v5 import runtime as rt


def contar(rows):
    return {'questoes':len(rows),'decisoes':{d:sum(r['decisao']==d for r in rows) for d in ['publicar','revisar','fora']},
            'cobertura':sum(r['decisao']=='publicar' for r in rows)/len(rows)}


def arredondar(x,superior=False):
    return str(Decimal(str(x)).quantize(Decimal('.00000001'),rounding=ROUND_CEILING if superior else ROUND_FLOOR))


def executar(projeto,modelo,saida):
    projeto,modelo,saida=Path(projeto).resolve(),Path(modelo).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Saída existente; use outra pasta.')
    m=json.loads((modelo/'modelo.json').read_text());dados=projeto/'dados/anexos'
    for nome,h in m['anexos_sha256'].items():
        if base.sha(dados/nome)!=h:raise ValueError('Anexos diferentes do experimento.')
    rt.executar(modelo,dados/'questoes.jsonl',saida)
    rows=list(csv.DictReader((saida/'publicacao.csv').open(encoding='utf-8',newline='')))
    # Os IDs da folha só excluem registros do denominador da avaliação.
    oficiais={r['id'] for r in csv.DictReader((dados/'folha_verdade.csv').open(encoding='utf-8-sig'))}
    alvo=[r for r in rows if r['id'] not in oficiais]
    recentes=[r for r in alvo if int(r['id'][1:])>=360]
    pubs=[r for r in alvo if r['decisao']=='publicar']
    pp=sum(float(r['confianca']) for r in pubs)/len(pubs) if pubs else None
    cv=m['resultado_cv'];intervalo=base.cal.intervalo_exato(cv['acertos_publicadas'],cv['publicar'])
    faixa=[min(intervalo[0],pp),max(intervalo[1],pp)] if pp is not None else [0.,1.]
    cobertura=len(pubs)/len(alvo)
    anterior={r['id']:r for r in csv.DictReader((projeto/'entrega_experimental_v3/publicacao.csv').open())}
    transicoes={}
    for r in alvo:
        key=anterior[r['id']]['decisao']+' -> '+r['decisao'];transicoes[key]=transicoes.get(key,0)+1
    comp={'v3':contar([r for r in anterior.values() if r['id'] not in oficiais]),'v5':contar(alvo),
        'transicoes_559':transicoes,'mudancas_tema':sum(r['tema_central_id']!=anterior[r['id']]['tema_central_id'] for r in alvo),
        'nota':'Mudança na seleção de publicação; não constitui medição de acerto nas 559.'}
    resumo={'versao':rt.VERSAO,'variante':'sem_formato','total':contar(rows),'fora_folha_verdade':contar(alvo),
        'recentes_300':contar(recentes),'precisao_prevista':pp,'precisao_faixa_sensibilidade':faixa,
        'precisao_real_559':None,'meta_95_nas_559_comprovada':False,'resultado_cv_100_conhecidos':cv,
        'comparacao_com_v3':comp,'atributos_retirados':list(rt.RETIRADOS)}
    base.escrever(saida/'resumo_entrega.json',resumo);base.escrever(saida/'comparacao_com_v3.json',comp)
    texto=[f'precisao_prevista: {pp:.8f}' if pp is not None else 'precisao_prevista: indefinida',
        f'precisao_intervalo: {arredondar(faixa[0])}-{arredondar(faixa[1],True)}',
        f'cobertura_prevista: {cobertura:.8f}',
        f'cobertura_intervalo: {arredondar(cobertura)}-{arredondar(cobertura,True)}','',
        'Versão v5 sem três atributos de formato. O primeiro tema da busca foi preservado; a política e as probabilidades vieram do experimento documentado.',
        'Precisão prevista: média das probabilidades congeladas das publicadas fora da folha-verdade. Ela não foi elevada à mão para coincidir com a meta de 95%.',
        f"Na comparação por grupos nos 100 rótulos conhecidos, a candidata publicou {cv['publicar']} e acertou {cv['acertos_publicadas']}. Esse é um resultado de desenvolvimento reutilizado, não um teste externo novo.",
        'A faixa de precisão usa o intervalo binomial descritivo dessa comparação, ampliado se necessário para conter a previsão. Não é um intervalo de confiança válido para a precisão das 559: não corrige dependência entre grupos, seleção de variantes, exposição prévia ou mudança de distribuição.',
        'A cobertura é a fração conhecida deste lote de 559; seu intervalo cobre apenas o arredondamento. Não é previsão de novas importações.',
        'Precisão real das 559 e atendimento à meta de 95% ainda não medidos. Nenhum LLM resolveu ou classificou essas questões nesta versão.','']
    (saida/'previsao.txt').write_text('\n'.join(texto),encoding='utf-8')
    with (saida/'fila_revisao.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=base.legado.CAMPOS_ENTREGA);w.writeheader();w.writerows(r for r in alvo if r['decisao']=='revisar')
    base.escrever(saida/'manifesto_entrega.json',{'modelo_sha256':base.sha(modelo/'modelo.json'),
        'arquivos_sha256':{p.name:base.sha(p) for p in sorted(saida.iterdir()) if p.is_file() and p.name!='manifesto_entrega.json'}})
    print(json.dumps(resumo,ensure_ascii=False,indent=2));return resumo


if __name__=='__main__':
    root=Path(__file__).parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=root)
    p.add_argument('--modelo',type=Path,default=root/'artefatos/flexivel_v5')
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args();executar(args.projeto,args.modelo,args.saida)
