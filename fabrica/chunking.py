"""Etapa 4 — Chunking estrutural (semântico pela estrutura do documento).

Leis: um chunk por artigo ("Art. Nº ..." até o próximo artigo). Artigos longos
(> MAX_PALAVRAS) são divididos em partes por incisos/parágrafos, e cada parte
repete o caput — a "sobreposição" que preserva o sentido (como na Aula 19).
Guias/cartilhas: um chunk por seção ("## Título").
Cabeçalhos de capítulo/seção não entram no texto: viram o metadado `secao`.
"""
import re

MAX_PALAVRAS = 170
RE_ARTIGO = re.compile(r"^Art\.\s*(\d+(?:-[A-Z])?)\s*[º.]?\s")
RE_TITULO_ESTRUTURA = re.compile(r"^(CAPÍTULO|TÍTULO|SEÇÃO|Seção)\s+[IVXLC\d]+", re.I)
RE_EMENTA = re.compile(r"^(Dispõe|Regula|Lei Geral)")


def _palavras(t: str) -> int:
    return len(t.split())


def _dividir_artigo(linhas: list[str]) -> list[str]:
    texto = "\n".join(linhas)
    if _palavras(texto) <= MAX_PALAVRAS:
        return [texto]
    caput, resto = linhas[0], linhas[1:]
    partes, atual = [], []
    for ln in resto:
        if atual and _palavras("\n".join([caput] + atual + [ln])) > MAX_PALAVRAS:
            partes.append("\n".join([caput] + atual))
            atual = []
        atual.append(ln)
    if atual:
        partes.append("\n".join([caput] + atual))
    return partes


def chunk_lei(doc_id: str, texto: str) -> list[dict]:
    chunks, secao, pendente_titulo = [], "", False
    art_num, art_linhas = None, []

    def fechar():
        if art_num is None:
            return
        partes = _dividir_artigo(art_linhas)
        for i, p in enumerate(partes, 1):
            sufixo = f".{i}" if len(partes) > 1 else ""
            chunks.append({"chunk_id": f"{doc_id}#art{art_num}{sufixo}",
                           "artigo": f"Art. {art_num}", "secao": art_secao, "texto": p})

    art_secao = ""
    for ln in texto.splitlines():
        if RE_EMENTA.match(ln) and art_num is None:
            chunks.append({"chunk_id": f"{doc_id}#ementa", "artigo": "ementa", "secao": "", "texto": ln})
            continue
        if RE_TITULO_ESTRUTURA.match(ln):
            secao, pendente_titulo = ln, True
            continue
        if pendente_titulo and not RE_ARTIGO.match(ln):
            secao = f"{secao} — {ln}"
            pendente_titulo = False
            continue
        pendente_titulo = False
        m = RE_ARTIGO.match(ln)
        if m:
            fechar()
            art_num, art_linhas, art_secao = m.group(1), [ln], secao
        elif art_num is not None:
            art_linhas.append(ln)
        # linhas antes do 1º artigo (título da lei, fórmula de promulgação) são descartadas
    fechar()
    return chunks


def chunk_guia(doc_id: str, texto: str) -> list[dict]:
    chunks, titulo, linhas, n = [], None, [], 0

    def fechar():
        nonlocal n
        if titulo and linhas:
            n += 1
            chunks.append({"chunk_id": f"{doc_id}#sec{n}", "artigo": None, "secao": titulo,
                           "texto": f"{titulo}\n" + "\n".join(linhas)})

    for ln in texto.splitlines():
        if ln.startswith("## "):
            fechar()
            titulo, linhas = ln[3:].strip(), []
        elif titulo:
            linhas.append(ln)
    fechar()
    return chunks


def chunk_paragrafos(doc_id: str, texto: str, alvo: int = 140) -> list[dict]:
    """Documentos sem estrutura (PDF/DOCX sem títulos): junta parágrafos até ~`alvo` palavras,
    sem cortar parágrafo no meio; o último parágrafo de um chunk é repetido no seguinte
    (sobreposição) quando é curto, para preservar o contexto."""
    paragrafos = [p for p in texto.splitlines() if p.strip()]
    chunks, atual, n = [], [], 0
    def fechar():
        nonlocal n
        n += 1
        chunks.append({"chunk_id": f"{doc_id}#p{n}", "artigo": None, "secao": "", "texto": "\n".join(atual)})

    for p in paragrafos:
        if atual and _palavras("\n".join(atual + [p])) > alvo:
            fechar()
            atual = [atual[-1]] if _palavras(atual[-1]) <= 40 else []
        atual.append(p)
    if atual:
        fechar()
    return chunks


def fazer_chunks(doc: dict, texto: str) -> list[dict]:
    if doc["tipo"].startswith("lei"):
        return chunk_lei(doc["doc_id"], texto)
    if re.search(r"^## ", texto, re.M):
        return chunk_guia(doc["doc_id"], texto)
    return chunk_paragrafos(doc["doc_id"], texto)
