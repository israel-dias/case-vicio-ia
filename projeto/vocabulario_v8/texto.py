"""Dicionário descritivo versionado; não recebe rótulos de questões."""
import math
import re
from compatibilidade_v2 import features as f
from mescla_marcadores_v7.texto import rotear


class Dicionario:
    def __init__(self,dados,temas,familias):
        self.familias=list(familias);self.temas=temas;self.grupos=[]
        if dados.get('versao')!='vocabulario_tematico_v8_1':raise ValueError('Versão do dicionário inválida.')
        nomes=[]
        for g in dados['grupos']:
            nomes.append(g['nome'])
            if not g['titulos'] or not g['padroes']:raise ValueError('Grupo vazio.')
            ids=[]
            for titulo in g['titulos']:
                encontrados=[i for i,t in temas.items() if f.normalizar(t['titulo'])==f.normalizar(titulo) and f.elegivel(i,temas)]
                if not encontrados:raise ValueError('Título ativo não encontrado: '+titulo)
                ids.extend(encontrados)
            dest=sorted({temas[i]['parent_id'] if temas[i]['nivel']==2 else i for i in ids})
            if not set(dest)<=set(familias):raise ValueError('Família fora dos candidatos.')
            if len(g['padroes'])!=len(set(g['padroes'])):raise ValueError('Padrão repetido no grupo.')
            for pat in g['padroes']:
                if re.search(r'Q\d{4}',pat,re.I):raise ValueError('IDs de questão não são vocabulário.')
                if re.compile(pat).search(''):raise ValueError('Padrão aceita texto vazio.')
            self.grupos.append({'nome':g['nome'],'ids_temas':sorted(set(ids)),'familias':dest,
                                'padroes':list(g['padroes'])})
        if len(nomes)!=len(set(nomes)):raise ValueError('Grupo repetido.')

    def encontrar(self,texto):
        texto=f.normalizar(f.visivel(texto));hits=[];contagens={t:0 for t in self.familias}
        for grupo in self.grupos:
            encontrado=False
            for pat in grupo['padroes']:
                m=re.search(pat,texto)
                if not m:continue
                hits.append({'grupo':grupo['nome'],'expressao_encontrada':m.group(),
                             'padrao':pat,'temas_ids':grupo['ids_temas'],'familias':grupo['familias']})
                encontrado=True
            # Sinônimos, repetições e padrões sobrepostos do MESMO grupo não
            # aumentam artificialmente o apoio. Grupos distintos podem somar.
            if encontrado:
                for tid in grupo['familias']:contagens[tid]+=1
        valores=f.np.asarray([1-math.exp(-contagens[t]/2) for t in self.familias])
        return valores,hits

    def atributos(self,q):
        efetiva,rota=rotear(q,self.temas)
        textos=[efetiva.get('enunciado_html',''),efetiva.get('comando','')]
        textos.extend(efetiva['alternativas'][k] for k in sorted(efetiva['alternativas']))
        resultados=[self.encontrar(t) for t in textos]
        en,cmd=resultados[0][0],resultados[1][0]
        alts=f.np.stack([s[0] for s in resultados[2:]])
        alt_max=alts.max(axis=0);alt_media=alts.mean(axis=0)
        alt_fracao=(alts>0).mean(axis=0)
        if rota['peso_textual_enunciado']==0:
            busca=alt_max
        elif not rota['alternativas_suficientes']:
            busca=f.np.maximum(en,cmd)
        else:
            busca=.65*en+.10*cmd+.25*alt_max
        x=f.np.column_stack([en,cmd,alt_max,alt_media,alt_fracao,busca,busca-max(busca)])
        return x,busca,{'enunciado':resultados[0][1],'comando':resultados[1][1],
                       'alternativas':[s[1] for s in resultados[2:]],'modo':rota['modo']}
