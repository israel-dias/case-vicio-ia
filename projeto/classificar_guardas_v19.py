"""Reproduz composição por disciplina prevista; não é política promovida."""
import argparse,csv,json
from pathlib import Path
from compatibilidade_v2.runtime import legado,validar_linear
from classificar_roteamento_v15 import verificar
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from isolamento_v17.metricas import medir
from expressoes_v19 import modelo as m
from expressoes_v19.guarda import combinar

VARIANTES=('frases_completas','vocabulario_escopos','passagem_cobrada')

def executar(projeto,experimento,questoes,saida,variante):
    projeto,experimento,questoes,saida=[Path(x).resolve() for x in [projeto,experimento,questoes,saida]]
    if saida.exists():raise ValueError('Use saída nova.')
    if variante not in VARIANTES:raise ValueError('Escolha uma variante explícita.')
    reg=json.loads((experimento/'manifesto_inferencia.json').read_text())
    if reg['versao']!='guarda_disciplina_v19_1':raise ValueError('Versão incompatível.')
    verificar(projeto,reg['codigo_sha256']);origem=projeto/reg['experimento_base']
    if not origem.resolve().is_relative_to(projeto):raise ValueError('Experimento fora do projeto.')
    verificar(origem,reg['artefatos_base_sha256']);r=json.loads((origem/'manifesto_inferencia.json').read_text())
    verificar(projeto,r['projeto_sha256']);verificar(origem,r['artefatos_sha256'])
    packs=json.loads((origem/'modelos_finais.json').read_text())['modelos']
    for v in ['controle_atual',variante]:
        validar_linear(packs[v]['modelo'],len(m.ATRIBUTOS[v]));validar_linear(packs[v]['calibrador'],1)
    cat,_=carregar_catalogo(projeto);dic=Dicionario(json.loads((projeto/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
    qs={q['id']:q for q in legado.ler_questoes(questoes)};ps=m.preparar(cat,dic,qs)
    base=m.aplicar(ps['controle_atual'],packs['controle_atual'],cat,'controle_atual');novas=m.aplicar(ps[variante],packs[variante],cat,variante)
    rows=sorted(combinar(base,novas,cat.temas),key=lambda r:r['id']);saida.mkdir(parents=True)
    with (saida/'classificacoes_experimentais.csv').open('w',encoding='utf-8',newline='') as a:
        w=csv.DictWriter(a,fieldnames=['id','decisao','tema_central_id','extras_ids','confianca','motivo']);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ['id','decisao','tema_central_id','confianca','motivo']}|{'extras_ids':''})
    with (saida/'rastreabilidade.jsonl').open('w',encoding='utf-8') as a:
        for r in rows:a.write(json.dumps({**r,'evidencia_v19':ps[variante][r['id']]['evidencia_v19']},ensure_ascii=False)+'\n')
    resumo=medir(rows)|{'variante':variante,'confianca_global_recalibrada':False,'precisao_real_559':None,'rotulos_lidos':False,'chamadas_llm':0,'promove_entrega':False}
    (saida/'resumo.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resumo,ensure_ascii=False));return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--experimento',type=Path,default=Path('experimentos/guardas_v19_001'));p.add_argument('--questoes',type=Path,default=Path('experimentos/expressoes_v19_001/questoes_559_sem_rotulos.jsonl'));p.add_argument('--saida',type=Path,required=True);p.add_argument('--variante',choices=VARIANTES,required=True);z=p.parse_args();executar(z.projeto,z.experimento,z.questoes,z.saida,z.variante)
