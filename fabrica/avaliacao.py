"""Etapa 7 — Avaliação no conjunto de teste (Aula 22), sem modelo de linguagem.

Sistema: regra dura de urgência -> regras de recusa -> busca -> limiar de "não sei".
Comparamos duas buscas:
  1. BM25 por palavras (linha de base)
  2. Busca híbrida: expansão de consulta + n-gramas de caracteres, fundidos por RRF
Toda escolha (variante de busca, sinônimos, limiar) é feita no TREINO ("dev"); o teste fica
congelado e só é medido no fim. Métricas: hit@1, hit@3, MRR; acurácia de comportamento;
urgências encaminhadas; recusa correta.
"""
import re
import unicodedata

from .busca import BM25, SINONIMOS, BuscaHibrida, _sem_acento
from .curadoria import QA, RECUSAS
from .geracao import _lista


def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


URGENCIA = [r"desmai", r"nao acorda", r"dor forte", r"falta de ar", r"sangr", r"socorro", r"fogo",
            r"incendio", r"fumaca", r"afog", r"enchente", r"agua .*subindo", r"desliz", r"barranco",
            r"\blama\b", r"rachad", r"arromb", r"assalt", r"tiro", r"faca", r"me bateu", r"agred", r"apanh",
            r"ameac", r"se matar", r"acabar com tudo", r"suicid", r"nao vale mais a pena", r"nao acordar",
            r"maltrat", r"sem comida", r"boca torta", r"nao consegue mexer"]
RECUSA = {
    "encaminhar": [r"process", r"causa ganha", r"peticao", r"justica contra", r"advogad", r"analisa meu contrato"],
    "recusar": [r"cpf d[oa] ", r"endereco d[aoe]", r"onde mora", r"telefone d[aoe]", r"\[cpf\]", r"\[nome\]",
                r" rg\b", r"meu endereco", r"votar", r"candidat", r"partido", r"governo atual",
                r"receita de", r"jogo de", r"piada", r"melhor celular", r"furar a fila", r"falso",
                r"cpf de outra", r"atestado .*sem ir"],
}


class MotorBM25:
    """Adapta o BM25 puro à mesma interface da BuscaHibrida."""
    def __init__(self, docs):
        self.bm25 = BM25(docs)

    def ranking(self, q, k=5):
        return self.bm25.ranking(q, k)

    def confianca(self, q):
        return self.bm25.ranking(q, 1)[0][1]


def classificar(pergunta: str, motor, limiar: float) -> str:
    p = _norm(pergunta)
    if any(re.search(rx, p) for rx in URGENCIA):
        return "encaminhar_urgencia"
    for comp, rxs in RECUSA.items():
        if any(re.search(rx, p) for rx in rxs):
            return comp
    return "recusar" if motor.confianca(pergunta) < limiar else "responder"


def calibrar_limiar(motor) -> float:
    """Ponto médio entre o 10º percentil das respondíveis e o máximo das 'sem base' (TREINO)."""
    resp = sorted(motor.confianca(p) for it in QA for p in it["treino"])
    sem_base = [motor.confianca(p) for it in RECUSAS if it["id"] == "rec_sem_base" for p in it["treino"]]
    p10 = resp[max(0, len(resp) // 10 - 1)]
    return round((p10 + max(sem_base)) / 2, 3)


def checar_sinonimos(teste: list[dict]) -> list[str]:
    """Chaves do dicionário de expansão que aparecem no TESTE mas em nenhuma pergunta de treino.
    Deve ser vazio: um sinônimo assim teria sido "aprendido" olhando o teste (vazamento)."""
    def casa(k, qs):
        return any(re.search(rf"\b{k}", q) for q in qs)
    treino = [_sem_acento(p.lower()) for it in QA + RECUSAS for p in it["treino"]]
    tst = [_sem_acento(t["pergunta"].lower()) for t in teste]
    return [k for k in SINONIMOS if casa(k, tst) and not casa(k, treino)]


def _conjunto_dev(corpus_referencia):
    """Perguntas de TREINO em formato de teste (para escolher a variante sem tocar no teste)."""
    dev = []
    for it in QA + RECUSAS:
        fontes = []
        for t in _lista(it["trecho"]):
            fontes += [r["id"] for r in corpus_referencia if t in r["texto"]][:1]
        for p in it["treino"]:
            dev.append({"id": it["id"], "pergunta": p, "fontes_esperadas": fontes,
                        "comportamento_esperado": it.get("comportamento", "responder")})
    return dev


def _medir(motor, ids, limiar, conjunto):
    hits1 = hits3 = rr = n_fact = acertos = 0
    urg_total = urg_ok = rec_total = rec_ok = 0
    erros = []
    for t in conjunto:
        esperado = t["comportamento_esperado"]
        if esperado == "responder":
            n_fact += 1
            rank_ids = [ids[i] for i, _ in motor.ranking(t["pergunta"], k=10)]
            pos = next((k for k, cid in enumerate(rank_ids, 1) if cid in t["fontes_esperadas"]), None)
            hits1 += pos == 1
            hits3 += pos is not None and pos <= 3
            rr += 1 / pos if pos else 0
        previsto = classificar(t["pergunta"], motor, limiar)
        ok = previsto == esperado or (esperado in ("recusar", "encaminhar") and previsto in ("recusar", "encaminhar"))
        acertos += ok
        if esperado == "encaminhar_urgencia":
            urg_total += 1
            urg_ok += previsto == "encaminhar_urgencia"
        if esperado in ("recusar", "encaminhar"):
            rec_total += 1
            rec_ok += previsto in ("recusar", "encaminhar")
        if not ok:
            erros.append({"id": t["id"], "esperado": esperado, "previsto": previsto})
    n = len(conjunto)
    return {"hit@1": round(hits1 / n_fact, 3), "hit@3": round(hits3 / n_fact, 3), "MRR": round(rr / n_fact, 3),
            "acuracia_comportamento": round(acertos / n, 3),
            "urgencias_encaminhadas": f"{urg_ok}/{urg_total}", "recusa_correta": f"{rec_ok}/{rec_total}",
            "n": n, "erros": erros}


def avaliar(corpus_referencia: list[dict], teste: list[dict]) -> dict:
    ids = [r["id"] for r in corpus_referencia]
    docs = [r["texto"] for r in corpus_referencia]
    dev = _conjunto_dev(corpus_referencia)
    sistemas = {}
    for nome, motor in (("BM25 (linha de base)", MotorBM25(docs)),
                        ("Híbrida: expansão + n-gramas + RRF", BuscaHibrida(docs))):
        limiar = calibrar_limiar(motor)
        sistemas[nome] = {"limiar_calibrado_no_treino": limiar,
                          "treino_dev": _medir(motor, ids, limiar, dev),
                          "teste": _medir(motor, ids, limiar, teste)}
    escolhido = max(sistemas, key=lambda s: (sistemas[s]["treino_dev"]["MRR"],
                                             sistemas[s]["treino_dev"]["acuracia_comportamento"]))
    return {"sistemas": sistemas, "escolhido_pelo_treino": escolhido,
            "sinonimos_so_no_teste": checar_sinonimos(teste),
            **{k: v for k, v in sistemas[escolhido]["teste"].items()}}
