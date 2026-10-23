import unittest
from mescla_marcadores_v7.texto import rotear,foco,alternativas_tematicas


def temas():
    return {'1':{'titulo':'Disciplina','nivel':0,'parent_id':'','ativo':True},
            '2':{'titulo':'Revisão Criminal','nivel':1,'parent_id':'1','ativo':True},
            '3':{'titulo':'Habeas Corpus','nivel':1,'parent_id':'1','ativo':True}}


class TestTexto(unittest.TestCase):
    def q(self,en,alts=None,**kw):
        return {'id':'X','enunciado_html':en,'comando':'','alternativas':alts or {'A':'Revisão criminal','B':'Habeas corpus'},**kw}

    def test_considerando_foi_excluido_dos_marcadores(self):
        r=foco(self.q('Considerando a revisão criminal, assinale a correta.'),temas())
        self.assertFalse(r['presente']);self.assertEqual(r['referencias'],[])

    def test_considerando_nao_apaga_tema_informativo(self):
        q=self.q('Considerando a revisão criminal, assinale a correta.')
        novo,r=rotear(q,temas())
        self.assertEqual(r['peso_textual_enunciado'],1)
        self.assertIn('revisão criminal',novo['enunciado_html'])

    def test_generico_zera_enunciado_comando_e_origem(self):
        q=self.q('Considerando as afirmativas abaixo, é correto afirmar que:',
                 assunto_origem='Tema contaminante',disciplina_origem='Origem')
        novo,r=rotear(q,temas())
        self.assertEqual(r['peso_textual_enunciado'],0)
        for n in ['enunciado_html','comando','assunto_origem','disciplina_origem']:self.assertEqual(novo[n],'')
        self.assertEqual(novo['alternativas'],q['alternativas'])

    def test_lista_de_assuntos_sem_caso_usa_alternativas(self):
        _,r=rotear(self.q('A respeito de revisão criminal e habeas corpus, assinale a correta.'),temas())
        self.assertEqual(r['peso_textual_enunciado'],0)

    def test_certo_errado_nao_substitui_assertiva(self):
        q=self.q('A interceptação telefônica pode ser prorrogada.',{'C':'Certo','E':'Errado'})
        novo,r=rotear(q,temas())
        self.assertEqual(r['peso_textual_enunciado'],1)
        self.assertEqual(novo['enunciado_html'],q['enunciado_html'])

    def test_combinacoes_nao_substituem_assertivas(self):
        self.assertFalse(alternativas_tematicas(self.q('I. Conteúdo. II. Outro.',{'A':'Apenas I e II','B':'Somente II'})))

    def test_sem_conteudo_e_certo_errado_bloqueia_publicacao(self):
        _,r=rotear(self.q('Julgue o item.',{'C':'Certo','E':'Errado'}),temas())
        self.assertTrue(r['conteudo_insuficiente'])

    def test_retira_cabecalho_preserva_assertiva(self):
        novo,r=rotear(self.q('A respeito de revisão criminal e habeas corpus, julgue os itens subsequentes. A revisão criminal admite uma hipótese.',{'C':'Certo','E':'Errado'}),temas())
        self.assertTrue(r['cabecalho_removido'])
        self.assertEqual(novo['enunciado_html'],'A revisão criminal admite uma hipótese.')

    def test_como_sendo_preserva_conceito_anterior(self):
        r=foco(self.q('O autor apresenta a “sociedade punitiva” como sendo uma sociedade com certa organização.'),temas())
        self.assertIn('sociedade punitiva',r['texto_foco'])

    def test_cabecalho_com_tema_unico_preserva_contexto(self):
        en='A respeito da revisão criminal, julgue os itens subsequentes. O pedido pode ter determinada consequência.'
        novo,r=rotear(self.q(en,{'C':'Certo','E':'Errado'}),temas())
        self.assertEqual(novo['enunciado_html'],en)
        self.assertFalse(r['cabecalho_removido'])

    def test_cabecalho_coletivo_em_cada_item(self):
        en='Em cada item que se segue, julgue a assertiva a respeito de revisão criminal e habeas corpus. O pedido admite determinada providência.'
        novo,r=rotear(self.q(en,{'C':'Certo','E':'Errado'}),temas())
        self.assertEqual(novo['enunciado_html'],'O pedido admite determinada providência.')
        self.assertTrue(r['cabecalho_removido'])

    def test_pratica_anterior_preserva_negacao(self):
        r=foco(self.q('O agente adotou “modificar sistema sem autorização”. Essa prática configura um crime.'),temas())
        self.assertIn('sem autorização',r['texto_foco'])

    def test_conduta_abaixo_busca_contexto_posterior(self):
        r=foco(self.q('Administração pública. Analise a conduta abaixo, caracterizando-a. Um funcionário exige dinheiro de uma pessoa.'),temas())
        self.assertIn('funcionário exige dinheiro',r['texto_foco'])

    def test_predicado_incompleto_nao_override(self):
        r=foco(self.q('Em relação ao crime de furto, Carlos é'),temas())
        self.assertFalse(r['presente'])
        self.assertEqual(r['referencias'][0]['motivo'],'predicado_incompleto')

    def test_marcador_na_alternativa_nao_conta(self):
        self.assertFalse(foco(self.q('Assinale a correta.',{'A':'A respeito da revisão criminal.'}),temas())['presente'])

    def test_nao_apaga_caso_concreto_por_ausencia_de_titulo(self):
        _,r=rotear(self.q('Um servidor modificou o sistema sem autorização e causou um dano.'),temas())
        self.assertEqual(r['peso_textual_enunciado'],1)

    def test_id_e_origem_nao_definem_roteamento(self):
        q=self.q('Assinale a alternativa correta.')
        a,r1=rotear(q,temas());b,r2=rotear({**q,'id':'Y','assunto_origem':'Revisão criminal'},temas())
        self.assertEqual(r1,r2)
        self.assertEqual(a['enunciado_html'],b['enunciado_html'])

    def test_script_e_negacao_preservados_corretamente(self):
        r=foco(self.q('A respeito dos atos que não constituem crime, assinale a correta.<script>como sendo</script>'),temas())
        self.assertIn('não constituem crime',r['texto_foco'])
        self.assertEqual(len(r['referencias']),1)

    def test_homonimos_nao_tornam_enunciado_generico(self):
        ts=temas();ts['4']={'titulo':'Habeas Corpus','nivel':1,'parent_id':'1','ativo':True}
        q=self.q('A respeito de habeas corpus, assinale a correta.')
        novo,r=rotear(q,ts)
        self.assertEqual(r['peso_textual_enunciado'],1)
        self.assertTrue(foco(q,ts)['presente'])

    def test_pergunta_especifica_com_dois_temas_nao_e_lista(self):
        q=self.q('Assinale a alternativa que indica o efeito da revisão criminal sobre o habeas corpus anteriormente impetrado.')
        _,r=rotear(q,temas())
        self.assertEqual(r['peso_textual_enunciado'],1)

    def test_lei_especifica_nao_e_vazia(self):
        _,r=rotear(self.q('Nos termos da Lei nº 9.099/1995, assinale a correta.'),temas())
        self.assertEqual(r['peso_textual_enunciado'],1)

    def test_narrativa_com_dois_assuntos_nao_e_lista(self):
        _,r=rotear(self.q('A defesa impetrou habeas corpus depois da revisão criminal. Assinale a correta.'),temas())
        self.assertEqual(r['peso_textual_enunciado'],1)
