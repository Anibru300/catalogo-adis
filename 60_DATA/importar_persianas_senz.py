#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Importa la línea Persianas y Cortinas del proveedor SENZ al catálogo local.

Descarga las fotos oficiales de senz.com.mx (el dueño es distribuidor) y las
acomoda en CATALOGO FINAL con la convención del sitio:
  <Categoria>/<Subcategoria>/<Producto>.jpg (+ <Producto>-2/3/4.jpg galería)

Uso: python 60_DATA/importar_persianas_senz.py
"""
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = Path("G:/Mi unidad/ADIS DISEÑO/CATALOGO FINAL")

BASE = "https://senz.com.mx/assets/images/website"

# dir en senz (bajo /website/) -> (nombre de producto en catálogo, subcarpeta destino)
PERSIANAS = [
    ("persianas/enrollable",     "Persianas Enrollables",        "10.1 Persianas"),
    ("persianas/sheerelegance",  "Cortina Duo Sheer Elegance",   "10.1 Persianas"),
    ("persianas/romana",         "Persiana Romana",              "10.1 Persianas"),
    ("persianas/panel",          "Panel Japones",                "10.1 Persianas"),
    ("persianas/vienna",         "Persiana Vienna",              "10.1 Persianas"),
    ("persianas/cellular",       "Persiana Cellular",            "10.1 Persianas"),
]
CORTINAS = [("cortinas/cortinas", "Cortinas Personalizadas", "10.2 Cortinas")]

CAT_DIR = "10. Persianas y Cortinas"


def descargar(url, dest, reintentos=3):
    for i in range(reintentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=60).read()
            if len(data) < 2000:  # probable fallback HTML del SPA
                return False
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return True
        except Exception as e:
            if i == reintentos - 1:
                print(f"    ✗ {url} — {e}")
            time.sleep(1)
    return False


def main():
    if not CATALOGO.exists():
        sys.exit(f"No existe {CATALOGO} — ¿Google Drive montado?")
    destino = CATALOGO / CAT_DIR
    total, ok = 0, 0

    for dir_senz, nombre, sub in PERSIANAS + CORTINAS:
        carpeta = destino / sub
        # foto principal = img-1; galería = img-2, img-3, bg-main
        plan = [("img-1.jpg", f"{nombre}.jpg"),
                ("img-2.jpg", f"{nombre}-2.jpg"),
                ("img-3.jpg", f"{nombre}-3.jpg"),
                ("bg-main.jpg", f"{nombre}-4.jpg")]
        print(f"{nombre}:")
        for src, dst in plan:
            total += 1
            if descargar(f"{BASE}/{dir_senz}/{src}", carpeta / dst):
                ok += 1
                print(f"    ✓ {dst}")
            else:
                print(f"    – {src} no disponible")

    print(f"\n{ok}/{total} fotos descargadas en {destino}")


if __name__ == "__main__":
    main()
