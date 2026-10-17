"""Aplica o reexame assistido salvo, preservando decisões e evidências anteriores."""
import json,math
from pathlib import Path
from .arquivos import sha256

ESTADOS={'resposta_assistida_sem_gabarito_oficial_confirmado','resposta_nao_confirmada','gabarito_oficial_definitivo','gabarito_oficial_preliminar'}

def ancestral(a,b,temas):
    atual=temas[b].get('parent_id')
    while atual:
        if atual==a:return True
        atual=temas[atual].get('parent_id')
    return False

def validar_registros(registros,linhas,temas):
    originais={r['id']:r for r in linhas}
    if len(registros)!=359 or {r.get('id') for r in registros}!=set(originais):
        raise ValueError('Auditoria precisa cobrir os 359 IDs uma vez.')
    novos=[]
    for r in registros:
        i=r['id'];a=r['antes'];d=r['depois']
        if a!=originais[i]:raise ValueError('Antes da auditoria não corresponde à v3: '+i)
        if set(d)!=set(originais[i]) or d['id']!=i:raise ValueError('Contrato CSV inválido: '+i)
        if any(not isinstance(v,str) for v in d.values()):raise ValueError('Campos CSV precisam ser texto: '+i)
        if d['decisao'] not in ('publicar','revisar','fora'):raise ValueError('Decisão inválida: '+i)
        t=d['tema_central_id'];extras=d['extras_ids'].split(';') if d['extras_ids'] else []
        if (d['decisao']=='fora')!= (not t):raise ValueError('Tema central incompatível com decisão: '+i)
        if not t and extras:raise ValueError('Fora não pode receber extras: '+i)
        valores=([t] if t else [])+extras
        if len(set(valores))!=len(valores):raise ValueError('Rótulo duplicado: '+i)
        for x in valores:
            if x not in temas or temas[x]['status']!='active' or str(temas[x]['nivel'])=='0':
                raise ValueError('Tema inativo, raiz ou inexistente: '+i)
        justificativas=r.get('justificativas_extras_independentes',{})
        for x in extras:
            if ancestral(x,t,temas):raise ValueError('Extra ancestral não acrescenta subtema: '+i)
            if ancestral(t,x,temas) and len(justificativas.get(x,'').strip())<15:
                raise ValueError('Filho como extra exige conteúdo independente justificado: '+i)
        for j,x in enumerate(extras):
            for y in extras[j+1:]:
                if ancestral(x,y,temas) or ancestral(y,x,temas):
                    raise ValueError('Extras redundantes entre si: '+i)
        try:c=float(d['confianca'])
        except (ValueError,TypeError):raise ValueError('Confiança inválida: '+i)
        if not math.isfinite(c) or not 0<=c<=1 or (not t and c!=0):raise ValueError('Confiança inválida: '+i)
        if not d['motivo'].strip() or not r.get('analise_individual') or not r.get('fundamento_indicado'):
            raise ValueError('Análise ou motivo ausente: '+i)
        if r.get('estado_resposta') not in ESTADOS:raise ValueError('Estado de evidência inválido: '+i)
        resposta=r.get('resposta_proposta')
        if resposta is not None and resposta not in ('A','B','C','D','E'):raise ValueError('Resposta não é letra válida: '+i)
        g=r.get('gabarito_oficial')
        if r['estado_resposta'].startswith('gabarito_oficial'):
            if not g or g['resposta']!=resposta or g['estado']!=r['estado_resposta']:
                raise ValueError('Gabarito oficial sem suporte registrado: '+i)
        if r.get('referencia_independente_de_tema') is not False:
            raise ValueError('Gabarito da prova não é referência independente dos temas: '+i)
        novos.append(dict(d))
    return sorted(novos,key=lambda r:r['id'])

def aplicar_auditoria(projeto,linhas,intervencoes,proveniencia,fingerprints,temas):
    pasta=projeto/'auditoria_v4';mf=pasta/'manifesto_auditoria.json'
    m=json.loads(mf.read_text(encoding='utf-8'))
    for nome,esperado in m['entradas_sha256'].items():
        if Path(nome).is_absolute() or '..' in Path(nome).parts:raise ValueError('Caminho inválido no manifesto da auditoria.')
        if sha256(projeto/nome)!=esperado:raise ValueError('Entrada da auditoria alterada: '+nome)
        fingerprints[nome]=esperado
    fingerprints['auditoria_v4/manifesto_auditoria.json']=sha256(mf)
    registros=json.loads((pasta/'reexame_359.json').read_text(encoding='utf-8'))['registros']
    novos=validar_registros(registros,linhas,temas)
    for r in registros:
        i=r['id'];proveniencia[i]+='+auditoria_assistida_v4'
        intervencoes.append({'id':i,'tipo':'reexame_assistido_v4','antes':r['antes'],'depois':r['depois'],
                             'analise':r['analise_individual'],'estado_resposta':r['estado_resposta'],
                             'origem':'auditoria_v4/reexame_359.json','referencia_independente_de_tema':False})
    return novos
