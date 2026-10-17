"""Formata 359 anotações explícitas de reexame. Não chama IA nem infere rótulos."""
import csv,hashlib,json,re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CURTOS={17: 'Defesa preliminar do rito especial de funcionário público não corresponde automaticamente ao nó '
     'subordinado ao Ordinário. Falta nó com esse escopo específico; 5533 é sugestão para decisão '
     'pedagógica.',
 20: 'Cinco julgamentos de campos independentes incluem crimes do ECA sem nó correspondente explícito; '
     'sequência e alcance dos rótulos não confirmados. Extras não comprovam representação adequada do '
     'conjunto.',
 23: 'Possíveis duas alternativas incorretas B/C; conferir original, interpretação da impronúncia e eventual '
     'anulação. Não é retenção por diversidade temática.',
 64: 'Data e regime da extinção de punibilidade por pagamento após trânsito em julgado afetam o conhecimento '
     'decisivo. Conferir fonte e contexto antes de liberar.',
 68: 'B indica condescendência, mas E e a pista de anulação exigem conferir versão oficial. Possível '
     'problema de unicidade da resposta; pista não é anulação confirmada.',
 90: 'A resposta compara réplica em Júri e procedimento originário superior; não há nó explícito para o '
     'segundo. Júri é sugestão parcial para o conhecimento comparativo exigido.',
 104: 'A redação atribui instauração do inquérito ao promotor e relaciona prosseguimento à autoridade '
      'coatora no HC. Distinção instauração/requisição e fundamento jurisprudencial não confirmados.',
 114: 'ADI4424 em2012, norma processual mista e afirmações constitucionais/doutrinárias problemáticas exigem '
      'prova e resposta históricas. A sugestão temporal permanece, sem ocultar a pendência de conteúdo.',
 123: 'Sequência exige conferir seletividade racial, criminalização e efeitos da discriminação na prova. '
      'Faltam referências para assegurar o conjunto e sua organização; não é mera homonímia.',
 163: 'O item usa a revogada Lei4.898/1965 e depende do regime histórico da correspondência prisional. '
      'Conferir prova/contexto, sem atualizar silenciosamente a resposta.',
 165: 'O art.2º,§1º, da Lei12.850 foi alterado pela Lei15.245/2025. O central4705 está escolhido, mas versão '
      'temporal e formulação da resposta exigem conferência.',
 172: 'A resposta indicada exige imunidade parlamentar para recebimento de denúncia; falta nó explícito. '
      'Competência por função não é equivalente; verificar contexto e alcance da sugestão.',
 182: 'Cinco proposições incluem rixa sem nó explícito e quantidade de erros não confirmada. O central é '
      'parcial; extras não solucionam a lacuna do conjunto.',
 219: 'Falta integralmente a situação hipotética. A expressão participação sugere tema, mas o item não pode '
      'ser resolvido ou apresentado completo ao aluno.',
 227: 'O art.240 do ECA é conteúdo adicional necessário; não se sabe se4709 abrange produção de imagem ou o '
      'regime da Lei13.431. É lacuna de escopo, não mero número de temas.',
 236: 'Institutos independentes e afirmação de nulidade absoluta exigem conferir contexto. Provas é sugestão '
      'parcial; resposta e integridade jurídica ainda não confirmadas.',
 260: 'III/IV cobram movimentos sociais e criação de direitos sem escopo claro no catálogo, além dos dois '
      'institutos criminais. Política Criminal é sugestão parcial; conferir fonte/sequência.',
 288: 'Inclui crime de responsabilidade municipal sem nó próprio e afirmação reunindo prefeitos e '
      'vereadores. Pendência concreta de conteúdo/alcance e sequência.',
 319: 'Lista I/II/III não se conecta às opções A–E; possível concatenação de questões. Conferir original '
      'antes de corrigir ou publicar.',
 324: 'A assertiva III sobre periculosidade presumida do semi-imputável e a combinação ofertada exigem '
      'conferência jurídica/histórica. Extras não eliminam essa pendência.',
 326: 'Prescrição/ministração culposa do art.38 é tipo médico autônomo, diferente do tráfico do art.33. '
      'Escolher entre homônimos não esclarece a abrangência desse objeto no módulo.',
 331: 'Possíveis duas alternativas incorretas A/C sobre HC e legitimidade do juiz. Conferir '
      'gabarito/eventual anulação; tema claro não elimina pendência de integridade.',
 348: 'Possível conflito D/E em corrupção internacional, além de alcance do art.337-B não delimitado no nó '
      'de Corrupção Ativa. Conferir original e resposta.',
 355: 'Porte/uso pessoal não penal de maconha do art.28 difere de tráfico. E confirmado não define '
      'abrangência desse objeto no módulo; não é apenas4708/6728.',
 359: 'Lei15.163/2025 alterou art.94 do Estatuto da Pessoa Idosa. Identificar versão histórica e sinalizar '
      'desatualização antes de liberar.'}

def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def escrever(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def executar(p=ROOT):
 a=p/'auditoria_v4';ant={r['id']:r for r in csv.DictReader((p/'historico/v3/publicacao.csv').open(encoding='utf-8'))}
 qs={x['id']:x for x in map(json.loads,(p/'dados/processados/questoes_preparadas.jsonl').read_text().splitlines())}
 ts={x['tema_id']:x for x in csv.DictReader((p/'dados/originais/temas.csv').open(encoding='utf-8'))}
 orig=[]
 for f in sorted((a/'decisoes').glob('*.json')):orig.extend(json.loads(f.read_text()))
 assert len(orig)==359 and {x[0] for x in orig}==set(range(1,360))
 oficiais=json.loads((a/'fontes/gabaritos_confirmados.json').read_text());conferidos=json.loads((a/'fontes/conferencias_dirigidas.json').read_text())['por_id']
 extras_explicitos=json.loads((a/'extras_independentes.json').read_text())
 registros=[]
 for n,resposta,decisao,tema,extras,c,analise,base in sorted(orig):
  id=f'Q{n:04}';q=qs[id]
  if decisao=='revisar':motivo=CURTOS[n]
  else:motivo=re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ú])',analise)[0]
  if len(motivo)>340:motivo=motivo[:337].rsplit(' ',1)[0]+'...'
  depois={'id':id,'decisao':decisao,'tema_central_id':tema or '', 'extras_ids':';'.join(extras),'confianca':f'{c:.2f}','motivo':motivo}
  evidencia=oficiais.get(id)
  if evidencia and evidencia['resposta']!=resposta:raise ValueError('Resposta diverge de gabarito confirmado: '+id)
  estado=evidencia['estado'] if evidencia else ('resposta_assistida_sem_gabarito_oficial_confirmado' if resposta else 'resposta_nao_confirmada')
  r={'id':id,'antes':ant[id],'depois':depois,'resposta_proposta':resposta,'estado_resposta':estado,
   'analise_individual':analise,'fundamento_indicado':base,'conferencias_dirigidas_registradas':conferidos.get(id,[]),
   'gabarito_oficial':evidencia,'busca_registrada':f'auditoria_v4/buscas/{id}.json',
   'caminho_central':ts[tema]['caminho'] if tema else None,'caminhos_extras':[ts[x]['caminho'] for x in extras],
   'justificativas_extras_independentes':extras_explicitos.get(id,{}),
   'referencia_independente_de_tema':False,'data_reexame':'2026-10-16','responsavel':'Assistente nesta conversa, com critérios corrigidos a partir da auditoria de Israel; identificador exato do modelo não confirmado.'}
  registros.append(r)
 escrever(a/'reexame_359.json',{'versao':'v4','tipo':'reexame_assistido_nao_gabarito_juridico','registros':registros})
 matriz=Counter((r['antes']['decisao'],r['depois']['decisao']) for r in registros)
 resumo={'questoes_reexaminadas':359,'decisoes':dict(Counter(r['depois']['decisao'] for r in registros)),
  'cobertura':sum(r['depois']['decisao']=='publicar' for r in registros)/359,
  'mudancas_de_decisao':sum(r['antes']['decisao']!=r['depois']['decisao'] for r in registros),
  'mudancas_de_tema_central':sum(r['antes']['tema_central_id']!=r['depois']['tema_central_id'] for r in registros),
  'mudancas_de_extras':sum(r['antes']['extras_ids']!=r['depois']['extras_ids'] for r in registros),
  'questoes_com_extras':sum(bool(r['depois']['extras_ids']) for r in registros),
  'estados_de_resposta':dict(Counter(r['estado_resposta'] for r in registros)),
  'transicoes':[{'antes':b,'depois':d,'quantidade':c} for (b,d),c in sorted(matriz.items())],
  'precisao_medida':None,'gabaritos_nao_sao_rotulos_tematicos':True,'aumento_de_cobertura_nao_comprova_aumento_de_precisao':True}
 escrever(a/'resumo_auditoria.json',resumo)
 linhas=['# Caderno de auditoria assistida — 359 questões','',
  'Respostas propostas são hipóteses assistidas, salvo estado explicitamente oficial. Gabaritos oficiais não certificam os IDs temáticos. Fundamentos indicados não equivalem a leitura confirmada de todos os precedentes. Os estados e as pendências são parte do resultado.','']
 for r in registros:
  q=qs[r['id']];d=r['depois'];b=r['antes']
  linhas += [f"## {r['id']} — {d['decisao']}",'',q['enunciado'],'']
  if q['comando'] and q['comando'] not in q['enunciado']:linhas += ['**Comando:** '+q['comando'],'']
  for k,v in q['alternativas'].items():linhas += [f'**{k}.** {v}','']
  linhas += [f"**Antes:** {b['decisao']} / {b['tema_central_id'] or 'sem tema'} / extras {b['extras_ids'] or 'nenhum'}.",'',
   f"**Depois:** {d['decisao']} / {r['caminho_central'] or 'nenhum tema ativo compatível'} / extras {d['extras_ids'] or 'nenhum'}.",'',
   f"**Resposta proposta:** {r['resposta_proposta'] or 'não confirmada'} — {r['estado_resposta']}.",'',
   '**Análise:** '+r['analise_individual'],'','**Fundamento indicado/pendências:** '+r['fundamento_indicado'],'']
  if r['justificativas_extras_independentes']:
   linhas += ['**Por que estes extras:** '+ '; '.join(k+': '+v for k,v in r['justificativas_extras_independentes'].items()),'']
  if r['gabarito_oficial']:
   e=r['gabarito_oficial'];linhas += [f"**Fontes oficiais:** [prova]({e['prova_url']}); [gabarito]({e['gabarito_url']}). {e['conferencia']}",'']
 (a/'caderno_auditoria.md').write_text('\n'.join(linhas)+'\n',encoding='utf-8')
 arquivos=['historico/v3/publicacao.csv','dados/originais/questoes.jsonl','dados/originais/temas.csv','dados/processados/questoes_preparadas.jsonl','auditoria_v4/PROTOCOLO_FINAL.md','auditoria_v4/reexame_359.json','auditoria_v4/fontes/gabaritos_confirmados.json','auditoria_v4/fontes/conferencias_dirigidas.json']
 arquivos += [str(f.relative_to(p)) for f in sorted((a/'decisoes').glob('*.json'))]
 arquivos += [str(f.relative_to(p)) for f in sorted((a/'buscas').glob('*.json'))]
 arquivos += ['auditoria_v4/extras_independentes.json','auditoria_v4/fontes/normas_consultadas.json','auditoria_v4/scripts/gerar_auditoria.py','docs/REVISAO_Q0097.md','historico/v4_antes_Q0097/decisao_Q0097.json','auditoria_v4/reavaliacao_57.json','auditoria_v4/fontes/reavaliacao_57.json','docs/REAVALIACAO_57_REVISOES.md','historico/v4_antes_reavaliacao_57/revisoes_57.json']
 manifesto={'versao':'v4','questoes':359,'tipo':'consolidacao_de_reexame_assistido_salvo','entradas_sha256':{s:sha(p/s) for s in arquivos},'nota':'Hashes detectam alteração acidental entre os arquivos registrados; não são assinatura digital nem garantem veracidade jurídica.'}
 escrever(a/'manifesto_auditoria.json',manifesto)
 return resumo
if __name__=='__main__':print(json.dumps(executar(),ensure_ascii=False,indent=2))
