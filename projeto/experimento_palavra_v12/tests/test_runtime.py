import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from compatibilidade_v2 import features as f
from classificar_palavra_v12 import executar,verificar_hashes
from experimento_palavra_v12.modelo import VARIANTES

class TestRuntime(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]

    def test_novos_ids_e_texto_alterado_nao_consultam_rotulos_ou_rede(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);q=p/'entrada.jsonl'
            rows=[{'id':i,'enunciado_html':'A respeito da prescrição, julgue.','comando':'',
                'alternativas':{'C':'Certo','E':'Errado'},'disciplina_origem':'','assunto_origem':''} for i in ['Q0066','id_novo']]
            q.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            with patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch('socket.create_connection',side_effect=AssertionError('rede')),contextlib.redirect_stdout(io.StringIO()):
                for v in VARIANTES:
                    rr=executar(self.projeto,self.projeto/'experimentos/palavra_v12_001',q,p/v,v)
                    self.assertTrue(all(r['tema_central_id']=='5185' for r in rr))
                    self.assertEqual(rr[0]['confianca'],rr[1]['confianca'])

    def test_artefato_adulterado_rejeitado_antes_de_abrir_questoes(self):
        import shutil
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);e=p/'modelo';e.mkdir()
            shutil.copy2(self.projeto/'experimentos/palavra_v12_001/manifesto_inferencia.json',e/'manifesto_inferencia.json')
            (e/'modelos_finais.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'artefato alterado'):
                executar(self.projeto,e,p/'nao_existe',p/'saida','palavra_relativa')
            self.assertFalse((p/'saida').exists())

    def test_manifesto_nao_permite_sair_do_projeto(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ValueError):verificar_hashes(Path(pasta).resolve(),{'../outro':'x'})

    def test_saida_existente_preservada(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);s=p/'saida';s.mkdir();(s/'nota.txt').write_text('original')
            with self.assertRaisesRegex(ValueError,'saída nova'):
                executar(self.projeto,p/'ausente',p/'ausente',s,'palavra_relativa')
            self.assertEqual((s/'nota.txt').read_text(),'original')

    def test_artefato_nao_contem_tabela_de_respostas_por_id(self):
        import re
        texto=(self.projeto/'experimentos/palavra_v12_001/modelos_finais.json').read_text()
        self.assertIsNone(re.search(r'Q\d{4}',texto))
        modelo=json.loads(texto)
        self.assertEqual(set(modelo['variantes']),set(VARIANTES))

if __name__=='__main__':unittest.main()
