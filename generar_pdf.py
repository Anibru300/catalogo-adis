import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
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
DARK = HexColor('#1A1A1A')
BLACK = HexColor('#0F0F0F')
GRAY = HexColor('#2A2A2A')
LIGHT = HexColor('#F5F5F5')

IMG_EXTS = ('.jpg', '.jpeg', '.png')
PRODUCTS_PER_PAGE = 9
COLS = 3
ROWS = 3


def is_image(filename):
    return filename.lower().endswith(IMG_EXTS)


def is_ficha(filename):
    return 'ficha' in filename.lower() and is_image(filename)


def clean_name(folder_name):
    """Quita numeración inicial."""
    import re
    cleaned = re.sub(r'^\d+(\.\d+)*\.?\s*', '', folder_name)
    return cleaned.strip()


def get_products(folder_path):
    """Lista productos (imágenes que NO son fichas técnicas)."""
    if not os.path.isdir(folder_path):
        return []
    files = []
    for f in sorted(os.listdir(folder_path)):
        if is_image(f) and not is_ficha(f):
            files.append(f)
    return files


def get_ficha(folder_path):
    """Busca ficha técnica en carpeta."""
    if not os.path.isdir(folder_path):
        return None
    for f in sorted(os.listdir(folder_path)):
        if is_ficha(f):
            return f
    return None


def scan_catalog():
    """Escanea CATALOGO FINAL y devuelve estructura completa."""
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


def draw_rounded_rect(c, x, y, w, h, r, fill, stroke=0):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, r, fill=1, stroke=stroke)


# ========== INICIAR PDF ==========
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=landscape(A4))
page_w, page_h = landscape(A4)

# ========== PORTADA ==========
c.setFillColor(BLACK)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

if os.path.exists(LOGO_PATH):
    logo_w, logo_h = get_image_size(LOGO_PATH, 8*cm, 8*cm)
    c.drawImage(str(LOGO_PATH), (page_w - logo_w)/2, page_h/2 - logo_h/2 + 2*cm, width=logo_w, height=logo_h, mask='auto')

c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 32)
c.drawCentredString(page_w/2, page_h/2 - 3.5*cm, "CATÁLOGO DE PRODUCTOS")

c.setFillColor(LIGHT)
c.setFont("Helvetica", 14)
c.drawCentredString(page_w/2, page_h/2 - 4.5*cm, "ADI'S DISEÑO & REMODELACIÓN")
c.setFont("Helvetica", 11)
c.drawCentredString(page_w/2, page_h/2 - 5.2*cm, "Creando espacios, reinventando hogares")

c.setFillColor(GOLD)
c.setFont("Helvetica", 10)
c.drawCentredString(page_w/2, 2*cm, "www.adis-remodelacion.com | +52 631-192-8993")

c.showPage()

# ========== ESCANEAR CATÁLOGO ==========
print("Escaneando CATALOGO FINAL...")
categories = scan_catalog()
print(f"Encontradas {len(categories)} categorías")

# ========== ÍNDICE ==========
c.setFillColor(BLACK)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

c.bookmarkPage('indice')
c.addOutlineEntry('ÍNDICE', 'indice', level=0)

c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 28)
c.drawCentredString(page_w/2, page_h - 3*cm, "ÍNDICE DE CATEGORÍAS")

c.setStrokeColor(GOLD)
c.setLineWidth(1)
c.line(page_w/2 - 4*cm, page_h - 3.5*cm, page_w/2 + 4*cm, page_h - 3.5*cm)

# Contar productos totales por categoría
for cat in categories:
    total = len(cat['direct_products'])
    for sub in cat['subcategories']:
        total += len(sub['products'])
    cat['total_products'] = total

# Dibujar botones de categorías en índice
btn_w = 8*cm
btn_h = 1.3*cm
margin_x = 2.5*cm
margin_y = 2.5*cm
gap_x = 1*cm
gap_y = 0.8*cm
cols = 3
start_y = page_h - 5*cm

for idx, cat in enumerate(categories):
    col = idx % cols
    row = idx // cols
    x = margin_x + col * (btn_w + gap_x)
    y = start_y - row * (btn_h + gap_y)

    draw_rounded_rect(c, x, y, btn_w, btn_h, 8, GRAY)

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.roundRect(x, y, btn_w, btn_h, 8, fill=0, stroke=1)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + btn_w/2, y + btn_h/2 + 0.15*cm, cat['name'])
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 9)
    c.drawCentredString(x + btn_w/2, y + btn_h/2 - 0.35*cm, f"{cat['total_products']} productos")

    dest = f"cat_{idx}"
    c.linkAbsolute("", dest, (x, y, x+btn_w, y+btn_h))

c.showPage()

# ========== PÁGINAS DE CATEGORÍAS ==========
margin = 1.2*cm
header_h = 1.2*cm
content_h = page_h - header_h - margin * 0.5
cell_w = (page_w - 2*margin) / COLS
cell_h = content_h / ROWS

for cat_idx, cat in enumerate(categories):
    dest = f"cat_{cat_idx}"
    all_sections = []

    # Subcategorías como secciones
    for sub in cat['subcategories']:
        if sub['products']:
            all_sections.append({
                'type': 'sub',
                'name': sub['name'],
                'products': sub['products'],
                'path': sub['path']
            })

    # Productos directos
    if cat['direct_products']:
        all_sections.append({
            'type': 'direct',
            'name': cat['name'],
            'products': cat['direct_products'],
            'path': cat['path']
        })

    if not all_sections:
        continue

    first_page = True
    current_page_products = []
    current_section_name = ""
    page_count = 0

    for section in all_sections:
        section_products = section['products']
        section_name = section['name']
        section_path = section['path']

        num_pages_section = (len(section_products) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE

        for page_idx in range(num_pages_section):
            c.setFillColor(BLACK)
            c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

            if first_page:
                c.bookmarkPage(dest)
                c.addOutlineEntry(cat['name'], dest, level=0)
                first_page = False

            # Header
            c.setFillColor(GRAY)
            c.rect(0, page_h - header_h, page_w, header_h, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 14)
            header_text = f"{cat['name']}"
            if len(all_sections) > 1:
                header_text += f"  —  {section_name}"
            page_num_text = f"{page_idx + 1}/{num_pages_section}"
            c.drawString(margin, page_h - header_h + 0.4*cm, header_text)
            c.setFont("Helvetica", 10)
            c.drawRightString(page_w - margin, page_h - header_h + 0.4*cm, page_num_text)

            # Botón Volver al Índice
            btn_w_idx = 3.2*cm
            btn_h_idx = 0.7*cm
            btn_x = page_w - margin - btn_w_idx
            btn_y = page_h - header_h + 0.25*cm
            draw_rounded_rect(c, btn_x, btn_y, btn_w_idx, btn_h_idx, 5, GOLD)
            c.setFillColor(BLACK)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(btn_x + btn_w_idx/2, btn_y + 0.2*cm, "← ÍNDICE")
            c.linkAbsolute("", "indice", (btn_x, btn_y, btn_x+btn_w_idx, btn_y+btn_h_idx))

            # Productos de esta página
            start_idx = page_idx * PRODUCTS_PER_PAGE
            end_idx = min(start_idx + PRODUCTS_PER_PAGE, len(section_products))
            page_prods = section_products[start_idx:end_idx]

            for i, prod_file in enumerate(page_prods):
                col = i % COLS
                row = i // COLS
                x = margin + col * cell_w
                y = page_h - header_h - margin * 0.3 - (row + 1) * cell_h

                pad = 0.2*cm
                cw = cell_w - pad*2
                ch = cell_h - pad*2

                # Fondo celda
                draw_rounded_rect(c, x + pad, y + pad, cw, ch, 8, GRAY)

                # Imagen
                img_path = section_path / prod_file
                img_max_w = cw - 0.4*cm
                img_max_h = ch - 1.0*cm

                if os.path.exists(img_path):
                    iw, ih = get_image_size(img_path, img_max_w, img_max_h)
                    img_x = x + (cell_w - iw) / 2
                    img_y = y + pad + 0.55*cm
                    c.drawImage(str(img_path), img_x, img_y, width=iw, height=ih, mask='auto')

                # Nombre del producto abajo
                prod_name = os.path.splitext(prod_file)[0]
                c.setFillColor(GOLD)
                c.setFont("Helvetica-Bold", 9)
                c.drawCentredString(x + cell_w/2, y + pad + 0.15*cm, prod_name)

            c.showPage()
            page_count += 1

c.save()
print(f"\nPDF generado exitosamente: {OUTPUT_PDF}")
total_pages = 2 + sum(
    sum(
        (len(sub['products']) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
        for sub in cat['subcategories'] if sub['products']
    ) +
    (len(cat['direct_products']) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    for cat in categories
)
print(f"Total páginas aproximadas: {total_pages}")
print("Categorías incluidas:")
for cat in categories:
    total = cat['total_products']
    print(f"  - {cat['name']}: {total} productos")
