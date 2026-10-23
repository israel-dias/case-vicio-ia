import copy
import json
from pathlib import Path
import unittest
from types import SimpleNamespace
import numpy as np
from experimento_atributos_v11 import modelo as m
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario


class TestAtributos(unittest.TestCase):
    def test_remocao_real_de_colunas_sem_mutar_matriz(self):
        x=np.arange(3*len(m.ATRIBUTOS)).reshape(3,-1);antes=x.copy()
        ix=m.indices('sem_palavra_completo');novo=x[:,ix]
        self.assertEqual(novo.shape[1],len(m.ATRIBUTOS)-1)
        self.assertNotIn(m.ATRIBUTOS.index('palavra_completo'),ix)
        np.testing.assert_array_equal(antes,x)

    def test_coeficientes_negativos_nao_sao_truncados(self):
        x=np.zeros((40,len(m.ATRIBUTOS)));x[:,0]=np.linspace(-3,3,40)
        y=(x[:,0]<0).astype(int);modelo=m.ajustar((x,y,np.ones(40)),'controle_41')
        self.assertLess(modelo['coeficientes'][0],0)

    def test_preservar_mantem_tema_e_confianca_anteriores(self):
        c=[{'id':'a','tema_central_id':'1','decisao':'publicar','confianca':.9},
           {'id':'b','tema_central_id':'2','decisao':'revisar','confianca':.4}]
        n=[{'id':'a','tema_central_id':'9','decisao':'revisar','confianca':.2},
           {'id':'b','tema_central_id':'2','decisao':'publicar','confianca':.8}]
        novo=m.preservar_publicadas(n,c)
        self.assertEqual(novo[0],dict(c[0],publicacao_preservada=True))
        self.assertEqual(novo[1],dict(n[1],publicacao_preservada=False))

    def test_preservacao_nao_oculta_erros_das_novas_publicacoes(self):
        base=[{'id':'a','decisao':'publicar','correto':1,'confianca':.9},
              {'id':'b','decisao':'revisar','correto':0,'confianca':.4}]
        novas=[dict(base[0]),dict(base[1],decisao='publicar',confianca=.8)]
        met=m.medidas(novas,base)
        self.assertEqual(met['novas_erradas'],1)
        self.assertEqual(met['precisao_publicadas'],.5)

    def test_treino_rejeita_rotulo_externo(self):
        with self.assertRaisesRegex(ValueError,'Rótulos externos'):
            m.matriz_treino({'a':{}},{'b':{}},None)

    def test_ranking_fixo_nao_muda_por_peso_do_modelo(self):
        x=np.zeros((2,len(m.ATRIBUTOS)));x[0,0]=100
        p={'x_mescla':x,'ranking_vocabulario_reordena':np.array([.1,.9]),
           'scores':np.array([.1,.9]),'scores_novos':np.array([.2,.8]),
           'scores_foco':np.zeros(2),'score_vocabulario':np.zeros(2),
           'rota':{'conteudo_insuficiente':False}}
        mod={'dimensao':len(m.ATRIBUTOS),'media':[0.]*len(m.ATRIBUTOS),'escala':[1.]*len(m.ATRIBUTOS),
             'coeficientes':[1.]+[0.]*(len(m.ATRIBUTOS)-1),'intercepto':0.}
        r=m.sinais({'novo':p},mod,SimpleNamespace(familias=['t1','t2']),'controle_41')[0]
        self.assertEqual(r['tema_central_id'],'t2')

    def test_variante_inventada_e_rejeitada(self):
        with self.assertRaisesRegex(ValueError,'desconhecida'):m.indices('ignorar_todos_erros')

    def test_conjuntos_diferentes_nao_podem_ser_unidos(self):
        with self.assertRaisesRegex(ValueError,'Conjuntos diferentes'):
            m.preservar_publicadas([{'id':'x'}],[{'id':'y'}])

    def test_frase_generica_nao_gera_publicacao_direta(self):
        p=Path(__file__).resolve().parents[2];cat,_=carregar_catalogo(p)
        dic=Dicionario(json.loads((p/'vocabulario_v8/dicionario.json').read_text()),cat.temas,cat.familias)
        q={'id':'novo','enunciado_html':'A respeito da teoria da conduta, julgue.','comando':'',
           'alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'','assunto_origem':''}
        pp=m.preparar(cat,dic,{'novo':q})['novo']
        self.assertTrue(pp['identificador_generico'])
        self.assertIsNone(pp['identificador_direto'])


if __name__=='__main__':unittest.main()
