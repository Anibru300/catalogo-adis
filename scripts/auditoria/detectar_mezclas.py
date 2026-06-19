import os
import hashlib

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Collect all images by category
categories = {}
for root, dirs, files in os.walk('img'):
    for f in files:
        if f.lower().endswith(('.jpg','.jpeg','.png')):
            path = os.path.join(root, f)
            # Determine category from path
            parts = path.split(os.sep)
            if len(parts) >= 2:
                cat = parts[1]  # e.g., '1-placas-pvc'
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(path)

# Build hash database
hash_db = {}
for cat, paths in categories.items():
    for p in paths:
        h = md5(p)
        if h not in hash_db:
            hash_db[h] = []
        hash_db[h].append((cat, p))

# Find images that appear in multiple categories
print("=== IMAGENES QUE APARECEN EN MULTIPLES CATEGORIAS ===\n")
found = False
for h, items in hash_db.items():
    cats = set([item[0] for item in items])
    if len(cats) > 1:
        found = True
        print(f"IMAGEN DUPLICADA EN {len(cats)} CATEGORIAS:")
        for cat, path in items:
            print(f"  [{cat}] {path}")
        print()

if not found:
    print("No se encontraron imagenes duplicadas entre categorias.")
