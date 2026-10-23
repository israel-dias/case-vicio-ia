import re,unittest
from pathlib import Path
from melhorias_v3.representacao import carregar_catalogo
from contexto_v18.foco_integral import Extrator

class TestItensVF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cat,_=carregar_catalogo(Path(__file__).resolve().parents[2]);cls.ex=Extrator(cat)

    def test_separacao_nao_engole_proposicoes_vf(self):
        q={'enunciado_html':'Analise as afirmativas a seguir e assinale (V) para a verdadeira e (F) para a falsa. <br> ( ) O Populismo Penal é caracterizado, entre outros fatores, pela punição transformada em espetáculo público e pela priorização do conhecimento popular em face do conhecimento oficial dos especialistas sobre o sistema de justiça criminal. <br> ( ) As Teorias do Consenso concebem o delito como uma anomalia do sistema. <br> ( ) As Criminologias Biologicistas, também chamadas de Ecologia Criminal, estudam a concentração delitiva em certas zonas territoriais, enxergando o crime como reflexo da cultura e da interação social na formação da pessoa. <br> Na ordem apresentada, as afirmativas são, respectivamente,','comando':'','alternativas':{'A':'V – F – F.','B':'F – V – F.'}}
        n,r=self.ex.extrair(q);texto=n['enunciado_html']+' '+n['comando']
        self.assertEqual(len(re.findall(r'\(\s*\)',texto)),3)
        for palavra in ['Populismo','Consenso','Biologicistas']:self.assertIn(palavra,texto)
        self.assertTrue(r['resguardo_proposicoes_vf'])
        self.assertFalse(r['cabecalho_geral_separado'])

    def test_lista_geral_sem_proposicoes_ainda_e_separada(self):
        q={'enunciado_html':'Julgue o item acerca de crimes, penas, imputabilidade e institutos. A tentativa pressupõe início da execução.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        n,r=self.ex.extrair(q);self.assertTrue(r['cabecalho_geral_separado']);self.assertIn('tentativa',n['comando'])

if __name__=='__main__':unittest.main()
