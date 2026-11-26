#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-off (2026-11-25): registra la compra de material TEKNOSTEP Factura 28024799.

Que hace, en orden (todo por la API del admin, nada directo a Sheets):
  1. Pre-chequeos idempotentes: aborta si ya existe un gasto con "28024799".
  2. Crea 2 productos nuevos (angulos por color, hoy solo existe el generico
     LAM-002): LAM-040 Angulo Rio y LAM-041 Angulo Brasilia.
  3. Registra el gasto "Compra de mercancia" (naturaleza=inventario) por
     $3,460.88 MXN con items_inventario -> entradas de stock al almacen
     Nogales trazadas al folio GAS- (doc_tipo GASTO), y actualiza el ultimo
     costo de cada producto (costo CON IVA = lo realmente pagado).
  4. Registra el pago total (tarjeta de debito, PUE) -> gasto PAGADA.
  5. Verifica: stock, movimientos, costos, estado del gasto y CxP.

Factura (pypdf, 2 paginas):
  Subtotal $2,983.52 + IVA $477.36 = $3,460.88
  - M-LAMBRIN-WPC-201-10 Lambrin RIO 160x2900x24 C/14PZ .... 1 caja  = 14 pzas ($1,201.76 s/IVA)
  - M-LAMBRIN-WPC-106-10 Lambrin BRASILIA 160x2900x24 C/14PZ  1 caja = 14 pzas ($1,201.76 s/IVA)
  - M-WPC-A201  Angulo RIO 30x30x2900 ....... 14.5 m.l. = 5 pzas x 2.9m ($290.00 s/IVA)
  - M-WPC-A106  Angulo BRASILIA 30x30x2900 .. 14.5 m.l. = 5 pzas x 2.9m ($290.00 s/IVA)
  Costos con IVA: lambrin 1,394.0416/14 = $99.57/pza · angulo 336.40/5 = $67.28/pza.

Uso:
  python 60_DATA/registrar_compra_teknostep_28024799.py            # dry-run (solo muestra)
  python 60_DATA/registrar_compra_teknostep_28024799.py --aplicar  # escribe en produccion
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
API_URL = None
for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
    p = ROOT / cand
    if p.exists():
        m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
        if m:
            API_URL = m.group(1)
            break
if not API_URL:
    cfg = json.loads((ROOT / "00_CORE/config/plataforma.json").read_text(encoding="utf-8"))
    API_URL = cfg["url_backend"]

USUARIO = "Adis"
CLAVE = "Adisdiseño2026"

ALMACEN = {"id": "e6a5e282", "nombre": "Nogales"}
FECHA = "2026-11-25"
FACTURA = "28024799"
MONTO_TOTAL = 3460.88

# Productos existentes (verificado en vivo 2026-11-25)
PROD_RIO = {"id": "3935f2b1", "codigo": "LAM-015", "nombre": "Río"}
PROD_BRAS = {"id": "4d494eba", "codigo": "LAM-005", "nombre": "Brasilia"}

# Productos nuevos (angulos por color)
NUEVOS = [
    {"codigo": "LAM-040", "nombre": "ANGULO PARA MURO INTERIOR RIO 30X30X2900MM",
     "categoria": "Lambrin WPC", "subcategoria": "Lambrin Interior", "proveedor": "Teknostep",
     "costo": 67.28, "precio": 0, "unidad": "pieza", "moneda": "MXN",
     "notas": "Clave proveedor M-WPC-A201 · Factura Teknostep 28024799"},
    {"codigo": "LAM-041", "nombre": "ANGULO PARA MURO INTERIOR BRASILIA 30X30X2900MM",
     "categoria": "Lambrin WPC", "subcategoria": "Lambrin Interior", "proveedor": "Teknostep",
     "costo": 67.28, "precio": 0, "unidad": "pieza", "moneda": "MXN",
     "notas": "Clave proveedor M-WPC-A106 · Factura Teknostep 28024799"},
]

COSTO_LAMBRIN = 99.57  # $1,394.0416 c/IVA por caja de 14 pzas
COSTO_ANGULO = 67.28   # $336.40 c/IVA entre 5 pzas

DESCRIPCION = ("Compra de material Teknostep — Factura 28024799: 14 lambrín Río + "
               "14 lambrín Brasilia 160x2900 (1 caja c/14 pzas c/u) + 5 ángulo Río + "
               "5 ángulo Brasilia 30x30x2900. OV 28033614, PUE tarjeta de débito.")


def post(payload):
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def get(action, token):
    url = f"{API_URL}?action={action}&token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    aplicar = "--aplicar" in sys.argv
    print(f"=== Registro compra Teknostep F-{FACTURA} — {'APLICAR (producción)' if aplicar else 'DRY-RUN'} ===\n")

    d = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})
    if not d.get("ok"):
        sys.exit(f"Login falló: {d}")
    tok = d["token"]
    print("✓ login")

    # ---- Pre-chequeos -------------------------------------------------------
    gastos = get("gastos", tok).get("gastos", [])
    ya = [g for g in gastos if FACTURA in str(g.get("descripcion", ""))]
    if ya:
        sys.exit(f"⛔ ABORTA: ya existe gasto con la factura {FACTURA}: "
                 f"{[(g.get('folio'), g.get('monto'), g.get('estado')) for g in ya]}")

    prods = get("productos", tok).get("productos", [])
    por_codigo = {str(p.get("codigo")).upper(): p for p in prods}
    for cod in ("LAM-015", "LAM-005"):
        if cod not in por_codigo:
            sys.exit(f"⛔ ABORTA: no encontré el producto existente {cod}")
    p_rio, p_bras = por_codigo["LAM-015"], por_codigo["LAM-005"]
    print(f"✓ productos base: LAM-015 Río (id {p_rio['id']}) · LAM-005 Brasilia (id {p_bras['id']})")

    def stock_de(pid):
        st = get("stock", tok).get("stock", [])
        return sum(float(s.get("cantidad") or 0) for s in st
                   if str(s.get("producto_id")) == str(pid) and str(s.get("almacen_id")) == ALMACEN["id"])

    antes = {p_rio["id"]: stock_de(p_rio["id"]), p_bras["id"]: stock_de(p_bras["id"])}
    print(f"✓ stock previo en {ALMACEN['nombre']}: Río={antes[p_rio['id']]:g} · Brasilia={antes[p_bras['id']]:g}")

    items = [
        {"producto_id": p_rio["id"], "cantidad": 14, "costo_unit": COSTO_LAMBRIN},
        {"producto_id": p_bras["id"], "cantidad": 14, "costo_unit": COSTO_LAMBRIN},
    ]
    suma_items = 14 * COSTO_LAMBRIN * 2
    print("\nPlan:")
    print(f"  1) crear LAM-040 / LAM-041 (ángulos, costo ${COSTO_ANGULO} c/IVA)")
    print(f"  2) gasto 'Compra de mercancía' (inventario) ${MONTO_TOTAL} → entradas a {ALMACEN['nombre']}:")
    print(f"     · Río 14 pzas @ ${COSTO_LAMBRIN} · Brasilia 14 pzas @ ${COSTO_LAMBRIN}")
    print(f"     · Ángulo Río 5 pzas @ ${COSTO_ANGULO} · Ángulo Brasilia 5 pzas @ ${COSTO_ANGULO}")
    print(f"  3) pago total ${MONTO_TOTAL} (Tarjeta de débito)")
    print(f"  (suma de partidas ${suma_items + 10 * COSTO_ANGULO:.2f} ≈ total por redondeo por pieza)")

    if not aplicar:
        print("\n(dry-run: nada se escribió — corre con --aplicar para registrar)")
        return

    # ---- 1) Crear ángulos ----------------------------------------------------
    ids_ang = {}
    for nuevo in NUEVOS:
        existente = por_codigo.get(nuevo["codigo"].upper())
        if existente:
            ids_ang[nuevo["codigo"]] = existente["id"]
            print(f"= {nuevo['codigo']} ya existía (id {existente['id']}) — se reutiliza")
            continue
        r = post({"tipo": "save_product", "token": tok, **nuevo})
        if not r.get("ok"):
            sys.exit(f"⛔ error creando {nuevo['codigo']}: {r}")
        ids_ang[nuevo["codigo"]] = r["id"]
        print(f"✓ creado {nuevo['codigo']} (id {r['id']})")
    items.append({"producto_id": ids_ang["LAM-040"], "cantidad": 5, "costo_unit": COSTO_ANGULO})
    items.append({"producto_id": ids_ang["LAM-041"], "cantidad": 5, "costo_unit": COSTO_ANGULO})

    # ---- 2) Gasto + entrada a inventario -------------------------------------
    r = post({"tipo": "gasto", "token": tok, "fecha": FECHA,
              "categoria": "Compra de mercancía", "descripcion": DESCRIPCION,
              "monto": MONTO_TOTAL, "moneda": "MXN", "naturaleza": "inventario",
              "almacen_id": ALMACEN["id"], "items_inventario": items})
    if not r.get("ok"):
        sys.exit(f"⛔ gasto RECHAZADO: {r}")
    folio_g, id_g = r.get("folio"), r.get("id")
    print(f"✓ gasto {folio_g} · stock_nuevo: {r.get('stock_nuevo')}")

    # ---- 3) Pago total ---------------------------------------------------------
    r = post({"tipo": "gasto_pago", "token": tok, "gasto_id": id_g,
              "monto": MONTO_TOTAL, "moneda": "MXN", "metodo": "Tarjeta de débito",
              "notas": f"Pago total factura {FACTURA} Teknostep (PUE)"})
    if not r.get("ok"):
        sys.exit(f"⛔ pago RECHAZADO (el gasto {folio_g} quedó pendiente): {r}")
    print(f"✓ pago {r.get('folio', 'PAG-?')} por ${MONTO_TOTAL}")

    # ---- 4) Verificación -------------------------------------------------------
    print("\n=== VERIFICACIÓN ===")
    ok = True
    esperado = {p_rio["id"]: 14, p_bras["id"]: 14,
                ids_ang["LAM-040"]: 5, ids_ang["LAM-041"]: 5}
    for pid, inc in esperado.items():
        ahora = stock_de(pid)
        base = antes.get(pid, 0)
        bien = abs(ahora - (base + inc)) < 1e-9
        ok &= bien
        print(f"  {'✓' if bien else '✗'} stock {pid}: {base:g} → {ahora:g} (esperado {base + inc:g})")

    movs = get("movimientos", tok).get("movimientos", [])
    mios = [m for m in movs if str(m.get("documento_tipo")) == "GASTO"
            and str(m.get("documento_id")) == folio_g]
    print(f"  {'✓' if len(mios) == 4 else '✗'} movimientos doc GASTO {folio_g}: {len(mios)} (esperados 4)")
    ok &= len(mios) == 4

    gastos2 = get("gastos", tok).get("gastos", [])
    g2 = next((g for g in gastos2 if str(g.get("folio")) == folio_g), {})
    pagada = str(g2.get("estado", "")).upper() == "PAGADA" or \
        abs(float(g2.get("pagado") or 0) - MONTO_TOTAL) < 0.01
    print(f"  {'✓' if pagada else '✗'} gasto {folio_g}: estado={g2.get('estado')} pagado={g2.get('pagado')}")
    ok &= pagada

    prods2 = get("productos", tok).get("productos", [])
    for pid, costo in [(p_rio["id"], COSTO_LAMBRIN), (p_bras["id"], COSTO_LAMBRIN),
                       (ids_ang["LAM-040"], COSTO_ANGULO), (ids_ang["LAM-041"], COSTO_ANGULO)]:
        pr = next((x for x in prods2 if str(x.get("id")) == str(pid)), {})
        bien = abs(float(pr.get("costo") or 0) - costo) < 0.01
        ok &= bien
        print(f"  {'✓' if bien else '✗'} costo {pr.get('codigo')}: ${pr.get('costo')} (esperado ${costo})")

    print(f"\n{'✅ COMPRA REGISTRADA Y VERIFICADA' if ok else '⚠️ REVISAR: algo no cuadra'} — {folio_g}")


if __name__ == "__main__":
    main()
