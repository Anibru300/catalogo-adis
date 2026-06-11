# -*- coding: utf-8 -*-
"""
Catálogo PDF Premium ADIS v3 — Interactivo · Adaptativo · Infográfico
A4 Vertical · Tema oscuro · Grid inteligente · Navegación premium
"""

import os, sys, re, tempfile
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
OUTPUT_PDF = BASE_DIR / 'catalogo.pdf'
LOGO_PATH  = BASE_DIR / 'logo nuevo.jpeg'
QR_PATH    = BASE_DIR / 'codigo QR.jpeg'
MEDIA_DIR  = BASE_DIR / 'media'

# ========== PALETA PREMIUM ==========
BG        = HexColor('#080808')
SURFACE   = HexColor('#121212')
CARD_BG   = HexColor('#181818')
GOLD      = HexColor('#C8A951')
GOLD_DIM  = HexColor('#8A7340')
GOLD_LIGHT= HexColor('#E5C97A')
WHITE     = HexColor('#F0F0F0')
BODY      = HexColor('#BBBBBB')
MUTED     = HexColor('#777777')
LINE      = HexColor('#222222')
GREEN_OK  = HexColor('#4CAF50')
RED_NO    = HexColor('#E74C3C')

IMG_EXTS = ('.jpg', '.jpeg', '.png')
pw, ph = A4
MARGIN_L = 2.0*cm
MARGIN_R = 2.0*cm
MARGIN_T = 2.0*cm
MARGIN_B = 1.4*cm
CONTENT_W = pw - MARGIN_L - MARGIN_R

WEB_URL = 'https://adis-diseño.com'
WA_NUM  = '526311928993'
WA_MSG  = 'Hola ADIS, vi el catalogo y me interesa cotizar sus productos.'
WA_URL  = f'https://wa.me/{WA_NUM}?text={WA_MSG.replace(" ", "%20")}'

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
    if len(name) > 20:
        name = name[:18] + '...'
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

def prepare_logo(out_path, max_size=900):
    try:
        with Image.open(LOGO_PATH) as im:
            if im.mode in ('RGBA','P'):
                bg = Image.new('RGB', im.size, (8,8,8))
                if im.mode == 'P': im = im.convert('RGBA')
                bg.paste(im, mask=im.split()[-1]); im = bg
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            if max(im.size) > max_size:
                im.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            im.save(out_path, 'PNG'); return True
    except Exception as e:
        print(f"Logo error: {e}"); return False

def optimize_image(src, dst, max_dim=380, quality=75):
    try:
        with Image.open(src) as im:
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            if im.mode in ('RGBA','P'):
                bg = Image.new('RGB', im.size, (18,18,18))
                if im.mode == 'P': im = im.convert('RGBA')
                bg.paste(im, mask=im.split()[-1]); im = bg
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            im.save(dst, 'JPEG', quality=quality, optimize=True)
            return True
    except:
        return False

def get_product_code(cat_name, prod_file, idx):
    cat_code = re.sub(r'[^a-zA-Z]', '', cat_name)[:3].upper()
    prod_short = re.sub(r'[^a-zA-Z0-9]', '', clean_product(prod_file))[:5].upper()
    return f"{cat_code}-{prod_short}-{idx:02d}"

# ========== DATOS ENRIQUECIDOS ==========
SPECS = {
    'Placas PVC tipo madera': {'Material':'PVC','Dimensiones':'2440×1220×3mm','Presentación':'2.98m²/pz','Garantía':'15 años','Uso':'Interior'},
    'Placas PVC Texturizadas': {'Material':'PVC','Dimensiones':'2440×1220×5mm','Presentación':'2.98m²/pz','Garantía':'15 años','Uso':'Interior'},
    'Placas PVC Tipo espejo': {'Material':'PVC','Dimensiones':'2440×1220×5mm','Presentación':'2.98m²/pz','Garantía':'15 años','Uso':'Interior'},
    'Placas PVC': {'Material':'PVC','Dimensiones':'2440×1220mm','Presentación':'2.98m²/pz','Garantía':'15 años','Uso':'Interior'},
    'Lambrin Interior': {'Material':'WPC','Dimensiones':'2900×160×24mm','Presentación':'0.464m²/pz, 14pz/caja','Garantía':'15 años','Uso':'Interior'},
    'Lambrin Exterior': {'Material':'WPC','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'15 años','Uso':'Exterior'},
    'Desigual': {'Material':'WPC','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'15 años','Uso':'Interior'},
    'Media luna': {'Material':'WPC','Dimensiones':'2900×159×15mm','Presentación':'4.61m²/caja, 10pz','Garantía':'15 años','Uso':'Interior'},
    'Media luna PS': {'Material':'PS','Dimensiones':'2900×152×12mm','Presentación':'6.17m²/caja, 14pz','Garantía':'15 años','Uso':'Interior'},
    'Lambrin WPC': {'Material':'WPC','Dimensiones':'2900×160mm','Presentación':'Consultar','Garantía':'15 años','Uso':'Int/Ext'},
    'Revestimiento Flexible': {'Material':'Flexible','Dimensiones':'900×600 / 1200×600mm','Presentación':'0.54/0.72m²/pz','Garantía':'35 años','Uso':'Int/Ext'},
    'Plafon pvc laminado': {'Material':'PVC','Dimensiones':'2900×250×8mm','Presentación':'0.725m²/pz, 10pz/caja','Garantía':'15 años','Uso':'Interior'},
    'Plafon Laminado wood': {'Material':'PVC','Dimensiones':'2800×300×9mm','Presentación':'0.84m²/pz, 10pz/caja','Garantía':'15 años','Uso':'Interior'},
    'Plafon ranurado': {'Material':'PVC','Dimensiones':'2900×250×8mm','Presentación':'Por pieza','Garantía':'15 años','Uso':'Interior'},
    'Plafon PVC': {'Material':'PVC','Dimensiones':'2900×250mm','Presentación':'Consultar','Garantía':'15 años','Uso':'Interior'},
    'Blanco': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz, 10/40pz/caja','Garantía':'1 año','Uso':'Res/Com'},
    'Grises': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz, 10/40pz/caja','Garantía':'1 año','Uso':'Res/Com'},
    'Madera': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz, 10/40pz/caja','Garantía':'1 año','Uso':'Res/Com'},
    'Negro': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz, 10/40pz/caja','Garantía':'1 año','Uso':'Res/Com'},
    'Oro': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz, 10/40pz/caja','Garantía':'1 año','Uso':'Res/Com'},
    'Paneles tridimensionales': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz','Garantía':'1 año','Uso':'Res/Com'},
    'Interior': {'Material':'WPC','Dimensiones':'2900×100×50mm','Presentación':'1pz/caja','Garantía':'15 años','Uso':'Interior'},
    'Exterior': {'Material':'WPC','Dimensiones':'2850×120×70mm','Presentación':'1pz/caja','Garantía':'15 años','Uso':'Exterior'},
    'Vigas PVC': {'Material':'WPC/PVC','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'15 años','Uso':'Int/Ext'},
    'Laminado': {'Material':'Laminado','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'10 años','Uso':'Residencial'},
    'WPC': {'Material':'WPC','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'15 años','Uso':'Residencial'},
    'SPC': {'Material':'SPC','Dimensiones':'625×125mm, Esp. 5+1.5mm','Presentación':'Consultar','Garantía':'12 años','Uso':'Res/Com'},
    'Deck Sintetico': {'Material':'WPC Coextruido','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'18-25 años','Uso':'Exterior'},
    'Pisos': {'Material':'Varios','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'10-25 años','Uso':'Res/Com'},
    'Follaje Sintetico': {'Material':'Polietileno/PVC','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'5-8 años','Uso':'Int/Ext'},
    'Pasto Recreativo': {'Material':'Polietileno','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'8-12 años','Uso':'Exterior'},
    'Zacate': {'Material':'Polietileno','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'5-12 años','Uso':'Int/Ext'},
    'Placa tipo roca': {'Material':'PU/Poliuretano','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'Consultar','Uso':'Int/Ext'},
    'Cladding': {'Material':'PU/Poliuretano','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'Consultar','Uso':'Int/Ext'},
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
    {'icono':'💧','texto':'Los pisos SPC son 100% resistentes al agua, ideales para cocinas y baños.','cats':['Pisos']},
    {'icono':'🌲','texto':'El WPC combina fibras de madera y polímeros para ofrecer la belleza natural de la madera sin mantenimiento.','cats':['Lambrin WPC','Vigas PVC']},
    {'icono':'🪨','texto':'Los revestimientos flexibles se adaptan a superficies curvas sin perder su apariencia de piedra natural.','cats':['Revestimiento Flexible']},
    {'icono':'🧼','texto':'Las placas PVC previenen la acumulación de humedad y son extremadamente fáciles de limpiar.','cats':['Placas PVC','Plafon PVC']},
    {'icono':'☀️','texto':'El pasto sintético premium incorpora protección UV para conservar su color durante años.','cats':['Zacate']},
    {'icono':'🏠','texto':'El cladding mejora la estética de fachadas y protege los muros exteriores del clima.','cats':['Cladding']},
    {'icono':'🔇','texto':'Los paneles 3D no solo decoran: también mejoran la insonorización de tus espacios.','cats':['Paneles tridimensionales']},
]

COMPARATIVA_PISOS = [
    ['Característica','Laminado','SPC','WPC'],
    ['Resistencia al agua','Moderada','✓ 100%','✓ Impermeable'],
    ['Uso recomendado','Residencial','Res / Comercial','Exterior / Residencial'],
    ['Instalación','Sistema click','Sistema click','Click / Atornillado'],
    ['Resistencia impacto','●●●○○','●●●●●','●●●●○'],
    ['Confort acústico','●●●○○','●●●●●','●●●○○'],
    ['Garantía','10 años','12 años','15 años'],
]

def get_spec_for_cat(cat_name):
    for k in SPECS:
        if k.lower() in cat_name.lower() or cat_name.lower() in k.lower():
            return SPECS[k]
    return {'Material':'Consultar','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'Consultar','Uso':'Consultar'}

def get_ambient_for_cat(cat_name):
    for k,v in AMBIENT.items():
        if k.lower() in cat_name.lower() or cat_name.lower() in k.lower():
            return v
    return None

# ========== INICIAR CANVAS ==========
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)

# ========== FOOTER PREMIUM ==========
def draw_footer():
    fy = 0.9*cm
    c.setStrokeColor(LINE); c.setLineWidth(0.35)
    c.line(MARGIN_L, fy+0.55*cm, pw-MARGIN_R, fy+0.55*cm)
    # logo izquierda
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 1.2*cm, 0.75*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, fy-0.02*cm, width=lw, height=lh, mask='auto')
        except: pass
    # página centrada
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, fy+0.18*cm, f"Página {page_num}")
    # contacto derecha
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.5)
    c.drawRightString(pw-MARGIN_R, fy+0.18*cm, "adis-diseño.com  |  WhatsApp +52 631-192-8993")

# ========== BOTÓN VOLVER AL ÍNDICE (discreto) ==========
def draw_back_to_index():
    bx = pw - MARGIN_R - 2.6*cm
    by = ph - MARGIN_T - 0.5*cm
    bw, bh = 2.4*cm, 0.4*cm
    c.setFillColor(SURFACE); c.roundRect(bx, by, bw, bh, 2, fill=1, stroke=0)
    c.setStrokeColor(GOLD_DIM); c.setLineWidth(0.4)
    c.roundRect(bx, by, bw, bh, 2, fill=0, stroke=1)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(bx+bw/2, by+0.12*cm, "← Índice")
    c.linkAbsolute("Volver al índice", 'indice', (bx, by, bx+bw, by+bh))

# ========== PORTADA PREMIUM ==========
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
    # overlay oscuro profundo
    c.setFillColor(Color(0,0,0,alpha=0.78))
    c.rect(0,0,pw,ph,fill=1,stroke=0)
    for i in range(35):
        a = 0.28 - i*0.006
        if a > 0:
            c.setFillColor(Color(0,0,0,alpha=a))
            c.rect(0,0,pw, 9*cm - i*0.22*cm, fill=1,stroke=0)
    # marco doble dorado
    fm = 1.5*cm
    c.setStrokeColor(GOLD); c.setLineWidth(1.5)
    c.roundRect(fm, fm, pw-2*fm, ph-2*fm, 14, fill=0, stroke=1)
    c.setStrokeColor(GOLD_DIM); c.setLineWidth(0.35)
    c.roundRect(fm+0.25*cm, fm+0.25*cm, pw-2*fm-0.5*cm, ph-2*fm-0.5*cm, 12, fill=0, stroke=1)
    # logo grande centrado
    if logo_path and os.path.exists(logo_path):
        lw, lh = img_size(logo_path, 11*cm, 11*cm)
        lx = (pw - lw)/2
        ly = ph/2 - lh/2 + 1.2*cm
        c.drawImage(str(logo_path), lx, ly, width=lw, height=lh, mask='auto')
    # tagline
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(pw/2, ph/2 - 3.0*cm, "TRANSFORMAMOS ESPACIOS")
    c.setFillColor(GOLD_LIGHT); c.setFont("Helvetica", 12)
    c.drawCentredString(pw/2, ph/2 - 3.65*cm, "Materiales premium para arquitectura e interiorismo")
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 3.2*cm, ph/2 - 4.15*cm, pw/2 + 3.2*cm, ph/2 - 4.15*cm)
    c.setFillColor(MUTED); c.setFont("Helvetica", 10)
    c.drawCentredString(pw/2, 2.6*cm, "CATÁLOGO 2025  |  ADIS DISEÑO & REMODELACIÓN")
    c.setFillColor(GOLD); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, 2.0*cm, "Nogales, Sonora  |  Río Rico, AZ")

# ========== ÍNDICE CON FOTOS ==========
def draw_index(cats):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(pw/2, ph - MARGIN_T - 0.6*cm, "ÍNDICE")
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 1.8*cm, ph - MARGIN_T - 1.0*cm, pw/2 + 1.8*cm, ph - MARGIN_T - 1.0*cm)
    c.setFillColor(MUTED); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, ph - MARGIN_T - 1.35*cm, "Selecciona una categoría para navegar")
    # grid 3×3
    cols, rows = 3, 3
    gap = 0.45*cm
    card_w = (CONTENT_W - (cols-1)*gap) / cols
    card_h = (ph - MARGIN_T - 1.7*cm - MARGIN_B - (rows-1)*gap) / rows
    for i, cat in enumerate(cats):
        col = i % cols
        row = i // cols
        x = MARGIN_L + col * (card_w + gap)
        y = ph - MARGIN_T - 1.7*cm - (row+1)*(card_h+gap) + gap
        # fondo tarjeta
        c.setFillColor(SURFACE); c.roundRect(x, y, card_w, card_h, 6, fill=1, stroke=0)
        c.setStrokeColor(LINE); c.setLineWidth(0.4)
        c.roundRect(x, y, card_w, card_h, 6, fill=0, stroke=1)
        # foto miniatura arriba
        amb = get_ambient_for_cat(cat['name'])
        if amb and amb.exists():
            iw, ih = img_size(amb, card_w-0.4*cm, card_h*0.45)
            ix = x + (card_w-iw)/2
            iy = y + card_h - ih - 0.15*cm
            c.drawImage(str(amb), ix, iy, width=iw, height=ih, mask='auto')
        # línea dorada
        c.setStrokeColor(GOLD); c.setLineWidth(1.2)
        c.line(x+0.2*cm, y+card_h*0.48, x+card_w-0.2*cm, y+card_h*0.48)
        # nombre
        total = sum(len(s['products']) for s in cat['subs'])
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x+card_w/2, y+card_h*0.36, cat['name'].upper())
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(x+card_w/2, y+card_h*0.26, f"{total} productos")
        # descripción
        desc = CAT_DESC.get(cat['name'], '')
        if len(desc) > 45: desc = desc[:42] + '...'
        c.setFillColor(MUTED); c.setFont("Helvetica", 7.5)
        c.drawCentredString(x+card_w/2, y+card_h*0.17, desc)
        # destacado para PVC y Lambrin
        if cat['name'] in ('Placas PVC', 'Lambrin WPC'):
            c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 6.5)
            c.drawCentredString(x+card_w/2, y+card_h*0.08, "★ CATEGORÍA DESTACADA ★")
        # clickeable
        c.setFillColor(GOLD_DIM); c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(x+card_w/2, y+0.22*cm, "VER CATEGORÍA →")
        dest = f"cat_{i}"
        c.linkAbsolute(f"Ir a {cat['name']}", dest, (x, y, x+card_w, y+card_h))
    draw_footer()



# ========== BANNER "¿SABÍAS QUE?" (horizontal discreto) ==========
def draw_sabias_que_banner(item, y_base):
    bh = 1.1*cm
    bx = MARGIN_L
    bw = CONTENT_W
    c.setFillColor(SURFACE); c.roundRect(bx, y_base-bh, bw, bh, 4, fill=1, stroke=0)
    c.setStrokeColor(GOLD_DIM); c.setLineWidth(0.4)
    c.roundRect(bx, y_base-bh, bw, bh, 4, fill=0, stroke=1)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 8)
    c.drawString(bx+0.3*cm, y_base-bh+0.55*cm, f"{item['icono']}  ¿SABÍAS QUE?")
    c.setFillColor(BODY); c.setFont("Helvetica", 8)
    # truncar si es largo
    txt = item['texto']
    if len(txt) > 110: txt = txt[:107] + '...'
    c.drawString(bx+0.3*cm, y_base-bh+0.22*cm, txt)

# ========== INTRO DE CATEGORÍA PREMIUM ==========
def draw_category_intro(cat_name, cat_idx, total_prods, sabias_item=None):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    hh = 0.85*cm
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 0.95*cm, 0.65*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, ph-hh-0.08*cm, width=lw, height=lh, mask='auto')
        except: pass
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, ph-hh+0.12*cm, cat_name.upper())
    c.setStrokeColor(LINE); c.setLineWidth(0.3)
    c.line(MARGIN_L, ph-hh-0.04*cm, pw-MARGIN_R, ph-hh-0.04*cm)
    top = ph - MARGIN_T - hh - 0.3*cm
    # título
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 28)
    c.drawString(MARGIN_L, top, cat_name.upper())
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(MARGIN_L, top-0.42*cm, MARGIN_L+5.5*cm, top-0.42*cm)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 10)
    c.drawRightString(pw-MARGIN_R, top-0.15*cm, f"{total_prods} PRODUCTOS")
    # descripción
    desc = CAT_DESC.get(cat_name, '')
    c.setFillColor(BODY); c.setFont("Helvetica", 10)
    lines = []
    while desc:
        if len(desc) > 95:
            idx = desc[:95].rfind(' ')
            if idx == -1: idx = 95
            lines.append(desc[:idx]); desc = desc[idx:].strip()
        else:
            lines.append(desc); break
    for i, line in enumerate(lines[:2]):
        c.drawString(MARGIN_L, top-0.85*cm - i*0.36*cm, line)
    # foto ambiente
    amb = get_ambient_for_cat(cat_name)
    img_h = 4.8*cm
    img_y = top - 1.6*cm - img_h
    if amb and amb.exists():
        iw, ih = img_size(amb, CONTENT_W, img_h)
        c.drawImage(str(amb), MARGIN_L, img_y, width=iw, height=ih, mask='auto')
    # specs box
    specs_y = img_y - 0.6*cm
    rep_spec = get_spec_for_cat(cat_name)
    if rep_spec:
        c.setFillColor(SURFACE); c.roundRect(MARGIN_L, specs_y-0.75*cm, CONTENT_W, 0.85*cm, 4, fill=1, stroke=0)
        line1 = "  |  ".join([f"{k}: {v}" for k,v in list(rep_spec.items())[:3]])
        line2 = "  |  ".join([f"{k}: {v}" for k,v in list(rep_spec.items())[3:]])
        c.setFillColor(BODY); c.setFont("Helvetica", 8)
        c.drawString(MARGIN_L+0.3*cm, specs_y-0.22*cm, line1)
        if line2:
            c.drawString(MARGIN_L+0.3*cm, specs_y-0.48*cm, line2)
    # ventajas
    ben_y = specs_y - 1.0*cm
    benefits = get_benefits(cat_name)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN_L, ben_y, "VENTAJAS DESTACADAS")
    for i, (title, desc) in enumerate(benefits[:4]):
        col = i % 2
        row = i // 2
        x = MARGIN_L + col * (CONTENT_W/2 + 0.25*cm)
        y = ben_y - 0.5*cm - row*0.85*cm
        c.setFillColor(CARD_BG); c.roundRect(x, y-0.08*cm, CONTENT_W/2-0.2*cm, 0.72*cm, 3, fill=1, stroke=0)
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x+0.2*cm, y+0.32*cm, f"▸ {title}")
        c.setFillColor(MUTED); c.setFont("Helvetica", 7.5)
        c.drawString(x+0.2*cm, y+0.08*cm, desc[:48])
    # banner sabias que si aplica
    if sabias_item:
        draw_sabias_que_banner(sabias_item, 2.6*cm)
    draw_back_to_index()
    draw_footer()

# ========== PÁGINA DE PRODUCTOS (GRID ADAPTATIVO) ==========
def draw_product_page(cat_name, prods, tmp_img_dir, global_idx_start, sabias_item=None):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    hh = 0.85*cm
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 0.95*cm, 0.65*cm)
        try: c.drawImage(str(LOGO_PATH), MARGIN_L, ph-hh-0.08*cm, width=lw, height=lh, mask='auto')
        except: pass
    c.setFillColor(MUTED); c.setFont("Helvetica", 8)
    c.drawCentredString(pw/2, ph-hh+0.12*cm, cat_name.upper())
    c.setStrokeColor(LINE); c.setLineWidth(0.3)
    c.line(MARGIN_L, ph-hh-0.04*cm, pw-MARGIN_R, ph-hh-0.04*cm)
    top = ph - MARGIN_T - hh - 0.25*cm
    n = len(prods)
    # grid adaptativo
    if n >= 7:
        cols, rows = 3, 3
    elif n >= 5:
        cols, rows = 3, 2
    elif n == 4:
        cols, rows = 2, 2
    elif n == 3:
        cols, rows = 3, 1
    elif n == 2:
        cols, rows = 2, 1
    else:
        cols, rows = 1, 1
    gap = 0.35*cm
    banner_h = 1.3*cm if sabias_item else 0
    cell_w = (CONTENT_W - (cols-1)*gap) / cols
    cell_h = (top - MARGIN_B - (rows-1)*gap - banner_h) / rows
    for i, prod in enumerate(prods):
        col = i % cols
        row = i // cols
        x = MARGIN_L + col * (cell_w + gap)
        y = top - (row+1) * (cell_h + gap) + gap
        # tarjeta
        c.setFillColor(CARD_BG); c.roundRect(x, y, cell_w, cell_h, 4, fill=1, stroke=0)
        c.setStrokeColor(LINE); c.setLineWidth(0.3)
        c.roundRect(x, y, cell_w, cell_h, 4, fill=0, stroke=1)
        c.setStrokeColor(GOLD); c.setLineWidth(0.4)
        c.line(x, y, x+cell_w, y)
        # imagen
        src = prod['path'] / prod['file']
        dst = tmp_img_dir / f"opt_{global_idx_start+i}_{prod['file']}"
        if not dst.exists():
            optimize_image(src, dst, max_dim=360, quality=72)
        img_max_w = cell_w - 0.3*cm
        img_max_h = cell_h - 0.75*cm
        if dst.exists():
            iw, ih = img_size(dst, img_max_w, img_max_h)
            ix = x + (cell_w - iw)/2
            iy = y + 0.52*cm
            c.drawImage(str(dst), ix, iy, width=iw, height=ih, mask='auto')
        # nombre
        name = clean_product(prod['file'])
        fn = 8 if len(name) <= 16 else 7
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", fn)
        c.drawCentredString(x + cell_w/2, y + 0.30*cm, name)
        # código
        code = get_product_code(cat_name, prod['file'], global_idx_start+i+1)
        c.setFillColor(GOLD); c.setFont("Courier-Bold", 6.5)
        c.drawCentredString(x + cell_w/2, y + 0.10*cm, code)
    # banner sabias que
    if sabias_item:
        draw_sabias_que_banner(sabias_item, MARGIN_B + 0.1*cm)
    draw_back_to_index()
    draw_footer()

# ========== COMPARATIVA INFOGRÁFICA ==========
def draw_comparativa():
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(pw/2, ph - MARGIN_T - 0.7*cm, "COMPARATIVA DE PISOS")
    c.setStrokeColor(GOLD); c.setLineWidth(0.8)
    c.line(pw/2 - 2.8*cm, ph - MARGIN_T - 1.1*cm, pw/2 + 2.8*cm, ph - MARGIN_T - 1.1*cm)
    c.setFillColor(MUTED); c.setFont("Helvetica", 9)
    c.drawCentredString(pw/2, ph - MARGIN_T - 1.45*cm, "Encuentra el piso ideal según tus necesidades")
    data = COMPARATIVA_PISOS
    rows = len(data)
    cols = len(data[0])
    cell_w = CONTENT_W / cols
    start_y = ph - MARGIN_T - 2.2*cm
    for ri, row in enumerate(data):
        y = start_y - ri*0.85*cm
        for ci, text in enumerate(row):
            x = MARGIN_L + ci*cell_w
            if ri == 0:
                c.setFillColor(GOLD)
                c.rect(x, y-0.65*cm, cell_w-0.04*cm, 0.80*cm, fill=1, stroke=0)
                c.setFillColor(BG); c.setFont("Helvetica-Bold", 9)
            else:
                bgc = SURFACE if ri % 2 == 0 else CARD_BG
                c.setFillColor(bgc)
                c.rect(x, y-0.65*cm, cell_w-0.04*cm, 0.80*cm, fill=1, stroke=0)
                # color de texto según contenido
                if text.startswith('✓'):
                    c.setFillColor(GREEN_OK); c.setFont("Helvetica-Bold", 8.5)
                elif text.startswith('●'):
                    c.setFillColor(GOLD); c.setFont("Helvetica", 9)
                else:
                    c.setFillColor(BODY); c.setFont("Helvetica", 8.5)
            c.drawCentredString(x + cell_w/2 - 0.02*cm, y - 0.30*cm, text)
            c.setStrokeColor(LINE); c.setLineWidth(0.25)
            c.rect(x, y-0.65*cm, cell_w-0.04*cm, 0.80*cm, fill=0, stroke=1)
    # leyenda visual
    ly = 2.2*cm
    c.setFillColor(GREEN_OK); c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN_L, ly, "✓ = Excelente / Sí")
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN_L+3.5*cm, ly, "● = Nivel de resistencia / calidad")
    draw_back_to_index()
    draw_footer()

# ========== PÁGINA FINAL ==========
def draw_final_page(qr_path):
    c.setFillColor(BG); c.rect(0,0,pw,ph,fill=1,stroke=0)
    if LOGO_PATH.exists():
        lw, lh = img_size(LOGO_PATH, 5.5*cm, 5.5*cm)
        try: c.drawImage(str(LOGO_PATH), (pw-lw)/2, ph-7.8*cm, width=lw, height=lh, mask='auto')
        except: pass
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(pw/2, ph-8.6*cm, "Gracias por preferirnos")
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.line(pw/2-2.5*cm, ph-8.95*cm, pw/2+2.5*cm, ph-8.95*cm)
    c.setFillColor(BODY); c.setFont("Helvetica", 11)
    c.drawCentredString(pw/2, ph-9.5*cm, "Estamos listos para transformar tu espacio")
    # caja contacto
    c.setFillColor(SURFACE); c.roundRect(MARGIN_L+1.5*cm, 5.0*cm, CONTENT_W-3*cm, 3.8*cm, 8, fill=1, stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(0.5)
    c.roundRect(MARGIN_L+1.5*cm, 5.0*cm, CONTENT_W-3*cm, 3.8*cm, 8, fill=0, stroke=1)
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(pw/2, 8.3*cm, "CONTACTO")
    lines = [
        "WhatsApp: +52 631-192-8993",
        "Showroom: +52 631-120-4943",
        "Email: adis.remodelacion@gmail.com",
        "Web: adis-diseño.com",
        "Nogales, Sonora  |  Río Rico, AZ",
    ]
    c.setFillColor(BODY); c.setFont("Helvetica", 9.5)
    for i, line in enumerate(lines):
        c.drawCentredString(pw/2, 7.6*cm - i*0.42*cm, line)
    # QR con zona de seguridad
    if qr_path and os.path.exists(qr_path):
        qs = 3.4*cm
        qx = (pw-qs)/2
        qy = 1.0*cm
        pad = 0.25*cm
        c.setFillColor(WHITE); c.roundRect(qx-pad, qy-pad, qs+2*pad, qs+2*pad+0.7*cm, 8, fill=1, stroke=0)
        c.setStrokeColor(GOLD); c.setLineWidth(0.8)
        c.roundRect(qx-pad, qy-pad, qs+2*pad, qs+2*pad+0.7*cm, 8, fill=0, stroke=1)
        c.drawImage(str(qr_path), qx, qy, width=qs, height=qs, mask='auto')
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(pw/2, qy-0.55*cm, "Escanea para visitarnos")
    draw_footer()

# ========== GENERACIÓN PRINCIPAL ==========
print("="*55)
print("CATALOGO PREMIUM ADIS v3 — OPTIMIZADO")
print("="*55)

with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    logo_prep = tmp/'logo.png'
    qr_file = QR_PATH if QR_PATH.exists() else tmp/'qr.png'
    img_tmp = tmp/'imgs'
    img_tmp.mkdir()
    
    print("\n[1/4] Preparando assets...")
    prepare_logo(logo_prep)
    if not QR_PATH.exists():
        try:
            qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
            qr.add_data(WA_URL); qr.make(fit=True)
            img = qr.make_image(fill_color="#C8A951", back_color="#080808")
            img = img.resize((220,220), Image.Resampling.LANCZOS)
            img.save(qr_file)
        except: pass
    
    print("[2/4] Escaneando catálogo...")
    cats = scan_catalog()
    total_prods = sum(sum(len(s['products']) for s in c['subs']) for c in cats)
    print(f"       {len(cats)} categorías | {total_prods} productos")
    
    print("\n[3/4] Generando páginas...")
    # PORTADA
    draw_cover(str(logo_prep) if logo_prep.exists() else None)
    next_page()
    # ÍNDICE
    c.bookmarkPage('indice')
    c.addOutlineEntry('ÍNDICE', 'indice', level=0)
    draw_index(cats)
    next_page()
    # CATEGORÍAS
    for ci, cat in enumerate(cats):
        total_in_cat = sum(len(s['products']) for s in cat['subs'])
        # Elegir un sabias que para esta categoría
        sq_items = [s for s in SABIAS_QUE if cat['name'] in s['cats']]
        if not sq_items:
            sq_items = SABIAS_QUE
        sabias_intro = sq_items[ci % len(sq_items)]
        sabias_prod = sq_items[(ci+1) % len(sq_items)]
        # INTRO
        draw_category_intro(cat['name'], ci, total_in_cat, sabias_item=sabias_intro)
        dest = f"cat_{ci}"
        c.bookmarkPage(dest)
        c.addOutlineEntry(cat['name'], dest, level=0)
        next_page()
        # PRODUCTOS: combinar todos los productos de la categoría
        all_prods = []
        for sub in cat['subs']:
            for p in sub['products']:
                all_prods.append({'file':p, 'path':sub['path'], 'sub_name':sub['name']})
        # distribuir en grupos de 9
        per_page = 9
        npages = (len(all_prods) + per_page - 1) // per_page
        for pi in range(npages):
            start = pi * per_page
            group = all_prods[start:start+per_page]
            # sabias en la primera página de productos
            sab = sabias_prod if pi == 0 else None
            draw_product_page(cat['name'], group, img_tmp, start, sabias_item=sab)
            next_page()
        # comparativa para pisos
        if cat['name'] == 'Pisos':
            draw_comparativa()
            next_page()
    # CIERRE
    draw_final_page(str(qr_file) if qr_file.exists() else None)
    next_page()
    
    print("\n[4/4] Guardando PDF...")
    c.save()

print(f"\n{'='*55}")
print(f"PDF GENERADO: {OUTPUT_PDF}")
print(f"Total páginas: {page_num}")
print(f"{'='*55}")
try:
    sz = os.path.getsize(OUTPUT_PDF)
    print(f"Tamaño: {sz/1024/1024:.1f} MB")
except: pass
