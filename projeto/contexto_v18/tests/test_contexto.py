import json,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from roteamento_v15.texto import Leitor
from contexto_v18 import modelo as m
from contexto_v18.texto import Identificadores,passagens,questao_estrita,frases


class TestTexto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projeto=Path(__file__).resolve().parents[2]
        cls.cat,_=carregar_catalogo(cls.projeto)
        cls.dic=Dicionario(json.loads((cls.projeto/'vocabulario_v8/dicionario.json').read_text()),cls.cat.temas,cls.cat.familias)
        cls.det=Identificadores(cls.cat);cls.leitor=Leitor(cls.cat,cls.dic)

    def q(self,cmd,en='Narrativa de contexto.',alts=None):
        return {'id':'nova','comando':cmd,'enunciado_html':en,'alternativas':alts or {'C':'Certo','E':'Errado'},
                'disciplina_origem':'Penal','assunto_origem':'Contexto de origem'}

    def test_plural_e_papeis_compostos_sao_identificador_de_catalogo(self):
        d=self.det.analisar(self.q('Lucas foi o autor de homicídio e Carlos figurou como partícipe do crime.'))
        self.assertTrue(d['forte'])
        h=[x for x in d['hits'] if x['titulo']=='Autores e Partícipes']
        self.assertEqual(len(h),1);self.assertGreater(h[0]['forca'],0)

    def test_autor_conduta_resultado_genericos_nao_ativam(self):
        for cmd in ['Explique a conduta e o resultado.','Assinale a alternativa correta.','Quem é o autor?']:
            self.assertFalse(self.det.analisar(self.q(cmd))['forte'])

    def test_adjetivo_impossivel_nao_e_crime_impossivel(self):
        d=self.det.analisar(self.q('Complete a frase indicando em quais crimes a coautoria é impossível.'))
        self.assertTrue(d['forte'])
        self.assertTrue(any(h['familia']=='5071' for h in d['hits']))
        self.assertFalse(any(h['titulo']=='Crime Impossível' for h in d['hits']))

    def test_expressao_crime_impossivel_completa_e_aceita(self):
        d=self.det.analisar(self.q('Explique o crime impossível.'))
        self.assertTrue(any(h['titulo']=='Crime Impossível' for h in d['hits']))

    def test_artigo_isolado_nao_e_identificador_forte(self):
        self.assertFalse(self.det.analisar(self.q('Explique o artigo 20 do CP.'))['forte'])

    def test_artigo_compartilhado_respeita_o_codigo(self):
        a=self.det.analisar(self.q('Explique o artigo 20 do CP.','Conforme artigo 20 do CP, examine a situação.'))
        b=self.det.analisar(self.q('Explique o artigo 20 do CP.','Conforme artigo 20 do CPP, examine a situação.'))
        self.assertTrue(a['forte']);self.assertFalse(b['forte'])

    def test_lei_sem_repeticao_no_enunciado_nao_ativa(self):
        self.assertFalse(self.det.analisar(self.q('Explique a Lei de Execução Penal.'))['forte'])

    def test_lei_especifica_repetida_pode_ativar_sem_fundir_ramos(self):
        q=self.q('Explique a Lei de Execução Penal.','A Lei de Execução Penal rege a situação descrita.')
        d=self.det.analisar(q);self.assertTrue(d['forte'])
        self.assertGreater(d['scores'][self.cat.familias.index('4703')],0)
        self.assertGreater(d['scores'][self.cat.familias.index('6734')],0)

    def test_estrito_retira_narrativa_e_metadados_sem_apagar_alternativas(self):
        q=self.q('Explique a interceptação telefônica.')
        e=questao_estrita(q,self.det.analisar(q))
        self.assertEqual(e['enunciado_html'],'');self.assertEqual(e['disciplina_origem'],'')
        self.assertEqual(e['assunto_origem'],'');self.assertEqual(e['alternativas'],q['alternativas'])

    def test_estrito_real_nao_vaza_narrativa_nem_origem_nos_atributos(self):
        a=self.q('Explique a interceptação telefônica.','Uma narrativa sobre homicídio e pena.')
        b={**a,'id':'outra','enunciado_html':'Um texto sobre criminologia e vitimologia.','disciplina_origem':'Criminologia','assunto_origem':'Vítimas'}
        ps=m.preparar(self.cat,self.dic,{'nova':a,'outra':b})
        for v in ['comando_estrito','estrito_pares']:
            np.testing.assert_array_equal(ps[v]['nova']['x'],ps[v]['outra']['x'])
            np.testing.assert_array_equal(ps[v]['nova']['ranking'],ps[v]['outra']['ranking'])
            self.assertEqual(ps[v]['nova']['candidatos'],ps[v]['outra']['candidatos'])
            self.assertTrue(ps[v]['nova']['excluiu_narrativa'])

    def test_comando_generico_mantem_enunciado(self):
        q=self.q('Assinale a alternativa correta.','A respeito da interceptação telefônica, examine o fato.')
        ps=m.preparar(self.cat,self.dic,{'nova':q})
        self.assertFalse(ps['comando_estrito']['nova']['excluiu_narrativa'])
        self.assertIn('interceptação',ps['comando_estrito']['nova']['rota']['en_usado'])

    def test_passagens_preservam_negacao_antecedente_e_texto_integral(self):
        q=self.q('Explique a situação descrita.','João não sabia a idade da vítima. Nessa situação, desconhecia uma condição relevante. O agente foi interrogado.')
        p=passagens(q,self.leitor)
        self.assertTrue(any('não sabia' in x and 'Nessa situação' in x for x in p['janelas']))
        self.assertIn('não sabia',p['texto_relacoes'])
        self.assertIn('interrogado',p['rota']['texto_efetivo'])

    def test_certo_errado_nao_oferece_temas_nas_alternativas(self):
        p=passagens(self.q('Explique a prescrição.'),self.leitor)
        self.assertTrue(p['certo_errado']);self.assertEqual(p['rota']['alts_usadas'],[])

    def test_todos_os_itens_permanecem_com_cabecalho(self):
        q=self.q('Julgue os itens.','Sobre a execução penal:<br>I. O trabalho pode remir pena.<br>II. A falta grave tem efeitos próprios.<br>III. A medida de segurança exige análise.')
        p=passagens(q,self.leitor);self.assertEqual(len(p['itens_preservados']),3)
        self.assertEqual(len(p['janelas']),3)
        self.assertTrue(all('execução penal' in s for s in p['janelas']))

    def test_nao_fraciona_citacao_em_artigo_e_numero(self):
        self.assertIn('art. 20',frases('Conforme art. 20 do CP, julgue. Nessa situação, há dúvida.')[0])


class TestPares(unittest.TestCase):
    def dados(self):
        cat=SimpleNamespace(familias=['1','2','3'],temas={str(j):{'parent_id':'','nivel':1,'ativo':True} for j in [1,2,3]})
        p={'x':np.ones((3,len(m.ATRIBUTOS['passagens_pares']))),'hash':'h','candidatos':[0,1]}
        y={'tema_central_id':'3','extras_ids':'','fora_da_taxonomia':'0'}
        return cat,p,y

    def test_nao_injeta_rotulo_ausente_nos_candidatos(self):
        cat,p,y=self.dados()
        with patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('Não existem pares válidos')):
            mod=m.ajustar({'a':p},{'a':y},cat,'passagens_pares')
        self.assertEqual(mod['questoes_com_pares'],0);self.assertEqual(p['candidatos'],[0,1])

    def test_fora_nao_cria_par_positivo(self):
        cat,p,y=self.dados();y['fora_da_taxonomia']='1';y['tema_central_id']=''
        mod=m.ajustar({'a':p},{'a':y},cat,'passagens_pares')
        self.assertEqual(mod['questoes_com_pares'],0)

    def test_rotulos_externos_sao_rejeitados(self):
        cat,p,y=self.dados()
        with self.assertRaisesRegex(ValueError,'externos'):m.ajustar({'a':p},{'b':y},cat,'passagens_pares')

    def test_sugestao_sem_sinal_nao_quebra_lista_de_candidatos(self):
        self.assertEqual(len(m.candidato_indices((np.zeros(3),5))),1)


if __name__=='__main__':unittest.main()
