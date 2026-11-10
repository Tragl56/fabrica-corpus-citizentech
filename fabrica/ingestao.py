"""Etapa 1 — Ingestão: acervo base (dados/metadados.json) + documentos enviados pelo usuário.

Qualquer arquivo suportado (.txt, .md, .html, .docx, .pdf) colocado numa pasta de entrada
vira um documento. Os metadados são inferidos (título, tipo, data de coleta) e podem ser
sobrescritos por um arquivo ao lado com o mesmo nome + ".meta.json".
"""
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

from .leitores import EXTENSOES, FormatoNaoSuportado, ler_arquivo

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
EXEMPLOS_UPLOAD = DADOS / "exemplos_upload"
SAIDA = RAIZ / "saida"


def _slug(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:40] or "doc"


def carregar_acervo_base(pasta_dados: Path = DADOS) -> list[dict]:
    metadados = json.loads((pasta_dados / "metadados.json").read_text(encoding="utf-8"))
    docs = []
    for meta in metadados:
        caminho = pasta_dados / meta["arquivo"]
        docs.append({**meta, "formato": caminho.suffix.lower().lstrip("."), "origem": "acervo_base",
                     "texto_bruto": ler_arquivo(caminho)})
    return docs


def inferir_tipo(texto: str) -> str:
    n_art = len(re.findall(r"^\s*Art\.\s*\d+", texto, re.M))
    return "lei" if n_art >= 3 else "documento"


def inferir_titulo(texto: str, nome: str) -> str:
    for ln in texto.splitlines():
        ln = ln.strip().lstrip("#").strip()
        if 6 <= len(ln) <= 160 and not ln.startswith("~~"):
            return ln
    return Path(nome).stem.replace("_", " ")


def documento_de_upload(caminho: Path, dados: bytes | None = None, meta_extra: dict | None = None) -> dict:
    caminho = Path(caminho)
    texto = ler_arquivo(caminho, dados)
    meta_extra = dict(meta_extra or {})
    lateral = caminho.with_name(caminho.name + ".meta.json")
    if dados is None and lateral.exists():
        meta_extra = {**json.loads(lateral.read_text(encoding="utf-8")), **meta_extra}
    tipo = meta_extra.pop("tipo", None) or inferir_tipo(texto)
    return {
        "doc_id": meta_extra.pop("doc_id", None) or _slug(caminho.stem),
        "arquivo": caminho.name,
        "titulo": meta_extra.pop("titulo", None) or inferir_titulo(texto, caminho.name),
        "tipo": tipo,
        "orgao_emissor": meta_extra.pop("orgao_emissor", "não informado"),
        "url_fonte": meta_extra.pop("url_fonte", f"upload:{caminho.name}"),
        "data_publicacao": meta_extra.pop("data_publicacao", None),
        "data_coleta": meta_extra.pop("data_coleta", dt.date.today().isoformat()),
        "licenca": meta_extra.pop("licenca", "informada pelo usuário no envio"),
        "ficticio": bool(meta_extra.pop("ficticio", False)),
        **meta_extra,
        "formato": caminho.suffix.lower().lstrip("."),
        "origem": "upload",
        "texto_bruto": texto,
    }


def carregar_uploads(pasta: Path) -> tuple[list[dict], list[str]]:
    docs, avisos = [], []
    for caminho in sorted(Path(pasta).iterdir()):
        if caminho.name.endswith(".meta.json") or caminho.is_dir():
            continue
        if caminho.suffix.lower() not in EXTENSOES:
            avisos.append(f"ignorado (formato não suportado): {caminho.name}")
            continue
        try:
            docs.append(documento_de_upload(caminho))
        except (FormatoNaoSuportado, KeyError, ValueError) as e:
            avisos.append(f"erro ao ler {caminho.name}: {e}")
    return docs, avisos


def carregar_documentos(entradas: list[Path] | None = None, incluir_base: bool = True) -> tuple[list[dict], list[str]]:
    """Acervo base (opcional) + todos os arquivos das pastas de entrada. Garante doc_id único."""
    docs = carregar_acervo_base() if incluir_base else []
    avisos = []
    for pasta in entradas if entradas is not None else [EXEMPLOS_UPLOAD]:
        novos, av = carregar_uploads(pasta)
        docs += novos
        avisos += av
    vistos = {}
    for d in docs:
        base = d["doc_id"]
        vistos[base] = vistos.get(base, 0) + 1
        if vistos[base] > 1:
            d["doc_id"] = f"{base}_{vistos[base]}"
    return docs, avisos
