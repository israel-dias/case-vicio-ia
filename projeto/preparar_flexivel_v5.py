"""Promove a candidata previamente avaliada, sem escolher regras pelo volume nas 559."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from compatibilidade_v2 import runtime as base
from auditoria_confianca_v4.experimento import manifesto_valido
from flexivel_v5 import runtime as rt


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve()
    if saida.exists():raise ValueError('Modelo existente; escolha outro destino.')
    exp=projeto/'experimentos/auditoria_confianca_v4_002';manifesto_valido(exp)
    protocolo=json.loads((exp/'protocolo_previo.json').read_text())
    for n,h in protocolo['codigo_sha256'].items():
        if base.sha(projeto/n)!=h:raise ValueError('Código do experimento alterado: '+n)
    for n,h in protocolo['dados_sha256'].items():
        if base.sha(projeto/'dados/anexos'/n)!=h:raise ValueError('Anexos alterados: '+n)
    antigo=json.loads((exp/'modelos_finais_diagnostico.json').read_text())
    if antigo['escolha_por_100_oof']!='sem_formato':raise ValueError('A candidata diverge da escolha anterior às 559.')
    cv=json.loads((exp/'resumo.json').read_text())['variantes']['sem_formato']
    if not cv['meta_95_na_amostra']:raise ValueError('A candidata não atingiu a meta empírica do experimento.')
    registro={'versao':rt.VERSAO,'variante':'sem_formato','nomes_atributos':rt.ATIVOS,
        'atributos_retirados':list(rt.RETIRADOS),'familias':json.loads((projeto/'artefatos/melhorias_v3/modelo.json').read_text())['familias'],
        'compatibilidade':antigo['modelos']['sem_formato'],'calibrador':antigo['calibradores']['sem_formato'],
        'politica':antigo['politicas']['sem_formato'],'resultado_cv':cv,
        'resultado_procedimento_selecao':json.loads((exp/'resumo.json').read_text())['variantes']['selecao_interna'],
        'codigo_sha256':rt.codigos(),'dependencias':protocolo['dependencias'],
        'anexos_sha256':protocolo['dados_sha256'],'protocolo_origem_sha256':base.sha(exp/'protocolo_previo.json'),
        'rotulos_no_treino':100,'rotulos_das_559_no_treino':0,'ids_como_atributos':False,
        'llm_na_decisao':False,'uso_de_gabaritos_de_respostas':False,
        'limite':'Desenvolvimento sobre rótulos conhecidos; precisão real das 559 não medida.'}
    rt.validar_modelo(registro)
    saida.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.modelo-flexivel-',dir=saida.parent))
    try:
        shutil.copytree(projeto/'artefatos/melhorias_v3/base_v2',tmp/'base_v2')
        shutil.copyfile(projeto/'artefatos/melhorias_v3/referencias_normativas_v1.json',tmp/'referencias_normativas_v1.json')
        base.escrever(tmp/'modelo.json',registro)
        base.escrever(tmp/'manifesto_modelo.json',{'arquivos_sha256':{str(p.relative_to(tmp)):base.sha(p)
            for p in sorted(tmp.rglob('*')) if p.is_file()}})
        rt.Runtime(tmp);tmp.rename(saida)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise
    return {'variante':'sem_formato','atributos':len(rt.ATIVOS),'politica':registro['politica'],'resultado_cv':cv}


if __name__=='__main__':
    root=Path(__file__).parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--projeto',type=Path,default=root)
    p.add_argument('--saida',type=Path,default=root/'artefatos/flexivel_v5')
    args=p.parse_args();print(json.dumps(executar(args.projeto,args.saida),ensure_ascii=False,indent=2))
