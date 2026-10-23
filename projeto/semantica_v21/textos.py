"""Vistas textuais sem rótulos, gabaritos, IDs ou metadados de origem."""
import hashlib
from compatibilidade_v2 import features as f
from contexto_v18.foco_morfologico import Extrator, IdentificadoresMorfologicos
from roteamento_v14.texto import limpar


def hash_texto(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def vistas(q, extrator, detector):
    nova,registro=extrator.extrair(q)
    en=limpar(q.get('enunciado_html',''));cmd=limpar(q.get('comando',''))
    alts=[limpar(q['alternativas'][k]) for k in sorted(q['alternativas'])]
    ce=set(map(f.normalizar,alts)) <= {'certo','errado','verdadeiro','falso'}
    partes=[en]
    if cmd and f.normalizar(cmd) not in f.normalizar(en):partes.append(cmd)
    if not ce:partes.extend(alts)
    completo='\n'.join(partes)
    d=detector.analisar(nova)
    if d['forte'] and nova.get('comando'):
        foco='\n'.join([limpar(nova['comando']),*([] if ce else alts)])
        origem='comando_identificado_com_alternativas'
    elif registro.get('cabecalho_geral_separado'):
        foco='\n'.join([limpar(nova.get('enunciado_html','')),limpar(nova.get('comando','')),*([] if ce else alts)])
        origem='assertiva_sem_lista_introdutoria'
    else:
        foco=completo;origem='integral_preservado'
    if not completo.strip() or not foco.strip():raise ValueError('Texto vazio.')
    return {'integral':completo,'foco':foco}, {'origem':origem,'extracao':registro,'certo_errado':ce}


def documentos(cat,propostas):
    return {t:cat.temas[t]['titulo']+'. '+propostas[t]['descricao_proposta'] for t in cat.ids}
