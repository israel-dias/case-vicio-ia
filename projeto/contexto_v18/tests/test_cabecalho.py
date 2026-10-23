import unittest
from pathlib import Path
from melhorias_v3.representacao import carregar_catalogo
from contexto_v18.extracao_foco import Extrator


class TestCabecalho(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat,_=carregar_catalogo(Path(__file__).resolve().parents[2]);cls.ex=Extrator(cls.cat)

    def q(self,en,cmd='',alts=None):
        return {'id':'novo','enunciado_html':en,'comando':cmd,'alternativas':alts or {'C':'Certo','E':'Errado'}}

    def test_lista_geral_separada_da_assertiva_real(self):
        q=self.q('Julgue o item acerca de crimes, penas, imputabilidade e institutos. Na tentativa de subtração e morte consumada, há latrocínio consumado.')
        n,r=self.ex.extrair(q)
        self.assertTrue(r['cabecalho_geral_separado'])
        self.assertNotIn('imputabilidade',n['enunciado_html']+' '+n['comando'])
        self.assertIn('latrocínio',n['comando'])
        self.assertIn('imputabilidade',r['enunciado_original'])

    def test_lista_sem_assertiva_nao_e_forcada_a_um_assunto(self):
        q=self.q('Assinale a opção correta em relação à culpabilidade, ao concurso de pessoas, às finalidades das penas e às medidas de segurança.',alts={'A':'Uma tese de culpabilidade.','B':'Uma tese sobre penas.'})
        n,r=self.ex.extrair(q)
        self.assertEqual(n,q);self.assertTrue(r['lista_sem_cobranca_especifica'])

    def test_cabecalho_de_um_assunto_e_preservado(self):
        q=self.q('A respeito da interceptação telefônica, julgue o item. A autorização precisa ser judicial.')
        n,r=self.ex.extrair(q)
        self.assertEqual(r['cabecalho_geral_separado'],'')
        self.assertIn('interceptação',n['enunciado_html']+' '+n['comando'])

    def test_cabecalho_normativo_necessario_nao_e_apagado(self):
        q=self.q('Conforme o CPP, julgue acerca de crimes, penas, imputabilidade e institutos. O artigo 20 tem aplicação ao caso.')
        n,r=self.ex.extrair(q)
        self.assertEqual(n,q);self.assertTrue(r['referencia_normativa_preservada'])

    def test_caso_com_nomes_e_relacao_autor_participe_nao_e_lista(self):
        q=self.q('João, Pedro e Carlos estavam no local. João foi o autor do homicídio e Pedro figurou como partícipe.','Indique o papel dos envolvidos no concurso de pessoas.')
        n,r=self.ex.extrair(q);self.assertEqual(n,q)


if __name__=='__main__':unittest.main()
