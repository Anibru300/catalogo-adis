#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entrada retroactiva de mercancia a inventario — ETAPA 2 (2026-11-07).

Registra en el STOCK las compras de mercancia de oct-2026 que hoy existen SOLO
como gastos (naturaleza=inventario). Usa el endpoint tipo:'gasto_inventario':
un MOV- de entrada por partida, ligado al folio GAS- (doc_tipo GASTO), con la
fecha original del gasto. Idempotente: un gasto solo admite una entrada.

El detalle (producto/cantidad/costo por folio) vive en:
  60_DATA/plan_entrada_inventario_fase2.json   (editable, sin tocar este script)

Por defecto es --dry-run (valida y muestra el plan sin escribir). Con
--aplicar escribe. En PRODUCCION exige ADIS_ENTRADA_INV_PROD=si (doble
confirmacion). Para la copia de prueba basta con ADIS_API_URL apuntando a ella.

Solo ejecutar DESPUES de redeployar el backend con el endpoint gasto_inventario.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_JSON = ROOT / "60_DATA" / "plan_entrada_inventario_fase2.json"

API = os.environ.get("ADIS_API_URL")
_prod = None
for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
    p = ROOT / cand
    if p.exists():
        m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
        if m:
            _prod = m.group(1)
            break
if not API:
    API = _prod
if not API:
    sys.exit("No encontre CONFIG.API_URL")

USUARIO = os.environ.get("ADIS_USUARIO", "Adis")
CLAVE = os.environ.get("ADIS_CLAVE", "Adisdiseño2026")


def post(payload):
    payload = dict(payload)
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def get(action, token):
    url = f"{API}?action={action}&token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="Entrada retroactiva gasto-mercancia -> stock (Etapa 2)")
    ap.add_argument("--aplicar", action="store_true", help="escribe (default: dry-run)")
    args = ap.parse_args()

    es_produccion = _prod and API.rstrip("/") == _prod.rstrip("/")
    if args.aplicar and es_produccion and os.environ.get("ADIS_ENTRADA_INV_PROD") != "si":
        sys.exit("BLOQUEADO: entrada a inventario en PRODUCCION sin autorizacion. "
                 "Solo si el dueno autoriza expresamente: ADIS_ENTRADA_INV_PROD=si. "
                 "Para la copia de prueba usa: set ADIS_API_URL=<url copia>.")
    if args.aplicar and es_produccion:
        print("ADVERTENCIA: escribiendo en PRODUCCION con autorizacion explicita del dueno.")

    plan_data = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    entradas = plan_data["plan"]

    tok = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})
    if not tok.get("ok"):
        sys.exit(f"Login fallo: {tok}")
    token = tok["token"]

    gastos = get("gastos", token)["gastos"]
    por_folio = {str(x.get("folio")): x for x in gastos}
    productos = get("productos", token)["productos"]
    prod_por_id = {str(p.get("id")): p for p in productos}
    almacenes = get("almacenes", token)["almacenes"]
    alm_por_id = {str(a.get("id")): a for a in almacenes}
    movs = get("movimientos", token).get("movimientos", [])
    ya_con_entrada = {str(m.get("documento_id")) for m in movs
                      if str(m.get("documento_tipo")) == "GASTO"}
    stock = get("stock", token).get("stock", [])
    stock_de = {(str(s["producto_id"]), str(s["almacen_id"])): float(s["cantidad"]) for s in stock}

    print(f"API: {'PRODUCCION' if es_produccion else 'copia/prueba'} · folios en plan: {len(entradas)}\n")
    listos, pendientes, omitidos = [], [], []
    for e in entradas:
        folio = str(e.get("folio"))
        g = por_folio.get(folio)
        if not g:
            omitidos.append((folio, "no existe en la hoja Gastos"))
            continue
        if str(g.get("estado")) == "CANCELADA":
            omitidos.append((folio, "CANCELADA"))
            continue
        if str(g.get("naturaleza") or "por_clasificar") != "inventario":
            omitidos.append((folio, f"naturaleza={g.get('naturaleza') or 'por_clasificar'} (no es inventario)"))
            continue
        if folio in ya_con_entrada:
            omitidos.append((folio, "YA tiene entradas de inventario (idempotencia)"))
            continue
        alm_id = str(e.get("almacen_id") or plan_data.get("_almacen_default") or "")
        if alm_id not in alm_por_id:
            pendientes.append((folio, f"almacen {alm_id} no existe"))
            continue
        items = e.get("items") or []
        if not items:
            pendientes.append((folio, e.get("nota") or "sin items definidos"))
            continue
        items_raw = e.get("items") or []
        detalle, valido = [], True
        for it in items_raw:
            pid = str(it.get("producto_id"))
            p = prod_por_id.get(pid)
            if not p:
                pendientes.append((folio, f"producto_id {pid} no existe"))
                valido = False
                break
            cant = float(it.get("cantidad") or 0)
            if cant <= 0:
                pendientes.append((folio, f"cantidad invalida ({cant}) para {p.get('nombre')}"))
                valido = False
                break
            costo = it.get("costo_unit")
            costo = float(costo) if costo not in (None, "") else float(p.get("costo") or 0)
            ant = stock_de.get((pid, alm_id), 0.0)
            detalle.append((p.get("nombre"), cant, costo, ant, ant + cant))
        if valido:
            listos.append((folio, g, alm_id, detalle, items_raw))

    for folio, g, alm_id, detalle, _items_raw in listos:
        print(f"LISTO  {folio} · {str(g.get('fecha'))[:10]} · {alm_por_id[alm_id]['nombre']}")
        for nombre, cant, costo, ant, post_ in detalle:
            print(f"         {nombre[:40]:<40} x{cant:<6} @ ${costo:,.2f}  stock {ant:g} -> {post_:g}")
    for folio, razon in pendientes:
        print(f"PENDIENTE {folio}: {razon}")
    for folio, razon in omitidos:
        print(f"OMITIDO   {folio}: {razon}")

    print(f"\nResumen: {len(listos)} listos · {len(pendientes)} pendientes · {len(omitidos)} omitidos "
          f"(dry-run={not args.aplicar})")
    if not args.aplicar:
        print("Dry-run: nada escrito. Completa los items en", PLAN_JSON.name,
              "y corre con --aplicar para ejecutar.")
        return
    if not listos:
        print("Nada que aplicar.")
        return

    ok = fail = 0
    for folio, g, alm_id, detalle, items_raw in listos:
        items = [{"producto_id": str(it.get("producto_id")), "cantidad": float(it.get("cantidad")),
                  **({"costo_unit": float(it["costo_unit"])} if it.get("costo_unit") not in (None, "") else {})}
                 for it in items_raw]
        try:
            r = post({"tipo": "gasto_inventario", "id": g["id"], "almacen_id": alm_id,
                      "items": items, "token": token})
            if r.get("ok"):
                ok += 1
                print(f"  OK {folio}: entrada aplicada")
            else:
                fail += 1
                print(f"  FAIL {folio}: {r}")
        except Exception as exc:
            fail += 1
            print(f"  ERROR {folio}: {exc}")
    print(f"\nAplicados: {ok} · fallos: {fail}")

    movs2 = get("movimientos", token).get("movimientos", [])
    nuevos = [m for m in movs2 if str(m.get("documento_tipo")) == "GASTO"]
    print(f"  Movimientos con doc_tipo=GASTO: {len(nuevos)} (esperado: "
          f"{sum(len(x[4]) for x in listos)})")
    for m in nuevos:
        print(f"    {m.get('id')} · {str(m.get('fecha'))[:16]} · {m.get('tipo')} · {m.get('producto')} "
              f"x{m.get('cantidad')} · {m.get('almacen')} · doc={m.get('documento_id')}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
