"""Preparação opcional de vetores E5, separada da classificação.

Não abre folha_verdade.csv e não seleciona, vota nem valida temas. Os pesos
locais e o tokenizer ficam fora da entrega; o cache resultante é versionado.
"""
import argparse,gzip,hashlib,json,time,importlib.metadata
from pathlib import Path
import numpy as np
from semantica_v21.textos import vistas,documentos,hash_texto,Extrator,IdentificadoresMorfologicos
from melhorias_v3.representacao import carregar_catalogo

REPO='intfloat/multilingual-e5-small'
REVISAO='614241f622f53c4eeff9890bdc4f31cfecc418b3'


def janelas(texto,tokenizer,limite=440,sobreposicao=32):
    enc=tokenizer.encode(texto,add_special_tokens=False);offs=enc.offsets
    if not offs:raise ValueError('Texto vazio.')
    out=[];inicio=0
    while inicio<len(offs):
        fim=min(inicio+limite,len(offs));trecho=texto[offs[inicio][0]:offs[fim-1][1]]
        out.append((trecho,fim-inicio if not inicio else fim-inicio-sobreposicao))
        if fim==len(offs):break
        inicio=fim-sobreposicao
    return out


def executar(projeto,modelo,saida):
    import onnxruntime as ort
    from tokenizers import Tokenizer
    projeto,modelo,saida=map(lambda p:Path(p).resolve(),[projeto,modelo,saida]);inicio=time.perf_counter()
    if saida.exists():raise ValueError('Saída existente; preserve a versão.')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    hashes={n:sha(modelo/n) for n in ['modelo.onnx','tokenizer.json','config.json']}
    tokenizer=Tokenizer.from_file(str(modelo/'tokenizer.json'));tokenizer.no_truncation();tokenizer.no_padding()
    opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
    ort.disable_telemetry_events();sess=ort.InferenceSession(str(modelo/'modelo.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
    cat,_=carregar_catalogo(projeto);ex=Extrator(cat);det=IdentificadoresMorfologicos(cat)
    propostas=json.loads((projeto/'artefatos/compatibilidade_v2/escopos.json').read_text())['temas']
    qs={}
    for linha in (projeto/'dados/anexos/questoes.jsonl').read_text().splitlines():
        q=json.loads(linha)
        if q['id'] in qs:raise ValueError('Questão repetida.')
        qs[q['id']]=q
    textos={};refs={};traces={}
    for i,q in qs.items():
        vs,tr=vistas(q,ex,det);traces[i]=tr;refs[i]={}
        for v,txt in vs.items():
            entrada='query: '+txt;h=hash_texto(entrada);textos[h]=entrada;refs[i][v]=h
    docs=documentos(cat,propostas);refs_t={}
    for tid,txt in docs.items():
        refs_t[tid]={}
        for prefix in ['query: ','passage: ']:
            entrada=prefix+txt;h=hash_texto(entrada);textos[h]=entrada;refs_t[tid][prefix.strip(': ')]=h
    print(f'Preparando {len(textos)} textos únicos; sem leitura de rótulos.',flush=True)
    vetores={};total_janelas=0;max_tokens=0
    for j,(h,txt) in enumerate(sorted(textos.items()),1):
        prefix='query: ' if txt.startswith('query: ') else 'passage: '
        partes=janelas(txt[len(prefix):],tokenizer);soma=np.zeros(384)
        for trecho,peso in partes:
            enc=tokenizer.encode(prefix+trecho);n=len(enc.ids)
            if n>512:raise ValueError('Limite do encoder excedido; sem truncamento silencioso.')
            ids=np.asarray([enc.ids],dtype=np.int64);mask=np.asarray([enc.attention_mask],dtype=np.int64)
            hidden=sess.run(None,{'input_ids':ids,'attention_mask':mask,'token_type_ids':np.zeros_like(ids)})[0]
            v=(hidden*mask[:,:,None]).sum(1)[0]/mask.sum();v=v/np.linalg.norm(v)
            soma+=peso*v;total_janelas+=1;max_tokens=max(max_tokens,n)
        vetores[h]=np.round(soma/np.linalg.norm(soma),8).tolist()
        if j%100==0:print(f'{j}/{len(textos)} textos; {round(time.perf_counter()-inicio,1)} s.',flush=True)
    saida.mkdir(parents=True)
    with gzip.GzipFile(filename=str(saida/'vetores.json.gz'),mode='wb',mtime=0) as g:
        g.write(json.dumps(vetores,separators=(',',':'),allow_nan=False).encode())
    (saida/'textos_preparados.json').write_text(json.dumps(textos,ensure_ascii=False,indent=2)+'\n')
    (saida/'referencias_textos.json').write_text(json.dumps({'questoes':refs,'temas':refs_t,'traces':traces},ensure_ascii=False,indent=2)+'\n')
    reg={'modelo':REPO,'revisao':REVISAO,'arquivo_modelo':'onnx/model_qint8_avx512_vnni.onnx','licenca':'MIT',
         'sha256_modelo':hashes,'dimensao':384,'prefixos':['query: ','passage: '],
         'pooling':'média dos tokens mascarados, L2, média ponderada das janelas, L2',
         'limite_janela':440,'sobreposicao':32,'max_tokens_observado':max_tokens,'janelas':total_janelas,
         'textos_unicos':len(textos),'questoes':len(qs),'temas':len(docs),'segundos':time.perf_counter()-inicio,
         'custo_api_usd':0,'provedor':'CPUExecutionProvider','rotulos_lidos':False,
         'sha256_entradas':{n:sha(projeto/'dados/anexos'/n) for n in ['questoes.jsonl','temas.csv']},
         'sha256_escopos':sha(projeto/'artefatos/compatibilidade_v2/escopos.json'),
         'sha256_codigo':{n:sha(projeto/n) for n in ['preparar_semantica_v21.py','semantica_v21/textos.py']},
         'versoes':{n:importlib.metadata.version(n) for n in ['numpy','onnxruntime','tokenizers']},
         'sha256_artefatos':{n:sha(saida/n) for n in ['vetores.json.gz','textos_preparados.json','referencias_textos.json']},
         'limites':'Encoder genérico; embeddings não são probabilidade nem rótulos. Inferência lê apenas vetores preparados.'}
    (saida/'manifesto.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n');print(json.dumps(reg,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--modelo',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.modelo,z.saida)
