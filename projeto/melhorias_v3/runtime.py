"""Inferência v3 congelada: sem rótulos, rede ou ajuste de modelos."""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path

from compatibilidade_v2 import features as f
from compatibilidade_v2 import runtime as rt
from . import aprendizado as a
from .representacao import Catalogo,NOMES

VERSAO='runtime_melhorias_v3_1'


def codigos():
    root=Path(__file__).resolve().parents[1]
    nomes=['melhorias_v3/runtime.py','melhorias_v3/representacao.py','melhorias_v3/aprendizado.py','classificar_melhorias_v3.py']
    return {n:rt.sha(root/n) for n in nomes}


class Runtime:
    def __init__(self,pasta):
        pasta=Path(pasta)
        manifesto=json.loads((pasta/'manifesto_modelo.json').read_text())
        for nome,h in manifesto['arquivos_sha256'].items():
            p=(pasta/nome).resolve()
            if not p.is_relative_to(pasta.resolve()) or rt.sha(p)!=h:
                raise ValueError('Artefato v3 alterado ou caminho inválido: '+nome)
        self.registro=json.loads((pasta/'modelo.json').read_text())
        mod=self.registro
        if mod['versao']!=VERSAO or mod['codigo_sha256']!=codigos() or mod['nomes_atributos']!=NOMES:
            raise ValueError('Código/versão/atributos diferentes do modelo registrado.')
        if mod['metodo_final'] not in ('controle_v2',*a.METODOS):raise ValueError('Método desconhecido.')
        for m in mod['modelos'].values():rt.validar_linear(m,len(NOMES))
        for m in mod['calibradores'].values():
            rt.validar_linear(m,1)
            if 'coeficientes' in m and m['coeficientes'][0]<0:raise ValueError('Calibrador não monotônico.')
        for pol in mod['politicas'].values():
            n,c=pol['suporte_interno'],pol['acertos_internos']
            rt.cal.validar_contagens(c,n)
            if not isinstance(pol['ativa'],bool):raise ValueError('Política inválida.')
            if pol['ativa']:
                limite=rt.cal.numero(pol['limiar'],'limiar')
                if not 0<=limite<=1 or n<10 or c/n<.95:raise ValueError('Política sem suporte.')
            elif pol['limiar'] is not None or n or c:raise ValueError('Política inativa inconsistente.')
        self.base=rt.Runtime(pasta/'base_v2')
        mapa=json.loads((pasta/'referencias_normativas_v1.json').read_text())
        propostas=json.loads((pasta/'base_v2/escopos.json').read_text())['temas']
        self.catalogo=Catalogo(self.base.temas,propostas,self.base.registro['configuracao_escopos'],mapa)
        self.temas=self.base.temas
        if mod['familias']!=self.catalogo.familias:raise ValueError('Famílias diferentes do ajuste.')

    def classificar(self,q):
        qid=q.get('id')
        if not isinstance(qid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',qid):raise ValueError('ID inválido.')
        metodo=self.registro['metodo_final']
        if metodo=='controle_v2':
            row,trace=self.base.classificar(q)
            return row,{**trace,'variante':'controle_v2','melhorias_promovidas':False}
        p=self.catalogo.transformar({'registro':q})['registro']
        ss=a.sinais({'registro':p},self.registro['modelos'],self.catalogo.familias)[metodo]
        sinal=ss[0];prob=a.confiancas(ss,self.registro['calibradores'][metodo])[0]
        pol=self.registro['politicas'][metodo]
        decisao=f.decidir(sinal,prob,pol)
        tid=sinal['tema_central_id'];k=sinal['indice'];attrs=dict(zip(NOMES,map(float,p['features_v3'][k])))
        if max(sinal['score_legacy'],sinal['score_referencias'])<=0:raise ValueError('Sem candidato: exige triagem de importação.')
        alertas=[]
        if tid!=sinal['primeiro_legacy']:alertas.append('Candidato escolhido difere do primeiro da busca v2.')
        if attrs['escopo_enunciado']<.03 and attrs['escopo_alternativas']>=.03:
            alertas.append('Correspondência com o escopo concentrada nas alternativas.')
        if attrs['citacao_sem_correspondencia']>0:
            alertas.append('Há referência normativa sem associação documental ao candidato.')
        if attrs['origem_reconhecida'] and not attrs['origem_compativel']:
            alertas.append('Disciplina de origem diverge da do candidato; metadado usado como apoio fraco.')
        if pol['ativa'] and abs(prob-pol['limiar'])<.03:alertas.append('Confiança próxima do corte.')
        if not pol['ativa']:motivo='Nenhum corte interno atingiu a meta empírica com suporte mínimo; conferir sugestão.'
        elif not sinal['elegivel']:motivo='Pouca evidência textual para publicação; conferir sugestão.'
        else:
            operador='>=' if decisao=='publicar' else '<'
            motivo=f"Confiança v3 {prob:.3f} {operador} corte {pol['limiar']:.3f}; variante {metodo}."
        if decisao=='revisar' and alertas:motivo+=' '+alertas[0]
        row={'id':qid,'decisao':decisao,'tema_central_id':tid,'extras_ids':'','confianca':f'{prob:.8f}','motivo':motivo}
        trace={'id':qid,'decisao':decisao,'tema_central_id':tid,'caminho':self.temas[tid]['caminho'],
               'variante':metodo,'confianca':prob,'limiar':pol['limiar'],'elegivel':sinal['elegivel'],
               'motivo':motivo,'alertas_computados':alertas,'atributos':attrs,'referencias_extraidas':p['refs_extraidas'],
               'candidatos_comparados':[{'tema_id':t,'caminho':self.temas[t]['caminho']} for t in sinal['candidatos']],
               'primeiro_busca_v2':sinal['primeiro_legacy'],'sha256_texto':p['hash'],
               'nota':'Alertas são sinais de engenharia, não diagnósticos jurídicos nem prova de erro na questão.'}
        return row,trace


def executar(modelo,questoes_path,saida):
    saida=Path(saida)
    if saida.exists():raise ValueError('A saída já existe; use outra pasta.')
    inicio=time.perf_counter();h=rt.sha(questoes_path);runtime=Runtime(modelo)
    qs=rt.legado.ler_questoes(questoes_path);linhas=[];rastros=[]
    with f.threadpool_limits(limits=2):
        for q in sorted(qs,key=lambda x:x['id']):
            row,trace=runtime.classificar(q);linhas.append(row);rastros.append(trace)
    rt.legado.validar_entrega(linhas,runtime.temas,[q['id'] for q in qs])
    if rt.sha(questoes_path)!=h:raise ValueError('Questões alteradas durante a execução.')
    resumo={'questoes':len(qs),'metodo':runtime.registro['metodo_final'],
            'decisoes':{d:sum(r['decisao']==d for r in linhas) for d in ['publicar','revisar','fora']},
            'precisao_real':None,'rotulos_lidos_na_classificacao':False,'chamadas_llm':0,
            'treinamento_na_classificacao':False,'segundos':time.perf_counter()-inicio}
    saida.parent.mkdir(parents=True,exist_ok=True);tmp=Path(tempfile.mkdtemp(prefix='.classificacao-v3-',dir=saida.parent))
    try:
        rt.cal.salvar_csv(tmp/'publicacao.csv',linhas,rt.legado.CAMPOS_ENTREGA)
        with (tmp/'rastreabilidade.jsonl').open('w',encoding='utf-8') as arq:
            for r in rastros:arq.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
        rt.escrever(tmp/'resumo_classificacao.json',resumo)
        rt.escrever(tmp/'manifesto_classificacao.json',{'questoes_sha256':h,'modelo_sha256':rt.sha(Path(modelo)/'modelo.json'),
            'arquivos_sha256':{p.name:rt.sha(p) for p in sorted(tmp.iterdir())}})
        tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise
    return resumo
