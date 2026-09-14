# -*- coding: utf-8 -*-
"""Reparacion one-time post-redeploy del fix 70d8570.

La version pre-fix desplegada piso estado/notas/fecha_actualizacion (cols 14-16)
con foto_2..4 vacios en cada save_product. Este script:
1. login en el backend
2. POST reparar_esquema con {codigo: {estado, notas}} desde dataset_maestro.json
   (el backend solo rellena celdas VACIAS y extiende encabezados a 19 columnas)
3. verifica: 0 estados vacios, keys foto_2/3/4 presentes, Adler intacto
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BACKEND = "https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec"
MAESTRO = Path(r"C:\Users\Carlos\Desktop\Pagina\60_DATA\dataset_maestro.json")

maestro = json.loads(MAESTRO.read_text(encoding="utf-8"))
datos = {p["codigo"]: {"estado": p.get("estado") or "activo", "notas": p.get("notas") or ""}
         for p in maestro["productos"]}
print(f"Maestro: {len(datos)} productos (activos={sum(1 for v in datos.values() if v['estado']=='activo')}, "
      f"inactivos={sum(1 for v in datos.values() if v['estado']!='activo')})")

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.goto("about:blank")
    r = pg.evaluate("""async ({BACKEND, datos}) => {
      const login = await (await fetch(BACKEND, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'},
        body: JSON.stringify({tipo:'login', usuario:'Adis', clave:'Adisdiseño2026'})})).json();
      if (!login.ok) return {error: 'login fallo: ' + JSON.stringify(login)};
      const tok = login.token;
      const post = (payload) => fetch(BACKEND, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'},
        body: JSON.stringify({...payload, token: tok})}).then(x=>x.json());
      const rep = await post({tipo:'reparar_esquema', datos});
      // verificacion
      const g = await (await fetch(BACKEND + '?action=productos&token=' + encodeURIComponent(tok))).json();
      const prods = g.productos || [];
      const estVacios = prods.filter(p => !String(p.estado || '').trim());
      const fecVacias = prods.filter(p => !String(p.fecha_actualizacion || '').trim());
      const conFoto2 = 'foto_2' in (prods[0] || {});
      const adler = prods.find(x => x.codigo === 'HJPVC-101') || {};
      return {reparar: rep, total: prods.length, estVacios: estVacios.length, fecVacias: fecVacias.length,
              foto2_key: conFoto2,
              adler: {estado: adler.estado, notas: String(adler.notas).slice(0, 40), fecha: adler.fecha_actualizacion,
                      foto: adler.foto, foto_2: adler.foto_2}};
    }""", {"BACKEND": BACKEND, "datos": datos})
    b.close()

print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
ok = (r.get("reparar", {}).get("ok") and r.get("estVacios") == 0 and r.get("foto2_key")
      and str(r.get("adler", {}).get("foto", "")).startswith("img/"))
print("RESULTADO:", "OK" if ok else "FALLO")
sys.exit(0 if ok else 1)
