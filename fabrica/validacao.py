"""Etapa 6 — Auditoria: a fábrica só entrega se TODOS os testes passarem.

  1. PII zero: os detectores rodam de novo sobre cada string de todos os .jsonl; além disso,
     nenhum dado pessoal ORIGINAL dos documentos fictícios (gabarito abaixo + log da
     anonimização de todos os documentos) pode aparecer em nenhum arquivo.
  2. Fidelidade: todo trecho de apoio está, literalmente, no CONTEXTO do exemplo e no corpus
     de referência; toda fonte usada é citada numa resposta do assistente.
  3. Recusas: >= 10 exemplos de recusa/encaminhamento, com urgências (Q&A e conversacional).
  4. Formato: system -> (user -> assistant)+ ; diálogos multi-turn presentes; texto puro não vazio; ids únicos.
  5. Vazamento: perguntas de teste diferentes de TODAS as perguntas de treino (curadas e automáticas).
"""
import json
import re

from .anonimizacao import detectar_pii

# Gabarito escrito à mão: dados pessoais (fictícios) do documento-teste e dos exemplos de upload.
PII_GABARITO = [
    # dados/brutos/documento_teste_ficticio_guia_vila_esperanca.txt
    "Maria Aparecida", "dos Santos Lima", "123.456.789-00", "12.345.678-X", "14/03/1978",
    "Rua das Palmeiras", "Jardim Esperança", "01234-567", "98888-7777", "maria.lima78",
    "898 0012 3456 7890", "João Carlos Pereira", "45.678", "2026.000123-4", "josé roberto",
    "José Roberto", "98765432111", "av. brasil 1500", "97777-6666", "BRA2E19", "Carlos Eduardo Souza",
    # dados/exemplos_upload/*
    "Ana Beatriz Moura", "97654-3210", "ana.moura@example.com", "Rua dos Ipês", "Roberto Alves Nunes",
    "321.654.987-00", "Sebastião Ferreira", "3456-7890", "Luzia Campos", "luzia.campos@example.com",
]
CHAT = ("corpus_perguntas_respostas", "corpus_conversacional")


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _papeis_ok(msgs) -> bool:
    papeis = [m["role"] for m in msgs]
    return (len(papeis) >= 3 and papeis[0] == "system" and len(papeis) % 2 == 1
            and all(p == ("user" if i % 2 == 0 else "assistant") for i, p in enumerate(papeis[1:])))


def auditar(corpus: dict, pii_originais: list[str], vazamento: tuple, usar_curadoria: bool = True) -> dict:
    rel = {"testes": {}, "detalhes": {}}

    # 1. PII
    achados_regex, achados_originais = [], []
    originais = sorted({p for p in PII_GABARITO + pii_originais if len(p) >= 4})
    for nome, regs in corpus.items():
        for r in regs:
            for s in _strings(r):
                for tipo, val in detectar_pii(s):
                    achados_regex.append((nome, tipo, val))
                low = s.lower()
                for p in originais:
                    if p.lower() in low:
                        achados_originais.append((nome, p))
    rel["testes"]["pii_detectores_zero"] = not achados_regex
    rel["testes"]["pii_originais_zero"] = not achados_originais
    rel["detalhes"]["pii_achados"] = achados_regex[:20] + achados_originais[:20]
    rel["detalhes"]["n_valores_pii_verificados"] = len(originais)

    # 2. Fidelidade
    ref = {r["id"]: r["texto"] for r in corpus["corpus_referencia"]}
    falhas = []
    for nome in CHAT:
        for ex in corpus[nome]:
            primeiro_user = ex["messages"][1]["content"]
            respostas = " ".join(m["content"] for m in ex["messages"] if m["role"] == "assistant")
            rotulo = ex["meta"].get("item") or ex["meta"].get("itens")
            for t in ex["meta"].get("trechos_apoio", []):
                if not (t in primeiro_user and any(t in ref.get(f, "") for f in ex["meta"]["fontes"])):
                    falhas.append((nome, rotulo, t[:60]))
            for f in ex["meta"]["fontes"]:
                if f not in respostas:
                    falhas.append((nome, rotulo, f"fonte {f} não citada"))
            # o inverso: toda fonte CITADA pelo assistente tem que estar no CONTEXTO que ele recebeu
            for f in re.findall(r"([a-z0-9_]+#[A-Za-z0-9.\-]+)", " ".join(re.findall(r"Fonte: \[([^\]]+)\]", respostas))):
                if f"[{f}]" not in primeiro_user:
                    falhas.append((nome, rotulo, f"fonte {f} citada mas ausente do CONTEXTO"))
    for t in corpus["conjunto_teste"]:
        for tr in t["trechos_apoio"]:
            if not any(tr in ref[f] for f in t["fontes_esperadas"]):
                falhas.append(("conjunto_teste", t["id"], tr[:60]))
    rel["testes"]["fidelidade_trechos"] = not falhas
    rel["detalhes"]["falhas_fidelidade"] = falhas[:20]

    # 3. Recusas / encaminhamentos
    qa = corpus["corpus_perguntas_respostas"]
    n_rec = sum(1 for e in qa if e["meta"]["comportamento"] != "responder")
    n_urg = sum(1 for e in qa if e["meta"]["categoria"] == "urgencia")
    n_urg_conv = sum(1 for e in corpus["corpus_conversacional"] if e["meta"].get("tipo_dialogo") == "urgencia")
    if usar_curadoria:
        rel["testes"]["recusas_ao_menos_10"] = n_rec >= 10
        rel["testes"]["urgencias_presentes"] = n_urg >= 1 and n_urg_conv >= 1
    rel["detalhes"].update({"n_recusas_encaminhamentos": n_rec, "n_urgencias": n_urg,
                            "n_dialogos_com_urgencia": n_urg_conv,
                            "recusas_auditadas": usar_curadoria})

    # 4. Formato
    rel["testes"]["formato_chat_valido"] = all(_papeis_ok(e["messages"]) for n in CHAT for e in corpus[n])
    n_multi = sum(1 for e in corpus["corpus_conversacional"] if e["meta"].get("n_turnos_usuario", 1) >= 2)
    rel["testes"]["conversacional_multi_turn"] = n_multi >= 1
    rel["testes"]["texto_puro_valido"] = bool(corpus["corpus_texto_puro"]) and all(
        isinstance(r.get("text"), str) and len(r["text"].split()) >= 5 for r in corpus["corpus_texto_puro"])
    ids_ref = [r["id"] for r in corpus["corpus_referencia"]]
    ids_teste = [t["id"] for t in corpus["conjunto_teste"]]
    rel["testes"]["ids_unicos"] = len(set(ids_ref)) == len(ids_ref) and len(set(ids_teste)) == len(ids_teste)
    rel["detalhes"]["n_dialogos_multi_turn"] = n_multi
    json.dumps(corpus)  # serializável

    # 5. Vazamento
    rel["testes"]["sem_vazamento_teste_treino"] = vazamento[0] < 0.7
    rel["detalhes"]["maior_jaccard_teste_treino"] = {"valor": round(vazamento[0], 3),
                                                     "teste": vazamento[1], "treino": vazamento[2]}
    rel["aprovado"] = all(rel["testes"].values())
    return rel
