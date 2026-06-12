# -*- coding: utf-8 -*-
"""
Convierte los catálogos HTML individuales a PDF usando Chrome headless.
Guarda los PDFs en catalogos/pdf/
"""

import os
import sys
import subprocess
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
HTML_DIR = BASE_DIR / 'catalogos' / 'html'
PDF_DIR = BASE_DIR / 'catalogos' / 'pdf'

# Buscar Chrome instalado
CHROME_PATHS = [
    Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'),
    Path(r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'),
    Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
]

CHROME = None
for p in CHROME_PATHS:
    if p.exists():
        CHROME = p
        break

if not CHROME:
    print('ERROR: No se encontró Google Chrome instalado.')
    print('Rutas buscadas:')
    for p in CHROME_PATHS:
        print(f'  - {p}')
    sys.exit(1)

print(f'Chrome encontrado: {CHROME}')

PDF_DIR.mkdir(parents=True, exist_ok=True)

# Archivos HTML a convertir (excluir catalogo_premium.html si ya tiene PDF)
html_files = sorted([f for f in HTML_DIR.glob('catalogo_*.html')])

if not html_files:
    print('No se encontraron archivos catalogo_*.html en', HTML_DIR)
    sys.exit(0)

print(f'\nArchivos HTML a convertir: {len(html_files)}')
for f in html_files:
    print(f'  - {f.name}')

success = []
failed = []

for html_file in html_files:
    pdf_name = html_file.stem + '.pdf'
    pdf_path = PDF_DIR / pdf_name
    html_url = 'file:///' + str(html_file).replace('\\', '/').replace(' ', '%20')
    
    print(f'\nConvirtiendo {html_file.name} -> {pdf_name}')
    
    cmd = [
        str(CHROME),
        '--headless',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--run-all-compositor-stages-before-draw',
        '--print-to-pdf-no-header',
        f'--print-to-pdf={pdf_path}',
        html_url,
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if pdf_path.exists() and pdf_path.stat().st_size > 1024:
            size_mb = pdf_path.stat().st_size / 1024 / 1024
            print(f'  [OK] {pdf_name} ({size_mb:.2f} MB)')
            success.append(pdf_name)
        else:
            print(f'  [ERROR] No se generó el PDF o está vacío')
            if result.stderr:
                print(f'  {result.stderr[:500]}')
            failed.append(html_file.name)
    except subprocess.TimeoutExpired:
        print(f'  [ERROR] Timeout al convertir {html_file.name}')
        failed.append(html_file.name)
    except Exception as e:
        print(f'  [ERROR] {e}')
        failed.append(html_file.name)
    
    # Pequeña pausa para no saturar Chrome
    time.sleep(1)

print(f'\n{"="*50}')
print(f'Conversiones exitosas: {len(success)}')
for name in success:
    print(f'  - {name}')
if failed:
    print(f'\nConversiones fallidas: {len(failed)}')
    for name in failed:
        print(f'  - {name}')
print(f'\nPDFs guardados en: {PDF_DIR}')
