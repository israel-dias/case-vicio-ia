import copy
import json
import math
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from vocabulario_v8.texto import Dicionario
from vocabulario_v8.experimento import preparar,ajustar


class TestVocabulario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[2]
        cls.cat,_=carregar_catalogo(root)
        cls.dados=json.loads((root/'vocabulario_v8/dicionario.json').read_text())
        cls.dic=Dicionario(cls.dados,cls.cat.temas,cls.cat.familias)

    def q(self,en,**kw):
        return {'id':'X','enunciado_html':en,'comando':'','alternativas':{'C':'Certo','E':'Errado'},**kw}

    def test_interceptacao_reconhece_expressoes_intercaladas(self):
        _,h=self.dic.encontrar('A respeito da interceptação das comunicações telefônicas.')
        self.assertTrue(any(x['grupo']=='interceptacao' for x in h))

    def test_lei_com_numero_pontuacao_e_ano(self):
        for t in ['Lei nº 9.099/1995','Lei n.º 9.099/1995','Lei 9.296/1996']:
            with self.subTest(t=t):self.assertTrue(self.dic.encontrar(t)[1])

    def test_juizado_singular_e_plural(self):
        for t in ['Juizado Especial Criminal','Juizados Especiais Criminais']:
            with self.subTest(t=t):self.assertTrue(self.dic.encontrar(t)[1])

    def test_sinonimos_e_repeticoes_nao_inflam_grupo(self):
        a,_=self.dic.encontrar('apelação')
        b,_=self.dic.encontrar('recurso de apelação; apelação; recurso de apelação')
        f.np.testing.assert_allclose(a,b,atol=0,rtol=0)

    def test_homonimos_permanecem_ids_distintos(self):
        _,h=self.dic.encontrar('falta grave na execução penal')
        lep=[x for x in h if x['grupo']=='execucao_penal']
        self.assertTrue(lep)
        self.assertTrue({'4703','6734'}<=set(lep[0]['temas_ids']))

    def test_marcadores_nao_sao_conteudo(self):
        x,h=self.dic.encontrar('Considerando, a respeito, em relação, como sendo.')
        self.assertFalse(h);self.assertTrue((x==0).all())

    def test_fora_do_vocabulario_nao_inventa_tema(self):
        x,h=self.dic.encontrar('A fotossíntese depende da luz.')
        self.assertFalse(h);self.assertTrue((x==0).all())

    def test_script_nao_cria_ancora(self):
        self.assertFalse(self.dic.encontrar('Texto.<script>habeas corpus</script>')[1])

    def test_id_de_questao_no_dicionario_e_rejeitado(self):
        d=copy.deepcopy(self.dados);d['grupos'][0]['padroes'].append('Q0001')
        with self.assertRaises(ValueError):Dicionario(d,self.cat.temas,self.cat.familias)

    def test_titulo_inexistente_nao_e_adivinhado(self):
        d=copy.deepcopy(self.dados);d['grupos'][0]['titulos']=['Tema inexistente']
        with self.assertRaises(ValueError):Dicionario(d,self.cat.temas,self.cat.familias)

    def test_roteamento_zerado_tambem_zera_vocabulario(self):
        q={'id':'X','enunciado_html':'Assinale a correta.','comando':'',
           'assunto_origem':'habeas corpus','alternativas':{'A':'revisão criminal','B':'apelação'}}
        x,_,r=self.dic.atributos(q)
        self.assertEqual(r['modo'],'alternativas_exclusivas')
        self.assertTrue((x[:,:2]==0).all());self.assertFalse(r['enunciado']);self.assertFalse(r['comando'])

    def test_certo_errado_preserva_vocabulario_do_enunciado(self):
        x,s,r=self.dic.atributos(self.q('O habeas corpus tem determinada função.'))
        self.assertTrue((s>0).any());self.assertTrue(r['enunciado'])
        self.assertTrue((x[:,2:5]==0).all())

    def test_metadados_nao_entram_no_dicionario(self):
        a=self.dic.atributos(self.q('Assinale a correta.',assunto_origem='habeas corpus'))
        b=self.dic.atributos(self.q('Assinale a correta.',assunto_origem='prescrição'))
        f.np.testing.assert_allclose(a[0],b[0],atol=0,rtol=0)

    def test_trocar_id_nao_muda_ranking_ou_atributos(self):
        q=self.q('A respeito da interceptação telefônica, julgue a assertiva.')
        with patch.object(socket,'create_connection',side_effect=AssertionError('Rede proibida')):
            pp=preparar(self.cat,self.dic,{'a':q,'b':{**q,'id':'Y'}})
        for campo in ['x_v8','ranking_vocabulario_fixo','ranking_vocabulario_reordena']:
            f.np.testing.assert_allclose(pp['a'][campo],pp['b'][campo],atol=0,rtol=0)

    def test_treino_rejeita_rotulo_externo(self):
        with self.assertRaises(ValueError):ajustar({'a':{}},{'b':{}},self.cat)

    def test_ablacao_ranking_nao_usa_sete_atributos_de_confianca(self):
        from vocabulario_v8.ranking import sinais
        n=len(self.cat.familias)
        perfil={'ranking_vocabulario_reordena':f.np.arange(n,dtype=float),
                'x_mescla':f.np.zeros((n,41)), 'x_v8':f.np.full((n,48),float('nan')),
                'scores':f.np.ones(n),'scores_novos':f.np.ones(n),'scores_foco':f.np.ones(n),
                'score_vocabulario':f.np.ones(n),'rota':{'conteudo_insuficiente':False}}
        r=sinais({'X':perfil},{'dimensao':41,'constante':.5},self.cat)
        self.assertEqual(len(r),1);self.assertEqual(r[0]['sinal'],0.)
