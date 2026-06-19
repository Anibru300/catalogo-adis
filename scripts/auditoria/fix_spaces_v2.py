import os, glob

base = r"G:\Mi unidad\ADIS DISEÑO\Pagina"

replacements = [
    ('CONCRETO%20Aparente.jpg', 'CONCRETO Aparente.jpg'),
    ('BAHIA%201.jpg', 'BAHIA 1.jpg'),
    ('Carrara%20Oscuro.jpg', 'Carrara Oscuro.jpg'),
]

for html in glob.glob(os.path.join(base, "*.html")):
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
        print(f"Fixed: {os.path.basename(html)}")
    else:
        print(f"OK: {os.path.basename(html)}")

print("Done")
