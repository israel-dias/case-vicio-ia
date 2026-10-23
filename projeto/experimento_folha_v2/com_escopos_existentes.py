"""Usa os escopos congelados do projeto local, sem modificar seus arquivos.

Este adaptador depende da interface pública de calibrar_etapa2.py já usada
no projeto. Se o contrato divergir, interrompe com erro em vez de adivinhar.
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from pathlib import Path

import experimento as e
import modelo as m


def formatar_leitura(formatador_padrao, resultados, tempo):
    texto = formatador_padrao(resultados, tempo)
    return texto.replace(
        "O controle usa o catálogo original, sem os escopos enriquecidos da entrega anterior. Por isso as diferenças desta tabela isolam os métodos deste pacote; não são uma reprodução do classificador anterior.",
        "Nesta execução, o controle usa os escores do classificador de escopos congelado do projeto informado. As variantes usam exatamente esses mesmos escores como evidência, além dos campos textuais e, quando aplicável, dos vizinhos oficiais de treino. Os folds e a calibração deste experimento são novos; não é uma reprodução do teste reservado antigo. A origem e os hashes estão em protocolo_previo.json.")


def configuracao_metodo(documento):
    achadas = []
    def buscar(obj):
        if isinstance(obj, dict):
            if {"modo", "peso_escopo", "familia"} <= set(obj):
                achadas.append(obj)
            else:
                for v in obj.values():
                    buscar(v)
        elif isinstance(obj, list):
            for v in obj:
                buscar(v)
    buscar(documento)
    unicas = {json.dumps(c, sort_keys=True): c for c in achadas}
    if len(unicas) != 1:
        raise ValueError("Não foi possível identificar uma única configuração congelada. Envie metodo_congelado.json para adaptar a interface.")
    return next(iter(unicas.values()))


def preparar(projeto, dados):
    projeto = Path(projeto).resolve()
    if not (projeto/"calibrar_etapa2.py").is_file():
        raise ValueError("A pasta do projeto precisa conter calibrar_etapa2.py.")
    metodo_path = projeto/"experimentos/escopos_001/metodo_congelado.json"
    escopos_path = projeto/"artefatos/escopos_v1/escopos.json"
    vocab_path = projeto/"artefatos/escopos_v1/vocabulario_autorado.tsv"
    # Importação usa o código do projeto local; nada é baixado ou sobrescrito.
    sys.path.insert(0, str(projeto))
    cal = importlib.import_module("calibrar_etapa2")
    if Path(cal.__file__).resolve().parent != projeto:
        raise ValueError("calibrar_etapa2 importado de uma pasta diferente da informada.")
    retorno = cal.conferir_congelamento(Path(dados), metodo_path, escopos_path, vocab_path)
    if not isinstance(retorno, tuple) or len(retorno) != 5:
        raise ValueError("Interface de conferir_congelamento diferente da esperada. Envie calibrar_etapa2.py para adaptar.")
    metodo, questoes, verdade, temas_originais, propostas = retorno
    cfg = configuracao_metodo(metodo)
    classificador = cal.esc.ClassificadorEscopos(temas_originais, propostas, cfg)
    classe_base = m.Catalogo

    class CatalogoComEscopos(classe_base):
        def transformar(self, qs):
            perfis = super().transformar(qs)
            for qid, q in qs.items():
                escores = classificador.pontuar(q)
                if not isinstance(escores, dict):
                    raise ValueError("pontuar() precisa retornar um mapa tema → número. Envie experimento_escopos.py para adaptar.")
                escores = {str(tid): float(v) for tid, v in escores.items()}
                if not all(math.isfinite(v) and v >= 0 for v in escores.values()):
                    raise ValueError("O classificador congelado retornou escores inválidos.")
                if not set(escores) <= set(self.familias):
                    raise ValueError("O método congelado não retornou exclusivamente famílias de nível 1. Nenhuma agregação será adivinhada.")
                novo = m.np.asarray([escores.get(t, 0.) for t in self.familias])
                perfis[qid]["scores"] = novo
                # Atributo 0 é a evidência do classificador congelado; os demais
                # continuam sendo sinais textuais independentes por campo.
                perfis[qid]["features"][:, 0] = novo
            return perfis

    arquivos = {"metodo": metodo_path, "escopos": escopos_path, "vocabulario": vocab_path,
                "calibrar_etapa2.py": projeto/"calibrar_etapa2.py",
                "experimento_escopos.py": projeto/"experimento_escopos.py",
                "experimento_campos.py": projeto/"experimento_campos.py",
                "gerar_escopos.py": projeto/"gerar_escopos.py"}
    origem = {"tipo": "classificador congelado de escopos do projeto existente",
              "sha256": {nome: e.sha(p) for nome, p in arquivos.items()},
              "adaptador_sha256": e.sha(__file__), "configuracao": cfg,
              "atributo_0": "score da família no classificador congelado de escopos",
              "aviso": "Comparar somente os métodos desta execução. Os folds e a calibração são novos; não é reprodução do teste reservado antigo."}
    return CatalogoComEscopos, origem


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", type=Path, required=True)
    p.add_argument("--dados", type=Path)
    p.add_argument("--saida", type=Path, required=True)
    args = p.parse_args()
    dados = args.dados or args.projeto/"dados/anexos"
    try:
        if args.saida.exists():
            raise ValueError("Saída existente: escolha uma pasta nova.")
        fabrica, origem = preparar(args.projeto, dados)
        formatador_padrao = e.leitura
        try:
            # Muda apenas a descrição do controle no relatório, sem alterar
            # classificação, calibração, folds ou avaliação.
            e.leitura = lambda rs, t: formatar_leitura(formatador_padrao, rs, t)
            with m.threadpool_limits(limits=2):
                resultados = e.executar(dados, args.saida, fabrica, origem)
        finally:
            e.leitura = formatador_padrao
        for nome, r in resultados.items():
            print(nome, json.dumps(r, ensure_ascii=False))
        print("Leitura:", args.saida/"LEITURA.md")
    except (OSError, ValueError, KeyError, AttributeError, TypeError, ImportError) as exc:
        p.exit(1, f"Erro no adaptador: {exc}\nNão altere nem regenere os artefatos antigos para contornar esse erro. Envie a saída e os arquivos mencionados para adaptar a leitura.\n")


if __name__ == "__main__":
    main()
