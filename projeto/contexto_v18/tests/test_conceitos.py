import unittest
from pathlib import Path
from melhorias_v3.representacao import carregar_catalogo
from contexto_v18.foco_morfologico import Extrator,IdentificadoresMorfologicos


class TestConceitos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c,_=carregar_catalogo(Path(__file__).resolve().parents[2]);cls.det=IdentificadoresMorfologicos(c);cls.ex=Extrator(c)

    def test_flexoes_compostas_reconhecem_tentativa_e_consumacao(self):
        d=self.det.analisar({'comando':'Discuta a tentativa e o crime consumado nessa situação.'})
        self.assertTrue(any(h['titulo']=='Crime Consumado e Tentado' for h in d['hits']))

    def test_consumada_isolada_nao_cria_identificador_composto(self):
        d=self.det.analisar({'comando':'A morte estava consumada e o agente deixou o local.'})
        self.assertFalse(any(h['titulo'] in ['Crime Consumado e Tentado','Morte do agente'] for h in d['hits']))

    def test_negação_preservada_sem_resolver_certo_errado(self):
        q={'comando':'O crime não foi consumado; houve tentativa.','enunciado_html':'','alternativas':{'C':'Certo','E':'Errado'}}
        d=self.det.analisar(q);self.assertIn('não',d['comando']);self.assertTrue(d['forte'])
        self.assertFalse(any(k in d for k in ['gabarito','resposta_correta']))

    def test_lista_geral_continua_sem_prioridade(self):
        d=self.det.analisar({'comando':'Assinale a opção sobre tentativa e crime consumado, culpabilidade, concurso de pessoas e medidas de segurança.'})
        self.assertFalse(d['forte']);self.assertEqual(d['origem'],'lista_multitematica_sem_foco')


if __name__=='__main__':unittest.main()
