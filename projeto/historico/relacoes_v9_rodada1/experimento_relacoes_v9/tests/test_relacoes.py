import json
import unittest
from pathlib import Path
from unittest.mock import patch
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from experimento_relacoes_v9.regras import Identificador


def questao(en, alts=None):
    return {'id':'exemplo','enunciado_html':en,'comando':'',
        'alternativas':alts or {'C':'Certo','E':'Errado'},
        'disciplina_origem':'','assunto_origem':''}


class TestRelacoes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        projeto=Path(__file__).resolve().parents[2]
        cls.cat,_=carregar_catalogo(projeto)
        dados=json.loads((projeto/'vocabulario_v8/dicionario.json').read_text())
        cls.ident=Identificador(cls.cat,Dicionario(dados,cls.cat.temas,cls.cat.familias))

    def test_id_e_origem_nao_mudam_regra(self):
        q=questao('A respeito da prescrição, assinale a correta.')
        a=self.ident.analisar(q)
        b=self.ident.analisar(dict(q,id='outro',disciplina_origem='Criminologia',assunto_origem='Júri'))
        self.assertEqual(a,b)

    def test_ultima_referencia_pode_separar_contexto_da_cobranca(self):
        q=questao('Sobre o inquérito policial há informações iniciais. A respeito da prescrição, julgue o item.')
        r=self.ident.analisar(q)
        self.assertEqual(r['variantes']['relacoes_diretas']['tema_regra'],'5185')
        self.assertFalse(r['variantes']['titulos_diretos']['acionou'])

    def test_considerando_sozinho_nao_e_marcador(self):
        refs=self.ident.referencias(questao('Considerando a prescrição, julgue o item.'))
        self.assertEqual(refs,[])

    def test_homonimos_nao_sao_fundidos(self):
        r=self.ident.analisar(questao('Sobre a Lei de Execução Penal, julgue o item.'))
        self.assertEqual(set(r['candidatos_relacoes']),{'4703','6734'})
        self.assertFalse(r['variantes']['relacoes_diretas']['acionou'])

    def test_certo_errado_nao_substitui_enunciado(self):
        r=self.ident.analisar(questao('Sobre a prescrição, julgue o item.'))
        self.assertFalse(r['alternativas_tematicas'])
        self.assertEqual(r['variantes']['relacoes_alternativas']['tema_regra'],'5185')

    def test_combinacoes_i_ii_nao_substituem_assertivas(self):
        r=self.ident.analisar(questao('I. A prescrição se aplica.',{'A':'Somente I.','B':'Somente II.'}))
        self.assertFalse(r['alternativas_tematicas'])
        self.assertEqual(r['variantes']['titulos_diretos']['tema_regra'],'5185')

    def test_empate_na_media_nao_escolhe_primeiro_id(self):
        import numpy as np
        with patch.object(self.ident,'similaridades',return_value=np.ones(len(self.cat.familias))):
            r=self.ident.analisar(questao('Sobre a Lei de Execução Penal, assinale.',{'A':'Regime aberto.','B':'Regime fechado.'}))
        self.assertFalse(r['variantes']['relacoes_alternativas']['acionou'])

    def test_nao_inventa_fora_quando_nao_ha_titulo(self):
        r=self.ident.analisar(questao('Analise os dados apresentados.'))
        self.assertTrue(all(not v['acionou'] for v in r['variantes'].values()))

    def test_negacao_nao_apaga_tema(self):
        r=self.ident.analisar(questao('A respeito da prescrição, NÃO é correto afirmar:'))
        self.assertEqual(r['variantes']['relacoes_diretas']['tema_regra'],'5185')

    def test_texto_de_script_nao_vira_identificador(self):
        r=self.ident.analisar(questao('<script>prescrição</script>Analise os dados.'))
        self.assertFalse(r['variantes']['titulos_diretos']['acionou'])

    def test_codigo_regra_nao_le_folha_ou_chama_rede(self):
        with patch('socket.create_connection',side_effect=AssertionError('rede')),patch('pathlib.Path.open',side_effect=AssertionError('arquivo')):
            r=self.ident.analisar(questao('A respeito da prescrição, julgue.'))
        self.assertEqual(r['variantes']['relacoes_diretas']['tema_regra'],'5185')


if __name__=='__main__':unittest.main()
