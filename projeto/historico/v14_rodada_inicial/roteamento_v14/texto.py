"""Hipóteses de leitura por papéis. Sem respostas, rótulos ou exceções por ID."""
import re
from collections import Counter
from functools import lru_cache
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import lexico,sem_acento
from mescla_marcadores_v7.texto import GENERICOS,rotear as rotear_v7,alternativas_tematicas
from experimento_relacoes_v9.regras import Identificador

INSTRUCAO=re.compile(r'\b(?:assinale|marque|selecione|indique)\s+(?:(?:a|uma)\s+)?(?:alternativa|opcao|assertiva)\s+(?:correta|incorreta|errada|certa)\b[.:,]?\s*',re.I)
ROMANO=re.compile(r'(?:^|(?<=[\n;:]))\s*(?P<numero>VIII|VII|VI|IV|III|II|IX|V|I|X)(?:\s*[.\)\-–—]\s*|\s+(?=[A-ZÀ-Ú]))')
VALORES={'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10}
STOP=set(GENERICOS)|set('crime crimes pena penas explicar explique indicando indique frase analisar analise hipotetica hipotetico situacao narrado narrada praticado praticada impossivel possivel complete responda regencia entendimento'.split())

def limpar(t):
    t=f.visivel(t)
    # Grafias de uma mesma palavra, sem inserir uma resposta ou tema presumido.
    return re.sub(r'\bco[\s-]+autoria\b','coautoria',t,flags=re.I)

def linhas(t):
    p=f.TextoVisivel();p.feed(t.replace('\\n','\n'));p.close();return ''.join(p.partes)

def separar_itens(en):
    texto=linhas(en);mm=list(ROMANO.finditer(texto))
    numeros=[VALORES[m['numero']] for m in mm]
    if len(mm)<2 or numeros[0]!=1 or numeros!=sorted(set(numeros)):
        return {'cabecalho':limpar(en),'itens':[],'numeros':[]}
    itens=[limpar(texto[m.end():mm[j+1].start() if j+1<len(mm) else len(texto)]) for j,m in enumerate(mm)]
    if any(not a for a in itens):return {'cabecalho':limpar(en),'itens':[],'numeros':[]}
    return {'cabecalho':limpar(texto[:mm[0].start()]),'itens':itens,'numeros':numeros}

def termos(t):return {w for w in lexico(limpar(t),{}).split() if len(w)>3 and w not in STOP and not w.isdigit()}

class Leitor:
    def __init__(self,cat,dic):
        self.cat=cat;self.idt=Identificador(cat,dic);self.idx={t:k for k,t in enumerate(cat.familias)}
        self.titulos=[];freq=Counter()
        for tid in cat.ids:
            t=cat.temas[tid];familia=t['parent_id'] if t['nivel']==2 else tid
            ts=termos(t['titulo']);self.titulos.append((familia,ts));
        for familia in cat.familias:
            ts=set().union(*(ts for fam,ts in self.titulos if fam==familia))
            freq.update(ts)
        self.freq=freq
        self.homonimos={t:[u for u in cat.familias if u!=t and f.normalizar(cat.temas[u]['titulo'])==f.normalizar(cat.temas[t]['titulo'])] for t in cat.familias}

    @lru_cache(maxsize=16000)
    def identificadores(self,texto):
        txt=limpar(texto);cs,hits=self.idt.encontrar(txt);encontrados=set(cs);q=termos(txt)
        for familia,ts in self.titulos:
            comuns=q&ts
            composto=len(comuns)>=2 and len(comuns)/max(1,len(ts))>=.5
            raro=any(len(w)>=7 and self.freq[w]<=2 for w in comuns)
            if composto or raro:encontrados.add(familia)
        return tuple(sorted(encontrados,key=int))

    @lru_cache(maxsize=16000)
    def pontuar(self,texto):
        txt=limpar(texto);nf=len(self.cat.familias)
        if not txt:return f.np.zeros((nf,7))
        norm=f.normalizar(txt);lx=lexico(txt,self.cat.aliases)
        w=(self.cat.palavras.transform([norm])@self.cat.wp.T).toarray()[0]
        c=(self.cat.caracteres.transform([norm])@self.cat.cp.T).toarray()[0]
        sw=(self.cat.escopo_palavras.transform([lx])@self.cat.ew.T).toarray()[0]
        sc=(self.cat.escopo_caracteres.transform([lx])@self.cat.ec.T).toarray()[0]
        tt=(self.cat.escopo_palavras.transform([lx])@self.cat.tw.T).toarray()[0]
        refs=self.cat.referencias.extrair(txt);ids=set(self.identificadores(txt));out=[]
        for fam,js in zip(self.cat.familias,self.cat.membros):
            nw,art=self.cat.referencias.apoio(refs,fam,self.cat.temas)
            out.append([float(f.np.mean(sorted(w[js],reverse=True)[:3])),
                float(f.np.mean(sorted(c[js],reverse=True)[:3])),float(max((.7*sw+.3*sc)[js])),
                float(max(tt[js])),float(fam in ids),nw,art])
        return f.np.asarray(out)

    def ranking_texto(self,t):
        x=self.pontuar(t)
        return .45*x[:,0]+.15*x[:,1]+.35*x[:,2]+.05*x[:,3]+.08*x[:,4]+.08*f.np.maximum(x[:,5],x[:,6])

    def norma_comando(self,cmd):
        r=self.cat.referencias.extrair(cmd);partes=[]
        for norma,art in r['artigos']:
            nome=norma.upper() if ':' not in norma else 'Lei '+norma.split(':',1)[1]
            partes.append('art. '+art+' do '+nome)
        if not partes:
            partes=[n.upper() if ':' not in n else 'Lei '+n.split(':',1)[1] for n in r['normas']]
        return ' '.join(partes)

    def rotear(self,q,literal):
        en=limpar(q.get('enunciado_html',''));cmd=limpar(q.get('comando',''))
        alts=[limpar(v) for _,v in sorted(q['alternativas'].items())]
        ce=set(f.normalizar(a) for a in alts)=={'certo','errado'}
        tematicas=alternativas_tematicas(q) and not ce
        blocos=separar_itens(q.get('enunciado_html',''));itens=blocos['itens']
        targets=list(self.identificadores(cmd));explique=bool(re.search(r'\bexplique\b',sem_acento(cmd)))
        normcmd=self.norma_comando(cmd) if explique else ''
        efetiva,_=rotear_v7(q,self.cat.temas)
        en_core=limpar(efetiva.get('enunciado_html',''))
        if not en_core and not itens:en_core=en
        rota={'en_usado':en_core,'cmd_usado':cmd if cmd and f.normalizar(cmd) not in f.normalizar(en_core) else '',
            'alts_usadas':alts if tematicas else [],'itens_usados':list(itens),
            'itens_originais':list(itens),'cabecalho':blocos['cabecalho'],'modo':'conjunto',
            'comando_identificadores':targets,'alvos_forcados':[],
            'itens_escolhidos':list(range(len(itens))),'votos_itens':[],
            'certo_errado':ce,'alternativas_tematicas':tematicas,'explique':explique,
            'primeiro_item_fallback':False,'maioria_aplicada':False,'sem_evidencia':False}
        modo='comando' if targets else 'explique_norma' if explique and normcmd else 'explique_sem_identificador' if explique else 'itens' if itens else 'ce' if ce else 'hipotetica' if 'situacao hipotetica' in sem_acento(en) else 'caso_narrado' if 'caso narrado' in sem_acento(en+' '+cmd) else 'instrucao' if INSTRUCAO.search(sem_acento(en+' '+cmd)) else 'conjunto'
        rota['modo']=modo
        if itens:
            votos=[]
            for t in itens:
                s=self.ranking_texto(t);k=int(f.ordenar(s)[0])
                votos.append(self.cat.temas[self.cat.familias[k]]['titulo'] if max(s)>0 else '')
            rota['votos_itens']=votos
        if literal:
            if modo=='comando':
                rota.update(en_usado='',cmd_usado=cmd,alts_usadas=[],itens_usados=[],alvos_forcados=targets)
            elif modo=='explique_norma':
                rota.update(en_usado='',cmd_usado=normcmd,alts_usadas=[],itens_usados=[])
            elif modo=='explique_sem_identificador':
                # Exceção explícita: não inventar um tema a partir de texto vazio.
                rota.update(cmd_usado='',alts_usadas=[],itens_usados=[],sem_evidencia=True)
            elif modo=='itens':
                cont=Counter(t for t in rota['votos_itens'] if t);mais=cont.most_common()
                maioria=bool(mais and mais[0][1]>=2 and (len(mais)==1 or mais[0][1]>mais[1][1]))
                escolhidos=[j for j,t in enumerate(rota['votos_itens']) if maioria and t==mais[0][0]] if maioria else [0]
                rota.update(en_usado='',cmd_usado='',alts_usadas=[],itens_usados=[itens[j] for j in escolhidos],
                    itens_escolhidos=escolhidos,primeiro_item_fallback=not maioria,maioria_aplicada=maioria)
            elif modo=='ce':
                # Muitos ou nenhum alvo na relação: enunciado como um todo.
                refs=self.idt.referencias(q);uteis=[r for r in refs if len(r['familias'])==1]
                trecho=uteis[-1]['trecho'] if len(uteis)==1 else en
                rota.update(en_usado=trecho,cmd_usado='',alts_usadas=[],itens_usados=[])
            elif modo=='hipotetica':
                rota.update(en_usado=en,cmd_usado='',alts_usadas=[],itens_usados=[])
            elif modo=='caso_narrado':
                rota.update(en_usado='',cmd_usado='',alts_usadas=alts if tematicas else [],itens_usados=[])
            elif modo=='instrucao':
                restante=INSTRUCAO.sub('',sem_acento(en+' '+cmd)).strip()
                if self.identificadores(restante):
                    rota.update(en_usado=restante,cmd_usado='',alts_usadas=[],itens_usados=[])
                else:rota.update(en_usado='',cmd_usado='',alts_usadas=alts if tematicas else [],itens_usados=[])
        else:
            # Versão comparativa preserva o contexto; comando recebe papel próprio.
            if modo=='itens':rota.update(en_usado=blocos['cabecalho'],itens_usados=itens)
            if modo=='ce':rota.update(alts_usadas=[])
        rota['texto_efetivo']=' '.join([rota['en_usado'],rota['cmd_usado'],*rota['itens_usados'],*rota['alts_usadas']]).strip()
        if not rota['texto_efetivo']:
            rota['texto_efetivo']=en+' '+cmd;rota['sem_evidencia']=True
        return rota
