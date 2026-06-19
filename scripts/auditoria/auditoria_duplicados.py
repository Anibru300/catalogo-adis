import os, hashlib
from pathlib import Path

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def scan_all(root):
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, root)
                result[rel] = {'abs': abs_path, 'md5': md5(abs_path), 'size': os.path.getsize(abs_path)}
    return result

# Escanear todo el proyecto
base = r"G:\Mi unidad\ADIS DISEÑO"
cat = scan_all(os.path.join(base, "CATALOGO FINAL"))
web = scan_all(os.path.join(base, "Pagina", "img"))
fotos = scan_all(os.path.join(base, "FOTOS"))
media = scan_all(os.path.join(base, "Pagina", "media"))
catalogo_img = scan_all(os.path.join(base, "Pagina", "catalogo_img"))

# Combinar todo
all_files = {}
for name, data in cat.items(): all_files[f"CATALOGO/{name}"] = data
for name, data in web.items(): all_files[f"WEB/{name}"] = data
for name, data in fotos.items(): all_files[f"FOTOS/{name}"] = data
for name, data in media.items(): all_files[f"MEDIA/{name}"] = data
for name, data in catalogo_img.items(): all_files[f"CATALOGO_IMG/{name}"] = data

# Buscar duplicados globales por MD5
md5_map = {}
for rel, data in all_files.items():
    md5_map.setdefault(data['md5'], []).append(rel)

duplicates = {k: v for k, v in md5_map.items() if len(v) > 1}

print(f"Total archivos escaneados: {len(all_files)}")
print(f"Grupos de duplicados globales: {len(duplicates)}")
print()

for md5_val, paths in sorted(duplicates.items(), key=lambda x: -len(x[1])):
    print(f"MD5: {md5_val} ({len(paths)} copias)")
    for p in paths:
        size = all_files[p]['size']
        print(f"  -> {p} ({size} bytes)")
    print()

# Verificar coincidencias exactas de fotos reales contra catalogo/web
print("="*60)
print("FOTOS REALES vs CATALOGO (coincidencia exacta por MD5)")
print("="*60)
for rel, data in fotos.items():
    matches = md5_map.get(data['md5'], [])
    cat_matches = [m for m in matches if m.startswith("CATALOGO/")]
    web_matches = [m for m in matches if m.startswith("WEB/")]
    if cat_matches or web_matches:
        print(f"\nFOTO: {rel}")
        for m in cat_matches + web_matches:
            print(f"  COINCIDE CON: {m}")
