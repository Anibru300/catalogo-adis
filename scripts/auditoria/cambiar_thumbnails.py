import os, glob, re

base = r"G:\Mi unidad\ADIS DISEÑO\Pagina"

# Reemplazos a aplicar en TODOS los HTML
# Pisos: ACONCAGUA -> CONCRETE
# Plafon PVC: SHERWOOD -> York
replacements = [
    # Mega-menu y cat-cards en index.html
    ('img/7-pisos/71-laminado/ACONCAGUA.jpg', 'img/7-pisos/73-spc/CONCRETE.jpg'),
    ('img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg', 'img/4-plafon-pvc/York.jpg'),
]

html_files = glob.glob(os.path.join(base, "public", "*.html"))

for html in html_files:
    with open(html, 'r', encoding='utf-8') as f:
        c = f.read()
    changed = False
    for old, new in replacements:
        if old in c:
            c = c.replace(old, new)
            changed = True
    if changed:
        with open(html, 'w', encoding='utf-8') as f:
            f.write(c)
        print(f"Updated: {os.path.basename(html)}")
    else:
        print(f"No changes: {os.path.basename(html)}")

print("Done")
