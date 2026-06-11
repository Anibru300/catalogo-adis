# -*- coding: utf-8 -*-
"""
Catálogo PDF Premium ADIS — Interactivo · Editorial · Navegable
A4 Vertical · Tema oscuro · Grid 3×3 · Links internos
"""

import os, sys, re, tempfile, io
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas
from PIL import Image
import qrcode

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ========== RUTAS ==========
BASE_DIR   = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR= Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')
OUTPUT_PDF = BASE_DIR / 'catalogo_temp.pdf'
LOGO_PATH  = BASE_DIR / 'logo nuevo.jpeg'
QR_PATH    = BASE_DIR / 'codigo QR.jpeg'
MEDIA_DIR  = BASE_DIR / 'media'

# ========== PALETA PREMIUM ==========
BG        = HexColor('#0A0A0A')
SURFACE   = HexColor('#141414')
CARD_BG   = HexColor('#1A1A1A')
GOLD      = HexColor('#C9A84C')
GOLD_LIGHT= HexColor('#E5C97A')
WHITE     = HexColor('#F5F5F5')
BODY      = HexColor('#CCCCCC')
MUTED     = HexColor('#888888')
LINE      = HexColor('#2A2A2A')

IMG_EXTS = ('.jpg', '.jpeg', '.png')

# ========== MÁRGENES ==========
MARGIN_L = 2.2*cm
MARGIN_R = 2.2*cm
MARGIN_T = 2.2*cm
MARGIN_B = 1.6*cm
CONTENT_W = A4[0] - MARGIN_L - MARGIN_R
pw, ph = A4

# ========== CONTACTO & WEB ==========
WEB_URL = 'https://adis-diseño.com'
WA_NUM  = '526311928993'
WA_MSG  = 'Hola ADIS, vi el catalogo y me interesa cotizar sus productos.'
WA_URL  = f'https://wa.me/{WA_NUM}?text={WA_MSG.replace(" ", "%20")}'

# ========== UTILIDADES ==========
page_num = 0

def next_page():
    global page_num
    c.showPage(); page_num += 1

def is_image(f): return f.lower().endswith(IMG_EXTS)
def is_ficha(f): return 'ficha' in f.lower() and is_image(f)

def clean_folder(name):
    return re.sub(r'^\d+(\.\d+)*\.?\s*', '', name).strip()

def clean_product(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^[^a-zA-Z]*', '', name)
    name = re.sub(r'\s*(copia|copy|img|imagen|new|nuevo)\s*$', '', name, flags=re.I)
    name = name.strip()
    words = name.split()
    result = []
    for w in words:
        if w.upper() in ('PVC','WPC','SPC','PS','PU','3D','DIY','UV','IXPE'):
            result.append(w.upper())
        else:
            result.append(w.capitalize())
    name = ' '.join(result)
    if len(name) > 26:
        name = name[:24] + '...'
    return name

def scan_catalog():
    cats = []
    for folder in sorted(os.listdir(CATALOG_DIR)):
        p = CATALOG_DIR / folder
        if not p.is_dir(): continue
        name = clean_folder(folder)
        subs = []
        direct = []
        for item in sorted(os.listdir(p)):
            ip = p / item
            if ip.is_dir():
                prods = [f for f in sorted(os.listdir(ip)) if is_image(f) and not is_ficha(f)]
                if prods:
                    subs.append({'name': clean_folder(item), 'products': prods, 'path': ip})
            elif is_image(item) and not is_ficha(item):
                direct.append(item)
        if direct:
            subs.append({'name': name, 'products': sorted(direct), 'path': p})
        cats.append({'name': name, 'subs': subs})
    return cats

def img_size(img_path, max_w, max_h):
    try:
        with Image.open(img_path) as im:
            iw, ih = im.size
            r = min(max_w/iw, max_h/ih)
            return iw*r, ih*r
    except:
        return max_w, max_h

def prepare_logo(out_path, max_size=800):
    try:
        with Image.open(LOGO_PATH) as im:
            if im.mode in ('RGBA','P'):
                bg = Image.new('RGB', im.size, (10,10,10))
                if im.mode == 'P': im = im.convert('RGBA')
                bg.paste(im, mask=im.split()[-1])
                im = bg
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            if max(im.size) > max_size:
                im.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            im.save(out_path, 'PNG')
            return True
    except Exception as e:
        print(f"Logo error: {e}")
        return False

def optimize_image(src, dst, max_dim=400, quality=75):
    try:
        with Image.open(src) as im:
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            if im.mode in ('RGBA','P'):
                bg = Image.new('RGB', im.size, (20,20,20))
                if im.mode == 'P': im = im.convert('RGBA')
                bg.paste(im, mask=im.split()[-1])
                im = bg
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            im.save(dst, 'JPEG', quality=quality, optimize=True)
            return True
    except:
        return False

def get_product_code(cat_name, prod_file, idx):
    cat_code = re.sub(r'[^a-zA-Z]', '', cat_name)[:3].upper()
    prod_short = re.sub(r'[^a-zA-Z0-9]', '', clean_product(prod_file))[:6].upper()
    return f"{cat_code}-{prod_short}-{idx:02d}"

# ========== DATOS ENRIQUECIDOS ==========

SPECS = {
    'Placas PVC tipo madera': {'Material':'PVC','Dimensiones':'2440×1220×3mm','Presentacion':'2.98m²/pz','Garantia':'15 años','Uso':'Interior'},
    'Placas PVC Texturizadas': {'Material':'PVC','Dimensiones':'2440×1220×5mm','Presentacion':'2.98m²/pz','Garantia':'15 años','Uso':'Interior'},
    'Placas PVC Tipo espejo': {'Material':'PVC','Dimensiones':'2440×1220×5mm','Presentacion':'2.98m²/pz','Garantia':'15 años','Uso':'Interior'},
    'Lambrin Interior': {'Material':'WPC','Dimensiones':'2900×160×24mm','Presentacion':'0.464m²/pz, 14pz/caja','Garantia':'15 años','Uso':'Interior'},
    'Lambrin Exterior': {'Material':'WPC','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'15 años','Uso':'Exterior'},
    'Desigual': {'Material':'WPC','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'15 años','Uso':'Interior'},
    'Media luna': {'Material':'WPC','Dimensiones':'2900×159×15mm','Presentacion':'4.61m²/caja, 10pz','Garantia':'15 años','Uso':'Interior'},
    'Media luna PS': {'Material':'PS','Dimensiones':'2900×152×12mm','Presentacion':'6.17m²/caja, 14pz','Garantia':'15 años','Uso':'Interior'},
    'Revestimiento Flexible': {'Material':'Flexible','Dimensiones':'900×600 / 1200×600mm','Presentacion':'0.54/0.72m²/pz','Garantia':'35 años','Uso':'Int/Ext'},
    'Plafon pvc laminado': {'Material':'PVC','Dimensiones':'2900×250×8mm','Presentacion':'0.725m²/pz, 10pz/caja','Garantia':'15 años','Uso':'Interior'},
    'Plafon Laminado wood': {'Material':'PVC','Dimensiones':'2800×300×9mm','Presentacion':'0.84m²/pz, 10pz/caja','Garantia':'15 años','Uso':'Interior'},
    'Plafon ranurado': {'Material':'PVC','Dimensiones':'2900×250×8mm','Presentacion':'Por pieza','Garantia':'15 años','Uso':'Interior'},
    'Blanco': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentacion':'0.25m²/pz, 10/40pz/caja','Garantia':'1 año','Uso':'Res/Com'},
    'Grises': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentacion':'0.25m²/pz, 10/40pz/caja','Garantia':'1 año','Uso':'Res/Com'},
    'Madera': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentacion':'0.25m²/pz, 10/40pz/caja','Garantia':'1 año','Uso':'Res/Com'},
    'Negro': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentacion':'0.25m²/pz, 10/40pz/caja','Garantia':'1 año','Uso':'Res/Com'},
    'Oro': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentacion':'0.25m²/pz, 10/40pz/caja','Garantia':'1 año','Uso':'Res/Com'},
    'Interior': {'Material':'WPC','Dimensiones':'2900×100×50mm','Presentacion':'1pz/caja','Garantia':'15 años','Uso':'Interior'},
    'Exterior': {'Material':'WPC','Dimensiones':'2850×120×70mm','Presentacion':'1pz/caja','Garantia':'15 años','Uso':'Exterior'},
    'Laminado': {'Material':'Laminado','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'10 años','Uso':'Residencial'},
    'WPC': {'Material':'WPC','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'15 años','Uso':'Residencial'},
    'SPC': {'Material':'SPC','Dimensiones':'625×125mm, Esp. 5+1.5mm','Presentacion':'Consultar','Garantia':'12 años','Uso':'Res/Com'},
    'Deck Sintetico': {'Material':'WPC Coextruido','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'18-25 años','Uso':'Exterior'},
    'Follaje Sintetico': {'Material':'Polietileno/PVC','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'5-8 años','Uso':'Int/Ext'},
    'Pasto Recreativo': {'Material':'Polietileno','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'8-12 años','Uso':'Exterior'},
    'Placa tipo roca': {'Material':'PU/Poliuretano','Dimensiones':'Consultar','Presentacion':'Consultar','Garantia':'Consultar','Uso':'Int/Ext'},
}

BENEFITS = {
    'PVC': [('Impermeable','Ideal cocinas y baños'),('Antibacteriano','Higiénico, fácil limpieza'),('Resistente','No se deforma con humedad'),('Duradero','15+ años de vida útil')],
    'WPC': [('Natural','Textura real de madera'),('Indestructible','No se pudre ni deforma'),('Sin mantenimiento','Sin barniz ni pintura'),('Ecológico','Fibras de madera recicladas')],
    'SPC': [('Piedra real','Core rígido ultra resistente'),('Impermeable','Apto para todo ambiente'),('Instalación DIY','Sistema click fácil'),('Comercial','Soporta alto tráfico')],
    'Deck': [('Sin astillas','No se agrieta con el tiempo'),('Anti-UV','No se decolora'),('Antiderrapante','Seguro mojado'),('Larga vida','18-25 años garantía')],
    'Revestimiento Flexible': [('Flexible','Se adapta a cualquier superficie'),('35 años','La garantía más larga'),('Int/Ext','Interior y exterior'),('Ligero','No sobrecarga')],
    'Panel 3D': [('Impacto visual','Diseño arquitectónico'),('Fácil','Instalación sencilla'),('Pintable','Personaliza a tu gusto'),('Acústico','Mejora insonorización')],
    'Viga': [('Realista','Imita perfecto la madera'),('Impermeable','Resiste humedad'),('Ligero','Fácil instalación'),('Int/Ext','Ambos ambientes')],
    'Zacate': [('Siempre verde','Sin riego ni poda'),('Anti-UV','No se decolora'),('Drenaje','No se encharca'),('Pet friendly','Seguro mascotas')],
    'Cladding': [('Piedra real','Textura y color natural'),('Ligero','Fácil de instalar'),('Versátil','Int/Ext'),('Térmico','Aislante energético')],
}

def get_benefits(sub_name):
    u = sub_name.upper()
    if 'PVC' in u and ('PLAC' in u or 'PLAF' in u): return BENEFITS['PVC']
    if 'WPC' in u or 'LAMBRIN' in u or 'DESIGUAL' in u or 'MEDIA LUNA' in u: return BENEFITS['WPC']
    if 'SPC' in u: return BENEFITS['SPC']
    if 'DECK' in u: return BENEFITS['Deck']
    if 'FLEX' in u or 'REVESTIMIENTO' in u: return BENEFITS['Revestimiento Flexible']
    if 'PANEL' in u or '3D' in u or sub_name in ('Blanco','Grises','Madera','Negro','Oro'): return BENEFITS['Panel 3D']
    if 'VIGA' in u or sub_name in ('Interior','Exterior'): return BENEFITS['Viga']
    if 'ZACATE' in u or 'FOLL' in u or 'PASTO' in u: return BENEFITS['Zacate']
    if 'CLAD' in u or 'ROCA' in u: return BENEFITS['Cladding']
    return BENEFITS['PVC']

AMBIENT = {
    'Placas PVC tipo madera':MEDIA_DIR/'pvc-real-01.jpeg','Placas PVC Texturizadas':MEDIA_DIR/'pvc-real-02.jpeg','Placas PVC Tipo espejo':MEDIA_DIR/'pvc-real-03.jpeg',
    'Lambrin Interior':MEDIA_DIR/'proyecto-02.jpeg','Lambrin Exterior':MEDIA_DIR/'proyecto-03.jpeg','Desigual':MEDIA_DIR/'proyecto-04.jpeg',
    'Media luna':MEDIA_DIR/'proyecto-05.jpeg','Media luna PS':MEDIA_DIR/'proyecto-06.jpeg','Revestimiento Flexible':MEDIA_DIR/'proyecto-07.jpeg',
    'Plafon pvc laminado':MEDIA_DIR/'pvc-real-04.jpeg','Plafon Laminado wood':MEDIA_DIR/'pvc-real-05.jpeg','Plafon ranurado':MEDIA_DIR/'pvc-real-06.jpeg',
    'Blanco':MEDIA_DIR/'proyecto-01.jpeg','Grises':MEDIA_DIR/'proyecto-02.jpeg','Madera':MEDIA_DIR/'proyecto-03.jpeg','Negro':MEDIA_DIR/'proyecto-04.jpeg','Oro':MEDIA_DIR/'proyecto-05.jpeg',
    'Interior':MEDIA_DIR/'proyecto-06.jpeg','Exterior':MEDIA_DIR/'proyecto-07.jpeg','Laminado':MEDIA_DIR/'pvc-real-01.jpeg',
    'WPC':MEDIA_DIR/'pvc-real-02.jpeg','SPC':MEDIA_DIR/'pvc-real-03.jpeg','Deck Sintetico':MEDIA_DIR/'despues.jpg',
    'Follaje Sintetico':MEDIA_DIR/'proyecto-recepcion.jpg','Pasto Recreativo':MEDIA_DIR/'proyecto-01.jpeg','Placa tipo roca':MEDIA_DIR/'ejemplo-tapiz.jpg',
}

CAT_DESC = {
    'Placas PVC': 'Soluciones decorativas de PVC para paredes interiores. Acabados tipo madera, texturizados y espejo.',
    'Lambrin WPC': 'Revestimientos de Wood Plastic Composite con apariencia natural de madera. Interior y exterior.',
    'Revestimiento Flexible': 'Paneles flexibles que se adaptan a cualquier superficie curva o irregular.',
    'Plafon PVC': 'Cielos rasos decorativos en PVC. Laminados, tipo madera y ranurados.',
    'Paneles tridimensionales': 'Paneles 3D decorativos para crear paredes con relieve y profundidad.',
    'Vigas PVC': 'Vigas decorativas tipo madera en PVC y WPC. Resistentes a humedad y termitas.',
    'Pisos': 'Pisos laminados, WPC, SPC y deck sintético para interior y exterior.',
    'Zacate': 'Pasto sintético y follaje decorativo para jardines, terrazas y muros verdes.',
    'Cladding': 'Revestimientos exteriores tipo piedra y roca para fachadas y muros.',
}

SABIAS_QUE = [
    {'icono':'💧','titulo':'¿Sabías que?','texto':'Los pisos SPC son 100% resistentes al agua y son ideales para cocinas y baños.','cats':['Pisos']},
    {'icono':'🌲','titulo':'¿Sabías que?','texto':'El WPC combina fibras de madera y polímeros para ofrecer la apariencia natural de la madera sin requerir mantenimiento constante.','cats':['Lambrin WPC','Vigas PVC']},
    {'icono':'🪨','titulo':'¿Sabías que?','texto':'Los revestimientos flexibles pueden adaptarse a superficies curvas sin perder su apariencia tipo piedra natural.','cats':['Revestimiento Flexible']},
    {'icono':'🧼','titulo':'¿Sabías que?','texto':'Las placas PVC ayudan a prevenir la acumulación de humedad y son fáciles de limpiar.','cats':['Placas PVC','Plafon PVC']},
    {'icono':'☀️','titulo':'¿Sabías que?','texto':'El pasto sintético de alta calidad incorpora protección UV para conservar su color durante años.','cats':['Zacate']},
    {'icono':'🏠','titulo':'¿Sabías que?','texto':'El cladding mejora la estética de las fachadas y contribuye a proteger los muros exteriores.','cats':['Cladding']},
    {'icono':'🔇','titulo':'¿Sabías que?','texto':'Los paneles 3D no solo decoran, también mejoran la insonorización de tus espacios.','cats':['Paneles tridimensionales']},
]

COMPARATIVA_PISOS = [
    ['Característica','Laminado','SPC','WPC'],
    ['Resistencia al agua','Moderada','100% Impermeable','Impermeable'],
    ['Uso recomendado','Residencial','Residencial / Comercial','Exterior / Residencial'],
    ['Instalación','Click','Click','Click / Atornillado'],
    ['Resistencia impacto','Media','Alta','Media-Alta'],
    ['Confort acústico','Bueno','Excelente','Bueno'],
    ['Garantía','10 años','12 años','15 años'],
]

# ========== INICIAR CANVAS ==========
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)

# ========== PIE DE PÁGINA ==========
def draw_footer():
    fy = 1.0*cm
    # línea divisoria
    c.setStrokeColor(LINE); c.setLineWidth(0.4)
    c.line(MARGIN_L, fy+0.5*cm, pw-MARGIN_R, fy+0.5*cm)
    # logo pequeño izquierda
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 1.4*cm, 0.9*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, fy-0.05*cm, width=lw, height=lh, mask='auto')
        except: pass
    # número de página centrado
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, fy+0.15*cm, str(page_num))
    # web + whatsapp derecha
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.5)
    c.drawRightString(pw-MARGIN_R, fy+0.15*cm, "adis-diseño.com  |  +52 631-192-8993")

# ========== BOTÓN VOLVER AL ÍNDICE ==========
def draw_back_to_index():
    bx = pw - MARGIN_R - 3.2*cm
    by = ph - MARGIN_T - 0.6*cm
    bw, bh = 3.0*cm, 0.5*cm
    c.setFillColor(GOLD); c.roundRect(bx, by, bw, bh, 3, fill=1, stroke=0)
    c.setFillColor(BG); c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(bx+bw/2, by+0.15*cm, "← Volver al Índice")
    c.linkAbsolute("Volver al índice", 'indice', (bx, by, bx+bw, by+bh))

# ========== PORTADA ==========
def draw_cover(logo_path):
    bg = MEDIA_DIR / 'proyecto-recepcion.jpg'
    if not bg.exists(): bg = MEDIA_DIR / 'despues.jpg'
    if bg.exists():
        try:
            iw, ih = img_size(bg, pw, ph)
            sc = max(pw/iw, ph/ih)
            iw2, ih2 = iw*sc, ih*sc
            c.drawImage(str(bg), (pw-iw2)/2, (ph-ih2)/2, width=iw2, height=ih2)
        except: pass
    # overlay oscuro gradiente
    c.setFillColor(Color(0,0,0,alpha=0.75))
    c.rect(0,0,pw,ph,fill=1,stroke=0)
    for i in range(30):
        a = 0.30 - i*0.008
        if a > 0:
            c.setFillColor(Color(0,0,0,alpha=a))
            c.rect(0,0,pw, 8*cm - i*0.25*cm, fill=1,stroke=0)
    # marco dorado doble
    fm = 1.6*cm
    c.setStrokeColor(GOLD); c.setLineWidth(1.2)
    c.roundRect(fm, fm, pw-2*fm, ph-2*fm, 12, fill=0, stroke=1)
    c.setLineWidth(0.35)
    c.roundRect(fm+0.3*cm, fm+0.3*cm, pw-2*fm-0.6*cm, ph-2*fm-0.6*cm, 10, fill=0, stroke=1)
    # logo grande centrado
    if logo_path and os.path.exists(logo_path):
        lw, lh = img_size(logo_path, 10.5*cm, 10.5*cm)
        lx = (pw - lw)/2
        ly = ph/2 - lh/2 + 1.0*cm
        c.drawImage(str(logo_path), lx, ly, width=lw, height=lh, mask='auto')
    # frase principal
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(pw/2, ph/2 - 3.2*cm, "TRANSFORMAMOS ESPACIOS")
    c.setFillColor(GOLD_LIGHT); c.setFont("Helvetica", 12)
    c.drawCentredString(pw/2, ph/2 - 3.9*cm, "Materiales premium para arquitectura e interiorismo")
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 3*cm, ph/2 - 4.4*cm, pw/2 + 3*cm, ph/2 - 4.4*cm)
    # año + ubicación
    c.setFillColor(MUTED); c.setFont("Helvetica", 10)
    c.drawCentredString(pw/2, 2.4*cm, "CATÁLOGO 2025  |  ADIS DISEÑO & REMODELACIÓN")
    c.setFillColor(GOLD); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, 1.8*cm, "Nogales, Sonora  |  Río Rico, AZ")

# ========== ÍNDICE INTERACTIVO ==========
def draw_index(cats):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    # header
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(pw/2, ph - MARGIN_T - 0.8*cm, "ÍNDICE")
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 2*cm, ph - MARGIN_T - 1.2*cm, pw/2 + 2*cm, ph - MARGIN_T - 1.2*cm)
    c.setFillColor(MUTED); c.setFont("Helvetica", 10)
    c.drawCentredString(pw/2, ph - MARGIN_T - 1.6*cm, "Selecciona una categoría para navegar directamente")
    # grid de tarjetas 3×3
    cols, rows = 3, 3
    gap = 0.5*cm
    card_w = (CONTENT_W - (cols-1)*gap) / cols
    card_h = (ph - MARGIN_T - 2.8*cm - MARGIN_B - (rows-1)*gap) / rows
    for i, cat in enumerate(cats):
        col = i % cols
        row = i // cols
        x = MARGIN_L + col * (card_w + gap)
        y = ph - MARGIN_T - 2.8*cm - (row+1)*(card_h+gap) + gap
        # fondo tarjeta
        c.setFillColor(SURFACE); c.roundRect(x, y, card_w, card_h, 6, fill=1, stroke=0)
        c.setStrokeColor(LINE); c.setLineWidth(0.5)
        c.roundRect(x, y, card_w, card_h, 6, fill=0, stroke=1)
        # línea dorada arriba
        c.setStrokeColor(GOLD); c.setLineWidth(2)
        c.line(x+0.3*cm, y+card_h-0.25*cm, x+card_w-0.3*cm, y+card_h-0.25*cm)
        # nombre categoría
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x+card_w/2, y+card_h-0.7*cm, cat['name'].upper())
        # conteo productos
        total = sum(len(s['products']) for s in cat['subs'])
        c.setFillColor(MUTED); c.setFont("Helvetica", 9)
        c.drawCentredString(x+card_w/2, y+card_h-1.1*cm, f"{total} productos")
        # descripción breve
        desc = CAT_DESC.get(cat['name'], '')
        if len(desc) > 55: desc = desc[:52] + '...'
        c.setFillColor(BODY); c.setFont("Helvetica", 8)
        c.drawCentredString(x+card_w/2, y+card_h-1.45*cm, desc)
        # texto clickeable
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(x+card_w/2, y+0.35*cm, "VER CATEGORÍA →")
        # link interno al destino de la categoría
        dest = f"cat_{i}"
        c.linkAbsolute(f"Ir a {cat['name']}", dest, (x, y, x+card_w, y+card_h))
    draw_footer()



# ========== INTRO DE CATEGORÍA ==========
def draw_category_intro(cat_name, cat_idx, total_prods):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    hh = 0.9*cm
    # header minimal
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 1.0*cm, 0.7*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, ph-hh-0.1*cm, width=lw, height=lh, mask='auto')
        except: pass
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, ph-hh+0.15*cm, cat_name.upper())
    c.setStrokeColor(LINE); c.setLineWidth(0.3)
    c.line(MARGIN_L, ph-hh-0.05*cm, pw-MARGIN_R, ph-hh-0.05*cm)
    top = ph - MARGIN_T - hh - 0.4*cm
    # título grande
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 28)
    c.drawString(MARGIN_L, top, cat_name.upper())
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(MARGIN_L, top-0.45*cm, MARGIN_L+5*cm, top-0.45*cm)
    # contador de productos
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11)
    c.drawString(pw-MARGIN_R-4*cm, top, f"{total_prods} PRODUCTOS")
    # descripción
    desc = CAT_DESC.get(cat_name, '')
    c.setFillColor(BODY); c.setFont("Helvetica", 10)
    lines = []
    while desc:
        if len(desc) > 90:
            idx = desc[:90].rfind(' ')
            if idx == -1: idx = 90
            lines.append(desc[:idx])
            desc = desc[idx:].strip()
        else:
            lines.append(desc); break
    for i, line in enumerate(lines[:2]):
        c.drawString(MARGIN_L, top-0.9*cm - i*0.38*cm, line)
    # foto ambiente
    amb = None
    for k,v in AMBIENT.items():
        if k.lower() in cat_name.lower() or cat_name.lower() in k.lower():
            amb = v; break
    if not amb or not amb.exists():
        for ext in IMG_EXTS:
            for f in sorted(os.listdir(MEDIA_DIR)):
                if f.lower().endswith(ext):
                    amb = MEDIA_DIR/f; break
            if amb: break
    img_h = 5.2*cm
    if amb and amb.exists():
        iw, ih = img_size(amb, CONTENT_W, img_h)
        iy = top - 2.0*cm - ih
        c.drawImage(str(amb), MARGIN_L, iy, width=iw, height=ih, mask='auto')
    # specs box
    specs_y = top - 2.3*cm - img_h
    rep_spec = None
    for k in SPECS:
        if k.lower() in cat_name.lower(): rep_spec = SPECS[k]; break
    if not rep_spec:
        for k in SPECS:
            if any(k.lower() in s['name'].lower() for s in []): rep_spec = SPECS[k]; break
    if rep_spec:
        c.setFillColor(SURFACE); c.roundRect(MARGIN_L, specs_y-0.6*cm, CONTENT_W, 0.7*cm, 4, fill=1, stroke=0)
        line = "  |  ".join([f"{k}: {v}" for k,v in rep_spec.items()])
        c.setFillColor(BODY); c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN_L+0.3*cm, specs_y-0.25*cm, line)
    # ventajas con iconos
    ben_y = specs_y - 1.2*cm
    benefits = get_benefits(cat_name)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN_L, ben_y, "VENTAJAS DESTACADAS")
    # 4 beneficios en 2 columnas
    for i, (title, desc) in enumerate(benefits[:4]):
        col = i % 2
        row = i // 2
        x = MARGIN_L + col * (CONTENT_W/2 + 0.3*cm)
        y = ben_y - 0.55*cm - row*0.9*cm
        c.setFillColor(SURFACE); c.roundRect(x, y-0.1*cm, CONTENT_W/2-0.2*cm, 0.75*cm, 3, fill=1, stroke=0)
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 9)
        c.drawString(x+0.2*cm, y+0.35*cm, f"▸ {title}")
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawString(x+0.2*cm, y+0.08*cm, desc[:45])
    # botón volver al índice
    draw_back_to_index()
    draw_footer()

# ========== PÁGINA DE PRODUCTOS (tarjetas profesionales) ==========
def draw_product_page(cat_name, subs_group, tmp_img_dir, global_idx_start):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    hh = 0.9*cm
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 1.0*cm, 0.7*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, ph-hh-0.1*cm, width=lw, height=lh, mask='auto')
        except: pass
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, ph-hh+0.15*cm, cat_name.upper())
    c.setStrokeColor(LINE); c.setLineWidth(0.3)
    c.line(MARGIN_L, ph-hh-0.05*cm, pw-MARGIN_R, ph-hh-0.05*cm)
    top = ph - MARGIN_T - hh - 0.3*cm
    # subtítulo
    if len(subs_group) > 1:
        names = " + ".join([s['name'] for s in subs_group])
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN_L, top, names)
        top -= 0.4*cm
    elif len(subs_group) == 1:
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawString(MARGIN_L, top, subs_group[0]['name'])
        top -= 0.3*cm
    # grid 3x3
    cols, rows = 3, 3
    gap = 0.35*cm
    cell_w = (CONTENT_W - (cols-1)*gap) / cols
    cell_h = (top - MARGIN_B - (rows-1)*gap) / rows
    all_prods = []
    for sub in subs_group:
        for p in sub['products']:
            all_prods.append({'file':p, 'path':sub['path'], 'sub':sub['name']})
    for i, prod in enumerate(all_prods[:9]):
        col = i % cols
        row = i // cols
        x = MARGIN_L + col * (cell_w + gap)
        y = top - (row+1) * (cell_h + gap) + gap
        # tarjeta
        c.setFillColor(CARD_BG); c.roundRect(x, y, cell_w, cell_h, 4, fill=1, stroke=0)
        c.setStrokeColor(LINE); c.setLineWidth(0.3)
        c.roundRect(x, y, cell_w, cell_h, 4, fill=0, stroke=1)
        c.setStrokeColor(GOLD); c.setLineWidth(0.5)
        c.line(x, y, x+cell_w, y)
        # imagen
        src = prod['path'] / prod['file']
        dst = tmp_img_dir / f"opt_{global_idx_start+i}_{prod['file']}"
        if not dst.exists():
            optimize_image(src, dst, max_dim=350, quality=72)
        img_max_w = cell_w - 0.25*cm
        img_max_h = cell_h - 0.7*cm
        if dst.exists():
            iw, ih = img_size(dst, img_max_w, img_max_h)
            ix = x + (cell_w - iw)/2
            iy = y + 0.48*cm
            c.drawImage(str(dst), ix, iy, width=iw, height=ih, mask='auto')
        # nombre
        name = clean_product(prod['file'])
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(x + cell_w/2, y + 0.28*cm, name)
        # código
        code = get_product_code(cat_name, prod['file'], global_idx_start+i+1)
        c.setFillColor(GOLD); c.setFont("Courier-Bold", 6.5)
        c.drawCentredString(x + cell_w/2, y + 0.08*cm, code)
    draw_back_to_index()
    draw_footer()

# ========== ¿SABÍAS QUE? ==========
def draw_sabias_que(item):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    # header
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(pw/2, ph - MARGIN_T - 1.0*cm, item['titulo'].upper())
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 2.5*cm, ph - MARGIN_T - 1.4*cm, pw/2 + 2.5*cm, ph - MARGIN_T - 1.4*cm)
    # icono grande
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 48)
    c.drawCentredString(pw/2, ph - MARGIN_T - 3.2*cm, item['icono'])
    # texto
    c.setFillColor(BODY); c.setFont("Helvetica", 13)
    words = item['texto'].split()
    lines = []
    line = ""
    for w in words:
        if len(line + " " + w) < 70:
            line += " " + w if line else w
        else:
            lines.append(line); line = w
    if line: lines.append(line)
    for i, l in enumerate(lines):
        c.drawCentredString(pw/2, ph - MARGIN_T - 4.5*cm - i*0.45*cm, l)
    # box decorativo
    c.setStrokeColor(GOLD); c.setLineWidth(0.6)
    c.roundRect(MARGIN_L + 1*cm, ph - MARGIN_T - 5.8*cm - len(lines)*0.45*cm, CONTENT_W - 2*cm, 0.6*cm + len(lines)*0.45*cm, 8, fill=0, stroke=1)
    draw_back_to_index()
    draw_footer()

# ========== TABLA COMPARATIVA ==========
def draw_comparativa():
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(pw/2, ph - MARGIN_T - 0.8*cm, "COMPARATIVA DE PISOS")
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 3*cm, ph - MARGIN_T - 1.2*cm, pw/2 + 3*cm, ph - MARGIN_T - 1.2*cm)
    c.setFillColor(MUTED); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, ph - MARGIN_T - 1.5*cm, "Encuentra el piso ideal según tus necesidades")
    data = COMPARATIVA_PISOS
    rows = len(data)
    cols = len(data[0])
    table_w = CONTENT_W
    table_h = (rows * 0.9*cm)
    cell_w = table_w / cols
    start_y = ph - MARGIN_T - 2.4*cm
    for ri, row in enumerate(data):
        y = start_y - ri*0.9*cm
        for ci, text in enumerate(row):
            x = MARGIN_L + ci*cell_w
            # fondo
            if ri == 0:
                c.setFillColor(GOLD)
                c.rect(x, y-0.7*cm, cell_w-0.05*cm, 0.85*cm, fill=1, stroke=0)
                c.setFillColor(BG); c.setFont("Helvetica-Bold", 9)
            else:
                bgc = SURFACE if ri % 2 == 0 else CARD_BG
                c.setFillColor(bgc)
                c.rect(x, y-0.7*cm, cell_w-0.05*cm, 0.85*cm, fill=1, stroke=0)
                c.setFillColor(BODY); c.setFont("Helvetica", 8.5)
            c.drawCentredString(x + cell_w/2 - 0.025*cm, y - 0.35*cm, text)
            c.setStrokeColor(LINE); c.setLineWidth(0.3)
            c.rect(x, y-0.7*cm, cell_w-0.05*cm, 0.85*cm, fill=0, stroke=1)
    draw_back_to_index()
    draw_footer()

# ========== PÁGINA FINAL ==========
def draw_final_page(qr_path):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 5*cm, 5*cm)
        try: c.drawImage(str(LOGO_PATH), (pw-lw)/2, ph-7.5*cm, width=lw, height=lh, mask='auto')
        except: pass
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(pw/2, ph-8.5*cm, "Gracias por preferirnos")
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.line(pw/2-2.5*cm, ph-8.85*cm, pw/2+2.5*cm, ph-8.85*cm)
    c.setFillColor(BODY); c.setFont("Helvetica", 11)
    c.drawCentredString(pw/2, ph-9.5*cm, "Estamos listos para transformar tu espacio")
    # contacto
    c.setFillColor(SURFACE); c.roundRect(MARGIN_L+1.5*cm, 5.2*cm, CONTENT_W-3*cm, 3.6*cm, 8, fill=1, stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.roundRect(MARGIN_L+1.5*cm, 5.2*cm, CONTENT_W-3*cm, 3.6*cm, 8, fill=0, stroke=1)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(pw/2, 8.4*cm, "CONTACTO")
    lines = [
        "WhatsApp: +52 631-192-8993",
        "Showroom: +52 631-120-4943",
        "Email: adis.remodelacion@gmail.com",
        "Web: adis-diseño.com",
        "Nogales, Sonora  |  Río Rico, AZ",
    ]
    c.setFillColor(BODY); c.setFont("Helvetica", 9.5)
    for i, line in enumerate(lines):
        c.drawCentredString(pw/2, 7.7*cm - i*0.42*cm, line)
    # QR profesional con zona de seguridad
    if qr_path and os.path.exists(qr_path):
        qs = 3.6*cm
        qx = (pw-qs)/2
        qy = 1.2*cm
        # zona de seguridad blanca
        pad = 0.25*cm
        c.setFillColor(WHITE); c.roundRect(qx-pad, qy-pad, qs+2*pad, qs+2*pad+0.7*cm, 8, fill=1, stroke=0)
        c.setStrokeColor(GOLD); c.setLineWidth(0.8)
        c.roundRect(qx-pad, qy-pad, qs+2*pad, qs+2*pad+0.7*cm, 8, fill=0, stroke=1)
        c.drawImage(str(qr_path), qx, qy, width=qs, height=qs, mask='auto')
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(pw/2, qy-0.55*cm, "Escanea para visitarnos")
    draw_footer()

# ========== GENERACIÓN PRINCIPAL ==========
print("="*50)
print("CATALOGO PREMIUM ADIS — INTERACTIVO")
print("="*50)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    logo_prep = tmp/'logo.png'
    qr_file = QR_PATH if QR_PATH.exists() else tmp/'qr.png'
    img_tmp = tmp/'imgs'
    img_tmp.mkdir()
    
    print("\n[1/5] Preparando assets...")
    prepare_logo(logo_prep)
    if not QR_PATH.exists():
        try:
            qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
            qr.add_data(WA_URL); qr.make(fit=True)
            img = qr.make_image(fill_color="#C9A84C", back_color="#0A0A0A")
            img = img.resize((220,220), Image.Resampling.LANCZOS)
            img.save(qr_file)
        except: pass
    
    print("[2/5] Escaneando catálogo...")
    cats = scan_catalog()
    total_prods = sum(sum(len(s['products']) for s in c['subs']) for c in cats)
    print(f"       {len(cats)} categorías | {total_prods} productos")
    
    # Estimar páginas
    total_pages = 1  # portada
    total_pages += 1  # índice
    sabias_counter = 0
    for ci, cat in enumerate(cats):
        total_pages += 1  # intro categoría
        for sub in cat['subs']:
            total_pages += (len(sub['products']) + 8) // 9
        # insertar sabias que cada ~4 páginas de esta categoría
        cat_pages = 1 + sum((len(s['products']) + 8)//9 for s in cat['subs'])
        total_pages += cat_pages // 4
        if cat['name'] == 'Pisos':
            total_pages += 1  # comparativa
    total_pages += 1  # cierre
    print(f"       Páginas estimadas: {total_pages}")
    
    print("\n[3/5] Generando portada e índice...")
    # PORTADA
    draw_cover(str(logo_prep) if logo_prep.exists() else None)
    next_page()
    # ÍNDICE
    c.bookmarkPage('indice')
    c.addOutlineEntry('ÍNDICE', 'indice', level=0)
    draw_index(cats)
    next_page()
    
    print("[4/5] Generando categorías...")
    global_idx = 0
    for ci, cat in enumerate(cats):
        total_in_cat = sum(len(s['products']) for s in cat['subs'])
        # INTRO
        draw_category_intro(cat['name'], ci, total_in_cat)
        dest = f"cat_{ci}"
        c.bookmarkPage(dest)
        c.addOutlineEntry(cat['name'], dest, level=0)
        next_page()
        
        cat_page_counter = 0
        for sub in cat['subs']:
            n = len(sub['products'])
            npages = (n + 8) // 9
            for pi in range(npages):
                start = pi * 9
                group = [{'name':sub['name'], 'products':sub['products'][start:start+9], 'path':sub['path']}]
                draw_product_page(cat['name'], group, img_tmp, global_idx + start)
                next_page()
                cat_page_counter += 1
                # insertar Sabías que cada 4 páginas
                if cat_page_counter % 4 == 0:
                    sq = [s for s in SABIAS_QUE if cat['name'] in s['cats']]
                    if not sq:
                        sq = SABIAS_QUE
                    item = sq[(ci + cat_page_counter//4) % len(sq)]
                    draw_sabias_que(item)
                    next_page()
            global_idx += n
        
        # Tabla comparativa para Pisos al final de la categoría
        if cat['name'] == 'Pisos':
            draw_comparativa()
            next_page()
    
    print("[5/5] Generando cierre...")
    draw_final_page(str(qr_file) if qr_file.exists() else None)
    next_page()
    
    print("\nGuardando PDF...")
    c.save()

# Reemplazar archivo final
final_path = BASE_DIR / 'catalogo.pdf'
try:
    if final_path.exists():
        os.remove(final_path)
    os.rename(OUTPUT_PDF, final_path)
    OUTPUT_PDF = final_path
except Exception as e:
    print(f"[AVISO] No se pudo reemplazar catalogo.pdf (puede estar abierto). Nuevo archivo: {OUTPUT_PDF}")

print(f"\n{'='*50}")
print(f"PDF GENERADO: {OUTPUT_PDF}")
print(f"Total páginas: {page_num}")
print(f"{'='*50}")
try:
    sz = os.path.getsize(OUTPUT_PDF)
    print(f"Tamaño: {sz/1024/1024:.1f} MB")
except: pass
