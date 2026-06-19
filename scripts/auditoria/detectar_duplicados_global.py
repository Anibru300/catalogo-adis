import os
import hashlib

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

hashes = {}
print("=== DUPLICADOS GLOBALES EN TODO EL CATÁLOGO ===")
for root, dirs, files in os.walk('img'):
    for f in files:
        if f.lower().endswith(('.jpg','.jpeg','.png')):
            path = os.path.join(root, f)
            h = md5(path)
            if h in hashes:
                print(f"DUPLICADO:")
                print(f"  A: {hashes[h]}")
                print(f"  B: {path}")
                print()
            else:
                hashes[h] = path
