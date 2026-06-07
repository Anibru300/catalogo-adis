# -*- coding: utf-8 -*-
import os, re, json
from pathlib import Path

base = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
errors = []
warnings = []

html_files = list(base.glob('*.html'))
all_files = set(str(p.relative_to(base)).replace('\\','/') for p in base.rglob('*') if p.is_file())

for html_path in html_files:
    content = html_path.read_text(encoding='utf-8')
    
    # Enlaces internos
    for m in re.finditer(r'href=["\']([^"\']+)["\']', content):
        href = m.group(1)
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or href.startswith('https://wa.me') or href.startswith('tel:') or href.startswith('javascript:'):
            continue
        decoded = href.replace('%20', ' ')
        if decoded not in all_files and decoded.lstrip('/') not in all_files:
            test = decoded.lstrip('/')
            if test not in all_files:
                errors.append(f'[{html_path.name}] Enlace roto: {href}')
    
    # Imagenes
    for m in re.finditer(r'src=["\']([^"\']+)["\']', content):
        src = m.group(1)
        if src.startswith('http') or src.startswith('data:'):
            continue
        decoded = src.replace('%20', ' ')
        if decoded not in all_files and decoded.lstrip('/') not in all_files:
            errors.append(f'[{html_path.name}] Imagen rota: {src}')
    
    # Background images
    for m in re.finditer(r'url\(["\']?([^"\')]+)["\']?\)', content):
        url = m.group(1)
        if url.startswith('http'):
            continue
        decoded = url.replace('%20', ' ')
        if decoded not in all_files and decoded.lstrip('/') not in all_files:
            errors.append(f'[{html_path.name}] Background roto: {url}')

# products.json
products_path = base / 'products.json'
if products_path.exists():
    try:
        data = json.loads(products_path.read_text(encoding='utf-8'))
        for p in data:
            thumb = p.get('thumb', '')
            if thumb and thumb.replace('%20',' ') not in all_files and thumb.lstrip('/').replace('%20',' ') not in all_files:
                errors.append(f'[products.json] Thumb rota: {thumb} para {p.get("name")}')
    except Exception as e:
        errors.append(f'[products.json] Error JSON: {e}')

print('=== ERRORES ===')
for e in errors[:80]:
    print(e)
print(f'Total errores: {len(errors)}')
