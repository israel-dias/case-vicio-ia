import unittest
from pathlib import Path
from melhorias_v3.representacao import carregar_catalogo
from expressoes_v19.evidencia import Evidencia,canon,contem

class TestEvidencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat,_=carregar_catalogo(Path(__file__).resolve().parents[2]);cls.e=Evidencia(cls.cat)

    def test_coocorrencia_nao_e_relacao_morte_do_agente(self):
        a,_,_,_=self.e.pontuar('A morte consumada ocorreu e o agente respondeu pela conduta.')
        self.assertEqual(a[self.e.ix['5191']],0)
        a,_,_,_=self.e.pontuar('A morte do agente ocorreu depois.')
        self.assertGreater(a[self.e.ix['5191']],0)

    def test_adjetivo_comum_nao_vira_ancora_isolada(self):
        _,_,r,_=self.e.pontuar('A morte estava consumada e o agente deixou o local.')
        self.assertEqual(r[self.e.ix['5175']],0)

    def test_ordem_da_expressao_importa(self):
        self.assertTrue(contem(canon('Trata-se de erro de tipo.'),canon('erro de tipo')))
        self.assertFalse(contem(canon('Esse tipo de erro é comum.'),canon('erro de tipo')))

    def test_vocabulo_do_escopo_e_recuperado_do_catalogo(self):
        _,_,r,t=self.e.pontuar('Discutem-se os elementos do latrocínio.')
        self.assertGreater(r[self.e.ix['5157']],0)
        self.assertTrue(any(z['tipo']=='vocabulo_distintivo_catalogo' and 'latrocinio' in z['expressoes'] for z in t))

    def test_ids_e_origem_nao_entram_na_evidencia(self):
        q={'id':'novo','enunciado_html':'O crime foi tentado, mas o resultado não se consumou.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        a=self.e.preparar(q);b=self.e.preparar({**q,'id':'outro','disciplina_origem':'Criminologia','assunto_origem':'tema falso'})
        for k in ['titulo','escopo','raro','foco_titulo','foco_escopo','foco_raro']:self.assertTrue((a[k]==b[k]).all())

    def test_ce_nao_fornece_palavras_para_classificar(self):
        q={'enunciado_html':'A tentativa exige início da execução.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        a=self.e.preparar(q)['trace'];self.assertTrue(a['certo_errado']);self.assertNotIn('Certo',a['texto_completo']);self.assertIn('tentativa',a['texto_completo'])

    def test_negacao_preservada(self):
        q={'enunciado_html':'A testemunha não pode ser coagida.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        self.assertIn('não',self.e.preparar(q)['trace']['texto_completo'])

    def test_itens_romanos_e_vf_nao_sao_descartados(self):
        for texto in ['I. O roubo envolve violência.\nII. A prescrição extingue a punibilidade.','( ) O roubo envolve violência. ( ) A prescrição extingue a punibilidade.']:
            r=self.e.preparar({'enunciado_html':texto,'comando':'','alternativas':{'A':'I apenas','B':'II apenas'}})['trace']
            self.assertEqual(r['origem_foco'],'todas_as_proposicoes_preservadas');self.assertIn('roubo',r['foco']);self.assertIn('prescrição',r['foco'])

    def test_homonimos_permanecem_em_familias_separadas(self):
        a,_,_,_=self.e.pontuar('Aplica-se a Lei de Execução Penal.')
        self.assertGreater(a[self.e.ix['4703']],0);self.assertGreater(a[self.e.ix['6734']],0);self.assertNotEqual(self.e.ix['4703'],self.e.ix['6734'])

    def test_enumeracao_sozinha_nao_cria_foco_unico(self):
        q={'enunciado_html':'Assinale a opção sobre culpabilidade, concurso de pessoas e medidas de segurança.','comando':'','alternativas':{'A':'Uma tese sobre culpabilidade.','B':'Outra sobre penas.'}}
        r=self.e.preparar(q)['trace'];self.assertEqual(r['origem_foco'],'sem_cobranca_inequivoca_preserva_conjunto')

if __name__=='__main__':unittest.main()
