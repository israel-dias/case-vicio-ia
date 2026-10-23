"""Roteamento de campos e foco referencial, sem rótulos ou exceções por ID."""
import re
from compatibilidade_v2 import features as f
from melhorias_v3.representacao import sem_acento, lexico


# 'considerando' é intencionalmente ausente. A palavra não é apagada dos dados.
MARCADOR = re.compile(
    r'\b(?:no que (?:se refere|diz respeito|concerne)\s+(?:a|ao|aos|as)|'
    r'a respeito\s+(?:de|do|da|dos|das)|(?:em|com) relacao\s+(?:a|ao|aos|as)|'
    r'no tocante\s+(?:a|ao|aos|as)|referentes?\s+(?:a|ao|aos|as)|como sendo|'
    r'(?:a|essa|esta|dessa|desta)\s+(?:pratica|conduta))\b')
INSTRUCAO = re.compile(r',?\s*\b(?:julgue|assinale|analise|marque|selecione)\b')
FIM = re.compile(r'[;:!?]|\.(?=\s+[A-ZÀ-Ú]|\s*$)')
RETOMADA = re.compile(r'(?:a|essa|esta|dessa|desta)\s+(?:pratica|conduta)')
CABECALHO = re.compile(
    r'^.{0,500}?\b(?:julgue|analise)\s+(?:(?:os|as)\s+)?'
    r'(?:itens|assertivas|afirmativas|proposicoes)\s+'
    r'(?:(?:a seguir|abaixo|seguintes|subsequentes|que se seguem))'
    r'(?:\s*,[^.]{0,140})?\s*[.:]\s*')
GENERICOS = set('''a o as os um uma uns umas de da do das dos em na no nas nos ao aos
e ou que se sua seu suas seus por para com como sendo refere referente refere-se
respeito relacao tocante concerne quanto considerando considere considerando-se
afirmativa afirmativas afirmacao afirmacoes assertiva assertivas item itens
proposicao proposicoes opcao opcoes alternativa alternativas frase frases
assinale julgue analise marque selecione responda complete indique diga abaixo
seguir seguinte seguintes subsequente subsequentes apresentado apresentados
apresentada apresentadas correto correta corretos corretas incorreto incorreta
incorretos incorretas verdadeiro verdadeira verdadeiros verdadeiras falso falsa
falsos falsas afirmar afirma dizer diz pode podem deve devem e eh sao esta estao
ser sera serao tem temos qual quais delas deles essas esses essa esse esta este
estes estas trata trate conforme acordo ponto vista legal termos disposicoes
estabelecido acerca sobre questao questoes contexto topico topicos tema temas
materia materias disciplina disciplinas direito penal processual processo
legislacao geral brasileira brasileiro brasil doutrina doutrinario doutrinaria
jurisprudencia entendimento sumulado tribunais superiores tribunal superior
justica supremo federal stf stj codigo cp cpp lei numero n nos termos correto
alternativa sentenca sentencas'''.split())
GENERICOS.update({'i','ii','iii','iv','v','vi'})


def limpar(t):
    return re.sub(r'\s+', ' ', f.visivel(t)).strip()


def conteudo_especifico(t):
    return [w for w in f.normalizar(t).split() if w not in GENERICOS and not w.isdigit()]


def alternativas_tematicas(q):
    alts=[f.normalizar(f.visivel(t)) for t in q.get('alternativas',{}).values()]
    if not alts or set(alts)<= {'certo','errado','verdadeiro','falso','sim','nao'}:
        return False
    # A/B = 'apenas I e II', por exemplo, não substitui as assertivas.
    residuo=[]
    for t in alts:
        residuo.extend(w for w in t.split() if w not in GENERICOS | {'apenas','somente','todas','todos','nenhuma','nenhum','exclusivamente','so'} and not w.isdigit())
    return bool(residuo)


def familias_literais(t, temas):
    text=' '+lexico(t,{})+' '
    encontrados=set()
    for tid,tema in temas.items():
        if not f.elegivel(tid,temas):continue
        titulo=lexico(tema['titulo'],{})
        partes=[titulo]
        if ':' in tema['titulo']:partes.append(lexico(tema['titulo'].split(':')[-1],{}))
        for parte in partes:
            palavras=conteudo_especifico(parte)
            if len(parte)>=8 and palavras and ' '+parte+' ' in text:
                familia=tema['parent_id'] if tema['nivel']==2 else tid
                encontrados.add(familia)
    return sorted(encontrados)


def assuntos_distintos(familias,temas):
    # Só para reconhecer uma LISTA no texto. Não torna os IDs equivalentes
    # na classificação ou na régua da empresa.
    return {lexico(temas[t]['titulo'],{}) for t in familias}


def rotear(q, temas):
    en,cmd=limpar(q.get('enunciado_html','')),limpar(q.get('comando',''))
    original=en
    h=CABECALHO.match(sem_acento(en))
    cabecalho=''
    fim_intro=h.end() if h else 0
    if not fim_intro and re.match(r'^em cada item que se segue\b',sem_acento(en)):
        sentenca=FIM.search(en)
        if sentenca:fim_intro=sentenca.end()
    if fim_intro and en[fim_intro:].strip():
        intro=en[:fim_intro]
        # Uma introdução com UM tema específico pode fornecer contexto
        # indispensável à assertiva. Retirá-la também seria uma perda de sinal.
        prefixo=re.split(r'\b(?:julgue|analise)\b',sem_acento(intro),maxsplit=1)[0]
        ampla=(len(assuntos_distintos(familias_literais(intro,temas),temas))>=2 or not conteudo_especifico(prefixo))
        if ampla:
            cabecalho=intro
            en=en[fim_intro:].strip()
        # O comando pode ser uma cópia do cabeçalho removido.
            if f.normalizar(cmd) in f.normalizar(cabecalho):cmd=''
    familias=familias_literais(en,temas)
    instrucao=bool(re.search(r'\b(?:assinale|julgue|marque|afirmar|afirmativas|assertivas|opcao|alternativa)\b',sem_acento(en)))
    # Reconhece uma enumeração de assuntos como título da pergunta, não uma
    # narrativa ou assertiva com vários assuntos. Sem limiar de confiança.
    prefixo_topical=bool(re.match(r'^(?:assinale\s+(?:a\s+)?(?:opcao|alternativa)\s+(?:correta|incorreta)\s+)?'
         r'(?:a respeito|sobre|acerca|(?:em|com) relacao|no tocante|no que (?:se refere|diz respeito|concerne)|quanto)\b',sem_acento(en)))
    norma_especifica=bool(re.search(r'\blei\s*(?:n[.oº°\s]*)?\d',sem_acento(' '.join([en,cmd]))))
    lista_de_assuntos=(instrucao and prefixo_topical and not norma_especifica
                       and len(assuntos_distintos(familias,temas))>=2 and len(en.split())<=80
                       and not re.search(r'\b(?:i\s*[-.]|ii\s*[-.]|considere a seguinte situacao|caso|quando|se o|se a)\b',sem_acento(en)))
    sem_conteudo=not conteudo_especifico(' '.join([en,cmd])) and not norma_especifica
    candidato_alts=sem_conteudo or lista_de_assuntos
    alternativas_suficientes=alternativas_tematicas(q)
    ignorar=candidato_alts and alternativas_suficientes
    insuficiente=candidato_alts and not alternativas_suficientes and sem_conteudo
    efetiva=dict(q)
    efetiva['enunciado_html']='' if ignorar else en
    efetiva['comando']='' if ignorar else cmd
    if ignorar:
        # Evita reintroduzir o tema do enunciado pelos metadados do site.
        efetiva['disciplina_origem']=''
        efetiva['assunto_origem']=''
    return efetiva,{'modo':'alternativas_exclusivas' if ignorar else 'enunciado_preservado',
        'peso_textual_enunciado':0 if ignorar else 1,
        'motivo':'lista_de_assuntos_sem_caso' if lista_de_assuntos else 'instrucao_sem_tema' if sem_conteudo else 'conteudo_informativo',
        'cabecalho_removido':cabecalho,'enunciado_original':original,
        'enunciado_efetivo':efetiva['enunciado_html'],'comando_efetivo':efetiva['comando'],
        'alternativas_suficientes':alternativas_suficientes,
        'conteudo_insuficiente':insuficiente,'familias_literais_no_enunciado':familias}


def foco(q, temas):
    texto=limpar(q.get('enunciado_html',''))
    norm=sem_acento(texto)
    refs=[]
    for m in MARCADOR.finditer(norm):
        antes=texto[max(0,m.start()-550):m.start()]
        depois=texto[m.end():m.end()+400]
        marcador=m.group()
        if RETOMADA.fullmatch(marcador) and re.match(r'\s*(?:abaixo|a seguir)',sem_acento(depois)):
            # Referência prospectiva: não buscar o antecedente à esquerda.
            parte=depois
            limite=FIM.search(parte)
            if limite and parte[limite.end():].strip():parte=parte[limite.end():]
            trecho=parte.strip()
            tipo='conduta_seguinte'
        else:
            fim=FIM.search(depois)
            if fim:depois=depois[:fim.start()]
            inst=INSTRUCAO.search(sem_acento(depois))
            if inst:depois=depois[:inst.start()]
            trecho=depois.strip(' ,.-–')
            tipo='complemento'
            if RETOMADA.fullmatch(marcador):
                citas=re.findall(r'[“"‘]([^”"’]{12,500})[”"’]',antes)
                if citas:
                    trecho=citas[-1]
                    tipo='citacao_anterior'
                else:
                    frases=re.split(r'(?<=[.!?])\s+',antes)
                    trecho=' '.join(frases[-2:]+[depois]).strip()
                    tipo='janela_anterior'
            elif marcador=='como sendo':
                # Preserva o conceito que é definido; não só sua descrição.
                esquerda=re.split(r'(?<=[.!?])\s+',antes)[-1]
                trecho=' '.join([esquerda,trecho]).strip()
                tipo='definicao_com_antecedente'
        fs=familias_literais(trecho,temas)
        pendente=bool(re.search(r'\b(?:e|sera|seria|sao|deve|devera|podera|pode)\s*$',sem_acento(trecho)))
        especifico=bool(conteudo_especifico(trecho))
        varios=len(assuntos_distintos(fs,temas))>1
        aceito=bool(especifico and not pendente and not varios)
        motivo='lista_de_assuntos' if varios else 'predicado_incompleto' if pendente else 'referencia_generica' if not especifico else 'foco_utilizavel'
        refs.append({'marcador':texto[m.start():m.end()],'trecho':trecho,'tipo':tipo,
                     'aceito':aceito,'motivo':motivo,'familias_literais':fs})
    # Deduplica referências contidas em outra para não triplicar a mesma conduta.
    trechos=[]
    for r in sorted((r for r in refs if r['aceito']),key=lambda r:-len(r['trecho'])):
        t=r['trecho']
        if not any(f.normalizar(t) in f.normalizar(x) for x in trechos):trechos.append(t)
    return {'referencias':refs,'texto_foco':' '.join(trechos),'presente':bool(trechos),
            'considerando_e_marcador':False}
