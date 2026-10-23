"""Controle de leitura com o mesmo recuperador V8. Não decide publicação."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.experimento import preparar
from roteamento_v15.texto import Leitor

VARIANTES=['original_v8','contexto_v15','sem_cabecalho_informativo','comando_sem_antecedente']
def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Use saída nova.')
    saida.mkdir(parents=True)
    prot={'variantes':VARIANTES,'codigo_sha256':sha(Path(__file__)),
          'leitor_sha256':sha(projeto/'roteamento_v15/texto.py'),
          'comparacao':'Mesmo recuperador V8. As duas retiradas são controles negativos, não propostas de promoção.',
          'somente_100':True,'mede_confianca':False,'promove_entrega':False,
          'avaliacao':'Desenvolvimento reutilizado e exposto. Não é teste cego.'}
    (saida/'protocolo_previo.json').write_text(json.dumps(prot,ensure_ascii=False,indent=2)+'\n')
    qs,temas,ys=f.carregar(projeto/'dados/anexos');cat,_=carregar_catalogo(projeto)
    dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),temas,cat.familias)
    leitor=Leitor(cat,dic);rotas={i:leitor.rotear(qs[i]) for i in sorted(ys)};rows=[];resumo={}
    for v in VARIANTES:
        entrada={}
        for i in sorted(ys):
            q=dict(qs[i]);r=rotas[i]
            if v!='original_v8':
                en=r['en_usado']
                if v=='sem_cabecalho_informativo' and r['itens_usados']:en=''
                if v=='comando_sem_antecedente' and (r['comando_retoma_enunciado'] or r['norma_sem_contexto']):en=''
                q.update(enunciado_html=' '.join([en,*r['itens_usados']]),comando=r['cmd_usado'],
                         alternativas={str(k):t for k,t in enumerate(r['alts_usadas'])} if r['alts_usadas'] else {'A':''})
            entrada[i]=q
        print('Controle de leitura:',v,flush=True);pp=preparar(cat,dic,entrada)
        for i,p in pp.items():
            t=cat.familias[int(f.ordenar(p['ranking_vocabulario_reordena'])[0])]
            rows.append({'id':i,'variante':v,'tema_central_id':t,'correto':int(f.aceito(t,ys[i],temas))})
    base={r['id']:r for r in rows if r['variante']=='original_v8'}
    for v in VARIANTES:
        rr=[r for r in rows if r['variante']==v]
        resumo[v]={'questoes':len(rr),'acertos_top1':sum(r['correto'] for r in rr),
                   'corrigidas':[r['id'] for r in rr if r['correto'] and not base[r['id']]['correto']],
                   'acertos_perdidos':[r['id'] for r in rr if not r['correto'] and base[r['id']]['correto']]}
    with (saida/'comparacao_100.csv').open('w',encoding='utf-8',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2));return resumo
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True)
    z=p.parse_args();executar(z.projeto,z.saida)
