"""Regras sem rótulos, IDs de questões, respostas resolvidas ou LLM.

Publicação por regra é uma HIPÓTESE sob avaliação; não garantia de 95%.
Os parâmetros são fixados antes da execução, sem busca nas 559 questões.
"""
import re
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import lexico, sem_acento
from mescla_marcadores_v7.texto import rotear, foco, conteudo_especifico, alternativas_tematicas

VARIANTES = ('titulos_diretos', 'relacoes_diretas', 'relacoes_alternativas')
PESO_CONTEXTO = .60
PESO_ALTERNATIVAS = .40
MARGEM_RELATIVA_MINIMA = .15
# Títulos homógrafos de palavras usadas como conectores/referentes comuns.
# Refinamento posterior à rodada 1, documentado; não é resultado cego novo.
TITULOS_GENERICOS_ISOLADOS = {'conduta', 'resultado'}
QUALIFICADORES_ESPECIFICOS = {
    'conduta': [
        r'\b(?:a respeito|acerca) das? teorias? da conduta\b',
        r'\bsobre as? teorias? da conduta\b',
        r'\b(?:o conceito de conduta|a conduta humana voluntaria) (?:como|enquanto) elemento do fato tipico\b',
    ],
    'resultado': [
        r'\b(?:a respeito|acerca) do resultado naturalistico (?:do crime|no fato tipico)\b',
        r'\bsobre o resultado naturalistico (?:do crime|no fato tipico)\b',
        r'\bo resultado (?:naturalistico|juridico|normativo) (?:como|enquanto) elemento do fato tipico\b',
    ],
}
RELACAO = re.compile(
    r'\b(?:a respeito (?:dos|das|do|da|de)|acerca (?:dos|das|do|da|de)|sobre|'
    r'quanto (?:aos|as|ao|a)|(?:em|com) relacao (?:aos|as|ao|a)|'
    r'no que (?:se refere|diz respeito|concerne|tange) (?:aos|as|ao|a)|'
    r'no tocante (?:aos|as|ao|a)|referentes? (?:aos|as|ao|a))\b')


class Identificador:
    def __init__(self, cat, dicionario):
        self.cat = cat
        self.dicionario = dicionario
        self.indice = {t: n for n, t in enumerate(cat.familias)}
        self.titulos = []
        for tid, tema in cat.temas.items():
            if not f.elegivel(tid, cat.temas):
                continue
            familia = tema['parent_id'] if tema['nivel'] == 2 else tid
            partes = [tema['titulo']]
            if ':' in tema['titulo']:
                partes.append(tema['titulo'].split(':')[-1])
            for texto in partes:
                normal = f.normalizar(texto)
                normal = re.sub(r'^(?:dos|das|do|da)\s+', '', normal)
                if len(normal) >= 5 and conteudo_especifico(normal) and normal not in TITULOS_GENERICOS_ISOLADOS:
                    self.titulos.append((re.compile(r'(?<!\w)' + re.escape(normal) + r'(?!\w)'), familia, tid))
                elif normal in QUALIFICADORES_ESPECIFICOS:
                    for padrao in QUALIFICADORES_ESPECIFICOS[normal]:
                        self.titulos.append((re.compile(padrao), familia, tid))

    def encontrar(self, texto):
        normal = f.normalizar(f.visivel(texto))
        hits = []
        for padrao, familia, tid in self.titulos:
            for m in padrao.finditer(normal):
                hits.append({'expressao': m.group(), 'familia': familia, 'tema': tid, 'fonte': 'titulo'})
        _, outros = self.dicionario.encontrar(texto)
        for h in outros:
            hits.extend({'expressao': h['expressao_encontrada'], 'familia': t,
                         'tema': '', 'fonte': 'vocabulario_v8'} for t in h['familias'])
        return sorted({h['familia'] for h in hits}), hits

    def referencias(self, q):
        # Cada referência é registrada: a última com candidato é preferida.
        # É uma heurística de proximidade da cobrança, não análise sintática geral.
        texto = f.visivel(q.get('enunciado_html', ''))
        norm = sem_acento(texto)
        refs = []
        for m in RELACAO.finditer(norm):
            trecho = norm[m.end():m.end()+400]
            trecho = re.split(r'[,\n.!?;:]|\b(?:julgue|assinale|analise|marque|selecione)\b', trecho, maxsplit=1)[0].strip(' ,')
            if trecho:
                fs, hits = self.encontrar(trecho)
                refs.append({'marcador': m.group(), 'trecho': trecho, 'familias': fs, 'hits': hits})
        # Reutiliza a retomada de "essa conduta", "a prática", "como sendo".
        # "considerando" não é marcador em nenhum dos dois extratores.
        for ref in foco(q, self.cat.temas)['referencias']:
            if ref['aceito'] and ref['tipo'] != 'complemento':
                fs, hits = self.encontrar(ref['trecho'])
                refs.append({'marcador': ref['marcador'], 'trecho': ref['trecho'], 'familias': fs, 'hits': hits})
        return refs

    def similaridades(self, texto):
        if not texto.strip():
            return f.np.zeros(len(self.cat.familias))
        t = lexico(texto, self.cat.aliases)
        w = (self.cat.escopo_palavras.transform([t]) @ self.cat.ew.T).toarray()[0]
        c = (self.cat.escopo_caracteres.transform([t]) @ self.cat.ec.T).toarray()[0]
        docs = .7*w + .3*c
        return f.np.asarray([max(docs[js]) for js in self.cat.membros])

    def analisar(self, q):
        efetiva, rota = rotear(q, self.cat.temas)
        texto = efetiva.get('enunciado_html', '')
        candidatos, hits = self.encontrar(texto)
        refs = self.referencias(efetiva)
        uteis = [r for r in refs if r['familias']]
        escolhida = uteis[-1] if uteis else None
        candidatos_rel = escolhida['familias'] if escolhida else candidatos
        contexto = escolhida['trecho'] if escolhida else texto
        alts_tematicas = alternativas_tematicas(efetiva)
        alt_scores = [self.similaridades(a) for a in efetiva['alternativas'].values()] if alts_tematicas else []
        apoio_alt = f.np.mean(alt_scores, axis=0) if alt_scores else f.np.zeros(len(self.cat.familias))
        apoio_contexto = self.similaridades(contexto)
        votos_alt = []
        if alts_tematicas:
            for a in efetiva['alternativas'].values():
                votos_alt.append(self.encontrar(a)[0])
        # Uma média das alternativas fornece evidência, não resolve o gabarito.
        composto = PESO_CONTEXTO*apoio_contexto + PESO_ALTERNATIVAS*apoio_alt
        resultado = {'rota': rota, 'hits_enunciado': hits, 'referencias': refs,
                     'referencia_preferida': escolhida, 'candidatos_iniciais': candidatos,
                     'candidatos_relacoes': candidatos_rel, 'alternativas_tematicas': alts_tematicas,
                     'candidatos_por_alternativa': votos_alt, 'variantes': {}}
        for nome in VARIANTES:
            cs = candidatos if nome == 'titulos_diretos' else candidatos_rel
            escolhido = cs[0] if len(cs) == 1 else None
            motivo = 'identificador_unico' if escolhido else 'sem_identificador' if not cs else 'ambiguidade'
            margem = None
            comparacao = []
            if nome == 'relacoes_alternativas' and len(cs) > 1:
                # Só desempata caminhos acionados pela MESMA expressão.
                # Citações a furto e denúncia são assuntos diferentes, não
                # versões homônimas de um único identificador.
                hs = escolhida['hits'] if escolhida else hits
                por_expressao = {}
                for h in hs:por_expressao.setdefault(h['expressao'], set()).add(h['familia'])
                ambiguo_mesmo_identificador = any(set(cs) <= fs for fs in por_expressao.values())
                comparacao = sorted([{'tema': t, 'contexto': float(apoio_contexto[self.indice[t]]),
                    'alternativas': float(apoio_alt[self.indice[t]]),
                    'media_ponderada': float(composto[self.indice[t]])} for t in cs],
                    key=lambda r: (-r['media_ponderada'], r['tema']))
                a, b = comparacao[:2]
                margem = (a['media_ponderada']-b['media_ponderada']) / max(a['media_ponderada'], 1e-12)
                if ambiguo_mesmo_identificador and a['media_ponderada'] > 0 and margem >= MARGEM_RELATIVA_MINIMA:
                    escolhido, motivo = a['tema'], 'desambiguacao_textual'
                elif not ambiguo_mesmo_identificador:
                    motivo = 'assuntos_distintos_sem_desempate_automatico'
            resultado['variantes'][nome] = {'tema_regra': escolhido, 'acionou': escolhido is not None,
                'motivo': motivo, 'candidatos': cs, 'margem': margem, 'comparacao': comparacao}
        return resultado
