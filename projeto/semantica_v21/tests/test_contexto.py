import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import carregar_catalogo
from semantica_v22 import modelo as m


class TestGuardaContextual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cat,_=carregar_catalogo(ROOT)

    def perfil(self,forte):
        cat=self.cat;n=len(cat.familias);a=cat.familias.index('5199');b=cat.familias.index('5185');c=cat.familias.index('5498')
        x=f.np.zeros((n,32));x[a,0]=.2;x[b,0]=.9;x[c,0]=1.;rank=f.np.zeros(n);rank[a]=1
        p={'x':x,'ranking':rank,'candidatos':[a,b,c],'identificacao':{'forte':forte},'rota':{'sem_evidencia':False},'sinal_textual':f.np.zeros(n),'homonimos':{t:[] for t in cat.familias}}
        mod={'dimensao':32,'media':[0]*32,'escala':[1]*32,'coeficientes':[1]+[0]*31,'intercepto':0}
        return p,mod

    def test_comando_forte_preservado_mesmo_com_outro_escore_maior(self):
        p,mod=self.perfil(True);r=m.sinais({'sem_id_semantico':p},mod,self.cat,'reranking_com_contexto')[0]
        self.assertEqual(r['tema_central_id'],'5199');self.assertEqual(r['rota'],'preservar_comando_explicito')

    def test_guarda_limita_reranking_ao_ramo_inferido(self):
        p,mod=self.perfil(False);r=m.sinais({'q':p},mod,self.cat,'reranking_com_contexto')[0]
        self.assertEqual(r['tema_central_id'],'5185');self.assertEqual(r['rota'],'reordenar_no_ramo_recuperado')

    def test_controle_livre_demonstra_efeito_da_guarda(self):
        p,mod=self.perfil(False);r=m.sinais({'q':p},mod,self.cat,'reranking_livre')[0]
        self.assertEqual(r['tema_central_id'],'5498')


if __name__=='__main__':unittest.main()
