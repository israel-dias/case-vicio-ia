import io,json,socket,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from classificar_expressoes_v19 import executar


class TestRuntimeV19(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]
    experimento=projeto/'experimentos/expressoes_v19_001'

    def test_comando_embutido_em_textos_novos_sem_leitura_de_rotulos(self):
        q={'id':'texto_novo','enunciado_html':'João foi acusado de um crime. Sobre o concurso de pessoas, assinale a opção correta.',
           'comando':'','alternativas':{'A':'Há coautoria.','B':'Há participação.'},'disciplina_origem':'Penal','assunto_origem':''}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);entrada=p/'entrada.jsonl';entrada.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in [q,{**q,'id':'id_diferente'}])+'\n')
            abrir=Path.open
            def protegido(path,*a,**kw):
                if path.name=='folha_verdade.csv':raise AssertionError('rótulos')
                return abrir(path,*a,**kw)
            with patch.object(Path,'open',protegido),patch.object(socket,'socket',side_effect=AssertionError('rede')), \
                 patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch.object(f,'aceito',side_effect=AssertionError('avaliador')), \
                 patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('fit')),redirect_stdout(io.StringIO()):
                rr=executar(self.projeto,self.experimento,entrada,p/'saida','passagem_cobrada')
            for k in ['tema_central_id','confianca','decisao','identificador_forte_cmd']:
                self.assertEqual(rr[0][k],rr[1][k])
            self.assertTrue(rr[0]['identificador_forte_cmd'])

    def test_saida_existente_nao_e_sobrescrita(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'saída nova'):executar(self.projeto,self.experimento,'ausente',tmp)


if __name__=='__main__':unittest.main()
