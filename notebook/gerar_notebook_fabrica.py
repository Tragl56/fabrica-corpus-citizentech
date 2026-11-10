"""Gera notebook/Fabrica_de_Corpus_CitizenTech.ipynb (demonstração passo a passo do pipeline).

    python notebook/gerar_notebook_fabrica.py
"""
import json
from pathlib import Path

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(True)})


def code(s):
    CELLS.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": s.strip("\n").splitlines(True)})


md(r"""
# Fábrica de Corpus CitizenTech — GS 2026.2
**FIAP · Processamento de Linguagem Natural, Chatbots & Virtual Agents**

> *Enunciado:* desenvolver uma ferramenta que permita **subir diversos tipos de documentos e textos**, realize a **limpeza e normalização** dos dados e permita criar **três tipos de corpus (conversacional, perguntas e respostas, texto puro)** para o fine-tuning de uma LLM de pequeno porte.

`Upload (TXT, MD, HTML, DOCX, PDF) → Limpeza e normalização → Anonimização (LGPD) → Chunking → Geração (curada + automática) → 3 corpus → Auditoria → Avaliação`

**Forma se treina, fato se consulta.** Roda sem chave de API. Interface com upload: `streamlit run app.py`.
""")
code(r"""
import os, sys, json
from collections import Counter
RAIZ = os.path.abspath("..") if os.path.basename(os.getcwd()) == "notebook" else os.getcwd()
sys.path.insert(0, RAIZ); os.chdir(RAIZ)
print("Raiz do projeto:", RAIZ)
""")

md("## 1. Upload de vários formatos\nCada leitor converte o arquivo para um texto padronizado: títulos viram `## `, texto tachado vira `~~revogado~~`. No PDF, saem o cabeçalho e o rodapé repetidos e a hifenização é desfeita. No HTML, saem menus, scripts e rodapé.")
code(r"""
from fabrica.ingestao import carregar_documentos, EXEMPLOS_UPLOAD
docs, avisos = carregar_documentos([EXEMPLOS_UPLOAD], incluir_base=True)
for d in docs:
    print(f"{d['doc_id']:<22} {d['formato']:<5} {d['origem']:<12} {d['tipo']:<30} {d['titulo'][:50]}")
""")
code(r"""
pdf = next(d for d in docs if d["formato"] == "pdf")
print("PDF depois do leitor (sem cabeçalho/rodapé, hifenização desfeita):\n")
print(pdf["texto_bruto"][:700])
""")

md("## 2. Limpeza e normalização\nRemove revogados, assinaturas, notas de alteração, navegação de site e incisos vetados. Normaliza Unicode, aspas, marcadores e caracteres invisíveis.")
code(r"""
from fabrica.limpeza import limpar
bruto = docs[0]["texto_bruto"]
limpo, stats = limpar(bruto)
print(dict(stats))
print("\n--- Art. 10-A ANTES ---\n", bruto[bruto.find("Art. 10-A"):][:600])
print("\n--- DEPOIS ---\n", limpo[limpo.find("Art. 10-A"):][:400])
""")

md("## 3. Anonimização (LGPD): antes × depois\nTodos os dados pessoais dos documentos fictícios são inventados (CPF com dígito verificador inválido, e-mail `example.com`).")
code(r"""
from fabrica.anonimizacao import anonimizar
for d in docs:
    if not d["ficticio"]:
        continue
    l, _ = limpar(d["texto_bruto"], lei=d["tipo"].startswith("lei"))
    _, reg = anonimizar(l)
    print(f"{d['doc_id']:<22} ({d['formato']}):", [(t, v) for t, v in reg][:6], "..." if len(reg) > 6 else "")
""")

md("## 4. Chunking\nLei: 1 chunk por artigo (artigos longos repetem o caput). Documento com títulos: 1 chunk por seção. Texto corrido: parágrafos agrupados com sobreposição.")
code(r"""
from fabrica.chunking import fazer_chunks
chunks_por_doc, textos = {}, {}
for d in docs:
    l, _ = limpar(d["texto_bruto"], lei=d["tipo"].startswith("lei")); a, _ = anonimizar(l)
    textos[d["doc_id"]], chunks_por_doc[d["doc_id"]] = a, fazer_chunks(d, a)
for doc_id in ("cdc", "decreto_hortas", "tarifa_social_agua"):
    for c in chunks_por_doc[doc_id]:
        print(f"{c['chunk_id']:<26} {len(c['texto'].split()):>4} palavras | {c['texto'][:60]!r}")
""")

md("## 5. Geração automática para QUALQUER documento\nRegras extrativas sobre a estrutura (caput, listas, definições, prazos, seções, parágrafos). A resposta copia linhas literais, então é fiel por construção. O gabarito curado à mão continua sendo a referência de qualidade e o conjunto de teste.")
code(r"""
from fabrica.autogeracao import gerar_itens_automaticos
auto = gerar_itens_automaticos(docs, chunks_por_doc)
print(len(auto), "itens automáticos | por regra:", Counter(i["regra"][:9] for i in auto))
for it in [i for i in auto if i["doc_id"] in ("decreto_hortas", "transporte_rural")][:4]:
    print("\nP:", it["treino"][0], "\nR:", it["resposta"][:220])
""")

md("## 6–8. Pipeline completo: 3 corpus + referência + teste, auditoria e avaliação")
code(r"""
import run_pipeline
rel = run_pipeline.executar()
print("\nAuditoria aprovada:", rel["auditoria"]["aprovado"])
""")

md("## 9. Os três corpus")
code(r"""
def ler(nome): return [json.loads(l) for l in open(f"saida/{nome}.jsonl", encoding="utf-8")]
tp, cv, qa = ler("corpus_texto_puro"), ler("corpus_conversacional"), ler("corpus_perguntas_respostas")

print("TEXTO PURO (pré-treino continuado):", len(tp), "registros\n", tp[-2]["text"][:350], "\n")

def mostrar(ex):
    for m in ex["messages"][1:]:
        c = m["content"]
        c = "[CONTEXTO omitido] " + c.split("PERGUNTA:")[1].strip() if "CONTEXTO:" in c else c
        print(f"  {m['role']:>9}: {c[:200]}")

print("CONVERSACIONAL:", len(cv), "| por tipo:", Counter(e["meta"]["tipo_dialogo"] for e in cv))
mostrar(next(e for e in cv if e["meta"]["tipo_dialogo"] == "urgencia"))
print("\nPERGUNTAS E RESPOSTAS:", len(qa), "| por origem:", Counter(e["meta"]["origem"] for e in qa))
mostrar(next(e for e in qa if e["meta"]["origem"] == "automatico" and "decreto" in e["meta"]["item"]))
""")

md(r"""
## 10. (Bônus) LoRA
`notebook/Bonus_LoRA_CidadaoBot_Colab.ipynb` treina um LoRA no Qwen2.5-0.5B com `corpus_perguntas_respostas.jsonl` + `corpus_conversacional.jsonl` (com máscara em todas as respostas dos diálogos de várias trocas) e compara A/B/C no `conjunto_teste.jsonl`.
""")

nb = {"cells": CELLS, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                   "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
out = Path(__file__).parent / "Fabrica_de_Corpus_CitizenTech.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("gerado:", out)
