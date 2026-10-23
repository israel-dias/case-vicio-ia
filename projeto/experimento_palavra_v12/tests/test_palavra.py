import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from experimento_palavra_v12 import modelo as m
from experimento_atributos_v11 import modelo as v11
from mescla_marcadores_v7.texto import alternativas_tematicas

class TestPalavra(unittest.TestCase):
    def test_vantagem_usa_concorrente_excluindo_o_proprio_tema(self):
        r=m.vantagens([.3,.1,.2]);np.testing.assert_allclose(r[:,0],[.1,-.2,-.1])
        np.testing.assert_allclose(r[:,1],[1/3,-2/3,-1/3])

    def test_empate_nao_vira_vantagem_positiva(self):
        np.testing.assert_allclose(m.vantagens([.2,.2]),0)
        np.testing.assert_allclose(m.vantagens([0.,0.]),0)
        with self.assertRaises(ValueError):m.vantagens([float('nan')])

    def test_todas_variantes_preservam_palavra_completo_e_controle_39(self):
        self.assertEqual(len(m.nomes('controle_v11')),39)
        for v in m.VARIANTES:self.assertIn('palavra_completo',m.nomes(v))
        with self.assertRaises(ValueError):m.nomes('inexistente')

    def test_alternativas_ce_numeros_e_combinacoes_nao_sao_tematicas(self):
        for alts in [{'C':'Certo','E':'Errado'},{'A':'1','B':'2'},{'A':'Apenas I e II','B':'Somente III'}]:
            self.assertFalse(alternativas_tematicas({'alternativas':alts}))
        self.assertTrue(alternativas_tematicas({'alternativas':{'A':'Apelação','B':'Revisão criminal'}}))

    def test_preparacao_preserva_matriz_anterior_e_zera_foco_ausente(self):
        x=np.arange(2*41,dtype=float).reshape(2,41)/100
        p={'x_mescla':x.copy(),'foco':{'presente':False,'texto_foco':''},'ranking_vocabulario_reordena':np.array([.3,.1])}
        cat=SimpleNamespace(temas={},familias=['a','b'])
        q={'id':'nova','enunciado_html':'texto','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        with patch.object(v11,'preparar',return_value={'nova':p}),patch.object(m,'rotear',return_value=(q,{})):
            z=m.preparar(cat,None,{'nova':q})['nova']
        np.testing.assert_array_equal(z['x_mescla'],x)
        np.testing.assert_array_equal(z['novos_v12']['foco'],np.zeros((2,2)))
        np.testing.assert_array_equal(z['novos_v12']['alternativas'][:,1],np.zeros(2))

    def test_rotulo_externo_rejeitado_antes_do_treino(self):
        with self.assertRaisesRegex(ValueError,'rótulos externos'):
            m.dados_treino({'a':{}},{'b':{}},None,'controle_v11')

    def test_preservacao_inclui_erro_antigo_sem_consultar_acerto(self):
        ant=[{'id':'a','decisao':'publicar','tema_central_id':'t','confianca':.8,'correto':0}]
        novos=[{'id':'a','decisao':'revisar','tema_central_id':'u','confianca':.4,'correto':1}]
        r=m.combinar(novos,ant)[0]
        self.assertEqual(r['tema_central_id'],'t');self.assertEqual(r['correto'],0)

    def test_ranking_fixo_nao_e_trocado_pela_maior_confianca(self):
        p={'ranking_vocabulario_reordena':np.array([.1,.9]),'scores':np.array([.1,.9]),
            'scores_novos':np.array([.1,.9]),'scores_foco':np.array([0,0]),'score_vocabulario':np.array([0,0]),
            'rota':{'conteudo_insuficiente':False},'base_v12':np.zeros((2,39)),'novos_v12':{}}
        with patch.object(m.a,'escore_linear',return_value=np.array([.5])):
            r=m.sinais({'a':p},{},SimpleNamespace(familias=['a','b']),'regularizacao_03')[0]
        self.assertEqual(r['tema_central_id'],'b')

if __name__=='__main__':unittest.main()
