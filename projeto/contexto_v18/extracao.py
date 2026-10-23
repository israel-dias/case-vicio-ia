"""Separa cobrança explícita embutida no enunciado, sem escolher um tema."""
import re
from compatibilidade_v2 import features as f
from roteamento_v14.texto import limpar,separar_itens

GENERICOS={'','assinale a alternativa correta','assinale a alternativa incorreta',
           'assinale a opcao correta','marque a alternativa correta','julgue o item',
           'julgue o item a seguir','julgue a assertiva','julgue os itens',
           'julgue a assertiva apresentada na situacao hipotetica'}
INSTRUCAO=re.compile(r'\b(?:assinale|marque|selecione|indique|identifique|julgue|responda)\b',re.I)
PERGUNTA=re.compile(r'\b(?:qual|quais|como|quando|quem|quantos|quantas|o que|em que)\b',re.I)


def extrair(q):
    cmd=limpar(q.get('comando',''));en=limpar(q.get('enunciado_html',''))
    registro={'extraido':False,'origem':'campo_comando_preservado','trecho':'','enunciado_original':en}
    if f.normalizar(cmd) not in GENERICOS:
        return dict(q),registro
    if separar_itens(q.get('enunciado_html',''))['itens']:
        return dict(q),{**registro,'origem':'itens_independentes_preservados'}
    # Inícios de frases; não fraciona "art. 20".
    starts=[0]+[m.end() for m in re.finditer(r'(?<=[.!?;])\s+(?=[A-ZÀ-Ú])',en)]
    escolhida=None
    for j,start in enumerate(starts):
        fim=starts[j+1] if j+1<len(starts) else len(en)
        s=en[start:fim]
        if INSTRUCAO.search(s):
            escolhida=start
    if escolhida is not None:
        origem='instrucao_embutida'
    elif en.endswith('?') and PERGUNTA.search(en[starts[-1]:]):
        escolhida=starts[-1];origem='pergunta_final'
    else:
        alts=[f.normalizar(limpar(x)) for x in q.get('alternativas',{}).values()]
        if len(starts)==1 and alts and set(alts)<={'certo','errado','verdadeiro','falso'}:
            escolhida=0;origem='assertiva_ce_unica'
    if escolhida is None:
        return dict(q),{**registro,'origem':'sem_cobranca_explicita_extraivel'}
    restante=en[:escolhida].strip();trecho=en[escolhida:].strip()
    if not trecho:return dict(q),registro
    # O trecho é removido da narrativa: uma lei citada uma vez não vira
    # artificialmente uma citação compartilhada entre dois campos.
    nova={**q,'enunciado_html':restante,'comando':trecho}
    return nova,{**registro,'extraido':True,'origem':origem,'trecho':trecho,
                 'narrativa_restante':restante,'texto_integral_transferido':not restante}
