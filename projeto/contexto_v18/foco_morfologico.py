"""Foco de cobrança com listas gerais e relações lexicais protegidas."""
import re
from compatibilidade_v2 import features as f
from roteamento_v14.texto import limpar
from roteamento_v15 import modelo as v15
from roteamento_v15.texto import Leitor
from . import modelo as original
from .texto import Identificadores, tokens, CONECTORES, questao_estrita, GENERICOS
from .extracao_foco import Extrator as ExtratorAnterior, INSTRUCAO
from .extracao import extrair as extrair_sem_separar_cabecalho

VARIANTES=('controle_fusao','comando_estrito')
ATRIBUTOS={v:original.ATRIBUTOS[v] for v in VARIANTES}
ajustar=original.ajustar
sinais=original.sinais
pacote=original.pacote
aplicar=original.aplicar
RELACAO=re.compile(r'\b(?:acerca d[aeo]s?|a respeito d[aeo]s?|em relacao (?:a|as|ao|aos)|sobre)\b')
COMUNS_RELACIONAIS=set('morte agente objeto resultado autor pessoa efeito funcao cargo conduta direito trabalho'.split())


class Extrator(ExtratorAnterior):
    def extrair(self,q):
        nova,r=super().extrair(q)
        # Marcadores V/F são proposições, mesmo quando a segmentação por
        # pontuação não reconhece a fronteira após "( )".
        antes=len(re.findall(r'\(\s*\)',limpar(q.get('enunciado_html',''))))
        depois=len(re.findall(r'\(\s*\)',limpar(nova.get('enunciado_html',''))+' '+limpar(nova.get('comando',''))))
        if depois<antes:
            nova,r=extrair_sem_separar_cabecalho(q)
            r={**r,'cabecalho_geral_separado':'','lista_sem_cobranca_especifica':False,
               'resguardo_proposicoes_vf':True}
        return nova,r

    def lista_geral(self,texto):
        norm=f.normalizar(texto)
        if not INSTRUCAO.search(norm):return False
        m=RELACAO.search(norm)
        if not m:return False
        # A pontuação é lida no original; a expressão aceita a/à/às/ao/aos.
        texto=limpar(texto)
        rel=re.search(r'\b(?:acerca d[aeo]s?|a respeito d[aeo]s?|em rela[çc][ãa]o (?:[aà]s?|aos?)|sobre)\b',texto,re.I)
        trecho=texto[rel.end():] if rel else texto
        d=self.det.analisar({'comando':texto,'enunciado_html':''})
        familias={h['familia'] for h in d['hits']}
        classes={'crime','crimes','pena','penas','instituto','institutos','imputabilidade'}
        enumera=trecho.count(',')>=2 and bool(classes & set(norm.split()))
        varios=len(familias)>=2 and trecho.count(',')>=1 and bool(re.search(r'\be\b',f.normalizar(trecho)))
        return enumera or varios


class IdentificadoresSeguros(Identificadores):
    def __init__(self,cat):
        super().__init__(cat);self.ex=Extrator(cat)

    def analisar(self,q):
        d=super().analisar(q);cmd=q.get('comando','')
        if self.ex.lista_geral(cmd):
            return {**d,'forte':False,'hits':[],'scores':f.np.zeros(len(self.cat.familias)),
                    'origem':'lista_multitematica_sem_foco','hits_nao_priorizados':d['hits']}
        sequencia=[w for w in tokens(cmd) if w not in CONECTORES]
        hits=[];rejeitados=[]
        for h in d['hits']:
            titulo=[w for w in tokens(h['titulo']) if w not in CONECTORES]
            apenas_comuns=len(titulo)>=2 and set(titulo)<=COMUNS_RELACIONAIS
            continua=any(sequencia[j:j+len(titulo)]==titulo for j in range(len(sequencia)))
            if apenas_comuns and not continua:rejeitados.append(h)
            else:hits.append(h)
        if not rejeitados:return d
        scores=f.np.zeros(len(self.cat.familias))
        for h in hits:
            k=self.indices[h['familia']];scores[k]=max(scores[k],h['forca'])
        # Não substitui a expressão recusada por inferência jurídica.
        return {**d,'forte':bool(hits),'hits':hits,'scores':scores,
                'origem':d['origem'] if hits else 'expressao_comum_sem_relacao_confirmada',
                'hits_nao_priorizados':rejeitados}


FORMAS={
    'consumado':'consumacao','consumada':'consumacao','consumacao':'consumacao',
    'tentado':'tentativa','tentada':'tentativa','tentativa':'tentativa',
    'absolvido':'absolvicao','absolvida':'absolvicao','absolvicao':'absolvicao',
    'condenado':'condenacao','condenada':'condenacao','condenacao':'condenacao',
    'extinto':'extincao','extinta':'extincao','extincao':'extincao',
    'prescrito':'prescricao','prescrita':'prescricao','prescricional':'prescricao','prescricao':'prescricao',
}


class IdentificadoresMorfologicos(IdentificadoresSeguros):
    def __init__(self,cat):
        super().__init__(cat);self.compostos=[]
        for tid in cat.ids:
            t=cat.temas[tid]
            if re.search(r'\b(?:lei|estatuto|codigo|decreto)\b',f.normalizar(t['titulo'])):continue
            orig=[w for w in tokens(t['titulo']) if w not in GENERICOS and len(w)>2]
            can=tuple(dict.fromkeys(FORMAS.get(w,w) for w in orig))
            if len(can)<2 or tuple(orig)==can:continue
            fam=t['parent_id'] if t['nivel']==2 else tid
            self.compostos.append((tid,fam,can))

    def analisar(self,q):
        d=super().analisar(q)
        if d['origem']=='lista_multitematica_sem_foco':return d
        ts=tokens(q.get('comando',''));can=[FORMAS.get(w,w) for w in ts]
        novos=[]
        for tid,fam,palavras in self.compostos:
            if not all(w in can for w in palavras):continue
            # Conserva os dois conceitos em proximidade, sem criar um tema
            # por ocorrência de um adjetivo comum isolado.
            pos=[can.index(w) for w in palavras]
            if max(pos)-min(pos)>16:continue
            novos.append({'tema_titulo_id':tid,'familia':fam,'titulo':self.cat.temas[tid]['titulo'],
                          'expressao':' '.join(ts[min(pos):max(pos)+1]),'forca':1+min(3,len(palavras)),
                          'tipo':'titulo_composto_com_flexao','formas_canonicas':list(palavras)})
        if not novos:return d
        hits=d['hits']+novos;scores=d['scores'].copy()
        for h in novos:
            k=self.indices[h['familia']];scores[k]=max(scores[k],h['forca'])
        return {**d,'forte':True,'origem':'identificador_composto_com_flexao','hits':hits,'scores':scores}


def preparar(cat,dic,qs):
    ex=Extrator(cat);det=IdentificadoresMorfologicos(cat);leitor=Leitor(cat,dic)
    novas={};registros={}
    for i,q in qs.items():novas[i],registros[i]=ex.extrair(q)
    ids={i:det.analisar(q) for i,q in novas.items()}
    controle=v15.preparar(cat,dic,qs)['fusao_contextual']
    base=v15.preparar(cat,dic,novas)['fusao_contextual']
    alteradas={i:questao_estrita(q,ids[i]) for i,q in novas.items() if ids[i]['forte']}
    mod=v15.preparar(cat,dic,alteradas)['fusao_contextual'] if alteradas else {}
    out={v:{} for v in VARIANTES}
    for i,q in novas.items():
        b=base[i];hash_original=f.campos(qs[i])['hash'];ident={k:v for k,v in ids[i].items() if k!='scores'}
        p={**controle[i],'candidatos':[int(k) for k in f.ordenar(controle[i]['ranking'])[:5]],
           'identificacao':ident,'excluiu_narrativa':False,'hash':hash_original}
        estrito={**(mod[i] if i in mod else b),'hash':hash_original,
                 'identificacao':ident,'excluiu_narrativa':i in mod}
        if i in mod:
            estrito['ranking']=.65*original.normalizar(estrito['ranking'])+.35*original.normalizar(ids[i]['scores'])
        estrito['candidatos']=original.candidato_indices((estrito['ranking'],5),(ids[i]['scores'],3))
        for v,preparada in [('controle_fusao',p),('comando_estrito',estrito)]:
            out[v][i]={**preparada,'extracao_comando':registros[i]}
    return out


def escolher(pacotes,internas):
    return max(VARIANTES,key=lambda v:(pacotes[v]['politica']['suporte_interno'],
                                      sum(int(r['correto']) for r in internas[v]),-VARIANTES.index(v)))
