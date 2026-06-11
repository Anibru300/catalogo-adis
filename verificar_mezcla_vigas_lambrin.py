import os
import hashlib

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

comparisons = [
    ('img/2-lambrin-wpc/24-media-luna/Bahia.jpg', 'img/6-vigas-pvc/61-interior/BAHIA.jpg', 'Bahia'),
    ('img/2-lambrin-wpc/24-media-luna/brasilia.jpg', 'img/6-vigas-pvc/61-interior/BRASILIA.jpg', 'Brasilia'),
    ('img/2-lambrin-wpc/24-media-luna/rio.jpg', 'img/6-vigas-pvc/61-interior/RIO.jpg', 'Rio'),
    ('img/2-lambrin-wpc/24-media-luna/Sao Paulo.jpg', 'img/6-vigas-pvc/61-interior/SAO PAULO.jpg', 'Sao Paulo'),
    ('img/2-lambrin-wpc/22-lambrin-exterior/DARK BLACK.jpg', 'img/6-vigas-pvc/62-exterior/DARK BLACK.jpg', 'Dark Black'),
]

for lambrin_path, viga_path, name in comparisons:
    if os.path.exists(lambrin_path) and os.path.exists(viga_path):
        lambrin_hash = md5(lambrin_path)
        viga_hash = md5(viga_path)
        if lambrin_hash == viga_hash:
            print(f"[IGUALES] {name}: Lambrin y Viga tienen la MISMA imagen!")
            print(f"  Lambrin: {lambrin_path}")
            print(f"  Viga:    {viga_path}")
        else:
            print(f"[DIFERENTES] {name}: Lambrin y Viga tienen imagenes distintas")
    else:
        missing = []
        if not os.path.exists(lambrin_path): missing.append(lambrin_path)
        if not os.path.exists(viga_path): missing.append(viga_path)
        print(f"[FALTA] {name}: No existe {' / '.join(missing)}")
