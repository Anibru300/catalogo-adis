# -*- coding: utf-8 -*-
"""P1 - Exporta la hoja Productos (fuente unica de verdad ERP) a dataset_maestro.json.

Direccion oficial hoja -> repo: este script reemplaza el flujo historico de
importacion (importar_maestro.py subia el dataset a Sheets). Ahora la hoja ES
el maestro y este export la vuelve versionable en el repo para:

  * que 60_DATA/verificar_fuentes.py detecte drift hoja vs sitio web, y
  * futura migracion del build a consumir la hoja directamente (Opcion A del
    plan en 00_CORE/config/FUENTES_DE_PRODUCTOS.md).

Uso:
    "C:\\...\\Python313\\python" 60_DATA/exportar_productos.py
Requiere backend desplegado y credenciales validas (ver 00_CORE/backend/GUIA_DESPLIEGUE.md).
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]


def _url_backend():
    """M1: URL desde 00_CORE/config/plataforma.json (fuente unica), con fallback."""
    try:
        cfg = json.loads((BASE / '00_CORE' / 'config' / 'plataforma.json').read_text(encoding='utf-8'))
        return cfg['url_backend']
    except Exception:
        return 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'


URL = _url_backend()
CREDS = {'usuario': 'Adis', 'clave': 'Adisdiseño2026'}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto('about:blank')

    def post(payload):
        r = pg.evaluate("""async ({URL, payload}) => {
          const res = await fetch(URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON.stringify(payload)});
          return await res.text();
        }""", {'URL': URL, 'payload': payload})
        return json.loads(r)

    def get(qs):
        r = pg.evaluate("""async ({URL, qs}) => {
          const res = await fetch(URL + '?' + qs);
          return await res.text();
        }""", {'URL': URL, 'qs': qs})
        return json.loads(r)

    login = post({'tipo': 'login', **CREDS})
    assert login.get('ok'), f'Login fallo: {login}'
    token = login['token']
    print('1. Login OK')

    productos = get(f'action=productos&token={token}')['productos']
    stock = get(f'action=stock&token={token}')['stock']
    print(f'2. Leidos {len(productos)} productos y {len(stock)} filas de stock')

    out = {
        'productos': productos,
        'stock': stock,
        '_exportado': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        '_fuente': URL,
    }
    dest = BASE / '60_DATA' / 'dataset_maestro.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'3. Escrito {dest.relative_to(BASE)} ({dest.stat().st_size} bytes)')
    b.close()

print('EXPORTACION COMPLETA')
