import os
import hashlib

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Compare images between CATALOGO FINAL and public/img/
comparisons = [
    ('../CATALOGO FINAL/1. Placas PVC/AGATA.jpg', 'public/img/1-placas-pvc/AGATA.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/ARENA.jpg', 'public/img/1-placas-pvc/ARENA.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Aurora Dorada.jpg', 'public/img/1-placas-pvc/Aurora Dorada.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Carrara Oscuro.jpg', 'public/img/1-placas-pvc/Carrara Oscuro.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Cuarzo.jpg', 'public/img/1-placas-pvc/Cuarzo.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Grafito.jpg', 'public/img/1-placas-pvc/Grafito.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Jaspe.jpg', 'public/img/1-placas-pvc/Jaspe.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/OBSIDIANA.jpg', 'public/img/1-placas-pvc/OBSIDIANA.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Onix.jpg', 'public/img/1-placas-pvc/Onix.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Opalo.jpg', 'public/img/1-placas-pvc/Opalo.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Perla.jpg', 'public/img/1-placas-pvc/Perla.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/Topacio.jpg', 'public/img/1-placas-pvc/Topacio.jpg'),
    ('../CATALOGO FINAL/1. Placas PVC/ZAFIRO.jpg', 'public/img/1-placas-pvc/ZAFIRO.jpg'),
    ('../CATALOGO FINAL/7. Pisos/7.1 Laminado/ACONCAGUA.jpg', 'public/img/7-pisos/71-laminado/ACONCAGUA.jpg'),
    ('../CATALOGO FINAL/4. Plafon PVC/4.1 Plafon pvc laminado/SHERWOOD.jpg', 'public/img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg'),
]

for cat_path, web_path in comparisons:
    if os.path.exists(cat_path) and os.path.exists(web_path):
        cat_hash = md5(cat_path)
        web_hash = md5(web_path)
        status = "IGUALES" if cat_hash == web_hash else "DIFERENTES"
        print(f"{status}: {os.path.basename(cat_path)}")
    elif os.path.exists(cat_path):
        print(f"FALTA EN WEB: {os.path.basename(cat_path)}")
    elif os.path.exists(web_path):
        print(f"FALTA EN CATALOGO: {os.path.basename(web_path)}")
    else:
        print(f"NO EXISTEN: {os.path.basename(cat_path)}")
