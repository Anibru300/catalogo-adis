import os
import hashlib

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Check all images in img/1-placas-pvc/
img_dir = 'img/1-placas-pvc'
hashes = {}

for root, dirs, files in os.walk(img_dir):
    for f in files:
        if f.lower().endswith(('.jpg','.jpeg','.png')):
            path = os.path.join(root, f)
            h = md5(path)
            if h in hashes:
                print(f"DUPLICADO: '{f}' y '{hashes[h]}'")
            else:
                hashes[h] = path

# Also check across all categories for the specific products mentioned
print("\n=== Verificando productos mencionados ===")

checks = [
    ('img/1-placas-pvc/11-placas-pvc-tipo-madera/Solaria.jpg', 'Solaria'),
    ('img/1-placas-pvc/12-placas-pvc-texturizadas/CEDAR.png', 'CEDAR'),
    ('img/1-placas-pvc/12-placas-pvc-texturizadas/ENCINO.png', 'ENCINO'),
    ('img/1-placas-pvc/13-placas-pvc-tipo-espejo/PLACA TIPO METAL.jpg', 'PLACA TIPO METAL'),
    ('img/1-placas-pvc/angulo 8x8x2440mm.jpg', 'angulo 8x8x2440mm'),
]

for path, name in checks:
    if os.path.exists(path):
        # Compare with other images to find similar/duplicate
        target_hash = md5(path)
        for root, dirs, files in os.walk(img_dir):
            for f in files:
                if f.lower().endswith(('.jpg','.jpeg','.png')):
                    other_path = os.path.join(root, f)
                    if other_path != path:
                        other_hash = md5(other_path)
                        if target_hash == other_hash:
                            print(f"  {name} es IDENTICO a: {other_path}")
