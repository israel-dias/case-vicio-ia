import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from roteamento_v14.texto import separar_itens,limpar,Leitor

class TestTexto(unittest.TestCase):
    def test_romanos_com_html_traco_ponto_e_sem_ponto(self):
        for t in ['Cabeçalho:<br>I. Primeiro.<br>II. Segundo.','Cabeçalho:<br>I – Primeiro;<br>II – Segundo.','Cabeçalho:<br>I Kant afirma isso.<br>II Hegel afirma aquilo.']:
            r=separar_itens(t);self.assertEqual(len(r['itens']),2);self.assertEqual(r['numeros'],[1,2])
    def test_citacao_de_inciso_nao_vira_lista(self):
        self.assertEqual(separar_itens('O art. 1º, inciso I, determina algo.')['itens'],[])
    def test_script_e_grafia(self):
        self.assertEqual(limpar('A co-autoria<script>apague</script> não é isso.'),'A coautoria não é isso.')

    def leitor(self):
        l=object.__new__(Leitor);l.cat=SimpleNamespace(temas={'a':{'titulo':'Tema A'},'b':{'titulo':'Tema B'},'c':{'titulo':'Tema C'}},familias=['a','b','c'])
        l.idx={'a':0,'b':1,'c':2};l.idt=SimpleNamespace(referencias=lambda q:[])
        l.identificadores=lambda s: ('a',) if 'coautoria' in s.lower() else ()
        l.norma_comando=lambda s:'art. 20 do CP' if 'artigo 20' in s else ''
        l.ranking_texto=lambda t:np.array([1,0,0]) if 'alfa' in t.lower() else np.array([0,1,0]) if 'beta' in t.lower() else np.array([0,0,1])
        return l
    def q(self,en,cmd='',alts=None):return {'id':'nova','enunciado_html':en,'comando':cmd,'alternativas':alts or {'C':'Certo','E':'Errado'}}
    def test_comando_com_tema_tem_prioridade_sobre_itens_na_literal(self):
        l=self.leitor();q=self.q('I. alfa<br>II. beta','Explique a coautoria.')
        with patch('roteamento_v14.texto.rotear_v7',return_value=(q,{})):
            r=l.rotear(q,True)
        self.assertEqual(r['modo'],'comando');self.assertEqual(r['itens_usados'],[]);self.assertEqual(r['en_usado'],'')
    def test_ce_ignora_alternativas(self):
        l=self.leitor();q=self.q('Situação hipotética sem tema nomeado.')
        with patch('roteamento_v14.texto.rotear_v7',return_value=(q,{})):
            for literal in [True,False]:self.assertEqual(l.rotear(q,literal)['alts_usadas'],[])
    def test_maioria_e_primeiro_sao_hipoteses_distintas(self):
        l=self.leitor()
        for en,maioria,indices in [('I. alfa<br>II. beta<br>III. alfa',True,[0,2]),('I. alfa<br>II. beta<br>III. gama',False,[0])]:
            q=self.q(en)
            with patch('roteamento_v14.texto.rotear_v7',return_value=(q,{})):r=l.rotear(q,True)
            self.assertEqual(r['maioria_aplicada'],maioria);self.assertEqual(r['itens_escolhidos'],indices)
    def test_explique_sem_tema_ou_norma_nao_inventa_publicacao(self):
        l=self.leitor();q=self.q('Enunciado contextual.','Explique a situação.')
        with patch('roteamento_v14.texto.rotear_v7',return_value=(q,{})):r=l.rotear(q,True)
        self.assertTrue(r['sem_evidencia'])
    def test_explique_no_enunciado_nao_aciona_regra_de_comando(self):
        l=self.leitor();q=self.q('Explique a situação.')
        with patch('roteamento_v14.texto.rotear_v7',return_value=(q,{})):r=l.rotear(q,True)
        self.assertFalse(r['explique'])
    def test_hipotetica_pode_ser_indicada_no_comando(self):
        l=self.leitor();q=self.q('Uma narrativa.', 'Diante da situação hipotética, responda.',{'A':'Uma resposta temática','B':'Outra resposta temática'})
        with patch('roteamento_v14.texto.rotear_v7',return_value=(q,{})):r=l.rotear(q,True)
        self.assertEqual(r['modo'],'hipotetica');self.assertEqual(r['alts_usadas'],[])

if __name__=='__main__':unittest.main()
