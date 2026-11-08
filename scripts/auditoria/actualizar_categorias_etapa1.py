#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincronizacion de catalogos de categorias para Etapa 1 (PREPARAR, no desplegar).

Que hace cuando se autorice (--aplicar):
  1. Agrega a Config las categorias nuevas de gastos/ingresos que falten.
  2. Con --quitar-viejas: retira del catalogo las categorias antiguas ya no usadas
     (NO modifica el texto de categoria de ningun gasto historico; solo el catalogo
     de sugerencias del dropdown).
  3. Carga en Config el mapeo de sugerencia categoria -> naturaleza (nat_<categoria>).

Por defecto es DRY-RUN (solo lectura). En produccion exige --produccion para escribir.
Los cambios se pueden revertir desde el tab Configuracion del panel (quitar/agregar).
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
API = os.environ.get("ADIS_API_URL")
prod = None
for cand in ["00_CORE/shared_js/admin_core.js", "00_CORE/shared_js/admin_core.src.js"]:
    p = ROOT / cand
    if p.exists():
        m = re.search(r"API_URL:\s*'([^']+)'", p.read_text(encoding="utf-8"))
        if m:
            prod = m.group(1)
            API = API or prod
            break
if not API:
    sys.exit("No encontre CONFIG.API_URL")

USUARIO = os.environ.get("ADIS_USUARIO", "Adis")
CLAVE = os.environ.get("ADIS_CLAVE", "Adisdiseño2026")

CATS_GASTOS_NUEVAS = ["Compra de mercancía", "Materiales para obra", "Gasolina y combustible", "Viáticos",
    "Alimentos de trabajo", "Nómina", "Renta", "Servicios", "Paquetería", "Papelería", "Mantenimiento",
    "Contabilidad", "Publicidad y marketing", "Plataformas y software", "Equipo y maquinaria", "Muestrarios",
    "Gastos personales", "Gastos médicos personales", "Retiros del propietario", "Otros"]
CATS_INGRESOS_NUEVAS = ["Venta de mercancía", "Servicios de instalación", "Anticipo de cliente", "Cobro de proyecto",
    "Otros ingresos operativos", "Aportación del propietario", "Otros"]
# catalogo viejo a retirar (solo con --quitar-viejas); el texto de los gastos historicos NO cambia
CATS_VIEJAS = ["Compra de material", "Materiales", "Compra de inventario", "Publicidad", "Inversión",
    "Envíos", "Honorarios", "Equipos", "Muestrario", "Otro", "Gasolina", "Alimentos", "Luz", "Agua",
    "Venta de activos", "Reembolso", "Otro ingreso"]
# NOTA 2026-11-07: 'Mantenimiento' se REMOVIO de esta lista: colisiona con la
# categoria NUEVA del mismo nombre (esta en CATS_GASTOS_NUEVAS y en uso). La
# categoria viva se queda; nada que retirar.
NAT_SUGERIDA = {"Compra de mercancía": "inventario", "Materiales para obra": "costo_directo",
    "Gasolina y combustible": "operativo", "Viáticos": "operativo", "Alimentos de trabajo": "operativo",
    "Nómina": "operativo", "Renta": "operativo", "Servicios": "operativo", "Paquetería": "operativo",
    "Papelería": "operativo", "Mantenimiento": "operativo", "Contabilidad": "operativo",
    "Publicidad y marketing": "operativo", "Plataformas y software": "operativo",
    "Equipo y maquinaria": "inversion", "Muestrarios": "inversion", "Gastos personales": "retiro",
    "Gastos médicos personales": "retiro", "Retiros del propietario": "retiro", "Otros": "por_clasificar"}


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true", help="escribe (default: dry-run)")
    ap.add_argument("--quitar-viejas", action="store_true", help="retira del catalogo las categorias viejas")
    ap.add_argument("--produccion", action="store_true", help="permite escribir contra la URL de produccion")
    args = ap.parse_args()

    es_prod = prod and API.rstrip("/") == prod.rstrip("/")
    if args.aplicar and es_prod and not args.produccion:
        sys.exit("BLOQUEADO: escritura en PRODUCCION requiere --produccion explicito.")

    tok = post({"tipo": "login", "usuario": USUARIO, "clave": CLAVE})
    if not tok.get("ok"):
        sys.exit(f"Login fallo: {tok}")
    token = tok["token"]
    cfg = get("config", token)
    act_g = [c.lower() for c in cfg.get("categorias_gastos", [])]
    act_i = [c.lower() for c in cfg.get("categorias_ingresos", [])]

    faltan_g = [c for c in CATS_GASTOS_NUEVAS if c.lower() not in act_g]
    faltan_i = [c for c in CATS_INGRESOS_NUEVAS if c.lower() not in act_i]
    sobran = [c for c in CATS_VIEJAS if (c.lower() in act_g or c.lower() in act_i)]
    mapa_actual = cfg.get("mapa_naturalezas", {})
    mapa_nuevo = {c: n for c, n in NAT_SUGERIDA.items() if mapa_actual.get(c) != n}

    print("Plan de sincronizacion (dry-run):" if not args.aplicar else "Aplicando:")
    print(f"  +{len(faltan_g)} categorias de gasto nuevas: {faltan_g}")
    print(f"  +{len(faltan_i)} categorias de ingreso nuevas: {faltan_i}")
    print(f"  mapeo nat_* a cargar/actualizar: {len(mapa_nuevo)} categorias")
    if args.quitar_viejas:
        print(f"  -{len(sobran)} categorias viejas a retirar del catalogo: {sobran}")
    else:
        print(f"  (categorias viejas se conservan; usa --quitar-viejas para retirarlas: {sobran})")

    if not args.aplicar:
        print("\nDry-run: nada escrito. Con tu autorizacion: --aplicar --produccion [--quitar-viejas]")
        return

    ok = fail = 0
    def accion(payload, desc):
        nonlocal ok, fail
        r = post(dict(payload, token=token))
        if r.get("ok"):
            ok += 1; print(f"  OK {desc}")
        else:
            fail += 1; print(f"  FAIL {desc}: {r}")
    for c in faltan_g:
        accion({"tipo": "categoria", "accion": "agregar", "clase": "gastos", "nombre": c}, f"+gasto {c}")
    for c in faltan_i:
        accion({"tipo": "categoria", "accion": "agregar", "clase": "ingresos", "nombre": c}, f"+ingreso {c}")
    if mapa_nuevo:
        accion({"tipo": "config", "mapa_naturalezas": mapa_nuevo}, f"mapa_naturalezas ({len(mapa_nuevo)})")
    if args.quitar_viejas:
        for c in sobran:
            clase = "ingresos" if c.lower() in act_i and c.lower() not in act_g else "gastos"
            accion({"tipo": "categoria", "accion": "quitar", "clase": clase, "nombre": c}, f"-vieja {c}")
    print(f"\nSincronizados: {ok} · fallos: {fail}")
    cfg2 = get("config", token)
    print("categorias_gastos:", len(cfg2.get("categorias_gastos", [])), "| categorias_ingresos:",
          len(cfg2.get("categorias_ingresos", [])), "| mapa_naturalezas:", len(cfg2.get("mapa_naturalezas", {})))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
