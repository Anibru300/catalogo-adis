import os
import re

category_htmls = [
    ('1-placas-pvc.html', '1-placas-pvc'),
    ('2-lambrin-wpc.html', '2-lambrin-wpc'),
    ('3-revestimiento-flexible.html', '3-revestimiento-flexible'),
    ('4-plafon-pvc.html', '4-plafon-pvc'),
    ('5-paneles-tridimensionales.html', '5-paneles-tridimensionales'),
    ('6-vigas-pvc.html', '6-vigas-pvc'),
    ('7-pisos.html', '7-pisos'),
    ('8-zacate.html', '8-zacate'),
    ('9-cladding.html', '9-cladding'),
]

for html_file, img_dir in category_htmls:
    if not os.path.exists(html_file):
        continue
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as fh:
        content = fh.read()
    
    # Find all product-gallery blocks with their following product-name
    # Pattern: product-gallery with onclick containing img path, then product-name
    galleries = re.findall(
        r'<div class="product-gallery" onclick="openLightbox\(\'([^\']+)\'[^)]*\)">\s*<img src="\1"[^>]*>\s*</div>\s*<div class="product-info">\s*<div class="product-name">([^<]+)</div>',
        content
    )
    
    mismatches = []
    for img_src, product_name in galleries:
        img_filename = os.path.basename(img_src)
        img_name_no_ext = os.path.splitext(img_filename)[0]
        prod_name = product_name.strip()
        if prod_name.lower() != img_name_no_ext.lower():
            mismatches.append((prod_name, img_src))
    
    if mismatches:
        print(f"=== {html_file} - NOMBRES QUE NO COINCIDEN CON ARCHIVO ===")
        for prod_name, img_src in mismatches:
            print(f"  Producto: '{prod_name}' -> Imagen: '{img_src}'")
        print()
    else:
        print(f"=== {html_file} - TODOS LOS NOMBRES COINCIDEN ===")
        print()
