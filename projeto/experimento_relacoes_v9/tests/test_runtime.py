import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from classificar_relacoes_v9 import executar
from compatibilidade_v2 import features as f


class TestRuntime(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]

    def test_questao_nova_e_texto_alterado_nao_usam_resposta_por_id(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);q=p/'questoes.jsonl'
            q.write_text('\n'.join(json.dumps({'id':i,'enunciado_html':'A respeito da prescrição, julgue.',
                'comando':'','alternativas':{'C':'Certo','E':'Errado'},
                'disciplina_origem':origem,'assunto_origem':''}) for i,origem in [('Q0308','Criminologia'),('nova_questao','Penal')])+'\n')
            with patch.object(f,'carregar',side_effect=AssertionError('rótulos')),patch('socket.create_connection',side_effect=AssertionError('rede')),contextlib.redirect_stdout(io.StringIO()):
                rows=executar(self.projeto,q,p/'saida','titulos_diretos',self.projeto/'experimento_relacoes_v9/artefato_regra.json')
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r['tema_central_id']=='5185' for r in rows))
            self.assertEqual(rows[0]['confianca'],rows[1]['confianca'])

    def test_codigo_divergente_rejeitado_antes_de_gerar_saida(self):
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta);m=json.loads((self.projeto/'experimento_relacoes_v9/artefato_regra.json').read_text())
            m['codigo_sha256']['experimento_relacoes_v9/regras.py']='0'*64
            a=p/'adulterado.json';a.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'Código v9 alterado'):
                executar(self.projeto,p/'ausente.jsonl',p/'saida','titulos_diretos',a)
            self.assertFalse((p/'saida').exists())


if __name__=='__main__':unittest.main()
