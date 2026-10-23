import json,re,tempfile,unittest
from pathlib import Path
from classificar_multivista_v16 import executar

class TestRuntimeV16(unittest.TestCase):
    projeto=Path(__file__).resolve().parents[2]
    def test_modelos_nao_contem_respostas_por_id(self):
        s=(self.projeto/'experimentos/multivista_v16_001/modelos_finais.json').read_text()
        self.assertIsNone(re.search(r'Q\d{4}',s))
    def test_artefato_alterado_e_rejeitado_antes_de_abrir_entrada(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);e=p/'modelo';e.mkdir()
            (e/'manifesto_inferencia.json').write_bytes((self.projeto/'experimentos/multivista_v16_001/manifesto_inferencia.json').read_bytes())
            (e/'modelos_finais.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'artefato alterado'):
                executar(self.projeto,e,p/'nao_existe',p/'saida','condicional_v15','70','preservar_v11')
    def test_saida_existente_nao_e_sobrescrita(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'saída nova'):
                executar(self.projeto,tmp,tmp,tmp,'condicional_v15','70','preservar_v11')
if __name__=='__main__':unittest.main()
