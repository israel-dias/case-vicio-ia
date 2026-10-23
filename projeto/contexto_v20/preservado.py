"""Nova recuperação; atributos e estimador de confiança de 27 dimensões preservados."""
from . import modelo as m

NOME='escopos_contextuais_estimador_preservado'

def aplicar(perfis,pack,cat):
    n=len(m.ATRIBUTOS['controle_atual'])
    reduzidos={i:{**p,'x':p['x'][:,:n]} for i,p in perfis.items()}
    rr=m.aplicar(reduzidos,pack,cat,'controle_atual')
    return [{**r,'variante':NOME,'estimador_de_confianca_preservado':True} for r in rr]
