# -*- coding: utf-8 -*-
"""Prueba funcional: Cotizador (sec. 03 sin desglose) + pestaña Flujo del panel admin.
Simula el backend de Apps Script con fetch stub vía playwright."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PUBLIC = Path(__file__).resolve().parent.parent.parent / "public"
ADMIN = PUBLIC / "admin.html"

VISITAS = [
    {"fecha": "2026-09-01", "hora": "10:12", "pagina": "/index.html", "seccion": "",
     "origen": "Google", "referrer": "https://www.google.com/", "idioma": "es",
     "dispositivo": "Móvil", "navegador": "Chrome", "ancho": "390", "ua": "x"},
    {"fecha": "2026-09-01", "hora": "10:13", "pagina": "/index.html", "seccion": "productos-destacados",
     "origen": "Google", "referrer": "https://www.google.com/", "idioma": "es",
     "dispositivo": "Móvil", "navegador": "Chrome", "ancho": "390", "ua": "x"},
    {"fecha": "2026-09-02", "hora": "11:00", "pagina": "/2-lambrin-wpc.html", "seccion": "",
     "origen": "Facebook", "referrer": "https://www.facebook.com/", "idioma": "es",
     "dispositivo": "Escritorio", "navegador": "Firefox", "ancho": "1366", "ua": "x"},
    {"fecha": "2026-09-04", "hora": "09:30", "pagina": "/contacto.html", "seccion": "",
     "origen": "Directo / sin dato", "referrer": "", "idioma": "en",
     "dispositivo": "Móvil", "navegador": "Safari", "ancho": "375", "ua": "x"},
]

STUB = """
(body) => {
  const data = typeof body === 'string' ? JSON.parse(body) : (body && body.tipo ? body : {});
  const t = data.tipo || '';
  if (t === 'login') return Promise.resolve(new Response(JSON.stringify({ok:true, token:'TEST'}), {status:200}));
  if (t === 'track') return Promise.resolve(new Response(JSON.stringify({ok:true}), {status:200}));
  return Promise.resolve(new Response(JSON.stringify({ok:false, error:'stub'}), {status:200}));
}
"""

errores = []
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.on("pageerror", lambda e: errores.append(f"pageerror: {e}"))
    def _cons(m):
        if m.type == "error" and 'URL scheme "file" is not supported' not in m.text:
            errores.append(f"console.error: {m.text}")
    page.on("console", _cons)

    # Stub GET y POST antes de cargar
    page.route("**/macros/**", lambda route: route.fulfill(
        json={"ok": True, "visitas": VISITAS},
        headers={"Access-Control-Allow-Origin": "*"}))
    page.route("**/*exec", lambda route: route.fulfill(
        json={"ok": True, "visitas": VISITAS}))

    page.goto(ADMIN.as_uri())
    page.evaluate(f"""() => {{ window.__origFetch = window.fetch;
      window.fetch = (url, opts) => {{
        const u = String(url);
        if (u.indexOf('action=') !== -1) {{
          const acc = (u.match(/action=([a-z_]+)/)||[])[1];
          const resp = {{ok:true, token:'TEST', usuario:'Adis'}};
          if (acc === 'visitas') resp.visitas = {json.dumps(VISITAS)};
          if (acc === 'productos') resp.productos = [];
          if (acc === 'config') resp.moneda_base='MXN', resp.tipo_cambio='18.5';
          if (acc === 'quotes') resp.quotes = [];
          if (acc === 'leads') resp.leads = [];
          if (acc === 'reviews_admin') resp.reviews = [];
          if (acc === 'almacenes') resp.almacenes = [];
          if (acc === 'stock') resp.stock = [];
          if (acc === 'movimientos') resp.movimientos = [];
          if (acc === 'ventas') resp.ventas = [];
          if (acc === 'gastos') resp.gastos = [];
          return Promise.resolve(new Response(JSON.stringify(resp), {{status:200}}));
        }}
        if (opts && opts.method === 'POST') {{
          const data = JSON.parse(opts.body);
          if (data.tipo === 'login') return Promise.resolve(new Response(JSON.stringify({{ok:true, token:'TEST'}}), {{status:200}}));
          return Promise.resolve(new Response(JSON.stringify({{ok:true}}), {{status:200}}));
        }}
        return window.__origFetch(url, opts);
      }};
    }}""")

    # Login
    page.fill("#loginUser", "Adis")
    page.fill("#loginPass", "Adisdiseño2026")
    page.click("button[type=submit], #loginView .btn-solid, #loginView button")
    page.wait_for_timeout(800)

    # ---- 1. Cotizador: sec. 03 sin desglose ----
    page.click("[data-tab=proposal]")
    page.wait_for_timeout(400)
    page.fill("#pCliente", "Cliente de Prueba")
    page.click("text=＋ Agregar partida")
    page.wait_for_timeout(200)
    fila = page.locator("#pItems tr").first
    fila.locator("td").nth(1).locator("input").fill("Placa PVC mármol Carrara")
    fila.locator("td").nth(2).locator("input").fill("2")
    fila.locator("td").nth(4).locator("input").fill("850")
    page.wait_for_timeout(400)

    preview = page.inner_html("#propPreview")
    assert "03 · INVERSIÓN TOTAL DEL PROYECTO" in preview, "Falta título sec. 03"
    assert "DESGLOSE" not in preview, "Todavía aparece DESGLOSE"
    assert "P. UNITARIO" not in preview, "Todavía aparece tabla de partidas"
    assert "SUBTOTAL" not in preview, "Todavía aparece subtotal"
    assert "$1,972.00 MXN" in preview, f"Total incorrecto: {preview[preview.find('03 ·'):preview.find('03 ·')+600]}"
    print("✅ Cotizador sec.03: solo inversión total ($1,972.00 MXN), sin desglose")

    # ---- 2. Pestaña Flujo ----
    page.click("[data-tab=flow]")
    page.wait_for_timeout(800)
    kpis = page.inner_text("#flowKpis").lower()
    assert "visitas a páginas" in kpis and "página más vista" in kpis, kpis
    assert "apartados vistos" in kpis
    origen = page.inner_text("#flowOrigen")
    assert "Google" in origen and "Facebook" in origen, origen
    disp = page.inner_text("#flowDisp")
    assert "Móvil" in disp, disp
    secc = page.inner_text("#flowSecciones")
    assert "productos-destacados" in secc, secc
    tabla = page.inner_text("#flowTabla")
    assert "lambrin-wpc" in tabla, tabla
    print("✅ Flujo: KPIs, origen, dispositivos, apartados y tabla OK")
    page.screenshot(path="screenshots/check_flujo_tab.png", full_page=False)
    page.click("[data-tab=proposal]")
    page.screenshot(path="screenshots/check_cotizador_sec03.png", full_page=False)

    # ---- 3. Página pública: tracker presente y sin errores JS ----
    page2 = browser.new_page()
    page2.on("pageerror", lambda e: errores.append(f"public pageerror: {e}"))
    page2.goto((PUBLIC / "index.html").as_uri())
    page2.wait_for_timeout(1200)
    ok = page2.evaluate("() => sessionStorage.getItem('adis_trk_sess') !== null")
    print(("✅" if ok else "⚠️") + f" Tracker en página pública (sessionStorage marcado: {ok})")

    browser.close()

if errores:
    print("\n⚠️ ERRORES JS:")
    for e in errores[:10]:
        print("  -", e)
    sys.exit(1)
print("\n🎉 Todo verificado sin errores JS")
