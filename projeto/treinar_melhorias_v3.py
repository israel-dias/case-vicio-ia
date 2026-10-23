"""Ajusta a candidata final da v3 somente nos 100 rótulos oficiais."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import tempfile

from compatibilidade_v2 import features as f
from compatibilidade_v2 import runtime as base
from melhorias_v3 import aprendizado as a
from melhorias_v3 import runtime as rt
from melhorias_v3.representacao import carregar_catalogo,NOMES


def executar(projeto,experimento,saida):
    if saida.exists():raise ValueError('Modelo existente; escolha outra saída.')
    manifesto=json.loads((experimento/'manifesto.json').read_text())
    for nome,h in manifesto.items():
        p=(experimento/nome).resolve()
        if not p.is_relative_to(experimento.resolve()) or base.sha(p)!=h:raise ValueError('Experimento alterado.')
    protocolo=json.loads((experimento/'protocolo_previo.json').read_text())
    for nome,h in protocolo['arquivos_sha256'].items():
        if base.sha(projeto/nome)!=h:raise ValueError('Código ou preparação mudou após a avaliação: '+nome)
    dados=projeto/'dados/anexos'
    for nome,h in protocolo['dados_sha256'].items():
        if base.sha(dados/nome)!=h:raise ValueError('Anexos mudaram.')
    qs,temas,ys=f.carregar(dados);catalogo,base_rt=carregar_catalogo(projeto)
    linhas={};calibradores={};politicas={}
    for nome in ['controle_v2',*a.METODOS]:
        rows=list(csv.DictReader((experimento/f'previsoes_{nome}.csv').open(encoding='utf-8')))
        if len(rows)!=100 or {r['id'] for r in rows}!=set(ys):raise ValueError('OOF incompleto.')
        for r in rows:
            r['sinal']=float(r['sinal']);r['correto']=int(r['correto']);r['elegivel']=r['elegivel']=='True'
            if r['correto']!=int(f.aceito(r['tema_central_id'],ys[r['id']],temas)):raise ValueError('Acerto OOF incompatível.')
        linhas[nome]=rows
        if nome=='controle_v2':
            calibradores[nome]=base_rt.registro['calibrador'];politicas[nome]=base_rt.registro['politica']
        else:
            calibradores[nome]=a.calibrar(rows);ps=a.confiancas(rows,calibradores[nome]);politicas[nome]=a.politica(rows,ps)
    escolhido=a.escolher(politicas,linhas)
    perfis=catalogo.transformar({i:qs[i] for i in sorted(ys)})
    with f.threadpool_limits(limits=2):
        modelos={'todos':a.ajustar(perfis,ys,catalogo.familias,temas,False),
                 'proximos':a.ajustar(perfis,ys,catalogo.familias,temas,True)}
    resultado=json.loads((experimento/'resumo.json').read_text())
    registro={'versao':rt.VERSAO,'metodo_final':escolhido,'familias':catalogo.familias,'nomes_atributos':NOMES,
        'modelos':modelos,'calibradores':{n:calibradores[n] for n in a.METODOS},'politicas':politicas,
        'codigo_sha256':rt.codigos(),'dependencias':protocolo['dependencias'],
        'resultado_cv':resultado,'protocolo_cv_sha256':base.sha(experimento/'protocolo_previo.json'),
        'anexos_sha256':protocolo['dados_sha256'],
        'procedimento':'Escolha final por suporte empírico nos sinais OOF conhecidos; não é uma nova avaliação independente.',
        'rotulos_usados':100,'sem_rotulo_no_ajuste':0,'ids_de_questoes_como_atributos':False,
        'tabela_de_decisoes_por_questao':False,'llm_na_decisao':False}
    saida.parent.mkdir(parents=True,exist_ok=True);tmp=Path(tempfile.mkdtemp(prefix='.modelo-v3-',dir=saida.parent))
    try:
        shutil.copytree(projeto/'artefatos/compatibilidade_v2',tmp/'base_v2')
        shutil.copyfile(projeto/'melhorias_v3/dados/referencias_normativas_v1.json',tmp/'referencias_normativas_v1.json')
        base.escrever(tmp/'modelo.json',registro)
        base.escrever(tmp/'manifesto_modelo.json',{'arquivos_sha256':{str(p.relative_to(tmp)):base.sha(p) for p in sorted(tmp.rglob('*')) if p.is_file()}})
        rt.Runtime(tmp);tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise
    print(json.dumps({'metodo_final':escolhido,'politica_final':politicas[escolhido],'comparacao_cv':resultado['metodos']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=Path(__file__).parent)
    p.add_argument('--experimento',type=Path,default=Path('experimentos/melhorias_v3_001'))
    p.add_argument('--saida',type=Path,default=Path('artefatos/melhorias_v3'))
    args=p.parse_args();executar(args.projeto.resolve(),args.experimento.resolve(),args.saida.resolve())
