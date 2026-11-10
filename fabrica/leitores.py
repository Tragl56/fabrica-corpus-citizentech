"""Etapa 1a — Leitores de formato: transformam qualquer arquivo suportado em texto "bruto padronizado".

Convenções de saída (entendidas pela limpeza e pelo chunking):
  - títulos/cabeçalhos viram linhas "## Título";
  - texto tachado (<s>, <strike>, <del>, w:strike do Word) vira ~~...~~ (trecho revogado);
  - um parágrafo por linha.

Formatos: .txt, .md, .html/.htm, .docx (biblioteca padrão) e .pdf (PyMuPDF, ou pypdf como
alternativa). Outros formatos geram FormatoNaoSuportado.
"""
import re
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

EXTENSOES = {".txt", ".md", ".markdown", ".html", ".htm", ".docx", ".pdf"}


class FormatoNaoSuportado(Exception):
    pass


# ---------------------------------------------------------------- texto e markdown
def _ler_texto(dados: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return dados.decode(enc)
        except UnicodeDecodeError:
            continue
    return dados.decode("utf-8", errors="replace")


def ler_markdown(dados: bytes) -> str:
    linhas = []
    for ln in _ler_texto(dados).splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", ln)
        if m:
            linhas.append(f"## {m.group(1).strip()}")
        else:
            ln = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda x: x.group(1) or x.group(2), ln)   # negrito
            ln = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", ln)                                  # links
            linhas.append(ln)
    return "\n".join(linhas)


# ---------------------------------------------------------------- HTML
class _HTMLTexto(HTMLParser):
    BLOCO = {"p", "div", "br", "li", "tr", "section", "article", "table", "ul", "ol", "blockquote", "td"}
    TITULO = {"h1", "h2", "h3"}
    IGNORAR = {"script", "style", "nav", "header", "footer", "noscript", "form", "button", "aside"}
    TACHADO = {"s", "strike", "del"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes, self.ignorando, self.titulo = [], 0, False

    def handle_starttag(self, tag, attrs):
        if tag in self.IGNORAR:
            self.ignorando += 1
        elif tag in self.TITULO:
            self.partes.append("\n## ")
            self.titulo = True
        elif tag in self.TACHADO:
            self.partes.append("~~")
        elif tag in self.BLOCO:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in self.IGNORAR:
            self.ignorando = max(0, self.ignorando - 1)
        elif tag in self.TITULO:
            self.partes.append("\n")
            self.titulo = False
        elif tag in self.TACHADO:
            self.partes.append("~~")
        elif tag in self.BLOCO:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self.ignorando:
            self.partes.append(re.sub(r"\s+", " ", data))


def ler_html(dados: bytes) -> str:
    p = _HTMLTexto()
    p.feed(_ler_texto(dados))
    linhas = [re.sub(r"\s+", " ", ln).strip() for ln in "".join(p.partes).splitlines()]
    return "\n".join(ln for ln in linhas if ln and ln != "##")


# ---------------------------------------------------------------- DOCX (Word)
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def ler_docx(dados: bytes, caminho: Path | None = None) -> str:
    import io
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        raiz = ET.fromstring(z.read("word/document.xml"))
    linhas = []
    for p in raiz.iter(f"{_W}p"):
        estilo = p.find(f"{_W}pPr/{_W}pStyle")
        estilo = (estilo.get(f"{_W}val") or "").lower() if estilo is not None else ""
        partes = []
        for r in p.iter(f"{_W}r"):
            txt = "".join(t.text or "" for t in r.iter(f"{_W}t"))
            if not txt:
                continue
            rpr = r.find(f"{_W}rPr")
            tachado = rpr is not None and (rpr.find(f"{_W}strike") is not None or rpr.find(f"{_W}dstrike") is not None)
            partes.append(f"~~{txt}~~" if tachado else txt)
        texto = "".join(partes).strip()
        if not texto:
            continue
        if estilo.startswith(("heading", "titulo", "título", "title")):
            linhas.append(f"## {texto}")
        else:
            linhas.append(texto)
    return "\n".join(linhas)


# ---------------------------------------------------------------- PDF
def _paginas_pdf(dados: bytes) -> list[str]:
    try:
        import pymupdf
        with pymupdf.open(stream=dados, filetype="pdf") as d:
            return [pg.get_text() for pg in d]
    except ImportError:
        pass
    try:
        import io
        from pypdf import PdfReader
        return [pg.extract_text() or "" for pg in PdfReader(io.BytesIO(dados)).pages]
    except ImportError as e:
        raise FormatoNaoSuportado("Para ler PDF instale: pip install pymupdf (ou pypdf)") from e


def ler_pdf(dados: bytes) -> str:
    """Normaliza o texto do PDF: tira cabeçalho/rodapé repetido, junta hifenização e linhas quebradas."""
    paginas = [[ln.strip() for ln in p.splitlines()] for p in _paginas_pdf(dados)]
    if len(paginas) >= 3:   # linha que aparece em >= metade das páginas = cabeçalho/rodapé
        freq = Counter(ln for p in paginas for ln in set(p) if ln)
        repetidas = {ln for ln, n in freq.items() if n >= max(2, len(paginas) // 2)}
    else:
        repetidas = set()
    linhas = [ln for p in paginas for ln in p
              if ln and ln not in repetidas and not re.fullmatch(r"(p[áa]g(ina)?\.?\s*)?\d+(\s*(de|/)\s*\d+)?", ln, re.I)]
    saida = []
    for ln in linhas:
        if saida:
            ant = saida[-1]
            if ant.endswith("-") and ln[:1].islower():                    # hifenização "pala-\nvra"
                saida[-1] = ant[:-1] + ln
                continue
            novo_bloco = re.match(r"^(Art\.|§|[IVXLC]+\s*-|[a-z]\)|\d+[.)]\s|##|[-•*]\s)", ln)
            if not novo_bloco and not re.search(r"[.:;!?]$", ant) and ln[:1].islower():
                saida[-1] = ant + " " + ln                               # frase quebrada no meio
                continue
        saida.append(ln)
    return "\n".join(saida)


# ---------------------------------------------------------------- despacho
def ler_arquivo(caminho: Path, dados: bytes | None = None) -> str:
    caminho = Path(caminho)
    ext = caminho.suffix.lower()
    if ext not in EXTENSOES:
        raise FormatoNaoSuportado(f"Formato {ext or '(sem extensão)'} não suportado: {caminho.name}")
    dados = caminho.read_bytes() if dados is None else dados
    if ext == ".txt":
        return _ler_texto(dados)
    if ext in (".md", ".markdown"):
        return ler_markdown(dados)
    if ext in (".html", ".htm"):
        return ler_html(dados)
    if ext == ".docx":
        return ler_docx(dados)
    return ler_pdf(dados)
