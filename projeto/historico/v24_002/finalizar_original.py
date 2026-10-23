"""Gera os arquivos formais do case: 659 linhas, previsão e rastreabilidade."""
import argparse,csv,json,math,shutil
from pathlib import Path
from scipy.stats import beta
from compatibilidade_v2.runtime import sha
from classificar_cobranca_v24 import executar as classificar
from testar_isolamento_v17 import gravar


def intervalo(c,n):
    if not n:return [0.,1.]
    return [float(beta.ppf(.025,c,n-c+1)) if c else 0.,float(beta.ppf(.975,c+1,n-c)) if c<n else 1.]


def executar(projeto,saida):
    projeto,saida=Path(projeto).resolve(),Path(saida).resolve();e=projeto/'experimentos/cobranca_v24_002'
    if (saida/'publicacao.csv').exists():raise ValueError('Entrega já concluída; use pasta nova.')
    reg=json.loads((e/'manifesto_inferencia.json').read_text())
    for nome,h in reg['dados_sha256'].items():
        if sha(projeto/'dados/anexos'/nome)!=h:raise ValueError('Anexo diferente: '+nome)
    packs=json.loads((e/'modelos_finais.json').read_text());sel=packs['selecionado'];chave=sel['variante']+'/'+sel['modo']
    rr=classificar(projeto,projeto/'dados/anexos/questoes.jsonl',saida/'inferencia',e)
    if len(rr)!=659 or len({r['id'] for r in rr})!=659:raise ValueError('Entrega exige exatamente 659 questões únicas.')
    # IDs usados apenas para delimitar o conjunto avaliado, nunca para tema.
    ids_ref=set()
    for f in (e/'folds').glob('fold_*.json'):ids_ref.update(json.loads(f.read_text())['avaliacao_ids'])
    alvo=[r for r in rr if r['id'] not in ids_ref];recentes=[r for r in rr if int(r['id'][1:])>=360]
    if len(ids_ref)!=100 or len(alvo)!=559 or len(recentes)!=300:raise ValueError('Recortes inesperados.')
    stats=json.loads((e/'resumo_100.json').read_text())[chave];n=stats['publicar'];c=stats.get('acertos_publicadas',0)
    pubs=[r for r in alvo if r['decisao']=='publicar'];cob=len(pubs)/len(alvo)
    prev=(c+1)/(n+2) if pubs and n else 0.
    faixa=intervalo(c,n);ant=json.loads((e/'resumo_100.json').read_text())['controle_anterior'];faixa_ant=intervalo(ant['acertos_publicadas'],ant['publicar'])
    faixa=[min(faixa[0],faixa_ant[0],prev),max(faixa[1],faixa_ant[1],prev)]
    saida.mkdir(parents=True,exist_ok=True);shutil.copy2(saida/'inferencia/classificacoes.csv',saida/'publicacao.csv')
    previsao=(f'precisao_prevista: {prev:.8f}\nprecisao_intervalo: {math.floor(faixa[0]*1e8)/1e8:.8f}-{math.ceil(faixa[1]*1e8)/1e8:.8f}\ncobertura_prevista: {cob:.8f}\ncobertura_intervalo: {math.floor(cob*1e8)/1e8:.8f}-{math.ceil(cob*1e8)/1e8:.8f}\n\n'
        f'Precisão: estimativa exploratória da frequência de acerto das publicadas na comparação por folds da composição selecionada, com suavização Beta(1,1): ({c}+1)/({n}+2). Não foi elevada manualmente para atingir 95%. Não é a média das confianças individuais.\n'
        'As 100 referências foram vistas e reutilizadas em ajustes; a composição de controles históricos não é teste independente nem calibração global comprovada. Há risco de otimismo e de mudança de distribuição, especialmente nas 300 recentes. A precisão real das 559 é desconhecida.\n'
        'Faixa de precisão: sensibilidade pela união dos intervalos binomiais descritivos da composição atual e do controle anterior, ampliada para conter a previsão. Não é um intervalo de confiança válido para as 559 após seleção adaptativa.\n'
        'Cobertura: fração exata das 559 decisões conhecidas; intervalo cobre apenas arredondamento, não novas semanas. Os 100 rótulos não entram no denominador da entrega avaliada.\n'
        'Runtime sem LLM, encoder, rede, folha-verdade ou retreino. Nenhum gabarito de resposta é usado para escolher tema. Similaridade, confiança e acerto observado são medidas diferentes.\n')
    (saida/'previsao.txt').write_text(previsao)
    medir=lambda rs:{'questoes':len(rs),'publicar':sum(r['decisao']=='publicar' for r in rs),'revisar':sum(r['decisao']=='revisar' for r in rs),'fora':sum(r['decisao']=='fora' for r in rs),'cobertura':sum(r['decisao']=='publicar' for r in rs)/len(rs)}
    resumo={'total':medir(rr),'fora_folha_verdade':medir(alvo),'recentes_300':medir(recentes),'precisao_prevista':prev,'precisao_intervalo_sensibilidade':faixa,'precisao_real_559':None,'comparacao_100':stats,'selecao':sel,'meta_95_real_comprovada':False,'media_confiancas_publicadas_alvo':sum(r['confianca'] for r in pubs)/len(pubs) if pubs else None}
    gravar(saida/'resumo_entrega.json',resumo);gravar(saida/'integridade.json',{'arquivos_sha256':{n:sha(saida/n) for n in ['publicacao.csv','previsao.txt','resumo_entrega.json']},'659_ids_unicos':True,'ids_referencia_apenas_para_recorte':True});print(json.dumps(resumo,ensure_ascii=False,indent=2));return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--projeto',type=Path,default=Path('.'));p.add_argument('--saida',type=Path,required=True);z=p.parse_args();executar(z.projeto,z.saida)
