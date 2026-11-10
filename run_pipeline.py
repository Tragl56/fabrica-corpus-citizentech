"""Fábrica de Corpus CitizenTech — roda tudo do início ao fim.

    python run_pipeline.py                         # acervo base + dados/exemplos_upload/
    python run_pipeline.py --entrada minha_pasta   # acervo base + seus arquivos (.txt .md .html .docx .pdf)
    python run_pipeline.py --entrada minha_pasta --sem-base --saida saida_minha

Sem chave de API. O pipeline usa só a biblioteca padrão (PDF precisa de pymupdf ou pypdf).
A interface com upload está em app.py (streamlit run app.py).
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from fabrica.anonimizacao import anonimizar
from fabrica.avaliacao import avaliar
from fabrica.chunking import fazer_chunks
from fabrica.geracao import checar_vazamento, gerar_tudo
from fabrica.ingestao import EXEMPLOS_UPLOAD, SAIDA, carregar_documentos
from fabrica.limpeza import limpar
from fabrica.validacao import auditar

TRES_CORPUS = ("corpus_texto_puro", "corpus_conversacional", "corpus_perguntas_respostas")


def salvar_jsonl(pasta: Path, nome: str, regs: list):
    with open(pasta / f"{nome}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in regs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def antes_depois_md(doc, anon, log) -> str:
    linhas = [f"# Antes × depois: {doc['titulo']}", "",
              f"Arquivo `{doc['arquivo']}` (formato {doc.get('formato')}, fictício={doc['ficticio']}).", "",
              "## Substituições feitas pela anonimização", "", "| # | Tipo | Valor original | Vira |", "|---|---|---|---|"]
    linhas += [f"| {i} | {tipo} | `{val}` | `[{tipo}]` |" for i, (tipo, val) in enumerate(log, 1)]
    linhas += ["", f"Total: **{len(log)}** dados pessoais substituídos "
               f"({', '.join(f'{k}: {v}' for k, v in Counter(t for t, _ in log).items()) or 'nenhum'}).", "",
               "## ANTES (texto extraído do arquivo, sem limpeza)", "", "```text", doc["texto_bruto"].strip(), "```", "",
               "## DEPOIS (limpo + anonimizado, como entra no corpus)", "", "```text", anon.strip(), "```", ""]
    return "\n".join(linhas)


def executar(entradas=None, incluir_base=True, pasta_saida: Path = SAIDA, avaliar_busca=True, log=print) -> dict:
    """Roda o pipeline inteiro e grava tudo em `pasta_saida`. Devolve o relatório (dict)."""
    pasta_saida = Path(pasta_saida)
    (pasta_saida / "antes_depois").mkdir(parents=True, exist_ok=True)

    log("1) Ingestão")
    docs, avisos = carregar_documentos(entradas, incluir_base)
    for a in avisos:
        log(f"   ! {a}")
    if not docs:
        raise SystemExit("Nenhum documento para processar.")
    for d in docs:
        log(f"   - {d['doc_id']:<22} {d.get('formato', ''):<5} {len(d['texto_bruto']):>6} caracteres  "
            f"origem={d.get('origem')}  ficticio={d['ficticio']}")
    usar_curadoria = incluir_base
    if not incluir_base:
        log("   ! Sem o acervo base: o corpus não terá recusas, urgências nem conjunto de teste curado. "
            "Recomendado manter o acervo base junto com os seus documentos.")

    log("2) Limpeza  3) Anonimização  4) Chunking")
    chunks_por_doc, textos_anon, estat, pii_originais = {}, {}, {}, []
    for d in docs:
        limpo, st = limpar(d["texto_bruto"], lei=d["tipo"].startswith("lei"))
        anon, reg = anonimizar(limpo)
        pii_originais += [v for _, v in reg]
        textos_anon[d["doc_id"]] = anon
        chunks_por_doc[d["doc_id"]] = fazer_chunks(d, anon)
        estat[d["doc_id"]] = {"formato": d.get("formato"), "origem": d.get("origem"),
                              "caracteres_brutos": len(d["texto_bruto"]), "caracteres_limpos": len(limpo),
                              **dict(st), "pii_substituidas": len(reg),
                              "pii_por_tipo": dict(Counter(t for t, _ in reg)),
                              "chunks": len(chunks_por_doc[d["doc_id"]])}
        log(f"   - {d['doc_id']:<22} limpeza={ {k: v for k, v in st.items() if v} } pii={len(reg)} "
            f"chunks={estat[d['doc_id']]['chunks']}")
        if d["ficticio"] or reg:
            (pasta_saida / "antes_depois" / f"{d['doc_id']}.md").write_text(antes_depois_md(d, anon, reg), encoding="utf-8")

    log("5) Geração dos corpus")
    corpus, avisos_ger = gerar_tudo(docs, chunks_por_doc, textos_anon, usar_curadoria)
    for a in avisos_ger:
        log(f"   ! {a}")
    for nome, regs in corpus.items():
        salvar_jsonl(pasta_saida, nome, regs)
        marca = "  <- corpus pedido no enunciado" if nome in TRES_CORPUS else ""
        log(f"   - {nome}.jsonl: {len(regs)} registros{marca}")
    origem = Counter(e["meta"]["origem"] for e in corpus["corpus_perguntas_respostas"])
    log(f"     perguntas e respostas por origem: {dict(origem)}")

    log("6) Auditoria")
    rel = auditar(corpus, pii_originais, checar_vazamento(corpus), usar_curadoria)
    for teste, ok in rel["testes"].items():
        log(f"   [{'OK' if ok else 'FALHOU'}] {teste}")
    d = rel["detalhes"]
    log(f"   recusas/encaminhamentos: {d['n_recusas_encaminhamentos']} (urgências: {d['n_urgencias']}); "
        f"diálogos multi-turn: {d['n_dialogos_multi_turn']} (com urgência no meio: {d['n_dialogos_com_urgencia']})")

    met = None
    if avaliar_busca and corpus["conjunto_teste"]:
        log("7) Avaliação sem LLM (regras + busca): escolha no treino, medida no teste")
        met = avaliar(corpus["corpus_referencia"], corpus["conjunto_teste"])
        cols = ("hit@1", "hit@3", "MRR", "acuracia_comportamento", "urgencias_encaminhadas", "recusa_correta")
        log(f"   {'sistema':<36} {'conjunto':<10} " + " ".join(f"{c[:12]:>12}" for c in cols))
        for nome, s in met["sistemas"].items():
            for conj in ("treino_dev", "teste"):
                log(f"   {nome:<36} {conj:<10} " + " ".join(f"{str(s[conj][c]):>12}" for c in cols))
        log(f"   -> escolhido pelo treino: {met['escolhido_pelo_treino']}")
        log(f"   sinônimos que só aparecem no teste (vazamento): {met['sinonimos_so_no_teste'] or 'nenhum'}")

    relatorio = {"documentos": [{k: v for k, v in x.items() if k != "texto_bruto"} for x in docs],
                 "avisos": avisos + avisos_ger, "estatisticas_por_documento": estat, "auditoria": rel,
                 "avaliacao_linha_de_base": met, "contagens": {n: len(r) for n, r in corpus.items()}}
    (pasta_saida / "relatorio_execucao.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                                         encoding="utf-8")
    return relatorio


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Fábrica de Corpus CitizenTech")
    ap.add_argument("--entrada", action="append", type=Path,
                    help="pasta com documentos (.txt .md .html .docx .pdf); pode repetir. Padrão: dados/exemplos_upload")
    ap.add_argument("--sem-base", action="store_true", help="não incluir o acervo base (leis + guia) nem o gabarito curado")
    ap.add_argument("--saida", type=Path, default=SAIDA)
    args = ap.parse_args()
    rel = executar(args.entrada or [EXEMPLOS_UPLOAD], not args.sem_base, args.saida)
    if not rel["auditoria"]["aprovado"]:
        print(f"\nAUDITORIA REPROVADA — veja {args.saida / 'relatorio_execucao.json'}")
        print(json.dumps(rel["auditoria"]["detalhes"], ensure_ascii=False, indent=1)[:3000])
        sys.exit(1)
    print(f"\nAuditoria aprovada. Corpus prontos em {args.saida}/")


if __name__ == "__main__":
    main()
