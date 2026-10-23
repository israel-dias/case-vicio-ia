"""Compara as decisões das 559 e exporta exemplos sem julgamento jurídico."""
import argparse
import csv
import json
from pathlib import Path

from compatibilidade_v2 import features as f
from compatibilidade_v2 import runtime as rt


def executar(projeto,saida):
    if saida.exists():raise ValueError('Saída existente; escolha outra pasta.')
    dados=projeto/'dados/anexos'
    qs,temas,ys=f.carregar(dados)
    def ler(p):return {r['id']:r for r in map(json.loads,p.read_text().splitlines())}
    antes=ler(projeto/'entrega_etapa2_v2/rastreabilidade.jsonl')
    depois=ler(projeto/'entrega_experimental_v3/rastreabilidade.jsonl')
    alteradas=[]
    for qid in sorted(set(qs)-set(ys)):
        a,b=antes[qid],depois[qid]
        if a['decisao']!=b['decisao']:
            alteradas.append({'id':qid,'antes':a['decisao'],'depois':b['decisao'],
                'confianca_antes':a['confianca'],'confianca_depois':b['confianca'],
                'caminho_antes':a['caminho'],'caminho_depois':b['caminho'],
                'motivo_depois':b['motivo'],'alertas':b.get('alertas_computados',[])})
    saida.mkdir(parents=True)
    rt.escrever(saida/'transicoes_559.json',{'questoes':559,'mudancas':alteradas,
        'nota':'Sem rótulos oficiais para estas questões. Liberação ou bloqueio não demonstra acerto jurídico.'})
    grupos=[('Passaram de revisão para publicação',[r for r in alteradas if r['depois']=='publicar']),
            ('Passaram de publicação para revisão',[r for r in alteradas if r['depois']=='revisar'])]
    texto=['# Casos das 559 questões avaliadas — comparação v2/v3','',
           'Exemplos selecionados automaticamente pela mudança de confiança, sem verificar respostas ou atribuir novos temas à mão. Todos estão fora da folha-verdade.','']
    for titulo,rows in grupos:
        texto+=['## '+titulo,'',f'Total neste grupo: {len(rows)}. Abaixo, até dez exemplos com a maior mudança absoluta de confiança.','']
        for r in sorted(rows,key=lambda r:(-abs(r['confianca_depois']-r['confianca_antes']),r['id']))[:10]:
            q=qs[r['id']]
            texto+=['### '+r['id'],'',f"Antes: **{r['antes']}**, {r['confianca_antes']:.2%}. Depois: **{r['depois']}**, {r['confianca_depois']:.2%}.",'',
                    '**Questão completa:** '+f.visivel(q['enunciado_html'])]
            cmd=f.visivel(q.get('comando',''))
            if cmd and f.normalizar(cmd) not in f.normalizar(f.visivel(q['enunciado_html'])):texto+=['',cmd]
            texto+=['']+[f"- **{k})** {f.visivel(v)}" for k,v in sorted(q['alternativas'].items())]
            texto+=['',f"Tema sugerido: {r['caminho_depois']}.",'',f"Motivo calculado: {r['motivo_depois']}",'',
                    'Alertas computados: '+(' '.join(r['alertas']) if r['alertas'] else 'Nenhum alerta adicional.'),'',
                    '**Precisão deste caso: não medida.**','']
    (saida/'CASOS_DAS_559.md').write_text('\n'.join(texto),encoding='utf-8')
    return {'mudancas':len(alteradas),'revisar_para_publicar':len(grupos[0][1]),'publicar_para_revisar':len(grupos[1][1])}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path(__file__).parent)
    p.add_argument('--saida',type=Path,required=True)
    args=p.parse_args();print(json.dumps(executar(args.projeto.resolve(),args.saida.resolve()),ensure_ascii=False,indent=2))
