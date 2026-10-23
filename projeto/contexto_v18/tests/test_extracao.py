import unittest
from contexto_v18.extracao import extrair


class TestExtracao(unittest.TestCase):
    def q(self,en,cmd='',alts=None):
        return {'id':'novo','enunciado_html':en,'comando':cmd,'alternativas':alts or {'A':'Primeira opção','B':'Segunda opção'}}

    def test_cobranca_extraida_com_topico_anterior_na_mesma_frase(self):
        q=self.q('João foi acusado de um crime. Sobre o concurso de pessoas, assinale a alternativa correta.')
        n,r=extrair(q);self.assertTrue(r['extraido'])
        self.assertIn('concurso de pessoas',n['comando']);self.assertEqual(n['enunciado_html'],'João foi acusado de um crime.')

    def test_comando_existente_informativo_nao_e_substituido(self):
        q=self.q('Assinale a alternativa correta.','Explique a interceptação telefônica.')
        n,r=extrair(q);self.assertFalse(r['extraido']);self.assertEqual(n,q)

    def test_lei_nao_e_duplicada_artificialmente_na_narrativa(self):
        n,r=extrair(self.q('Conforme a Lei de Execução Penal, assinale a opção correta.'))
        self.assertTrue(r['extraido']);self.assertEqual(n['enunciado_html'],'')

    def test_pergunta_final_preserva_narrativa_anterior(self):
        n,r=extrair(self.q('O investigado foi ouvido. Qual recurso é cabível?'))
        self.assertEqual(r['origem'],'pergunta_final');self.assertEqual(n['comando'],'Qual recurso é cabível?')
        self.assertIn('investigado',n['enunciado_html'])

    def test_assertiva_ce_unica_e_cobranca_sem_corte_por_tamanho(self):
        n,r=extrair(self.q('A interceptação telefônica exige decisão judicial. Negrito: não.',alts={'C':'Certo','E':'Errado'}))
        self.assertFalse(r['extraido'])
        n,r=extrair(self.q('A interceptação telefônica exige decisão judicial.',alts={'C':'Certo','E':'Errado'}))
        self.assertTrue(r['extraido']);self.assertIn('decisão judicial',n['comando'])

    def test_itens_independentes_nao_sao_recortados(self):
        q=self.q('Sobre provas:<br>I. Uma proposição.<br>II. Outra proposição.<br>Assinale a alternativa correta.')
        n,r=extrair(q);self.assertFalse(r['extraido']);self.assertEqual(n,q)

    def test_negacao_e_instrucao_incorreta_sao_preservadas(self):
        n,r=extrair(self.q('O agente não conhecia o fato. Sobre o erro de tipo, assinale a alternativa INCORRETA.'))
        self.assertIn('não conhecia',n['enunciado_html']);self.assertIn('INCORRETA',n['comando'])


if __name__=='__main__':unittest.main()
