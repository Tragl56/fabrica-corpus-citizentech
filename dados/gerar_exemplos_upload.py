"""Gera dados/exemplos_upload/: documentos FICTÍCIOS em 4 formatos (.docx, .html, .pdf, .md)
para demonstrar que a fábrica aceita "diversos tipos de documentos".

Cada um traz o ruído típico do formato (menu/rodapé de site, cabeçalho repetido em PDF,
hifenização, trecho tachado = revogado) e dados pessoais INVENTADOS (CPF com dígito
verificador inválido, e-mail em example.com) para testar a anonimização.
Requer pymupdf só para gerar o PDF:  python dados/gerar_exemplos_upload.py
"""
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

PASTA = Path(__file__).parent / "exemplos_upload"
ORGAO = "Prefeitura Municipal de Vila Esperança (fictícia)"
META = {"orgao_emissor": ORGAO, "licenca": "Documento fictício criado pelo grupo para teste",
        "ficticio": True, "data_publicacao": "2026-10-01", "data_coleta": "2026-11-10"}

# Dados pessoais inventados presentes nos exemplos (a auditoria verifica que nenhum sobra).
PII_EXEMPLOS = ["Ana Beatriz Moura", "(11) 97654-3210", "ana.moura@example.com", "Rua dos Ipês, 88",
                "Roberto Alves Nunes", "321.654.987-00", "Sebastião Ferreira", "(11) 3456-7890",
                "Luzia Campos", "luzia.campos@example.com"]


# ------------------------------------------------------------------ DOCX
def _docx(caminho: Path, paragrafos: list[tuple[str, str]]):
    """paragrafos: (estilo, texto); estilo 'h' = título, 'p' = normal, 's' = tachado (revogado)."""
    corpo = []
    for estilo, texto in paragrafos:
        ppr = '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>' if estilo == "h" else ""
        rpr = "<w:rPr><w:strike/></w:rPr>" if estilo == "s" else ""
        corpo.append(f'<w:p>{ppr}<w:r>{rpr}<w:t xml:space="preserve">{escape(texto)}</w:t></w:r></w:p>')
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(corpo) + "</w:body></w:document>")
    tipos = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", tipos)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)


COLETA = [
    ("p", "Cartilha da Coleta Seletiva de Vila Esperança"),
    ("h", "Dias de coleta"),
    ("p", "A coleta de lixo comum passa três vezes por semana em todos os bairros: segunda, quarta e sexta-feira, a partir das 7 horas."),
    ("p", "A coleta seletiva de recicláveis passa uma vez por semana, às terças-feiras. Separe papel, plástico, metal e vidro limpos e secos."),
    ("s", "A coleta seletiva acontecia aos sábados."),
    ("h", "Descarte de móveis e entulho"),
    ("p", "Móveis velhos, colchões e entulho de pequenas reformas não podem ser deixados na calçada. Agende a retirada gratuita pelo telefone 156 ou leve ao Ecoponto do bairro, aberto de segunda a sábado, das 8 às 17 horas."),
    ("p", "O descarte irregular de entulho em terrenos ou vias públicas pode gerar multa, conforme o Código de Posturas do município."),
    ("h", "Pilhas, baterias e eletrônicos"),
    ("p", "Pilhas, baterias, lâmpadas e eletrônicos não devem ir para o lixo comum. Leve aos pontos de entrega voluntária nas Unidades Básicas de Saúde e nos Ecopontos."),
    ("h", "Contato da equipe responsável"),
    ("p", "Coordenadora da campanha: Ana Beatriz Moura, telefone (11) 97654-3210, e-mail ana.moura@example.com, atendimento na Rua dos Ipês, 88."),
]

HTML = """<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><title>Tarifa social da água</title>
<script>window.dataLayer = []; function gtag(){}</script><style>nav{color:red}</style></head><body>
<header><a href="/">Início</a> | <a href="/servicos">Serviços</a> | Acessibilidade | Alto contraste</header>
<nav><ul><li>Saúde</li><li>Educação</li><li>Ouvidoria</li></ul></nav>
<main>
<h1>Tarifa Social da Água — Vila Esperança</h1>
<p>A Tarifa Social garante desconto de 50% na conta de água para famílias de baixa renda.</p>
<h2>Quem tem direito</h2>
<p>Têm direito as famílias inscritas no Cadastro Único com renda mensal de até meio salário mínimo por pessoa, e os moradores que recebem o Benefício de Prestação Continuada (BPC).</p>
<p><s>O desconto era de 30% até dezembro de 2025.</s></p>
<h2>Como pedir</h2>
<p>O pedido é feito no Posto de Atendimento ao Cidadão ou pelo telefone 156. Leve a conta de água mais recente, um documento com foto e o número de inscrição no Cadastro Único.</p>
<p>O desconto começa a valer na conta do mês seguinte à aprovação do pedido. A análise leva até 15 dias úteis.</p>
<h2>Renovação</h2>
<p>O benefício deve ser renovado a cada 2 anos. A família recebe um aviso na conta de água 60 dias antes do vencimento.</p>
<p>Exemplo de atendimento registrado: o morador Roberto Alves Nunes, CPF 321.654.987-00, teve o pedido aprovado em 5 dias.</p>
</main>
<footer>Prefeitura de Vila Esperança © 2026 — Todos os direitos reservados | Política de cookies | Mapa do site</footer>
</body></html>"""

DECRETO_PAGINAS = [
    """DECRETO MUNICIPAL Nº 1.234/2026 (FICTÍCIO)
Institui o Programa Hortas Comunitárias de Vila Esperança.
O PREFEITO DE VILA ESPERANÇA, no uso de suas atribuições, DECRETA:
Art. 1º Fica instituído o Programa Hortas Comunitárias, com o objetivo de incentivar a produção de ali-
mentos saudáveis, a geração de renda e o uso social de terrenos públicos sem utilização.
Art. 2º Podem participar do Programa:
I - associações de moradores e grupos com pelo menos 5 (cinco) pessoas residentes no bairro;
II - escolas públicas municipais;
III - pequenos produtores rurais do município cadastrados na Secretaria de Agricultura.""",
    """Art. 3º O pedido de participação deve ser feito na Secretaria de Agricultura, com a indicação do terreno e
a lista dos participantes.
Parágrafo único. A Secretaria responderá ao pedido no prazo de 30 (trinta) dias.
Art. 4º A Prefeitura fornecerá, sem custo, sementes, mudas, ferramentas e orientação técnica de um agrô-
nomo durante o primeiro ano de funcionamento da horta.
Art. 5º É proibido o uso de agrotóxicos nas hortas do Programa.""",
    """Art. 6º A produção poderá ser consumida pelos participantes, doada a entidades assistenciais ou vendida
em feiras livres do município, sem cobrança de taxa de banca.
Art. 7º Este Decreto entra em vigor na data de sua publicação.
Responsável técnico: Sebastião Ferreira, telefone (11) 3456-7890.""",
]

FAQ_MD = """# Transporte escolar rural — perguntas frequentes

Documento **fictício** da Secretaria de Educação de Vila Esperança.

## Quem pode usar o transporte escolar rural?

Alunos da rede pública que moram na zona rural a mais de 2 km da escola ou do ponto de ônibus urbano mais próximo têm direito ao transporte escolar gratuito.

## Como fazer a inscrição?

A inscrição é feita na secretaria da própria escola no ato da matrícula. É preciso apresentar um comprovante de endereço rural ou uma declaração da associação de produtores.

## O que fazer se o ônibus não passar?

Registre a falta na escola no mesmo dia ou na Ouvidoria pelo telefone 156. Se a rota ficar mais de 3 dias sem atendimento, a Secretaria deve oferecer transporte alternativo.

## Contato

Dúvidas sobre rotas: falar com Luzia Campos, e-mail luzia.campos@example.com.
"""


def main():
    PASTA.mkdir(exist_ok=True)
    _docx(PASTA / "cartilha_coleta_seletiva.docx", COLETA)
    (PASTA / "tarifa_social_agua.html").write_text(HTML, encoding="utf-8")
    (PASTA / "faq_transporte_escolar_rural.md").write_text(FAQ_MD, encoding="utf-8")

    import pymupdf
    pdf = pymupdf.open()
    for i, texto in enumerate(DECRETO_PAGINAS, 1):
        pg = pdf.new_page(width=595, height=842)
        pg.insert_text((50, 40), "Diário Oficial de Vila Esperança — edição fictícia", fontsize=8)
        pg.insert_textbox(pymupdf.Rect(50, 70, 545, 780), texto, fontsize=10.5, fontname="helv")
        pg.insert_text((280, 820), f"Página {i} de {len(DECRETO_PAGINAS)}", fontsize=8)
    pdf.save(PASTA / "decreto_hortas_comunitarias.pdf")

    metas = {
        "cartilha_coleta_seletiva.docx": {"doc_id": "coleta_seletiva", "tipo": "cartilha"},
        "tarifa_social_agua.html": {"doc_id": "tarifa_social_agua", "tipo": "pagina_web"},
        "decreto_hortas_comunitarias.pdf": {"doc_id": "decreto_hortas", "titulo": "Decreto Municipal nº 1.234/2026 — Programa Hortas Comunitárias (fictício)", "tipo": "lei_municipal"},
        "faq_transporte_escolar_rural.md": {"doc_id": "transporte_rural", "tipo": "faq"},
    }
    for nome, m in metas.items():
        (PASTA / f"{nome}.meta.json").write_text(json.dumps({**META, **m}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("gerados em", PASTA)


if __name__ == "__main__":
    main()
