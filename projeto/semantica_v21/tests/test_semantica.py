import copy,csv,json,socket,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from semantica_v21 import modelo as m
from semantica_v21.textos import vistas,hash_texto
from semantica_v22 import qualidade
from preparar_semantica_verificada import verificar_modelo


class TestSemantica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat,_=carregar_catalogo(ROOT);cls.busca=m.Busca(ROOT,cls.cat,ROOT/'artefatos/semantica_v21')
        cls.qs={q['id']:q for q in map(json.loads,(ROOT/'dados/anexos/questoes.jsonl').read_text().splitlines())}

    def test_id_e_origem_nao_mudam_textos_vetores_ou_ranking(self):
        q=self.qs['Q0208'];n={**q,'id':'NOVO_ID','disciplina_origem':'outra','assunto_origem':'inventado'}
        pp=self.busca.preparar({'a':q,'b':n})
        self.assertTrue(f.np.array_equal(pp['a']['x'],pp['b']['x']))
        self.assertEqual(pp['a']['textos_sha256'],pp['b']['textos_sha256'])

    def test_texto_novo_exige_preparacao_sem_devolver_vetor_do_id(self):
        q={**self.qs['Q0208'],'comando':'Texto diferente sem embedding ainda preparado.'}
        with self.assertRaisesRegex(ValueError,'sem embedding preparado'):self.busca.preparar({'Q0208':q})

    def test_comando_especifico_foca_autoria_sem_apagar_alternativas(self):
        vs,tr=vistas(self.qs['Q0208'],self.busca.ex,self.busca.det)
        self.assertEqual(tr['origem'],'comando_identificado_com_alternativas')
        self.assertIn('partícipe',vs['foco'].lower())
        self.assertLess(len(vs['foco']),len(vs['integral']))
        self.assertNotIn('\nCerto',vs['foco']);self.assertNotIn('\nErrado',vs['foco'])

    def test_cabecalho_geral_nao_oculta_assertiva_e_ce_nao_e_tema(self):
        vs,tr=vistas(self.qs['Q0274'],self.busca.ex,self.busca.det)
        self.assertIn('latrocínio',vs['foco'].lower());self.assertNotIn('\nCerto',vs['foco']);self.assertNotIn('\nErrado',vs['foco'])

    def test_proposicoes_e_negacoes_preservadas(self):
        vs,_=vistas(self.qs['Q0052'],self.busca.ex,self.busca.det)
        for k in ['I.','II.','III.']:self.assertIn(k,vs['integral'])
        q={**self.qs['Q0052'],'comando':'Indique o que não está correto nas proposições.'}
        nova,_=vistas(q,self.busca.ex,self.busca.det)
        self.assertIn('não',nova['integral'].lower())

    def test_vf_nao_perde_proposicoes(self):
        vs,_=vistas(self.qs['Q0526'],self.busca.ex,self.busca.det)
        self.assertEqual(vs['integral'].count('( )'),3)
        self.assertEqual(vs['foco'].count('( )'),3)

    def test_vetores_finitos_normalizados_e_licenca_registrada(self):
        reg=json.loads((ROOT/'artefatos/semantica_v21/manifesto.json').read_text())
        self.assertEqual(reg['licenca'],'MIT');self.assertFalse(reg['rotulos_lidos']);self.assertLessEqual(reg['max_tokens_observado'],512)
        for v in self.busca.vec.values():self.assertAlmostEqual(float(f.np.linalg.norm(v)),1,places=5)

    def test_arquivo_adulterado_rejeitado_antes_de_carregar_vetores(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);reg=json.loads((ROOT/'artefatos/semantica_v21/manifesto.json').read_text());(p/'manifesto.json').write_text(json.dumps(reg));(p/'vetores.json.gz').write_bytes(b'alterado')
            with self.assertRaisesRegex(ValueError,'Cache alterado'):m.Busca(ROOT,self.cat,p)

    def test_pesos_invalidos_rejeitados_antes_de_importar_encoder(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'Pesos ou tokenizer diferentes'):verificar_modelo(td)

    def test_preparar_perfis_sem_rotulos_rede_encoder_ou_treino(self):
        abrir=Path.open
        def protegido(p,*a,**kw):
            if p.name=='folha_verdade.csv':raise AssertionError('rótulos')
            return abrir(p,*a,**kw)
        with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')),patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('treino')):
            pp=self.busca.preparar({'q':self.qs['Q0508']})
        self.assertEqual(set(pp),{'q'})
        self.assertNotIn('onnxruntime',sys.modules);self.assertNotIn('tokenizers',sys.modules)

    def test_tema_raiz_inativo_irmao_nao_sao_equivalentes(self):
        y={'tema_central_id':'5224','extras_ids':'','fora_da_taxonomia':'0'}
        self.assertTrue(f.aceito('5218',y,self.cat.temas));self.assertFalse(f.aceito('5211',y,self.cat.temas))
        for t in self.cat.familias:self.assertTrue(f.elegivel(t,self.cat.temas));self.assertEqual(self.cat.temas[t]['nivel'],1)

    def test_estimador_qualidade_nao_muda_tema(self):
        p=self.busca.preparar({'q':self.qs['Q0508']});tid=self.cat.familias[0]
        r={'id':'q','tema_central_id':tid,'elegivel':True,'identificador_forte_cmd':False,'motivos_bloqueio':''}
        pack={'modelo':{'dimensao':3,'constante':.8},'atributos':qualidade.ATRIBUTOS['margens'],'politica':{'ativa':False,'limiar':1,'suporte_interno':0}}
        rr=qualidade.aplicar([r],p,self.cat,'margens',pack)
        self.assertEqual(rr[0]['tema_central_id'],tid);self.assertEqual(rr[0]['decisao'],'revisar');self.assertEqual(rr[0]['confianca'],.8)


if __name__=='__main__':unittest.main()
