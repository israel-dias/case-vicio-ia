import copy
import json
import math
from pathlib import Path
import unittest

import numpy as np

from auditoria_confianca_v4 import experimento as e
from compatibilidade_v2 import features as f
from melhorias_v3 import aprendizado as a


PROJETO = Path(__file__).resolve().parents[2]


class TestAuditoriaConfianca(unittest.TestCase):
    def test_decomposicao_reconstroi_probabilidade_calibrada(self):
        modelo = {'dimensao':2,'media':[.2,.4],'escala':[.3,.7],
                  'coeficientes':[1.2,-.8],'intercepto':-.3}
        calib = {'dimensao':1,'media':[.5],'escala':[1.3],
                 'coeficientes':[.9],'intercepto':.2}
        for x in [[0.,0.],[1.,2.],[.2,.4]]:
            esperado = a.confiancas([{'sinal':float(a.escore_linear([x],modelo)[0])}],calib)[0]
            calculado = e.decompor(x,modelo,calib)
            self.assertAlmostEqual(calculado['confianca_reconstruida'],esperado,places=13)

    def test_direcao_da_contribuicao_depende_do_valor_centralizado(self):
        modelo={'dimensao':1,'media':[.5],'escala':[1.],
                'coeficientes':[2.],'intercepto':0.}
        calib={'dimensao':1,'media':[0.],'escala':[1.],
               'coeficientes':[1.],'intercepto':0.}
        self.assertLess(e.decompor([0.],modelo,calib)['contribuicoes_logit'][0],0)
        self.assertGreater(e.decompor([1.],modelo,calib)['contribuicoes_logit'][0],0)

    def test_remover_grupo_preserva_scores_e_nao_muda_original(self):
        x=np.arange(2*len(e.NOMES),dtype=float).reshape(2,-1)
        perfis={'registro':{'features_v3':x.copy(),'scores':np.array([.2,.5]),'hash':'abc'}}
        variante=next(v for v in e.VARIANTES if v['nome']=='sem_metadados')
        resultado=e.projetar(perfis,variante)
        self.assertEqual(resultado['registro']['features_v3'].shape,(2,len(e.NOMES)-3))
        np.testing.assert_array_equal(perfis['registro']['features_v3'],x)
        np.testing.assert_array_equal(resultado['registro']['scores'],perfis['registro']['scores'])
        resultado['registro']['features_v3'][0,0]=-200
        self.assertEqual(perfis['registro']['features_v3'][0,0],x[0,0])

    def test_sinais_preservam_candidato_mesmo_que_peso_prefira_outro(self):
        x=np.zeros((2,len(e.NOMES)));x[0,0]=100
        perfis={'registro':{'features_v3':x,'scores':np.array([.1,.5]),
                            'scores_novos':np.array([.9,.2])}}
        v=e.VARIANTES[0]
        mod={'dimensao':len(e.NOMES),'media':[0.]*len(e.NOMES),'escala':[1.]*len(e.NOMES),
             'coeficientes':[1.]+[0.]*(len(e.NOMES)-1),'intercepto':0.}
        r=e.sinais(perfis,mod,['tema_1','tema_2'],v)[0]
        self.assertEqual(r['tema_central_id'],'tema_2')
        self.assertEqual(r['sinal'],0.)

    def test_id_nao_altera_probabilidade(self):
        p={'features_v3':np.zeros((2,len(e.NOMES))), 'scores':np.array([.1,.5]),
           'scores_novos':np.array([.2,.4])}
        mod={'dimensao':len(e.NOMES),'constante':.7}
        r1=e.sinais({'Q0001':p},mod,['t1','t2'],e.VARIANTES[0])[0]
        r2=e.sinais({'Q9999':p},mod,['t1','t2'],e.VARIANTES[0])[0]
        r1.pop('id');r2.pop('id');self.assertEqual(r1,r2)

    def test_treino_rejeita_rotulo_externo(self):
        with self.assertRaisesRegex(ValueError,'outro grupo'):
            e.ajustar({'treino':{}},{'teste':{}},None,e.VARIANTES[0])

    def test_selecao_usa_suporte_interno_e_favorece_controle_no_empate(self):
        ps={v['nome']:{'suporte_interno':10} for v in e.VARIANTES}
        self.assertEqual(e.escolher_internamente(ps),'controle_v3')
        ps['sem_formato']['suporte_interno']=11
        self.assertEqual(e.escolher_internamente(ps),'sem_formato')

    def test_variantes_rejeitam_coluna_inventada_e_duplicada(self):
        for coluna in ['id','confianca_esperada']:
            variantes=copy.deepcopy(e.VARIANTES);variantes[1]['atributos'].append(coluna)
            with self.assertRaises(ValueError):e.validar_variantes(variantes)
        variantes=copy.deepcopy(e.VARIANTES);variantes[1]['atributos'].append(e.NOMES[0])
        with self.assertRaises(ValueError):e.validar_variantes(variantes)

    def test_otimizacao_preserva_modelo_e_probabilidades_originais(self):
        rng=np.random.default_rng(2026);x=rng.normal(size=(35,6));y=[0]*29+[1]*6
        pesos=np.linspace(.5,2.,35)
        for balancear in [True,False]:
            antigo=f.ajustar_linear(x,y,pesos,balancear)
            novo=e.ajustar_linear_eficiente(x,y,pesos,balancear)
            np.testing.assert_allclose(f.predizer_linear(x,antigo),f.predizer_linear(x,novo),rtol=0,atol=1e-13)

    def test_contribuicoes_casos_reais_reproduzem_registro(self):
        mod=json.loads((PROJETO/'artefatos/melhorias_v3/modelo.json').read_text())
        ras=map(json.loads,(PROJETO/'entrega_experimental_v3/rastreabilidade.jsonl').read_text().splitlines())
        ids={'Q0568','Q0496','Q0523','Q0492','Q0458'};encontrados=set()
        for r in ras:
            if r['id'] in ids:
                resultado=e.decompor([r['atributos'][n] for n in e.NOMES],mod['modelos']['todos'],mod['calibradores']['referencias_fixa'])
                self.assertAlmostEqual(resultado['confianca_reconstruida'],r['confianca'],places=12)
                encontrados.add(r['id'])
        self.assertEqual(encontrados,ids)


if __name__=='__main__':unittest.main()
