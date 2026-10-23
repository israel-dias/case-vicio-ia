import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import numpy as np
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from roteamento_v14 import modelo as m
from roteamento_v14.texto import Leitor

class TestModelo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parents[2];cls.cat,_=carregar_catalogo(p)
        cls.dic=Dicionario(json.loads((p/'vocabulario_v8/dicionario.json').read_text()),cls.cat.temas,cls.cat.familias)
    def test_rotulos_externos_rejeitados(self):
        with self.assertRaisesRegex(ValueError,'rótulos externos'):m.ajustar({'a':{}},{'b':{}},self.cat)
    def test_ce_nao_produz_atributos_de_alternativas(self):
        q={'id':'nova','enunciado_html':'A respeito do inquérito policial, julgue.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        pp=m.preparar(self.cat,self.dic,{'nova':q})
        for v in pp:
            x=pp[v]['nova']['x']
            for nome in ['alt_palavra_media','alt_escopo_media','alt_escopo_max']:
                np.testing.assert_array_equal(x[:,m.NOMES.index(nome)],0)
    def test_normas_cp_cpp_nao_sao_confundidas(self):
        leitor=Leitor(self.cat,self.dic)
        self.assertIn('CPP',leitor.norma_comando('Explique o artigo 20 do Código de Processo Penal.'))
        self.assertNotIn('CPP',leitor.norma_comando('Explique o artigo 20 do Código Penal.'))
    def test_reranking_pode_trocar_o_primeiro_tema(self):
        p={'x':np.zeros((2,len(m.NOMES))),'ranking':np.array([1.,0.]),'sinal_textual':np.array([1.,0.]),
            'rota':{'sem_evidencia':False,'modo':'conjunto','primeiro_item_fallback':False,'maioria_aplicada':False},'homonimos':{'a':[],'b':[]}}
        p['x'][:,0]=.1;cat=SimpleNamespace(familias=['a','b'])
        with patch.object(m.a,'escore_linear',return_value=np.array([1.,2.])):
            self.assertEqual(m.sinais({'nova':p},{},cat,'usuario_literal')[0]['tema_central_id'],'a')
            self.assertEqual(m.sinais({'nova':p},{},cat,'comparador_treinado')[0]['tema_central_id'],'b')
    def test_homonimos_empatados_nao_publicam_por_ordem_de_id(self):
        p={'x':np.full((2,len(m.NOMES)),.2),'ranking':np.array([1.,1.]),'sinal_textual':np.array([1.,1.]),
            'rota':{'sem_evidencia':False,'modo':'comando','primeiro_item_fallback':False,'maioria_aplicada':False},'homonimos':{'a':['b'],'b':['a']}}
        with patch.object(m.a,'escore_linear',return_value=np.array([5.,5.])):
            r=m.sinais({'nova':p},{},SimpleNamespace(familias=['a','b']),'usuario_literal')[0]
        self.assertTrue(r['homonimo_nao_resolvido']);self.assertFalse(r['elegivel'])

if __name__=='__main__':unittest.main()
