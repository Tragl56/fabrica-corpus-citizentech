"""Gera o vídeo de apresentação (MP4 1920x1080) da Fábrica de Corpus, 100% local.

  - slides montados com DADOS REAIS (saida/*.jsonl, relatorio_execucao.json, PDF de exemplo, LoRA)
  - telas reais da interface (relatorio/video/telas/, ver capturar_telas.py)
  - narração com a voz pt-BR do Windows (System.Speech, "Microsoft Maria")
  - legendas .srt embutidas + arquivo .srt ao lado; montagem com ffmpeg (imageio-ffmpeg)

    python relatorio/video/gerar_video.py        (rode antes: python run_pipeline.py)
"""
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ))
TMP = AQUI / "_build"
TELAS = AQUI / "telas"
SAIDA_MP4 = AQUI / "video_fabrica_de_corpus.mp4"
W, H = 1920, 1080

AZUL, AZUL_CLARO, FUNDO = (11, 79, 108), (225, 238, 244), (247, 249, 251)
TEXTO, CINZA, VERDE, VERMELHO = (26, 32, 38), (96, 108, 118), (25, 135, 84), (190, 40, 50)
F = "C:/Windows/Fonts/"


def fonte(nome, tam):
    return ImageFont.truetype(F + nome, tam)


TIT, SUB, CORPO, PEQ = fonte("segoeuib.ttf", 58), fonte("segoeui.ttf", 34), fonte("segoeui.ttf", 36), fonte("segoeui.ttf", 26)
NEG, MONO, MONO_P = fonte("segoeuib.ttf", 36), fonte("consola.ttf", 27), fonte("consola.ttf", 24)


# ------------------------------------------------------------------ desenho
def quebrar(d, texto, f, largura):
    linhas = []
    for par in texto.split("\n"):
        atual = ""
        for pal in par.split(" "):
            teste = (atual + " " + pal).strip()
            if d.textlength(teste, font=f) <= largura:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                atual = pal
        linhas.append(atual)
    return linhas


def base(titulo, n):
    img = Image.new("RGB", (W, H), FUNDO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 130], fill=AZUL)
    d.text((80, 32), titulo, font=TIT, fill="white")
    d.text((80, H - 50), "Fábrica de Corpus CitizenTech · FIAP GS 2026.2 · PLN", font=PEQ, fill=CINZA)
    d.text((W - 120, H - 50), f"{n:02d}", font=PEQ, fill=CINZA)
    return img, d


def bloco(d, x, y, w, texto, f=CORPO, cor=TEXTO, esp=10, maxl=None):
    linhas = quebrar(d, texto, f, w)
    if maxl:
        linhas = linhas[:maxl]
    alt = f.size + esp
    for i, ln in enumerate(linhas):
        d.text((x, y + i * alt), ln, font=f, fill=cor)
    return y + len(linhas) * alt


def caixa(d, x0, y0, x1, y1, rotulo=None, cor=AZUL, fundo="white"):
    d.rounded_rectangle([x0, y0, x1, y1], 18, fill=fundo, outline=cor, width=3)
    if rotulo:
        tw = d.textlength(rotulo, font=NEG)
        d.rounded_rectangle([x0 + 24, y0 - 26, x0 + 48 + tw, y0 + 26], 12, fill=cor)
        d.text((x0 + 36, y0 - 22), rotulo, font=NEG, fill="white")


def slide_titulo(n):
    img = Image.new("RGB", (W, H), AZUL)
    d = ImageDraw.Draw(img)
    d.text((140, 250), "Fábrica de Corpus", font=fonte("segoeuib.ttf", 110), fill="white")
    d.text((140, 380), "CitizenTech", font=fonte("segoeuib.ttf", 110), fill=(150, 210, 230))
    d.text((140, 540), "Do documento público ao corpus de fine-tuning, sem dado pessoal e sem inventar fonte",
           font=SUB, fill="white")
    d.text((140, 660), "Davi Gravina · RM 565619", font=CORPO, fill="white")
    d.text((140, 712), "Henry Andrade Browne · RM 562089", font=CORPO, fill="white")
    d.text((140, 764), "Luiz Felipe dos Santos Tragi · RM 565009", font=CORPO, fill="white")
    d.text((140, 900), "FIAP · Global Solution 2026.2 · Processamento de Linguagem Natural, Chatbots & Virtual Agents",
           font=PEQ, fill=(190, 220, 232))
    return img


def slide_topicos(n, titulo, topicos, destaque=None):
    img, d = base(titulo, n)
    y = 200
    for t in topicos:
        d.ellipse([90, y + 16, 106, y + 32], fill=AZUL)
        y = bloco(d, 130, y, 1680, t) + 28
    if destaque:
        caixa(d, 80, 860, 1840, 990, cor=VERDE, fundo=(232, 245, 238))
        d.text((120, 898), destaque, font=NEG, fill=VERDE)
    return img


def slide_pipeline(n):
    img, d = base("Pipeline: 7 etapas, tudo local e sem chave de API", n)
    etapas = [("Upload", "TXT · MD · HTML\nDOCX · PDF"), ("Limpeza", "revogados, notas,\nsite, Unicode"),
              ("Anonimização", "LGPD: CPF, nome,\ntelefone, e-mail…"), ("Chunking", "artigo · seção\n· parágrafo"),
              ("Geração", "automática +\ngabarito curado"), ("Auditoria", "10 testes\n(bloqueia saída)"),
              ("Avaliação", "busca sem LLM\n+ LoRA (bônus)")]
    x, y, w, h = 70, 330, 232, 300
    for i, (t, s) in enumerate(etapas):
        x0 = x + i * (w + 28)
        d.rounded_rectangle([x0, y, x0 + w, y + h], 20, fill="white", outline=AZUL, width=3)
        d.rounded_rectangle([x0, y, x0 + w, y + 80], 20, fill=AZUL)
        d.rectangle([x0, y + 50, x0 + w, y + 80], fill=AZUL)
        tw = d.textlength(t, font=fonte("segoeuib.ttf", 30))
        d.text((x0 + (w - tw) / 2, y + 22), t, font=fonte("segoeuib.ttf", 30), fill="white")
        for k, ln in enumerate(s.split("\n")):
            lw = d.textlength(ln, font=PEQ)
            d.text((x0 + (w - lw) / 2, y + 130 + k * 40), ln, font=PEQ, fill=TEXTO)
        if i < len(etapas) - 1:
            d.polygon([(x0 + w + 6, y + h / 2 - 12), (x0 + w + 22, y + h / 2), (x0 + w + 6, y + h / 2 + 12)], fill=AZUL)
    caixa(d, 160, 740, 1760, 880, cor=AZUL, fundo=AZUL_CLARO)
    d.text((210, 770), "Saída: corpus_texto_puro · corpus_conversacional · corpus_perguntas_respostas",
           font=fonte("segoeuib.ttf", 32), fill=AZUL)
    d.text((210, 822), "+ corpus_referencia (RAG) e conjunto_teste (avaliação)", font=CORPO, fill=TEXTO)
    return img


def slide_antes_depois(n, titulo, antes, depois, nota=None):
    img, d = base(titulo, n)
    caixa(d, 70, 200, 940, 900, "ANTES", cor=VERMELHO)
    caixa(d, 980, 200, 1850, 900, "DEPOIS", cor=VERDE)
    for x, txt in ((100, antes), (1010, depois)):
        y = 250
        for ln in txt.splitlines():
            for sub in quebrar(d, ln, MONO_P, 810):
                if y > 860:
                    break
                d.text((x, y), sub, font=MONO_P, fill=TEXTO)
                y += 34
    if nota:
        d.text((80, 930), nota, font=SUB, fill=AZUL)
    return img


def slide_chat(n, titulo, turnos, nota=None, max_linhas=4):
    img, d = base(titulo, n)
    y = 165
    chat = fonte("segoeui.ttf", 31)
    for papel, txt in turnos:
        usuario = papel == "user"
        x0, x1 = (80, 1360) if usuario else (560, 1840)
        linhas = quebrar(d, txt, chat, x1 - x0 - 60)[:max_linhas]
        h = 62 + len(linhas) * 40
        cor = (234, 240, 245) if usuario else (232, 245, 238)
        d.rounded_rectangle([x0, y, x1, y + h], 22, fill=cor, outline=AZUL if usuario else VERDE, width=2)
        d.text((x0 + 30, y + 12), "Cidadão" if usuario else "CidadãoBot", font=fonte("segoeuib.ttf", 26),
               fill=AZUL if usuario else VERDE)
        for k, ln in enumerate(linhas):
            d.text((x0 + 30, y + 48 + k * 40), ln, font=chat, fill=TEXTO)
        y += h + 18
    if nota:
        d.text((80, max(y + 4, H - 110)), nota, font=PEQ, fill=CINZA)
    return img


def slide_tabela(n, titulo, cab, linhas, destaque_linha=None, nota=None):
    img, d = base(titulo, n)
    larg = [int(1760 * p) for p in cab[1]]
    x0, y = 80, 230
    d.rectangle([x0, y, x0 + sum(larg), y + 70], fill=AZUL)
    x = x0
    for c, w in zip(cab[0], larg):
        d.text((x + 18, y + 16), c, font=fonte("segoeuib.ttf", 30), fill="white")
        x += w
    y += 70
    for i, ln in enumerate(linhas):
        fundo = (232, 245, 238) if i == destaque_linha else ("white" if i % 2 == 0 else (242, 246, 249))
        d.rectangle([x0, y, x0 + sum(larg), y + 78], fill=fundo, outline=(210, 220, 228))
        x = x0
        for c, w in zip(ln, larg):
            d.text((x + 18, y + 20), str(c), font=NEG if i == destaque_linha else CORPO, fill=TEXTO)
            x += w
        y += 78
    if nota:
        bloco(d, 80, y + 50, 1760, nota, f=SUB, cor=AZUL)
    return img


def slide_tela(n, titulo, arquivo, legenda):
    img, d = base(titulo, n)
    tela = Image.open(TELAS / arquivo).convert("RGB")
    caixa_w, caixa_h = 1640, 800
    tela.thumbnail((caixa_w, caixa_h - 70))
    x = (W - tela.width) // 2
    d.rounded_rectangle([x - 8, 152, x + tela.width + 8, 160 + tela.height + 8], 10, fill=(200, 210, 218))
    img.paste(tela, (x, 160))
    bloco(d, 80, 160 + tela.height + 30, 1760, legenda, f=SUB, cor=AZUL, maxl=2)
    return img


# ------------------------------------------------------------------ dados reais
def ler(nome):
    return [json.loads(l) for l in (RAIZ / "saida" / f"{nome}.jsonl").read_text(encoding="utf-8").splitlines()]


def pergunta(conteudo):
    return conteudo.split("PERGUNTA:")[-1].strip()


def dados_reais():
    import pymupdf
    from fabrica.anonimizacao import anonimizar
    from fabrica.leitores import ler_arquivo
    from fabrica.limpeza import limpar

    pdf = RAIZ / "dados/exemplos_upload/decreto_hortas_comunitarias.pdf"
    with pymupdf.open(pdf) as doc:
        bruto_pdf = doc[0].get_text().strip() + "\n" + doc[1].get_text().strip()[:200]
    lido_pdf = ler_arquivo(pdf)

    lei = (RAIZ / "dados/brutos/lei_13460_2017_usuario_servico_publico.txt").read_text(encoding="utf-8")
    i = lei.find("Art. 10-A")
    lei_antes = lei[i:i + 520]
    limpo, _ = limpar(lei)
    j = limpo.find("Art. 10-A")
    lei_depois = limpo[j:j + 420]

    guia = (RAIZ / "dados/brutos/documento_teste_ficticio_guia_vila_esperanca.txt").read_text(encoding="utf-8")
    gl, _ = limpar(guia, lei=False)
    ga, _ = anonimizar(gl)
    k, k2 = gl.find("A cidadã"), ga.find("A cidadã")
    w1, w2 = gl.find("[10:02]"), ga.find("[10:02]")
    linha = lambda t, i: t[i:t.find("\n", i)]
    anon_antes = gl[k:k + 330] + "\n\n" + linha(gl, w1)
    anon_depois = ga[k2:k2 + 230] + "\n\n" + linha(ga, w2)

    docx = RAIZ / "dados/exemplos_upload/cartilha_coleta_seletiva.docx"
    bruto_docx = ler_arquivo(docx)
    docx_bruto = "…\n" + bruto_docx[bruto_docx.find("~~"):bruto_docx.find("## Descarte")] + "…\n" + \
        bruto_docx[bruto_docx.find("## Pilhas"):]

    qa = ler("corpus_perguntas_respostas")
    auto = next(e for e in qa if e["meta"]["item"] == "auto_decreto_hortas#art2_R2_lista")
    conv = ler("corpus_conversacional")
    urg = next(e for e in conv if "urg_enchente" in e["meta"].get("itens", []))
    tp = next(r for r in ler("corpus_texto_puro") if r["meta"]["doc_id"] == "coleta_seletiva")
    t = tp["text"]
    tp_json = ('{"text": "…secos.\n' + t[t.find("Descarte de móveis"):t.find("Descarte de móveis") + 1].replace("D", "…\n")
               + t[t.find("Pilhas, baterias e"):] + '",\n "meta": {"id": "' + tp["meta"]["id"]
               + '", "formato_original": "docx"}}')

    rel = json.loads((RAIZ / "saida/relatorio_execucao.json").read_text(encoding="utf-8"))
    lora = json.loads((RAIZ / "notebook/resultados_lora_local/resultados_lora.json").read_text(encoding="utf-8"))
    return locals()


# ------------------------------------------------------------------ roteiro (cena = slide + narração)
def cenas(D):
    pct = lambda v: f"{v:.0%}".replace(".", ",")
    s = D["rel"]["avaliacao_linha_de_base"]["sistemas"]
    bm, hib = s["BM25 (linha de base)"]["teste"], s["Híbrida: expansão + n-gramas + RRF"]["teste"]
    br = lambda v: f"{v:.3f}".replace(".", ",")
    msgs_auto = D["auto"]["messages"]
    turnos_urg = [(m["role"], pergunta(m["content"]) if m["role"] == "user" else m["content"])
                  for m in D["urg"]["messages"][1:]]
    return [
        (lambda n: slide_titulo(n),
         "Olá! Somos Davi Gravina, Henry Andrade Browne e Luiz Felipe dos Santos Tragi. "
         "Este é o nosso projeto de Processamento de Linguagem Natural da Global Solution: a Fábrica de Corpus CitizenTech."),
        (lambda n: slide_topicos(n, "O desafio da disciplina", [
            "Uma ferramenta para subir diversos tipos de documentos e textos",
            "Limpeza e normalização dos dados",
            "Três corpus para fine-tuning de uma LLM pequena: conversacional, perguntas e respostas e texto puro",
            "Nosso tema CitizenTech: leis federais (CDC, LAI, LGPD, Lei 13.460) e orientações de uma prefeitura"],
            destaque="Regra do projeto: forma se treina, fato se consulta."),
         "O desafio pede uma ferramenta que receba vários tipos de documentos, faça a limpeza e a normalização, "
         "e gere três corpus, conversacional, perguntas e respostas e texto puro, para o fine-tuning de uma LLM pequena. "
         "Nosso tema é o cidadão: leis federais e orientações de uma prefeitura. "
         "A regra que guiou tudo foi: forma se treina, fato se consulta."),
        (lambda n: slide_pipeline(n),
         "O pipeline tem sete etapas: upload, limpeza e normalização, anonimização pela LGPD, chunking, "
         "geração dos corpus, auditoria e avaliação. Tudo roda localmente, sem chave de API, "
         "pela interface ou pela linha de comando."),
        (lambda n: slide_tela(n, "Interface: upload de vários formatos", "01_inicio.png",
                              "Streamlit: envie TXT, Markdown, HTML, Word ou PDF. Os arquivos ficam nesta máquina."),
         "Esta é a interface, feita em Streamlit. Dá para enviar arquivos TXT, Markdown, HTML, Word e PDF. "
         "Na demonstração usamos o acervo base, com quatro leis federais, e quatro documentos fictícios, um em cada formato."),
        (lambda n: slide_antes_depois(n, "Leitor de PDF: normalização do texto extraído", D["bruto_pdf"], D["lido_pdf"][:900],
                                      "Saem o cabeçalho e a \"Página X de Y\" repetidos; \"ali- / mentos\" volta a ser \"alimentos\"."),
         "Cada formato tem um leitor. No PDF, o cabeçalho do Diário Oficial e a numeração de página, "
         "que se repetem em todas as páginas, são removidos, e as palavras hifenizadas na quebra de linha são juntadas. "
         "No HTML saem o menu e o rodapé, e no Word os títulos e o texto tachado são lidos direto do arquivo."),
        (lambda n: slide_antes_depois(n, "Limpeza: o texto da lei sem o ruído da coleta", D["lei_antes"], D["lei_depois"],
                                      "Removidos: trechos revogados, notas de alteração, assinaturas e navegação do site."),
         "Depois vem a limpeza. Trechos revogados, notas como incluído pela lei, assinaturas e o ruído do site saem, "
         "e o texto é normalizado. O conteúdo da lei não muda."),
        (lambda n: slide_antes_depois(n, "LGPD: nenhum dado pessoal real no corpus", D["anon_antes"], D["anon_depois"],
                                      "30 substituições em 5 documentos · dados de teste inventados (CPF inválido, example.com)"),
         "Nenhum dado pessoal pode entrar no corpus. Os documentos de teste têm dados inventados, e a anonimização "
         "troca CPF, telefone, e-mail, endereço e nomes por etiquetas, inclusive nomes escritos em minúsculas, "
         "como numa conversa de WhatsApp. Foram trinta substituições em cinco documentos."),
        (lambda n: slide_tela(n, "Gerar corpus: os três arquivos", "02_resultado.png",
                              "14 textos puros · 103 conversas · 336 perguntas e respostas · auditoria OK"),
         "Ao clicar em gerar corpus, a fábrica produz os três arquivos: catorze registros de texto puro, "
         "cento e três conversas e trezentos e trinta e seis pares de perguntas e respostas."),
        (lambda n: slide_chat(n, "Perguntas e respostas geradas automaticamente (decreto em PDF)",
                              [("user", "[CONTEXTO: fonte certa + distrator] " + pergunta(msgs_auto[1]["content"])),
                               ("assistant", msgs_auto[2]["content"])],
                              "Resposta extrativa: copia o trecho literal e cita a fonte. 171 itens automáticos + 165 curados à mão.",
                              max_linhas=9),
         "As perguntas e respostas são geradas automaticamente para qualquer documento, por regras sobre a estrutura do texto: "
         "artigos, listas, definições, prazos e seções. A resposta copia o trecho literal, então é fiel por construção, "
         "e sempre cita a fonte. Um gabarito escrito à mão completa o corpus "
         "com respostas em linguagem simples, recusas e urgências."),
        (lambda n: slide_chat(n, "Conversacional: urgência no meio da conversa", turnos_urg,
                              "54 diálogos com várias trocas · o modelo não pode \"embalar\" no assunto anterior."),
         "O corpus conversacional tem diálogos de várias trocas. Neste, o cidadão pergunta sobre a LGPD e, de repente, "
         "relata uma rachadura enorme na parede de casa. O assistente não continua no assunto anterior: "
         "manda procurar um lugar seguro e ligar para a Defesa Civil, no um nove nove."),
        (lambda n: slide_antes_depois(n, "Texto puro: do Word ao registro de pré-treino", D["docx_bruto"],
                                      D["tp_json"], "Revogado (~~tachado~~) removido · contato anonimizado · formato {\"text\": ...}"),
         "O corpus de texto puro guarda cada documento limpo e anonimizado, em partes de até seiscentas palavras, "
         "no formato usado para pré-treino continuado. Neste exemplo, vindo de um arquivo do Word, "
         "a frase revogada sumiu e o contato da coordenadora virou etiqueta."),
        (lambda n: slide_tela(n, "Auditoria automática: 10 testes, 10 aprovados", "03_auditoria.png",
                              "Se algum teste falha, os downloads ficam bloqueados."),
         "No fim roda uma auditoria com dez testes, de dado pessoal a vazamento entre treino e teste. "
         "Se algum falha, os downloads ficam bloqueados. Ela pegou dois problemas reais: um nome que escapava "
         "da anonimização, e respostas que citavam uma fonte que o modelo nunca tinha recebido."),
        (lambda n: slide_tabela(n, "Avaliação sem LLM no conjunto de teste (43 perguntas)",
                                (["Busca", "hit@1", "hit@3", "MRR", "Comportamento", "Urgências"],
                                 [0.36, 0.11, 0.11, 0.11, 0.18, 0.13]),
                                [["BM25 (linha de base)", br(bm["hit@1"]), br(bm["hit@3"]), br(bm["MRR"]),
                                  br(bm["acuracia_comportamento"]), bm["urgencias_encaminhadas"]],
                                 ["Híbrida: expansão + n-gramas + RRF", br(hib["hit@1"]), br(hib["hit@3"]), br(hib["MRR"]),
                                  br(hib["acuracia_comportamento"]), hib["urgencias_encaminhadas"]]],
                                destaque_linha=1,
                                nota="Variante, limiar e sinônimos escolhidos só no treino; o teste fica congelado."),
         "Para ter uma régua antes de treinar, medimos um sistema sem LLM, com regras e busca. "
         "A nossa busca híbrida põe o trecho certo entre os três primeiros em oitenta e seis por cento das perguntas de teste, "
         "e encaminha todas as sete urgências."),
        (lambda n: slide_tabela(n, "Bônus: LoRA no Qwen2.5-0.5B (treino reduzido local)",
                                (["Configuração", "Cita a fonte", "Urgências", "Recusa correta", "Tokens do system"],
                                 [0.34, 0.17, 0.14, 0.17, 0.18]),
                                [[r["config"], pct(r["cita_fonte"]), r["urgencias_encaminhadas"], r["recusa_correta"],
                                  r["tokens_system"]] for r in D["lora"]["resultados"]],
                                destaque_linha=2,
                                nota="Nenhuma configuração resolve as urgências: por isso elas são tratadas por regra antes do modelo."),
         "No bônus, um LoRA no Qwen de meio bilhão de parâmetros, mesmo num treino reduzido, passou a citar a fonte "
         "em oitenta e seis por cento das respostas, contra cinquenta e nove do prompt longo, com um prompt de oito tokens. "
         "Mas nenhuma configuração acertou as urgências, o que confirma a decisão: urgência é regra antes do modelo."),
        (lambda n: slide_topicos(n, "Resumo e onde encontrar", [
            "5 formatos de entrada · limpeza e normalização · anonimização LGPD",
            "3 corpus: texto puro (14) · conversacional (103) · perguntas e respostas (336)",
            "Auditoria 10/10 · fidelidade por construção · urgências por regra",
            "Código, corpus, notebooks e relatório: github.com/Tragl56/fabrica-corpus-citizentech"],
            destaque="Obrigado!"),
         "O código, os corpus, os notebooks e o relatório estão no GitHub. Obrigado!"),
    ]


# ------------------------------------------------------------------ narração e montagem
def falar(texto, wav):
    ps = TMP / "falar.ps1"
    ps.write_text(
        "Add-Type -AssemblyName System.Speech\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "$s.SelectVoice('Microsoft Maria Desktop')\n"
        "$s.Rate = 2\n"
        f"$s.SetOutputToWaveFile('{wav}')\n"
        f"$s.Speak([IO.File]::ReadAllText('{wav.with_suffix('.txt')}', [Text.Encoding]::UTF8))\n"
        "$s.Dispose()\n", encoding="utf-8-sig")
    wav.with_suffix(".txt").write_text(texto, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps)], check=True)
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


def ts(seg):
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def legendas(texto, inicio, dur):
    """Divide a narração da cena em frases e distribui o tempo proporcionalmente ao tamanho."""
    frases = []
    for f in (f.strip() for f in re.split(r"(?<=[.!?:])\s+", texto) if f.strip()):
        if frases and len(frases[-1]) < 25:      # junta frases muito curtas ("Olá!") com a seguinte
            frases[-1] += " " + f
        else:
            frases.append(f)
    total = sum(len(f) for f in frases)
    out, t = [], inicio
    for f in frases:
        d = dur * len(f) / total
        out.append((t, t + d, f))
        t += d
    return out


def main():
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    TMP.mkdir(exist_ok=True)
    D = dados_reais()
    srt, t0, segmentos = [], 0.0, []
    for n, (fazer_slide, narracao) in enumerate(cenas(D), 1):
        png, wav, mp4 = TMP / f"c{n:02d}.png", TMP / f"c{n:02d}.wav", TMP / f"c{n:02d}.mp4"
        fazer_slide(n).save(png)
        dur_fala = falar(narracao, wav)
        dur = dur_fala + 0.6                       # respiro entre cenas
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(png),
                        "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,adelay=300|300,apad",
                        "-t", f"{dur:.2f}",
                        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
                        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(mp4)], check=True)
        srt += legendas(narracao, t0 + 0.3, dur_fala)
        segmentos.append(mp4)
        t0 += dur
        print(f"cena {n:02d}: {dur:5.1f} s  (total {t0:5.1f} s)")
    lista = TMP / "lista.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in segmentos), encoding="utf-8")
    srt_path = SAIDA_MP4.with_suffix(".srt")
    srt_path.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(srt, 1)),
                        encoding="utf-8")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-i", str(srt_path), "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
                    "-metadata:s:s:0", "language=por", "-movflags", "+faststart", str(SAIDA_MP4)], check=True)
    print(f"\n{SAIDA_MP4.name}: {t0 / 60:.1f} min · legendas: {srt_path.name}")


if __name__ == "__main__":
    main()
