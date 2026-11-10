"""Etapa 5 — Geração dos corpus .jsonl.

Os TRÊS corpus pedidos no enunciado (fine-tuning de LLM pequena):
  1. corpus_texto_puro.jsonl          — {"text": ...}: texto limpo e anonimizado de cada documento
                                         (pré-treino continuado / adaptação de domínio)
  2. corpus_conversacional.jsonl      — chat com VÁRIAS trocas (multi-turn): diálogos sobre os
                                         documentos, urgência no meio da conversa, persona e linguagem simples
  3. corpus_perguntas_respostas.jsonl — chat SFT de 1 troca: CONTEXTO + pergunta -> resposta fiel com fonte,
                                         recusas e encaminhamentos (gabarito curado + geração automática)
Apoio:
  4. corpus_referencia.jsonl          — chunks + metadados: a base que o RAG CONSULTA
  5. conjunto_teste.jsonl             — golden set congelado (só gabarito curado), frases diferentes do treino
"""
import random

from .anonimizacao import anonimizar
from .autogeracao import gerar_itens_automaticos
from .busca import BM25, tokenizar
from .curadoria import (DIALOGOS_ESTILO, PEDIDOS_REESCRITA, QA, RECUSAS, REESCRITAS_SIMPLES,
                        SYSTEM_PROMPT, TRECHO_EMERGENCIA)

SEMENTE = 2026
MAX_PALAVRAS_TEXTO_PURO = 600
ABERTURAS = ["oi, tudo bem? ", "bom dia! ", "olá, ", "", "boa tarde, uma dúvida: ", ""]
CONTINUACOES = ["e {q}", "outra dúvida: {q}", "aproveitando, {q}", "{q}"]
FECHAMENTOS = [("obrigado, ajudou muito!", "Que bom que ajudei! Se surgir outra dúvida, é só chamar."),
               ("valeu", "Por nada! Estou aqui se precisar."),
               ("entendi, obrigada", "Disponha! Se quiser, posso explicar outro ponto do documento.")]


class TrechoNaoEncontrado(Exception):
    pass


def _lista(x):
    return [] if x is None else ([x] if isinstance(x, str) else list(x))


def localizar(trecho: str, chunks: list[dict]) -> dict:
    """Fidelidade: o trecho de apoio precisa existir LITERALMENTE em um chunk."""
    for c in chunks:
        if trecho in c["texto"]:
            return c
    raise TrechoNaoEncontrado(f"Trecho sem apoio no corpus: {trecho[:80]}...")


def _fontes(trechos: list[str], chunks: list[dict]) -> list[dict]:
    fontes = []
    for t in trechos:
        c = localizar(t, chunks)
        if c not in fontes:
            fontes.append(c)
    return fontes


def _contexto(chs: list[dict]) -> str:
    return "\n\n".join(f"[{c['chunk_id']}] {c['texto']}" for c in chs)


def _msg(*turnos: str) -> list[dict]:
    papeis = ["user", "assistant"] * len(turnos)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [{"role": p, "content": t} for p, t in zip(papeis, turnos)]


def _anon(t: str) -> str:
    return anonimizar(t)[0]


def _com_fonte(resposta: str, ids: list[str]) -> str:
    if ids and f"[{ids[0]}]" not in resposta:
        return resposta + f" Fonte: [{', '.join(ids)}]"
    return resposta


# ------------------------------------------------------------------ 1. texto puro
def _norm_titulo(s: str) -> str:
    return " ".join(tokenizar(s))



def gerar_texto_puro(docs: list[dict], textos_anon: dict) -> list[dict]:
    regs = []
    for d in docs:
        paragrafos = [p for p in textos_anon[d["doc_id"]].splitlines() if p.strip()]
        partes, atual = [], []
        for p in paragrafos:
            if atual and len(" ".join(atual + [p]).split()) > MAX_PALAVRAS_TEXTO_PURO:
                partes.append(atual)
                atual = []
            atual.append(p.removeprefix("## "))
        if atual:
            partes.append(atual)
        for i, parte in enumerate(partes, 1):
            corpo = "\n".join(parte)
            # o título só entra se o próprio texto não começar com ele (evita duplicar)
            cabeca = "" if _norm_titulo(parte[0]) in _norm_titulo(d["titulo"]) or \
                _norm_titulo(d["titulo"]) in _norm_titulo(parte[0]) else f"{d['titulo']}\n\n"
            regs.append({"text": cabeca + corpo,
                         "meta": {"id": f"{d['doc_id']}#parte{i}", "doc_id": d["doc_id"], "fonte": d["url_fonte"],
                                  "formato_original": d.get("formato"), "origem": d.get("origem"),
                                  "n_palavras": len(" ".join(parte).split())}})
    return regs


# ------------------------------------------------------------------ 4. referência (RAG)
def gerar_referencia(docs: list[dict], chunks_por_doc: dict) -> list[dict]:
    regs = []
    for d in docs:
        for c in chunks_por_doc[d["doc_id"]]:
            regs.append({
                "id": c["chunk_id"], "doc_id": d["doc_id"], "titulo": d["titulo"],
                "tipo_documento": d["tipo"], "formato_original": d.get("formato"), "origem": d.get("origem"),
                "orgao_emissor": d["orgao_emissor"], "url_fonte": d["url_fonte"],
                "data_publicacao": d["data_publicacao"], "data_coleta": d["data_coleta"], "licenca": d["licenca"],
                "ficticio": d["ficticio"], "secao": c["secao"], "artigo": c["artigo"],
                "texto": c["texto"], "n_palavras": len(c["texto"].split()),
                "etiquetas_pii": c["texto"].count("["),
            })
    return regs


# ------------------------------------------------------------------ itens (curados + automáticos)
def preparar_itens(chunks: list[dict], usar_curadoria: bool, automaticos: list[dict]) -> tuple[list[dict], list[str]]:
    """Anexa a cada item suas fontes. Curadoria só entra se os trechos existirem (acervo base carregado)."""
    itens, avisos = [], []
    curados = (QA + RECUSAS) if usar_curadoria else []
    for it in [{**i, "origem": "curado"} for i in curados] + automaticos:
        trechos = _lista(it["trecho"])
        try:
            fontes = _fontes(trechos, chunks)
        except TrechoNaoEncontrado as e:
            if it["origem"] == "curado":
                raise      # o gabarito não pode perder o apoio: dado mudou, a fábrica para
            avisos.append(str(e))
            continue
        if it.get("categoria") == "urgencia":
            assert [c["chunk_id"] for c in fontes] == [TRECHO_EMERGENCIA], it["id"]
        itens.append({**it, "_fontes": fontes, "_trechos": trechos})
    return itens, avisos


# ------------------------------------------------------------------ 3. perguntas e respostas
def gerar_qa(itens: list[dict], chunks: list[dict], bm25: BM25, rng: random.Random) -> list[dict]:
    exemplos = []

    def distrator(excluir: set, pergunta: str) -> dict:
        # o chunk mais parecido que NÃO é a fonte certa: ensina a escolher o trecho
        for i, _ in bm25.ranking(pergunta, k=len(chunks)):
            if chunks[i]["chunk_id"] not in excluir:
                return chunks[i]
        return rng.choice(chunks)

    for item in itens:
        fontes, ids = item["_fontes"], [c["chunk_id"] for c in item["_fontes"]]
        for pergunta in item["treino"]:
            if fontes:
                ctx = fontes + [distrator(set(ids), pergunta)]
            else:   # a busca SEMPRE devolve algo; quem recusa é o gerador (Aula 22)
                ctx = [chunks[i] for i, _ in bm25.ranking(pergunta, k=2)]
            rng.shuffle(ctx)
            exemplos.append({
                "messages": _msg(f"CONTEXTO:\n{_contexto(ctx)}\n\nPERGUNTA: {_anon(pergunta)}",
                                 _com_fonte(item["resposta"], ids)),
                "meta": {"item": item["id"], "origem": item["origem"], "categoria": item.get("categoria", "factual"),
                         "comportamento": item.get("comportamento", "responder"),
                         "fontes": ids, "trechos_apoio": item["_trechos"]},
            })
    rng.shuffle(exemplos)
    return exemplos


# ------------------------------------------------------------------ 2. conversacional (multi-turn)
def _dialogo(itens_factuais: list[dict], bm25: BM25, chunks: list[dict], rng: random.Random, extra=None) -> dict:
    """2 perguntas factuais (+ opcional turno de urgência/recusa) + fechamento, numa só conversa.
    O CONTEXTO recuperado vai no 1º turno (com as fontes de todas as perguntas e um distrator)."""
    fontes = []
    for it in itens_factuais + ([extra] if extra else []):
        fontes += [c for c in it["_fontes"] if c not in fontes]
    ids = [c["chunk_id"] for c in fontes]
    q1 = _anon(rng.choice(itens_factuais[0]["treino"]))
    dist = next((chunks[i] for i, _ in bm25.ranking(q1, k=len(chunks)) if chunks[i]["chunk_id"] not in ids), None)
    ctx = fontes + ([dist] if dist else [])
    rng.shuffle(ctx)
    turnos = [f"CONTEXTO:\n{_contexto(ctx)}\n\nPERGUNTA: {rng.choice(ABERTURAS)}{q1}",
              _com_fonte(itens_factuais[0]["resposta"], [c["chunk_id"] for c in itens_factuais[0]["_fontes"]])]
    for it in itens_factuais[1:]:
        q = _anon(rng.choice(it["treino"]))
        turnos += [rng.choice(CONTINUACOES).format(q=q[0].lower() + q[1:]),
                   _com_fonte(it["resposta"], [c["chunk_id"] for c in it["_fontes"]])]
    tipo = "documento"
    if extra:
        turnos += [_anon(rng.choice(extra["treino"])), _com_fonte(extra["resposta"], [c["chunk_id"] for c in extra["_fontes"]])]
        tipo = extra.get("categoria", "recusa")
    else:
        turnos += list(rng.choice(FECHAMENTOS))
    trechos = [t for it in itens_factuais + ([extra] if extra else []) for t in it["_trechos"]]
    return {"messages": _msg(*turnos),
            "meta": {"tipo_dialogo": tipo, "n_turnos_usuario": len(turnos) // 2,
                     "itens": [it["id"] for it in itens_factuais] + ([extra["id"]] if extra else []),
                     "fontes": ids, "trechos_apoio": trechos}}


def gerar_conversacional(itens: list[dict], chunks: list[dict], bm25: BM25, rng: random.Random) -> list[dict]:
    exemplos = []
    factuais = [i for i in itens if i.get("comportamento", "responder") == "responder" and i["_fontes"]]
    # (a) diálogos sobre cada documento: perguntas do mesmo documento, de 2 em 2
    por_doc = {}
    for it in factuais:
        por_doc.setdefault(it["_fontes"][0]["chunk_id"].split("#")[0], []).append(it)
    for doc_id, lst in por_doc.items():
        lst = lst[:]
        rng.shuffle(lst)
        for k in range(0, len(lst) - 1, 2):
            exemplos.append(_dialogo(lst[k:k + 2], bm25, chunks, rng))
    # (b) urgência ou recusa NO MEIO da conversa (o modelo não pode "embalar" no assunto anterior)
    especiais = [i for i in itens if i.get("comportamento", "responder") != "responder"]
    for k, esp in enumerate(especiais):
        base = factuais[(k * 7) % len(factuais)] if factuais else None
        if base:
            exemplos.append(_dialogo([base], bm25, chunks, rng, extra=esp))
    # (c) persona e linguagem simples (1 troca)
    for trecho, simples in REESCRITAS_SIMPLES:
        try:
            c = localizar(trecho, chunks)
        except TrechoNaoEncontrado:
            continue
        for tpl in PEDIDOS_REESCRITA:
            # o trecho chega rotulado com o id, como viria da busca: o modelo só cita o que recebeu
            user = f"CONTEXTO:\n[{c['chunk_id']}] {trecho}\n\nPERGUNTA: {tpl.format(t=trecho)}"
            exemplos.append({"messages": _msg(user, f"{simples} Fonte: [{c['chunk_id']}]"),
                             "meta": {"tipo_dialogo": "linguagem_simples", "n_turnos_usuario": 1,
                                      "fontes": [c["chunk_id"]], "trechos_apoio": [trecho]}})
    for user, asst in DIALOGOS_ESTILO:
        exemplos.append({"messages": _msg(user, asst),
                         "meta": {"tipo_dialogo": "tom_e_persona", "n_turnos_usuario": 1, "fontes": [], "trechos_apoio": []}})
    rng.shuffle(exemplos)
    return exemplos


# ------------------------------------------------------------------ 5. conjunto de teste
def gerar_teste(chunks: list[dict], usar_curadoria: bool) -> list[dict]:
    teste = []
    for item in (QA + RECUSAS) if usar_curadoria else []:
        trechos = _lista(item["trecho"])
        fontes = _fontes(trechos, chunks)
        pergunta = _anon(item["teste"])
        teste.append({
            "id": f"teste_{item['id']}",
            "pergunta": pergunta,
            "categoria": item.get("categoria", "factual"),
            "comportamento_esperado": item.get("comportamento", "responder"),
            "fontes_esperadas": [c["chunk_id"] for c in fontes],
            "trechos_apoio": trechos,
            "resposta_referencia": item["resposta"],
            # versão "oráculo" (contexto certo já recuperado) para avaliar só o gerador / LoRA
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": (f"CONTEXTO:\n{_contexto(fontes)}\n\n" if fontes else "")
                          + f"PERGUNTA: {pergunta}"}],
        })
    return teste


def jaccard(a: str, b: str) -> float:
    A, B = set(tokenizar(a)), set(tokenizar(b))
    return len(A & B) / max(len(A | B), 1)


def perguntas_de_treino(corpus: dict) -> list[str]:
    """Todas as perguntas que o modelo vê no treino (Q&A e todos os turnos do conversacional)."""
    out = []
    for nome in ("corpus_perguntas_respostas", "corpus_conversacional"):
        for e in corpus[nome]:
            for m in e["messages"]:
                if m["role"] == "user":
                    out.append(m["content"].split("PERGUNTA:")[-1])
    return out


def checar_vazamento(corpus: dict) -> tuple[float, str, str]:
    """Maior semelhança (Jaccard) entre uma pergunta de teste e qualquer pergunta de treino."""
    treino = perguntas_de_treino(corpus)
    return max(((jaccard(t["pergunta"], p), t["pergunta"], p) for t in corpus["conjunto_teste"] for p in treino),
               default=(0.0, "", ""))


def gerar_tudo(docs, chunks_por_doc, textos_anon, usar_curadoria=True):
    rng = random.Random(SEMENTE)
    todos = [c for d in docs for c in chunks_por_doc[d["doc_id"]]]
    bm25 = BM25([c["texto"] for c in todos])
    automaticos = gerar_itens_automaticos(docs, chunks_por_doc)
    itens, avisos = preparar_itens(todos, usar_curadoria, automaticos)
    corpus = {
        "corpus_texto_puro": gerar_texto_puro(docs, textos_anon),
        "corpus_conversacional": gerar_conversacional(itens, todos, bm25, rng),
        "corpus_perguntas_respostas": gerar_qa(itens, todos, bm25, rng),
        "corpus_referencia": gerar_referencia(docs, chunks_por_doc),
        "conjunto_teste": gerar_teste(todos, usar_curadoria),
    }
    return corpus, avisos
