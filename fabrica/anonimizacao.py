"""Etapa 3 — Anonimização (LGPD): troca dados pessoais por etiquetas.

Duas camadas:
  1. Padrões estruturados (regex): e-mail, cartão SUS, CPF, CNPJ, RG, CEP,
     telefone, placa, data de nascimento, endereço, bairro, protocolo, matrícula.
  2. Nomes de pessoas: (a) depois de gatilhos de contexto ("cidadã", "Sr.",
     "aqui é o", "meu nome é", "servidor"...), aceitando também nomes em
     minúsculas (estilo WhatsApp); (b) sequência Nome + Sobrenome em que o
     primeiro nome está num dicionário de prenomes brasileiros.

Cada substituição é registrada (tipo, original, etiqueta) para o relatório
de antes/depois. As etiquetas não carregam o dado original.
"""
import re

# ---------------------------------------------------------------- camada 1
_D = r"\d"
PADROES = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("CARTAO_SUS", re.compile(r"\b[1-9]\d{2}\s\d{4}\s\d{4}\s\d{4}\b|\b[1-9]\d{14}\b")),
    ("CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
    ("CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|(?<![\d.])\d{11}(?![\d.])")),
    ("RG", re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dXx]\b")),
    ("CEP", re.compile(r"\b\d{5}-\d{3}\b")),
    ("TELEFONE", re.compile(r"(?:\(\d{2}\)\s?|\b\d{2}\s)?\b9?\d{4}-\d{4}\b")),
    ("PLACA", re.compile(r"\b[A-Z]{3}-?\d[A-Z0-9]\d{2}\b")),
]
# padrões com gatilho: o gatilho fica, só o valor vira etiqueta
PADROES_COM_GATILHO = [
    ("DATA_NASCIMENTO", re.compile(r"(?i)(nascid[oa] em|data de nascimento:?|nasc\.)\s*\d{1,2}/\d{1,2}/\d{2,4}")),
    ("PROTOCOLO", re.compile(r"(?i)(protocolo(?: nº| n\.)?)\s*[\d][\d./-]{5,}\d")),
    ("MATRICULA", re.compile(r"(?i)(matrícula(?: nº)?)\s*[\d][\d./-]*\d")),
    ("BAIRRO", re.compile(r"(Bairro)\s+[A-ZÀ-Ú][\wÀ-ú]+(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ú][\wÀ-ú]+)*")),
]
RE_ENDERECO = re.compile(
    r"(?i)\b(?:rua|r\.|avenida|av\.|travessa|alameda|praça|estrada|rodovia)\s+"
    r"[^,\n\d]{2,40}?,?\s*(?:nº|n°|n\.|número)?\s*\d+[a-z]?"
    r"(?:\s*,?\s*(?:apto|apartamento|ap\.|bloco|casa)\s*\d+)?"
)
VERBOS_COMUNS = {"ta", "tá", "está", "esta", "estão", "faz", "fica", "ficou", "tem", "é", "foi"}

# ---------------------------------------------------------------- camada 2
PRENOMES = set("""
maria josé jose joão joao ana antônio antonio francisco carlos paulo pedro lucas luiz luis
marcos gabriel rafael daniel marcelo bruno eduardo felipe raimundo rodrigo manoel manuel
mateus matheus andré andre fernando fábio fabio leonardo gustavo guilherme leandro tiago
thiago anderson ricardo márcio marcio jorge sebastião sebastiao alexandre roberto edson
diego vitor victor sérgio sergio claudio cláudio juliana adriana márcia marcia fernanda
patrícia patricia aline sandra camila amanda bruna jéssica jessica letícia leticia júlia
julia luciana vanessa mariana gabriela vera vitória vitoria larissa cláudia claudia beatriz
rita sônia sonia renata eliane josefa simone natália natalia cristina carla débora debora
rosângela rosangela jaqueline rosa daniela aparecida marta raquel francisca antônia antonia
helena luana tatiana paula priscila carolina isabela laura sofia alice valentina heloísa
luzia lúcia lucia benedita conceição conceicao terezinha tereza teresa irene joana luíza luiza
""".split())
CONECTORES = {"da", "de", "do", "das", "dos", "e"}
GATILHOS_NOME = re.compile(
    r"(?i)\b(cidadã|cidadão|servidora?|sr\.|sra\.|senhora?|requerente|vizinh[oa]|"
    r"aqui é (?:o|a)|meu nome é|me chamo|sou (?:o|a)|dono é o|dona é a|eu,|"
    r"falar com|fale com|procure|procurar|atendente|morador[a]?|coordenador[a]?(?: d[aoe] [a-zà-ú]+)?:|"
    r"respons[áa]vel(?: técnic[oa])?:|contato:)\s+"
)
RE_PALAVRA = re.compile(r"[A-Za-zÀ-ÿ]+")


def _eh_nome(tok: str, permitir_minuscula: bool) -> bool:
    if tok.lower() in PRENOMES:
        return True
    return tok[:1].isupper() and tok[1:].islower() and len(tok) > 1


def _consumir_nome(texto: str, inicio: int, permitir_minuscula: bool) -> int:
    """A partir de `inicio`, avança enquanto houver tokens de nome. Devolve o fim."""
    pos, fim, n_nomes = inicio, inicio, 0
    while True:
        m = RE_PALAVRA.match(texto, pos)
        if not m:
            break
        tok = m.group(0)
        minusc_ok = permitir_minuscula and n_nomes >= 1 and tok.lower() not in CONECTORES and len(tok) > 2
        if _eh_nome(tok, permitir_minuscula) or minusc_ok:
            n_nomes += 1
            fim = m.end()
        elif tok.lower() in CONECTORES and n_nomes >= 1:
            pass  # conector só entra se vier outro nome depois
        else:
            break
        # pula espaço simples entre tokens
        prox = m.end()
        if prox < len(texto) and texto[prox] == " ":
            pos = prox + 1
        else:
            break
    return fim if n_nomes >= 1 else inicio


def _substituir_nomes(texto: str, log: list) -> str:
    # (a) gatilhos de contexto
    saida, ultimo = [], 0
    for m in GATILHOS_NOME.finditer(texto):
        if m.start() < ultimo:
            continue
        ini = m.end()
        prim = RE_PALAVRA.match(texto, ini)
        if not prim:
            continue
        minuscula = prim.group(0).islower()
        if minuscula and prim.group(0).lower() not in PRENOMES:
            continue
        fim = _consumir_nome(texto, ini, permitir_minuscula=minuscula)
        if fim > ini:
            log.append(("NOME", texto[ini:fim]))
            saida.append(texto[ultimo:ini] + "[NOME]")
            ultimo = fim
    saida.append(texto[ultimo:])
    texto = "".join(saida)

    # (b) Prenome do dicionário + Sobrenome(s) capitalizado(s)
    def repl(m):
        log.append(("NOME", m.group(0)))
        return "[NOME]"
    padrao = re.compile(
        r"\b(?:" + "|".join(sorted((p.capitalize() for p in PRENOMES), key=len, reverse=True)) + r")"
        r"(?:\s+(?:d[aeo]s?\s+)?[A-ZÀ-Ú][a-zà-ÿ]+)+"
    )
    return padrao.sub(repl, texto)


def anonimizar(texto: str) -> tuple[str, list[tuple[str, str]]]:
    """Devolve (texto_anonimizado, log) com log = [(tipo, valor_original), ...]."""
    log: list[tuple[str, str]] = []

    for tipo, rx in PADROES_COM_GATILHO:
        def repl(m, tipo=tipo):
            log.append((tipo, m.group(0)[len(m.group(1)):].strip()))
            return f"{m.group(1)} [{tipo}]"
        texto = rx.sub(repl, texto)

    def repl_end(m):
        # evita falso positivo do tipo "a lâmpada da minha rua ta queimada faz 1 semana"
        if set(re.findall(r"[a-zà-ÿ]+", m.group(0).lower())) & VERBOS_COMUNS:
            return m.group(0)
        log.append(("ENDERECO", m.group(0)))
        return "[ENDERECO]"
    texto = RE_ENDERECO.sub(repl_end, texto)

    for tipo, rx in PADROES:
        def repl(m, tipo=tipo):
            log.append((tipo, m.group(0)))
            return f"[{tipo}]"
        texto = rx.sub(repl, texto)

    texto = _substituir_nomes(texto, log)
    return texto, log


def detectar_pii(texto: str) -> list[tuple[str, str]]:
    """Auditoria: roda os mesmos detectores sem substituir (usado no validador)."""
    _, log = anonimizar(texto)
    return log
