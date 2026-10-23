import contextlib,io,json,re,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from compatibilidade_v2 import features as f
from classificar_roteamento_v15 import executar

class TestRuntime(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]
    def test_ids_e_origens_nao_mudam_classificacao_nova_sem_rede_ou_rotulos(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);arq=p/'novas.jsonl';qs=[]
            for i,orig in [('Q0066','Penal'),('id_novo','Criminologia')]:
                qs.append({'id':i,'enunciado_html':'A respeito da prescrição, julgue.','comando':'Explique a prescrição.','alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':orig,'assunto_origem':orig})
            arq.write_text('\n'.join(json.dumps(q) for q in qs)+'\n')
            with patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch('socket.create_connection',side_effect=AssertionError('rede')),contextlib.redirect_stdout(io.StringIO()):
                rr=executar(self.projeto,self.projeto/'experimentos/roteamento_v15_002',arq,p/'saida','foco_contextual','70','substituir')
            self.assertEqual(rr[0]['tema_central_id'],rr[1]['tema_central_id']);self.assertEqual(rr[0]['confianca'],rr[1]['confianca'])
    def test_saida_existente_preservada(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaisesRegex(ValueError,'saída nova'):executar(self.projeto,p,p,p,'foco_contextual','70','substituir')
    def test_modelos_nao_contem_questoes_ou_rotulos_por_id(self):
        s=(self.projeto/'experimentos/roteamento_v15_002/modelos_finais.json').read_text()
        self.assertIsNone(re.search(r'Q\d{4}',s))
    def test_artefato_adulterado_rejeitado_antes_de_abrir_questoes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);e=p/'experimento';e.mkdir()
            (e/'manifesto_inferencia.json').write_bytes((self.projeto/'experimentos/roteamento_v15_002/manifesto_inferencia.json').read_bytes())
            (e/'modelos_finais.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'artefato alterado'):executar(self.projeto,e,p/'inexistente',p/'saida','foco_contextual','70','substituir')

if __name__=='__main__':unittest.main()
