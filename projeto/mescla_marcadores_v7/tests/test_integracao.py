from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo,NOMES
from mescla_marcadores_v7.experimento import preparar,ajustar


class TestIntegracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[2]
        with patch.object(socket,'create_connection',side_effect=AssertionError('Rede proibida')):
            cls.cat,_=carregar_catalogo(root)

    def q(self,id,en,**kw):
        return {'id':id,'enunciado_html':en,'comando':'',
                'alternativas':{'A':'O habeas corpus pode ser impetrado.','B':'A revisão criminal permite determinado pedido.'},**kw}

    def test_texto_ignorado_nao_reaparece_nos_atributos(self):
        qs={'a':self.q('a','Assinale a alternativa correta.',assunto_origem='Tráfico de drogas'),
            'b':self.q('b','Considerando as afirmativas abaixo, é correto afirmar que:',assunto_origem='Homicídio')}
        with patch.object(socket,'create_connection',side_effect=AssertionError('Rede proibida')):
            pp=preparar(self.cat,qs)
        self.assertTrue(all(p['rota']['peso_textual_enunciado']==0 for p in pp.values()))
        f.np.testing.assert_allclose(pp['a']['x_mescla'],pp['b']['x_mescla'],atol=0,rtol=0)
        f.np.testing.assert_allclose(pp['a']['scores'],pp['b']['scores'],atol=0,rtol=0)
        for nome in ['palavra_enunciado','caractere_enunciado','escopo_enunciado','titulo_enunciado','norma_enunciado','artigo_enunciado']:
            if nome in NOMES:self.assertTrue((pp['a']['features_v3'][:,NOMES.index(nome)]==0).all())

    def test_treino_rejeita_rotulos_externos(self):
        with self.assertRaises(ValueError):ajustar({'a':{}},{'b':{}},self.cat,'mescla_condicional')

    def test_trocar_id_nao_muda_ranking(self):
        q=self.q('a','A respeito da interceptação telefônica, assinale a correta.')
        p=preparar(self.cat,{'a':q,'b':{**q,'id':'outro'}})
        f.np.testing.assert_allclose(p['a']['ranking_mescla_condicional'],p['b']['ranking_mescla_condicional'],atol=0,rtol=0)
