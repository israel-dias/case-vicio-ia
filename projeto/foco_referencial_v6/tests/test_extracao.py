import unittest
from foco_referencial_v6.extracao import extrair


class TestExtracao(unittest.TestCase):
    def test_nao_le_alternativas_ou_metadados(self):
        q={'enunciado_html':'Julgue o item.', 'alternativas':{'A':'A respeito da lei.'},
           'assunto_origem':'Em relação ao crime.'}
        self.assertFalse(extrair(q)['presente'])

    def test_foco_explicito_preserva_conteudo(self):
        r=extrair({'enunciado_html':'A respeito da interceptação telefônica, julgue o item.'})
        self.assertEqual(r['texto_foco'],'interceptação telefônica')

    def test_retomada_citacao_proxima_preserva_negacao(self):
        r=extrair({'enunciado_html':'A conduta foi “modificar sistema sem autorização”. A prática desta conduta configura:'})
        self.assertIn('sem autorização',r['texto_foco'])
        self.assertTrue(any(x['retomada_textual'] for x in r['marcadores']))

    def test_considerando_nao_implica_tema(self):
        r=extrair({'enunciado_html':'Considerando as afirmativas abaixo, assinale a correta.'})
        self.assertEqual(r['texto_foco'],'as afirmativas abaixo')
        self.assertNotIn('tema_central_id',r)

    def test_script_nao_vira_marcador(self):
        r=extrair({'enunciado_html':'Questão.<script>A respeito da lei.</script>'})
        self.assertFalse(r['presente'])

    def test_id_nao_altera_extracao(self):
        q={'id':'Q1','enunciado_html':'Em relação à conduta, assinale a correta.'}
        self.assertEqual(extrair(q),extrair({**q,'id':'outro'}))

    def test_nao_ignora_negacao(self):
        r=extrair({'enunciado_html':'No que se refere aos atos que não constituem crime, assinale a correta.'})
        self.assertIn('não constituem crime',r['texto_foco'])
