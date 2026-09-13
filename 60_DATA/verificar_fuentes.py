# -*- coding: utf-8 -*-
"""P1 - Puerta de drift: hoja Productos (maestro ERP) vs sitio web (products.json).

Cruza por `foto` (hoja) == `thumb` (products.json) — la relacion ya existe y
es exacta. Corre despues del build (necesita public/products.json y public/img).

Criterios:
  ERROR (exit 1) — drift duro que exige accion:
    * producto web sin fila en la hoja,
    * producto web cuya `foto` no existe en public/img (foto en Drive perdida),
    * fila de hoja con estado activo cuya `foto` no existe en public/img.
  AVISO (exit 0) — diferencias conocidas/aceptadas:
    * filas de hoja sin foto o marcadas REVISAR (los "solo-Excel"),
    * filas activas cuya foto no se publica en la web (si las fuera haber).

Uso:
    "C:\\...\\Python313\\python" 60_DATA/verificar_fuentes.py
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATASET = BASE / '60_DATA' / 'dataset_maestro.json'
PRODUCTS = BASE / 'public' / 'products.json'
PUBLIC_IMG = BASE / 'public' / 'img'

errores, avisos = [], []

if not DATASET.exists():
    sys.exit('ERROR: no existe 60_DATA/dataset_maestro.json. Correr primero exportar_productos.py')
if not PRODUCTS.exists():
    sys.exit('ERROR: no existe public/products.json. Correr primero el build (generar_web.py)')

dataset = json.loads(DATASET.read_text(encoding='utf-8'))
web = json.loads(PRODUCTS.read_text(encoding='utf-8'))['products']

hoja = dataset['productos']
por_foto = {}
for fila in hoja:
    por_foto.setdefault(str(fila.get('foto', '')).strip(), []).append(fila)

errores_web, ok_web = [], 0
for prod in web:
    thumb = str(prod.get('thumb', '')).strip()
    if thumb not in por_foto:
        errores_web.append(f"WEB sin hoja: {prod.get('name')!r} ({thumb})")
        continue
    if not (BASE / 'public' / thumb.replace('/', '\\')).exists() and not (BASE / 'public' / thumb).exists():
        errores_web.append(f"WEB foto perdida: {prod.get('name')!r} -> public/{thumb}")
        continue
    ok_web += 1

en_web = {str(p.get('thumb', '')).strip() for p in web}
huerfanas, revisar, activas_no_web = [], 0, []
for foto, filas in por_foto.items():
    if not foto:
        revisar += sum(1 for f in filas if not str(f.get('notas', '')).strip().upper().startswith('REVISAR'))
        continue
    for f in filas:
        if 'REVISAR' in str(f.get('notas', '')).upper():
            revisar += 1
            continue
        if foto not in en_web:
            rel = BASE / 'public' / foto
            if rel.exists():
                activas_no_web.append(f"{f.get('nombre')!r} ({foto})")
            else:
                errores.append(f"HOJA foto perdida en build: {f.get('nombre')!r} -> public/{foto}")

errores.extend(errores_web)
if activas_no_web:
    avisos.append(f"{len(activas_no_web)} fila(s) activa(s) de hoja con foto valida que NO se publican: " + '; '.join(activas_no_web[:5]) + (' ...' if len(activas_no_web) > 5 else ''))
if revisar:
    avisos.append(f"{revisar} fila(s) de hoja sin foto / marcadas REVISAR (solo-Excel, esperado).")

print(f'Hoja (ERP):      {len(hoja)} productos')
print(f'Web (products.json): {len(web)} productos')
print(f'Cruce foto==thumb OK: {ok_web}/{len(web)}')
print()
for a in avisos:
    print('AVISO:', a)
if errores:
    print()
    for e in errores:
        print('ERROR:', e)
    sys.exit(f'\nDRIFT DURO: {len(errores)} problema(s). Corregir la hoja/Drive antes de pushear.')
print('\nFUENTES CONSISTENTES')
