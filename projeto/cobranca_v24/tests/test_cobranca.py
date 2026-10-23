import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from cobranca_v24.texto import Leitura
from cobranca_v24.modelo import compor


class TestCobranca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat,_=carregar_catalogo(ROOT);cls.leitor=Leitura(cls.cat)
        cls.qs={q['id']:q for q in map(json.loads,(ROOT/'dados/anexos/questoes.jsonl').read_text().splitlines())}

    def test_final_do_enunciado_recupera_cobranca_sem_comando(self):
        q,tr,d=self.leitor.preparar(self.qs['Q0215']);self.assertTrue(d['forte']);self.assertEqual(d['familias'],['5199']);self.assertEqual(tr['origem_leitura'],'cobranca_final_do_enunciado')
        self.assertIn('regime inicial',q['comando'].lower());self.assertEqual(q['alternativas'],self.qs['Q0215']['alternativas'])

    def test_penal_isolado_nao_e_identificador_especifico(self):
        for s in ['Penal','Direito Penal','Processo Penal','conforme o CPP','art. 406 do CPP']:
            self.assertFalse(self.leitor.detectar(s)['forte'],s)

    def test_comando_generico_nao_descarta_enunciado_e_alternativas(self):
        q={'id':'x','enunciado_html':'Uma narrativa de fatos a ser examinada.','comando':'Assinale a alternativa correta.','alternativas':{'A':'Uma possibilidade.','B':'Outra possibilidade.'}}
        n,tr,d=self.leitor.preparar(q);self.assertFalse(d['forte']);self.assertEqual(n['comando'],'');self.assertEqual(n['enunciado_html'],q['enunciado_html']);self.assertEqual(n['alternativas'],q['alternativas'])

    def test_nao_usa_limite_de_caracteres_para_comando_generico(self):
        q={'id':'x','enunciado_html':'O texto a analisar.','comando':'Assinale a alternativa correta. '*20,'alternativas':{'C':'Certo','E':'Errado'}}
        n,tr,d=self.leitor.preparar(q);self.assertFalse(d['forte']);self.assertEqual(n['comando'],'')

    def test_comando_informativo_sem_identificador_nao_perde_informacao(self):
        q={'id':'x','enunciado_html':'Narrativa para interpretar.','comando':'Analise os fatos e a possibilidade de responsabilizacao dos envolvidos.','alternativas':{'C':'Certo','E':'Errado'}}
        n,tr,d=self.leitor.preparar(q);self.assertFalse(d['forte']);self.assertEqual(n['comando'],q['comando']);self.assertEqual(tr['origem_leitura'],'comando_sem_identificador_preservado_como_apoio')

    def test_efeito_condenacao_tem_prioridade_no_comando(self):
        _,tr,d=self.leitor.preparar(self.qs['Q0313']);self.assertEqual(d['familias'],['5199']);self.assertTrue(d['forte']);self.assertEqual(tr['origem_leitura'],'comando_especifico')

    def test_retomada_recupera_objeto_do_enunciado(self):
        n,tr,d=self.leitor.preparar(self.qs['Q0320']);self.assertTrue(d['forte']);self.assertEqual(d['familias'],['5543']);self.assertEqual(tr['origem_leitura'],'retomada_do_enunciado')

    def test_citacoes_convergentes_com_ato_diferem_de_lei_isolada(self):
        _,tr,d=self.leitor.preparar(self.qs['Q0028']);self.assertTrue(d['forte']);self.assertEqual(d['familias'],['5524'])
        self.assertTrue(any(h['tipo']=='citacao_e_ato_contextualizados' for h in d['hits']))

    def test_assertiva_final_ce_preserva_negacao_e_nao_resolve_gabarito(self):
        n,tr,d=self.leitor.preparar(self.qs['Q0274']);self.assertEqual(d['familias'],['5175']);self.assertTrue(d['forte']);self.assertIn('tentativa',n['comando']);self.assertEqual(n['alternativas'],{'C':'Certo','E':'Errado'})

    def test_proposicoes_numeradas_e_vf_nao_sao_reduzidas_ao_final(self):
        for i in ['Q0052','Q0324','Q0526']:
            n,tr,d=self.leitor.preparar(self.qs[i]);self.assertEqual(n['enunciado_html'],self.qs[i]['enunciado_html']);self.assertEqual(tr['origem_leitura'],'proposicoes_preservadas')

    def test_veto_de_crime_apenas_contextual(self):
        self.assertTrue(self.leitor.contexto_sem_cobranca(self.qs['Q0252'],'5157'))
        q={**self.qs['Q0252'],'comando':'Explique os elementos do estelionato.'}
        self.assertFalse(self.leitor.contexto_sem_cobranca(q,'5157'))

    def test_publicacao_anterior_nao_e_protegida_de_conflito(self):
        q=self.qs['Q0215'];b={'id':'q','tema_central_id':'5572','decisao':'publicar','confianca':.9};r={'id':'q','tema_central_id':'5199','decisao':'revisar','confianca':.7,'motivo':'abaixo_do_limiar_calibrado'}
        z=compor([r],[b],{'q':q},self.leitor,'revalidar_cobranca')[0];self.assertEqual(z['tema_central_id'],'5199');self.assertEqual(z['decisao'],'revisar');self.assertEqual(z['confianca'],.7)

    def test_identificador_contextual_nao_implica_publicacao(self):
        q=self.qs['Q0252'];b={'id':'q','tema_central_id':'5157','decisao':'publicar','confianca':.95238};r={'id':'q','tema_central_id':'5199','decisao':'revisar','confianca':.65}
        z=compor([r],[b],{'q':q},self.leitor,'revalidar_cobranca')[0];self.assertEqual(z['decisao'],'revisar');self.assertTrue(z['veto_contexto'])

    def test_novo_identificador_nao_inventa_piso_de_confianca(self):
        _,_,d=self.leitor.preparar(self.qs['Q0215']);self.assertTrue(d['forte']);self.assertNotIn('confianca',d)

    def test_id_e_origem_nao_mudam_a_leitura(self):
        q=self.qs['Q0215'];n={**q,'id':'NOVO','disciplina_origem':'inventado','assunto_origem':'outro'}
        a,ta,da=self.leitor.preparar(q);b,tb,db=self.leitor.preparar(n);self.assertEqual(ta,tb);self.assertTrue(f.np.array_equal(da['scores'],db['scores']))

    def test_regua_nao_e_relaxada_para_irmaos_ou_homonimos(self):
        y={'tema_central_id':'5224','extras_ids':'','fora_da_taxonomia':'0'}
        self.assertTrue(f.aceito('5218',y,self.cat.temas));self.assertFalse(f.aceito('5211',y,self.cat.temas))
        y={'tema_central_id':'4703','extras_ids':'','fora_da_taxonomia':'0'};self.assertFalse(f.aceito('6734',y,self.cat.temas))


if __name__=='__main__':unittest.main()
