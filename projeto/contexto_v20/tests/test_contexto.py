import unittest
from pathlib import Path
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from contexto_v20.evidencia import Evidencia
from contexto_v20.modelo import misturar

class TestContexto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat,_=carregar_catalogo(Path(__file__).resolve().parents[2]);cls.e=Evidencia(cls.cat);cls.h=Evidencia(cls.cat,homonimos=True)
    def test_transito_em_julgado_nao_e_ancora_de_crime_de_transito(self):
        t,s,r,_=self.e.pontuar('A condenação transitou e houve trânsito em julgado.')
        self.assertEqual(r[self.e.ix['4691']],0);self.assertEqual(t[self.e.ix['4691']],0)
    def test_crime_de_transito_mantem_expressao_completa(self):
        t,_,_,_=self.e.pontuar('A questão trata de crimes de trânsito.')
        self.assertGreater(t[self.e.ix['4691']],0)
    def test_fechado_nao_e_vocabulo_distintivo(self):
        _,_,r,_=self.e.pontuar('O local estava fechado.')
        self.assertEqual(r.max(),0)
    def test_expressao_regime_fechado_continua_disponivel(self):
        _,s,_,_=self.e.pontuar('O cumprimento é em regime fechado.')
        self.assertGreater(s[self.e.ix['5199']],0)
    def test_alternativa_isolada_nao_tem_o_mesmo_peso_do_topico(self):
        q={'enunciado_html':'Sobre a relação entre sistema penal e pobreza, assinale a opção correta.','comando':'','alternativas':{'A':'A seletividade atinge os mais pobres.','B':'Uma tese de vitimização.','C':'A internação por medidas de segurança.','D':'O controle social da pobreza.'}}
        e=self.e.campos(q);j=self.e.ix['5184']
        self.assertEqual(e['foco_titulo'][j],0);self.assertLess(e['titulo'][j],.1)
    def test_itens_preservados_e_cabecalho_mantido_como_apoio(self):
        q={'enunciado_html':'Uma pessoa está em regime fechado.\nI. A remição depende de trabalho.\nII. O estudo também conta na remição.','comando':'Analise os itens.','alternativas':{'A':'I apenas','B':'I e II'}}
        e=self.h.campos(q);self.assertEqual(len(e['trace']['itens_preservados']),2);self.assertIn('regime fechado',e['trace']['texto_completo']);self.assertIn('remição',e['trace']['foco'])
    def test_homonimos_recebem_apoio_sem_fundir_ids(self):
        _,_,r,_=self.h.pontuar('Discute-se a remição.')
        self.assertGreater(r[self.e.ix['4703']],0);self.assertGreater(r[self.e.ix['6734']],0)
    def test_evidencia_fraca_nao_e_amplificada_para_trocar_candidato(self):
        base=f.np.array([1.,.99]);sinal=f.np.array([0.,.01]);r=misturar(base,sinal)
        self.assertGreater(r[0],r[1])
    def test_ce_preserva_nao_e_ignora_respostas_vazias(self):
        e=self.e.campos({'enunciado_html':'A testemunha não pode ser coagida.','comando':'','alternativas':{'C':'Certo','E':'Errado'}})
        self.assertIn('não',e['trace']['foco']);self.assertNotIn('Certo',e['trace']['texto_completo'])
    def test_id_e_metadados_nao_alteram_evidencia(self):
        q={'id':'novo','enunciado_html':'A prescrição depende do prazo.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
        x=self.h.campos(q);y=self.h.campos({**q,'id':'outro','disciplina_origem':'Direito Civil'})
        for k in ['titulo','escopo','raro','foco_titulo','foco_escopo','foco_raro']:self.assertTrue((x[k]==y[k]).all())

if __name__=='__main__':unittest.main()
