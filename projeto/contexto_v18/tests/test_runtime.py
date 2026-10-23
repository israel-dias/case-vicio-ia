import io,json,re,socket,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from contexto_v18 import modelo as m
from classificar_contexto_v18 import executar


class TestRuntimeV18(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]
    experimento=projeto/'experimentos/contexto_v18_002'

    def test_modelos_sem_respostas_por_id(self):
        s=(self.experimento/'modelos_finais.json').read_text()
        self.assertIsNone(re.search(r'Q\d{4}',s));self.assertEqual(set(json.loads(s)['modelos']),set(m.VARIANTES))

    def test_saida_existente_preservada(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'saída nova'):executar(self.projeto,self.experimento,'ausente',tmp)

    def test_adulteracao_rejeitada_antes_da_entrada(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ex=p/'ex';ex.mkdir()
            for n in ['manifesto_inferencia.json','modelos_finais.json','escolha_antes_559.json']:
                (ex/n).write_bytes((self.experimento/n).read_bytes())
            (ex/'modelos_finais.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'alterado'):executar(self.projeto,ex,p/'ausente',p/'saida')

    def test_textos_novos_sem_rotulos_rede_treino_ou_recalibracao(self):
        q={'id':'texto_novo_a','enunciado_html':'João foi acusado de homicídio. Paulo ajudou na ação.',
           'comando':'João foi o autor de homicídio e Paulo figurou como partícipe do crime.',
           'alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'Penal','assunto_origem':'Crimes'}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);entrada=p/'novas.jsonl';entrada.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in [q,{**q,'id':'texto_novo_b'}])+'\n')
            abrir=Path.open
            def protegido(path,*args,**kw):
                if path.name=='folha_verdade.csv':raise AssertionError('Rótulos na inferência')
                return abrir(path,*args,**kw)
            with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')), \
                 patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliação')), \
                 patch.object(m,'ajustar',side_effect=AssertionError('treino')),patch.object(m.a,'calibrar',side_effect=AssertionError('recalibração')), \
                 patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('fit supervisionado')),redirect_stdout(io.StringIO()):
                rr=executar(self.projeto,self.experimento,entrada,p/'saida')
            for k in ['tema_central_id','decisao','confianca','top5_ids','identificador_forte_cmd']:
                self.assertEqual(rr[0][k],rr[1][k])


if __name__=='__main__':unittest.main()
