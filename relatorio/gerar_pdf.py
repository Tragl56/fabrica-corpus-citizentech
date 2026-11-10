"""Gera relatorio/relatorio.pdf a partir de relatorio/relatorio.html (requer: pip install pymupdf)."""
from pathlib import Path

import pymupdf

AQUI = Path(__file__).parent
CSS = """
body { font-family: sans-serif; font-size: 9.6pt; line-height: 1.32; color: #1a1a1a; }
h1 { font-size: 19pt; color: #0b4f6c; margin-bottom: 2pt; }
h2 { font-size: 12pt; color: #0b4f6c; margin-top: 9pt; margin-bottom: 3pt; }
p { margin-top: 2pt; margin-bottom: 4pt; text-align: justify; }
.sub { color: #555; font-size: 9pt; }
.code { font-family: monospace; font-size: 8pt; background-color: #f2f4f5; padding: 4pt; }
code { font-family: monospace; font-size: 8.5pt; }
table { border-collapse: collapse; margin-top: 3pt; margin-bottom: 5pt; width: 100%; }
th { background-color: #0b4f6c; color: white; font-size: 8.5pt; padding: 2pt; text-align: left; }
td { border: 1px solid #c8d0d4; font-size: 8.5pt; padding: 2pt; }
li { margin-bottom: 2pt; }
"""


def main():
    html = (AQUI / "relatorio.html").read_text(encoding="utf-8")
    story = pymupdf.Story(html=html, user_css=CSS)
    saida = AQUI / "relatorio.pdf"
    writer = pymupdf.DocumentWriter(str(saida))
    pagina = pymupdf.paper_rect("a4")
    area = pagina + (48, 44, -48, -44)
    mais, n = 1, 0
    while mais:
        dev = writer.begin_page(pagina)
        mais, _ = story.place(area)
        story.draw(dev)
        writer.end_page()
        n += 1
    writer.close()
    print(f"{saida} gerado com {n} páginas")


if __name__ == "__main__":
    main()
