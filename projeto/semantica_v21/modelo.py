"""Busca híbrida e comparador clássico; não importa encoder nem usa rede."""
import gzip,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import sha
from melhorias_v3 import aprendizado as a
from .textos import vistas,documentos,hash_texto,Extrator,IdentificadoresMorfologicos
from contexto_v18.texto import tokens,CONECTORES

VARIANTES=('lexical_bm25','e5_query','e5_passage','hibrido_25','hibrido_50','comparador')
NOMES=['palavras','caracteres','bm25','e5_integral','e5_foco','e5_passage',
       'margem_palavras','margem_e5','posicao_palavras','posicao_e5','apoio_lei','apoio_artigo']


def normal(v):
    v=np.asarray(v,dtype=float);amplitude=float(max(v)-min(v))
    return (v-min(v))/amplitude if amplitude>1e-12 else np.zeros(len(v))


class Busca:
    def __init__(self,projeto,cat,cache):
        projeto,cache=Path(projeto),Path(cache);self.cat=cat;self.ex=Extrator(cat);self.det=IdentificadoresMorfologicos(cat)
        reg=json.loads((cache/'manifesto.json').read_text())
        for n,h in reg['sha256_artefatos'].items():
            if sha(cache/n)!=h:raise ValueError('Cache alterado: '+n)
        with gzip.open(cache/'vetores.json.gz','rt') as g:self.vec=json.load(g)
        for h,v in self.vec.items():
            v=np.asarray(v)
            if v.shape!=(384,) or not np.isfinite(v).all() or abs(float(np.linalg.norm(v))-1)>1e-5:
                raise ValueError('Vetor inválido.')
        props=json.loads((projeto/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
        if sha(projeto/'artefatos/compatibilidade_v2/escopos.json')!=reg['sha256_escopos']:raise ValueError('Escopos diferentes do cache.')
        docs=documentos(cat,props);self.ids=cat.ids
        self.eq=np.asarray([self.vetor('query: '+docs[t]) for t in self.ids]);self.ep=np.asarray([self.vetor('passage: '+docs[t]) for t in self.ids])
        dd=[' '.join(tokens(docs[t])) for t in self.ids]
        self.w=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True);self.c=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True)
        self.wd=self.w.fit_transform(dd);self.cd=self.c.fit_transform(dd)
        self.bdocs=[Counter(w for w in d.split() if w not in CONECTORES) for d in dd]
        self.df=Counter(w for d in self.bdocs for w in d);self.dl=np.asarray([sum(d.values()) for d in self.bdocs]);self.avg=float(np.mean(self.dl))
        self.membros=[[self.ids.index(t) for t in self.ids if fam in f.pais(t,cat.temas)] for fam in cat.familias]

    def vetor(self,texto):
        h=hash_texto(texto)
        if h not in self.vec:raise ValueError('Texto sem embedding preparado. Prepare e versione novo cache antes da inferência.')
        return np.asarray(self.vec[h],dtype=float)

    def agregar(self,s):
        # Um pai representa o ramo; os IDs homônimos permanecem separados.
        return np.asarray([.75*max(s[ms])+.25*float(np.mean(sorted(s[ms],reverse=True)[:3])) for ms in self.membros])

    def bm25(self,texto):
        ts=Counter(w for w in tokens(texto) if w not in CONECTORES);out=np.zeros(len(self.ids));n=len(self.ids)
        for w in ts:
            if w not in self.df:continue
            idf=math.log(1+(n-self.df[w]+.5)/(self.df[w]+.5));tf=np.asarray([d[w] for d in self.bdocs])
            out+=idf*tf*2.2/(tf+1.2*(.25+.75*self.dl/max(self.avg,1)))
        return out

    def preparar(self,qs):
        out={}
        for i,q in qs.items():
            vs,tr=vistas(q,self.ex,self.det);full,focus=vs['integral'],vs['foco']
            qf,qc=self.vetor('query: '+full),self.vetor('query: '+focus)
            sf=self.agregar(self.eq@qf);sc=self.agregar(self.eq@qc);sp=self.agregar(self.ep@(.5*qf+.5*qc))
            texts=[' '.join(tokens(t)) for t in [full,focus]]
            w=(self.w.transform(texts)@self.wd.T).toarray();c=(self.c.transform(texts)@self.cd.T).toarray()
            ww=self.agregar(.5*w[0]+.5*w[1]);cc=self.agregar(.5*c[0]+.5*c[1]);bm=self.agregar(self.bm25(focus))
            sem=.5*sf+.5*sc;lex=.5*normal(ww)+.2*normal(cc)+.3*normal(bm)
            ranks={'lexical_bm25':lex,'e5_query':sem,'e5_passage':sp,'hibrido_25':.75*normal(lex)+.25*normal(sem),'hibrido_50':.5*normal(lex)+.5*normal(sem)}
            posw=np.zeros(len(lex));poss=np.zeros(len(lex))
            for j,k in enumerate(f.ordenar(lex)):posw[k]=1/(j+1)
            for j,k in enumerate(f.ordenar(sem)):poss[k]=1/(j+1)
            refs=self.cat.referencias.extrair(full);apoio=np.asarray([self.cat.referencias.apoio(refs,t,self.cat.temas) for t in self.cat.familias])
            x=np.column_stack([ww,cc,bm,sf,sc,sp,lex-max(lex),sem-max(sem),posw,poss,apoio])
            cand=sorted(set(int(k) for s in ranks.values() for k in f.ordenar(s)[:5]))
            out[i]={'x':x,'ranks':ranks,'candidatos':cand,'hash':f.campos(q)['hash'],'trace':tr,'textos_sha256':{n:hash_texto(t) for n,t in vs.items()}}
        return out


def ajustar(pp,ys,cat):
    if not pp or set(pp)!=set(ys):raise ValueError('Treino e rótulos divergentes.')
    xx=[];yy=[];ww=[];cont=Counter(p['hash'] for p in pp.values())
    for i,p in pp.items():
        positivos=[k for k,t in enumerate(cat.familias) if f.aceito(t,ys[i],cat.temas)]
        ks=sorted(set(positivos)|set(p['candidatos']))
        xx.extend(p['x'][ks]);yy.extend(int(k in positivos) for k in ks);ww.extend([1/(len(ks)*cont[p['hash']])]*len(ks))
    return f.ajustar_linear(xx,yy,ww,balancear=True)


def sinais(pp,mod,cat,variante):
    out=[]
    for i,p in pp.items():
        es=a.escore_linear(p['x'],mod)
        if variante=='comparador':
            k=max(p['candidatos'],key=lambda k:(es[k],-k));rank=sorted(p['candidatos'],key=lambda k:(-es[k],k));scores=es
        else:
            scores=p['ranks'][variante];rank=list(map(int,f.ordenar(scores)));k=rank[0]
        empate=len(rank)>1 and abs(float(scores[k]-scores[rank[1]]))<1e-10
        out.append({'id':i,'tema_central_id':cat.familias[k],'sinal':float(es[k]),'elegivel':not empate,
                    'motivos_bloqueio':'empate_entre_candidatos' if empate else '',
                    'top5_ids':';'.join(cat.familias[j] for j in rank[:5]),'variante':variante})
    return out


def pacote(pp,ys,cat,v,internas,mod=None):
    cal=a.calibrar(internas);cs=a.confiancas(internas,cal)
    return {'modelo':mod or ajustar(pp,ys,cat),'calibrador':cal,'politica':a.politica(internas,cs),'atributos':NOMES}


def aplicar(pp,pack,cat,v):
    if pack['atributos']!=NOMES:raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,pack['modelo'],cat,v);cs=a.confiancas(ss,pack['calibrador']);out=[]
    for r,c in zip(ss,cs):
        d=f.decidir(r,float(c),pack['politica']);out.append({**r,'confianca':float(c),'decisao':d,'motivo':'' if d=='publicar' else r['motivos_bloqueio'] or ('abaixo_do_limiar_calibrado' if pack['politica']['ativa'] else 'sem_politica_com_suporte')})
    return out
