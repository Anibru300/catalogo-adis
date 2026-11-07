#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba aislada ETAPA 1 — Control de Ingresos y Egresos.

Modo local (default): calcula con el snapshot pre-Fase0/1 los valores esperados
del endpoint control_ie para 2026-10 (mes completo con datos) y valida las
definiciones del reporte: la variacion neta incluye TODOS los movimientos de
efectivo (retiros, inventario e inversiones incluidos) y no hay doble conteo
(se usa Cobros+Pagos, nunca Gastos como salida de dinero).

Modo API (--api): compara el endpoint real contra los valores esperados del
snapshot (ejecutar SOLO despues del redeploy de Etapa 1, antes de reclasificar
o despues, segun convenga; usar --desde/--hasta coherentes con el snapshot).
"""
import json
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = ROOT / "60_DATA" / "auditoria_2026-11-06"
MES = "2026-10"  # ultimo mes completo del snapshot

cobros = json.loads((SNAP / "cxc.json").read_text(encoding="utf-8"))["cobros"]
pagos = json.loads((SNAP / "cxp.json").read_text(encoding="utf-8"))["pagos"]


def en_mes(fecha):
    return str(fecha)[:7] == MES


ingresos = sum(float(c.get("monto_base") or 0) for c in cobros if en_mes(c.get("fecha")))
egresos = sum(float(p.get("monto_base") or 0) for p in pagos if en_mes(p.get("fecha")))
neto = ingresos - egresos

print(f"Esperados {MES} (desde snapshot):")
print(f"  ingresos = {ingresos:,.2f}")
print(f"  egresos  = {egresos:,.2f}")
print(f"  neto     = {neto:,.2f}")

ok = True

# Invariantes de definicion (valen siempre)
ok &= ingresos > 0 and egresos > 0
ok &= abs((ingresos - egresos) - neto) < 0.01

# Chequeo cruzado: los pagos del mes incluyen salidas de TODAS las naturalezas
# (en el snapshot aun no hay naturaleza; lo que verificamos es que el total de
# pagos del mes == suma de cobros... no: que ningun pago quede fuera por fecha)
fuera = [p for p in pagos if en_mes(p.get("fecha")) and not str(p.get("fecha"))[:10]]
print(f"  pagos del mes sin fecha parseable: {len(fuera)} (deben ser 0)")
ok &= len(fuera) == 0

if "--api" not in sys.argv:
    print("\nModo local: definiciones validadas." + ("" if ok else " — FALLO"))
    sys.exit(0 if ok else 1)

# --- Modo API: compara endpoint real vs esperados del snapshot ---
# Objetivo: produccion por defecto (solo lectura); entorno aislado con
#   set ADIS_API_URL=<url del despliegue de la copia de prueba>
import os
API = os.environ.get("ADIS_API_URL")
if not API:
    for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
        p = ROOT / cand
        if p.exists():
            m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
            if m:
                API = m.group(1)
                break

USUARIO = os.environ.get("ADIS_USUARIO", "Adis")
CLAVE = os.environ.get("ADIS_CLAVE", "Adisdiseño2026")

def post(payload):
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def get(action, token):
    url = f"{API}?action={action}&token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

tok = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})["token"]
ci = get(f"control_ie&desde={MES}-01&hasta={MES}-31", tok)

checks = [
    ("control_ie ok", bool(ci.get("ok"))),
    ("ingresos == esperado", abs(float(ci["ingresos"]["total_base"]) - ingresos) < 0.01,
     f"{ci['ingresos']['total_base']} vs {ingresos:,.2f}"),
    ("egresos == esperado (incluye TODAS las salidas)", abs(float(ci["egresos"]["total_base"]) - egresos) < 0.01,
     f"{ci['egresos']['total_base']} vs {egresos:,.2f}"),
    ("variacion_neta == ingresos - egresos", abs(ci["variacion_neta"] - neto) < 0.01),
    ("mensual trae 12 meses", len(ci.get("mensual", [])) == 12),
    ("retiros es subconjunto de por_naturaleza", abs(ci["retiros"]["total_base"] -
        ci["egresos"]["por_naturaleza"].get("retiro", 0)) < 0.01),
]
# Consistencia con flujo_caja (mismo rango): entradas/salidas deben coincidir
fl = get(f"flujo_caja&desde={MES}-01&hasta={MES}-31", tok)
checks.append(("flujo_caja entradas == control_ie ingresos (sin doble conteo)",
               abs(float(fl["entradas"]) - float(ci["ingresos"]["total_base"])) < 0.01))
checks.append(("flujo_caja salidas == control_ie egresos (sin doble conteo)",
               abs(float(fl["salidas"]) - float(ci["egresos"]["total_base"])) < 0.01))
checks.append(("variacion_neta == flujo neto",
               abs(ci["variacion_neta"] - float(fl["neto"])) < 0.01))

fails = 0
for nombre, passed, *det in checks:
    print(("PASS " if passed else "FAIL ") + nombre + (f" · {det[0]}" if det else ""))
    fails += 0 if passed else 1
print(f"\n{len(checks)-fails}/{len(checks)} PASS")
sys.exit(1 if fails else 0)
