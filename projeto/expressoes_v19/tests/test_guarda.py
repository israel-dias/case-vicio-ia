import unittest
from expressoes_v19.guarda import combinar

class TestGuarda(unittest.TestCase):
    temas={'a':{'parent_id':''},'b':{'parent_id':''},'1':{'parent_id':'a'},'2':{'parent_id':'a'},'3':{'parent_id':'b'}}
    def r(self,t):return {'id':'novo','tema_central_id':t,'decisao':'revisar','confianca':.5,'variante':'teste'}
    def test_troca_de_disciplina_conserva_controle_sem_elevar_confianca(self):
        r=combinar([self.r('1')],[self.r('3')],self.temas)[0]
        self.assertEqual(r['tema_central_id'],'1');self.assertTrue(r['guarda_disciplina_acionada']);self.assertEqual(r['confianca'],.5)
    def test_mesma_disciplina_nao_torna_irmaos_equivalentes(self):
        r=combinar([self.r('1')],[self.r('2')],self.temas)[0]
        self.assertEqual(r['tema_central_id'],'2');self.assertFalse(r['guarda_disciplina_acionada']);self.assertFalse(r['confianca_global_recalibrada'])
    def test_nao_adivinha_conjunto_faltante(self):
        with self.assertRaises(ValueError):combinar([self.r('1')],[],self.temas)

if __name__=='__main__':unittest.main()
