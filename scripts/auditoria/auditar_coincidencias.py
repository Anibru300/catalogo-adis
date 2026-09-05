# -*- coding: utf-8 -*-
"""Fase 0 - Auditoria: cruza el Excel de inventario con los productos del sitio web."""
import json, unicodedata, re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]', '', s)

site = json.load(open(BASE / 'public/products.json', encoding='utf-8'))['products']
inv = json.load(open('/tmp/inventario_extraido.json', encoding='utf-8'))
excel_items = inv['codigos']  # [codigo, desc, proveedor, unidad, costo, ruta_img]

site_idx = {}
for p in site:
    site_idx.setdefault(norm(p['name']), p)

print("=== Coincidencias Excel <-> Web ===")
matched = {}
for item in excel_items:
    code, desc, prov, unid, costo, img = item
    hit = site_idx.get(norm(desc))
    if not hit and img:
        fname = re.split(r'[\\/]', img)[-1].rsplit('.', 1)[0]
        hit = site_idx.get(norm(fname))
    print(f"{code:14} {desc:22} -> {'WEB: ' + hit['name'] + ' (' + hit['category'] + '/' + str(hit['subcategory']) + ')' if hit else 'SIN COINCIDENCIA WEB'}")
    if hit:
        matched[code] = hit['name']
print(f"\nCoincidencias: {len(matched)}/{len(excel_items)}")

print("\n=== Categorias del sitio ===")
cats = {}
for p in site:
    cats.setdefault(p['category'], set()).add(p['subcategory'])
for c, subs in cats.items():
    n = sum(1 for p in site if p['category'] == c)
    print(f"  {c} ({n} prod)")

json.dump({'matched': matched, 'total_site': len(site)}, open('/tmp/auditoria.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\nGuardado /tmp/auditoria.json")
