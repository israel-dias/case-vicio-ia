"""Inferência congelada da candidata sem sinais de formato, sem LLM ou rótulos."""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from compatibilidade_v2 import features as f
from compatibilidade_v2 import runtime as base
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import Catalogo, NOMES


VERSAO = 'runtime_flexivel_v5_1'
RETIRADOS = ('certo_errado','assertivas_numeradas','numero_alternativas')
ATIVOS = [n for n in NOMES if n not in RETIRADOS]


def codigos():
    root=Path(__file__).resolve().parents[1]
    nomes=['flexivel_v5/runtime.py','classificar_flexivel_v5.py',
           'melhorias_v3/representacao.py','melhorias_v3/aprendizado.py']
    return {n:base.sha(root/n) for n in nomes}


def validar_modelo(m):
    if m.get('versao')!=VERSAO or m.get('variante')!='sem_formato':
        raise ValueError('Versão ou variante inválida.')
    if m.get('nomes_atributos')!=ATIVOS or m.get('atributos_retirados')!=list(RETIRADOS):
        raise ValueError('Conjunto de atributos incompatível.')
    if m.get('codigo_sha256')!=codigos():raise ValueError('Código diferente do artefato congelado.')
    base.validar_linear(m['compatibilidade'],len(ATIVOS))
    base.validar_linear(m['calibrador'],1)
    if 'coeficientes' in m['calibrador'] and m['calibrador']['coeficientes'][0]<0:
        raise ValueError('Calibrador não monotônico.')
    pol=m['politica'];n,c=pol['suporte_interno'],pol['acertos_internos']
    base.cal.validar_contagens(c,n)
    if not isinstance(pol['ativa'],bool):raise ValueError('Política inválida.')
    if pol['ativa']:
        corte=base.cal.numero(pol['limiar'],'limiar')
        if not 0<=corte<=1 or n<10 or c/n<.95:raise ValueError('Política sem suporte empírico previsto.')
    elif pol['limiar'] is not None or n or c:raise ValueError('Política inativa inconsistente.')


class Runtime:
    def __init__(self,pasta):
        self.pasta=Path(pasta).resolve()
        manifest=json.loads((self.pasta/'manifesto_modelo.json').read_text())
        hashes=manifest.get('arquivos_sha256',{})
        if not {'modelo.json','referencias_normativas_v1.json','base_v2/modelo.json'}<=set(hashes):
            raise ValueError('Manifesto incompleto.')
        for nome,h in hashes.items():
            p=(self.pasta/nome).resolve()
            if not p.is_relative_to(self.pasta) or base.sha(p)!=h:
                raise ValueError('Artefato alterado ou caminho inválido: '+nome)
        self.registro=json.loads((self.pasta/'modelo.json').read_text())
        validar_modelo(self.registro)
        self.base=base.Runtime(self.pasta/'base_v2')
        props=json.loads((self.pasta/'base_v2/escopos.json').read_text())['temas']
        mapa=json.loads((self.pasta/'referencias_normativas_v1.json').read_text())
        self.catalogo=Catalogo(self.base.temas,props,self.base.registro['configuracao_escopos'],mapa)
        self.temas=self.base.temas
        if self.registro['familias']!=self.catalogo.familias:raise ValueError('Famílias diferentes do treinamento.')
        self.indices=[NOMES.index(n) for n in ATIVOS]

    def classificar(self,q):
        qid=q.get('id')
        if not isinstance(qid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',qid):
            raise ValueError('ID inválido.')
        p=self.catalogo.transformar({'registro':q})['registro']
        k=int(f.ordenar(p['scores'])[0]);tid=self.catalogo.familias[k]
        if max(p['scores'][k],p['scores_novos'][k])<=0:
            raise ValueError('Sem candidato recuperável; exige triagem de importação.')
        x=p['features_v3'][[k]][:,self.indices]
        z=float(a.escore_linear(x,self.registro['compatibilidade'])[0])
        prob=float(f.predizer_linear([[z]],self.registro['calibrador'])[0])
        elegivel=bool(p['scores'][k]>=.03 or p['scores_novos'][k]>=.03)
        decisao=f.decidir({'elegivel':elegivel},prob,self.registro['politica'])
        pol=self.registro['politica']
        if not pol['ativa']:motivo='Política sem suporte empírico para publicação; conferir sugestão.'
        elif not elegivel:motivo='Pouco sinal textual para sustentar a sugestão; conferir tema.'
        else:
            op='>=' if decisao=='publicar' else '<'
            motivo=f"Confiança calibrada {prob:.3f} {op} corte {pol['limiar']:.3f}; política sem atributos de formato."
        attrs=dict(zip(ATIVOS,map(float,x[0])));notas=[]
        if attrs['citacao_sem_correspondencia']>0:
            notas.append('O mapa preparado não estabelece apoio normativo ao candidato; isso não demonstra incompatibilidade jurídica.')
        if attrs['origem_reconhecida'] and not attrs['origem_compativel']:
            notas.append('Origem e candidato diferem; a origem é um atributo auxiliar e não constitui veto.')
        if attrs['escopo_enunciado']<.03 and attrs['escopo_alternativas']>=.03:
            notas.append('Apoio textual ao candidato concentrado nas alternativas; alerta informativo, sem veto adicional.')
        row={'id':qid,'decisao':decisao,'tema_central_id':tid,'extras_ids':'',
             'confianca':f'{prob:.8f}','motivo':motivo}
        trace={'id':qid,'decisao':decisao,'tema_central_id':tid,'caminho':self.temas[tid]['caminho'],
            'confianca':prob,'limiar':pol['limiar'],'elegivel':elegivel,'atributos_em_uso':attrs,
            'atributos_retirados':list(RETIRADOS),'escore_linear':z,'motivo':motivo,
            'notas_informativas':notas,'referencias_extraidas':p['refs_extraidas'],
            'sha256_texto':p['hash'],'nota':'O tema da busca foi preservado. A confiança estima o enquadramento sugerido, não a qualidade jurídica da questão.'}
        return row,trace


def executar(modelo,questoes,saida):
    saida=Path(saida).resolve()
    if saida.exists():raise ValueError('Saída existente; use outra pasta.')
    inicio=time.perf_counter();h=base.sha(questoes);rt=Runtime(modelo)
    qs=base.legado.ler_questoes(questoes);rows=[];traces=[]
    with f.threadpool_limits(limits=2):
        for q in sorted(qs,key=lambda q:q['id']):
            row,trace=rt.classificar(q);rows.append(row);traces.append(trace)
    base.legado.validar_entrega(rows,rt.temas,[q['id'] for q in qs])
    if base.sha(questoes)!=h:raise ValueError('Entrada alterada durante a classificação.')
    resumo={'questoes':len(rows),'versao':VERSAO,'variante':'sem_formato',
        'decisoes':{d:sum(r['decisao']==d for r in rows) for d in ['publicar','revisar','fora']},
        'precisao_real':None,'rotulos_lidos_na_inferencia':False,'chamadas_llm':0,
        'treinamento_na_inferencia':False,'custo_api_usd':0,'segundos':time.perf_counter()-inicio}
    saida.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.flexivel-v5-',dir=saida.parent))
    try:
        base.cal.salvar_csv(tmp/'publicacao.csv',rows,base.legado.CAMPOS_ENTREGA)
        with (tmp/'rastreabilidade.jsonl').open('w',encoding='utf-8') as arq:
            for r in traces:arq.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
        base.escrever(tmp/'resumo_classificacao.json',resumo)
        base.escrever(tmp/'manifesto_classificacao.json',{'modelo_sha256':base.sha(Path(modelo)/'modelo.json'),
            'questoes_sha256':h,'arquivos_sha256':{p.name:base.sha(p) for p in sorted(tmp.iterdir())}})
        tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise
    return resumo
