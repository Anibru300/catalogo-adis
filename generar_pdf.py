import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from PIL import Image

# Forzar UTF-8 en stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ========== CONFIGURACIÓN ==========
BASE_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')
OUTPUT_PDF = BASE_DIR / 'catalogo_adis.pdf'
LOGO_PATH = BASE_DIR / 'LOGO ADIS.png'

# Colores ADIS
GOLD = HexColor('#C5A059')
GOLD_LIGHT = HexColor('#E8D5A3')
DARK = HexColor('#1A1A1A')
BLACK = HexColor('#0F0F0F')
GRAY = HexColor('#2A2A2A')
LIGHT = HexColor('#F5F5F5')

IMG_EXTS = ('.jpg', '.jpeg', '.png')
PRODUCTS_PER_PAGE = 6
COLS = 2
ROWS = 3


def is_image(filename):
    return filename.lower().endswith(IMG_EXTS)


def is_ficha(filename):
    return 'ficha' in filename.lower() and is_image(filename)


def clean_name(folder_name):
    import re
    cleaned = re.sub(r'^\d+(\.\d+)*\.?\s*', '', folder_name)
    return cleaned.strip()


def get_products(folder_path):
    if not os.path.isdir(folder_path):
        return []
    files = []
    for f in sorted(os.listdir(folder_path)):
        if is_image(f) and not is_ficha(f):
            files.append(f)
    return files


def get_ficha(folder_path):
    if not os.path.isdir(folder_path):
        return None
    for f in sorted(os.listdir(folder_path)):
        if is_ficha(f):
            return f
    return None


def scan_catalog():
    categories = []
    for cat_folder in sorted(os.listdir(CATALOG_DIR)):
        cat_path = CATALOG_DIR / cat_folder
        if not cat_path.is_dir():
            continue

        cat_name = clean_name(cat_folder)
        subcategories = []
        direct_products = []

        for item in sorted(os.listdir(cat_path)):
            item_path = cat_path / item
            if item_path.is_dir():
                sub_name = clean_name(item)
                products = get_products(item_path)
                ficha = get_ficha(item_path)
                subcategories.append({
                    'folder': item,
                    'name': sub_name,
                    'products': products,
                    'ficha': ficha,
                    'path': item_path
                })
            elif is_image(item) and not is_ficha(item):
                direct_products.append(item)

        categories.append({
            'folder': cat_folder,
            'name': cat_name,
            'subcategories': subcategories,
            'direct_products': sorted(direct_products),
            'ficha': get_ficha(cat_path),
            'path': cat_path
        })
    return categories


def get_image_size(img_path, max_w, max_h):
    try:
        with Image.open(img_path) as img:
            iw, ih = img.size
            ratio = min(max_w / iw, max_h / ih)
            return iw * ratio, ih * ratio
    except:
        return max_w, max_h


# ========== DATOS TÉCNICOS ==========
SPECS_DATA = {
    'Placas PVC tipo madera': {
        'Material': 'PVC', 'Dimensiones': '2440 x 1220 x 3 mm',
        'Presentación': '2.977 m²/pz, 1 pz/Caja, 19 kg/pz', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Placas PVC Texturizadas': {
        'Material': 'PVC', 'Dimensiones': '2440 x 1220 x 5 mm',
        'Presentación': '2.977 m²/pz, 1 pz/Caja, 10.5 kg/pz', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Placas PVC Tipo espejo': {
        'Material': 'PVC', 'Dimensiones': '2440 x 1220 x 5 mm',
        'Presentación': '2.977 m²/pz, 1 pz/Caja, 10.5 kg/pz', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Lambrin Interior': {
        'Material': 'WPC', 'Dimensiones': '2900 x 160 x 24 mm',
        'Presentación': '0.464 m²/pz, 14 pz/Caja, 6.496 m²/caja', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Lambrin Exterior': {
        'Material': 'WPC', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': 'Consultar ficha técnica', 'Uso': 'Exterior'},
    'Desigual': {
        'Material': 'WPC', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': 'Consultar ficha técnica', 'Uso': 'Interior'},
    'Media luna': {
        'Material': 'WPC', 'Dimensiones': '2900 x 159 x 15 mm',
        'Presentación': '4.611 m²/caja, 10 pzas/Caja', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Media luna PS': {
        'Material': 'PS (Poliestireno)', 'Dimensiones': '2900 x 152 x 12 mm',
        'Presentación': '6.171 m²/caja, 14 pzas/Caja', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Revestimiento Flexible': {
        'Material': 'Revestimiento flexible', 'Dimensiones': '900 x 600 mm / 1200 x 600 mm',
        'Presentación': '0.54/0.72 m²/pz, 13.5/0.72 m²/Caja', 'Garantía': '35 años', 'Uso': 'Interior/Exterior'},
    'Plafon pvc laminado': {
        'Material': 'PVC', 'Dimensiones': '2900 x 250 x 8 mm',
        'Presentación': '0.725 m²/pz, 10 pz/Caja, 7.25 m²/Caja', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Plafon Laminado wood': {
        'Material': 'PVC', 'Dimensiones': '2800 x 300 x 9 mm',
        'Presentación': '0.84 m²/pz, 10 pz/Caja, 8.4 m²/Caja', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Plafon ranurado': {
        'Material': 'PVC', 'Dimensiones': '2900 x 250 x 8 mm',
        'Presentación': 'Por pieza, 2.90 m largo x 0.25 m ancho', 'Garantía': '15 años', 'Uso': 'Interior', 'Acabado': 'Ranurado decorativo'},
    'Blanco': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja', 'Garantía': '1 año', 'Uso': 'Residencial y comercial'},
    'Grises': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja', 'Garantía': '1 año', 'Uso': 'Residencial y comercial'},
    'Madera': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja', 'Garantía': '1 año', 'Uso': 'Residencial y comercial'},
    'Negro': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja', 'Garantía': '1 año', 'Uso': 'Residencial y comercial'},
    'Oro': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja', 'Garantía': '1 año', 'Uso': 'Residencial y comercial'},
    'Interior': {
        'Material': 'WPC', 'Dimensiones': '2900 x 100 x 50 mm / 2900 x 50 x 50 mm',
        'Presentación': '1 pz/Caja', 'Garantía': '15 años', 'Uso': 'Interior'},
    'Exterior': {
        'Material': 'WPC', 'Dimensiones': '2850 x 120 x 70 mm',
        'Presentación': '1 pz/Caja', 'Garantía': '15 años sin carga', 'Uso': 'Exterior'},
    'Laminado': {
        'Material': 'Laminado', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': 'Consultar ficha técnica', 'Uso': 'Residencial'},
    'WPC': {
        'Material': 'WPC', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': 'Consultar ficha técnica', 'Uso': 'Residencial'},
    'SPC': {
        'Material': 'SPC', 'Dimensiones': '625 x 125 mm, Espesor 5+IXPE 1.5 mm',
        'Presentación': 'Consultar ficha técnica', 'Garantía': 'Consultar ficha técnica', 'Uso': 'Residencial'},
    'Deck Sintetico': {
        'Material': 'WPC Coextruido', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': '18-25 años', 'Uso': 'Exterior'},
    'Follaje Sintetico': {
        'Material': 'Polietileno / PVC', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': '5-8 años', 'Uso': 'Interior/Exterior'},
    'Pasto Recreativo': {
        'Material': 'Polietileno', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': '8-12 años', 'Uso': 'Exterior'},
    'Placa tipo roca': {
        'Material': 'PU / Poliuretano', 'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica', 'Garantía': 'Consultar ficha técnica', 'Uso': 'Interior/Exterior'},
}


def get_specs_text(sub_name):
    return SPECS_DATA.get(sub_name, {})


# ========== INICIAR PDF (A4 VERTICAL) ==========
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)
page_w, page_h = A4
margin = 1.5*cm
page_num = 0


def next_page():
    global page_num
    c.showPage()
    page_num += 1


def draw_page_bg():
    """Fondo negro con sutil degradado dorado en esquina."""
    c.setFillColor(BLACK)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    for i in range(30):
        alpha = 0.012 - (i * 0.00035)
        if alpha > 0:
            c.setFillColor(Color(197/255, 160/255, 89/255, alpha=alpha))
            c.circle(page_w, page_h, 12*cm - i*0.35*cm, fill=1, stroke=0)


def draw_header(title_text):
    h = 1.3*cm
    c.setFillColor(DARK)
    c.rect(0, page_h - h, page_w, h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(margin, page_h - h, page_w - margin, page_h - h)
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(page_w/2, page_h - h + 0.35*cm, title_text)
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 7)
    c.drawRightString(page_w - margin, page_h - h + 0.35*cm, "ADIS DISEÑO & REMODELACIÓN")
    return h


def draw_footer(page_n, total_n):
    h = 0.7*cm
    c.setFillColor(DARK)
    c.rect(0, 0, page_w, h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(margin, h, page_w - margin, h)
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 7)
    c.drawString(margin, 0.25*cm, "+52 631-192-8993  |  +52 631-120-4943  |  adis.remodelacion@gmail.com")
    c.drawRightString(page_w - margin, 0.25*cm, f"Página {page_n} de {total_n}")


# ========== PORTADA ==========
draw_page_bg()

# Marco decorativo
fm = 2*cm
c.setStrokeColor(GOLD)
c.setLineWidth(2)
c.roundRect(fm, fm, page_w - 2*fm, page_h - 2*fm, 16, fill=0, stroke=1)
c.setLineWidth(0.5)
c.roundRect(fm + 0.4*cm, fm + 0.4*cm, page_w - 2*fm - 0.8*cm, page_h - 2*fm - 0.8*cm, 14, fill=0, stroke=1)

# Logo
if os.path.exists(LOGO_PATH):
    logo_max = 7*cm
    iw, ih = get_image_size(LOGO_PATH, logo_max, logo_max)
    logo_x = (page_w - iw) / 2
    logo_y = page_h / 2 - ih/2 + 2*cm
    c.drawImage(str(LOGO_PATH), logo_x, logo_y, width=iw, height=ih, mask='auto')

# Títulos
c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 32)
c.drawCentredString(page_w/2, page_h/2 - 2.5*cm, "CATÁLOGO DE PRODUCTOS")

c.setFillColor(GOLD_LIGHT)
c.setFont("Helvetica", 14)
c.drawCentredString(page_w/2, page_h/2 - 3.5*cm, "ADI'S DISEÑO & REMODELACIÓN")

c.setFillColor(LIGHT)
c.setFont("Helvetica", 11)
c.drawCentredString(page_w/2, page_h/2 - 4.2*cm, "Creando espacios, reinventando hogares")

# Info contacto
c.setFillColor(GOLD)
c.setFont("Helvetica", 9)
c.drawCentredString(page_w/2, 3.5*cm, "WhatsApp: +52 631-192-8993")
c.drawCentredString(page_w/2, 3.0*cm, "Showroom: +52 631-120-4943")
c.drawCentredString(page_w/2, 2.5*cm, "adis.remodelacion@gmail.com")
c.drawCentredString(page_w/2, 2.0*cm, "Nogales, Sonora  ·  Rio Rico, AZ")

next_page()

# ========== ESCANEAR CATÁLOGO ==========
print("Escaneando CATALOGO FINAL...")
categories = scan_catalog()
print(f"Encontradas {len(categories)} categorías")

for cat in categories:
    total = len(cat['direct_products'])
    for sub in cat['subcategories']:
        total += len(sub['products'])
    cat['total_products'] = total

# Calcular total de páginas
total_pages = 2  # portada + índice
for cat in categories:
    for sub in cat['subcategories']:
        if sub['products']:
            total_pages += 1  # página intro
            total_pages += (len(sub['products']) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    if cat['direct_products']:
        total_pages += 1
        total_pages += (len(cat['direct_products']) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE

# ========== ÍNDICE ==========
draw_page_bg()
page_num = 2

c.bookmarkPage('indice')
c.addOutlineEntry('ÍNDICE', 'indice', level=0)

c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 26)
c.drawCentredString(page_w/2, page_h - 2.8*cm, "ÍNDICE DE CATEGORÍAS")
c.setStrokeColor(GOLD)
c.setLineWidth(1.5)
c.line(page_w/2 - 4*cm, page_h - 3.3*cm, page_w/2 + 4*cm, page_h - 3.3*cm)

# Tarjetas de categoría
card_w = 7.8*cm
card_h = 2.6*cm
gap_x = 0.8*cm
gap_y = 0.7*cm
cols_idx = 2
start_y = page_h - 4.2*cm

for idx, cat in enumerate(categories):
    col = idx % cols_idx
    row = idx // cols_idx
    x = margin + col * (card_w + gap_x)
    y = start_y - row * (card_h + gap_y)
    
    c.setFillColor(DARK)
    c.roundRect(x, y, card_w, card_h, 10, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.roundRect(x, y, card_w, card_h, 10, fill=0, stroke=1)
    
    # Imagen mini
    img_drawn = False
    if cat['subcategories']:
        for sub in cat['subcategories']:
            if sub['products']:
                img_path = sub['path'] / sub['products'][0]
                if os.path.exists(img_path):
                    iw, ih = get_image_size(img_path, 1.8*cm, 1.8*cm)
                    c.drawImage(str(img_path), x + 0.3*cm, y + card_h - 2.2*cm, width=iw, height=ih, mask='auto')
                    img_drawn = True
                    break
    if not img_drawn and cat['direct_products']:
        img_path = cat['path'] / cat['direct_products'][0]
        if os.path.exists(img_path):
            iw, ih = get_image_size(img_path, 1.8*cm, 1.8*cm)
            c.drawImage(str(img_path), x + 0.3*cm, y + card_h - 2.2*cm, width=iw, height=ih, mask='auto')
            img_drawn = True
    
    tx = x + 2.3*cm if img_drawn else x + 0.4*cm
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(tx, y + card_h - 0.8*cm, cat['name'])
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 9)
    c.drawString(tx, y + card_h - 1.35*cm, f"{cat['total_products']} productos")
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 7.5)
    subs = ", ".join([s['name'] for s in cat['subcategories'][:2]])
    if len(cat['subcategories']) > 2:
        subs += "..."
    if subs:
        c.drawString(tx, y + card_h - 1.85*cm, subs[:40])
    
    dest = f"cat_{idx}"
    c.linkAbsolute("", dest, (x, y, x+card_w, y+card_h))

draw_footer(page_num, total_pages)
next_page()

# ========== PÁGINAS DE CATEGORÍAS ==========
content_top = page_h - 1.6*cm
content_bottom = 1.0*cm
content_h = content_top - content_bottom

cell_w = (page_w - 2*margin) / COLS
cell_h = content_h / ROWS

for cat_idx, cat in enumerate(categories):
    dest = f"cat_{cat_idx}"
    all_sections = []
    
    for sub in cat['subcategories']:
        if sub['products']:
            all_sections.append({
                'type': 'sub', 'name': sub['name'],
                'products': sub['products'], 'path': sub['path']
            })
    
    if cat['direct_products']:
        all_sections.append({
            'type': 'direct', 'name': cat['name'],
            'products': cat['direct_products'], 'path': cat['path']
        })
    
    if not all_sections:
        continue
    
    for section in all_sections:
        section_products = section['products']
        section_name = section['name']
        section_path = section['path']
        
        # ========== PÁGINA INTRO ==========
        draw_page_bg()
        draw_header(f"{cat['name']}  —  {section_name}")
        
        c.bookmarkPage(dest)
        c.addOutlineEntry(cat['name'], dest, level=0)
        
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(page_w/2, page_h - 3.2*cm, section_name.upper())
        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.line(page_w/2 - 3*cm, page_h - 3.6*cm, page_w/2 + 3*cm, page_h - 3.6*cm)
        
        # Tabla de especificaciones
        specs = get_specs_text(section_name)
        if specs:
            table_y = page_h - 4.3*cm
            row_h = 0.65*cm
            table_w = 11*cm
            table_x = (page_w - table_w) / 2
            
            c.setFillColor(GOLD_LIGHT)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(page_w/2, table_y + 0.4*cm, "ESPECIFICACIONES TÉCNICAS")
            
            for i, (label, value) in enumerate(specs.items()):
                y = table_y - 0.6*cm - i * row_h
                bg = GRAY if i % 2 == 0 else DARK
                c.setFillColor(bg)
                c.rect(table_x, y, table_w, row_h, fill=1, stroke=0)
                c.setStrokeColor(GOLD)
                c.setLineWidth(0.3)
                c.rect(table_x, y, table_w, row_h, fill=0, stroke=1)
                c.setFillColor(GOLD)
                c.setFont("Helvetica-Bold", 8.5)
                c.drawString(table_x + 0.3*cm, y + 0.22*cm, label)
                c.setFillColor(LIGHT)
                c.setFont("Helvetica", 8.5)
                # Truncar valor si es muy largo
                val = value[:55]
                c.drawString(table_x + 3.8*cm, y + 0.22*cm, val)
        else:
            c.setFillColor(LIGHT)
            c.setFont("Helvetica", 10)
            c.drawCentredString(page_w/2, page_h - 5*cm, "Consulte ficha técnica para especificaciones detalladas.")
        
        # Imagen representativa
        if section_products:
            img_path = section_path / section_products[0]
            if os.path.exists(img_path):
                img_max_w = 6*cm
                img_max_h = 5*cm
                iw, ih = get_image_size(img_path, img_max_w, img_max_h)
                img_x = (page_w - iw) / 2
                img_y = margin + 1.5*cm
                c.setStrokeColor(GOLD)
                c.setLineWidth(1.5)
                c.roundRect(img_x - 0.2*cm, img_y - 0.2*cm, iw + 0.4*cm, ih + 0.4*cm, 8, fill=0, stroke=1)
                c.drawImage(str(img_path), img_x, img_y, width=iw, height=ih, mask='auto')
        
        # Botón índice
        btn_w = 3.2*cm
        btn_h = 0.7*cm
        btn_x = margin
        btn_y = margin * 0.4
        c.setFillColor(GOLD)
        c.roundRect(btn_x, btn_y, btn_w, btn_h, 5, fill=1, stroke=0)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(btn_x + btn_w/2, btn_y + 0.22*cm, "← ÍNDICE")
        c.linkAbsolute("", "indice", (btn_x, btn_y, btn_x+btn_w, btn_y+btn_h))
        
        draw_footer(page_num, total_pages)
        next_page()
        
        # ========== PÁGINAS DE PRODUCTOS ==========
        num_pages_section = (len(section_products) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
        
        for page_idx in range(num_pages_section):
            draw_page_bg()
            draw_header(f"{cat['name']}  —  {section_name}")
            
            start_idx = page_idx * PRODUCTS_PER_PAGE
            end_idx = min(start_idx + PRODUCTS_PER_PAGE, len(section_products))
            page_prods = section_products[start_idx:end_idx]
            
            for i, prod_file in enumerate(page_prods):
                col = i % COLS
                row = i // COLS
                x = margin + col * cell_w
                y = content_top - (row + 1) * cell_h
                
                pad = 0.2*cm
                cw = cell_w - pad*2
                ch = cell_h - pad*2
                
                # Fondo celda
                c.setFillColor(DARK)
                c.roundRect(x + pad, y + pad, cw, ch, 8, fill=1, stroke=0)
                c.setStrokeColor(Color(197/255, 160/255, 89/255, alpha=0.35))
                c.setLineWidth(1)
                c.roundRect(x + pad, y + pad, cw, ch, 8, fill=0, stroke=1)
                
                # Imagen
                img_path = section_path / prod_file
                img_max_w = cw - 0.5*cm
                img_max_h = ch - 1.1*cm
                
                if os.path.exists(img_path):
                    iw, ih = get_image_size(img_path, img_max_w, img_max_h)
                    img_x = x + (cell_w - iw) / 2
                    img_y = y + pad + 0.55*cm
                    c.drawImage(str(img_path), img_x, img_y, width=iw, height=ih, mask='auto')
                
                # Nombre producto
                prod_name = os.path.splitext(prod_file)[0]
                c.setFillColor(GOLD_LIGHT)
                c.setFont("Helvetica-Bold", 9)
                c.drawCentredString(x + cell_w/2, y + pad + 0.18*cm, prod_name)
            
            # Botón índice
            btn_w = 3.2*cm
            btn_h = 0.7*cm
            btn_x = margin
            btn_y = 0.3*cm
            c.setFillColor(GOLD)
            c.roundRect(btn_x, btn_y, btn_w, btn_h, 5, fill=1, stroke=0)
            c.setFillColor(BLACK)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(btn_x + btn_w/2, btn_y + 0.22*cm, "← ÍNDICE")
            c.linkAbsolute("", "indice", (btn_x, btn_y, btn_x+btn_w, btn_y+btn_h))
            
            draw_footer(page_num, total_pages)
            next_page()

c.save()
print(f"\n✅ PDF generado exitosamente: {OUTPUT_PDF}")
print(f"Total páginas: {page_num}")
print("Categorías incluidas:")
for cat in categories:
    total = cat['total_products']
    print(f"  - {cat['name']}: {total} productos")
