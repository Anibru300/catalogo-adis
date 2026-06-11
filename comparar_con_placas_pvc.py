import os
import hashlib

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Images used in index.html for categories
category_images = {
    'Pisos': 'img/7-pisos/71-laminado/ACONCAGUA.jpg',
    'Plafon PVC': 'img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg',
    'Revestimiento': 'img/3-revestimiento-flexible/CONCRETO Aparente.jpg',
    'Paneles 3D': 'img/5-paneles-tridimensionales/51-blanco/Austin.jpg',
    'Vigas PVC': 'img/6-vigas-pvc/61-interior/BAHIA 1.jpg',
    'Zacate': 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg',
    'Cladding': 'img/9-cladding/91-placa-tipo-roca/BLACK.jpg',
    'Placas PVC': 'img/1-placas-pvc/11-placas-pvc-tipo-madera/Adler.jpg',
    'Lambrin WPC': 'img/2-lambrin-wpc/21-lambrin-interior/AMANECHER.jpg',
}

# Collect all placas PVC images
placas_pvc_images = []
for root, dirs, files in os.walk('img/1-placas-pvc'):
    for f in files:
        if f.lower().endswith(('.jpg','.jpeg','.png')):
            placas_pvc_images.append(os.path.join(root, f))

print("=== Comparando imagenes de categorias con Placas PVC ===\n")

for cat_name, cat_path in category_images.items():
    if not os.path.exists(cat_path):
        print(f"{cat_name}: NO EXISTE {cat_path}")
        continue
    cat_hash = md5(cat_path)
    matches = []
    for pvc_path in placas_pvc_images:
        if md5(pvc_path) == cat_hash:
            matches.append(pvc_path)
    if matches:
        print(f"[X] {cat_name}: ES IDENTICA a Placa PVC!")
        print(f"   Categoria: {cat_path}")
        for m in matches:
            print(f"   Placa PVC: {m}")
        print()
    else:
        print(f"[OK] {cat_name}: Es diferente de Placas PVC")
