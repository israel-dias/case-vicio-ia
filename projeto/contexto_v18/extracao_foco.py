"""Distingue preâmbulo de vários assuntos da cobrança efetiva."""
import re
from compatibilidade_v2 import features as f
from roteamento_v14.texto import limpar,separar_itens
from .texto import Identificadores
from .extracao import extrair as extrair_anterior,GENERICOS

RELACAO=re.compile(r'\b(?:acerca de|a respeito de|em relacao a|sobre)\b')
INSTRUCAO=re.compile(r'\b(?:julgue|assinale|marque|selecione|indique|identifique)\b')


class Extrator:
    def __init__(self,cat):
        self.cat=cat;self.det=Identificadores(cat)

    def lista_geral(self,texto):
        norm=f.normalizar(texto)
        if not INSTRUCAO.search(norm):return False
        m=RELACAO.search(norm)
        if not m:return False
        # Pontuação da lista original, depois da expressão de relação.
        acento=limpar(texto).lower()
        pos=re.search(r'\b(?:acerca de|a respeito de|em rela[çc][ãa]o [aà]|sobre)\b',acento)
        trecho=acento[pos.end():] if pos else acento
        d=self.det.analisar({'comando':texto,'enunciado_html':''})
        familias={h['familia'] for h in d['hits']}
        classes={'crime','crimes','pena','penas','instituto','institutos','imputabilidade'}
        enumera=trecho.count(',')>=2 and bool(classes & set(norm.split()))
        varios=len(familias)>=2 and trecho.count(',')>=1 and bool(re.search(r'\be\b',f.normalizar(trecho)))
        return enumera or varios

    def extrair(self,q):
        cmd=limpar(q.get('comando',''));en=limpar(q.get('enunciado_html',''))
        if f.normalizar(cmd) not in GENERICOS or separar_itens(q.get('enunciado_html',''))['itens']:
            nova,r=extrair_anterior(q)
            return nova,{**r,'cabecalho_geral_separado':'','lista_sem_cobranca_especifica':False}
        starts=[0]+[m.end() for m in re.finditer(r'(?<=[.!?;])\s+(?=[A-ZÀ-Ú])',en)]
        fim=starts[1] if len(starts)>1 else len(en)
        primeiro=en[:fim].strip()
        if not self.lista_geral(primeiro):
            nova,r=extrair_anterior(q)
            return nova,{**r,'cabecalho_geral_separado':'','lista_sem_cobranca_especifica':False}
        resto=en[fim:].strip()
        refs=self.cat.referencias.extrair(primeiro)
        if not resto or refs['normas'] or refs['artigos']:
            # Sem assertiva seguinte não há um tema principal determinado.
            # Uma referência legal no cabeçalho também pode ser necessária.
            return dict(q),{'extraido':False,'origem':'lista_multitematica_mantida_sem_prioridade',
                            'trecho':'','enunciado_original':en,'cabecalho_geral_separado':'',
                            'lista_sem_cobranca_especifica':not bool(resto),
                            'referencia_normativa_preservada':bool(refs['normas'] or refs['artigos'])}
        limpa={**q,'enunciado_html':resto}
        nova,r=extrair_anterior(limpa)
        return nova,{**r,'origem':'preambulo_geral_separado/'+r['origem'],
                     'enunciado_original':en,'cabecalho_geral_separado':primeiro,
                     'lista_sem_cobranca_especifica':False}
