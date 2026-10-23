"""Renderiza quatro páginas do relatório; não participa da classificação."""
import argparse
import html
import json
from pathlib import Path


def gerar(entrada, saida):
    if saida.exists():
        raise ValueError("PDF já existe; use outro nome para preservar a versão.")
    # Dependência opcional, restrita à apresentação do documento.
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab

    fontes = Path(reportlab.__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("VicioSans", str(fontes / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("VicioSansBold", str(fontes / "VeraBd.ttf")))

    doc = json.loads(entrada.read_text(encoding="utf-8"))
    if len(doc["paginas"]) != 4 or "Memo" not in doc["paginas"][-1]["titulo"]:
        raise ValueError("Esperadas quatro páginas, com memo na última.")
    largura, altura = A4
    margem = 43; area_largura = largura - 2 * margem
    topo, base = altura - 111, 65
    roxo = colors.HexColor("#58327F"); verde = colors.HexColor("#126A60")
    escuro = colors.HexColor("#23272C"); cinza = colors.HexColor("#67717A")

    def fluxo(pagina, fonte):
        estilo = ParagraphStyle("corpo", fontName="VicioSans", fontSize=fonte, leading=fonte * 1.30,
                                textColor=escuro, alignment=TA_LEFT, splitLongWords=True)
        sub = ParagraphStyle("sub", parent=estilo, fontName="VicioSansBold", fontSize=fonte + .5,
                             leading=fonte * 1.35, textColor=verde)
        celula = ParagraphStyle("celula", parent=estilo, fontSize=fonte - .5, leading=fonte * 1.14)
        cab = ParagraphStyle("cabecalho", parent=celula, fontName="VicioSansBold", textColor=colors.white)
        objetos = []
        for b in pagina["blocos"]:
            if b["tipo"] == "tabela":
                n = len(b["cabecalho"])
                proporcoes = {2: [.57, .43], 3: [.34, .24, .42], 4: [.21, .18, .22, .39]}[n]
                rows = [[Paragraph(html.escape(str(s)), cab) for s in b["cabecalho"]]]
                rows += [[Paragraph(html.escape(str(s)), celula) for s in r] for r in b["linhas"]]
                objeto = Table(rows, colWidths=[area_largura * x for x in proporcoes], hAlign="LEFT")
                objeto.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), roxo), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F3F1F7"), colors.white]),
                    ("LINEBELOW", (0, -1), (-1, -1), .35, colors.HexColor("#CFC8D7")),
                ]))
                espaco = 9
            else:
                objeto = Paragraph(html.escape(b["texto"]), sub if b["tipo"] == "subtitulo" else estilo)
                espaco = 8 if b["tipo"] == "subtitulo" else 7
            _, h = objeto.wrap(area_largura, altura)
            objetos.append((objeto, h, espaco))
        return objetos

    paginas = []
    for pagina in doc["paginas"]:
        fonte = 10.2
        while True:
            objetos = fluxo(pagina, fonte)
            if sum(h + espaco for _, h, espaco in objetos) <= topo - base:
                break
            fonte = round(fonte - .15, 2)
            if fonte < 9.15:
                raise ValueError(f"Página não cabe com legibilidade adequada: {pagina['titulo']}")
        paginas.append((pagina, objetos, fonte))
    saida.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(saida), pagesize=A4, invariant=1, pageCompression=1)
    canvas.setTitle(doc["titulo"]); canvas.setAuthor(doc["autor"])
    canvas.setSubject("Sistema de classificação, evidência, produção e memo para o professor")
    for numero, (pagina, objetos, fonte) in enumerate(paginas, 1):
        canvas.setFillColor(roxo); canvas.rect(margem, altura - 47, 5, 17, fill=1, stroke=0)
        canvas.setFont("VicioSansBold", 8.5); canvas.drawString(margem + 14, altura - 40, doc["titulo"].upper())
        canvas.setFillColor(cinza); canvas.setFont("VicioSans", 8)
        canvas.drawRightString(largura - margem, altura - 40, pagina["rotulo"])
        canvas.setFillColor(escuro); canvas.setFont("VicioSansBold", 21)
        canvas.drawString(margem, altura - 78, pagina["titulo"])
        canvas.setStrokeColor(colors.HexColor("#D9D3E1")); canvas.setLineWidth(.5)
        canvas.line(margem, altura - 94, largura - margem, altura - 94)
        y = topo
        for objeto, h, espaco in objetos:
            y -= h; objeto.drawOn(canvas, margem, y); y -= espaco
        if y < base - .01:
            raise ValueError("Conteúdo extrapolou a área da página.")
        canvas.setStrokeColor(colors.HexColor("#D9D3E1")); canvas.line(margem, 51, largura - margem, 51)
        canvas.setFillColor(cinza); canvas.setFont("VicioSans", 8)
        canvas.drawString(margem, 38, doc["autor"] + " | Etapa complementar | Regra fixa; precisão final desconhecida")
        canvas.drawRightString(largura - margem, 38, f"{numero} / 4")
        canvas.setFont("VicioSans", 7.3)
        canvas.drawString(margem, 25, "Fontes: github.com/viciod/case-vicio-ia | NIST e-Handbook, seção 7.2.4.1")
        canvas.showPage()
    canvas.save()
    return {"paginas": 4, "fontes_corpo": [f for _, _, f in paginas], "arquivo": str(saida)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entrada", type=Path, default=Path("entrega_etapa2/relatorio_paginas.json"))
    p.add_argument("--saida", type=Path, default=Path("entrega_etapa2/relatorio.pdf"))
    a = p.parse_args()
    try:
        resultado = gerar(a.entrada, a.saida)
    except ImportError:
        p.exit(2, "Erro: instale a dependência opcional com python3 -m pip install -r requirements-relatorio.txt\n")
    except (ValueError, OSError, KeyError) as erro:
        p.exit(2, f"Erro: {erro}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
