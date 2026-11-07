#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reclasificacion historica FASE 1 (autorizada 2026-11-06).

Aplica la naturaleza financiera a los gastos historicos autorizados por el
dueno (grupos: retiros / inventario / operativos). Usa el endpoint
tipo:'gasto_clasificar' (solo toca la columna naturaleza; bitacora incluida).

IMPORTANTE: ejecutar SOLO despues del redeploy de Fase 0/1.
Por defecto es --dry-run (muestra el plan sin escribir). Con --aplicar escribe.

Los folios ambiguos (pendientes/insuficientes de la tabla de revision) NO estan
en esta lista: el dueno los decide folio por folio.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Objetivo: por defecto produccion. Entorno aislado: set ADIS_API_URL=<url copia>.
API = os.environ.get("ADIS_API_URL")
if not API:
    for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
        p = ROOT / cand
        if p.exists():
            m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
            if m:
                API = m.group(1)
                break
if not API:
    sys.exit("No encontre CONFIG.API_URL")

USUARIO = os.environ.get("ADIS_USUARIO", "Adis")
CLAVE = os.environ.get("ADIS_CLAVE", "Adisdiseño2026")

# Grupos autorizados por el dueno el 2026-11-06 (tabla de revision).
# ACTUALIZADO 2026-11-06 (conciliacion definitiva): cubre los 49 activos.
# Estado: PREPARADO PARA APROBACION — no ejecutar --aplicar sin autorizacion
# expresa. Ver 99_DOCUMENTACION/CONCILIACION_DEFINITIVA_CLASIFICACION_2026-11-06.md
RECLASIFICAR = {
    # Retiros del propietario — 17 folios ($24,804.72)
    "retiro": [
        "GAS-2026-0004", "GAS-2026-0009", "GAS-2026-0010", "GAS-2026-0025",
        "GAS-2026-0029", "GAS-2026-0030", "GAS-2026-0031", "GAS-2026-0032",
        "GAS-2026-0034", "GAS-2026-0036", "GAS-2026-0038", "GAS-2026-0041",
        "GAS-2026-0046", "GAS-2026-0050", "GAS-2026-0051", "GAS-2026-0055",
        "GAS-2026-0056",
    ],
    # Compras de inventario / mercancia — 9 folios ($40,139.32; incluye GAS-0013/0014 segun dueno)
    "inventario": [
        "GAS-2026-0005", "GAS-2026-0006", "GAS-2026-0013", "GAS-2026-0014",
        "GAS-2026-0018", "GAS-2026-0019", "GAS-2026-0020", "GAS-2026-0039",
        "GAS-2026-0040",
    ],
    # Inversion en activos — 2 folios ($6,200.00: telefono + muestrario)
    "inversion": [
        "GAS-2026-0011", "GAS-2026-0016",
    ],
    # Gastos operativos — 21 folios ($26,227.00; incluye 5 gasolinas y 4 alimentos segun dueno)
    "operativo": [
        "GAS-2026-0001", "GAS-2026-0002", "GAS-2026-0003", "GAS-2026-0007",
        "GAS-2026-0008", "GAS-2026-0012", "GAS-2026-0015", "GAS-2026-0017",
        "GAS-2026-0033", "GAS-2026-0035", "GAS-2026-0037", "GAS-2026-0042",
        "GAS-2026-0043", "GAS-2026-0044", "GAS-2026-0045", "GAS-2026-0047",
        "GAS-2026-0048", "GAS-2026-0049", "GAS-2026-0052", "GAS-2026-0053",
        "GAS-2026-0054",
    ],
    # Los 7 cancelados (0021/0022/0023/0024/0026/0027/0028) NO se tocan:
    # estan excluidos por baja logica.
    "por_clasificar": [],  # vacio: las 49 activas quedan decididas por el dueno
}


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
    ap = argparse.ArgumentParser(description="Reclasificacion historica Fase 1 (autorizada)")
    ap.add_argument("--aplicar", action="store_true", help="escribe (default: dry-run)")
    args = ap.parse_args()

    # SEGURIDAD (2026-11-06): la reclasificacion esta SIN AUTORIZAR. En produccion
    # exige doble confirmacion explicita; en la copia de prueba (ADIS_API_URL
    # apuntando a otra URL) basta --aplicar.
    prod = None
    for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
        p = ROOT / cand
        if p.exists():
            m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
            if m:
                prod = m.group(1)
                break
    es_produccion = prod and API.rstrip("/") == prod.rstrip("/")
    if args.aplicar and es_produccion and os.environ.get("ADIS_RECLASIFICAR_PROD") != "si":
        sys.exit("BLOQUEADO: reclasificacion en PRODUCCION sin autorizacion. "
                 "La reclasificacion de los 31 folios esta pendiente de revision del dueno. "
                 "Para la copia de prueba usa: set ADIS_API_URL=<url copia>. "
                 "(Solo si el dueno autoriza expresamente: ADIS_RECLASIFICAR_PROD=si)")
    if args.aplicar and es_produccion:
        print("ADVERTENCIA: escribiendo en PRODUCCION con autorizacion explicita del dueno.")

    tok = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})
    if not tok.get("ok"):
        sys.exit(f"Login fallo: {tok}")
    token = tok["token"]

    gastos = get("gastos", token)["gastos"]
    por_folio = {str(x.get("folio")): x for x in gastos}

    plan = []  # (folio, naturaleza_actual, naturaleza_nueva, id)
    for naturaleza, folios in RECLASIFICAR.items():
        if naturaleza == "por_clasificar":
            continue  # nunca se tocan automaticamente
        for folio in folios:
            g = por_folio.get(folio)
            if not g:
                print(f"AVISO: {folio} no existe (omitido)")
                continue
            if str(g.get("estado")) == "CANCELADA":
                print(f"AVISO: {folio} esta CANCELADA (omitido)")
                continue
            actual = str(g.get("naturaleza") or "por_clasificar")
            plan.append((folio, actual, naturaleza, g["id"]))

    print(f"\nPlan: {len(plan)} gastos a reclasificar (dry-run={not args.aplicar})")
    tot = {}
    for folio, actual, nueva, _ in plan:
        g = por_folio[folio]
        base = float(g.get("monto_base") or 0)
        tot[nueva] = tot.get(nueva, 0) + base
        print(f"  {folio} · {str(g.get('categoria'))[:24]:<24} · {actual:<14} -> {nueva:<10} · ${base:,.2f} base")
    print("  Totales:", {k: f"${v:,.0f}" for k, v in tot.items()})

    if not args.aplicar:
        print("\nDry-run: nada escrito. Corre con --aplicar para ejecutar.")
        return

    ok = fail = 0
    for folio, _, nueva, gid in plan:
        try:
            r = post({"tipo": "gasto_clasificar", "id": gid, "naturaleza": nueva, "token": token})
            if r.get("ok"):
                ok += 1
                print(f"  OK {folio} -> {nueva}")
            else:
                fail += 1
                print(f"  FAIL {folio}: {r}")
        except Exception as e:
            fail += 1
            print(f"  ERROR {folio}: {e}")
    print(f"\nReclasificados: {ok} · fallos: {fail}")

    # Verificacion post: P&L debe reflejar la separacion
    er = get("estado_resultados", token)
    print("\nP&L despues de reclasificar:")
    for k in ["ingresos", "costos", "utilidad_bruta", "total_gastos", "utilidad_operativa",
              "otros_resultados", "utilidad_neta", "retiros", "inventario", "sin_clasificar"]:
        print(f"  {k}: {er.get(k)}")
    print("  advertencia:", er.get("advertencia"))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
