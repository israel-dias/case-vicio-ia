"""Etapa opcional de preparação: produz somente vetores, sem folha-verdade.

Não é importada nem executada pelo classificador. Requer fastembed==0.9.0.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Definido antes de importar o runtime: a API sozinha pode ser tardia para o
# evento de inicialização. Os arquivos do modelo são obtidos por URLs fixas.
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import experimento_campos as base
import semantico_textos as textos

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REPOSITORIO = "Qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q"
REVISAO = "faf4aa4225822f3bc6376869cb1164e8e3feedd0"
ARQUIVOS_MODELO = ("config.json", "model_optimized.onnx", "special_tokens_map.json",
                   "tokenizer.json", "tokenizer_config.json")
HASHES_FIXOS = {
    "model_optimized.onnx": "634d0f66c29dc934c8fa72b8a4fe91dd4d420a22f1d82a241058d4316e659a99",
    "tokenizer.json": "fa685fc160bbdbab64058d4fc91b60e62d207e8dc60b9af5c002c5ab946ded00",
}


def baixar_modelo(pasta):
    pasta.mkdir(parents=True, exist_ok=True)

    def baixar(nome):
        destino = pasta / nome
        if destino.exists():
            if nome in HASHES_FIXOS and base.sha256(destino) != HASHES_FIXOS[nome]:
                raise ValueError(f"Arquivo de modelo diferente: {destino}. Use outra pasta.")
            return
        url = f"https://huggingface.co/{REPOSITORIO}/resolve/{REVISAO}/{nome}?download=true"
        temporario = pasta / (nome + ".parcial")
        try:
            with urllib.request.urlopen(url, timeout=60) as origem, temporario.open("wb") as saida:
                shutil.copyfileobj(origem, saida, length=1024 * 1024)
            if nome in HASHES_FIXOS and base.sha256(temporario) != HASHES_FIXOS[nome]:
                raise ValueError(f"Hash inesperado no download: {nome}")
            temporario.replace(destino)
        except BaseException:
            temporario.unlink(missing_ok=True)
            raise
        print(f"Modelo: {nome} obtido.", flush=True)

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(baixar, ARQUIVOS_MODELO))


def dividir_texto(texto, tokenizer, limite=112, sobreposicao=16):
    """Janelas de tokens, com verificação após recorte; evita truncamento silencioso."""
    offsets = tokenizer.encode(texto, add_special_tokens=False).offsets
    if not offsets:
        raise ValueError("Texto vazio para embedding.")
    partes = []
    inicio = 0
    while inicio < len(offsets):
        fim = min(inicio + limite, len(offsets))
        while True:
            trecho = texto[offsets[inicio][0]:offsets[fim - 1][1]]
            quantidade = len(tokenizer.encode(trecho, add_special_tokens=True).ids)
            if quantidade <= 126:
                break
            fim -= 1
            if fim <= inicio:
                raise ValueError("Não foi possível respeitar o limite de tokens.")
        peso = fim - inicio if inicio == 0 else max(1, fim - inicio - sobreposicao)
        partes.append((trecho, peso, quantidade))
        if fim == len(offsets):
            break
        inicio = max(inicio + 1, fim - sobreposicao)
    return partes


def preparar(dados, pasta_modelo, saida, permitir_download=False):
    inicio = time.perf_counter()
    if saida.exists():
        raise ValueError("Saída já existe; use outra pasta para preservar a versão.")
    if permitir_download:
        baixar_modelo(pasta_modelo)
    for nome in ARQUIVOS_MODELO:
        if not (pasta_modelo / nome).is_file():
            raise ValueError("Modelo local incompleto. Use --baixar-modelo na preparação.")
    for nome, esperado in HASHES_FIXOS.items():
        if base.sha256(pasta_modelo / nome) != esperado:
            raise ValueError(f"Modelo com hash diferente: {nome}")
    # Importações e carregamento do encoder existem somente nesta preparação.
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    from tokenizers import Tokenizer
    from fastembed import TextEmbedding

    tokenizer = Tokenizer.from_file(str(pasta_modelo / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    temas = base.ler_temas(dados / "temas.csv")
    questoes = {}
    with (dados / "questoes.jsonl").open(encoding="utf-8-sig") as arquivo:
        for linha in arquivo:
            if linha.strip():
                q = json.loads(linha)
                if q["id"] in questoes:
                    raise ValueError("Questão repetida.")
                questoes[q["id"]] = q
    objetos = [("questoes", qid, textos.texto_questao(q)) for qid, q in sorted(questoes.items())]
    objetos += [("temas", tid, textos.texto_tema(t))
                for tid, t in sorted(textos.temas_candidatos(temas).items())]
    encoder = TextEmbedding(model_name=MODELO, specific_model_path=str(pasta_modelo),
                            providers=["CPUExecutionProvider"], threads=2, local_files_only=True)
    vetores = {"questoes": {}, "temas": {}}
    hashes_textos = {"questoes": {}, "temas": {}}
    max_tokens, total_janelas = 0, 0
    for contador, (tipo, identificador, texto) in enumerate(objetos, 1):
        partes = dividir_texto(texto, tokenizer)
        embeddings = list(encoder.embed([trecho for trecho, _, _ in partes], batch_size=16))
        soma = [0.0] * 384
        for vetor, (_, peso, n_tokens) in zip(embeddings, partes):
            normalizado = textos.normalizar_vetor([float(x) for x in vetor])
            soma = [a + peso * b for a, b in zip(soma, normalizado)]
            max_tokens = max(max_tokens, n_tokens)
        vetores[tipo][identificador] = [round(x, 8) for x in textos.normalizar_vetor(soma)]
        hashes_textos[tipo][identificador] = textos.hash_texto(texto)
        total_janelas += len(partes)
        if contador % 100 == 0:
            print(f"Preparados {contador}/{len(objetos)} textos; {total_janelas} janelas.", flush=True)
    saida.parent.mkdir(parents=True, exist_ok=True)
    temporaria = Path(tempfile.mkdtemp(prefix=".embeddings-", dir=saida.parent))
    try:
        conteudo = json.dumps(vetores, ensure_ascii=False, separators=(",", ":"),
                              allow_nan=False).encode("utf-8")
        with (temporaria / "vetores.json.gz").open("wb") as arquivo:
            with gzip.GzipFile(filename="", mode="wb", fileobj=arquivo, mtime=0) as comprimido:
                comprimido.write(conteudo)
        manifesto = {
            "versao": "embeddings_semanticos_v1", "versao_textos": textos.VERSAO_TEXTOS,
            "modelo": MODELO, "repositorio": REPOSITORIO, "revisao": REVISAO,
            "dimensao": 384, "licenca_modelo": "Apache-2.0", "provedor": "CPUExecutionProvider",
            "telemetria_desativada": {"ORT_DISABLE_TELEMETRY": "1",
                                      "HF_HUB_DISABLE_TELEMETRY": "1",
                                      "HF_HUB_OFFLINE": "1"},
            "sha256_modelo": {nome: base.sha256(pasta_modelo / nome) for nome in ARQUIVOS_MODELO},
            "sha256_entradas": {nome: base.sha256(dados / nome)
                               for nome in ("questoes.jsonl", "temas.csv")},
            "sha256_vetores": base.sha256(temporaria / "vetores.json.gz"),
            "sha256_textos": hashes_textos,
            "preparacao": {"limite_janela": 112, "sobreposicao_tokens": 16,
                            "max_tokens_com_especiais_observado": max_tokens,
                            "janelas": total_janelas, "pooling": "média ponderada por novos tokens; L2",
                            "tempo_segundos": round(time.perf_counter() - inicio, 3)},
            "versoes": {nome: importlib.metadata.version(nome)
                         for nome in ("fastembed", "onnxruntime", "tokenizers", "numpy")},
            "sha256_codigo_preparacao": base.sha256(Path(__file__)),
            "custo_api_usd": 0,
            "observacoes": ["Somente vetores; nenhuma escolha, voto ou validação de tema.",
                             "Não lê folha_verdade.csv, gabaritos ou respostas anteriores.",
                             "Todos os enunciados, comandos e alternativas são preservados.",
                             "Pesos e tokenizer locais; textos não são enviados a API."],
        }
        (temporaria / "manifesto_embeddings.json").write_text(
            json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporaria.rename(saida)
    except BaseException:
        shutil.rmtree(temporaria, ignore_errors=True)
        raise
    print(json.dumps({"saida": str(saida), "questoes": len(vetores['questoes']),
                      "temas": len(vetores['temas']), "janelas": total_janelas,
                      "tempo_segundos": manifesto['preparacao']['tempo_segundos']},
                     ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Path("dados/anexos"))
    parser.add_argument("--modelo-local", type=Path, default=Path("artefatos/modelo_embedding"))
    parser.add_argument("--saida", type=Path, default=Path("artefatos/embeddings_v1"))
    parser.add_argument("--baixar-modelo", action="store_true")
    args = parser.parse_args()
    preparar(args.dados, args.modelo_local, args.saida, args.baixar_modelo)


if __name__ == "__main__":
    main()
