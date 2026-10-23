"""Comparação de temas com modelos clássicos e papéis textuais versionados."""
from collections import Counter
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from auditoria_confianca_v4.experimento import ajustar_linear_eficiente
from vocabulario_v8.experimento import preparar as preparar_v8
from .texto import Leitor,limpar
import re

VARIANTES={'usuario_literal':{'literal':True,'reranking':False},
    'contexto_preservado':{'literal':False,'reranking':False},
    'comparador_treinado':{'literal':False,'reranking':True},
    'fusao_conservadora':{'literal':False,'reranking':False,'fusao':True}}
COL=['palavra','caracteres','escopo','titulo','identificador','norma','artigo']
NOMES=['efetivo_'+n for n in COL]+['en_palavra','en_escopo']+['cmd_'+n for n in COL]+[
    'alt_palavra_media','alt_escopo_media','alt_escopo_max','itens_escopo_media','itens_escopo_max',
    'itens_escopo_top2','voto_itens','desconhecimento_erro','condicao_vitima_erro','vantagem_lexical','vantagem_relativa']

def preparar(cat,dic,qs):
    leitor=Leitor(cat,dic);saida={v:{} for v in VARIANTES}
    # Variante posterior à primeira rodada: conservar a recuperação legada.
    legado=preparar_v8(cat,dic,qs)
    erro=leitor.pontuar('erro')[:,0]
    for i,q in qs.items():
        if not isinstance(i,str) or q.get('id')!=i:raise ValueError('ID inconsistente.')
        perfis={}
        for literal in [True,False]:
            rota=leitor.rotear(q,literal);mat=leitor.pontuar(rota['texto_efetivo'])
            en=leitor.pontuar(rota['en_usado']);cmd=leitor.pontuar(rota['cmd_usado'])
            alts=[leitor.pontuar(t) for t in rota['alts_usadas']]
            itens=[leitor.pontuar(t) for t in rota['itens_usados']]
            zeros=f.np.zeros(len(cat.familias))
            am=f.np.mean(alts,axis=0) if alts else f.np.zeros_like(mat)
            ax=f.np.max([z[:,2] for z in alts],axis=0) if alts else zeros
            im=f.np.mean([z[:,2] for z in itens],axis=0) if itens else zeros
            ix=f.np.max([z[:,2] for z in itens],axis=0) if itens else zeros
            itop=f.np.mean(f.np.sort(f.np.asarray([z[:,2] for z in itens]),axis=0)[-2:],axis=0) if itens else zeros
            votos=Counter()
            for t in rota['itens_usados']:
                ss=leitor.ranking_texto(t)
                if max(ss)>0:votos[cat.familias[int(f.ordenar(ss)[0])]]+=1
            voto=f.np.asarray([votos[t]/max(1,len(itens)) for t in cat.familias])
            score=leitor.ranking_texto(rota['texto_efetivo']).copy()
            if not literal:
                if rota['comando_identificadores'] or rota['explique']:
                    score=.55*leitor.ranking_texto(rota['cmd_usado'])+.45*score
                elif rota['modo']=='caso_narrado' and alts:
                    score=.7*f.np.mean([leitor.ranking_texto(t) for t in rota['alts_usadas']],axis=0)+.3*leitor.ranking_texto(rota['en_usado'])
                elif itens:score=.6*score+.4*im
            if rota['alvos_forcados']:
                permitido={leitor.idx[t] for t in rota['alvos_forcados']}
                score=f.np.asarray([s if k in permitido else -1. for k,s in enumerate(score)])
            norm=limpar(rota['texto_efetivo']).lower()
            desconhece=bool(re.search(r'\b(?:desconhec\w*|ignorava|nao sabia|não sabia|nao tinha conhecimento|não tinha conhecimento)\b',norm))
            condicao=bool(re.search(r'\b(?:vitima|vítima|menoridade|idade|condicao|condição|elementar)\b',norm))
            # Contrastes são atributos; não percentuais ou vetos jurídicos.
            base=leitor.ranking_texto(rota['texto_efetivo']);ordem=f.ordenar(base);outros=f.np.full(len(base),float(base[ordem[0]]))
            if len(base)>1:outros[ordem[0]]=base[ordem[1]]
            dif=base-outros;rel=dif/f.np.maximum(f.np.maximum(base,outros),1e-12)
            x=f.np.column_stack([mat,en[:,[0,2]],cmd,am[:,0],am[:,2],ax,im,ix,itop,voto,
                int(desconhece)*erro,int(desconhece and condicao)*erro,dif,rel])
            assert x.shape==(len(cat.familias),len(NOMES))
            perfis[literal]={'x':x,'ranking':score,'rota':rota,'hash':f.campos(q)['hash'],
                'sinal_textual':base,'homonimos':leitor.homonimos}
        for v,cfg in VARIANTES.items():
            saida[v][i]=perfis[cfg['literal']]
            if cfg.get('fusao'):
                base=legado[i]['ranking_vocabulario_reordena'];novo=perfis[False]['ranking']
                score=.7*base/max(float(max(base)),1e-12)+.3*novo/max(float(max(novo)),1e-12)
                saida[v][i]={**perfis[False],'ranking':score}
    return saida

def ajustar(pp,ys,cat):
    if not pp or set(pp)!=set(ys):raise ValueError('Treino vazio ou rótulos externos.')
    cont=Counter(p['hash'] for p in pp.values());x=[];y=[];w=[]
    for i,p in pp.items():
        x.extend(p['x']);y.extend(int(f.aceito(t,ys[i],cat.temas)) for t in cat.familias)
        w.extend([1/cont[p['hash']]]*len(cat.familias))
    return ajustar_linear_eficiente(x,y,w,True)

def sinais(pp,modelo,cat,variante):
    if variante not in VARIANTES:raise ValueError('Variante desconhecida.')
    saida=[]
    for i,p in pp.items():
        escores=a.escore_linear(p['x'],modelo)
        k=int(f.ordenar(escores if VARIANTES[variante]['reranking'] else p['ranking'])[0]);t=cat.familias[k]
        ambiguo=False
        for outro in p['homonimos'][t]:
            j=cat.familias.index(outro)
            # Não desempatar títulos iguais por ordem de ID quando a evidência empata.
            if abs(float(p['sinal_textual'][k]-p['sinal_textual'][j]))<=1e-6 and abs(float(escores[k]-escores[j]))<.25:
                ambiguo=True
        valido=bool(not p['rota']['sem_evidencia'] and max(p['x'][k,0:4])>=.03 and not ambiguo)
        saida.append({'id':i,'tema_central_id':t,'sinal':float(escores[k]),'elegivel':valido,
            'homonimo_nao_resolvido':ambiguo,'modo':p['rota']['modo'],
            'primeiro_item_fallback':p['rota']['primeiro_item_fallback'],
            'maioria_aplicada':p['rota']['maioria_aplicada']})
    return saida

def aplicar(pp,m,cat,variante,corte):
    if m['atributos']!=NOMES:raise ValueError('Atributos incompatíveis.')
    ss=sinais(pp,m['modelo'],cat,variante);cs=a.confiancas(ss,m['calibrador'])
    return [{**r,'confianca':float(c),'decisao':f.decidir(r,c,m['politica']) if corte=='calibrado' else 'publicar' if r['elegivel'] and c>=.7 else 'revisar','via':'modelo_v14'} for r,c in zip(ss,cs)]
