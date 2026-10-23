"""Obtém fontes legislativas públicas; não infere respostas nem valida Direito."""
import argparse, concurrent.futures, hashlib, json, re, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

FONTES = {
 'CP':'https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm',
 'CPP':'https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm',
 'LEP':'https://www.planalto.gov.br/ccivil_03/leis/l7210.htm',
 'JECRIM':'https://www.planalto.gov.br/ccivil_03/leis/l9099.htm',
 'DROGAS':'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11343.htm',
 'ABUSO':'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13869.htm',
 'TERROR':'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/lei/l13260.htm',
 'LMP':'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm',
 'AMBIENTAL':'https://www.planalto.gov.br/ccivil_03/leis/l9605.htm',
 'LAVAGEM':'https://www.planalto.gov.br/ccivil_03/leis/l9613.htm',
 'ORGANIZACOES':'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12850.htm',
 'TRIBUTARIOS':'https://www.planalto.gov.br/ccivil_03/leis/l8137.htm',
 'TORTURA':'https://www.planalto.gov.br/ccivil_03/leis/l9455.htm',
 'HEDIONDOS':'https://www.planalto.gov.br/ccivil_03/leis/l8072.htm',
 'ARMAS':'https://www.planalto.gov.br/ccivil_03/leis/2003/l10.826.htm',
 'IDOSO':'https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741compilado.htm',
 'ALTERACAO_IDOSO':'https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15163.htm',
 'DISCRIMINACAO_TRABALHO':'https://www.planalto.gov.br/ccivil_03/leis/l9029.htm',
 'SOFTWARE':'https://www.planalto.gov.br/ccivil_03/leis/l9609.htm',
 'FALENCIAS':'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11101.htm',
 'ECA':'https://www.planalto.gov.br/ccivil_03/leis/l8069.htm',
 'PAGAMENTO_TRIBUTARIO':'https://www.planalto.gov.br/ccivil_03/leis/2003/l10.684.htm',
 'CF':'https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm',
 'PACOTE':'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13964.htm',
 'CPC':'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm',
}
class Texto(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True);self.partes=[];self.excluidos=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','s','strike','del'):self.excluidos.append(tag)
  if not self.excluidos and tag in ('p','br','div','tr','h1','h2','h3'):self.partes.append('\n')
 def handle_endtag(self,tag):
  if self.excluidos and tag==self.excluidos[-1]:self.excluidos.pop()
  if not self.excluidos and tag in ('p','div','tr'):self.partes.append('\n')
 def handle_data(self,data):
  if not self.excluidos:self.partes.append(data)

def decodificar(b):
 if b.startswith((b'\xff\xfe',b'\xfe\xff')):return b.decode('utf-16',errors='replace'),'utf-16-com-substituicao-se-byte-final-incompleto'
 if b.startswith(b'\xef\xbb\xbf'):return b.decode('utf-8-sig'),'utf-8-sig'
 try:return b.decode('utf-8'),'utf-8'
 except UnicodeDecodeError:return b.decode('cp1252',errors='replace'),'cp1252'

def obter(item,cache):
 nome,url=item
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=18) as r:
   b=r.read(5*1024*1024); final=r.url
  if len(b)>=5*1024*1024:raise ValueError('Fonte ultrapassa limite de tamanho')
  html,encoding=decodificar(b);parser=Texto();parser.feed(html)
  t='\n'.join(re.sub(r'\s+',' ',s).strip() for s in ''.join(parser.partes).splitlines());t=re.sub('\n{3,}','\n\n',t)
  if '\x00' in t or len(t)<300:raise ValueError('Texto não legível após extração')
  cache.mkdir(parents=True,exist_ok=True);(cache/f'{nome}.html').write_bytes(b);(cache/f'{nome}.txt').write_text(t,encoding='utf-8')
  return {'nome':nome,'url':url,'url_final':final,'encoding':encoding,'sha256_html':hashlib.sha256(b).hexdigest(),'sha256_texto':hashlib.sha256(t.encode()).hexdigest(),'obtida':True,'bytes_html':len(b),'data_obtencao_utc':datetime.now(timezone.utc).isoformat(),'nota':'Texto atual extraído sem trechos riscados; não equivale a gabarito nem a versão histórica da prova.'}
 except Exception as e:return {'nome':nome,'url':url,'obtida':False,'erro':str(e)}

def executar(cache,indice):
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rs=list(pool.map(lambda x:obter(x,cache),FONTES.items()))
 indice.parent.mkdir(parents=True,exist_ok=True);indice.write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n')
 return {'fontes':len(rs),'obtidas':sum(x['obtida'] for x in rs),'falhas':[x['nome'] for x in rs if not x['obtida']]}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,default=Path('auditoria_v4/cache_local/normas'));p.add_argument('--indice',type=Path,default=Path('auditoria_v4/fontes/normas_nova_consulta.json'));a=p.parse_args();print(json.dumps(executar(a.cache,a.indice),ensure_ascii=False))
