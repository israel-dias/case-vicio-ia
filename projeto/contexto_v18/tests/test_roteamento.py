import unittest
from contexto_v18.roteamento import compor


class TestRoteamento(unittest.TestCase):
    def dados(self,forte=True):
        base=[{'id':'x','tema_central_id':'1','confianca':.9,'decisao':'publicar'}]
        novas=[{'id':'x','tema_central_id':'2','confianca':.6,'decisao':'revisar','motivo':'abaixo do corte','identificador_forte_cmd':forte}]
        return novas,base

    def test_prioridade_aplica_nova_leitura_mas_nao_libera_so_pelo_gatilho(self):
        n,b=self.dados();r=compor(n,b,'comando_prioritario')[0]
        self.assertEqual(r['tema_central_id'],'2');self.assertEqual(r['decisao'],'revisar')

    def test_sem_gatilho_nao_modifica_controle(self):
        n,b=self.dados(False);r=compor(n,b,'comando_prioritario')[0]
        self.assertEqual(r['tema_central_id'],'1');self.assertFalse(r['rota_nova_aplicada'])

    def test_suplemento_so_altera_revisoes_identificadas(self):
        n,b=self.dados();r=compor(n,b,'suplemento_revisoes')[0]
        self.assertEqual(r['tema_central_id'],'1');self.assertFalse(r['rota_nova_aplicada'])
        b[0]['decisao']='revisar';r=compor(n,b,'suplemento_revisoes')[0]
        self.assertEqual(r['tema_central_id'],'2');self.assertTrue(r['rota_nova_aplicada'])

    def test_string_false_nao_ativa_regra(self):
        n,b=self.dados();n[0]['identificador_forte_cmd']='False'
        with self.assertRaisesRegex(ValueError,'booleano'):compor(n,b,'comando_prioritario')


if __name__=='__main__':unittest.main()
