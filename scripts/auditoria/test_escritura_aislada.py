#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de ESCRITURA — SOLO entorno aislado (copia de Google Sheets).

Ejecuta el ciclo de escritura de Etapa 1 contra la COPIA de prueba, nunca contra
produccion:
  1. login
  2. alta gasto $1 (naturaleza=operativo) + pago $1
  3. verifica que control_ie lo incluya en egresos (una sola vez)
  4. reclasifica el gasto a 'retiro' (gasto_clasificar) y verifica por_naturaleza
  5. alta ingreso $1 (tipo_ingreso='otro') + edicion de descripcion (sin tocar
     monto_base: valida el fix de TC historico)
  6. verifica columna naturaleza en GET gastos

Uso (Git Bash):
  export ADIS_API_URL="https://script.google.com/macros/s/<ID_COPIA>/exec"
  python scripts/auditoria/test_escritura_aislada.py

El script ABORTA si el objetivo es la URL de produccion.
Las filas de prueba quedan en la copia (no se borran de produccion jamas).
"""
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = os.environ.get("ADIS_API_URL")
prod = None
for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
    p = ROOT / cand
    if p.exists():
        m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
        if m:
            prod = m.group(1)
            break
if not API:
    sys.exit("Define ADIS_API_URL con la URL del despliegue de la COPIA de prueba.")
if prod and API.rstrip("/") == prod.rstrip("/"):
    sys.exit("BLOQUEADO: ADIS_API_URL apunta a PRODUCCION. Usa la URL de la copia de prueba.")

USUARIO = os.environ.get("ADIS_USUARIO", "Adis")
CLAVE = os.environ.get("ADIS_CLAVE", "Adisdiseño2026")

resultados = []


def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok))
    print(("PASS " if ok else "FAIL ") + nombre + (" · " + str(detalle) if detalle else ""))


def post(payload):
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def get(action, token):
    url = f"{API}?action={action}&token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    tok = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})
    check("login (copia)", bool(tok.get("ok") and tok.get("token")))
    token = tok["token"]
    hoy = __import__("datetime").date.today().isoformat()

    # 2. gasto $1 + pago
    g = post({"tipo": "gasto", "fecha": hoy, "categoria": "Otro", "descripcion": "PRUEBA AISLADA Etapa1",
              "monto": 1, "moneda": "MXN", "naturaleza": "operativo", "token": token})
    check("alta gasto con naturaleza", bool(g.get("ok") and g.get("folio")), g.get("folio"))
    folio_g = g.get("folio")
    pg = post({"tipo": "gasto_pago", "gasto_id": g.get("id"), "fecha": hoy, "monto": 1,
               "moneda": "MXN", "metodo": "Efectivo", "token": token})
    check("pago del gasto", bool(pg.get("ok")), pg.get("folio"))

    # 3. control_ie incluye el pago una sola vez
    ci = get(f"control_ie&desde={hoy}&hasta={hoy}", token)
    det = [m for m in ci["egresos"]["detalle"] if m.get("gasto_folio") == folio_g]
    check("control_ie incluye el pago exactamente 1 vez", len(det) == 1, f"apariciones={len(det)}")
    check("control_ie: naturaleza operativo reflejada",
          det and det[0].get("naturaleza") == "operativo", det and det[0].get("naturaleza"))

    # 4. reclasificar a retiro y verificar
    cl = post({"tipo": "gasto_clasificar", "id": g.get("id"), "naturaleza": "retiro", "token": token})
    check("gasto_clasificar -> retiro", bool(cl.get("ok")))
    ci2 = get(f"control_ie&desde={hoy}&hasta={hoy}", token)
    det2 = [m for m in ci2["egresos"]["detalle"] if m.get("gasto_folio") == folio_g]
    check("control_ie: ahora figura como retiro", det2 and det2[0].get("naturaleza") == "retiro")
    check("retiros del periodo >= $1 (en la copia)",
          ci2["retiros"]["total_base"] >= 1)

    # 5. ingreso $1 tipo otro + edicion sin tocar monto_base (fix TC)
    i = post({"tipo": "ingreso", "fecha": hoy, "concepto": "PRUEBA AISLADA ingreso", "monto": 1,
              "moneda": "MXN", "metodo": "Efectivo", "tipo_ingreso": "otro", "token": token})
    check("alta ingreso tipo 'otro'", bool(i.get("ok")), i.get("folio"))
    cobros = get("cxc", token)["cobros"]
    row = next((c for c in cobros if str(c.get("folio")) == str(i.get("folio"))), None)
    check("ingreso quedo tipo 'otro'", row and str(row.get("tipo")) == "otro", row and row.get("tipo"))
    mb_antes = float(row.get("monto_base"))
    ed = post({"tipo": "ingreso_editar", "id": row.get("id"), "fecha": hoy,
               "concepto": "PRUEBA AISLADA ingreso (editada)", "monto": 1, "moneda": "MXN",
               "metodo": "Efectivo", "notas": "", "tipo_ingreso": "otro", "token": token})
    check("ingreso_editar (solo descripcion)", bool(ed.get("ok")))
    cobros2 = get("cxc", token)["cobros"]
    row2 = next((c for c in cobros2 if str(c.get("folio")) == str(i.get("folio"))), None)
    check("monto_base intacto tras editar descripcion (fix TC historico)",
          row2 and abs(float(row2.get("monto_base")) - mb_antes) < 0.001,
          f"{mb_antes} -> {row2 and row2.get('monto_base')}")

    # 6. columna naturaleza expuesta
    gs = get("gastos", token)["gastos"]
    check("columna naturaleza presente en GET gastos", all("naturaleza" in x for x in gs[:5]))

    fails = [r for r in resultados if not r[1]]
    print(f"\n{len(resultados)-len(fails)}/{len(resultados)} PASS" + (f" — FALLOS: {[f[0] for f in fails]}" if fails else ""))
    print("\nNOTA: las filas de prueba permanecen en la COPIA (folio gasto", folio_g, "/ ingreso", i.get("folio"), "). No afectan produccion.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
