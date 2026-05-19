# -*- coding: utf-8 -*-
"""
Catálogo PDF Editorial ADIS — Revista de Arquitectura e Interiorismo
A4 Vertical · Tema oscuro · Espaciado premium · Jerarquía clara
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
OUTPUT_PDF = BASE_DIR / 'catalogo_adis_editorial.pdf'
LOGO_PATH  = BASE_DIR / 'LOGO ADIS.png'
MEDIA_DIR  = BASE_DIR / 'media'

# ========== PALETA EDITORIAL ==========
BG       = HexColor('#0D0D0D')
SURFACE  = HexColor('#161616')
GOLD     = HexColor('#C5A059')
GOLD_SOFT= HexColor('#D4AF37')
WHITE    = HexColor('#FFFFFF')
BODY     = HexColor('#E0E0E0')
MUTED    = HexColor('#666666')
LINE     = HexColor('#333333')

IMG_EXTS = ('.jpg', '.jpeg', '.png')

# ========== MÁRGENES PREMIUM ==========
MARGIN_L = 2.5*cm
MARGIN_R = 2.5*cm
MARGIN_T = 2.5*cm
MARGIN_B = 2.0*cm
CONTENT_W = A4[0] - MARGIN_L - MARGIN_R

# WhatsApp
WA_NUM = '526311928993'
WA_MSG = 'Hola ADIS, vi el catalogo y me interesa cotizar sus productos.'
WA_URL = f'https://wa.me/{WA_NUM}?text={WA_MSG.replace(" ", "%20")}'

# ========== UTILIDADES ==========

def is_image(f): return f.lower().endswith(IMG_EXTS)
def is_ficha(f): return 'ficha' in f.lower() and is_image(f)

def clean_folder(name):
    return re.sub(r'^\d+(\.\d+)*\.?\s*', '', name).strip()

def clean_product(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^[^a-zA-Z]*', '', name)
    name = re.sub(r'\s*(copia|copy|img|imagen|new|nuevo)\s*$', '', name, flags=re.I)
    name = name.strip()
    # Title case inteligente
    words = name.split()
    result = []
    for w in words:
        if w.upper() in ('PVC','WPC','SPC','PS','PU','3D','DIY','UV','IXPE'):
            result.append(w.upper())
        else:
            result.append(w.capitalize())
    name = ' '.join(result)
    if len(name) > 28:
        name = name[:26] + '...'
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

def prepare_logo(out_path, max_size=600):
    try:
        with Image.open(LOGO_PATH) as im:
            if im.mode in ('RGBA','P'):
                bg = Image.new('RGB', im.size, (13,13,13))
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

def gen_qr(path, url, size=200):
    try:
        qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
        qr.add_data(url); qr.make(fit=True)
        img = qr.make_image(fill_color="#C5A059", back_color="#0D0D0D")
        img = img.resize((size,size), Image.Resampling.LANCZOS)
        img.save(path); return True
    except: return False

def optimize_image(src, dst, max_dim=500, quality=80):
    """Redimensiona y comprime imagen para PDF ligero."""
    try:
        with Image.open(src) as im:
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            if im.mode in ('RGBA','P'):
                bg = Image.new('RGB', im.size, (22,22,22))
                if im.mode == 'P': im = im.convert('RGBA')
                bg.paste(im, mask=im.split()[-1])
                im = bg
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            im.save(dst, 'JPEG', quality=quality, optimize=True)
            return True
    except:
        return False

# ========== DATOS ==========

SPECS = {
    'Placas PVC tipo madera': {'Material':'PVC','Dimensiones':'2440×1220×3mm','Presentacion':'2.98m²/pz, 1pz/caja','Garantia':'15 años','Uso':'Interior'},
    'Placas PVC Texturizadas': {'Material':'PVC','Dimensiones':'2440×1220×5mm','Presentacion':'2.98m²/pz, 1pz/caja','Garantia':'15 años','Uso':'Interior'},
    'Placas PVC Tipo espejo': {'Material':'PVC','Dimensiones':'2440×1220×5mm','Presentacion':'2.98m²/pz, 1pz/caja','Garantia':'15 años','Uso':'Interior'},
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

SKU_PREFIX = {
    'Placas PVC tipo madera':'PVC-MAD','Placas PVC Texturizadas':'PVC-TEX','Placas PVC Tipo espejo':'PVC-ESP',
    'Lambrin Interior':'WPC-INT','Lambrin Exterior':'WPC-EXT','Desigual':'WPC-DSG','Media luna':'WPC-MLU','Media luna PS':'WPC-MLP',
    'Revestimiento Flexible':'FLEX','Plafon pvc laminado':'PLF-LAM','Plafon Laminado wood':'PLF-WOD','Plafon ranurado':'PLF-RAN',
    'Blanco':'PAN3D-BLA','Grises':'PAN3D-GRY','Madera':'PAN3D-MAD','Negro':'PAN3D-BLK','Oro':'PAN3D-GLD',
    'Interior':'VIGA-INT','Exterior':'VIGA-EXT','Laminado':'PISO-LAM','WPC':'PISO-WPC','SPC':'PISO-SPC',
    'Deck Sintetico':'DECK','Follaje Sintetico':'ZAC-FOL','Pasto Recreativo':'ZAC-PST','Placa tipo roca':'CLD-ROC',
}

def get_sku(sub_name, idx):
    return f"{SKU_PREFIX.get(sub_name,'PROD')}-{idx:03d}"

BENEFITS = {
    'PVC': [('Impermeable','Ideal cocinas y banos'),('Antibacteriano','Higienico, facil limpieza'),('Resistente','No se deforma con humedad'),('Duradero','15+ anos de vida util')],
    'WPC': [('Natural','Textura real de madera'),('Indestructible','No se pudre ni deforma'),('Sin mantenimiento','Sin barniz ni pintura'),('Ecologico','Fibras de madera recicladas')],
    'SPC': [('Piedra real','Core rigido ultra resistente'),('Impermeable','Apto para todo ambiente'),('Instalacion DIY','Sistema click facil'),('Comercial','Soporta alto trafico')],
    'Deck': [('Sin astillas','No se agrieta con el tiempo'),('Anti-UV','No se decolora'),('Antiderrapante','Seguro mojado'),('Larga vida','18-25 anos garantia')],
    'Revestimiento Flexible': [('Flexible','Se adapta a cualquier superficie'),('35 anos','La garantia mas larga'),('Int/Ext','Interior y exterior'),('Ligero','No sobrecarga')],
    'Panel 3D': [('Impacto visual','Diseno arquitectonico'),('Facil','Instalacion sencilla'),('Pintable','Personaliza a tu gusto'),('Acustico','Mejora insonorizacion')],
    'Viga': [('Realista','Imita perfecto la madera'),('Impermeable','Resiste humedad'),('Ligero','Facil instalacion'),('Int/Ext','Ambos ambientes')],
    'Zacate': [('Siempre verde','Sin riego ni poda'),('Anti-UV','No se decolora'),('Drenaje','No se encharca'),('Pet friendly','Seguro mascotas')],
    'Cladding': [('Piedra real','Textura y color natural'),('Ligero','Facil de instalar'),('Versatil','Int/Ext'),('Termico','Aislante energetico')],
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
    'Pisos': 'Pisos laminados, WPC, SPC y deck sintetico para interior y exterior.',
    'Zacate': 'Pasto sintetico y follaje decorativo para jardines, terrazas y muros verdes.',
    'Cladding': 'Revestimientos exteriores tipo piedra y roca para fachadas y muros.',
}

CAT_MATERIAL = {
    'Placas PVC': 'PVC','Lambrin WPC': 'WPC','Revestimiento Flexible': 'Flexible',
    'Plafon PVC': 'PVC','Paneles tridimensionales': 'PVC/Compuesto','Vigas PVC': 'WPC/PVC',
    'Pisos': 'Varios','Zacate': 'Polietileno','Cladding': 'PU/Poliuretano',
}

# ========== INICIAR CANVAS ==========
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)
pw, ph = A4
page_num = 0

def next_page():
    global page_num
    c.showPage(); page_num += 1

# ========== DIBUJO DE PÁGINAS ==========

def draw_bg():
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    # sutil brillo dorado arriba-derecha
    for i in range(30):
        a = 0.012 - i*0.00035
        if a > 0:
            c.setFillColor(Color(197/255,160/255,89/255,alpha=a))
            c.circle(pw, ph, 12*cm - i*0.35*cm, fill=1, stroke=0)

def draw_header_min(cat_name=""):
    """Header minimalista: logo pequeno izquierda, categoria centro."""
    h = 0.9*cm
    # logo
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 1.0*cm, 0.7*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, ph - h - 0.1*cm, width=lw, height=lh, mask='auto')
        except: pass
    # categoria
    if cat_name:
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawCentredString(pw/2, ph - h + 0.15*cm, cat_name.upper())
    # linea sutil
    c.setStrokeColor(LINE); c.setLineWidth(0.3)
    c.line(MARGIN_L, ph - h - 0.05*cm, pw - MARGIN_R, ph - h - 0.05*cm)
    return h + 0.15*cm

def draw_footer_min():
    """Footer: solo numero de pagina centrado, pequeno."""
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, 0.7*cm, str(page_num))



def draw_cover(logo_path):
    """Portada espectacular con foto a pantalla completa."""
    bg = MEDIA_DIR / 'proyecto-recepcion.jpg'
    if not bg.exists(): bg = MEDIA_DIR / 'despues.jpg'
    
    if bg.exists():
        try:
            iw, ih = img_size(bg, pw, ph)
            sc = max(pw/iw, ph/ih)
            iw2, ih2 = iw*sc, ih*sc
            c.drawImage(str(bg), (pw-iw2)/2, (ph-ih2)/2, width=iw2, height=ih2)
        except: pass
    
    # overlay degradado desde abajo
    c.setFillColor(Color(0,0,0,alpha=0.82))
    c.rect(0,0,pw,ph,fill=1,stroke=0)
    for i in range(25):
        a = 0.35 - i*0.012
        if a > 0:
            c.setFillColor(Color(0,0,0,alpha=a))
            c.rect(0,0,pw, 7*cm - i*0.25*cm, fill=1,stroke=0)
    
    # marco dorado fino
    fm = 1.8*cm
    c.setStrokeColor(GOLD); c.setLineWidth(1.5)
    c.roundRect(fm, fm, pw-2*fm, ph-2*fm, 10, fill=0, stroke=1)
    c.setLineWidth(0.4)
    c.roundRect(fm+0.25*cm, fm+0.25*cm, pw-2*fm-0.5*cm, ph-2*fm-0.5*cm, 8, fill=0, stroke=1)
    
    # logo grande centrado
    if logo_path and os.path.exists(logo_path):
        lw, lh = img_size(logo_path, 7.5*cm, 7.5*cm)
        lx = (pw - lw)/2
        ly = ph/2 + 1.0*cm
        # circulo dorado sutil
        c.setStrokeColor(GOLD); c.setLineWidth(0.8)
        r = max(lw,lh)/2 + 0.5*cm
        c.circle(pw/2, ly+lh/2, r, fill=0, stroke=1)
        c.drawImage(str(logo_path), lx, ly, width=lw, height=lh, mask='auto')
    
    # tagline
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(pw/2, ph/2 - 1.2*cm, "TRANSFORMAMOS ESPACIOS")
    
    c.setFillColor(BODY); c.setFont("Helvetica", 13)
    c.drawCentredString(pw/2, ph/2 - 2.0*cm, "Materiales premium para arquitectura e interiorismo")
    
    # linea dorada
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(pw/2 - 2.5*cm, ph/2 - 2.5*cm, pw/2 + 2.5*cm, ph/2 - 2.5*cm)
    
    # año + marca abajo
    c.setFillColor(MUTED); c.setFont("Helvetica", 10)
    c.drawCentredString(pw/2, 2.2*cm, "2025  |  ADIS DISENO & REMODELACION")
    c.setFillColor(GOLD); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, 1.6*cm, "Nogales, Sonora  |  Rio Rico, AZ")


def draw_brand_page(qr_path):
    """Pagina unica de marca con toda la info comercial centralizada."""
    draw_bg()
    
    # logo
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 4.5*cm, 4.5*cm)
        try: c.drawImage(str(LOGO_PATH), (pw-lw)/2, ph-6*cm, width=lw, height=lh, mask='auto')
        except: pass
    
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(pw/2, ph-7.2*cm, "COMO COTIZAR")
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.line(pw/2-2*cm, ph-7.5*cm, pw/2+2*cm, ph-7.5*cm)
    
    # 3 pasos horizontales
    steps = [('1','Elige','Explora el catalogo y anota el SKU'),('2','Contacta','Escríbenos por WhatsApp'),('3','Recibe','Cotizacion en menos de 24h')]
    sw = CONTENT_W / 3
    for i, (num, title, desc) in enumerate(steps):
        x = MARGIN_L + i*sw
        y = ph - 8.5*cm
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(x + sw/2, y, num)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + sw/2, y-0.6*cm, title)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawCentredString(x + sw/2, y-1.0*cm, desc)
        if i < 2:
            c.setStrokeColor(LINE); c.setLineWidth(0.3)
            c.line(x+sw, y-0.3*cm, x+sw, y-1.1*cm)
    
    # caja de contacto
    box_y = ph - 11*cm
    bh = 4.2*cm
    c.setFillColor(SURFACE); c.roundRect(MARGIN_L, box_y-bh, CONTENT_W, bh, 8, fill=1, stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.roundRect(MARGIN_L, box_y-bh, CONTENT_W, bh, 8, fill=0, stroke=1)
    
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(pw/2, box_y-0.4*cm, "CONTACTO")
    
    contacts = [
        "WhatsApp: +52 631-192-8993",
        "Showroom: +52 631-120-4943",
        "Email: adis.remodelacion@gmail.com",
        "Ubicacion: Nogales, Sonora | Rio Rico, AZ",
    ]
    c.setFillColor(BODY); c.setFont("Helvetica", 9)
    for i, line in enumerate(contacts):
        c.drawCentredString(pw/2, box_y-1.0*cm - i*0.42*cm, line)
    
    # QR
    if qr_path and os.path.exists(qr_path):
        qs = 2.8*cm
        qx = (pw-qs)/2
        qy = box_y - 4.6*cm
        c.setFillColor(SURFACE); c.roundRect(qx-0.2*cm, qy-0.2*cm, qs+0.4*cm, qs+0.7*cm, 5, fill=1, stroke=0)
        c.setStrokeColor(GOLD); c.setLineWidth(0.5)
        c.roundRect(qx-0.2*cm, qy-0.2*cm, qs+0.4*cm, qs+0.7*cm, 5, fill=0, stroke=1)
        c.drawImage(str(qr_path), qx, qy, width=qs, height=qs, mask='auto')
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(pw/2, qy-0.45*cm, "Escanea para cotizar por WhatsApp")
    
    # garantias resumidas
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, 1.8*cm, "Garantias: PVC/WPC 15años | SPC 12años | Flexible 35años | Deck 18-25años")
    c.drawCentredString(pw/2, 1.4*cm, "Todos los precios incluyen IVA | Envios a todo Mexico")


def draw_category_intro(cat_name, cat_idx):
    """Intro de categoria con foto de ambiente, specs compactos, beneficios."""
    draw_bg()
    hh = draw_header_min(cat_name)
    top = ph - MARGIN_T - hh - 0.3*cm
    
    # nombre categoria grande
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 26)
    c.drawString(MARGIN_L, top, cat_name.upper())
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(MARGIN_L, top-0.4*cm, MARGIN_L+4*cm, top-0.4*cm)
    
    # descripcion
    desc = CAT_DESC.get(cat_name, '')
    c.setFillColor(BODY); c.setFont("Helvetica", 10)
    # truncar a 2 lineas
    if len(desc) > 90:
        desc = desc[:87] + '...'
    c.drawString(MARGIN_L, top-0.9*cm, desc)
    
    # foto de ambiente
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
    
    img_h = 5.5*cm
    if amb and amb.exists():
        iw, ih = img_size(amb, CONTENT_W, img_h)
        iy = top - 1.3*cm - ih
        c.drawImage(str(amb), MARGIN_L, iy, width=iw, height=ih, mask='auto')
    
    # specs compactos en formato horizontal
    specs_y = top - 1.5*cm - img_h
    # buscar specs representativos de esta categoria
    rep_spec = None
    for k in SPECS:
        if k.lower() in cat_name.lower() or any(s['name']==k for s in []):
            rep_spec = SPECS[k]; break
    if not rep_spec:
        for k in SPECS:
            if any(k.lower() in s['name'].lower() for s in []):
                rep_spec = SPECS[k]; break
    
    if rep_spec:
        # formato horizontal: Material · Dimensiones · Presentacion · Garantia
        line = " | ".join([f"{v}" for v in rep_spec.values()][:4])
        c.setFillColor(SURFACE); c.roundRect(MARGIN_L, specs_y-0.5*cm, CONTENT_W, 0.6*cm, 4, fill=1, stroke=0)
        c.setFillColor(BODY); c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN_L+0.3*cm, specs_y-0.22*cm, line)
    
    # beneficios
    ben_y = specs_y - 1.0*cm
    benefits = get_benefits(cat_name)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN_L, ben_y, "VENTAJAS")
    
    for i, (title, desc) in enumerate(benefits[:3]):
        y = ben_y - 0.5*cm - i*0.55*cm
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN_L+0.2*cm, y, "+")
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN_L+0.5*cm, y, title)
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawString(MARGIN_L+0.5*cm, y-0.22*cm, desc[:45])
    
    # lista de subcategorias
    sub_y = ben_y - 2.3*cm
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawString(MARGIN_L, sub_y, "Productos en esta categoria:")
    
    draw_footer_min()


def draw_separator(cat_name):
    """Pagina separadora elegante entre categorias."""
    draw_bg()
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2-3*cm, ph/2+0.8*cm, pw/2+3*cm, ph/2+0.8*cm)
    c.setFillColor(MUTED); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, ph/2+1.1*cm, "CATEGORIA")
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(pw/2, ph/2-0.3*cm, cat_name.upper())
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2-3*cm, ph/2-0.7*cm, pw/2+3*cm, ph/2-0.7*cm)


def draw_product_page(cat_name, subs_group, tmp_img_dir, global_idx_start):
    """Pagina de productos: grid 2x2, aireado, minimalista."""
    draw_bg()
    hh = draw_header_min(cat_name)
    top = ph - MARGIN_T - hh - 0.4*cm
    
    # titulo de grupo si es combinado
    if len(subs_group) > 1:
        names = " + ".join([s['name'] for s in subs_group])
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN_L, top, names)
        top -= 0.5*cm
    elif len(subs_group) == 1:
        c.setFillColor(MUTED); c.setFont("Helvetica", 9)
        c.drawString(MARGIN_L, top, subs_group[0]['name'])
        top -= 0.4*cm
    
    # grid 2x2
    cols, rows = 2, 2
    gap = 0.5*cm
    cell_w = (CONTENT_W - gap) / cols
    cell_h = (top - MARGIN_B - gap) / rows
    
    all_prods = []
    for sub in subs_group:
        for p in sub['products']:
            all_prods.append({'file':p, 'path':sub['path'], 'sub':sub['name']})
    
    for i, prod in enumerate(all_prods[:4]):
        col = i % cols
        row = i // cols
        x = MARGIN_L + col * (cell_w + gap)
        y = top - (row+1) * (cell_h + gap) + gap
        
        # fondo celda
        c.setFillColor(SURFACE)
        c.roundRect(x, y, cell_w, cell_h, 5, fill=1, stroke=0)
        # linea dorada inferior sutil
        c.setStrokeColor(GOLD); c.setLineWidth(0.5)
        c.line(x, y, x+cell_w, y)
        
        # imagen optimizada
        src = prod['path'] / prod['file']
        dst = tmp_img_dir / f"opt_{global_idx_start+i}_{prod['file']}"
        if not dst.exists():
            optimize_image(src, dst, max_dim=450, quality=75)
        
        img_max_w = cell_w - 0.8*cm
        img_max_h = cell_h - 1.6*cm
        if dst.exists():
            iw, ih = img_size(dst, img_max_w, img_max_h)
            ix = x + (cell_w - iw)/2
            iy = y + 0.9*cm
            c.drawImage(str(dst), ix, iy, width=iw, height=ih, mask='auto')
        
        # nombre
        name = clean_product(prod['file'])
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(x + cell_w/2, y + 0.5*cm, name)
        
        # SKU
        sku = get_sku(prod['sub'], global_idx_start+i+1)
        c.setFillColor(GOLD); c.setFont("Courier-Bold", 7.5)
        c.drawCentredString(x + cell_w/2, y + 0.2*cm, sku)
    
    draw_footer_min()


def draw_final_page(qr_path):
    """Pagina de cierre editorial."""
    draw_bg()
    
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 4*cm, 4*cm)
        try: c.drawImage(str(LOGO_PATH), (pw-lw)/2, ph-6.5*cm, width=lw, height=lh, mask='auto')
        except: pass
    
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(pw/2, ph-7.5*cm, "Gracias por preferirnos")
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.line(pw/2-2*cm, ph-7.85*cm, pw/2+2*cm, ph-7.85*cm)
    
    c.setFillColor(BODY); c.setFont("Helvetica", 10)
    c.drawCentredString(pw/2, ph-8.5*cm, "Estamos listos para transformar tu espacio")
    
    # contacto compacto
    c.setFillColor(MUTED); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, ph-9.5*cm, "+52 631-192-8993  |  adis.remodelacion@gmail.com")
    c.drawCentredString(pw/2, ph-9.9*cm, "Nogales, Sonora  |  Rio Rico, AZ")
    
    if qr_path and os.path.exists(qr_path):
        qs = 2.2*cm
        qx = (pw-qs)/2
        qy = 2.5*cm
        c.drawImage(str(qr_path), qx, qy, width=qs, height=qs, mask='auto')
        c.setFillColor(MUTED); c.setFont("Helvetica", 8)
        c.drawCentredString(pw/2, qy-0.4*cm, "Escanea para cotizar")


# ========== GENERACIÓN PRINCIPAL ==========
print("="*50)
print("CATALOGO EDITORIAL ADIS")
print("="*50)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    logo_prep = tmp/'logo.png'
    qr_file = tmp/'qr.png'
    img_tmp = tmp/'imgs'
    img_tmp.mkdir()
    
    print("\n[1/4] Preparando assets...")
    prepare_logo(logo_prep)
    gen_qr(qr_file, WA_URL, size=220)
    
    print("[2/4] Escaneando catalogo...")
    cats = scan_catalog()
    total_prods = sum(sum(len(s['products']) for s in c['subs']) for c in cats)
    print(f"       {len(cats)} categorias | {total_prods} productos")
    
    # calcular paginas
    total_pages = 1  # portada
    total_pages += 1  # marca
    total_pages += len(cats)  # intros
    total_pages += len(cats) - 1  # separadores (entre categorias)
    
    for cat in cats:
        for sub in cat['subs']:
            total_pages += (len(sub['products']) + 3) // 4  # 4 por pagina
    total_pages += 1  # cierre
    
    print(f"       Paginas estimadas: {total_pages}")
    
    print("\n[3/4] Generando paginas...")
    
    # PORTADA
    print("       -> Portada")
    draw_cover(str(logo_prep) if logo_prep.exists() else None)
    next_page()
    
    # MARCA
    print("       -> Pagina de marca")
    draw_brand_page(str(qr_file) if qr_file.exists() else None)
    c.bookmarkPage('indice'); c.addOutlineEntry('INDICE', 'indice', level=0)
    next_page()
    
    # CATEGORIAS
    global_idx = 0
    for ci, cat in enumerate(cats):
        # separador (excepto primera)
        if ci > 0:
            print(f"       -> Separador: {cat['name']}")
            draw_separator(cat['name'])
            next_page()
        
        # intro
        print(f"       -> Intro: {cat['name']}")
        draw_category_intro(cat['name'], ci)
        dest = f"cat_{ci}"
        c.bookmarkPage(dest); c.addOutlineEntry(cat['name'], dest, level=0)
        next_page()
        
        # productos por subcategoria
        for sub in cat['subs']:
            n = len(sub['products'])
            npages = (n + 3) // 4
            print(f"       -> {cat['name']} | {sub['name']} ({n} productos, {npages} paginas)")
            for pi in range(npages):
                start = pi * 4
                group = [{'name':sub['name'], 'products':sub['products'][start:start+4], 'path':sub['path']}]
                draw_product_page(cat['name'], group, img_tmp, global_idx + start)
                next_page()
            global_idx += n
    
    # CIERRE
    print("       -> Cierre")
    draw_final_page(str(qr_file) if qr_file.exists() else None)
    next_page()
    
    print("\n[4/4] Guardando...")
    c.save()

print(f"\n{'='*50}")
print(f"PDF GENERADO: {OUTPUT_PDF}")
# Copiar a nombre estandar para GitHub Pages
try:
    std = BASE_DIR / 'catalogo_adis.pdf'
    if std.exists():
        try: os.remove(std)
        except: pass
    if not std.exists():
        import shutil
        shutil.copy2(OUTPUT_PDF, std)
        print(f"Copiado tambien a: {std}")
except Exception as e:
    print(f"No se pudo copiar a nombre estandar: {e}")
print(f"Total paginas: {page_num}")
print(f"{'='*50}")

# Mostrar tamano
try:
    sz = os.path.getsize(OUTPUT_PDF)
    print(f"Tamanio: {sz/1024/1024:.1f} MB")
except: pass
