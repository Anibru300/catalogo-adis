# -*- coding: utf-8 -*-
"""Smoke test del dashboard nativo de Estadisticas (tab analytics).

Requiere: servidor local en public/ (python -m http.server 8000).

Verifica:
  1. El tab analytics carga KPIs y 5 graficas Chart.js.
  2. Los canvas tienen contenido dibujado (no estan vacios).
  3. 0 errores JS al abrir el tab.

Salida: captura en screenshots/ y PASS/FAIL por chequeo.
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[2]
URL = "http://localhost:8000/admin.html"
DEST = BASE / "screenshots"
DEST.mkdir(exist_ok=True)

resultados = []
errors = []


def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok))
    print(("PASS " if ok else "FAIL ") + nombre + (f" — {detalle}" if detalle else ""))


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="domcontentloaded")
    page.fill("#loginUser", "Adis")
    page.fill("#loginPass", "Adisdiseño2026")
    page.press("#loginPass", "Enter")
    page.wait_for_function("getComputedStyle(document.getElementById('loginView')).display==='none'", timeout=30000)

    page.evaluate("typeof showTab==='function' && showTab('analytics')")
    page.wait_for_function("document.querySelectorAll('#estKpis .pnl-card').length >= 3", timeout=45000)

    check("KPIs cargados", page.evaluate("document.querySelectorAll('#estKpis .pnl-card').length") >= 3,
          f"{page.evaluate('document.querySelectorAll(\'#estKpis .pnl-card\').length')} tarjetas")
    canvases = ["estVisitasLine", "estOrigenDough", "estVentasBar", "estGastosBar", "estFlujoBar"]
    for cid in canvases:
        try:
            page.wait_for_function(f"window.Chart && !!Chart.getChart('{cid}')", timeout=45000)
            check(f"grafica {cid}", True)
        except Exception:
            check(f"grafica {cid}", False)
    if not errors:
        pixels = page.evaluate("""() => {
          const c = document.getElementById('estVisitasLine');
          const ctx = c.getContext('2d');
          const d = ctx.getImageData(0, 0, c.width, c.height).data;
          let n = 0;
          for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
          return n;
        }""")
        check("linea de visitas dibujada (pixeles > 0)", pixels > 1000, f"{pixels} px")
    page.screenshot(path=str(DEST / "check_estadisticas.png"), full_page=True)
    b.close()

check("0 errores JS", len(errors) == 0, "; ".join(errors[:3]))

fallos = [n for n, ok in resultados if not ok]
print()
print(f"TOTAL: {len(resultados) - len(fallos)}/{len(resultados)} PASS")
sys.exit(1 if fallos else 0)
