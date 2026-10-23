"""Obtém PDFs públicos já localizados nas buscas; não classifica nem confirma gabaritos."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen


def normalizar(s):
    s = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', s)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def obter(item, cache):
    url = item['url']; chave = hashlib.sha256(url.encode()).hexdigest()[:16]
    pdf, txt = cache / (chave + '.pdf'), cache / (chave + '_leitura.txt')
    out = {**item, 'chave': chave, 'url': url}
    try:
        if not pdf.exists():
            with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=14) as r:
                data = r.read(16 * 1024 * 1024 + 1)
            if len(data) > 16 * 1024 * 1024 or not data.startswith(b'%PDF'):
                raise ValueError('Resposta não é PDF ou excede 16 MiB.')
            pdf.write_bytes(data)
        if not txt.exists():
            subprocess.run(['pdftotext', str(pdf), str(txt)], check=True, capture_output=True, timeout=18)
        out.update({'estado': 'texto_obtido_nao_gabarito_confirmado', 'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    'bytes_pdf': pdf.stat().st_size, 'arquivo_texto_local': str(txt)})
    except Exception as e:
        out.update({'estado': 'falha_ao_obter', 'erro': type(e).__name__ + ': ' + str(e)[:180]})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projeto', type=Path, default=Path.cwd())
    parser.add_argument('--cache', type=Path, default=Path('auditoria_v4/cache_local'))
    args = parser.parse_args()
    root = args.projeto
    cache = args.cache
    cache.mkdir(parents=True, exist_ok=True)
    candidatos = json.loads((root / 'auditoria_v4/fontes/provas_candidatas.json').read_text())
    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for resultado in pool.map(lambda i: obter(i, cache), candidatos):
            resultados.append(resultado)
            if len(resultados) % 20 == 0:
                print(json.dumps({'documentos_tentados': len(resultados), 'obtidos': sum(r['estado'].startswith('texto_obtido') for r in resultados)}), flush=True)
    (root / 'auditoria_v4/fontes/obtencao_provas.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n')
    questoes = [json.loads(x) for x in (root / 'dados/processados/questoes_preparadas.jsonl').read_text().splitlines()]
    correspondencias = []
    for doc in resultados:
        if not doc['estado'].startswith('texto_obtido'):
            continue
        pages = Path(doc['arquivo_texto_local']).read_text(errors='replace').split('\f')
        npages = [normalizar(p) for p in pages]
        for q in questoes:
            en = normalizar(q['enunciado'])
            alternatives = [normalizar(v) for v in q['alternativas'].values() if len(normalizar(v)) >= 40]
            for j, page in enumerate(npages):
                neighborhood = page + ' ' + (npages[j + 1] if j + 1 < len(npages) else '')
                stem = len(en) >= 75 and en[:min(300, len(en))] in neighborhood
                alt_hits = sum(a[:min(100, len(a))] in neighborhood for a in alternatives)
                if (stem and (not alternatives or alt_hits >= min(2, len(alternatives)))) or (len(alternatives) >= 3 and alt_hits == len(alternatives)):
                    correspondencias.append({'id': q['id'], 'url': doc['url'], 'chave': doc['chave'], 'pagina_pdf_1based': j + 1,
                                             'enunciado_prefixo_encontrado': stem, 'alternativas_prefixos_encontrados': alt_hits,
                                             'estado': 'correspondencia_textual_candidata_exige_conferencia_visual_de_ordem_e_numero'})
                    break
    (root / 'auditoria_v4/fontes/correspondencias_provas.json').write_text(json.dumps(correspondencias, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'tentados': len(resultados), 'obtidos': sum(r['estado'].startswith('texto_obtido') for r in resultados),
                      'ids_com_correspondencia_candidata': len({r['id'] for r in correspondencias}), 'nao_confirma_gabarito': True}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
