import os, hashlib, json
from pathlib import Path

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def scan_images(root, prefix=''):
    """Escanea recursivamente imágenes y retorna dict: rel_path -> {abs_path, md5, size}"""
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                abs_path = os.path.join(dirpath, fn)
                rel_path = os.path.relpath(abs_path, root)
                key = prefix + rel_path if prefix else rel_path
                result[key] = {
                    'abs': abs_path,
                    'md5': md5(abs_path),
                    'size': os.path.getsize(abs_path),
                    'name': fn
                }
    return result

# Directorios
CATALOGO = r"G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL"
WEB = r"G:\Mi unidad\ADIS DISEÑO\Pagina\public\img"
FOTOS = r"G:\Mi unidad\ADIS DISEÑO\FOTOS"

print("Escaneando CATALOGO FINAL...")
cat = scan_images(CATALOGO, "CATALOGO/")
print(f"  {len(cat)} imágenes encontradas")

print("Escaneando public/img...")
web = scan_images(WEB, "WEB/")
print(f"  {len(web)} imágenes encontradas")

print("Escaneando FOTOS...")
fotos = scan_images(FOTOS, "FOTOS/")
print(f"  {len(fotos)} imágenes encontradas")

# Normalizar nombres: quitar prefijo y comparar por ruta relativa sin drive
# Para comparar, normalizamos la ruta: lower, reemplazar \ por /, quitar numeración de carpetas tipo "1. ", "2.1 "
import re

def clean_path(p):
    # Quitar prefijo CATALOGO/ o WEB/
    p = re.sub(r'^(CATALOGO|WEB|FOTOS)/', '', p)
    # Normalizar separadores
    p = p.replace('\\', '/')
    # Quitar numeración tipo "1. ", "2.1 ", "6.1 " al inicio de segmentos
    parts = p.split('/')
    cleaned_parts = []
    for part in parts:
        cleaned = re.sub(r'^\d+(\.\d+)?\s+', '', part)
        cleaned_parts.append(cleaned)
    return '/'.join(cleaned_parts).lower()

cat_clean = {clean_path(k): v for k, v in cat.items()}
web_clean = {clean_path(k): v for k, v in web.items()}
fotos_clean = {clean_path(k): v for k, v in fotos.items()}

report = {
    'missing_in_web': [],
    'missing_in_catalogo': [],
    'content_mismatch': [],
    'duplicates_in_catalogo': [],
    'fotos_matches': []
}

# 1. ¿Qué hay en CATALOGO que no esté en WEB (por ruta limpia)?
for k, v in cat_clean.items():
    if k not in web_clean:
        report['missing_in_web'].append({
            'catalogo_path': v['abs'],
            'clean_name': k,
            'md5': v['md5'],
            'size': v['size']
        })

# 2. ¿Qué hay en WEB que no esté en CATALOGO?
for k, v in web_clean.items():
    if k not in cat_clean:
        report['missing_in_catalogo'].append({
            'web_path': v['abs'],
            'clean_name': k,
            'md5': v['md5'],
            'size': v['size']
        })

# 3. ¿Qué archivos comparten nombre pero tienen contenido diferente?
for k in set(cat_clean.keys()) & set(web_clean.keys()):
    c = cat_clean[k]
    w = web_clean[k]
    if c['md5'] != w['md5']:
        report['content_mismatch'].append({
            'name': k,
            'catalogo_md5': c['md5'],
            'web_md5': w['md5'],
            'catalogo_size': c['size'],
            'web_size': w['size'],
            'catalogo_path': c['abs'],
            'web_path': w['abs']
        })

# 4. Duplicados DENTRO de CATALOGO FINAL (mismo MD5, diferente ruta)
md5_to_paths_cat = {}
for k, v in cat_clean.items():
    md5_to_paths_cat.setdefault(v['md5'], []).append(k)

for md5_val, paths in md5_to_paths_cat.items():
    if len(paths) > 1:
        report['duplicates_in_catalogo'].append({
            'md5': md5_val,
            'paths': paths,
            'sizes': [cat_clean[p]['size'] for p in paths]
        })

# 5. Cruce de FOTOS con CATALOGO (por nombre de archivo, ignorando extensión)
cat_by_filename = {}
for k, v in cat_clean.items():
    filename = os.path.splitext(os.path.basename(k))[0].lower()
    cat_by_filename.setdefault(filename, []).append(k)

for k, v in fotos_clean.items():
    filename = os.path.splitext(os.path.basename(k))[0].lower()
    if filename in cat_by_filename:
        report['fotos_matches'].append({
            'foto_path': v['abs'],
            'foto_md5': v['md5'],
            'foto_size': v['size'],
            'matches': cat_by_filename[filename]
        })

# Imprimir resumen
print("\n" + "="*60)
print("REPORTE DE AUDITORÍA DE IMÁGENES")
print("="*60)
print(f"\n1. Imágenes en CATALOGO FINAL pero NO en public/img: {len(report['missing_in_web'])}")
for item in report['missing_in_web'][:20]:
    print(f"   - {item['clean_name']} ({item['size']} bytes)")
if len(report['missing_in_web']) > 20:
    print(f"   ... y {len(report['missing_in_web'])-20} más")

print(f"\n2. Imágenes en public/img pero NO en CATALOGO FINAL: {len(report['missing_in_catalogo'])}")
for item in report['missing_in_catalogo'][:20]:
    print(f"   - {item['clean_name']} ({item['size']} bytes)")
if len(report['missing_in_catalogo']) > 20:
    print(f"   ... y {len(report['missing_in_catalogo'])-20} más")

print(f"\n3. Imágenes con MISMO NOMBRE pero CONTENIDO DIFERENTE: {len(report['content_mismatch'])}")
for item in report['content_mismatch'][:20]:
    print(f"   - {item['name']}")
    print(f"     CATALOGO: {item['catalogo_size']} bytes, md5={item['catalogo_md5']}")
    print(f"     WEB:      {item['web_size']} bytes, md5={item['web_md5']}")
if len(report['content_mismatch']) > 20:
    print(f"   ... y {len(report['content_mismatch'])-20} más")

print(f"\n4. Duplicados DENTRO de CATALOGO FINAL (misma imagen, diferente ruta): {len(report['duplicates_in_catalogo'])}")
for item in report['duplicates_in_catalogo'][:20]:
    print(f"   - md5={item['md5'][:16]}... en {len(item['paths'])} rutas:")
    for p in item['paths']:
        print(f"       {p}")
if len(report['duplicates_in_catalogo']) > 20:
    print(f"   ... y {len(report['duplicates_in_catalogo'])-20} más")

print(f"\n5. Fotos reales (FOTOS/) que coinciden por nombre con CATALOGO: {len(report['fotos_matches'])}")
for item in report['fotos_matches'][:20]:
    print(f"   - Foto: {os.path.basename(item['foto_path'])}")
    print(f"     Coincide con: {', '.join(item['matches'])}")
if len(report['fotos_matches']) > 20:
    print(f"   ... y {len(report['fotos_matches'])-20} más")

# Guardar reporte completo
script_dir = Path(__file__).parent
with open(script_dir / "auditoria_imagenes_reporte.json", 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\n[OK] Reporte completo guardado en auditoria_imagenes_reporte.json")
