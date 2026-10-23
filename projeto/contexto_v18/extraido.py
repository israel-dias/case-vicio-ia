"""Adaptador de preparação; mantém controle original e testa cobrança extraída."""
from compatibilidade_v2 import features as f
from roteamento_v15 import modelo as v15
from . import modelo as original
from .extracao import extrair

VARIANTES=('controle_fusao','comando_estrito','passagens_apoio')
ATRIBUTOS={v:original.ATRIBUTOS[v] for v in VARIANTES}
ajustar=original.ajustar
sinais=original.sinais
pacote=original.pacote
aplicar=original.aplicar


def preparar(cat,dic,qs):
    novas={};registros={}
    for i,q in qs.items():novas[i],registros[i]=extrair(q)
    pp=original.preparar(cat,dic,novas)
    controle=v15.preparar(cat,dic,qs)['fusao_contextual']
    for i,p in controle.items():
        pp['controle_fusao'][i]={**pp['controle_fusao'][i],**p,
            'candidatos':[int(k) for k in f.ordenar(p['ranking'])[:5]],'excluiu_narrativa':False}
    for v in VARIANTES:
        for i,p in pp[v].items():
            p['hash']=f.campos(qs[i])['hash']
            p['extracao_comando']=registros[i]
            if v=='controle_fusao':
                # O detector nas outras opções pode acionar pela preparação,
                # mas a recuperação/atributos deste controle são os originais.
                p['extracao_comando']={**registros[i],'aplicada_no_controle':False}
    return {v:pp[v] for v in VARIANTES}


def escolher(pacotes,internas):
    return max(VARIANTES,key=lambda v:(pacotes[v]['politica']['suporte_interno'],
                                      sum(int(r['correto']) for r in internas[v]),-VARIANTES.index(v)))
