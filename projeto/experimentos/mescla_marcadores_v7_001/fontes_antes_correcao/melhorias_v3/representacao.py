"""Preparação textual e atributos gerais; não recebe rótulos oficiais."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from compatibilidade_v2 import features as f
from compatibilidade_v2.runtime import CatalogoCompatibilidade


NOMES_NOVOS = [
    'escopo_texto', 'escopo_enunciado', 'escopo_comando', 'escopo_alternativas',
    'escopo_alternativa_max', 'escopo_alternativa_media', 'titulo_enunciado',
    'norma_enunciado', 'norma_alternativas', 'artigo_enunciado', 'artigo_alternativas',
    'citacao_sem_correspondencia', 'ha_norma_explicita', 'ha_artigo_vinculado',
    'evidencia_escopo_enunciado_alt', 'posicao_busca', 'diferenca_melhor_busca',
]
NOMES = f.NOMES_BASE + NOMES_NOVOS


def artigo_ordem(valor):
    m = re.fullmatch(r'(\d+)(?:-?([a-z]))?', str(valor).lower().replace(' ', ''))
    if not m:
        raise ValueError('Artigo inválido: '+str(valor))
    return int(m[1]), ord(m[2])-96 if m[2] else 0


def sem_acento(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.lower())
                   if not unicodedata.combining(c))


def lexico(texto, aliases):
    texto = f.normalizar(f.visivel(texto))
    for antes, depois in aliases.items():
        texto = re.sub(r'\b'+re.escape(antes)+r'\b', depois, texto)
    # Flexão simples como evidência adicional, sem substituir o controle v2.
    partes=[]
    for token in texto.split():
        if len(token)>5 and token.endswith('oes'): token=token[:-3]+'ao'
        elif len(token)>4 and token.endswith('ais'): token=token[:-3]+'al'
        elif len(token)>4 and token.endswith('s') and token[-2] in 'aeiou': token=token[:-1]
        partes.append(token)
    return ' '.join(partes)


class Referencias:
    def __init__(self, dados, temas):
        self.dados = dados
        self.normas = {n['id']:n for n in dados['normas']}
        if len(self.normas)!=len(dados['normas']):
            raise ValueError('Normas repetidas.')
        self.numero = {}
        self.aliases=[]
        for n in dados['normas']:
            for numero in n['numeros']:
                if numero in self.numero: raise ValueError('Número normativo repetido.')
                self.numero[numero]=n['id']
            for alias in n['aliases']:
                self.aliases.append((sem_acento(alias),n['id']))
            for tid in n['temas_ids']:
                if not f.elegivel(tid,temas): raise ValueError('Tema normativo inválido.')
        self.aliases.sort(key=lambda x:-len(x[0]))
        self.regras=[]
        for r in dados['intervalos_artigos']:
            if r['norma'] not in self.normas or artigo_ordem(r['inicio'])>artigo_ordem(r['fim']):
                raise ValueError('Intervalo normativo inválido.')
            if any(not f.elegivel(t,temas) for t in r['temas_ids']):
                raise ValueError('Intervalo aponta para tema inválido.')
            self.regras.append((r['norma'],artigo_ordem(r['inicio']),artigo_ordem(r['fim']),r['temas_ids']))

    def normas_no_texto(self, texto):
        texto=sem_acento(f.visivel(texto)); spans=[]
        for alias,norma in self.aliases:
            for m in re.finditer(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',texto):
                if not any(m.start()<b and m.end()>a for a,b,_ in spans):
                    spans.append((m.start(),m.end(),norma))
        padrao=r'\b(?:decreto[\s-]*)?lei\s*(?:n[.oº°\s]*)?(\d[\d.]*)\s*(?:/\s*(\d{2,4})|,?\s+de\s+(\d{4}))(?!\d)'
        for m in re.finditer(padrao,texto):
            numero=m[1].replace('.','');ano=int(m[2] or m[3])
            if ano<100: ano+=1900 if ano>=30 else 2000
            chave=numero+'/'+str(ano)
            spans.append((m.start(),m.end(),self.numero.get(chave,'lei:'+chave)))
        # Caso número sem ano, só reconhecer quando inequívoco no dado preparado.
        for m in re.finditer(r'\b(?:decreto[\s-]*)?lei\s*(?:n[.oº°\s]*)?(\d[\d.]*)(?!\d)',texto):
            if any(m.start()<b and m.end()>a for a,b,_ in spans): continue
            candidatos={n for k,n in self.numero.items() if k.split('/')[0]==m[1].replace('.','')}
            if len(candidatos)==1: spans.append((m.start(),m.end(),next(iter(candidatos))))
        return texto,sorted(spans)

    def extrair(self, texto, contexto=()):
        texto,spans=self.normas_no_texto(texto)
        normas={n for _,_,n in spans}; pares=[]
        for m in re.finditer(r'\bart(?:igo)?s?\.?\s*(\d+(?:\s*[-–]\s*[a-z])?)(?:[oº°])?(?!\w)',texto):
            art=re.sub(r'\s+','',m[1]).replace('–','-')
            # "art. 155 do CPP" prevalece sobre uma menção anterior ao CP.
            conector=re.match(r'\s*(?:,\s*)?(?:(?:do|da|no|na|pelo|pela)\s+)?',texto[m.end():])
            inicio_norma=m.end()+conector.end()
            diretas={n for a,b,n in spans if a==inicio_norma}
            esquerda=max(texto.rfind(';',0,m.start()),texto.rfind('\n',0,m.start()))
            direita=texto.find(';',m.end())
            if direita<0: direita=len(texto)
            perto=sorted((min(abs(m.end()-a),abs(m.start()-b)),n) for a,b,n in spans if a>esquerda and a<direita)
            if diretas:
                ns=diretas
            elif perto and perto[0][0]<=160:
                # Empate entre normas diferentes é preservado como ambiguidade.
                ns={n for dist,n in perto if dist==perto[0][0]}
            else:
                ns=normas if len(normas)==1 else set(contexto) if not normas and len(contexto)==1 else set()
            if len(ns)==1: pares.append((next(iter(ns)),art))
        return {'normas':sorted(normas),'artigos':[list(p) for p in sorted(set(pares))]}

    def apoio(self, refs, familia, temas):
        def relacionado(t):
            return familia in f.pais(t,temas) or t in f.pais(familia,temas)
        ns=refs['normas'];arts=refs['artigos']
        leis=sum(any(relacionado(t) for t in self.normas.get(n,{}).get('temas_ids',[])) for n in ns)
        positivos=0
        for norma,art in arts:
            encontrados=set(self.normas.get(norma,{}).get('temas_ids',[]))
            for n,a,b,tids in self.regras:
                if n==norma and a<=artigo_ordem(art)<=b: encontrados.update(tids)
            positivos+=any(relacionado(t) for t in encontrados)
        return leis/max(1,len(ns)),positivos/max(1,len(arts))


class Catalogo(CatalogoCompatibilidade):
    def __init__(self, temas, propostas, configuracao, mapa):
        super().__init__(temas,propostas,configuracao)
        self.mapa=mapa
        self.referencias=Referencias(mapa,temas)
        self.aliases=mapa['normalizacao_lexical']
        docs=[];titulos=[]
        for tid in self.ids:
            t=temas[tid]
            doc=' '.join([t['titulo']]*2+[propostas[tid]['descricao_proposta']])
            docs.append(lexico(doc,self.aliases))
            titulos.append(lexico(t['titulo'],self.aliases))
        self.escopo_palavras=f.TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)
        self.escopo_caracteres=f.TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True)
        self.ew=self.escopo_palavras.fit_transform(docs)
        self.ec=self.escopo_caracteres.fit_transform(docs)
        self.tw=self.escopo_palavras.transform(titulos)

    def transformar(self, qs):
        perfis=super().transformar(qs)
        for qid,q in qs.items():
            p=perfis[qid]
            raw_en=f.visivel(q.get('enunciado_html',''))
            raw_cmd=f.visivel(q.get('comando',''))
            raw_alts=[f.visivel(q['alternativas'][k]) for k in sorted(q['alternativas'])]
            c=f.campos(q)
            en=' '.join([raw_en,raw_cmd]) if c['comando'] not in c['enunciado'] else raw_en
            context=self.referencias.extrair(en)
            ar=[self.referencias.extrair(a,context['normas']) for a in raw_alts]
            textos=[' '.join([en,*raw_alts]),en,raw_cmd,' '.join(raw_alts),*raw_alts]
            normalizados=[lexico(a,self.aliases) for a in textos]
            w=(self.escopo_palavras.transform(normalizados)@self.ew.T).toarray()
            ch=(self.escopo_caracteres.transform(normalizados)@self.ec.T).toarray()
            sim=.7*w+.3*ch
            nome=(self.escopo_palavras.transform([normalizados[1]])@self.tw.T).toarray()[0]
            ordem=f.ordenar(p['scores']);pos={int(v):i for i,v in enumerate(ordem)}
            novos=[];apoios=[]
            alt_refs={'normas':sorted({n for r in ar for n in r['normas']}),
                      'artigos':[list(a) for a in sorted({tuple(a) for r in ar for a in r['artigos']})]}
            for k,membros in enumerate(self.membros):
                def agregar(valores): return float(max(valores[membros]))
                fs=[agregar(v) for v in sim]
                n_en,a_en=self.referencias.apoio(context,self.familias[k],self.temas)
                n_alt,a_alt=self.referencias.apoio(alt_refs,self.familias[k],self.temas)
                ha_n=bool(context['normas'] or alt_refs['normas'])
                ha_a=bool(context['artigos'] or alt_refs['artigos'])
                apoio=max(n_en,n_alt,a_en,a_alt)
                # C/E não fornece conteúdo temático nas alternativas.
                alt=fs[1] if c['certo_errado'] else fs[3]
                novos.append([*fs[:4],max(fs[4:]),float(f.np.mean(fs[4:])),agregar(nome),
                              n_en,n_alt,a_en,a_alt,float(ha_n)*(1-apoio),float(ha_n),float(ha_a),
                              min(fs[1],alt),1/(1+pos[k]),float(p['scores'][k]-max(p['scores']))])
                apoios.append(apoio)
            p['features_v3']=f.np.hstack([p['features'],f.np.asarray(novos)])
            p['scores_novos']=.65*p['scores']+.25*f.np.asarray([a[0] for a in novos])+.10*f.np.asarray(apoios)
            p['refs_extraidas']={'enunciado_comando':context,'alternativas':ar}
            p['hash_v3']=p['hash']
        return perfis


def carregar_catalogo(projeto):
    from compatibilidade_v2.runtime import Runtime
    rt=Runtime(Path(projeto)/'artefatos/compatibilidade_v2')
    propostas=json.loads((Path(projeto)/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
    mapa=json.loads((Path(projeto)/'melhorias_v3/dados/referencias_normativas_v1.json').read_text())
    return Catalogo(rt.temas,propostas,rt.registro['configuracao_escopos'],mapa),rt
