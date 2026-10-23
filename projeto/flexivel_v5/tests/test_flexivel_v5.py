import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from compatibilidade_v2 import features as f
from flexivel_v5 import runtime as rt
from melhorias_v3.representacao import NOMES


ROOT=Path(__file__).resolve().parents[2]


class TestFlexivelV5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta=ROOT/'artefatos/flexivel_v5'
        cls.runtime=rt.Runtime(cls.pasta)

    def item(self):
        return {'id':'NOVO_REGISTRO','enunciado_html':'Julgue a assertiva sobre o art. 20 do CP e erro de tipo.',
                'comando':'','alternativas':{'C':'Certo','E':'Errado'},
                'disciplina_origem':'Direito Penal','assunto_origem':''}

    def test_inferencia_sem_rede_sem_rotulos_sem_treinamento(self):
        abrir=Path.open
        def guard(path,*args,**kwargs):
            if Path(path).name=='folha_verdade.csv':raise AssertionError('Leitura de rótulos na inferência')
            return abrir(path,*args,**kwargs)
        with patch.object(Path,'open',guard),patch.object(f.LogisticRegression,'fit',side_effect=AssertionError('Treino')),\
             patch('socket.create_connection',side_effect=AssertionError('Rede')):
            runtime=rt.Runtime(self.pasta)
            row,trace=runtime.classificar(self.item())
        self.assertIn(row['decisao'],['publicar','revisar'])
        self.assertTrue(0<float(row['confianca'])<1)
        self.assertFalse(set(trace['atributos_em_uso']) & set(rt.RETIRADOS))

    def test_mudar_tres_colunas_retiradas_nao_muda_predicao(self):
        q=self.item();p=self.runtime.catalogo.transformar({'registro':q})['registro']
        p2=copy.deepcopy(p)
        for n in rt.RETIRADOS:p2['features_v3'][:,NOMES.index(n)]+=100
        with patch.object(self.runtime.catalogo,'transformar',return_value={'registro':p}):
            row1,_=self.runtime.classificar(q)
        with patch.object(self.runtime.catalogo,'transformar',return_value={'registro':p2}):
            row2,_=self.runtime.classificar(q)
        self.assertEqual(row1,row2)

    def test_alerta_normativo_e_origem_nao_impoem_veto_adicional(self):
        q=self.item();p=self.runtime.catalogo.transformar({'registro':q})['registro']
        p['features_v3'][:,NOMES.index('citacao_sem_correspondencia')]=1
        p['features_v3'][:,NOMES.index('origem_reconhecida')]=1
        p['features_v3'][:,NOMES.index('origem_compativel')]=0
        with patch.object(self.runtime.catalogo,'transformar',return_value={'registro':p}),\
             patch.object(f,'predizer_linear',return_value=f.np.array([.99])):
            row,trace=self.runtime.classificar(q)
        self.assertEqual(row['decisao'],'publicar')
        self.assertGreaterEqual(len(trace['notas_informativas']),2)

    def test_id_nao_altera_tema_decisao_ou_confianca(self):
        q=self.item();r1,_=self.runtime.classificar(q)
        q['id']='QUALQUER_OUTRO';r2,_=self.runtime.classificar(q)
        for n in ['decisao','tema_central_id','extras_ids','confianca','motivo']:self.assertEqual(r1[n],r2[n])

    def test_texto_de_id_existente_e_reprocessado(self):
        q=self.item();q['id']='Q0001';r1,t1=self.runtime.classificar(q)
        q['enunciado_html']='A prova testemunhal e o depoimento de testemunhas no Código de Processo Penal.'
        r2,t2=self.runtime.classificar(q)
        self.assertNotEqual(t1['sha256_texto'],t2['sha256_texto'])
        self.assertNotEqual(t1['atributos_em_uso'],t2['atributos_em_uso'])

    def test_tema_inicial_da_busca_e_preservado(self):
        q=self.item();p=self.runtime.catalogo.transformar({'registro':q})['registro']
        esperado=self.runtime.catalogo.familias[int(f.ordenar(p['scores'])[0])]
        row,_=self.runtime.classificar(q)
        self.assertEqual(row['tema_central_id'],esperado)
        self.assertEqual(row['extras_ids'],'')

    def test_modelo_copiado_e_calibracao_sao_os_previamente_avaliados(self):
        antigo=json.loads((ROOT/'experimentos/auditoria_confianca_v4_002/modelos_finais_diagnostico.json').read_text())
        m=self.runtime.registro
        self.assertEqual(m['compatibilidade'],antigo['modelos']['sem_formato'])
        self.assertEqual(m['calibrador'],antigo['calibradores']['sem_formato'])
        self.assertEqual(m['politica'],antigo['politicas']['sem_formato'])
        self.assertNotRegex((self.pasta/'modelo.json').read_text(),r'Q\d{4}')

    def test_artefato_adulterado_e_rejeitado(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta=Path(tmp)/'modelo';shutil.copytree(self.pasta,pasta)
            p=pasta/'referencias_normativas_v1.json';p.write_text(p.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'alterado'):rt.Runtime(pasta)

    def test_manifesto_rejeita_caminho_externo(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta=Path(tmp)/'modelo';shutil.copytree(self.pasta,pasta)
            p=pasta/'manifesto_modelo.json';m=json.loads(p.read_text())
            m['arquivos_sha256']['../fora.json']='qualquer'
            p.write_text(json.dumps(m))
            with self.assertRaises(ValueError):rt.Runtime(pasta)

    def test_codigo_divergente_e_rejeitado(self):
        with patch.object(rt,'codigos',return_value={}):
            with self.assertRaisesRegex(ValueError,'Código diferente'):rt.Runtime(self.pasta)

    def test_saida_se_reproduz_e_nao_sobrescreve_historico(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);entrada=p/'questoes.jsonl';entrada.write_text(json.dumps(self.item())+'\n')
            rt.executar(self.pasta,entrada,p/'a');rt.executar(self.pasta,entrada,p/'b')
            self.assertEqual((p/'a/publicacao.csv').read_bytes(),(p/'b/publicacao.csv').read_bytes())
            with self.assertRaises(ValueError):rt.executar(self.pasta,entrada,p/'a')


if __name__=='__main__':unittest.main()
