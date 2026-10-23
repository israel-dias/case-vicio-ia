import unittest,json,tempfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from diagnosticar_559_v15 import validar_alvo,motivo_foco,decompor,ids_excluidos

class TestDiagnostico559(unittest.TestCase):
    def excluidos(self):return {f'Q{i:04d}' for i in range(1,101)}
    def test_alvo_tem_559_sem_100_e_separa_os_300_recentes(self):
        excl=self.excluidos();qs={f'Q{i:04d}':{} for i in range(1,660) if f'Q{i:04d}' not in excl}
        self.assertEqual(validar_alvo(qs,excl),{'total':559,'antigas_259':259,'recentes_300':300,'rotuladas_incluidas':0})
    def test_contagem_559_nao_esconde_inclusao_de_id_rotulado(self):
        qs={f'Q{i:04d}':{} for i in range(101,660)};qs.pop('Q0101');qs['Q0001']={}
        with self.assertRaisesRegex(ValueError,'fora dos 100'):validar_alvo(qs,self.excluidos())
    def test_lista_de_referencia_incompleta_e_rejeitada(self):
        with self.assertRaisesRegex(ValueError,'100 IDs'):validar_alvo({},set())
    def test_folds_de_tamanhos_diferentes_sao_preservados(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'folds').mkdir();ids=sorted(self.excluidos());inicio=0
            for i,n in enumerate([18,20,20,20,22],1):
                (p/f'folds/fold_{i}.json').write_text(json.dumps({'avaliacao_ids':ids[inicio:inicio+n]}));inicio+=n
            self.assertEqual(ids_excluidos(p),self.excluidos())
    def test_homonimo_e_confianca_sao_causas_separadas(self):
        r={'decisao':'revisar','tema_central_id':'a','confianca':.85,'homonimo_nao_resolvido':True}
        p={'x':np.full((1,27),.1),'rota':{'sem_evidencia':False}};cat=SimpleNamespace(familias=['a'])
        self.assertEqual(motivo_foco(r,p,cat),'homonimo_com_escopo_nao_resolvido')
        r.update(homonimo_nao_resolvido=False,confianca=.69)
        self.assertEqual(motivo_foco(r,p,cat),'confianca_abaixo_de_70')
    def test_piso_sem_sinal_nao_vira_ausencia_da_taxonomia(self):
        r={'decisao':'revisar','tema_central_id':'a','confianca':.9,'homonimo_nao_resolvido':False}
        p={'x':np.zeros((1,27)),'rota':{'sem_evidencia':False}}
        self.assertEqual(motivo_foco(r,p,SimpleNamespace(familias=['a'])),'apoio_textual_abaixo_do_piso')
    def test_decomposicao_reconstroi_logit_sem_penalidade_percentual(self):
        mod={'media':[1,2],'escala':[2,4],'coeficientes':[3,-2],'intercepto':.5}
        d=decompor(np.array([3,6]),mod,['a','b'])
        self.assertAlmostEqual(d['sinal_reconstruido'],1.5)
        self.assertEqual([x['contribuicao_logit'] for x in d['contribuicoes']],[3.,-2.])
        self.assertIn('não pontos percentuais',d['unidade'])
if __name__=='__main__':unittest.main()
