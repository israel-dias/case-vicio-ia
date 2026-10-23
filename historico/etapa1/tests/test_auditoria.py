import copy,csv,json,shutil,tempfile,unittest
from pathlib import Path
from vicio_ia.auditoria import aplicar_auditoria,validar_registros
from vicio_ia.temas import validar_temas
from vicio_ia.arquivos import ler_csv
ROOT=Path(__file__).resolve().parents[1]

class TestAuditoria(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rs=json.loads((ROOT/'auditoria_v4/reexame_359.json').read_text())['registros']
  with (ROOT/'historico/v3/publicacao.csv').open(encoding='utf-8') as h:
   cls.antes=list(csv.DictReader(h))
  cls.temas=validar_temas(ler_csv(ROOT/'dados/originais/temas.csv'))
 def test_todos_os_ids_tem_reexame_inclusive_fora(self):
  novos=validar_registros(self.rs,self.antes,self.temas)
  self.assertEqual(len(novos),359)
  self.assertEqual({r['id'] for r in novos},{f'Q{i:04}' for i in range(1,360)})
  self.assertEqual(next(r for r in novos if r['id']=='Q0142')['decisao'],'fora')
 def test_gabarito_oficial_nao_elimina_pendencia_de_taxonomia(self):
  novos={r['id']:r for r in validar_registros(self.rs,self.antes,self.temas)}
  for i in ('Q0355',):
   r=next(r for r in self.rs if r['id']==i)
   self.assertEqual(r['estado_resposta'],'gabarito_oficial_definitivo')
   self.assertEqual(novos[i]['decisao'],'revisar')
 def test_antes_incompativel_e_rejeitado(self):
  rs=copy.deepcopy(self.rs);rs[0]['antes']['decisao']='fora'
  with self.assertRaisesRegex(ValueError,'não corresponde'):validar_registros(rs,self.antes,self.temas)
 def test_confianca_booleana_nao_e_probabilidade(self):
  rs=copy.deepcopy(self.rs);rs[0]['depois']['confianca']=True
  with self.assertRaisesRegex(ValueError,'Campos CSV'):validar_registros(rs,self.antes,self.temas)
 def test_extra_inativo_nao_pode_entrar_na_entrega(self):
  rs=copy.deepcopy(self.rs);rs[0]['depois']['extras_ids']='5078'
  with self.assertRaisesRegex(ValueError,'inativo'):validar_registros(rs,self.antes,self.temas)
 def test_filho_como_extra_exige_justificativa_independente(self):
  rs=copy.deepcopy(self.rs);r=next(x for x in rs if x['id']=='Q0031');r['depois']['extras_ids']='4388'
  with self.assertRaisesRegex(ValueError,'independente'):validar_registros(rs,self.antes,self.temas)
 def test_extras_dos_tipos_correlacionados_podem_ser_filhos_do_central(self):
  novos={r['id']:r for r in validar_registros(self.rs,self.antes,self.temas)}
  self.assertEqual(novos['Q0248']['tema_central_id'],'5087')
  self.assertIn('5092',novos['Q0248']['extras_ids'].split(';'))
 def test_resposta_nao_pode_divergir_da_evidencia_alegada(self):
  rs=copy.deepcopy(self.rs);r=next(x for x in rs if x['id']=='Q0171');r['resposta_proposta']='A'
  with self.assertRaisesRegex(ValueError,'Gabarito oficial'):validar_registros(rs,self.antes,self.temas)
 def test_adulteracao_do_protocolo_e_detectada(self):
  m=json.loads((ROOT/'auditoria_v4/manifesto_auditoria.json').read_text())
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   for f in ['auditoria_v4/manifesto_auditoria.json',*m['entradas_sha256']]:
    d=p/f;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f,d)
   with (p/'auditoria_v4/PROTOCOLO_FINAL.md').open('a') as h:h.write('\n')
   with self.assertRaisesRegex(ValueError,'Entrada da auditoria alterada'):
    aplicar_auditoria(p,self.antes,[],{}, {},self.temas)

if __name__=='__main__':unittest.main()
