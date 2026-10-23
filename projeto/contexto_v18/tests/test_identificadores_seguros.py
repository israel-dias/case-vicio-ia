import unittest
from pathlib import Path
from melhorias_v3.representacao import carregar_catalogo
from contexto_v18.foco_seguro import Extrator,IdentificadoresSeguros


class TestIdentificadoresSeguros(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat,_=carregar_catalogo(Path(__file__).resolve().parents[2]);cls.det=IdentificadoresSeguros(cls.cat);cls.ex=Extrator(cls.cat)

    def test_lista_com_preposicao_feminina_plural_nao_vira_foco(self):
        t='Assinale a opção correta em relação às causas de exclusão de culpabilidade, ao concurso de pessoas, às finalidades das penas e às medidas de segurança.'
        q={'enunciado_html':t,'comando':'','alternativas':{'A':'Exclusão de culpabilidade.','B':'Medida de segurança.'}}
        n,r=self.ex.extrair(q)
        self.assertTrue(r['lista_sem_cobranca_especifica']);self.assertEqual(n,q)
        d=self.det.analisar({**q,'comando':t})
        self.assertFalse(d['forte']);self.assertEqual(d['origem'],'lista_multitematica_sem_foco')

    def test_morte_e_agente_proximos_nao_significam_morte_do_agente(self):
        d=self.det.analisar({'comando':'Na tentativa de subtração patrimonial e morte consumada, o agente responderá por latrocínio consumado.'})
        self.assertFalse(any(h['titulo']=='Morte do agente' for h in d['hits']))
        self.assertTrue(any(h['titulo']=='Morte do agente' for h in d.get('hits_nao_priorizados',[])))

    def test_frase_literal_morte_do_agente_continua_disponivel(self):
        d=self.det.analisar({'comando':'Qual o efeito da morte do agente sobre a punibilidade?'})
        self.assertTrue(any(h['titulo']=='Morte do agente' for h in d['hits']))

    def test_autor_e_participe_admitem_flexoes_e_relacao_explicita(self):
        d=self.det.analisar({'comando':'Indique quem são os autores e os partícipes do caso.'})
        self.assertTrue(any(h['familia']=='5071' for h in d['hits']))

    def test_tema_unico_nao_e_confundido_com_lista_geral(self):
        d=self.det.analisar({'comando':'A respeito da interceptação telefônica, assinale a opção correta.'})
        self.assertTrue(d['forte']);self.assertNotEqual(d['origem'],'lista_multitematica_sem_foco')


if __name__=='__main__':unittest.main()
