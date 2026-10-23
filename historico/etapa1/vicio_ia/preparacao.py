"""Limpa a apresentação sem resolver ou reescrever questões jurídicas."""
import re
import unicodedata
from html.parser import HTMLParser


class ExtratorTexto(HTMLParser):
    BLOCOS = {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self.ignorar = 0
        self.imagens = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignorar += 1
        if tag == "img":
            self.imagens = True
        if tag in self.BLOCOS and not self.ignorar:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.ignorar = max(0, self.ignorar - 1)
        if tag in self.BLOCOS and not self.ignorar:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self.ignorar:
            self.partes.append(data)


def limpar_html(texto: str) -> tuple[str, bool]:
    parser = ExtratorTexto()
    parser.feed(texto.replace("\\r\\n", "\n").replace("\\n", "\n"))
    parser.close()
    texto_limpo = "".join(parser.partes).replace("\xa0", " ")
    linhas = [re.sub(r"[ \t\r\f\v]+", " ", linha).strip()
              for linha in texto_limpo.splitlines()]
    return "\n".join(linha for linha in linhas if linha), parser.imagens


def normalizar_nome(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return re.sub(r"\s+", " ", "".join(c for c in texto if not unicodedata.combining(c))).strip().casefold()


def disciplina_comparavel(texto: str) -> str:
    normal = normalizar_nome(texto)
    return {"direito penal": "penal", "direito processual penal": "processo penal"}.get(normal, normal)


def preparar_questoes(registros: list[dict], disciplinas: set[str]) -> list[dict]:
    vistos, preparados = set(), []
    campos = {"id", "enunciado_html", "comando", "alternativas", "disciplina_origem", "assunto_origem"}
    for questao in registros:
        if not campos <= questao.keys():
            raise ValueError("Questão sem os campos obrigatórios.")
        identificador = questao["id"]
        if not isinstance(identificador, str) or not re.fullmatch(r"Q\d{4}", identificador):
            raise ValueError(f"ID inválido: {identificador!r}")
        if identificador in vistos:
            raise ValueError(f"ID de questão duplicado: {identificador}")
        vistos.add(identificador)
        if any(not isinstance(questao[c], str) for c in campos - {"alternativas"}):
            raise ValueError(f"{identificador}: campos textuais inválidos.")
        alternativas = questao["alternativas"]
        if not isinstance(alternativas, dict) or not alternativas:
            raise ValueError(f"{identificador}: alternativas ausentes.")
        if any(not isinstance(k, str) or not isinstance(v, str) or not v.strip()
               for k, v in alternativas.items()):
            raise ValueError(f"{identificador}: alternativa inválida ou vazia.")
        enunciado, imagem = limpar_html(questao["enunciado_html"])
        if not enunciado:
            raise ValueError(f"{identificador}: enunciado sem texto.")
        comando, imagem_comando = limpar_html(questao["comando"])
        alternativas_limpas = {}
        for chave, valor in alternativas.items():
            limpo, imagem_alternativa = limpar_html(valor)
            imagem = imagem or imagem_alternativa
            if not limpo:
                raise ValueError(f"{identificador}: alternativa {chave} sem texto.")
            alternativas_limpas[chave] = limpo
        alertas = []
        for campo in ("comando", "disciplina_origem", "assunto_origem"):
            if not questao[campo].strip():
                alertas.append(f"{campo}_ausente")
        if (questao["disciplina_origem"].strip()
                and disciplina_comparavel(questao["disciplina_origem"]) not in disciplinas):
            alertas.append("disciplina_origem_fora_catalogo")
        if imagem or imagem_comando:
            alertas.append("imagem_referenciada_exige_inspecao")
        preparados.append({
            "id": identificador, "enunciado": enunciado, "comando": comando,
            "alternativas": alternativas_limpas, "disciplina_origem": questao["disciplina_origem"],
            "assunto_origem": questao["assunto_origem"], "alertas_preparacao": alertas,
        })
    return preparados
