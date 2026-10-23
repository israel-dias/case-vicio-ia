"""Reproduz a candidata v3 congelada e documenta sua comparação com a v2."""
import argparse
import csv
import json
from pathlib import Path
import shutil

from compatibilidade_v2 import runtime as base
from melhorias_v3 import runtime as rt


def contar(rows):
    return {'questoes':len(rows),'decisoes':{d:sum(r['decisao']==d for r in rows) for d in ['publicar','revisar','fora']},
            'cobertura':sum(r['decisao']=='publicar' for r in rows)/len(rows)}


def executar(projeto,modelo,saida):
    if saida.exists():raise ValueError('Saída existente: escolha outra pasta.')
    m=json.loads((modelo/'modelo.json').read_text())
    dados=projeto/'dados/anexos'
    for nome,h in m['anexos_sha256'].items():
        if base.sha(dados/nome)!=h:raise ValueError('Anexos diferentes do experimento.')
    rt.executar(modelo,dados/'questoes.jsonl',saida)
    with (saida/'publicacao.csv').open(encoding='utf-8',newline='') as arq:rows=list(csv.DictReader(arq))
    with (dados/'folha_verdade.csv').open(encoding='utf-8-sig') as arq:oficiais={r['id'] for r in csv.DictReader(arq)}
    alvo=[r for r in rows if r['id'] not in oficiais]
    recentes=[r for r in alvo if int(r['id'][1:])>=360]
    publicadas=[r for r in alvo if r['decisao']=='publicar']
    pp=sum(float(r['confianca']) for r in publicadas)/len(publicadas) if publicadas else None
    faixa=[0.,1.]
    if publicadas:
        nomes=['controle_v2','selecionado_internamente',m['metodo_final']]
        intervalos=[]
        for n in nomes:
            v=m['resultado_cv']['metodos'][n]
            if v['publicar']:intervalos.append(base.cal.intervalo_exato(v['acertos_publicadas'],v['publicar']))
        if intervalos:faixa=[min(pp,*[v[0] for v in intervalos]),max(pp,*[v[1] for v in intervalos])]
    resumo={'metodo_final':m['metodo_final'],'total':contar(rows),'fora_folha_verdade':contar(alvo),'recentes_300':contar(recentes),
        'precisao_real_559':None,'precisao_prevista':pp,'precisao_faixa_sensibilidade':faixa,
        'meta_95_nas_559_comprovada':False,'resultado_cv':m['resultado_cv']['metodos'],
        'nota':'Faixa descritiva de sensibilidade baseada em CV de desenvolvimento, sem garantia para os 559 ou distribuição nova.'}
    base.escrever(saida/'resumo_entrega.json',resumo)
    cobertura=len(publicadas)/len(alvo)
    texto=[f"precisao_prevista: {pp:.8f}" if pp is not None else 'precisao_prevista: indefinida',
           f"precisao_intervalo: {faixa[0]:.8f}-{faixa[1]:.8f}",f'cobertura_prevista: {cobertura:.8f}',
           f'cobertura_intervalo: {cobertura:.8f}-{cobertura:.8f}','',
           'Candidata experimental v3. A precisão prevista é a média das probabilidades congeladas nas publicadas fora da folha-verdade. Não foi ajustada para atingir artificialmente 95%.',
           'O intervalo de precisão é uma faixa de sensibilidade descritiva de validação cruzada, não um intervalo de confiança válido para as 559 questões. Todos os rótulos de desenvolvimento já eram conhecidos.',
           'A cobertura é a fração calculada das decisões nesta população de 559, não uma previsão para semanas futuras.',
           'A seleção final e os cortes usaram somente sinais OOF dos 100 exemplos oficiais. Não houve uso dos 559 para escolher pesos, modelos ou limiares.',
           'O sistema não chama LLM durante a classificação e não usa decisões por ID. A precisão real nas 559 e a meta de 95% permanecem não comprovadas.','']
    (saida/'previsao.txt').write_text('\n'.join(texto),encoding='utf-8')
    with (saida/'fila_revisao.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=base.legado.CAMPOS_ENTREGA);w.writeheader();w.writerows(r for r in alvo if r['decisao']=='revisar')
    anterior={r['id']:r for r in csv.DictReader((projeto/'entrega_etapa2_v2/publicacao.csv').open(encoding='utf-8'))}
    transicoes={}
    for r in alvo:
        par=anterior[r['id']]['decisao']+' -> '+r['decisao'];transicoes[par]=transicoes.get(par,0)+1
    base.escrever(saida/'comparacao_com_v2.json',{'transicoes_alvo':transicoes,
        'v2':contar([r for r in anterior.values() if r['id'] not in oficiais]),'v3':contar(alvo),
        'mudancas_de_tema_alvo':sum(r['tema_central_id']!=anterior[r['id']]['tema_central_id'] for r in alvo),
        'interpretacao':'Mudança de tema não é prova de correção ou erro; os rótulos dos 559 não estão disponíveis.'})
    base.escrever(saida/'manifesto_entrega.json',{'modelo_sha256':base.sha(modelo/'modelo.json'),
        'arquivos_sha256':{p.name:base.sha(p) for p in sorted(saida.iterdir()) if p.is_file() and p.name!='manifesto_entrega.json'}})
    print(json.dumps(resumo,ensure_ascii=False,indent=2));return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path(__file__).parent)
    p.add_argument('--modelo',type=Path,default=Path('artefatos/melhorias_v3'))
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args();executar(args.projeto.resolve(),args.modelo.resolve(),args.saida.resolve())
