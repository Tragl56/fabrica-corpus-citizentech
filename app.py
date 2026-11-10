"""Interface da Fábrica de Corpus CitizenTech: envie documentos e baixe os três corpus.

    streamlit run app.py
"""
import io
import json
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from fabrica.leitores import EXTENSOES
from run_pipeline import TRES_CORPUS, executar

st.set_page_config(page_title="Fábrica de Corpus CitizenTech", page_icon="🏛️", layout="wide")

NOMES = {"corpus_texto_puro": "Texto puro", "corpus_conversacional": "Conversacional",
         "corpus_perguntas_respostas": "Perguntas e respostas", "corpus_referencia": "Referência (RAG)",
         "conjunto_teste": "Conjunto de teste"}

st.title("Fábrica de Corpus CitizenTech")
st.caption("Envie documentos públicos (TXT, Markdown, HTML, Word ou PDF). A fábrica limpa, normaliza, "
           "anonimiza (LGPD) e gera os três corpus para fine-tuning de uma LLM pequena: "
           "texto puro, conversacional e perguntas e respostas.")

with st.sidebar:
    st.header("Configuração")
    incluir_base = st.checkbox("Incluir acervo base", value=True,
                               help="4 leis federais + guia fictício, com o gabarito curado de recusas, "
                                    "urgências e o conjunto de teste. Recomendado.")
    usar_exemplos = st.checkbox("Incluir exemplos de upload (DOCX, HTML, PDF, MD fictícios)", value=False)
    st.divider()
    st.markdown("**Privacidade:** os arquivos são processados nesta máquina, numa pasta temporária. "
                "Nenhum dado é enviado a serviços externos.")

arquivos = st.file_uploader("Documentos", type=sorted(e.lstrip(".") for e in EXTENSOES), accept_multiple_files=True)

if st.button("Gerar corpus", type="primary", disabled=not (arquivos or incluir_base or usar_exemplos)):
    tmp = Path(tempfile.mkdtemp(prefix="fabrica_"))
    entrada = tmp / "entrada"
    entrada.mkdir()
    for f in arquivos or []:
        (entrada / Path(f.name).name).write_bytes(f.getvalue())
    entradas = [entrada]
    if usar_exemplos:
        from fabrica.ingestao import EXEMPLOS_UPLOAD
        entradas.append(EXEMPLOS_UPLOAD)
    linhas = []
    with st.status("Processando...", expanded=True) as status:
        try:
            rel = executar(entradas, incluir_base, tmp / "saida", log=lambda s: (linhas.append(s), st.write(f"`{s}`")))
            status.update(label="Concluído", state="complete", expanded=False)
        except SystemExit as e:
            status.update(label=str(e), state="error")
            st.stop()
    st.session_state["resultado"] = {"rel": rel, "saida": str(tmp / "saida"), "log": linhas}

res = st.session_state.get("resultado")
if not res:
    st.info("Escolha os documentos e clique em **Gerar corpus**.")
    st.stop()

rel, saida = res["rel"], Path(res["saida"])
audit = rel["auditoria"]

def ler(nome):
    p = saida / f"{nome}.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []

# ------------------------------------------------------------ resumo
c = st.columns(4)
for col, nome in zip(c, TRES_CORPUS):
    col.metric(f"{NOMES[nome]} (registros)", rel["contagens"][nome])
c[3].metric("Auditoria", "OK" if audit["aprovado"] else "Falhou")
if not audit["aprovado"]:
    st.error("A auditoria falhou: os corpus NÃO devem ser usados. Veja os detalhes abaixo.")
for a in rel["avisos"]:
    st.warning(a)

with st.expander("Auditoria (PII, fidelidade, recusas, formato, vazamento)", expanded=not audit["aprovado"]):
    for teste, ok in audit["testes"].items():
        st.markdown(f"{'✅' if ok else '❌'} `{teste}`")
    st.json(audit["detalhes"], expanded=False)

with st.expander("Documentos processados"):
    linhas = [{"documento": k, **{c: v.get(c) for c in ("formato", "origem", "caracteres_brutos", "caracteres_limpos",
                                                          "pii_substituidas", "chunks")}}
              for k, v in rel["estatisticas_por_documento"].items()]
    st.dataframe(linhas, use_container_width=True, hide_index=True)

# ------------------------------------------------------------ downloads
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in saida.rglob("*"):
        if p.is_file():
            z.write(p, p.relative_to(saida))
d = st.columns(len(TRES_CORPUS) + 1)
for col, nome in zip(d, TRES_CORPUS):
    col.download_button(f"Baixar {NOMES[nome].lower()}", (saida / f"{nome}.jsonl").read_bytes(),
                        f"{nome}.jsonl", "application/jsonl", disabled=not audit["aprovado"])
d[-1].download_button("Baixar tudo (.zip)", buf.getvalue(), "corpus_citizentech.zip", "application/zip",
                      disabled=not audit["aprovado"])

# ------------------------------------------------------------ inspeção (humano no circuito)
st.subheader("Revise antes de treinar")
abas = st.tabs([NOMES[n] for n in TRES_CORPUS] + ["Antes × depois"])

with abas[0]:
    regs = ler("corpus_texto_puro")
    for r in regs[:20]:
        with st.expander(f"{r['meta']['id']} — {r['meta']['n_palavras']} palavras ({r['meta']['formato_original']})"):
            st.text(r["text"])


def mostrar_chat(ex):
    for m in ex["messages"][1:]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            txt = m["content"]
            if "CONTEXTO:" in txt:
                ctx, perg = txt.split("PERGUNTA:", 1)
                with st.expander("CONTEXTO recuperado (o que o modelo recebe)"):
                    st.text(ctx.replace("CONTEXTO:", "").strip())
                txt = perg.strip()
            st.markdown(txt)


with abas[1]:
    regs = ler("corpus_conversacional")
    tipos = sorted({r["meta"]["tipo_dialogo"] for r in regs})
    tipo = st.selectbox("Tipo de diálogo", tipos)
    sel = [r for r in regs if r["meta"]["tipo_dialogo"] == tipo]
    i = st.number_input("Exemplo", 1, max(1, len(sel)), 1, key="conv") - 1
    if sel:
        mostrar_chat(sel[i])

with abas[2]:
    regs = ler("corpus_perguntas_respostas")
    origem = st.radio("Origem", ["todas", "automatico", "curado"], horizontal=True)
    sel = [r for r in regs if origem == "todas" or r["meta"]["origem"] == origem]
    i = st.number_input("Exemplo", 1, max(1, len(sel)), 1, key="qa") - 1
    if sel:
        st.caption(f"item `{sel[i]['meta']['item']}` · comportamento `{sel[i]['meta']['comportamento']}` · "
                   f"fontes {sel[i]['meta']['fontes']}")
        mostrar_chat(sel[i])

with abas[3]:
    arqs = sorted((saida / "antes_depois").glob("*.md"))
    if arqs:
        esc = st.selectbox("Documento", [a.stem for a in arqs])
        st.markdown((saida / "antes_depois" / f"{esc}.md").read_text(encoding="utf-8"))
    else:
        st.info("Nenhum dado pessoal encontrado nos documentos enviados.")
