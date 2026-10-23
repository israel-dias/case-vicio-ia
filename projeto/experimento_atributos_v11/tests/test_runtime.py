import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from compatibilidade_v2 import features as f
from classificar_atributos_v11 import executar


class TestRuntime(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]

    def test_questoes_novas_e_id_antigo_recalculado_sem_rotulos_rede(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);q=p/'questoes.jsonl'
            qs=[{'id':i,'enunciado_html':'A respeito da prescrição, julgue.','comando':'',
                 'alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'','assunto_origem':''} for i in ['Q0066','nova_questao']]
            q.write_text('\n'.join(json.dumps(x) for x in qs)+'\n')
            with patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch('socket.create_connection',side_effect=AssertionError('rede')),contextlib.redirect_stdout(io.StringIO()):
                rr=executar(self.projeto,self.projeto/'experimentos/atributos_v11_001',q,p/'saida','sem_apoio_duplo')
            self.assertTrue(all(r['tema_central_id']=='5185' for r in rr))
            self.assertEqual(rr[0]['confianca'],rr[1]['confianca'])

    def test_modelo_adulterado_e_rejeitado_antes_da_saida(self):
        import shutil
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);e=p/'artefato';e.mkdir()
            fonte=self.projeto/'experimentos/atributos_v11_001'
            for n in ['manifesto_inferencia.json','estatistica_identificador.json']:shutil.copy2(fonte/n,e/n)
            (e/'modelos_finais.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Artefato alterado'):
                executar(self.projeto,e,p/'ausente.jsonl',p/'saida','sem_apoio_duplo')
            self.assertFalse((p/'saida').exists())

    def test_pasta_existente_nao_e_sobrescrita(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);s=p/'saida';s.mkdir();(s/'manual.txt').write_text('preservar')
            with self.assertRaisesRegex(ValueError,'saída nova'):
                executar(self.projeto,self.projeto/'experimentos/atributos_v11_001',p/'ausente.jsonl',s,'sem_apoio_duplo')
            self.assertEqual((s/'manual.txt').read_text(),'preservar')


if __name__=='__main__':unittest.main()
