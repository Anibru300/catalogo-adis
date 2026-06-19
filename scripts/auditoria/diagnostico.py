# -*- coding: utf-8 -*-
import os, re, json
from pathlib import Path

base = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
web_dir = base / 'public'
errors = []
warnings = []

html_files = list(web_dir.glob('*.html'))
all_files = set(str(p.relative_to(web_dir)).replace('\\','/') for p in web_dir.rglob('*') if p.is_file())

for html_path in html_files:
    content = html_path.read_text(encoding='utf-8')
    
    # Enlaces internos
    for m in re.finditer(r'href=["\']([^"\']+)["\']', content):
        href = m.group(1)
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or href.startswith('https://wa.me') or href.startswith('tel:') or href.startswith('javascript:'):
            continue
        if '${' in href:
            continue
        decoded = href.split('#')[0].replace('%20', ' ')
        if decoded and decoded not in all_files and decoded.lstrip('/') not in all_files:
            errors.append(f'[{html_path.name}] Enlace roto: {href}')
    
    # Imagenes
    for m in re.finditer(r'src=["\']([^"\']+)["\']', content):
        src = m.group(1)
        if src.startswith('http') or src.startswith('data:'):
            continue
        if '${' in src:
            continue
        decoded = src.split('#')[0].replace('%20', ' ')
        if decoded and decoded not in all_files and decoded.lstrip('/') not in all_files:
            errors.append(f'[{html_path.name}] Imagen rota: {src}')
    
    # Background images
    for m in re.finditer(r'url\(["\']?([^"\')]+)["\']?\)', content):
        url = m.group(1)
        if url.startswith('http'):
            continue
        if '${' in url:
            continue
        decoded = url.split('#')[0].replace('%20', ' ')
        if decoded and decoded not in all_files and decoded.lstrip('/') not in all_files:
            errors.append(f'[{html_path.name}] Background roto: {url}')

# products.json
products_path = web_dir / 'products.json'
if products_path.exists():
    try:
        data = json.loads(products_path.read_text(encoding='utf-8'))
        for p in data.get('products', []):
            thumb = p.get('thumb', '')
            if thumb and '${' not in thumb and thumb.replace('%20',' ') not in all_files and thumb.lstrip('/').replace('%20',' ') not in all_files:
                errors.append(f'[products.json] Thumb rota: {thumb} para {p.get("name")}')
    except Exception as e:
        errors.append(f'[products.json] Error JSON: {e}')

print('=== ERRORES ===')
for e in errors[:80]:
    print(e)
print(f'Total errores: {len(errors)}')
