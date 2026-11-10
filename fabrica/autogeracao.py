"""Etapa 5a — Geração AUTOMÁTICA de pares pergunta -> resposta para QUALQUER documento enviado.

Sem LLM e sem API: regras sobre a estrutura do texto já limpo e anonimizado. Toda resposta é
EXTRATIVA (copia linhas literais do chunk), então a fidelidade é garantida por construção e
conferida de novo pela auditoria. Regras:

  R1 caput de artigo ............ "O que diz o Art. 5º do Decreto X?"
  R2 lista ("São direitos...:") . "Quais são os direitos básicos do usuário?"
  R3 definição ("I - termo: ...") "O que é dado pessoal, segundo a LGPD?"
  R4 prazo (número + dias/anos) . "Qual é o prazo previsto no Art. 3º do Decreto X?"
  R5 seção com título ........... título em forma de pergunta (FAQ) ou "O que ... diz sobre <título>?"
  R6 parágrafo sem estrutura .... "O que <documento> diz sobre <palavras-chave>?"

Cada item tem 3 formas de pergunta (formal, alternativa e informal sem acento, como no WhatsApp).
O gabarito curado à mão (curadoria.py) continua sendo a referência de qualidade e o conjunto de teste.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass

from .busca import STOP, _sem_acento

FEMININO = {"lei", "cartilha", "pagina", "resolucao", "portaria", "instrucao", "norma", "politica", "carta",
            "medida", "lgpd", "lai", "constituicao", "orientacao", "nota", "tarifa", "agenda", "campanha"}
ROTULO_TIPO = {"cartilha": "cartilha", "pagina_web": "página", "faq": "guia de perguntas frequentes",
               "documento": "documento", "guia": "guia"}
RE_ITEM = re.compile(r"^(?:[IVXLC]+|[a-z]|\d+)\s*[-–)]\s*")
RE_DEFINICAO = re.compile(r"^[IVXLC]+\s*-\s*([a-zà-ú][^:;]{1,60}?)\s*(?::|\s-\s)\s*(.{10,})$")
RE_PRAZO = re.compile(r"\b(\d+|um|uma|dois|duas|três|cinco|dez|quinze|vinte|trinta|sessenta|noventa)\b"
                      r"[^.;]{0,25}\b(dias?|horas?|anos?|meses|mês|semanas?)\b", re.I)
MAX_PALAVRAS_RESPOSTA = 90


@dataclass
class Ref:
    nome: str
    feminino: bool

    @property
    def o(self):    # "a Lei de Acesso à Informação" / "o Decreto ..."
        return ("a " if self.feminino else "o ") + self.nome

    @property
    def do(self):   # "da Lei ..." / "do Decreto ..."
        return ("da " if self.feminino else "do ") + self.nome


def _fem(palavra: str) -> bool:
    return _sem_acento(palavra.lower()) in FEMININO


def referencia(doc: dict) -> Ref:
    t = re.sub(r"\s*\((?:DOCUMENTO-TESTE )?FICTÍCI[OA]\)", "", doc["titulo"], flags=re.I).strip()
    t = re.sub(r",?\s*texto compilado", "", t, flags=re.I).replace("()", "").strip()
    if "—" in t:
        a, b = [x.strip() for x in t.split("—", 1)]
        # lei federal: o nome popular (depois do travessão) é o que o cidadão usa
        t = b if doc["tipo"].startswith("lei") and "municipal" not in doc["tipo"] else a
    t = re.sub(r"\s*\(\s*\)", "", t).strip()[:80]
    rotulo = next((v for k, v in ROTULO_TIPO.items() if doc["tipo"].startswith(k)), None)
    primeira = t.split()[0] if t else "documento"
    if rotulo and _sem_acento(primeira.lower()) != _sem_acento(rotulo.split()[0].lower()):
        return Ref(f"{rotulo} \"{t}\"", _fem(rotulo.split()[0]))
    return Ref(t, _fem(primeira))


def _artigo(art: str) -> str:
    """'Art. 5' -> 'Art. 5º' (ordinal até o 9º, como na redação legal)."""
    m = re.match(r"Art\.\s*(\d+)$", art)
    return f"Art. {m.group(1)}º" if m and int(m.group(1)) <= 9 else art


def _informal(q: str) -> str:
    q = _sem_acento(q.lower()).rstrip("?.")
    return q.replace("qual e ", "qual ").replace("o que e ", "oq e ")


def _corpo_artigo(linha: str) -> str:
    return re.sub(r"^Art\.\s*\d+(?:-[A-Z])?\s*[º.]?\s*", "", linha).strip()


def _limitar(linhas: list[str]) -> list[str]:
    out, n = [], 0
    for ln in linhas:
        n += len(ln.split())
        if out and n > MAX_PALAVRAS_RESPOSTA:
            break
        out.append(ln)
    return out


def _tem_pii(texto: str) -> bool:
    return bool(re.search(r"\[(?:NOME|CPF|RG|TELEFONE|EMAIL|ENDERECO|CARTAO_SUS|PROTOCOLO|MATRICULA|PLACA)\]", texto))


def _item(doc_id, chunk, regra, perguntas, trechos, resposta):
    return {"id": f"auto_{chunk['chunk_id']}_{regra}", "doc_id": doc_id, "origem": "automatico", "regra": regra,
            "categoria": "factual", "comportamento": "responder", "trecho": trechos,
            "resposta": resposta, "treino": perguntas}


def _regras_artigo(doc, chunk, ref: Ref):
    itens, linhas = [], chunk["texto"].splitlines()
    art = _artigo(chunk["artigo"])
    ra = f"{art} {ref.do}"                     # "Art. 49 do Código de Defesa do Consumidor"
    primeira_parte = not re.search(r"\.\d+$", chunk["chunk_id"]) or chunk["chunk_id"].endswith(".1")
    caput = _corpo_artigo(linhas[0])
    # R2 lista
    if linhas[0].rstrip().endswith(":") and primeira_parte and not re.search(r"considera(?:m)?-se", caput):
        itens_lista = [ln for ln in linhas[1:] if RE_ITEM.match(ln)]
        if len(itens_lista) >= 2:
            sel = _limitar([linhas[0]] + itens_lista)
            m = re.match(r"^São (.+):$", caput)
            if m:
                pergs = [f"Quais são os {m.group(1)}, segundo {ref.o}?", f"Quais são os {m.group(1)}?"]
            else:
                pergs = [f"O que está listado no {ra}?", f"Quais são os pontos do {ra}?"]
            pergs.append(_informal(pergs[0]))
            corpo = "\n".join(f"- {RE_ITEM.sub('', ln)}" for ln in sel[1:])
            mais = " (entre outros itens do artigo)" if len(sel) - 1 < len(itens_lista) else ""
            itens.append(_item(doc["doc_id"], chunk, "R2_lista", pergs, sel,
                               f"Segundo o {ra}{mais}, {caput[0].lower() + caput[1:]}\n{corpo}"))
    # R1 caput
    if primeira_parte and len(caput.split()) >= 6 and not caput.endswith(":"):
        pergs = [f"O que diz o {ra}?", f"Me explica o que determina o {ra}.", _informal(f"o que diz o {ra}?")]
        itens.append(_item(doc["doc_id"], chunk, "R1_caput", pergs, [linhas[0]], f"O {ra} determina: \"{caput}\""))
    # R3 definições
    if re.search(r"considera(?:m)?-se", chunk["texto"]):
        for ln in linhas[1:]:
            m = RE_DEFINICAO.match(ln)
            if m:
                termo = m.group(1).strip()
                definicao = re.sub(r"[;.]\s*(?:e|ou)?\s*$", "", m.group(2).strip())
                pergs = [f"O que é {termo}, segundo {ref.o}?", f"O que significa \"{termo}\"?",
                         _informal(f"o que é {termo}?")]
                regra = "R3_def_" + re.sub(r"\W+", "_", _sem_acento(termo))[:24]
                itens.append(_item(doc["doc_id"], chunk, regra, pergs, [ln],
                                   f"Segundo o {ra}, {termo} é: {definicao}."))
    # R4 prazo (uma por chunk)
    for ln in linhas:
        if RE_PRAZO.search(ln) and "prazo" in ln.lower():
            pergs = [f"Qual é o prazo previsto no {ra}?", f"Quanto tempo o {ra} estabelece?",
                     _informal(f"qual o prazo do {ra}?")]
            itens.append(_item(doc["doc_id"], chunk, "R4_prazo", pergs, [ln], f"O {ra} diz: \"{_corpo_artigo(ln)}\""))
            break
    return itens


def _regra_secao(doc, chunk, ref: Ref):
    linhas = chunk["texto"].splitlines()
    titulo, corpo = linhas[0].strip(), [ln for ln in linhas[1:] if ln.strip()]
    if not corpo or sum(len(ln.split()) for ln in corpo) < 10 or _tem_pii(chunk["texto"]):
        return []
    sel = _limitar(corpo)
    if titulo.endswith("?"):
        pergs = [titulo, f"{titulo[:-1]}, de acordo com {ref.o}?", _informal(titulo)]
    else:
        assunto = titulo[0].lower() + titulo[1:]
        pergs = [f"O que {ref.o} diz sobre {assunto}?", f"Como funciona: {assunto}?",
                 _informal(f"me fala sobre {assunto}")]
    resposta = f"De acordo com {ref.o} (seção \"{titulo}\"): " + " ".join(sel)
    return [_item(doc["doc_id"], chunk, "R5_secao", pergs, sel, resposta)]


def _palavras_chave(texto: str, df: Counter, n_docs: int, k: int = 2) -> list[str]:
    palavras = [w for w in re.findall(r"[a-zà-ú]{5,}", texto.lower()) if _sem_acento(w) not in STOP]
    tf = Counter(palavras)
    nota = {w: c * math.log(1 + n_docs / (1 + df[_sem_acento(w)[:6]])) for w, c in tf.items()}
    return [w for w, _ in sorted(nota.items(), key=lambda x: -x[1])[:k]]


def _regra_paragrafo(doc, chunk, ref: Ref, df, n_docs):
    if _tem_pii(chunk["texto"]):
        return []
    linhas = [ln for ln in chunk["texto"].splitlines() if len(ln.split()) >= 6]
    if not linhas:
        return []
    sel = _limitar(linhas)
    kw = _palavras_chave(" ".join(sel), df, n_docs)
    if len(kw) < 2:
        return []
    pergs = [f"O que {ref.o} diz sobre {kw[0]} e {kw[1]}?", f"Fale sobre {kw[0]} segundo {ref.o}.",
             _informal(f"o que fala sobre {kw[0]}?")]
    return [_item(doc["doc_id"], chunk, "R6_paragrafo", pergs, sel, f"De acordo com {ref.o}: " + " ".join(sel))]


def gerar_itens_automaticos(docs: list[dict], chunks_por_doc: dict) -> list[dict]:
    todos = [c for d in docs for c in chunks_por_doc[d["doc_id"]]]
    df = Counter(t for c in todos for t in {_sem_acento(w)[:6] for w in re.findall(r"[a-zà-ú]{5,}", c["texto"].lower())})
    itens = []
    for d in docs:
        ref = referencia(d)
        for c in chunks_por_doc[d["doc_id"]]:
            parte = c["chunk_id"].split("#")[1]
            if c.get("artigo") and c["artigo"].startswith("Art."):
                itens += _regras_artigo(d, c, ref)
            elif parte.startswith("sec"):
                itens += _regra_secao(d, c, ref)
            elif parte.startswith("p"):
                itens += _regra_paragrafo(d, c, ref, df, len(todos))
    vistos = set()
    for it in itens:   # ids únicos (a mesma regra pode disparar em chunks irmãos)
        base, k = it["id"], 1
        while it["id"] in vistos:
            k += 1
            it["id"] = f"{base}_{k}"
        vistos.add(it["id"])
    return itens
