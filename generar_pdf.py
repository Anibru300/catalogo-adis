import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

base_dir = r'G:\Mi unidad\ADIS DISEÑO\Catalogo'
output_pdf = os.path.join(base_dir, 'catalogo_adis.pdf')
logo_path = os.path.join(base_dir, 'LOGO ADIS.png')

# Colores ADIS
GOLD = HexColor('#C5A059')
DARK = HexColor('#1A1A1A')
BLACK = HexColor('#0F0F0F')
GRAY = HexColor('#2A2A2A')
LIGHT = HexColor('#F5F5F5')

CATEGORY_CONFIG = {
    'MURO MARMOL DIGITAL': {
        'title': 'Muro Mármol Digital',
        'specs': ['Panel de alto brillo', 'Mármol digital UV', 'Humedad / Rayos UV', 'Interiores', 'Garantía: 15 años']
    },
    'FACHADA Y MURO INTERIOR FLEXIBLE': {
        'title': 'Fachada y Muro Interior Flexible',
        'specs': ['Lámina flexible', 'Textura natural', 'Flexible / Adherible', 'Interiores y fachadas', 'Consultar']
    },
    'LAMBIRN WPC INTERIOR': {
        'title': 'Lambrín WPC Interior',
        'specs': ['WPC Interior', '2900 x 160 x 24 mm', '0.464 m²/pz', '14 pz/caja', 'Garantía: 15 años']
    },
    'LAMBRIN WPC EXTERIOR': {
        'title': 'Lambrín WPC Exterior',
        'specs': ['WPC Exterior', '2850 x 200 x 26 mm', '0.57 m²/pz', '4 pz/caja', '10 ext. / 15 int.']
    },
    'PANELES PVC INTERIORES': {
        'title': 'Paneles PVC Interiores',
        'specs': ['Panel PVC Interior', '2800 x 300 x 9 mm', '0.84 m²/pz', '10 pz/caja', 'Garantía: 15 años']
    },
    'PANELES DECORATIVOS 3D': {
        'title': 'Paneles Decorativos 3D',
        'specs': ['Panel Decorativo 3D', '500 x 500 x 40/10 mm', '0.25 m²/pz', '10 pz/caja', 'Garantía: 1 año']
    },
    'PANELES METALICOS AUTO ADERIBLES': {
        'title': 'Paneles Metálicos Autoadheribles',
        'specs': ['Metálico autoadherible', 'Espesor: 3 mm', '5 pz / caja', 'Garantía: 3 años', 'Autoadherible']
    },
    'Paneles XPC 3D autoadheribles': {
        'title': 'Paneles XPC 3D Autoadheribles',
        'specs': ['XPC 3D autoadherible', '300 x 300 x 4 mm', '0.09 m²/pz', '10 pz/caja', 'Garantía: 1 año']
    },
    'Muros Reflexions': {
        'title': 'Muros Reflexions',
        'specs': ['Placa reflectiva', '2440 x 1220 x 5 mm', '2.977 m²/pz', '1 pz/caja', 'Garantía: 15 años']
    }
}

CATEGORY_ORDER = [
    'MURO MARMOL DIGITAL',
    'FACHADA Y MURO INTERIOR FLEXIBLE',
    'LAMBIRN WPC INTERIOR',
    'LAMBRIN WPC EXTERIOR',
    'PANELES PVC INTERIORES',
    'PANELES DECORATIVOS 3D',
    'PANELES METALICOS AUTO ADERIBLES',
    'Paneles XPC 3D autoadheribles',
    'Muros Reflexions'
]

def safe_id(name):
    return name.lower().replace(' ', '-').replace('_', '-').replace('ñ','n').replace('ó','o')[:30]

def draw_rounded_rect(c, x, y, w, h, r, fill, stroke=0):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, r, fill=1, stroke=stroke)

def get_image_size(img_path, max_w, max_h):
    try:
        with Image.open(img_path) as img:
            iw, ih = img.size
            ratio = min(max_w / iw, max_h / ih)
            return iw * ratio, ih * ratio
    except:
        return max_w, max_h

c = canvas.Canvas(output_pdf, pagesize=landscape(A4))
page_w, page_h = landscape(A4)

# ========== PORTADA ==========
c.setFillColor(BLACK)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

# Logo en portada
if os.path.exists(logo_path):
    logo_w, logo_h = get_image_size(logo_path, 8*cm, 8*cm)
    c.drawImage(logo_path, (page_w - logo_w)/2, page_h/2 - logo_h/2 + 2*cm, width=logo_w, height=logo_h, mask='auto')

# Texto portada
c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 32)
title = "CATÁLOGO DE PRODUCTOS"
c.drawCentredString(page_w/2, page_h/2 - 3.5*cm, title)

c.setFillColor(LIGHT)
c.setFont("Helvetica", 14)
c.drawCentredString(page_w/2, page_h/2 - 4.5*cm, "ADI'S DISEÑO & REMODELACIÓN")
c.setFont("Helvetica", 11)
c.drawCentredString(page_w/2, page_h/2 - 5.2*cm, "Creando espacios, reinventando hogares")

c.setFillColor(GOLD)
c.setFont("Helvetica", 10)
c.drawCentredString(page_w/2, 2*cm, "www.adis-remodelacion.com | +52 631-192-8993")

c.showPage()

# ========== ÍNDICE ==========
c.setFillColor(BLACK)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

# Destino para índice
c.bookmarkPage('indice')
c.addOutlineEntry('ÍNDICE', 'indice', level=0)

# Título índice
c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 28)
c.drawCentredString(page_w/2, page_h - 3*cm, "ÍNDICE DE CATEGORÍAS")

c.setStrokeColor(GOLD)
c.setLineWidth(1)
c.line(page_w/2 - 4*cm, page_h - 3.5*cm, page_w/2 + 4*cm, page_h - 3.5*cm)

# Leer categorías
categories = []
for folder in CATEGORY_ORDER:
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files.sort()
    config = CATEGORY_CONFIG.get(folder, {'title': folder, 'specs': []})
    categories.append({
        'folder': folder,
        'id': safe_id(folder),
        'title': config['title'],
        'specs': config['specs'],
        'products': files
    })

# Dibujar botones de categorías en índice
btn_w = 8*cm
btn_h = 1.3*cm
margin_x = 2.5*cm
margin_y = 2.5*cm
gap_x = 1*cm
gap_y = 0.8*cm
cols = 3
rows = 3
start_y = page_h - 5*cm

for idx, cat in enumerate(categories):
    col = idx % cols
    row = idx // cols
    x = margin_x + col * (btn_w + gap_x)
    y = start_y - row * (btn_h + gap_y)
    
    # Fondo botón
    draw_rounded_rect(c, x, y, btn_w, btn_h, 8, GRAY)
    
    # Borde dorado
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.roundRect(x, y, btn_w, btn_h, 8, fill=0, stroke=1)
    
    # Texto
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + btn_w/2, y + btn_h/2 + 0.15*cm, cat['title'])
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 9)
    c.drawCentredString(x + btn_w/2, y + btn_h/2 - 0.35*cm, f"{len(cat['products'])} productos")
    
    # Enlace al destino de la categoría
    dest = f"cat_{cat['id']}"
    c.linkAbsolute("", dest, (x, y, x+btn_w, y+btn_h))

c.showPage()

# ========== PÁGINAS DE CATEGORÍAS ==========
PRODUCTS_PER_PAGE = 12
COLS = 4
ROWS = 3

margin = 1.2*cm
cell_w = (page_w - 2*margin) / COLS
cell_h = (page_h - 2*margin - 1.5*cm) / ROWS  # espacio extra para header

for cat in categories:
    total_prods = len(cat['products'])
    num_pages = (total_prods + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    dest = f"cat_{cat['id']}"
    
    for page_idx in range(num_pages):
        c.setFillColor(BLACK)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        
        # Destino en primera página de la categoría
        if page_idx == 0:
            c.bookmarkPage(dest)
            c.addOutlineEntry(cat['title'], dest, level=0)
        
        # Header con nombre de categoría
        header_h = 1.4*cm
        c.setFillColor(GRAY)
        c.rect(0, page_h - header_h, page_w, header_h, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 16)
        page_text = f"{cat['title']}  —  Página {page_idx + 1} de {num_pages}"
        c.drawString(margin, page_h - header_h + 0.45*cm, page_text)
        
        # Botón Volver al Índice
        btn_w_idx = 3.5*cm
        btn_h_idx = 0.8*cm
        btn_x = page_w - margin - btn_w_idx
        btn_y = page_h - header_h + 0.3*cm
        draw_rounded_rect(c, btn_x, btn_y, btn_w_idx, btn_h_idx, 5, GOLD)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(btn_x + btn_w_idx/2, btn_y + 0.25*cm, "← ÍNDICE")
        c.linkAbsolute("", "indice", (btn_x, btn_y, btn_x+btn_w_idx, btn_y+btn_h_idx))
        
        # Productos de esta página
        start_idx = page_idx * PRODUCTS_PER_PAGE
        end_idx = min(start_idx + PRODUCTS_PER_PAGE, total_prods)
        page_prods = cat['products'][start_idx:end_idx]
        
        for i, prod_file in enumerate(page_prods):
            col = i % COLS
            row = i // COLS
            x = margin + col * cell_w
            y = page_h - header_h - margin - (row + 1) * cell_h
            
            # Fondo celda
            draw_rounded_rect(c, x + 0.15*cm, y + 0.15*cm, cell_w - 0.3*cm, cell_h - 0.3*cm, 6, GRAY)
            
            # Especificaciones arriba (máx 3 líneas)
            c.setFillColor(LIGHT)
            c.setFont("Helvetica", 7)
            spec_y = y + cell_h - 0.6*cm
            for s_idx, spec in enumerate(cat['specs'][:3]):
                c.drawString(x + 0.3*cm, spec_y - s_idx*0.32*cm, f"• {spec}")
            
            # Imagen
            img_path = os.path.join(base_dir, cat['folder'], prod_file)
            img_max_w = cell_w - 0.6*cm
            img_max_h = cell_h - 2.2*cm
            
            if os.path.exists(img_path):
                iw, ih = get_image_size(img_path, img_max_w, img_max_h)
                img_x = x + (cell_w - iw) / 2
                img_y = y + 0.8*cm
                c.drawImage(img_path, img_x, img_y, width=iw, height=ih, mask='auto')
            
            # Nombre del producto abajo
            prod_name = os.path.splitext(prod_file)[0]
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x + cell_w/2, y + 0.35*cm, prod_name)
        
        c.showPage()

c.save()
print(f"PDF generado exitosamente: {output_pdf}")
print(f"Total páginas: {len(categories) + 2} aprox")
