"""Relatório descritivo de erros conhecidos, sem mudar classificações."""
import csv,json
from pathlib import Path
from compatibilidade_v2 import features as f


def executar(root=Path('.')):
    root=Path(root);qs,ts,ys=f.carregar(root/'dados/anexos');p=root/'pesquisa_v21';p.mkdir(exist_ok=True)
    ler=lambda fn:list(csv.DictReader((root/fn).open()))
    base={r['id']:r for r in ler('experimentos/semantica_v22_001/avaliacao_100.csv') if r['avaliacao']=='controle_contextual'}
    sem={r['id']:r for r in ler('experimentos/semantica_v21_001/avaliacao_100.csv') if r['avaliacao']=='comparador'}
    caminho=lambda t:ts[t]['caminho'] if t else 'Fora da taxonomia segundo a referência'
    linhas=['# Erros conhecidos e nuances — diagnóstico de desenvolvimento',
            'As 100 referências estão expostas. Este documento compara previsões com os rótulos fornecidos; não usa LLM para resolver ou validar as 559 avaliadas. Uma sugestão errada numa referência não gera uma exceção por ID no classificador.',
            'O controle contextual teve 74 temas aceitos/100. Dos 26 desacertos, oito são referências fora da taxonomia; dos 18 com tema, 17 têm um ramo aceito já entre os cinco candidatos. Isso aponta sobretudo uma falha de ordenação e de convenção/escopo, não uma ausência geral do tema na busca.',
            'A ordem abaixo é somente de leitura. As correções de código são testadas em todos os exemplos; reconhecer um erro neste caderno não prova que uma regra o corrigiu nem autoriza um novo rótulo manual para o alvo.']
    for i,r in sorted(base.items()):
        if r['correto']!='0':continue
        q=qs[i];y=ys[i];cands=r['top5_recuperacao_ids'].split(';');tem=any(f.aceito(t,y,ts) for t in cands)
        tipo='Ausência da taxonomia conforme referência' if y['fora_da_taxonomia']=='1' else 'Escolha errada com ramo aceito disponível no top5' if tem else 'Ramo aceito ausente do top5'
        linhas += [f'## {i} — {tipo}',f"**Controle:** {caminho(r['tema_central_id'])}; {r['decisao']}; confiança estimada {float(r['confianca']):.2%}.",
                   f"**Referência:** {caminho(y['tema_central_id'])}. Extras oficiais: {y['extras_ids'] or 'nenhum'}.",
                   f"**Comparador E5:** {caminho(sem[i]['tema_central_id'])}; {'tema aceito' if sem[i]['correto']=='1' else 'tema não aceito'}; {sem[i]['decisao']}.",
                   '**Enunciado:** '+f.visivel(q['enunciado_html']), '**Comando:** '+(f.visivel(q['comando']) or '(vazio)')]
        linhas += [f"- **{k})** {f.visivel(v)}" for k,v in q['alternativas'].items()]
        linhas += ['**Cinco candidatos do controle:** '+ '; '.join(f'{t}: {caminho(t)}' for t in cands),
                   'Quando a referência está fora, encontrar um título parecido não demonstra que o recorte está coberto. A causa do fora precisa ser esclarecida com a equipe; não inferimos uma proibição geral a partir de uma única questão.' if y['fora_da_taxonomia']=='1' else 'A decisão precisa escolher um ramo sustentado pela cobrança, considerando comando, contexto e alternativas; a menção literal não equivale automaticamente à exigência da questão.']
    (p/'CADERNO_ERROS_CONHECIDOS.md').write_text('\n\n'.join(linhas)+'\n')
    print('Caderno com',sum(r['correto']=='0' for r in base.values()),'erros conhecidos, incluindo oito fora; sem alterar previsões.')


if __name__=='__main__':executar()
