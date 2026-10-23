"""Ablação de leitura sobre o MESMO recuperador V8; não avalia confiança."""
import argparse,json,csv
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.experimento import preparar

VARIANTES=['original','ce_sem_alternativas','somente_comando_identificado','somente_itens_selecionados','roteamento_literal_completo']
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True)
    protocolo={'variantes':VARIANTES,'codigo_sha256':sha(Path(__file__)),
        'comparacao':'Mesmo catálogo, dicionário e recuperador V8 em todas; só muda o texto/campo segundo as rotas V14 salvas.',
        'rotas_sha256':sha(projeto/'experimentos/roteamento_v14_002/campos_659.json'),
        'somente_100':True,'avaliacao':'Diagnóstico pós-rodadas V14 reutilizando os mesmos 100; não independente.',
        'mede_confianca':False,'publica_questoes':False,'promove_entrega':False}
    (saida/'protocolo_previo.json').write_text(json.dumps(protocolo,ensure_ascii=False,indent=2)+'\n')
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    rotas=json.loads((projeto/'experimentos/roteamento_v14_002/campos_659.json').read_text());resumo={};rows=[]
    for v in VARIANTES:
        entrada={}
        for i in sorted(ys):
            q=dict(qs[i]);r=rotas[i]['literal']
            usar=(v=='roteamento_literal_completo' or v=='somente_comando_identificado' and r['modo'] in ['comando','explique_norma'] or v=='somente_itens_selecionados' and r['modo']=='itens')
            if v=='ce_sem_alternativas' and r['certo_errado']:q['alternativas']={'A':''}
            elif usar:
                q.update(enunciado_html=r['en_usado']+' '+' '.join(r['itens_usados']),comando=r['cmd_usado'],
                    alternativas={str(j):t for j,t in enumerate(r['alts_usadas'])} if r['alts_usadas'] else {'A':''})
                if not q['enunciado_html'].strip() and not q['comando'].strip() and not any(q['alternativas'].values()):q['enunciado_html']=r['texto_efetivo']
            entrada[i]=q
        print('Ablação de leitura:',v,flush=True);pp=preparar(cat,dic,entrada);atuais=[]
        for i,p in pp.items():
            t=cat.familias[int(f.ordenar(p['ranking_vocabulario_reordena'])[0])]
            r={'id':i,'variante':v,'tema_central_id':t,'correto':int(f.aceito(t,ys[i],temas))};rows.append(r);atuais.append(r)
        resumo[v]={'questoes':100,'acertos_top1':sum(r['correto'] for r in atuais)}
    baseline={r['id']:r for r in rows if r['variante']=='original'}
    for v,z in resumo.items():
        rr=[r for r in rows if r['variante']==v]
        z['corrigidas']=[r['id'] for r in rr if r['correto'] and not baseline[r['id']]['correto']]
        z['acertos_perdidos']=[r['id'] for r in rr if not r['correto'] and baseline[r['id']]['correto']]
    with (saida/'comparacao_100.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resumo,ensure_ascii=False,indent=2));return resumo
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
