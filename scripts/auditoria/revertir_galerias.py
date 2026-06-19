import re

base = r"G:\Mi unidad\ADIS DISEÑO\Pagina"

# Fix 7-pisos.html: ACONCAGUA product was showing CONCRETE.jpg
p7 = base + r"\public\7-pisos.html"
with open(p7, 'r', encoding='utf-8') as f:
    c = f.read()

# Revert only where alt/lightbox label is ACONCAGUA
c = c.replace(
    "onclick=\"openLightbox('img/7-pisos/73-spc/CONCRETE.jpg', 'ACONCAGUA')\"",
    "onclick=\"openLightbox('img/7-pisos/71-laminado/ACONCAGUA.jpg', 'ACONCAGUA')\""
)
c = c.replace(
    '<img src="img/7-pisos/73-spc/CONCRETE.jpg" alt="ACONCAGUA" loading="lazy">',
    '<img src="img/7-pisos/71-laminado/ACONCAGUA.jpg" alt="ACONCAGUA" loading="lazy">'
)
with open(p7, 'w', encoding='utf-8') as f:
    f.write(c)
print("Fixed 7-pisos.html")

# Fix 4-plafon-pvc.html: SHERWOOD product was showing York.jpg
p4 = base + r"\public\4-plafon-pvc.html"
with open(p4, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "onclick=\"openLightbox('img/4-plafon-pvc/York.jpg', 'SHERWOOD')\"",
    "onclick=\"openLightbox('img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg', 'SHERWOOD')\""
)
c = c.replace(
    '<img src="img/4-plafon-pvc/York.jpg" alt="SHERWOOD" loading="lazy">',
    '<img src="img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg" alt="SHERWOOD" loading="lazy">'
)
with open(p4, 'w', encoding='utf-8') as f:
    f.write(c)
print("Fixed 4-plafon-pvc.html")
print("Done")
