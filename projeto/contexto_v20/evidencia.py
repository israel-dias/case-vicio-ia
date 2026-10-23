"""O peso de um termo depende da expressão e do campo em que aparece."""
import json,re
from pathlib import Path
from collections import defaultdict
from compatibilidade_v2 import features as f
from expressoes_v19.evidencia import Evidencia as Anterior,canon,COMUNS
from contexto_v18.texto import tokens
from roteamento_v14.texto import limpar,separar_itens

AMBIGUOS={'transito','fechado','aberto','internacao','anterior','posterior','imediato','simultaneo'}
TOPICO=re.compile(r'^(?:sobre|a respeito|acerca|em relacao|quanto|no tocante|com relacao)\b')


class Evidencia(Anterior):
    def __init__(self,cat,homonimos=False):
        super().__init__(cat)
        if homonimos:
            propostas=json.loads((Path(__file__).resolve().parents[1]/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
            familias=defaultdict(set)
            for tid in cat.ids:
                t=cat.temas[tid];fam=t['parent_id'] if t['nivel']==2 else tid
                for w in canon(propostas[tid]['descricao_proposta']):
                    if w not in COMUNS and len(w)>=7:familias[w].add(fam)
            self.raridades={t:set() for t in cat.familias}
            for w,fs in familias.items():
                # Mesma expressão descritiva pode apoiar títulos homônimos,
                # mantendo cada ID e caminho separado, sem desempate por ID.
                conceitos={f.normalizar(cat.temas[t]['titulo']) for t in fs}
                if len(conceitos)==1:
                    for t in fs:self.raridades[t].add(w)
        self.raridades={t:ws-AMBIGUOS for t,ws in self.raridades.items()}

    def campos(self,q):
        n,extr=self.ex.extrair(q);d=self.det.analisar(n)
        en=limpar(n.get('enunciado_html',''));cmd=limpar(n.get('comando',''))
        alts=[limpar(t) for t in n.get('alternativas',{}).values()]
        ce=bool(alts and set(f.normalizar(t) for t in alts)<={'certo','errado','verdadeiro','falso'})
        blocos=separar_itens(q.get('enunciado_html',''));itens=blocos['itens'];cab=blocos['cabecalho']
        if not itens and re.search(r'\(\s*\)',limpar(q.get('enunciado_html',''))):
            partes=re.split(r'\(\s*\)',limpar(q.get('enunciado_html','')));cab=partes[0];itens=[t for t in partes[1:] if t.strip()]
        zero=f.np.zeros((3,len(self.cat.familias)))
        def pont(texto):return f.np.asarray(self.pontuar(texto)[:3])
        alt=f.np.mean([pont(t) for t in alts],axis=0) if alts and not ce else zero
        combinado=' '.join([en,cmd,*([] if ce else alts)])
        if itens:
            prim=f.np.mean([pont(t) for t in itens],axis=0);sec=pont(cab);peso=.8
            evidencia=peso*prim+(1-peso)*sec;foco=' '.join(itens);origem='todas_proposicoes_com_cabecalho_como_apoio'
        elif ce:
            foco=' '.join([en,cmd]);prim=pont(foco);evidencia=prim;origem='assertiva_ce_integral_sem_alternativas'
        elif d['forte'] and cmd:
            foco=cmd;prim=pont(cmd);evidencia=.9*prim+.1*alt;origem='comando_identificado_alternativas_com_apoio_limitado'
        elif d['origem']!='lista_multitematica_sem_foco' and TOPICO.search(f.normalizar(en or cmd)):
            foco=' '.join([en,cmd]);prim=pont(foco);evidencia=.9*prim+.1*alt;origem='delimitacao_temática_sem_voto_de_alternativa_isolada'
        else:
            foco=' '.join([en,cmd]);prim=pont(foco);evidencia=.7*prim+.3*alt;origem='campos_sem_prioridade_media_das_alternativas'
        _,_,_,reg=self.pontuar(combinado)
        return {'titulo':evidencia[0],'escopo':evidencia[1],'raro':evidencia[2],
                'foco_titulo':prim[0],'foco_escopo':prim[1],'foco_raro':prim[2],
                'trace':{'origem_foco':origem,'foco':foco,'texto_completo':combinado,'evidencias':reg,
                         'extracao':extr,'certo_errado':ce,'itens_preservados':itens,
                         'alternativas_por_media':not ce,'palavras_nao_usadas_isoladamente':sorted(AMBIGUOS)}}
