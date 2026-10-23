import json,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from roteamento_v15.texto import Leitor,apenas_referencia_normativa
from roteamento_v15 import modelo as m

class TestContexto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).resolve().parents[2]
        cls.qs={q['id']:q for q in map(json.loads,(p/'dados/anexos/questoes.jsonl').read_text().splitlines())}
        cls.cat,_=carregar_catalogo(p)
        cls.dic=Dicionario(json.loads((p/'vocabulario_v8/dicionario.json').read_text()),cls.cat.temas,cls.cat.familias)
        cls.leitor=Leitor(cls.cat,cls.dic)
    def q(self,en,cmd='',alts=None):
        return {'id':'nova','enunciado_html':en,'comando':cmd,'alternativas':alts or {'C':'Certo','E':'Errado'}}
    def test_q0052_preserva_situacao_e_todos_os_itens(self):
        r=self.leitor.rotear(self.qs['Q0052'])
        self.assertIn('300 dias',r['en_usado']);self.assertEqual(len(r['itens_usados']),4)
        self.assertTrue(r['cabecalho_prioritario']);self.assertFalse(r['primeiro_item_fallback'])
        self.assertFalse(r['maioria_aplicada']);self.assertEqual(r['alts_usadas'],[])
    def test_q0124_cabecalho_curto_tematico_e_prioritario(self):
        r=self.leitor.rotear(self.qs['Q0124'])
        self.assertIn('teorias das penas',r['en_usado']);self.assertTrue(r['cabecalho_prioritario'])
        self.assertEqual(len(r['itens_usados']),5);self.assertEqual(r['alts_usadas'],[])
    def test_cabecalho_curto_generico_e_omitido_sem_apagar_itens(self):
        r=self.leitor.rotear(self.q('É certo afirmar:<br>I. Busca e apreensão.<br>II. Prova testemunhal.'))
        self.assertEqual(r['en_usado'],'');self.assertEqual(len(r['itens_usados']),2)
    def test_q0028_explique_procedimento_remete_aos_artigos_no_enunciado(self):
        r=self.leitor.rotear(self.qs['Q0028'])
        self.assertTrue(r['comando_retoma_enunciado']);self.assertIn('406',r['en_usado'])
        self.assertFalse(r['sem_evidencia']);self.assertEqual(r['alts_usadas'],[])
    def test_q0275_nao_substitui_citacao_por_lei_sozinha(self):
        r=self.leitor.rotear(self.qs['Q0275'])
        self.assertTrue(r['norma_sem_contexto']);self.assertFalse(r['comando_tematico'])
        self.assertIn('citado',r['en_usado']);self.assertTrue(r['alts_usadas'])
    def test_q0316_conserva_lei_e_contexto_sem_resolver_resposta(self):
        q=self.qs['Q0316'];r=self.leitor.rotear(q)
        self.assertEqual(r['en_usado'],f.visivel(q['enunciado_html']))
        self.assertIn('20',r['cmd_usado']);self.assertTrue(r['comando_retoma_enunciado'])
        self.assertTrue(r['en_usado']);self.assertEqual(r['alvos_forcados'],[])
    def test_norma_cp_cpp_permanece_distinta(self):
        cp=self.leitor.norma_comando('Explique o art. 20 do Código Penal.')
        cpp=self.leitor.norma_comando('Explique o art. 20 do Código de Processo Penal.')
        self.assertNotEqual(cp,cpp);self.assertTrue(apenas_referencia_normativa('Conforme a Lei nº 9.099/1995.'))
    def test_lei_sozinha_nao_certifica_evidencia(self):
        r=self.leitor.rotear(self.q('', 'Explique a Lei nº 9.099/1995.'))
        self.assertTrue(r['sem_evidencia']);self.assertFalse(r['comando_tematico'])
    def test_lei_no_cabecalho_permanece_vinculada_as_proposicoes(self):
        r=self.leitor.rotear(self.q('Segundo a Lei nº 9.099/1995:<br>I. A transação penal tem requisitos.<br>II. A composição civil tem efeitos.'))
        self.assertIn('9.099',r['en_usado']);self.assertEqual(len(r['itens_usados']),2)
        self.assertFalse(r['cabecalho_prioritario']);self.assertFalse(r['sem_evidencia'])
    def test_q0319_coautoria_normalizada_e_comando_conservado(self):
        r=self.leitor.rotear(self.qs['Q0319'])
        self.assertIn('coautoria',r['cmd_usado']);self.assertTrue(r['comando_tematico'])
        self.assertEqual(len(r['itens_usados']),3)
    def test_q0202_comando_nao_descarta_desconhecimento_da_idade(self):
        r=self.leitor.rotear(self.qs['Q0202'])
        self.assertIn('não sabia',r['cmd_usado']);self.assertTrue(r['en_usado'])
    def test_case_narrado_preserva_alternativas_e_narrativa(self):
        r=self.leitor.rotear(self.q('No caso narrado, João foi preso por crime funcional.','Que recurso cabe?',{'A':'Apelação.','B':'Agravo.'}))
        self.assertTrue(r['en_usado']);self.assertEqual(len(r['alts_usadas']),2)
    def test_todos_os_itens_permanecem_mesmo_sem_assunto_majoritario(self):
        r=self.leitor.rotear(self.q('I. Roubo.<br>II. Recurso de apelação.<br>III. Vitimologia.'))
        self.assertEqual(r['itens_escolhidos'],[0,1,2]);self.assertFalse(r['maioria_aplicada'])
    def test_ce_nao_inventa_atributos_de_alternativas(self):
        q=self.q('A respeito do inquérito policial, julgue a assertiva.')
        pp=m.preparar(self.cat,self.dic,{'nova':q})
        for v in pp:
            for n in ['alt_palavra_media','alt_escopo_media','alt_escopo_max']:
                np.testing.assert_array_equal(pp[v]['nova']['x'][:,m.NOMES.index(n)],0)
    def test_ids_e_metadados_nao_afetam_novas_rotas_ou_atributos(self):
        q=self.q('À luz das teorias das penas, julgue:<br>I. Kant.<br>II. Hegel.')
        outra={**q,'id':'Q9999','disciplina_origem':'Outra','assunto_origem':'Mudou'}
        a=m.preparar(self.cat,self.dic,{'nova':q});b=m.preparar(self.cat,self.dic,{'Q9999':outra})
        for v in a:
            np.testing.assert_array_equal(a[v]['nova']['x'],b[v]['Q9999']['x'])
            np.testing.assert_array_equal(a[v]['nova']['ranking'],b[v]['Q9999']['ranking'])
    def test_treino_rejeita_rotulo_externo(self):
        with self.assertRaisesRegex(ValueError,'rótulos externos'):m.ajustar({'a':{}},{'b':{}},self.cat)

if __name__=='__main__':unittest.main()
