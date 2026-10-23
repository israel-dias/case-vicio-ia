import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from classificar_ampliacao_v16 import executar

class TestAmpliacao(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]
    def test_dados_novos_sem_id_conhecido_sem_rotulos_e_sem_rede(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);arq=p/'entrada.jsonl'
            q={'enunciado_html':'A respeito da prescrição da pretensão punitiva, julgue a assertiva.','comando':'','alternativas':{'C':'Certo','E':'Errado'}}
            arq.write_text('\n'.join(json.dumps({**q,'id':i}) for i in ['id_novo_a','id_novo_b'])+'\n')
            with patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch('socket.create_connection',side_effect=AssertionError('rede')),contextlib.redirect_stdout(io.StringIO()):
                rr=executar(self.projeto,arq,p/'saida')
            self.assertEqual(len(rr),2)
            self.assertEqual((rr[0]['tema_central_id'],rr[0]['decisao'],rr[0]['confianca']),(rr[1]['tema_central_id'],rr[1]['decisao'],rr[1]['confianca']))
    def test_saida_existente_preservada(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaisesRegex(ValueError,'saída nova'):executar(self.projeto,p,p)
    def test_ampliacao_nao_contem_tabela_de_respostas_por_id(self):
        p=self.projeto/'experimentos/ampliacao_v15_v16_002/manifesto_ampliacao.json'
        obj=json.loads(p.read_text());self.assertIn('projeto_sha256',obj)
        self.assertNotIn('questoes',obj);self.assertNotIn('classificacoes',obj)
if __name__=='__main__':unittest.main()
