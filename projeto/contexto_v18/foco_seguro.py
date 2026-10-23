"""Foco de cobrança com listas gerais e relações lexicais protegidas."""
import re
from compatibilidade_v2 import features as f
from roteamento_v14.texto import limpar
from roteamento_v15 import modelo as v15
from roteamento_v15.texto import Leitor
from . import modelo as original
from .texto import Identificadores, tokens, CONECTORES, questao_estrita
from .extracao_foco import Extrator as ExtratorAnterior, INSTRUCAO

VARIANTES=('controle_fusao','comando_estrito','passagens_apoio')
ATRIBUTOS={v:original.ATRIBUTOS[v] for v in VARIANTES}
ajustar=original.ajustar
sinais=original.sinais
pacote=original.pacote
aplicar=original.aplicar
RELACAO=re.compile(r'\b(?:acerca d[aeo]s?|a respeito d[aeo]s?|em relacao (?:a|as|ao|aos)|sobre)\b')
COMUNS_RELACIONAIS=set('morte agente objeto resultado autor pessoa efeito funcao cargo conduta direito trabalho'.split())


class Extrator(ExtratorAnterior):
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


def preparar(cat,dic,qs):
    ex=Extrator(cat);det=IdentificadoresSeguros(cat);leitor=Leitor(cat,dic)
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
        apoio=original.vistas(q,b,ids[i],leitor)|{'hash':hash_original,'excluiu_narrativa':False}
        for v,preparada in [('controle_fusao',p),('comando_estrito',estrito),('passagens_apoio',apoio)]:
            out[v][i]={**preparada,'extracao_comando':registros[i]}
    return out


def escolher(pacotes,internas):
    return max(VARIANTES,key=lambda v:(pacotes[v]['politica']['suporte_interno'],
                                      sum(int(r['correto']) for r in internas[v]),-VARIANTES.index(v)))
