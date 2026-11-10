"""Busca léxica em Python puro (Aula 19).

- BM25 por palavras: escolhe os contextos-distratores na geração e é a linha de base.
- BuscaHibrida: BM25 por palavras com EXPANSÃO DE CONSULTA (linguagem do cidadão ->
  termos da lei) + BM25 por n-gramas de caracteres (tolera erros de digitação e
  variações de palavra), fundidos por Reciprocal Rank Fusion (RRF).
A escolha da variante foi feita medindo só nas perguntas de TREINO (ver avaliacao.py).
"""
import math
import re
import unicodedata
from collections import Counter

STOP = set("""a o as os um uma uns umas de da do das dos e é em no na nos nas por para pra pro
com sem que se ou ao aos à às eu me meu minha meus minhas você voce vc tu ele ela isso
esse essa este esta tem ter ta tá foi ser são sao como qual quais quando onde quanto qto
mais mas já ja não nao sim pode posso lei art""".split())


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tokenizar(texto: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", _sem_acento(texto.lower()))
    return [t[:6] for t in toks if t not in STOP and len(t) > 1]   # "stemming" por prefixo


def ngramas(texto: str, n: int = 4) -> list[str]:
    t = " " + re.sub(r"\s+", " ", _sem_acento(texto.lower())) + " "
    return [t[i:i + n] for i in range(len(t) - n + 1)]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75, tokenizador=tokenizar):
        self.tok = tokenizador
        self.toks = [tokenizador(d) for d in docs]
        self.n = len(docs)
        self.avg = sum(map(len, self.toks)) / max(self.n, 1)
        self.df = Counter(t for d in self.toks for t in set(d))
        self.tf = [Counter(d) for d in self.toks]
        self.k1, self.b = k1, b

    def idf(self, t):
        return math.log(1 + (self.n - self.df[t] + 0.5) / (self.df[t] + 0.5))

    def scores(self, consulta: str) -> list[float]:
        q = self.tok(consulta)
        out = []
        for tf, d in zip(self.tf, self.toks):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf(t) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            out.append(s)
        return out

    def ranking(self, consulta: str, k: int = 5) -> list[tuple[int, float]]:
        sc = self.scores(consulta)
        return sorted(enumerate(sc), key=lambda x: -x[1])[:k]


# Linguagem do cidadão -> vocabulário da lei. Nenhuma chave pode aparecer SÓ nas perguntas
# de teste (checado a cada execução em avaliacao.checar_sinonimos).
SINONIMOS = {
    "defeito": "vicio", "estragou": "vicio", "quebrou": "vicio", "conserto": "vicio sanado",
    "consertar": "vicio sanado", "arrumar": "vicio sanado", "trocar": "substituicao", "troca": "substituicao",
    "devolver": "restituicao quantia", "devolvido": "restituicao", "dinheiro": "quantia",
    "desconto": "abatimento", "desistir": "arrependimento", "arrependi": "arrependimento",
    "cobrador": "cobranca", "cobrando": "cobranca", "ameaca": "constrangimento", "humilhar": "ridiculo constrangimento",
    "reclamacao": "manifestacao", "reclamar": "manifestacao", "denuncia": "manifestacao",
    "prefeitura": "orgao entidade", "governo": "orgao entidade publica", "documento": "informacao",
    "negaram": "indeferimento", "negado": "indeferimento", "negou": "indeferimento",
    "pagar": "gratuito", "cobrar": "gratuito", "apagar": "eliminacao", "excluir": "eliminacao",
    "apaguem": "eliminacao", "corrigir": "correcao", "errado": "correcao incompletos inexatos",
    "meus dados": "titular dados pessoais", "internet": "fora estabelecimento comercial",
    "telefone": "fora estabelecimento comercial", "site": "fora estabelecimento comercial",
    "poste": "iluminacao lampada", "lampada": "iluminacao", "buraco": "buracos via",
    "demora": "prazo", "demorando": "prazo", "quanto tempo": "prazo dias",
}


def expandir(consulta: str) -> str:
    q = _sem_acento(consulta.lower())
    extra = [v for k, v in SINONIMOS.items() if re.search(rf"\b{k}", q)]
    return consulta + (" " + " ".join(extra) if extra else "")


class BuscaHibrida:
    def __init__(self, docs: list[str], k_rrf: int = 60):
        self.palavras = BM25(docs)
        self.chars = BM25(docs, tokenizador=ngramas)
        self.k_rrf = k_rrf

    def confianca(self, consulta: str) -> float:
        """Maior pontuação BM25 (palavras, consulta expandida): usada no limiar de 'não sei'."""
        return max(self.palavras.scores(expandir(consulta)))

    def ranking(self, consulta: str, k: int = 5) -> list[tuple[int, float]]:
        q = expandir(consulta)
        fusao = Counter()
        for motor in (self.palavras, self.chars):
            for pos, (i, _) in enumerate(motor.ranking(q, k=motor.n)):
                fusao[i] += 1 / (self.k_rrf + pos + 1)
        return fusao.most_common(k)
