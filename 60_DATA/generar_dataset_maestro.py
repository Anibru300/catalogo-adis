# -*- coding: utf-8 -*-
"""Fase 1 - Genera el dataset maestro para importar a Google Sheets.

- 251 productos del sitio web clasificados por categoria/subcategoria
- 10 productos del Excel sin coincidencia web (marcados REVISION MANUAL)
- Codigos: los del Excel se conservan; los demas se generan por categoria
- Costos del Excel donde hay coincidencia; stock por almacen
Salida: scripts/auditoria/dataset_maestro.json
"""
import json, unicodedata, re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
PREFIX = {
    'Placas PVC': 'HJPVC', 'Lambrin WPC': 'LAM', 'Revestimiento Flexible': 'RVF',
    'Plafon PVC': 'PLF', 'Paneles tridimensionales': 'P3D', 'Vigas PVC': 'VIG',
    'Pisos': 'PIS', 'Zacate': 'ZAC', 'Cladding': 'CLA',
}
# Placas PVC web ya usan HJPVC1..17 sin guion -> las nuevas usan serie HJPVC-1xx
def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]', '', s)

site = json.load(open(BASE / 'public/products.json', encoding='utf-8'))['products']
inv = json.load(open('/tmp/inventario_extraido.json', encoding='utf-8'))
excel_items = inv['codigos']

site_idx = {}
for p in site:
    site_idx.setdefault(norm(p['name']), p)

excel_by_code = {}
matched_names = {}
for code, desc, prov, unid, costo, img in excel_items:
    item = {'codigo': code, 'desc': desc, 'proveedor': prov, 'unidad': unid,
            'costo': costo, 'img': img}
    hit = site_idx.get(norm(desc))
    if not hit and img:
        fname = re.split(r'[\\/]', img)[-1].rsplit('.', 1)[0]
        hit = site_idx.get(norm(fname))
    if hit:
        matched_names[hit['name']] = code
        item['web'] = hit
    excel_by_code[code] = item

# contadores por prefijo (los codigos Excel existentes no se tocan)
counters = {c: 0 for c in PREFIX}
def nuevo_codigo(categoria):
    if categoria == 'Placas PVC':
        counters[categoria] += 1
        return f"HJPVC-{100 + counters[categoria]}"
    counters[categoria] += 1
    return f"{PREFIX[categoria]}-{counters[categoria]:03d}"

productos = []
fotos = {p['name']: p['thumb'] for p in site}
for p in site:
    code = matched_names.get(p['name']) or nuevo_codigo(p['category'])
    excel_item = excel_by_code.get(code, {})
    productos.append({
        'codigo': code, 'nombre': p['name'],
        'descripcion': '', 'categoria': p['category'],
        'subcategoria': p['subcategory'] or '',
        'proveedor': (excel_item.get('proveedor') or ''),
        'costo': excel_item.get('costo') or 0,
        'precio': 0, 'unidad': (excel_item.get('unidad') or 'pieza').lower(),
        'stock_minimo': 0, 'moneda': 'MXN',
        'foto': p['thumb'], 'estado': 'activo',
        'notas': 'Importado de la pagina web',
    })

# productos del Excel sin coincidencia web -> REVISION MANUAL
for code, item in excel_by_code.items():
    if 'web' in item:
        continue
    productos.append({
        'codigo': code, 'nombre': item['desc'], 'descripcion': '',
        'categoria': 'Placas PVC', 'subcategoria': '',
        'proveedor': item['proveedor'], 'costo': item['costo'] or 0,
        'precio': 0, 'unidad': item['unidad'].lower(), 'stock_minimo': 0,
        'moneda': 'MXN', 'foto': '', 'estado': 'activo',
        'notas': 'REVISION MANUAL - importado del Excel sin coincidencia en la web',
    })

# stock por almacen desde el Excel
stock = []
for alm, filas in (('Nogales', inv['nogales']), ('Decosonora', inv['decosonora']), ('Rio rico', inv['riorico'])):
    for code, desc, prov, cant, unid in filas:
        stock.append({'codigo': code, 'almacen': alm, 'cantidad': cant})

out = {'productos': productos, 'stock': stock}
json.dump(out, open(BASE / 'scripts/auditoria/dataset_maestro.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"Productos: {len(productos)} (web {len(site)} + excel-solo {len(productos)-len(site)})")
print(f"Stock por almacen: {len(stock)} filas")
revisar = [p['codigo'] for p in productos if 'REVISION' in p['notas']]
print(f"Revision manual: {len(revisar)} -> {revisar}")
codigos = [p['codigo'] for p in productos]
dupes = {c for c in codigos if codigos.count(c) > 1}
print(f"Codigos duplicados: {dupes or 'NINGUNO'}")
