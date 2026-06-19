import os, re

# Get all images from CATALOGO FINAL
catalog_images = set()
for root, dirs, files in os.walk('..' + os.sep + 'CATALOGO FINAL'):
    for f in files:
        if f.lower().endswith(('.jpg','.jpeg','.png')):
            catalog_images.add(os.path.splitext(f)[0].lower())

# Get all product names from HTML
html_products = set()
for html in [f for f in os.listdir('.') if f.endswith('.html')]:
    with open(html, 'r', encoding='utf-8', errors='ignore') as fh:
        content = fh.read()
    names = re.findall(r'<div class="product-name">([^<]+)</div>', content)
    for n in names:
        html_products.add(n.strip().lower())

# Compare
only_in_html = html_products - catalog_images
only_in_catalog = catalog_images - html_products

print('=== PRODUCTOS EN HTML QUE NO ESTAN EN CATALOGO FINAL ===')
for p in sorted(only_in_html):
    print(' ', p)

print()
print('=== PRODUCTOS EN CATALOGO FINAL QUE NO ESTAN EN HTML ===')
for p in sorted(only_in_catalog)[:50]:
    print(' ', p)
