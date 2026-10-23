"""Contratos que protegem referências, avaliação e independência dos IDs."""
import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a
from melhorias_v3.representacao import Referencias,carregar_catalogo,lexico
from melhorias_v3.experimento import validar_grupos
from melhorias_v3 import runtime as novo_runtime


class TestMelhoriasV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo,cls.base=carregar_catalogo(ROOT)
        cls.refs=cls.catalogo.referencias

    def test_cp_cpp_e_militares_nao_sao_confundidos(self):
        for texto,norma in [('art. 20 do CP','cp'),('art. 20 do CPP','cpp'),
                            ('art. 20 do Código Penal Militar','cpm'),('art. 20 do CPPM','cppm')]:
            r=self.refs.extrair(texto)
            self.assertEqual(r['normas'],[norma]);self.assertEqual(r['artigos'],[[norma,'20']])

    def test_citacoes_com_ordinais_anos_e_lei_sem_ano(self):
        for texto in ['Art. 1º da Lei n.º 9.296/96','artigo 1 da Lei 9296 de 1996',
                      'Art. 1 da Lei nº 9.296, de 24 de julho de 1996','art. 1 da Lei 9.296']:
            r=self.refs.extrair(texto)
            self.assertEqual(r['normas'],['lei:9296/1996'])
            self.assertEqual(r['artigos'],[['lei:9296/1996','1']])

    def test_artigo_sem_norma_nao_recebe_codigo_inventado(self):
        self.assertEqual(self.refs.extrair('art. 20')['artigos'],[])
        self.assertEqual(self.refs.extrair('art. 20',['cp','cpp'])['artigos'],[])
        self.assertEqual(self.refs.extrair('art. 20',['cp'])['artigos'],[['cp','20']])

    def test_normas_proximas_ficam_com_seus_artigos(self):
        r=self.refs.extrair('art. 20 do CP; art. 155 do CPP.')
        self.assertEqual(r['artigos'],[['cp','20'],['cpp','155']])

    def test_artigos_identicos_em_codigos_diferentes_nao_compartilham_apoio(self):
        cp=self.refs.apoio(self.refs.extrair('art. 20 do CP'),'5218',self.catalogo.temas)
        cpp=self.refs.apoio(self.refs.extrair('art. 20 do CPP'),'5218',self.catalogo.temas)
        self.assertEqual(cp[1],1.);self.assertEqual(cpp[1],0.)

    def test_alias_de_norma_nao_funde_ids_homonimos(self):
        y={'tema_central_id':'4703','extras_ids':'','fora_da_taxonomia':'0'}
        r=self.refs.extrair('Lei de Execução Penal')
        self.assertGreater(self.refs.apoio(r,'4703',self.catalogo.temas)[0],0)
        self.assertGreater(self.refs.apoio(r,'6734',self.catalogo.temas)[0],0)
        self.assertFalse(f.aceito('6734',y,self.catalogo.temas))

    def test_atributos_ignoram_id_preservam_negacao_e_alternativas(self):
        q={'id':'NOVO_A','enunciado_html':'<b>Não</b> se admite interceptação. <!-- omitir --><script>furto</script>',
           'comando':'Julgue.','alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'Processo Penal','assunto_origem':''}
        q2={**q,'id':'OUTRO_ID'}
        with patch('socket.create_connection',side_effect=AssertionError('Sem rede')):
            ps=self.catalogo.transformar({'a':q,'b':q2})
        self.assertTrue(f.np.array_equal(ps['a']['features_v3'],ps['b']['features_v3']))
        self.assertIn('nao',f.campos(q)['completo'])
        self.assertNotIn('furto',f.campos(q)['completo'])
        self.assertEqual(len(ps['a']['refs_extraidas']['alternativas']),2)

    def test_normalizacao_adicional_nao_reescreve_textos_de_entrada(self):
        t='Não se admitem intercepções telefônicas.'
        self.assertEqual(lexico(t,self.catalogo.aliases),'nao se admitem interceptacao telefonica')
        self.assertEqual(t,'Não se admitem intercepções telefônicas.')

    def test_ajuste_rejeita_rotulo_externo(self):
        with self.assertRaises(ValueError):a.ajustar({'a':{}},{'a':{},'b':{}},[],{},True)

    def test_particoes_rejeitam_duplicatas_e_sobreposicao(self):
        ps={'a':{'hash':'x'},'b':{'hash':'x'}}
        with self.assertRaises(ValueError):validar_grupos(ps,['a'],['b'],ps)
        with self.assertRaises(ValueError):validar_grupos(ps,['a'],['a','b'],ps)

    def test_suporte_minimo_e_precisao_indefinida_sao_preservados(self):
        rows=[{'id':str(i),'elegivel':True,'correto':1,'confianca':.99,'decisao':'revisar','fora_oficial':0} for i in range(2)]
        self.assertFalse(a.politica(rows,[.99,.99])['ativa'])
        self.assertIsNone(a.resumo(rows)['precisao_publicadas'])

    def test_mapa_nao_contem_questoes_ou_respostas_por_id(self):
        texto=(ROOT/'melhorias_v3/dados/referencias_normativas_v1.json').read_text()
        self.assertNotRegex(texto,r'Q\d{4}')
        dados=json.loads(texto)
        alterado=copy.deepcopy(dados);alterado['intervalos_artigos'][0]['temas_ids']=['999999']
        with self.assertRaises(ValueError):Referencias(alterado,self.catalogo.temas)


class TestRuntimeCongeladoV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta=ROOT/'artefatos/melhorias_v3'
        if not cls.pasta.exists():raise unittest.SkipTest('Artefato congelado ainda não foi criado.')
        cls.runtime=novo_runtime.Runtime(cls.pasta)

    def item(self):
        return {'id':'NOVA','enunciado_html':'De acordo com o art. 20 do CP, julgue a assertiva sobre erro de tipo.',
                'comando':'','alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'Direito Penal','assunto_origem':''}

    def test_inferencia_sem_folha_verdade_sem_treino_sem_rede(self):
        abrir=Path.open
        def guard(path,*args,**kwargs):
            if Path(path).name=='folha_verdade.csv':raise AssertionError('Classificação tentou ler rótulos.')
            return abrir(path,*args,**kwargs)
        with patch.object(Path,'open',guard),patch.object(a,'ajustar',side_effect=AssertionError('Treino')),\
             patch.object(f,'ajustar_linear',side_effect=AssertionError('Treino')),\
             patch('socket.create_connection',side_effect=AssertionError('Rede')):
            runtime=novo_runtime.Runtime(self.pasta)
            row,trace=runtime.classificar(self.item())
        self.assertIn(row['decisao'],['publicar','revisar'])
        self.assertTrue(0<float(row['confianca'])<1)

    def test_trocar_id_nao_muda_resultado(self):
        q=self.item();r1,_=self.runtime.classificar(q)
        q['id']='OUTRA';r2,_=self.runtime.classificar(q)
        for k in ['decisao','tema_central_id','extras_ids','confianca','motivo']:self.assertEqual(r1[k],r2[k])

    def test_modelo_nao_tem_gabaritos_por_questao(self):
        self.assertNotRegex((self.pasta/'modelo.json').read_text(),r'Q\d{4}')

    def test_artefato_alterado_e_rejeitado(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            copia=Path(tmp)/'modelo';shutil.copytree(self.pasta,copia)
            mapa=copia/'referencias_normativas_v1.json';mapa.write_text(mapa.read_text()+' ')
            with self.assertRaises(ValueError):novo_runtime.Runtime(copia)

    def test_csv_reproduz_sem_rotulos_e_saida_existente_e_preservada(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta=Path(tmp);dados=pasta/'questoes.jsonl'
            dados.write_text(json.dumps(self.item(),ensure_ascii=False)+'\n')
            novo_runtime.executar(self.pasta,dados,pasta/'a')
            novo_runtime.executar(self.pasta,dados,pasta/'b')
            self.assertEqual((pasta/'a/publicacao.csv').read_bytes(),(pasta/'b/publicacao.csv').read_bytes())
            with self.assertRaises(ValueError):novo_runtime.executar(self.pasta,dados,pasta/'a')


if __name__=='__main__':unittest.main()
