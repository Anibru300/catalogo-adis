# -*- coding: utf-8 -*-
"""Inspeccionar estado del panel tras login: token, apiGet, tabla."""
import sys, time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/admin.html"
with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    msgs = []
    page.on("console", lambda m: msgs.append(m.text[:150]))
    page.goto(URL, wait_until="domcontentloaded")
    page.fill("#loginUser", "Adis")
    page.fill("#loginPass", "Adisdiseño2026")
    page.press("#loginPass", "Enter")
    time.sleep(6)
    estado = page.evaluate("""(async () => {
      const tok = sessionStorage.getItem('adis_admin_token');
      let r = null, err = null;
      try { r = await apiGet('productos'); } catch (e) { err = String(e); }
      return {token: tok, resp: r ? (r.ok ? 'ok ' + (r.productos||[]).length : JSON.stringify(r.error)) : null,
              err, invTable: document.getElementById('invTable').textContent.slice(0,60),
              loginVisible: getComputedStyle(document.getElementById('loginView')).display};
    })()""")
    print("token:", (estado["token"] or "")[:12], "...")
    print("apiGet productos:", estado["resp"], "| err:", estado["err"])
    print("invTable:", estado["invTable"])
    print("loginVisible:", estado["loginVisible"])
    print("avisos:", [m for m in msgs if 'error' in m.lower() or 'token' in m.lower()][:4])
    page.screenshot(path=r"C:\Users\Carlos\Desktop\Pagina\capturas de pantalla de inventario\diag_panel.png")
    b.close()
