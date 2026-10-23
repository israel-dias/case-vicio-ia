"""Formata vocabulário autorado do catálogo; não classifica nem lê questões/rótulos."""
import argparse
import json
import re
from pathlib import Path

import experimento_campos as base

VERSAO = "escopos_catalogo_v1"
FONTES = {
    "catalogo": "temas.csv fornecido no case; a árvore não foi alterada",
    "CP": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
    "CPP": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm",
    "LEP": "https://www.planalto.gov.br/ccivil_03/leis/l7210.htm",
    "LCP": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3688.htm",
}
LIMITES = {
    "4694": "O título restringe o tema ao CDC; não abrange automaticamente todos os crimes econômicos ou tributários.",
    "4703": "Vocabulário de execução penal não torna este ID equivalente ao homônimo de Processo Penal.",
    "6734": "Vocabulário de execução penal não torna este ID equivalente ao homônimo de Legislação Especial.",
    "4389": "A presença de uma vítima em narrativa não demonstra cobrança de vitimologia.",
    "5127": "A expressão meios de comunicação pode ser contexto; exige conteúdo penal próprio desse grupo.",
    "5501": "Menção a arquivamento não equivale a prescrição. Avaliar o instituto efetivamente cobrado.",
    "5207": "Suspensão condicional da pena não se confunde com suspensão condicional do processo.",
    "5542": "Suspensão condicional do processo não se confunde com suspensão condicional da pena.",
    "5563": "O tema pode conter conteúdo histórico; não se presume vigência atual de todo instituto mencionado.",
}


def ler_vocabulario(caminho):
    registros = {}
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        if not linha.strip() or linha.startswith("#"):
            continue
        partes = linha.split("\t", 1)
        if len(partes) != 2 or not partes[1].strip():
            raise ValueError(f"Linha inválida no vocabulário: {n}")
        ids, descricao = partes
        if re.search(r"\bQ\d{4}\b", descricao):
            raise ValueError("A descrição não pode conter IDs de questões.")
        for tid in ids.split(";"):
            if not tid.isdigit() or tid in registros:
                raise ValueError(f"Tema repetido ou inválido no vocabulário: {tid}")
            registros[tid] = descricao.strip()
    return registros


def construir(temas, vocabulario):
    candidatos = {tid: t for tid, t in temas.items() if t["ativo"] and t["nivel"] != 0
                  and all(temas[p]["ativo"] for p in base.ancestrais(tid, temas))}
    if set(vocabulario) - set(candidatos):
        raise ValueError("O vocabulário contém tema desconhecido, inativo ou raiz.")
    saida = {}
    for tid, t in sorted(candidatos.items()):
        descricao = vocabulario.get(tid, "")
        limite = LIMITES.get(tid, "Preservar o caminho e avaliar conteúdo efetivamente cobrado; nomes homônimos não implicam equivalência.")
        if not descricao:
            limite = "Recorte insuficientemente descrito no título. Não presumir equivalência com módulo geral nem inventar sua divisão em partes."
        saida[tid] = {
            "tema_id": tid, "titulo_original": t["titulo"], "caminho_original": t["caminho"],
            "descricao_proposta": descricao,
            "status_proposta": "proposta_sem_validacao_juridica_independente" if descricao else "escopo_pendente",
            "limites_para_documentacao": limite,
            "observacao": "Limites não são indexados como termos positivos nem usados como veto automático.",
        }
    return saida


def gerar(temas_path, vocabulario_path, saida):
    if saida.exists():
        raise ValueError("Arquivo de saída já existe; escolha outro para registrar nova versão.")
    temas = base.ler_temas(temas_path)
    registros = construir(temas, ler_vocabulario(vocabulario_path))
    objeto = {
        "versao": VERSAO,
        "sha256_temas": base.sha256(temas_path),
        "sha256_vocabulario_autorado": base.sha256(vocabulario_path),
        "fontes_base_consultadas": FONTES,
        "proveniencia": {
            "autor": "Assistente nesta conversa; identificador do modelo não confirmado.",
            "natureza": "Propostas de escopo e vocabulário para os temas, não rótulos de questões.",
            "contexto": "O histórico desta conversa inclui os 100 rótulos oficiais e diagnósticos do desenvolvimento. Não é geração cega ou independente.",
            "execucao_gerador": "Lê somente temas.csv e vocabulário autorado; não lê questoes.jsonl, folha_verdade.csv ou decisões anteriores.",
            "revisao": "Sem revisão jurídica independente. Referências normativas são bases terminológicas; não se afirma validação integral de cada proposta.",
            "custo_api_usd": 0,
            "tokens_conversa": "não medidos; assinatura existente não rateada",
            "prompt_referencia_nao_transcricao": "Propor descrições e sinônimos de escopo a partir dos títulos e caminhos do catálogo e do diagnóstico de desenvolvimento. Preservar IDs, árvore, nomes e status. Não classificar questões avaliadas, não copiar questões, não usar seus IDs como regras, não equiparar homônimos e não inventar escopos dos módulos por partes. Manter limites fora do texto positivo de busca.",
        },
        "contagens": {"candidatos": len(registros),
                      "com_proposta": sum(bool(r["descricao_proposta"]) for r in registros.values()),
                      "escopo_pendente": sum(not r["descricao_proposta"] for r in registros.values())},
        "temas": registros,
    }
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(objeto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return objeto


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--temas", type=Path, default=Path("dados/anexos/temas.csv"))
    p.add_argument("--vocabulario", type=Path, default=Path("artefatos/escopos_v1/vocabulario_autorado.tsv"))
    p.add_argument("--saida", type=Path, default=Path("artefatos/escopos_v1/escopos.json"))
    args = p.parse_args()
    try:
        resultado = gerar(args.temas, args.vocabulario, args.saida)
    except (ValueError, OSError, KeyError) as erro:
        p.exit(2, f"Erro: {erro}\n")
    print(json.dumps(resultado["contagens"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
