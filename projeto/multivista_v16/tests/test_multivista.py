import json,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from multivista_v16.catalogo import compilar,Busca
from multivista_v16 import modelo as m

class TestMultivista(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=Path(__file__).resolve().parents[2];cls.cat,_=carregar_catalogo(cls.p)
        cls.props=json.loads((cls.p/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
        cls.dic=Dicionario(json.loads((cls.p/'vocabulario_v8/dicionario.json').read_text()),cls.cat.temas,cls.cat.familias)
        cls.snapshot=compilar(cls.cat,cls.props)
    def test_catalogo_nao_le_questoes_ou_rotulos(self):
        with patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(Path,'read_text',side_effect=AssertionError('arquivo')):
            ss=compilar(self.cat,self.props)
        self.assertEqual(ss,self.snapshot);self.assertNotRegex(json.dumps(ss),r'Q\d{4}')
    def test_homonimos_nao_sao_fundidos(self):
        docs={d['tema_id']:d for d in self.snapshot['documentos']}
        self.assertIn('4703',docs);self.assertIn('6734',docs)
        self.assertNotEqual(docs['4703']['familia_id'],docs['6734']['familia_id'])
        self.assertTrue(any('4703' in g['ids'] and '6734' in g['ids'] for g in self.snapshot['homonimos']))
    def test_bm25_sem_sinal_nao_inventa_probabilidade(self):
        busca=Busca(self.cat,self.snapshot);np.testing.assert_array_equal(busca.buscar(''),0)
        np.testing.assert_array_equal(busca.buscar('zzzzzzz'),0)
        s=busca.buscar('remição e trabalho prisional');self.assertTrue(np.isfinite(s).all());self.assertLessEqual(max(s),1)
    def test_campo_inaplicavel_tem_zero_apos_padronizacao(self):
        mod={'media':[10.,20.],'escala':[2.,5.],'coeficientes':[3.,4.],'intercepto':.5}
        p={'x':np.array([[0.,25.],[1000.,25.]]),'mask':np.array([[False,True],[False,True]])}
        np.testing.assert_array_equal(m.escores(p,mod),[4.5,4.5])
    def test_treino_rejeita_rotulos_externos(self):
        with self.assertRaisesRegex(ValueError,'rótulos externos'):m.ajustar({'a':{}},{'b':{}},self.cat,'condicional_v15')
    def test_novos_atributos_e_rankings_ignoram_id_e_origem(self):
        q={'id':'nova','enunciado_html':'A respeito do inquérito policial, julgue a assertiva.','comando':'','alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'Penal','assunto_origem':'Prescrição'}
        outra={**q,'id':'outro_id','disciplina_origem':'Criminologia','assunto_origem':'Outra origem'}
        a=m.preparar(self.cat,self.dic,self.snapshot,{'nova':q});b=m.preparar(self.cat,self.dic,self.snapshot,{'outro_id':outra})
        for v in a:
            np.testing.assert_array_equal(a[v]['nova']['x'],b[v]['outro_id']['x'])
            np.testing.assert_array_equal(a[v]['nova']['ranking'],b[v]['outro_id']['ranking'])
    def test_ce_e_sem_itens_marcam_campos_inaplicaveis(self):
        q={'id':'nova','enunciado_html':'A respeito da prescrição, julgue.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        pp=m.preparar(self.cat,self.dic,self.snapshot,{'nova':q})
        for v,mp in pp.items():
            p=mp['nova']
            for j,n in enumerate(m.nomes(v)):
                if n.startswith(('alt_','itens_')) or n in ['voto_itens','bm25_alternativas','bm25_itens_media','bm25_itens_max']:
                    self.assertFalse(p['mask'][:,j].any())
    def test_regua_nao_funde_irmaos(self):
        t={'1':{'parent_id':''},'2':{'parent_id':'1'},'3':{'parent_id':'1'}}
        self.assertTrue(m.mesmo_ramo('1','2',t));self.assertFalse(m.mesmo_ramo('2','3',t))
    def dados_preservacao(self,c=.8):
        temas={'1':{'parent_id':'','titulo':'Tema A'},'2':{'parent_id':'','titulo':'Tema B'}}
        ant=[{'id':'nova','tema_central_id':'1','decisao':'publicar','confianca':.95}]
        novo=[{'id':'nova','tema_central_id':'2','decisao':'publicar','confianca':c,'elegivel':True,'homonimo_nao_resolvido':False}]
        par=[{**novo[0],'confianca':.9}]
        return temas,ant,novo,par
    def test_guarda_exige_duas_sugestoes_fortes_contra_ramo_antigo(self):
        temas,ant,n,par=self.dados_preservacao()
        r=m.preservar(n,ant,par,temas,True)[0]
        self.assertEqual(r['decisao'],'revisar');self.assertEqual(r['confianca'],.95)
        self.assertTrue(r['veto_preservacao'])
    def test_nova_sugestao_fraca_nao_apaga_publicacao_anterior(self):
        temas,ant,n,par=self.dados_preservacao(.69)
        r=m.preservar(n,ant,par,temas,True)[0]
        self.assertEqual(r['decisao'],'publicar');self.assertFalse(r['veto_preservacao'])
    def test_modo_sem_guarda_preserva_tambem_erro_potencial(self):
        temas,ant,n,par=self.dados_preservacao()
        r=m.preservar(n,ant,par,temas,False)[0];self.assertEqual(r['tema_central_id'],'1');self.assertEqual(r['decisao'],'publicar')
    def test_conjuntos_de_preservacao_incompativeis_sao_rejeitados(self):
        temas,ant,n,par=self.dados_preservacao()
        with self.assertRaisesRegex(ValueError,'Conjuntos'):m.preservar(n,[],par,temas,True)
if __name__=='__main__':unittest.main()
