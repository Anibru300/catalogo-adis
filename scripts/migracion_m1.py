#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración M1 (one-off): extrae CORE de generar_web.py hacia 00_CORE/.

Hace cirugía de texto por anclas exactas. No ejecuta nada del generador.
Tras correrlo: py_compile + rebuild + comparación de hashes.
"""
import pathlib, re, sys

ROOT = pathlib.Path(r'C:\Users\Carlos\Desktop\Pagina')
GW = ROOT / 'generar_web.py'
CORE = ROOT / '00_CORE'
src = GW.read_text(encoding='utf-8')
orig_len = len(src)
report = []

def swap(old, new, label, count=1):
    global src
    n = src.count(old)
    assert n == count, f'{label}: se esperaban {count} ocurrencias, hay {n}'
    src = src.replace(old, new, count)
    report.append(f'OK  {label}')

# ---------------------------------------------------------------- 1. plataforma.json
URL = 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'
plataforma = '''{
  "url_backend": "%s",
  "site_url": "https://xn--adis-diseo-19a.com/",
  "whatsapp": "15208392877",
  "looker_studio_url": "",
  "catalog_dir": "G:\\\\Mi unidad\\\\ADIS DISEÑO\\\\CATALOGO FINAL",
  "material_media_dir": "Material de Facebock",
  "notas": {
    "url_backend": "Fuente UNICA de la URL del Apps Script. Si cambia el redeploy, actualizar SOLO aqui.",
    "whatsapp": "Numero del negocio (CTA del sitio y panel).",
    "catalog_dir": "Carpeta del catalogo fuente en Google Drive (solo lectura). Usada por scan_catalog/sync_images.",
    "material_media_dir": "Carpeta local fuente de public/media (sin tracking en git). Usada por sync_media. En M3 la ruta quedara solo en config."
  }
}
''' % URL
(CORE / 'config' / 'plataforma.json').write_text(plataforma, encoding='utf-8')
report.append('OK  00_CORE/config/plataforma.json creado')

# ------------------------------------------------- 2. CSS -> design-system (verbatim)
m = re.search(r"CSS = '''\n", src)
assert m, 'inicio de CSS no encontrado'
start = m.end()
end = src.index("\n'''", start)
css_content = src[start:end] + '\n'
(CORE / 'design-system' / 'sitio-publico.css').write_text(css_content, encoding='utf-8')
src = src[:m.start()] + "CSS = (CORE_DIR / 'design-system' / 'sitio-publico.css').read_text(encoding='utf-8')\n" + src[end + len("\n'''"):]
report.append(f'OK  CSS extraido ({len(css_content)} chars) -> 00_CORE/design-system/sitio-publico.css')

# ------------------------------------------------- 3. TRANSLATIONS -> i18n
m = re.search(r'TRANSLATIONS = \{\n', src)
assert m, 'inicio de TRANSLATIONS no encontrado'
tstart = m.start()
tend = src.index('\n}\n', tstart) + len('\n}\n')
tr_block = src[tstart:tend]
i18n_header = ('# Textos i18n del sitio publico (ES/EN). Extraido de generar_web.py en M1.\n'
               '# NO renombrar claves: las usa generar_web.py y el toggle JS (data-i18n).\n\n')
(CORE / 'i18n' / 'translations.py').write_text(i18n_header + tr_block + '\n', encoding='utf-8')
src = src[:tstart] + 'from translations import TRANSLATIONS  # dict en 00_CORE/i18n/translations.py (M1)\n' + src[tend:]
report.append('OK  TRANSLATIONS extraido -> 00_CORE/i18n/translations.py')

# ------------------------------------------------- 4. JSONs de datos -> 00_CORE/i18n
for jname in ('traducciones_productos.json', 'investigacion_data.json', 'investigacion_data_en.json'):
    (ROOT / jname).rename(CORE / 'i18n' / jname)
    swap(f"BASE_DIR / '{jname}'", f"CORE_DIR / 'i18n' / '{jname}'", f'ruta {jname}')

# ------------------------------------------------- 5. helpers puros -> shared/web_utils.py
def cut_func(name, new_src_label=None):
    """Extrae 'def name(...): ...' (hasta el siguiente def de nivel 0 o bloque) hacia un pool."""
    global src
    m = re.search(rf'\ndef {name}\(', src)
    assert m, f'def {name} no encontrada'
    start = m.start() + 1
    m2 = re.search(r'\n(?=def |\n# =|\n[A-Z_]+ =|\Z)', src[start:])
    assert m2, f'fin de {name} no localizado'
    block = src[start:start + m2.start()]
    src = src[:start] + src[start + m2.start():]
    return block

pool = []
for fn in ('svg_icon', 'minify_css', 'minify_html', 'json_ld',
           'whatsapp_url', 'build_whatsapp_message', 'md_to_html', 'clean_name', 'slugify'):
    pool.append(cut_func(fn))
    report.append(f'OK  def {fn} extraida')

# ICONS_SVG: bloque previo a svg_icon (ya cortado); localizarlo ahora
mi = re.search(r"ICONS_SVG = \{\n", src)
assert mi, 'ICONS_SVG no encontrado'
iend = src.index('\n}\n', mi.start()) + len('\n}\n')
icons_block = src[mi.start():iend]
src = src[:mi.start()] + src[iend:]
pool.insert(0, icons_block)
report.append('OK  ICONS_SVG extraido')

header = ('# Helpers puros compartidos (sin estado del generador).\n'
          '# Extraidos de generar_web.py en M1. Solo stdlib.\n\n'
          'import re\nimport json\nimport unicodedata\nimport urllib.parse\n\n')
(CORE / 'shared' / 'web_utils.py').write_text(header + '\n\n'.join(b.rstrip() for b in pool) + '\n', encoding='utf-8')
report.append('OK  -> 00_CORE/shared/web_utils.py')

# importar el pool en generar_web (tras las rutas de 00_CORE que añadimos abajo)
swap("from translations import TRANSLATIONS  # dict en 00_CORE/i18n/translations.py (M1)\n",
     "from translations import TRANSLATIONS  # dict en 00_CORE/i18n/translations.py (M1)\nfrom web_utils import *  # helpers puros: minify, json_ld, svg_icon, whatsapp, md, slugify (M1)\n",
     'import web_utils')

# ------------------------------------------------- 6. infra de rutas + config en generar_web
swap("BASE_DIR = Path(__file__).resolve().parent\n",
     "BASE_DIR = Path(__file__).resolve().parent\n"
     "CORE_DIR = BASE_DIR / '00_CORE'\n"
     "import sys\n"
     "sys.path.insert(0, str(CORE_DIR / 'i18n'))\n"
     "sys.path.insert(0, str(CORE_DIR / 'shared'))\n"
     "import json as _json\n"
     "PLATAFORMA = _json.loads((CORE_DIR / 'config' / 'plataforma.json').read_text(encoding='utf-8'))\n",
     'infra CORE_DIR/PLATAFORMA')

swap("CATALOG_DIR = Path(r'G:\\Mi unidad\\ADIS DISEÑO\\CATALOGO FINAL')",
     "CATALOG_DIR = Path(PLATAFORMA['catalog_dir'])", 'CATALOG_DIR desde config')

swap("LEADS_URL = '%s'    # Recibe los envios del formulario de contacto (pestaña Leads)" % URL,
     "LEADS_URL = PLATAFORMA['url_backend']    # Recibe los envios del formulario de contacto (pestaña Leads)", 'LEADS_URL')
swap("REVIEWS_URL = '%s'  # Mismo script; expone las resenas para el sitio" % URL,
     "REVIEWS_URL = PLATAFORMA['url_backend']  # Mismo script; expone las resenas para el sitio", 'REVIEWS_URL')

swap("SITE_URL = 'https://xn--adis-diseo-19a.com/'", "SITE_URL = PLATAFORMA['site_url']", 'SITE_URL')

swap("    src_dir = BASE_DIR / 'Material de Facebock'",
     "    src_dir = BASE_DIR / PLATAFORMA['material_media_dir']", 'sync_media dir')

# ------------------------------------------------- 7. inyeccion de config en admin.html al copiar
swap("""    admin_src = BASE_DIR / 'admin' / 'index.html'
    if admin_src.exists():
        shutil.copy2(admin_src, OUTPUT_DIR / 'admin.html')
        print("admin.html copiado al sitio")""",
     """    admin_src = BASE_DIR / 'admin' / 'index.html'
    if admin_src.exists():
        # M1: inyectar config central en la copia (salida identica si los valores no cambiaron)
        admin_html = admin_src.read_text(encoding='utf-8')
        admin_html = re.sub(r"(API_URL:\\s*')[^']*(')", lambda m: m.group(1) + PLATAFORMA['url_backend'] + m.group(2), admin_html, count=1)
        admin_html = re.sub(r"(WHATSAPP:\\s*')[^']*(')", lambda m: m.group(1) + PLATAFORMA['whatsapp'] + m.group(2), admin_html, count=1)
        (OUTPUT_DIR / 'admin.html').write_text(admin_html, encoding='utf-8')
        print("admin.html copiado al sitio (config inyectada desde 00_CORE/config/plataforma.json)")""",
     'admin copy con inyeccion')

GW.write_text(src, encoding='utf-8')
report.append(f'OK  generar_web.py reescrito ({orig_len} -> {len(src)} chars)')
print('\n'.join(report))
