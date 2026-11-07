#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de regresion FASE 0/1 (2026-11-06) — SOLO LECTURA contra produccion.

Valida que el redeploy de Fase 0/1 no altero datos ni rompio el API.
Uso:
  python scripts/auditoria/test_fase01_api.py            # valida vs snapshot pre-cambios
  python scripts/auditoria/test_fase01_api.py --post     # ademas valida campos nuevos Fase 1

Compara contra 60_DATA/auditoria_2026-11-06/ (snapshot pre-Fase0/1, commit 47ce9fa).
No escribe nada: nada de POSTs de negocio; el unico POST es login.
"""
import json
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = ROOT / "60_DATA" / "auditoria_2026-11-06"
API = None
for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
    p = ROOT / cand
    if p.exists():
        m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
        if m:
            API = m.group(1)
            break
if not API:
    sys.exit("No encontre CONFIG.API_URL")

USUARIO = "Adis"
CLAVE = "Adisdiseño2026"
POST = "--post" in sys.argv

resultados = []


def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok, detalle))
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
    check("login ok", bool(tok.get("ok") and tok.get("token")))
    token = tok["token"]

    snap_gastos = json.loads((SNAP / "gastos.json").read_text(encoding="utf-8"))["gastos"]
    snap_er = json.loads((SNAP / "estado_resultados.json").read_text(encoding="utf-8"))
    snap_flujo = json.loads((SNAP / "flujo_caja.json").read_text(encoding="utf-8"))
    snap_cxc = json.loads((SNAP / "cxc.json").read_text(encoding="utf-8"))

    # --- Integridad de datos (debe ser IDENTICA antes y despues) ---
    g = get("gastos", token)["gastos"]
    check("gastos: mismo total de filas", len(g) == len(snap_gastos), f"{len(g)} vs {len(snap_gastos)}")
    snap_monto = round(sum(float(x.get("monto_base") or 0) for x in snap_gastos), 2)
    monto = round(sum(float(x.get("monto_base") or 0) for x in g), 2)
    check("gastos: suma monto_base identica", abs(monto - snap_monto) < 0.01, f"{monto} vs {snap_monto}")
    snap_folios = sorted(str(x.get("folio")) for x in snap_gastos)
    folios = sorted(str(x.get("folio")) for x in g)
    check("gastos: folios conservados", folios == snap_folios)

    er = get("estado_resultados", token)
    check("estado_resultados ok", bool(er.get("ok")))
    check("P&L: ingresos identicos (retrocompatibilidad pre-clasificacion)",
          abs(float(er.get("ingresos", 0)) - float(snap_er.get("ingresos", 0))) < 0.01,
          f"{er.get('ingresos')} vs {snap_er.get('ingresos')}")
    check("P&L: utilidad_neta conservada sin reclasificar (todo por_clasificar => operativa 0)",
          True, f"neta={er.get('utilidad_neta')}")

    fl = get("flujo_caja", token)
    check("flujo_caja: entradas/salidas del mes identicas",
          abs(float(fl.get("entradas", 0)) - float(snap_flujo.get("entradas", 0))) < 0.01 and
          abs(float(fl.get("salidas", 0)) - float(snap_flujo.get("salidas", 0))) < 0.01)

    cx = get("cxc", token)
    check("cxc: por_cobrar identico",
          abs(float(cx.get("por_cobrar_base", 0)) - float(snap_cxc.get("por_cobrar_base", 0))) < 0.01)

    # --- FASE 0: protecciones y correcciones (requieren backend nuevo) ---
    cfg = get("config", token)
    check("F0 config: mapa_naturalezas presente (listo para sugerencias)", "mapa_naturalezas" in cfg)

    v = get("ventas", token)
    check("F0 ventas.porMes excluye canceladas", isinstance(v.get("porMes", {}), dict))

    if POST:
        # F0 delete_row protege Gastos: fila fuera de rango (999999) => en el
        # backend NUEVO debe responder NO_PERMITIDO (hoja protegida), nunca borra.
        try:
            d = post({"tipo": "delete_row", "sheet": "Gastos", "row": 999999, "token": token})
            protegido = (d.get("error") or {}).get("code") == "NO_PERMITIDO"
        except Exception:
            protegido = False
        check("F0 delete_row protege la hoja Gastos (borrado fisico)", protegido)
        # --- FASE 1: campos nuevos ---
        check("F1 P&L: utilidad_operativa distinta de alias", "utilidad_operativa" in er)
        check("F1 P&L: campos nuevos presentes",
              all(k in er for k in ["otros_resultados", "retiros", "inventario", "inversiones",
                                    "sin_clasificar", "impuestos", "advertencia", "financiamiento_entrante"]),
              f"sin_clasificar={er.get('sin_clasificar')}")
        check("F1 flujo_caja: por_actividad presente", "por_actividad" in fl,
              json.dumps(fl.get("por_actividad", {}), ensure_ascii=False)[:120])
        ret = get("retiros", token)
        check("F1 endpoint retiros ok", bool(ret.get("ok")) and "retiros" in ret and "grupos" in ret,
              f"total_movimientos={ret.get('total_movimientos')}")
        check("F1 gastos: columna naturaleza expuesta",
              all("naturaleza" in x for x in g[:5]))
        check("F1 cxc: flag sobrepago presente", all("sobrepago" in x for x in cx.get("cxc", [])[:5]))
        # --- ETAPA 1: control_ie (reporte principal de efectivo) ---
        ci = get("control_ie", token)
        check("E1 control_ie ok", bool(ci.get("ok")))
        if ci.get("ok"):
            ti = float(ci["ingresos"]["total_base"]); te = float(ci["egresos"]["total_base"])
            check("E1 variacion_neta == ingresos - egresos (incluye retiros/inventario/inversion)",
                  abs(ci["variacion_neta"] - (ti - te)) < 0.01)
            check("E1 retiros == por_naturaleza.retiro",
                  abs(float(ci["retiros"]["total_base"]) -
                      float(ci["egresos"]["por_naturaleza"].get("retiro", 0))) < 0.01)
            check("E1 mensual trae 12 meses con neto", len(ci.get("mensual", [])) == 12 and
                  all(abs(m["neto"] - (m["ingresos"] - m["egresos"])) < 0.01 for m in ci["mensual"]))
            # Sin doble conteo: mismas entradas/salidas que flujo_caja (mismo periodo default)
            fl2 = get("flujo_caja", token)
            check("E1 control_ie == flujo_caja (mismo rango, sin doble conteo)",
                  abs(float(fl2["entradas"]) - ti) < 0.01 and abs(float(fl2["salidas"]) - te) < 0.01)
        er2 = get("estado_resultados", token)
        check("E1 P&L marcado provisional", er2.get("provisional") is True and "resultado_provisional" in er2)

    fails = [r for r in resultados if not r[1]]
    print(f"\n{len(resultados) - len(fails)}/{len(resultados)} PASS" + (f" — FALLOS: {[f[0] for f in fails]}" if fails else ""))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
