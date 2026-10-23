import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from experimento_corte50_v13.avaliar import aplicar,medidas,executar

class TestCorte(unittest.TestCase):
    def rows(self):return [{'id':'nova','decisao':'revisar','confianca':.5,'elegivel':'True','tema_central_id':'t','correto':'0'}]
    def test_exatamente_50_publica_sem_mudar_tema_ou_confianca(self):
        r=self.rows();old=copy.deepcopy(r);z=aplicar(r)[0]
        self.assertEqual(z['decisao'],'publicar');self.assertEqual(z['confianca'],.5)
        self.assertEqual(z['tema_central_id'],'t');self.assertEqual(r,old)
    def test_abaixo_do_corte_e_inelegivel_continuam_revisar(self):
        r=self.rows();r[0]['confianca']=.4999;self.assertEqual(aplicar(r)[0]['decisao'],'revisar')
        r=self.rows();r[0]['elegivel']='False';r[0]['confianca']=.99;self.assertEqual(aplicar(r)[0]['decisao'],'revisar')
    def test_publicadas_e_fora_preservados_sem_olhar_rotulo(self):
        for d in ['publicar','fora']:
            r=self.rows();r[0]['decisao']=d;r[0]['confianca']=.1
            self.assertEqual(aplicar(r)[0]['decisao'],d)
    def test_erro_novo_contado_e_nao_ajusta_confianca(self):
        r=self.rows();z=aplicar(r);m=medidas(z,r)
        self.assertEqual(m['novas_erradas'],1);self.assertEqual(m['precisao_publicadas'],0)
        self.assertEqual(z[0]['confianca'],r[0]['confianca'])
    def test_bool_nan_infinito_e_ids_duplicados_rejeitados(self):
        for x in [True,float('nan'),float('inf'),-1,1.1]:
            r=self.rows();r[0]['confianca']=x
            with self.assertRaises(ValueError):aplicar(r)
        with self.assertRaises(ValueError):aplicar(self.rows()*2)
    def test_sem_publicadas_precisao_indefinida(self):
        r=self.rows();r[0]['confianca']=.1
        self.assertIsNone(medidas(aplicar(r),r)['precisao_publicadas'])
    def test_saida_existente_preservada(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaisesRegex(ValueError,'saída nova'):executar('.',Path(p))
    def test_independente_de_rede_e_de_modelo(self):
        with patch('socket.create_connection',side_effect=AssertionError('rede')):
            r=self.rows();self.assertEqual(aplicar(r)[0]['decisao'],'publicar')

if __name__=='__main__':unittest.main()
