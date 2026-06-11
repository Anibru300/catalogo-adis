import os

def collect_files(base_dir):
    files = {}
    for root, dirs, filenames in os.walk(base_dir):
        for f in filenames:
            if f.lower().endswith(('.jpg','.jpeg','.png')):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, base_dir)
                files[f.lower()] = rel
    return files

# Collect from CATALOGO FINAL and Pagina/img
catalog = collect_files('..' + os.sep + 'CATALOGO FINAL')
web = collect_files('img')

print("=== ARCHIVOS EN CATALOGO FINAL QUE NO ESTAN EN Pagina/img ===")
missing_in_web = []
for name, path in catalog.items():
    if name not in web:
        missing_in_web.append((name, path))

for name, path in sorted(missing_in_web):
    print(f"  FALTA EN WEB: {path}")

print(f"\nTotal faltantes en web: {len(missing_in_web)}")

print("\n=== ARCHIVOS EN Pagina/img QUE NO ESTAN EN CATALOGO FINAL ===")
extra_in_web = []
for name, path in web.items():
    if name not in catalog:
        extra_in_web.append((name, path))

for name, path in sorted(extra_in_web):
    print(f"  EXTRA EN WEB: {path}")

print(f"\nTotal extras en web: {len(extra_in_web)}")

print("\n=== ARCHIVOS QUE ESTAN EN AMBOS PERO EN CARPETA DIFERENTE ===")
moved = []
for name in catalog:
    if name in web and catalog[name].replace('\\','/') != web[name].replace('\\','/'):
        moved.append((name, catalog[name], web[name]))

for name, cat_path, web_path in sorted(moved):
    print(f"  {name}:")
    print(f"    CATALOGO: {cat_path}")
    print(f"    WEB:      {web_path}")
