"""Índice BM25 derivado apenas do catálogo e dos escopos já preparados."""
from collections import Counter,defaultdict
import re
from sklearn.feature_extraction.text import CountVectorizer
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import lexico
from mescla_marcadores_v7.texto import GENERICOS

def tokens(texto):
    return [t for t in lexico(texto,{}).split() if len(t)>2 and t not in GENERICOS and not t.isdigit()]

def compilar(cat,propostas):
    docs=[];grupos=defaultdict(list)
    for tid in cat.ids:
        t=cat.temas[tid];fam=t['parent_id'] if t['nivel']==2 else tid
        texto=' '.join([t['titulo'],propostas[tid]['descricao_proposta']])
        if re.search(r'\bQ\d{4}\b',texto):raise ValueError('ID de questão no catálogo.')
        docs.append({'tema_id':tid,'familia_id':fam,'texto':texto})
        grupos[f.normalizar(t['titulo'])].append(tid)
    hom=[{'titulo':nome,'ids':ids,'escopo_da_empresa_confirmado':False,
          'observacao':'IDs e ramos preservados; vocabulário compartilhado não prova equivalência.'}
         for nome,ids in sorted(grupos.items()) if len(ids)>1]
    return {'versao':'catalogo_bm25_v16_1','origem':'Títulos, árvore e descrições preparadas já existentes; sem questões ou rótulos.',
            'enriquecimento':'Documentos dos nós e associação explícita a seus pais para recuperação hierárquica. Nenhum novo escopo jurídico ou diferença entre homônimos foi inventado.',
            'limites_nao_indexados':True,'homonimos':hom,'documentos':docs,
            'familias':list(cat.familias),'k1':1.2,'b':.75}

class Busca:
    def __init__(self,cat,snapshot):
        self.cat=cat;self.snapshot=snapshot;docs=snapshot['documentos']
        if snapshot['familias']!=list(cat.familias):raise ValueError('Famílias incompatíveis.')
        self.cv=CountVectorizer(tokenizer=tokens,token_pattern=None,lowercase=False,ngram_range=(1,2))
        ct=self.cv.fit_transform([d['texto'] for d in docs]).astype(float)
        por_fam=[' '.join(d['texto'] for d in docs if d['familia_id']==fam) for fam in cat.familias]
        df=f.np.asarray((self.cv.transform(por_fam)>0).sum(axis=0)).ravel();n=len(cat.familias)
        idf=f.np.log1p((n-df+.5)/(df+.5));tam=f.np.asarray(ct.sum(axis=1)).ravel();media=max(float(tam.mean()),1)
        matriz=ct.tocsr(copy=True);k1=snapshot['k1'];b=snapshot['b']
        for j in range(len(docs)):
            a,z=matriz.indptr[j:j+2];tf=matriz.data[a:z]
            matriz.data[a:z]=idf[matriz.indices[a:z]]*tf*(k1+1)/(tf+k1*(1-b+b*tam[j]/media))
        self.matriz=matriz
        self.membros=[[j for j,d in enumerate(docs) if d['familia_id']==fam] for fam in cat.familias]
        if any(not js for js in self.membros):raise ValueError('Família sem documento.')
        self.cache={}
    def buscar(self,texto):
        if texto in self.cache:return self.cache[texto]
        if not texto.strip():return f.np.zeros(len(self.cat.familias))
        q=self.cv.transform([texto]).astype(float);q.data=1+f.np.log(q.data)
        s=(q@self.matriz.T).toarray()[0]
        vals=f.np.asarray([.65*max(s[js])+.35*f.np.mean(sorted(s[js],reverse=True)[:3]) for js in self.membros])
        vals=vals/max(float(max(vals)),1e-12);self.cache[texto]=vals
        return vals
