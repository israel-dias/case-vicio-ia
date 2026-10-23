"""Hipótese linguística geral: extrair referências somente do enunciado.

Não resolve questões, não recebe rótulos e não certifica um tema. A retomada
de uma conduta usa apenas citação próxima ou janela textual; não é um parser
semântico capaz de resolver toda anáfora da língua portuguesa.
"""
import re
import unicodedata

from compatibilidade_v2.features import visivel


def sem_acento(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s.lower())
                   if not unicodedata.combining(c))


MARCADOR = re.compile(
    r'\b(?:no que (?:se refere|diz respeito)\s+(?:a|ao|aos|as)|'
    r'a respeito\s+(?:de|do|da|dos|das)|em relacao\s+(?:a|ao|aos|as)|'
    r'referentes?\s+(?:a|ao|aos|as)|considerando(?:-se)?|como sendo|'
    r'(?:a|essa|esta|dessa|desta)\s+(?:pratica|conduta))\b')
INSTRUCAO = re.compile(r',?\s*\b(?:julgue|assinale|analise|marque|selecione)\b')
FIM = re.compile(r'[;:!?]|\.(?=\s+[A-ZÀ-Ú]|\s*$)')
ANAFORA = re.compile(r'\b(?:essa|esta|dessa|desta|da|a)\s+(?:pratica|conduta)\b')


def extrair(q):
    texto = re.sub(r'\s+', ' ', visivel(q.get('enunciado_html', ''))).strip()
    normal = sem_acento(texto)
    refs = []
    for m in MARCADOR.finditer(normal):
        depois = texto[m.end():m.end()+320]
        # Instrução termina o trecho introduzido. Uma vírgula dentro de uma
        # descrição de conduta não termina automaticamente a referência.
        fim = FIM.search(depois)
        if fim:
            depois = depois[:fim.start()]
        instrucao = INSTRUCAO.search(sem_acento(depois))
        if instrucao:
            depois = depois[:instrucao.start()]
        depois = depois.strip(' ,.-–')
        retomada = ''
        if ANAFORA.fullmatch(m.group()):
            anterior = texto[max(0, m.start()-450):m.start()]
            citacoes = re.findall(r'[“"‘]([^”"’]{12,400})[”"’]', anterior)
            if citacoes:
                retomada = citacoes[-1]
            else:
                # Janela, sem presumir que o antecedente foi resolvido.
                partes = re.split(r'(?<=[.!?])\s+', anterior)
                retomada = next((p.strip() for p in reversed(partes) if p.strip()), '')
        trecho = ' '.join(x for x in [retomada, depois] if x).strip()
        refs.append({'marcador': texto[m.start():m.end()], 'inicio': m.start(),
                     'trecho': trecho, 'retomada_textual': bool(retomada),
                     'limite_janela': len(depois) >= 310})
    trechos = list(dict.fromkeys(r['trecho'] for r in refs if r['trecho']))
    return {'marcadores': refs, 'texto_foco': ' '.join(trechos),
            'presente': bool(refs), 'origem': 'enunciado_html exclusivamente'}
