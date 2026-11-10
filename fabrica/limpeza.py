"""Etapa 2 — Limpeza: remove ruído de coleta sem alterar o conteúdo normativo.

Regras (cada uma é contada para o relatório):
  - trechos revogados (marcados com ~~...~~ na coleta, vindos de <strike> no HTML);
  - bloco final de assinaturas e aviso do DOU (a partir de "Brasília, ...");
  - linhas de navegação do site (Vigência, Regulamento, Mensagem de veto, (Vide ...));
  - anotações de alteração legislativa ((Incluído pela...), (Redação dada pela...));
  - incisos vetados, marcadores de página e rodapés;
  - normalização Unicode (NFC), espaços, travessões e o símbolo "°" usado como "º".
"""
import re
import unicodedata
from collections import Counter

RE_REVOGADO = re.compile(r"~~.*?~~", re.S)
RE_ASSINATURAS = re.compile(r"^\s*Brasília\s*,", re.M)
RE_ANOTACAO = re.compile(
    r"\s*\((?:Incluíd[oa]|Redação dada|Vide|Revogad[oa]|Renumerad[oa]|Vigência)[^)]*\)", re.I
)
RE_VIGENCIA_FIM = re.compile(r"\s+Vigência\s*$")
RE_LINHA_RUIDO = re.compile(
    r"^(?:Presidência da República|Casa Civil|Secretaria-Geral|Subchefia para Assuntos Jurídicos"
    r"|Vigência|Regulamento(?:\s+Vigência)?|Mensagem de veto|\*|Página \d+ de \d+"
    r"|Prefeitura Municipal de .*documento sem valor legal)$",
    re.I,
)
RE_VETADO = re.compile(r"^[IVXLC]+\s*-\s*\(Vetado\)[.;]?$", re.I)


def limpar(texto: str, lei: bool = True) -> tuple[str, Counter]:
    """Limpa um texto bruto. Devolve (texto_limpo, contagem_de_remocoes).
    `lei=False` (documentos genéricos) não corta o bloco de assinaturas "Brasília, ..."."""
    stats = Counter()
    t = unicodedata.normalize("NFC", texto).replace(" ", " ")
    t = t.replace("–", "-")
    t = re.sub("[\u200b\u200c\u200d\ufeff\u00ad]", "", t)                 # largura zero / hífen suave
    t = re.sub("[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", t)                    # caracteres de controle
    t = t.translate(str.maketrans({"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'"}))
    t = re.sub(r"[\u2022\u25cf\u25aa]\s*", "- ", t)                          # marcadores -> "- "

    stats["trechos_revogados"] = len(RE_REVOGADO.findall(t))
    t = RE_REVOGADO.sub("", t)

    m = RE_ASSINATURAS.search(t) if lei else None
    if m:
        stats["linhas_assinatura_removidas"] = t[m.start():].strip().count("\n") + 1
        t = t[: m.start()]

    linhas = []
    for linha in t.splitlines():
        n_anot = len(RE_ANOTACAO.findall(linha))
        stats["anotacoes_legislativas"] += n_anot
        linha = RE_ANOTACAO.sub("", linha)
        linha = RE_VIGENCIA_FIM.sub("", linha)
        linha = re.sub(r"\s+", " ", linha).strip()
        linha = re.sub(r"\s+([.,;:])", r"\1", linha)          # "Federal ." -> "Federal."
        linha = re.sub(r"(\d)\s?°", r"\1º", linha)             # "§ 1°" -> "§ 1º"
        if not linha:
            continue
        if RE_LINHA_RUIDO.match(linha):
            stats["linhas_ruido_site"] += 1
            continue
        if RE_VETADO.match(linha):
            stats["incisos_vetados"] += 1
            continue
        linhas.append(linha)
    return "\n".join(linhas), stats
