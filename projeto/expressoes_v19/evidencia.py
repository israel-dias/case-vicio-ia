"""Extrai evidências literais do catálogo; não recebe rótulos de questões."""
import re,json
from pathlib import Path
from collections import Counter
from compatibilidade_v2 import features as f
from contexto_v18.texto import tokens,GENERICOS,CONECTORES,ISOLADOS_AMBIGUOS,frases
from contexto_v18.foco_morfologico import FORMAS,Extrator,IdentificadoresMorfologicos
from roteamento_v14.texto import limpar,separar_itens

COMUNS=GENERICOS|CONECTORES|ISOLADOS_AMBIGUOS|set('agente morte contra mediante outros outras casos caso fato fatos forma formas conduta resultado causas efeitos existencia ausencia vontade hipoteses hipotese materia assunto instituto institutos'.split())


def canon(texto):
    return [FORMAS.get(w,w) for w in tokens(texto) if w not in CONECTORES]


def contem(seq,padrao):
    return bool(padrao) and any(tuple(seq[j:j+len(padrao)])==tuple(padrao) for j in range(len(seq)))


class Evidencia:
    def __init__(self,cat):
        self.cat=cat;self.ex=Extrator(cat);self.det=IdentificadoresMorfologicos(cat)
        propostas=json.loads((Path(__file__).resolve().parents[1]/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
        self.ix={t:k for k,t in enumerate(cat.familias)};self.expressoes=[];familias_palavra={t:set() for t in cat.familias}
        for tid in cat.ids:
            t=cat.temas[tid];fam=t['parent_id'] if t['nivel']==2 else tid
            titulo=tuple(canon(t['titulo']))
            if len(titulo)>=2:self.expressoes.append((fam,titulo,'titulo',tid))
            texto=propostas[tid]['descricao_proposta']
            partes=re.split(r'[;,.:]',texto)
            for parte in partes:
                ts=tuple(canon(parte));infos=[w for w in ts if w not in COMUNS]
                if 2<=len(ts)<=8 and infos:self.expressoes.append((fam,ts,'escopo',tid))
                familias_palavra[fam].update(w for w in ts if w not in COMUNS and len(w)>=7)
        frequencia=Counter(w for ws in familias_palavra.values() for w in ws)
        self.raridades={t:{w for w in ws if frequencia[w]==1} for t,ws in familias_palavra.items()}
        self.expressoes=list(dict.fromkeys(self.expressoes))

    def pontuar(self,texto):
        seq=canon(texto);ws=set(seq);literais=set(tokens(texto));nf=len(self.cat.familias)
        tit=f.np.zeros(nf);esc=f.np.zeros(nf);raro=f.np.zeros(nf);rastros=[]
        for fam,padrao,tipo,tid in self.expressoes:
            if not contem(seq,padrao):continue
            j=self.ix[fam]
            if tipo=='titulo':tit[j]=max(tit[j],min(1,len(padrao)/4))
            else:esc[j]=max(esc[j],min(1,len(padrao)/5))
            rastros.append({'familia':fam,'tema_fonte':tid,'tipo':tipo,'expressao':' '.join(padrao)})
        for fam,palavras in self.raridades.items():
            # Derivações como 'consumada' não viram um substantivo jurídico
            # distintivo isolado. Continuam disponíveis em expressões compostas.
            achadas=sorted(w for w in palavras&ws if w not in set(FORMAS.values()) or w in literais)
            if achadas:
                j=self.ix[fam];raro[j]=min(1,len(achadas)/2)
                rastros.append({'familia':fam,'tipo':'vocabulo_distintivo_catalogo','expressoes':achadas})
        return tit,esc,raro,rastros

    def preparar(self,q):
        n,extr=self.ex.extrair(q);d=self.det.analisar(n)
        alts=[limpar(x) for x in n.get('alternativas',{}).values()]
        ce=bool(alts and set(f.normalizar(a) for a in alts)<={'certo','errado','verdadeiro','falso'})
        combinado=' '.join([limpar(n.get('enunciado_html','')),limpar(n.get('comando','')),*([] if ce else alts)])
        itens=separar_itens(q.get('enunciado_html',''))['itens']
        vf=bool(re.search(r'\(\s*\)',limpar(q.get('enunciado_html',''))))
        cmd=limpar(n.get('comando',''));en=limpar(n.get('enunciado_html',''))
        if itens or vf:foco=combinado;motivo='todas_as_proposicoes_preservadas'
        elif d['forte'] and cmd:foco=' '.join([cmd,*([] if ce else alts)]);motivo='comando_com_identificador_e_alternativas_tematicas'
        elif cmd and d['origem']!='lista_multitematica_sem_foco':
            # Uma pergunta de retomada mantém a frase anterior da narrativa.
            anteriores=frases(en);retoma=bool(re.search(r'\b(?:caso|situacao|narrad\w*|referid\w*|nesse|nessa)\b',f.normalizar(cmd)))
            foco=' '.join([anteriores[-1] if anteriores and retoma else '',cmd,*([] if ce else alts)])
            motivo='cobranca_com_contexto_da_retomada' if retoma else 'cobranca_extraida'
        else:foco=combinado;motivo='sem_cobranca_inequivoca_preserva_conjunto'
        titulo,escopo,raro,reg=self.pontuar(combinado);ft,fe,fr,freg=self.pontuar(foco)
        # Títulos duplicados de ramos distintos não são fundidos.
        return {'titulo':titulo,'escopo':escopo,'raro':raro,'foco_titulo':ft,'foco_escopo':fe,'foco_raro':fr,
                'trace':{'origem_foco':motivo,'foco':foco,'texto_completo':combinado,'evidencias':reg,'evidencias_foco':freg,'extracao':extr,'certo_errado':ce}}
