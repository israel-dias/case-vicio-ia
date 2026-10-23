"""Leitura contextual: marcadores orientam campos, nunca certificam um tema."""
import re
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import sem_acento
from mescla_marcadores_v7.texto import alternativas_tematicas, GENERICOS
from roteamento_v14.texto import Leitor as LeitorAnterior, limpar, separar_itens

# Não há limite de caracteres, regra por ID ou resolução de alternativa.
REFERENCIA = re.compile(r'\b(?:procediment\w*|etapa\w*|mencionad\w*|descrit\w*|'
    r'narrad\w*|referid\w*|situacao|caso|disposicoes|essa|esse|isso|dessa|desse)\b')
TOPICAL = re.compile(r'^(?:a luz|a respeito|sobre|acerca|quanto|no que|no tocante|'
    r'em relacao|com relacao|segundo|conforme|de acordo)\b')
VAZIAS = GENERICOS | set('''apenas somente todas todos nenhum nenhuma cada exemplo
    quantidade quantidade certos certas certa certo quantidade julgar classificar
    analisem analisando proposicoes analise total luz preencha lacuna lacunas
    resposta respostas explique explicar indicando indique narrado narrada
    mencionadas mencionados descrito descrita descritos descritas isso essa esse
    frase fato fatos hipotetica hipotetico hipotese conteudo caso casos
    procedimento procedimentos etapa etapas complete preencher'''.split())
NUMEROS_NORMA = re.compile(r'\b(?:lei|artigo|art|decreto|resolucao)\b\s*'
    r'(?:(?:n|numero)\s*)?[\d.º°o/\-]+')

def substantivos_textuais(texto):
    """Resíduo textual informativo; heurística, não análise sintática completa."""
    return [w for w in f.normalizar(texto).split()
            if w not in VAZIAS and not w.isdigit() and len(w)>2]

def apenas_referencia_normativa(texto):
    texto=NUMEROS_NORMA.sub(' ',sem_acento(texto))
    sobra=[w for w in substantivos_textuais(texto)
           if w not in {'segundo','siga','cod','paragrafo','inciso','ordenamento','juridico'}]
    return not sobra

class Leitor(LeitorAnterior):
    def informatividade(self,texto):
        tokens=substantivos_textuais(texto)
        ids=list(self.identificadores(texto))
        norma=self.norma_comando(texto)
        so_norma=bool(norma and apenas_referencia_normativa(texto))
        relacao=bool(TOPICAL.search(sem_acento(texto)))
        # Uma introdução curta com delimitador temático não é removida.
        # Uma narrativa longa também pode estabelecer o objeto dos itens.
        informativo=bool(not so_norma and (ids or len(tokens)>=3 or relacao and len(tokens)>=2))
        return {'informativo':informativo,'identificadores':ids,
                'referencia_normativa':norma,'somente_norma':so_norma,
                'delimitador_tematico':bool(relacao and len(tokens)>=2),
                'termos_informativos':tokens,
                'motivo':'conteudo_contextual' if informativo else 'referencia_normativa_dependente' if so_norma else 'instrucao_generica'}

    def rotear(self,q,literal=False):
        en=limpar(q.get('enunciado_html',''));cmd=limpar(q.get('comando',''))
        alts=[limpar(v) for _,v in sorted(q.get('alternativas',{}).items())]
        ce=bool(alts and set(f.normalizar(a) for a in alts)<= {'certo','errado','verdadeiro','falso','sim','nao'})
        tematicas=alternativas_tematicas(q) and not ce
        blocos=separar_itens(q.get('enunciado_html',''));itens=blocos['itens']
        cab=blocos['cabecalho'];info=self.informatividade(cab)
        cmdinfo=self.informatividade(cmd)
        explique=bool(re.search(r'\bexplique\b',sem_acento(cmd)))
        retomada=bool(REFERENCIA.search(sem_acento(cmd)))
        ligado=bool(retomada and (explique or not cmdinfo['informativo']))
        # A referência à lei é preservada no texto em que foi citada; nunca
        # substitui o conteúdo por uma string sintetizada de artigo ou lei.
        normcmd=self.norma_comando(cmd)
        usarcmd=bool(cmd and (cmdinfo['informativo'] or normcmd or retomada))
        cmdusado=cmd if usarcmd and f.normalizar(cmd) not in f.normalizar(en) else ''
        enusado=cab if itens else en
        if itens and not info['informativo']:
            # Só instruções genéricas são omitidas. Número de caracteres não
            # aumenta/diminui confiança e não elimina uma situação concreta.
            enusado=''
        modo='itens_contextuais' if itens else 'explique_retomada' if explique and retomada else 'explique_contextual' if explique else 'ce_contextual' if ce else 'comando_contextual' if cmdinfo['informativo'] else 'conjunto_contextual'
        rota={'en_usado':enusado,'cmd_usado':cmdusado,
              'alts_usadas':alts if tematicas else [],'itens_usados':list(itens),
              'itens_originais':list(itens),'cabecalho':cab,'modo':modo,
              'comando_identificadores':cmdinfo['identificadores'],
              'alvos_forcados':[],'itens_escolhidos':list(range(len(itens))),
              'votos_itens':[],'certo_errado':ce,'alternativas_tematicas':tematicas,
              'explique':explique,'comando_retoma_enunciado':ligado,
              'norma_sem_contexto':cmdinfo['somente_norma'],
              'comando_tematico':bool(cmdinfo['informativo'] and not cmdinfo['somente_norma'] and not ligado),
              'cabecalho_info':info,'cabecalho_prioritario':bool(itens and info['informativo']),
              'primeiro_item_fallback':False,'maioria_aplicada':False,'sem_evidencia':False}
        rota['texto_efetivo']=' '.join([enusado,cmdusado,*itens,*rota['alts_usadas']]).strip()
        # Um comando sem identificador não obriga revisão se o enunciado
        # fornece evidência. O inverso também vale: uma lei sozinha não basta.
        conteudo=' '.join([enusado,*itens,*rota['alts_usadas']])
        rota['sem_evidencia']=not bool(substantivos_textuais(conteudo) or cmdinfo['informativo'])
        if not rota['texto_efetivo']:rota['texto_efetivo']=en+' '+cmd
        return rota
