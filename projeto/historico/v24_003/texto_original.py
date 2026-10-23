"""Extração por conteúdo e gramática; tamanho da pergunta não é critério."""
import json,re
from pathlib import Path
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import sem_acento
from contexto_v18.foco_morfologico import Extrator, IdentificadoresMorfologicos
from contexto_v18.texto import frases
from roteamento_v14.texto import limpar,separar_itens
from roteamento_v15.texto import Leitor as LeitorContextual

COBRANCA=re.compile(r'\b(?:qual|quais|caber[aá]|ser[aá]|responder[aá]|dever[aá]|poder[aá]|deve|pode|configura|caracteriza|consiste|assinale|marque|responda|identifique|explique|o regime|a medida|o recurso|a consequ[eê]ncia)\b',re.I)
RETOMA=re.compile(r'\b(?:referid\w*|essa especie|esse instituto|essa modalidade|mencionad\w*|descrit\w*|disposicoes|procedimento|etapas)\b')
CONTEXTO_CRIME=re.compile(r'\b(?:condenad[oa]|acusad[oa]|processad[oa]|investigad[oa])\b[^.;]{0,100}?\b(?:crime|delito|pratica)\s+(?:de|do|da)\s+(.+?)(?=,|\s+a\s+pena\b|[.;]|$)')


class Leitura:
    def __init__(self,cat):
        self.cat=cat;self.ex=Extrator(cat);self.det=IdentificadoresMorfologicos(cat);self.contextual=LeitorContextual(cat,None)
        self.regras=json.loads((Path(__file__).with_name('expressoes.json')).read_text())['regras'];self.indices={t:k for k,t in enumerate(cat.familias)}
        if any(r['familia'] not in self.indices for r in self.regras):raise ValueError('Expressão aponta para família não utilizável.')

    def detectar(self,texto,apoio=''):
        norm=sem_acento(limpar(texto));todos=norm+' '+sem_acento(limpar(apoio));d=self.det.analisar({'comando':texto,'enunciado_html':apoio})
        hits=list(d['hits']);scores=d['scores'].copy()
        for r in self.regras:
            m=re.search(r['padrao'],norm)
            if not m or r.get('apoio') and not re.search(r['apoio'],todos):continue
            if r.get('consequencia') and not re.search(r['consequencia'],todos):continue
            h={'familia':r['familia'],'titulo':self.cat.temas[r['familia']]['titulo'],'expressao':m.group(),'tipo':r['nome'],'forca':3.0}
            hits.append(h);scores[self.indices[r['familia']]]=max(scores[self.indices[r['familia']]],3.)
        # Citação no trecho + ato do procedimento: não basta a lei isolada.
        refs=self.cat.referencias.extrair(texto)
        atos={
            '5524':r'\b(?:pronuncia|impronuncia|jurados|tribunal do juri|plen[aá]rio)\b',
            '5487':r'\b(?:citacao|intimacao|notificacao|carta precatoria)\b',
            '5498':r'\b(?:inquerito|indiciamento|arquivamento|investigacao policial)\b',
            '5199':r'\b(?:pena|regime|condenacao|dosimetria)\b'}
        normativos=[]
        for fam,ato in atos.items():
            if not refs['artigos'] or not re.search(ato,norm):continue
            lei,art=self.cat.referencias.apoio(refs,fam,self.cat.temas)
            if art<=0:continue
            h={'familia':fam,'titulo':self.cat.temas[fam]['titulo'],'expressao':re.search(ato,norm).group(),'tipo':'citacao_e_ato_contextualizados','forca':3.0,'referencias':refs}
            h['fracao_artigos_compativeis']=art;normativos.append(h)
            hits.append(h);scores[self.indices[fam]]=max(scores[self.indices[fam]],3.)
        # Duas ou mais citações convergentes e ato característico podem
        # delimitar o procedimento, apesar de nomes de sujeitos/atos gerais.
        convergentes=[h for h in normativos if h['fracao_artigos_compativeis']>=.75]
        if len(set(map(tuple,refs['artigos'])))>=2 and len(convergentes)==1:
            rejeitados=hits;hits=convergentes;scores=f.np.zeros(len(self.indices))
            scores[self.indices[hits[0]['familia']]]=4.
        else:rejeitados=[]
        familias=sorted({h['familia'] for h in hits})
        # Vários conteúdos independentes não viram uma prioridade única.
        return {**d,'hits':hits,'scores':scores,'forte':len(familias)==1,'familias':familias,
                'origem':'expressao_contextual_v24' if hits else 'sem_identificador_especifico',
                'hits_secundarios_sem_prioridade':rejeitados}

    def preparar(self,q):
        en=limpar(q.get('enunciado_html',''));cmd=limpar(q.get('comando',''));alts=' '.join(limpar(a) for a in q.get('alternativas',{}).values())
        itens=separar_itens(q.get('enunciado_html',''))['itens'];vf=bool(re.search(r'\(\s*\)',en));d=self.detectar(cmd,en+' '+alts)
        novo=dict(q);origem='comando_especifico' if d['forte'] else 'enunciado_alternativas_sem_comando_especifico';foco=cmd if d['forte'] else ''
        if not d['forte'] and not itens and not vf:
            partes=frases(en)
            # As últimas unidades têm prioridade somente se expressam uma
            # cobrança e contêm identificador específico contextualizado.
            for s in reversed(partes[-2:]):
                nd=self.detectar(s,alts)
                if nd['forte'] and COBRANCA.search(s):
                    foco=s;d=nd;origem='cobranca_final_do_enunciado';break
            if not foco and RETOMA.search(f.normalizar(cmd)):
                nd=self.detectar(en,alts)
                if nd['forte']:foco=en;d=nd;origem='retomada_do_enunciado'
            if not foco:
                # Um cabeçalho temático explícito também pode delimitar a
                # questão. Não escolhe apenas pelo último assunto mencionado.
                ini=partes[0] if partes else en;nd=self.detectar(ini,alts)
                if nd['forte'] and re.match(r'^(?:sobre|acerca|a respeito|com relacao|o direito|segundo sua)',f.normalizar(ini)):
                    foco=ini;d=nd;origem='delimitacao_temática_do_enunciado'
        if not foco:
            nd=self.detectar(cmd,en+' '+alts)
            # Comando instrucional sem identificador deixa de competir com
            # enunciado e alternativas; o original permanece na rastreabilidade.
            info=self.contextual.informatividade(cmd)
            guardar=bool(info['informativo'] or info['referencia_normativa'])
            novo['comando']=cmd if guardar else '';d=nd
            origem='comando_sem_identificador_preservado_como_apoio' if guardar else 'enunciado_alternativas_sem_comando_especifico'
        else:
            novo['comando']=foco
            # Transferência, sem duplicar artificialmente a citação.
            if foco in en:novo['enunciado_html']=en.replace(foco,'',1).strip()
        if itens or vf:
            # Não extrai apenas o último item nem apaga proposições.
            novo=dict(q);d=self.detectar(cmd,en+' '+alts);foco=cmd if d['forte'] else '';origem='proposicoes_preservadas'
        return novo,{k:v for k,v in d.items() if k!='scores'}|{'foco':foco,'origem_leitura':origem,'enunciado_original':en,'comando_original':cmd,'itens_preservados':itens,'vf_preservado':vf},d

    def contexto_sem_cobranca(self,q,tema):
        # Veto específico de contexto, não proibição de todo crime narrado.
        en=sem_acento(limpar(q.get('enunciado_html','')));spans=list(CONTEXTO_CRIME.finditer(en))
        if not spans:return False
        alvo=next(t for t in f.pais(tema,self.cat.temas) if self.cat.temas[t]['nivel']==1)
        hit_contexto=any(alvo in self.detectar(m.group(), '')['familias'] for m in spans)
        if not hit_contexto:return False
        resto=CONTEXTO_CRIME.sub(' ',en)+' '+q.get('comando','')+' '+' '.join(q.get('alternativas',{}).values())
        return alvo not in self.detectar(resto,'')['familias']
