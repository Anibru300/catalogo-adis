#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Captura manual de movimientos financieros (ingresos/egresos) en la plataforma.

Sirve para volcar a la base de datos los movimientos que el dueño pasa en
crudo (por chat/WhatsApp) sin entrar al panel. Usa la misma API y credenciales
del admin (lee API_URL de 00_CORE/shared_js/admin_core.js).

Uso:
  python 60_DATA/capturar_movimiento.py gasto  --fecha 2026-10-06 --categoria "Honorarios" --monto 1500 --moneda MXN --descripcion "Pago al contador"
  python 60_DATA/capturar_movimiento.py ingreso --fecha 2026-10-06 --concepto "Venta de esquineros" --monto 560 --moneda MXN

  # o en lote desde un JSON:
  python 60_DATA/capturar_movimiento.py --batch movimientos.json

Formato del batch (lista):
  [{"tipo":"gasto","fecha":"2026-10-06","categoria":"Gasolina","monto":500,"moneda":"MXN","descripcion":""},
   {"tipo":"ingreso","fecha":"2026-10-06","concepto":"Reembolso","monto":950,"moneda":"USD","notas":""},
   {"tipo":"pago","fecha":"2026-10-06","gasto_folio":"GAS-2026-0001","monto":1500,"moneda":"MXN","metodo":"Transferencia"}]

Notas:
- Moneda por defecto: MXN. tipo_cambio: el de Config (fallback 18.5).
- fecha en yyyy-MM-dd (si se omite, hoy).
- `gasto` requiere endpoint ya desplegado (existe desde fase 5).
- `ingreso` requiere el redeploy de oct-2026 (folio ING-).
- `pago` liquida un gasto por folio (gasto_folio); si se omite el monto, paga
  el saldo completo. La hoja registra el folio PAG- y baja el saldo del gasto.
- Cuando el dueño confirme que un gasto YA se pagó, capturar el gasto y su
  pago con la misma fecha (así el flujo de caja refleja la salida real).
"""
import argparse
import json
import re
import sys
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
    sys.exit("No encontré CONFIG.API_URL en 00_CORE/shared_js/admin_core.js")

USUARIO = "Adis"
CLAVE = "Adisdiseño2026"


def post(payload):
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "text/plain;charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get(action, token):
    url = f"{API_URL}?action={action}&token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def login():
    d = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})
    if not d.get("ok") or not d.get("token"):
        sys.exit(f"Login falló: {d}")
    return d["token"]


def capturar(mov, token):
    """Un movimiento -> POST a la API. Devuelve (ok, mensaje)."""
    tipo = mov.get("tipo", "").lower()
    base = {"fecha": mov.get("fecha", ""), "moneda": mov.get("moneda", "MXN"),
            "tipo_cambio": mov.get("tipo_cambio", ""), "token": token}
    if tipo == "gasto":
        payload = dict(base, tipo="gasto", categoria=mov.get("categoria", ""),
                       descripcion=mov.get("descripcion", mov.get("concepto", "")),
                       monto=mov.get("monto"))
    elif tipo == "ingreso":
        payload = dict(base, tipo="ingreso", concepto=mov.get("concepto", mov.get("categoria", "")),
                       metodo=mov.get("metodo", ""), notas=mov.get("notas", mov.get("descripcion", "")),
                       monto=mov.get("monto"))
    elif tipo == "pago":
        folio = mov.get("gasto_folio", "")
        gastos = get("gastos", token).get("gastos", [])
        g = next((x for x in gastos if str(x.get("folio", "")) == folio), None)
        if not g:
            return False, f"pago RECHAZADO: no existe gasto con folio {folio!r}"
        saldo = float(g.get("monto") or 0) - float(g.get("pagado") or 0)
        payload = dict(base, tipo="gasto_pago", gasto_id=g.get("id"),
                       monto=mov.get("monto") or saldo,
                       metodo=mov.get("metodo", ""), notas=mov.get("notas", ""))
        tipo = f"pago({folio})"
    else:
        return False, f"tipo desconocido: {tipo!r} (usa gasto|ingreso|pago)"
    try:
        d = post(payload)
    except Exception as e:
        return False, f"error de red: {e}"
    if d.get("ok"):
        return True, f"{tipo} {d.get('folio', '')} ✓".strip()
    err = (d.get("error") or {}).get("message", str(d))
    return False, f"{tipo} RECHAZADO: {err}"


def main():
    ap = argparse.ArgumentParser(description="Captura movimientos financieros en la plataforma")
    ap.add_argument("tipo", nargs="?", choices=["gasto", "ingreso"], help="tipo de movimiento (si no hay --batch)")
    ap.add_argument("--batch", help="archivo JSON con una lista de movimientos")
    ap.add_argument("--fecha", help="yyyy-MM-dd (default: hoy en Hermosillo)")
    ap.add_argument("--categoria", help="categoría (gasto)")
    ap.add_argument("--concepto", "--descripcion", dest="concepto", help="concepto/descripción")
    ap.add_argument("--monto", type=float, help="monto (> 0)")
    ap.add_argument("--moneda", default="MXN", help="MXN|USD (default MXN)")
    ap.add_argument("--metodo", default="", help="método de pago/cobro (ingreso)")
    ap.add_argument("--notas", default="")
    ap.add_argument("--listo", action="store_true", help="no pedir confirmación interactiva")
    args = ap.parse_args()

    if args.batch:
        movs = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    elif args.tipo:
        monto = args.monto
        if not monto:
            ap.error("--monto es obligatorio")
        movs = [{"tipo": args.tipo, "fecha": args.fecha or "", "categoria": args.categoria or "",
                 "concepto": args.concepto or "", "monto": monto, "moneda": args.moneda,
                 "metodo": args.metodo, "notas": args.notas}]
    else:
        ap.error("indica gasto/ingreso o --batch")

    print(f"{len(movs)} movimiento(s) a capturar:")
    for m in movs:
        desc = m.get("categoria") or m.get("concepto") or m.get("descripcion") or ""
        print(f"  - [{m.get('tipo','?')}] {m.get('fecha','(hoy)')}  {m.get('moneda','MXN')} {m.get('monto')}  {desc}")

    if not args.listo:
        if input("¿Subir a la base de datos? [s/N]: ").strip().lower() not in ("s", "si", "sí", "y"):
            sys.exit("Cancelado.")

    token = login()
    ok_count = 0
    for m in movs:
        ok, msg = capturar(m, token)
        print(("  " if ok else "  ✗ ") + msg)
        ok_count += ok
    print(f"\n{ok_count}/{len(movs)} capturados.")
    sys.exit(0 if ok_count == len(movs) else 1)


if __name__ == "__main__":
    import urllib.parse  # noqa: E402  (usado en get())

    main()
