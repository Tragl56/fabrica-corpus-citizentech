"""Captura telas reais da interface (app.py) em 1920x1080 com o Edge instalado, via Playwright.

Pré-requisito: o app rodando em http://localhost:8517  (streamlit run app.py --server.port 8517)
    python relatorio/video/capturar_telas.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8517"
PASTA = Path(__file__).parent / "telas"
PASTA.mkdir(exist_ok=True)


def foto(page, nome):
    page.wait_for_timeout(1200)
    page.screenshot(path=str(PASTA / f"{nome}.png"))
    print("ok", nome)


with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge", headless=True)
    page = nav.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1.2, color_scheme="light")
    page.goto(URL)
    page.get_by_text("Gerar corpus").first.wait_for(timeout=60000)
    foto(page, "01_inicio")

    page.get_by_text("Incluir exemplos de upload").click()
    page.wait_for_timeout(800)
    page.get_by_role("button", name="Gerar corpus").click()
    page.get_by_text("Concluído").wait_for(timeout=120000)
    page.wait_for_timeout(1500)
    foto(page, "02_resultado")

    page.get_by_text("Auditoria (PII, fidelidade").click()
    page.wait_for_timeout(800)
    page.get_by_text("Auditoria (PII, fidelidade").scroll_into_view_if_needed()
    page.mouse.wheel(0, 200)
    foto(page, "03_auditoria")
    page.get_by_text("Auditoria (PII, fidelidade").click()

    page.get_by_text("Documentos processados").click()
    page.wait_for_timeout(800)
    page.get_by_text("Documentos processados").scroll_into_view_if_needed()
    foto(page, "04_documentos")
    page.get_by_text("Documentos processados").click()

    # Aba Conversacional (1º diálogo do tipo padrão), só clicando na aba
    page.get_by_role("tab", name="Conversacional").click()
    page.wait_for_timeout(1500)
    page.get_by_text("Revise antes de treinar").scroll_into_view_if_needed()
    page.mouse.wheel(0, 380)
    foto(page, "05_conversacional")
    nav.close()
