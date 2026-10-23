"""Identificadores preparados do catálogo e janelas textuais rastreáveis."""
import re
from collections import Counter
from compatibilidade_v2 import features as f
from roteamento_v15.texto import Leitor, substantivos_textuais
from roteamento_v14.texto import limpar, separar_itens

GENERICOS = set('''a o os as de da do das dos e em no na nos nas para por um uma
com sem sobre quanto relacao respeito acerca explique assinale alternativa correta
incorreta marque julgue item itens afirmativa assertiva proposicao seguintes
direito penal processo crime crimes pena penas lei artigo artigos codigo
teoria teorias geral gerais conceito conceitos especie especies estudo introducao
conduta resultado objeto objeto juridico juridica autor autores pessoa pessoas
questao questoes caso situacao hipotetica hipotetico'''.split())
ISOLADOS_AMBIGUOS = set('''acao conduta resultado objeto autor pessoa competencia
recurso comunicacao prova trabalho efeito concurso erro principio sistema
infracao classificacao punicao execucao pena crime lei codigo estatuto'''.split())


def singular(w):
    # Somente flexões superficiais de plural; não é lematização jurídica.
    if w.endswith('oes') and len(w) > 5:
        return w[:-3]+'ao'
    if w.endswith('ais') and len(w) > 4:
        return w[:-3]+'al'
    if w.endswith('es') and len(w) > 4 and w[-3] in 'rz':
        return w[:-2]
    if w.endswith('s') and len(w) > 4:
        return w[:-1]
    return w


def tokens(texto):
    return [singular(w) for w in f.normalizar(limpar(texto)).split()]


class Identificadores:
    def __init__(self, cat):
        self.cat = cat
        self.indices = {t: k for k, t in enumerate(cat.familias)}
        self.titulos = []
        freq = Counter()
        for tid in cat.ids:
            tema = cat.temas[tid]
            familia = tema['parent_id'] if tema['nivel'] == 2 else tid
            palavras = tuple(dict.fromkeys(w for w in tokens(tema['titulo']) if w not in GENERICOS and len(w)>2))
            # "Autores e Partícipes" precisa conservar ambos os papéis,
            # embora "autor" sozinho seja genérico.
            orig = set(tokens(tema['titulo']))
            if 'autor' in orig and 'participe' in orig:
                palavras = ('autor', 'participe')
            normativo = bool(re.search(r'\b(?:lei|estatuto|codigo|decreto)\b', f.normalizar(tema['titulo'])))
            self.titulos.append((tid, familia, palavras, normativo, f.normalizar(tema['titulo'])))
            freq.update(set(palavras))
        self.freq = freq

    def analisar(self, q):
        cmd = limpar(q.get('comando', ''))
        en = limpar(q.get('enunciado_html', ''))
        ts = tokens(cmd)
        hits, normativos = [], []
        for tid, fam, palavras, normativa, titulo in self.titulos:
            if not palavras or not all(w in ts for w in palavras):
                continue
            pos = [ts.index(w) for w in palavras]
            # Proximidade é da expressão, não um corte de tamanho da questão.
            if max(pos)-min(pos) > 16:
                continue
            forte = len(palavras) >= 2 or (
                palavras[0] not in ISOLADOS_AMBIGUOS and len(palavras[0]) >= 5 and self.freq[palavras[0]] <= 3
            )
            if not forte:
                continue
            h = {'tema_titulo_id': tid, 'familia': fam, 'titulo': cat_titulo(self.cat, tid),
                 'expressao': ' '.join(ts[min(pos):max(pos)+1]),
                 'forca': 1+min(3, len(palavras)), 'tipo': 'titulo_especifico'}
            if normativa:
                if titulo in f.normalizar(en):
                    normativos.append({**h, 'tipo': 'titulo_normativo_repetido'})
            else:
                hits.append(h)
        refs_c = self.cat.referencias.extrair(cmd)
        refs_e = self.cat.referencias.extrair(en)
        artigos = set(map(tuple, refs_c['artigos'])) & set(map(tuple, refs_e['artigos']))
        normas = (set(refs_c['normas']) & set(refs_e['normas'])) - {'cp', 'cpp'}
        origem = 'identificador_textual' if hits else 'referencia_normativa_repetida' if normativos or artigos or normas else 'sem_identificador_forte'
        ativos = hits if hits else normativos
        scores = f.np.zeros(len(self.cat.familias))
        for h in ativos:
            k = self.indices[h['familia']]
            scores[k] = max(scores[k], h['forca'])
        if not hits and (artigos or normas):
            refs = {'normas': sorted(normas), 'artigos': [list(x) for x in sorted(artigos)]}
            for k, fam in enumerate(self.cat.familias):
                n, a = self.cat.referencias.apoio(refs, fam, self.cat.temas)
                scores[k] = max(scores[k], float(max(n, a)))
        return {'forte': bool(ativos or max(scores)>0), 'origem': origem,
                'hits': ativos, 'scores': scores,
                'artigos_compartilhados': [list(x) for x in sorted(artigos)],
                'normas_compartilhadas': sorted(normas), 'comando': cmd}


def cat_titulo(cat, tid):
    return cat.temas[tid]['titulo']


def questao_estrita(q, identificacao):
    if not identificacao['forte']:
        return dict(q)
    # Nenhum atributo/candidato pode reutilizar narrativa ou origem neste ramo.
    return {**q, 'enunciado_html': '', 'disciplina_origem': '', 'assunto_origem': ''}


def frases(texto):
    texto = limpar(texto)
    # Não separa "art. 20", números decimais ou parágrafos da citação.
    return [s.strip() for s in re.split(r'(?<=[.!?;])\s+(?=[A-ZÀ-Ú])', texto) if s.strip()]


def passagens(q, leitor):
    rota = leitor.rotear(q)
    en = limpar(q.get('enunciado_html', ''))
    cmd = rota['cmd_usado']
    blocos = separar_itens(q.get('enunciado_html', ''))
    unidades = blocos['itens'] if blocos['itens'] else frases(en)
    if not unidades and en:
        unidades = [en]
    if blocos['itens']:
        # Toda proposição preservada; cabeçalho compartilhado acompanha cada uma.
        janelas = [' '.join([blocos['cabecalho'], x]).strip() for x in unidades]
    else:
        janelas = [' '.join(unidades[max(0,j-1):min(len(unidades),j+2)]) for j in range(len(unidades))]
    ancora = set(substantivos_textuais(cmd))
    sobreposicoes = [len(ancora & set(substantivos_textuais(s)))/max(1,len(ancora)) for s in janelas]
    # Empate preserva mais contexto por meio de duas janelas; nunca usa IDs/temas.
    escolhidos = sorted(range(len(janelas)), key=lambda j:(-sobreposicoes[j], j))[:2] if ancora else []
    ligado = ' '.join(dict.fromkeys(janelas[j] for j in escolhidos))
    if rota['comando_retoma_enunciado'] and not any(sobreposicoes):
        ligado = en
    relacionais = []
    for s in [cmd, *unidades]:
        n = f.normalizar(s)
        desconhece = re.search(r'\b(?:nao sabia|nao tinha conhecimento|sem saber|ignorava|desconhec\w*)\b', n)
        papeis = re.search(r'\b(?:autor\w*|coautor\w*)\b', n) and re.search(r'\bpartic\w*\b', n)
        if desconhece or papeis:
            relacionais.append(s)
    return {'rota': rota, 'unidades': unidades, 'janelas': janelas,
            'ligado': ligado, 'sobreposicoes': sobreposicoes,
            'texto_relacoes': ' '.join(dict.fromkeys(relacionais)),
            'relacoes': relacionais, 'itens_preservados': list(blocos['itens']),
            'certo_errado': rota['certo_errado']}
