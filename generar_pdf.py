# -*- coding: utf-8 -*-
"""
Generador de Catálogo PDF Premium ADIS Diseño & Remodelación
A4 Vertical · Tema oscuro/dorado · Orientado a ventas
"""

import os
import sys
import re
import tempfile
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from PIL import Image
import qrcode

# Forzar UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ========== CONFIGURACIÓN ==========
BASE_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')
OUTPUT_PDF = BASE_DIR / 'catalogo_adis.pdf'
LOGO_PATH = BASE_DIR / 'LOGO ADIS.png'
MEDIA_DIR = BASE_DIR / 'media'

# Colores ADIS Premium
GOLD = HexColor('#C5A059')
GOLD_LIGHT = HexColor('#E8D5A3')
DARK = HexColor('#1C1C1E')
BLACK = HexColor('#0A0A0A')
GRAY = HexColor('#2C2C2E')
LIGHT = HexColor('#F5F5F5')
MUTED = HexColor('#8E8E93')
WHATSAPP = HexColor('#25D366')
WHITE = HexColor('#FFFFFF')

IMG_EXTS = ('.jpg', '.jpeg', '.png')
PRODUCTS_PER_PAGE = 6
COLS = 2
ROWS = 3

# WhatsApp
WHATSAPP_NUM = '526311928993'
WHATSAPP_MSG = 'Hola ADIS, vi el catálogo y me interesa cotizar sus productos.'
WHATSAPP_URL = f'https://wa.me/{WHATSAPP_NUM}?text={WHATSAPP_MSG.replace(" ", "%20")}'

# ========== UTILIDADES ==========

def is_image(filename):
    return filename.lower().endswith(IMG_EXTS)


def is_ficha(filename):
    return 'ficha' in filename.lower() and is_image(filename)


def clean_name(folder_name):
    cleaned = re.sub(r'^\d+(\.\d+)*\.?\s*', '', folder_name)
    return cleaned.strip()


def clean_product_name(filename):
    """Limpia nombre de producto para mostrar."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^[\d\w]+[\.\-_\s]+', '', name)
    name = re.sub(r'\s*\(?copia\)?\s*$', '', name, flags=re.I)
    name = re.sub(r'\s*\(?copy\)?\s*$', '', name, flags=re.I)
    return name.strip()


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


def prepare_logo(output_path, max_size=800):
    """Convierte logo RGBA a RGB para compatibilidad con ReportLab."""
    try:
        with Image.open(LOGO_PATH) as img:
            if img.mode in ('RGBA', 'P'):
                bg = Image.new('RGB', img.size, (10, 10, 10))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            img.save(output_path, 'PNG')
            return True
    except Exception as e:
        print(f"Error preparando logo: {e}")
        return False


def generate_qr(path, url, size=200):
    """Genera QR code con tema oscuro/dorado."""
    try:
        qr = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#C5A059", back_color="#0A0A0A")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        img.save(path)
        return True
    except Exception as e:
        print(f"Error generando QR: {e}")
        return False


# ========== DATOS TÉCNICOS ==========
SPECS_DATA = {
    'Placas PVC tipo madera': {
        'Material': 'PVC premium', 'Dimensiones': '2440 x 1220 x 3 mm',
        'Presentacion': '2.977 m2/pz, 1 pz/caja, 19 kg/pz',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Tipo madera natural'},
    'Placas PVC Texturizadas': {
        'Material': 'PVC premium', 'Dimensiones': '2440 x 1220 x 5 mm',
        'Presentacion': '2.977 m2/pz, 1 pz/caja, 10.5 kg/pz',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Textura 3D'},
    'Placas PVC Tipo espejo': {
        'Material': 'PVC premium', 'Dimensiones': '2440 x 1220 x 5 mm',
        'Presentacion': '2.977 m2/pz, 1 pz/caja, 10.5 kg/pz',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Alto brillo espejo'},
    'Lambrin Interior': {
        'Material': 'WPC', 'Dimensiones': '2900 x 160 x 24 mm',
        'Presentacion': '0.464 m2/pz, 14 pz/caja, 6.496 m2/caja',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Madera natural'},
    'Lambrin Exterior': {
        'Material': 'WPC', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '15 anos', 'Uso': 'Exterior',
        'Acabado': 'Madera texturizada'},
    'Desigual': {
        'Material': 'WPC', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Diseno desigual'},
    'Media luna': {
        'Material': 'WPC', 'Dimensiones': '2900 x 159 x 15 mm',
        'Presentacion': '4.611 m2/caja, 10 pzas/caja',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Media luna'},
    'Media luna PS': {
        'Material': 'PS (Poliestireno)', 'Dimensiones': '2900 x 152 x 12 mm',
        'Presentacion': '6.171 m2/caja, 14 pzas/caja',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Media luna'},
    'Revestimiento Flexible': {
        'Material': 'Revestimiento flexible', 'Dimensiones': '900x600 / 1200x600 mm',
        'Presentacion': '0.54/0.72 m2/pz, 13.5/0.72 m2/caja',
        'Garantia': '35 anos', 'Uso': 'Interior/Exterior',
        'Acabado': 'Textura flexible'},
    'Plafon pvc laminado': {
        'Material': 'PVC', 'Dimensiones': '2900 x 250 x 8 mm',
        'Presentacion': '0.725 m2/pz, 10 pz/caja, 7.25 m2/caja',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Laminado'},
    'Plafon Laminado wood': {
        'Material': 'PVC', 'Dimensiones': '2800 x 300 x 9 mm',
        'Presentacion': '0.84 m2/pz, 10 pz/caja, 8.4 m2/caja',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Madera laminada'},
    'Plafon ranurado': {
        'Material': 'PVC', 'Dimensiones': '2900 x 250 x 8 mm',
        'Presentacion': 'Por pieza, 2.90m largo x 0.25m ancho',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Ranurado decorativo'},
    'Blanco': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentacion': '0.25 m2/pz, 10/40 pz/caja',
        'Garantia': '1 ano', 'Uso': 'Residencial y comercial',
        'Acabado': '3D blanco'},
    'Grises': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentacion': '0.25 m2/pz, 10/40 pz/caja',
        'Garantia': '1 ano', 'Uso': 'Residencial y comercial',
        'Acabado': '3D gris'},
    'Madera': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentacion': '0.25 m2/pz, 10/40 pz/caja',
        'Garantia': '1 ano', 'Uso': 'Residencial y comercial',
        'Acabado': '3D madera'},
    'Negro': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentacion': '0.25 m2/pz, 10/40 pz/caja',
        'Garantia': '1 ano', 'Uso': 'Residencial y comercial',
        'Acabado': '3D negro'},
    'Oro': {
        'Material': 'PVC / Compuesto', 'Dimensiones': '500 x 500 mm',
        'Presentacion': '0.25 m2/pz, 10/40 pz/caja',
        'Garantia': '1 ano', 'Uso': 'Residencial y comercial',
        'Acabado': '3D dorado'},
    'Interior': {
        'Material': 'WPC', 'Dimensiones': '2900 x 100 x 50 mm',
        'Presentacion': '1 pz/caja',
        'Garantia': '15 anos', 'Uso': 'Interior',
        'Acabado': 'Madera natural'},
    'Exterior': {
        'Material': 'WPC', 'Dimensiones': '2850 x 120 x 70 mm',
        'Presentacion': '1 pz/caja',
        'Garantia': '15 anos sin carga', 'Uso': 'Exterior',
        'Acabado': 'Madera exterior'},
    'Laminado': {
        'Material': 'Laminado', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '10 anos', 'Uso': 'Residencial',
        'Acabado': 'Madera/Piedra'},
    'WPC': {
        'Material': 'WPC', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '15 anos', 'Uso': 'Residencial',
        'Acabado': 'Madera natural'},
    'SPC': {
        'Material': 'SPC', 'Dimensiones': '625 x 125 mm, Espesor 5+1.5 mm',
        'Presentacion': 'Consultar', 'Garantia': '12 anos', 'Uso': 'Residencial/Comercial',
        'Acabado': 'Piedra/Madera'},
    'Deck Sintetico': {
        'Material': 'WPC Coextruido', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '18-25 anos', 'Uso': 'Exterior',
        'Acabado': 'Madera exterior'},
    'Follaje Sintetico': {
        'Material': 'Polietileno / PVC', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '5-8 anos', 'Uso': 'Int/Ext',
        'Acabado': 'Natural'},
    'Pasto Recreativo': {
        'Material': 'Polietileno', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': '8-12 anos', 'Uso': 'Exterior',
        'Acabado': 'Natural'},
    'Placa tipo roca': {
        'Material': 'PU / Poliuretano', 'Dimensiones': 'Consultar',
        'Presentacion': 'Consultar', 'Garantia': 'Consultar', 'Uso': 'Int/Ext',
        'Acabado': 'Piedra natural'},
}


# ========== SISTEMA DE SKU ==========
SKU_PREFIX = {
    'Placas PVC tipo madera': 'PVC-MAD',
    'Placas PVC Texturizadas': 'PVC-TEX',
    'Placas PVC Tipo espejo': 'PVC-ESP',
    'Lambrin Interior': 'WPC-INT',
    'Lambrin Exterior': 'WPC-EXT',
    'Desigual': 'WPC-DSG',
    'Media luna': 'WPC-MLU',
    'Media luna PS': 'WPC-MLP',
    'Revestimiento Flexible': 'FLEX',
    'Plafon pvc laminado': 'PLF-LAM',
    'Plafon Laminado wood': 'PLF-WOD',
    'Plafon ranurado': 'PLF-RAN',
    'Blanco': 'PAN3D-BLA',
    'Grises': 'PAN3D-GRY',
    'Madera': 'PAN3D-MAD',
    'Negro': 'PAN3D-BLK',
    'Oro': 'PAN3D-GLD',
    'Interior': 'VIGA-INT',
    'Exterior': 'VIGA-EXT',
    'Laminado': 'PISO-LAM',
    'WPC': 'PISO-WPC',
    'SPC': 'PISO-SPC',
    'Deck Sintetico': 'DECK',
    'Follaje Sintetico': 'ZAC-FOL',
    'Pasto Recreativo': 'ZAC-PST',
    'Placa tipo roca': 'CLD-ROC',
}


def get_sku(sub_name, prod_idx):
    prefix = SKU_PREFIX.get(sub_name, 'PROD')
    return f"{prefix}-{prod_idx:03d}"


# ========== VENTAJAS POR MATERIAL ==========
VENTAJAS = {
    'PVC': [
        ('100% Impermeable', 'Ideal para cocinas, banos y areas humedas'),
        ('Antibacteriano', 'Higienico y facil de desinfectar'),
        ('Resistente a rayaduras', 'Mantiene su apariencia por anos'),
        ('No se deforma', 'Con la humedad ni cambios de temperatura'),
        ('Instalacion rapida', 'Sin obra ni polvo, listo en horas'),
        ('15+ anos de vida util', 'Inversion a largo plazo'),
    ],
    'WPC': [
        ('Apariencia 100% natural', 'Textura y veta real de madera'),
        ('No se pudre ni deforma', 'Resiste humedad y termitas'),
        ('Cero mantenimiento', 'Sin barniz, sin lijado, sin pintura'),
        ('Instalacion con click', 'Sistema facil y rapido'),
        ('Ecologico', 'Hecho con fibras de madera recicladas'),
        ('15 anos de garantia', 'Durabilidad comprobada'),
    ],
    'SPC': [
        ('Core rigido de piedra', 'Ultra resistente al impacto'),
        ('100% impermeable', 'Apto para cocinas y banos'),
        ('Instalacion DIY', 'Sistema click sin pegamento'),
        ('Trafico comercial', 'Soporta alto uso intensivo'),
        ('Compatible con calefaccion', 'Piso radiante bajo demanda'),
    ],
    'Deck': [
        ('No se astilla ni agrieta', 'Mantiene su integridad por anos'),
        ('Resistente a UV', 'No se decolora con el sol'),
        ('Sin mantenimiento anual', 'Olvidate de barnizar'),
        ('Textura antiderrapante', 'Seguro incluso mojado'),
        ('18-25 anos de garantia', 'La mas larga del mercado'),
    ],
    'Revestimiento Flexible': [
        ('Instalacion en 3D', 'Se adapta a cualquier superficie'),
        ('35 anos de garantia', 'La mas larga de todas'),
        ('Int/Ext', 'Para interior y exterior'),
        ('Ligero', 'No sobrecarga las estructuras'),
    ],
    'Panel 3D': [
        ('Diseno arquitectonico', 'Impacto visual inmediato'),
        ('Facil instalacion', 'Sistema de pegado o fijacion'),
        ('Pintable', 'Personalizable a tu gusto'),
        ('Acustico', 'Mejora la insonorizacion'),
    ],
    'Viga': [
        ('Acabado realista', 'Imita perfectamente la madera'),
        ('No se pudre', 'Resiste humedad sin problema'),
        ('Ligero', 'Facil manipulacion e instalacion'),
        ('Int/Ext', 'Opciones para ambos ambientes'),
    ],
    'Zacate': [
        ('Siempre verde', 'Sin riego, sin poda'),
        ('Resistente a UV', 'No se decolora'),
        ('Drenaje integrado', 'No se encharca'),
        ('Pet friendly', 'Seguro para mascotas'),
    ],
    'Cladding': [
        ('Aspecto piedra real', 'Textura y color naturales'),
        ('Ligero', 'Facil de instalar en cualquier pared'),
        ('Int/Ext', 'Versatil para cualquier espacio'),
        ('Aislante termico', 'Mejora la eficiencia energetica'),
    ],
}


def get_ventajas(sub_name):
    sub_upper = sub_name.upper()
    if 'PVC' in sub_upper and 'PLAC' in sub_upper:
        return VENTAJAS['PVC']
    if 'PVC' in sub_upper and 'PLAF' in sub_upper:
        return VENTAJAS['PVC']
    if 'WPC' in sub_upper or 'LAMBRIN' in sub_upper or 'DESIGUAL' in sub_upper or 'MEDIA LUNA' in sub_upper:
        return VENTAJAS['WPC']
    if 'SPC' in sub_upper:
        return VENTAJAS['SPC']
    if 'DECK' in sub_upper:
        return VENTAJAS['Deck']
    if 'FLEX' in sub_upper or 'REVESTIMIENTO' in sub_upper:
        return VENTAJAS['Revestimiento Flexible']
    if 'PANEL' in sub_upper or '3D' in sub_upper or sub_name in ('Blanco', 'Grises', 'Madera', 'Negro', 'Oro'):
        return VENTAJAS['Panel 3D']
    if 'VIGA' in sub_upper or sub_name in ('Interior', 'Exterior'):
        return VENTAJAS['Viga']
    if 'ZACATE' in sub_upper or 'FOLL' in sub_upper or 'PASTO' in sub_upper:
        return VENTAJAS['Zacate']
    if 'CLAD' in sub_upper or 'ROCA' in sub_upper:
        return VENTAJAS['Cladding']
    return VENTAJAS['PVC']


# ========== IMAGENES DE AMBIENTE REAL ==========
AMBIENT_IMAGES = {
    'Placas PVC tipo madera': MEDIA_DIR / 'pvc-real-01.jpeg',
    'Placas PVC Texturizadas': MEDIA_DIR / 'pvc-real-02.jpeg',
    'Placas PVC Tipo espejo': MEDIA_DIR / 'pvc-real-03.jpeg',
    'Lambrin Interior': MEDIA_DIR / 'proyecto-02.jpeg',
    'Lambrin Exterior': MEDIA_DIR / 'proyecto-03.jpeg',
    'Desigual': MEDIA_DIR / 'proyecto-04.jpeg',
    'Media luna': MEDIA_DIR / 'proyecto-05.jpeg',
    'Media luna PS': MEDIA_DIR / 'proyecto-06.jpeg',
    'Revestimiento Flexible': MEDIA_DIR / 'proyecto-07.jpeg',
    'Plafon pvc laminado': MEDIA_DIR / 'pvc-real-04.jpeg',
    'Plafon Laminado wood': MEDIA_DIR / 'pvc-real-05.jpeg',
    'Plafon ranurado': MEDIA_DIR / 'pvc-real-06.jpeg',
    'Blanco': MEDIA_DIR / 'proyecto-01.jpeg',
    'Grises': MEDIA_DIR / 'proyecto-02.jpeg',
    'Madera': MEDIA_DIR / 'proyecto-03.jpeg',
    'Negro': MEDIA_DIR / 'proyecto-04.jpeg',
    'Oro': MEDIA_DIR / 'proyecto-05.jpeg',
    'Interior': MEDIA_DIR / 'proyecto-06.jpeg',
    'Exterior': MEDIA_DIR / 'proyecto-07.jpeg',
    'Laminado': MEDIA_DIR / 'pvc-real-01.jpeg',
    'WPC': MEDIA_DIR / 'pvc-real-02.jpeg',
    'SPC': MEDIA_DIR / 'pvc-real-03.jpeg',
    'Deck Sintetico': MEDIA_DIR / 'despues.jpg',
    'Follaje Sintetico': MEDIA_DIR / 'proyecto-recepcion.jpg',
    'Pasto Recreativo': MEDIA_DIR / 'proyecto-01.jpeg',
    'Placa tipo roca': MEDIA_DIR / 'ejemplo-tapiz.jpg',
}


def get_ambient_image(sub_name):
    path = AMBIENT_IMAGES.get(sub_name)
    if path and os.path.exists(path):
        return path
    for ext in IMG_EXTS:
        for f in sorted(os.listdir(MEDIA_DIR)):
            if f.lower().endswith(ext):
                return MEDIA_DIR / f
    return None



# ========== INICIAR PDF ==========
c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)
page_w, page_h = A4
margin = 2*cm
page_num = 0


def next_page():
    global page_num
    c.showPage()
    page_num += 1


def draw_page_bg():
    """Fondo negro con sutil degradado dorado en esquina superior derecha."""
    c.setFillColor(BLACK)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    for i in range(40):
        alpha = 0.015 - (i * 0.0003)
        if alpha > 0:
            c.setFillColor(Color(197/255, 160/255, 89/255, alpha=alpha))
            c.circle(page_w, page_h, 14*cm - i*0.3*cm, fill=1, stroke=0)


def draw_header(title_text):
    h = 1.2*cm
    c.setFillColor(DARK)
    c.rect(0, page_h - h, page_w, h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(margin, page_h - h, page_w - margin, page_h - h)
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_w/2, page_h - h + 0.35*cm, title_text.upper())
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 6.5)
    c.drawRightString(page_w - margin, page_h - h + 0.35*cm, "ADIS DISENO & REMODELACION")
    return h


def draw_footer(page_n, total_n, show_cta=True):
    h = 1.0*cm
    c.setFillColor(DARK)
    c.rect(0, 0, page_w, h, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(margin, h, page_w - margin, h)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(margin, 0.35*cm, "WhatsApp: +52 631-192-8993  |  Showroom: +52 631-120-4943")
    if show_cta:
        c.setFillColor(WHATSAPP)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(page_w/2, 0.35*cm, "COTIZA POR WHATSAPP")
    c.setFillColor(GOLD)
    c.setFont("Helvetica", 7)
    c.drawRightString(page_w - margin, 0.35*cm, f"PAGINA {page_n} DE {total_n}")


def draw_cover(logo_path, qr_path):
    """Portada de impacto con imagen de fondo real."""
    bg_img = MEDIA_DIR / 'proyecto-recepcion.jpg'
    if not os.path.exists(bg_img):
        bg_img = MEDIA_DIR / 'despues.jpg'
    
    if os.path.exists(bg_img):
        try:
            iw, ih = get_image_size(bg_img, page_w, page_h)
            scale = max(page_w/iw, page_h/ih)
            iw2, ih2 = iw * scale, ih * scale
            x = (page_w - iw2) / 2
            y = (page_h - ih2) / 2
            c.drawImage(str(bg_img), x, y, width=iw2, height=ih2)
        except:
            pass
    
    c.setFillColor(Color(0, 0, 0, alpha=0.75))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    for i in range(30):
        alpha = 0.4 - (i * 0.012)
        if alpha > 0:
            c.setFillColor(Color(0, 0, 0, alpha=alpha))
            c.rect(0, 0, page_w, 8*cm - i*0.2*cm, fill=1, stroke=0)
    
    fm = 1.5*cm
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.5)
    c.roundRect(fm, fm, page_w - 2*fm, page_h - 2*fm, 12, fill=0, stroke=1)
    c.setLineWidth(0.6)
    c.roundRect(fm + 0.35*cm, fm + 0.35*cm, page_w - 2*fm - 0.7*cm, page_h - 2*fm - 0.7*cm, 10, fill=0, stroke=1)
    
    if logo_path and os.path.exists(logo_path):
        logo_max = 6*cm
        iw, ih = get_image_size(logo_path, logo_max, logo_max)
        logo_x = (page_w - iw) / 2
        logo_y = page_h / 2 + 1.5*cm
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        r = max(iw, ih) / 2 + 0.4*cm
        c.circle(page_w/2, logo_y + ih/2, r, fill=0, stroke=1)
        c.drawImage(str(logo_path), logo_x, logo_y, width=iw, height=ih, mask='auto')
    
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(page_w/2, page_h/2 - 0.8*cm, "TRANSFORMA TU ESPACIO")
    
    c.setFillColor(LIGHT)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(page_w/2, page_h/2 - 1.8*cm, "MATERIALES PREMIUM PARA INTERIOR Y EXTERIOR")
    
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 11)
    c.drawCentredString(page_w/2, page_h/2 - 2.6*cm, "CATALOGO 2025  |  ADIS DISENO & REMODELACION")
    
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(page_w/2 - 3*cm, page_h/2 - 3.1*cm, page_w/2 + 3*cm, page_h/2 - 3.1*cm)
    
    if qr_path and os.path.exists(qr_path):
        qr_size = 2.8*cm
        qr_x = page_w - margin - qr_size
        qr_y = margin + 0.5*cm
        c.setFillColor(DARK)
        c.roundRect(qr_x - 0.2*cm, qr_y - 0.2*cm, qr_size + 0.4*cm, qr_size + 0.9*cm, 6, fill=1, stroke=0)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.5)
        c.roundRect(qr_x - 0.2*cm, qr_y - 0.2*cm, qr_size + 0.4*cm, qr_size + 0.9*cm, 6, fill=0, stroke=1)
        c.drawImage(str(qr_path), qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(qr_x + qr_size/2, qr_y - 0.5*cm, "ESCANEA PARA COTIZAR")
    
    c.setFillColor(LIGHT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, margin + 2.2*cm, "CONTACTANOS")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(margin, margin + 1.6*cm, "WhatsApp: +52 631-192-8993")
    c.drawString(margin, margin + 1.1*cm, "Showroom: +52 631-120-4943")
    c.drawString(margin, margin + 0.6*cm, "adis.remodelacion@gmail.com")
    c.drawString(margin, margin + 0.1*cm, "Nogales, Sonora  |  Rio Rico, AZ")
    
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 9)
    badge_w = 5.5*cm
    badge_h = 0.6*cm
    badge_x = (page_w - badge_w) / 2
    badge_y = margin + 0.3*cm
    c.roundRect(badge_x, badge_y, badge_w, badge_h, 4, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.drawCentredString(page_w/2, badge_y + 0.18*cm, "SHOWROOM Y SERVICIO DE INSTALACION")


def draw_content_page(total_sections, categories):
    """Pagina de contenido / guia de uso."""
    draw_page_bg()
    
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(page_w/2, page_h - 3*cm, "CONTENIDO")
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(page_w/2 - 2.5*cm, page_h - 3.4*cm, page_w/2 + 2.5*cm, page_h - 3.4*cm)
    
    guide_y = page_h - 4.2*cm
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawCentredString(page_w/2, guide_y, "Como usar este catalogo:")
    
    steps = [
        "1. Explora las categorias y encuentra el producto ideal para tu proyecto",
        "2. Anota el codigo SKU del producto que te interesa",
        "3. Escribenos por WhatsApp con el SKU para una cotizacion inmediata",
        "4. Pregunta por nuestro servicio de instalacion profesional",
    ]
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 8.5)
    for i, step in enumerate(steps):
        c.drawString(margin + 0.5*cm, guide_y - 0.7*cm - i*0.5*cm, step)
    
    gar_y = guide_y - 3.2*cm
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, gar_y, "GARANTIAS POR MATERIAL")
    
    garantias = [
        ('PVC', '15 anos'), ('WPC', '15 anos'), ('SPC', '12 anos'),
        ('Revestimiento Flexible', '35 anos'), ('Deck Sintetico', '18-25 anos'),
        ('Panel 3D', '1 ano'), ('Vigas', '15 anos'),
        ('Zacate / Follaje', '5-12 anos'),
    ]
    
    col_w = (page_w - 2*margin) / 2
    for i, (mat, gar) in enumerate(garantias):
        col = i % 2
        row = i // 2
        x = margin + col * col_w
        y = gar_y - 0.6*cm - row * 0.55*cm
        c.setFillColor(GOLD)
        c.circle(x + 0.15*cm, y + 0.12*cm, 1.5, fill=1, stroke=0)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 8.5)
        c.drawString(x + 0.4*cm, y, f"{mat}: {gar}")
    
    note_y = gar_y - 3.0*cm
    c.setFillColor(DARK)
    c.roundRect(margin, note_y - 0.8*cm, page_w - 2*margin, 1.6*cm, 8, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.roundRect(margin, note_y - 0.8*cm, page_w - 2*margin, 1.6*cm, 8, fill=0, stroke=1)
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_w/2, note_y + 0.3*cm, "PREGUNTAS? ESCRIBENOS POR WHATSAPP")
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(page_w/2, note_y - 0.15*cm, "+52 631-192-8993  |  Respuesta en menos de 24 horas")


def draw_benefits_page():
    """Pagina de ventajas competitivas por material."""
    draw_page_bg()
    
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(page_w/2, page_h - 2.5*cm, "POR QUE ELEGIR NUESTROS MATERIALES?")
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(page_w/2 - 3.5*cm, page_h - 2.9*cm, page_w/2 + 3.5*cm, page_h - 2.9*cm)
    
    materials = [
        ('PVC', VENTAJAS['PVC'][:4]),
        ('WPC', VENTAJAS['WPC'][:4]),
        ('SPC', VENTAJAS['SPC'][:4]),
        ('DECK', VENTAJAS['Deck'][:4]),
    ]
    
    card_w = (page_w - 2*margin - 0.6*cm) / 2
    card_h = 3.3*cm
    start_y = page_h - 3.5*cm
    
    for i, (mat_name, benefits) in enumerate(materials):
        col = i % 2
        row = i // 2
        x = margin + col * (card_w + 0.6*cm)
        y = start_y - row * (card_h + 0.5*cm)
        
        c.setFillColor(DARK)
        c.roundRect(x, y - card_h, card_w, card_h, 8, fill=1, stroke=0)
        c.setStrokeColor(Color(197/255, 160/255, 89/255, alpha=0.4))
        c.setLineWidth(1)
        c.roundRect(x, y - card_h, card_w, card_h, 8, fill=0, stroke=1)
        
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 0.3*cm, y - 0.4*cm, mat_name)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.5)
        c.line(x + 0.3*cm, y - 0.55*cm, x + card_w - 0.3*cm, y - 0.55*cm)
        
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 8)
        for j, (title, desc) in enumerate(benefits):
            by = y - 0.9*cm - j * 0.55*cm
            c.setFillColor(GOLD)
            c.drawString(x + 0.3*cm, by, "+")
            c.setFillColor(LIGHT)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(x + 0.6*cm, by, title)
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 7)
            c.drawString(x + 0.6*cm, by - 0.22*cm, desc[:50])


def draw_process_page():
    """Pagina de proceso de compra."""
    draw_page_bg()
    
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(page_w/2, page_h - 2.5*cm, "COMO COMPRAR?")
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(page_w/2 - 2.5*cm, page_h - 2.9*cm, page_w/2 + 2.5*cm, page_h - 2.9*cm)
    
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawCentredString(page_w/2, page_h - 3.4*cm, "4 pasos sencillos para transformar tu espacio")
    
    steps = [
        ('1', 'ELIGE', 'Explora el catalogo y selecciona tus productos. Anota el codigo SKU.'),
        ('2', 'CONTACTANOS', 'Escribenos por WhatsApp con los SKU de los productos que te interesan.'),
        ('3', 'RECIBE COTIZACION', 'Te enviamos tu cotizacion detallada en menos de 24 horas.'),
        ('4', 'INSTALACION', 'Te entregamos el material o lo instalamos con nuestro equipo profesional.'),
    ]
    
    step_h = 2.2*cm
    start_y = page_h - 4.2*cm
    
    for i, (num, title, desc) in enumerate(steps):
        y = start_y - i * (step_h + 0.4*cm)
        
        c.setFillColor(DARK)
        c.roundRect(margin, y - step_h, page_w - 2*margin, step_h, 8, fill=1, stroke=0)
        c.setStrokeColor(Color(197/255, 160/255, 89/255, alpha=0.3))
        c.roundRect(margin, y - step_h, page_w - 2*margin, step_h, 8, fill=0, stroke=1)
        
        c.setFillColor(GOLD)
        cx = margin + 1.0*cm
        cy = y - step_h/2
        c.circle(cx, cy, 0.7*cm, fill=1, stroke=0)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(cx, cy - 0.18*cm, num)
        
        c.setFillColor(GOLD_LIGHT)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin + 2.0*cm, y - 0.7*cm, title)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 9)
        c.drawString(margin + 2.0*cm, y - 1.2*cm, desc)
    
    cta_y = start_y - 4 * (step_h + 0.4*cm) - 0.3*cm
    c.setFillColor(WHATSAPP)
    c.roundRect(margin + 1*cm, cta_y - 0.9*cm, page_w - 2*margin - 2*cm, 0.9*cm, 6, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(page_w/2, cta_y - 0.55*cm, "COTIZA AHORA POR WHATSAPP: +52 631-192-8993")


def draw_section_intro(cat_name, section_name, section_path, section_products, page_n, total_n):
    """Pagina intro de seccion con specs, ventajas y foto de ambiente."""
    draw_page_bg()
    draw_header(f"{cat_name}  |  {section_name}")
    
    content_top = page_h - 1.6*cm
    
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(page_w/2, content_top - 0.8*cm, section_name.upper())
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(page_w/2 - 2.5*cm, content_top - 1.15*cm, page_w/2 + 2.5*cm, content_top - 1.15*cm)
    
    col_w = (page_w - 2*margin - 0.6*cm) / 2
    left_x = margin
    right_x = margin + col_w + 0.6*cm
    
    specs = SPECS_DATA.get(section_name, {})
    if specs:
        table_y = content_top - 1.6*cm
        row_h = 0.52*cm
        table_w = col_w
        
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left_x, table_y + 0.15*cm, "ESPECIFICACIONES TECNICAS")
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.5)
        c.line(left_x, table_y - 0.05*cm, left_x + table_w, table_y - 0.05*cm)
        
        for i, (label, value) in enumerate(specs.items()):
            y = table_y - 0.35*cm - i * row_h
            bg = GRAY if i % 2 == 0 else DARK
            c.setFillColor(bg)
            c.rect(left_x, y - row_h + 0.15*cm, table_w, row_h, fill=1, stroke=0)
            c.setStrokeColor(Color(197/255, 160/255, 89/255, alpha=0.2))
            c.setLineWidth(0.3)
            c.rect(left_x, y - row_h + 0.15*cm, table_w, row_h, fill=0, stroke=1)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(left_x + 0.2*cm, y - 0.08*cm, label)
            c.setFillColor(LIGHT)
            c.setFont("Helvetica", 7.5)
            val = str(value)[:45]
            c.drawString(left_x + 3.2*cm, y - 0.08*cm, val)
    
    ventajas = get_ventajas(section_name)
    vent_y = content_top - 1.6*cm - (len(specs) * 0.52*cm) - 0.8*cm if specs else content_top - 1.8*cm
    
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left_x, vent_y + 0.15*cm, "VENTAJAS")
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(left_x, vent_y - 0.05*cm, left_x + col_w, vent_y - 0.05*cm)
    
    for i, (title, desc) in enumerate(ventajas[:4]):
        y = vent_y - 0.35*cm - i * 0.48*cm
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(left_x + 0.2*cm, y, "+")
        c.setFillColor(LIGHT)
        c.drawString(left_x + 0.5*cm, y, title)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        c.drawString(left_x + 0.5*cm, y - 0.2*cm, desc[:50])
    
    amb_img = get_ambient_image(section_name)
    if amb_img and os.path.exists(amb_img):
        img_max_w = col_w
        img_max_h = 6*cm
        iw, ih = get_image_size(amb_img, img_max_w, img_max_h)
        img_x = right_x + (col_w - iw) / 2
        img_y = content_top - 0.5*cm - ih
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.roundRect(img_x - 0.2*cm, img_y - 0.2*cm, iw + 0.4*cm, ih + 0.4*cm, 8, fill=0, stroke=1)
        c.drawImage(str(amb_img), img_x, img_y, width=iw, height=ih, mask='auto')
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        c.drawCentredString(right_x + col_w/2, img_y - 0.5*cm, "Aplicacion real del producto")
    
    cta_y = margin + 0.8*cm
    
    cta_w = 6.5*cm
    cta_h = 0.65*cm
    c.setFillColor(WHATSAPP)
    c.roundRect(margin, cta_y, cta_w, cta_h, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(margin + cta_w/2, cta_y + 0.2*cm, "COTIZA POR WHATSAPP")
    
    c.setFillColor(GOLD)
    c.roundRect(margin + cta_w + 0.4*cm, cta_y, cta_w, cta_h, 4, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(margin + cta_w + 0.4*cm + cta_w/2, cta_y + 0.2*cm, "PREGUNTA POR INSTALACION")
    
    c.setFillColor(DARK)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.roundRect(margin + 2*cta_w + 0.8*cm, cta_y, cta_w, cta_h, 4, fill=1, stroke=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(margin + 2*cta_w + 0.8*cm + cta_w/2, cta_y + 0.2*cm, "SOLICITA MUESTRAS")
    
    draw_footer(page_n, total_n)
    next_page()


def draw_product_pages(cat_name, section_name, section_path, section_products, page_n_start, total_n):
    """Paginas de productos en grid 2x3 con SKUs."""
    content_top = page_h - 1.6*cm
    content_bottom = 1.2*cm
    content_h = content_top - content_bottom
    
    cell_w = (page_w - 2*margin) / COLS
    cell_h = content_h / ROWS
    
    num_pages = (len(section_products) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    pages_drawn = 0
    
    for page_idx in range(num_pages):
        draw_page_bg()
        draw_header(f"{cat_name}  |  {section_name}")
        
        start_idx = page_idx * PRODUCTS_PER_PAGE
        end_idx = min(start_idx + PRODUCTS_PER_PAGE, len(section_products))
        page_prods = section_products[start_idx:end_idx]
        
        for i, prod_file in enumerate(page_prods):
            col = i % COLS
            row = i // COLS
            x = margin + col * cell_w
            y = content_top - (row + 1) * cell_h
            
            pad = 0.25*cm
            cw = cell_w - pad*2
            ch = cell_h - pad*2
            
            c.setFillColor(DARK)
            c.roundRect(x + pad, y + pad, cw, ch, 8, fill=1, stroke=0)
            c.setStrokeColor(Color(197/255, 160/255, 89/255, alpha=0.35))
            c.setLineWidth(1)
            c.roundRect(x + pad, y + pad, cw, ch, 8, fill=0, stroke=1)
            
            prod_idx = start_idx + i + 1
            sku = get_sku(section_name, prod_idx)
            c.setFillColor(Color(197/255, 160/255, 89/255, alpha=0.25))
            c.roundRect(x + pad + cw - 2.2*cm, y + pad + ch - 0.5*cm, 2.0*cm, 0.38*cm, 3, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x + pad + cw - 1.1*cm, y + pad + ch - 0.38*cm, sku)
            
            img_path = section_path / prod_file
            img_max_w = cw - 0.6*cm
            img_max_h = ch - 1.4*cm
            
            if os.path.exists(img_path):
                iw, ih = get_image_size(img_path, img_max_w, img_max_h)
                img_x = x + (cell_w - iw) / 2
                img_y = y + pad + 0.7*cm
                c.drawImage(str(img_path), img_x, img_y, width=iw, height=ih, mask='auto')
            
            prod_name = clean_product_name(prod_file)
            c.setFillColor(GOLD_LIGHT)
            c.setFont("Helvetica-Bold", 8.5)
            if len(prod_name) > 30:
                prod_name = prod_name[:28] + "..."
            c.drawCentredString(x + cell_w/2, y + pad + 0.25*cm, prod_name)
        
        btn_w = 2.8*cm
        btn_h = 0.6*cm
        btn_x = margin
        btn_y = 0.35*cm
        c.setFillColor(GOLD)
        c.roundRect(btn_x, btn_y, btn_w, btn_h, 4, fill=1, stroke=0)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(btn_x + btn_w/2, btn_y + 0.18*cm, "<- INDICE")
        c.linkAbsolute("", "indice", (btn_x, btn_y, btn_x+btn_w, btn_y+btn_h))
        
        draw_footer(page_n_start + pages_drawn, total_n)
        next_page()
        pages_drawn += 1
    
    return pages_drawn


def draw_final_page(qr_path):
    """Pagina final de contacto y cierre."""
    draw_page_bg()
    
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        logo_max = 5*cm
        iw, ih = get_image_size(LOGO_PATH, logo_max, logo_max)
        logo_x = (page_w - iw) / 2
        logo_y = page_h - 7*cm
        c.drawImage(str(LOGO_PATH), logo_x, logo_y, width=iw, height=ih, mask='auto')
    
    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(page_w/2, page_h - 8.5*cm, "GRACIAS POR PREFERIRNOS")
    
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(page_w/2 - 3*cm, page_h - 8.9*cm, page_w/2 + 3*cm, page_h - 8.9*cm)
    
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_w/2, page_h - 9.6*cm, "Estamos listos para transformar tu espacio")
    c.drawCentredString(page_w/2, page_h - 10.0*cm, "con los mejores materiales del mercado.")
    
    box_y = page_h - 12*cm
    c.setFillColor(DARK)
    c.roundRect(margin + 1*cm, box_y - 3.5*cm, page_w - 2*margin - 2*cm, 3.8*cm, 10, fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.roundRect(margin + 1*cm, box_y - 3.5*cm, page_w - 2*margin - 2*cm, 3.8*cm, 10, fill=0, stroke=1)
    
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(page_w/2, box_y - 0.4*cm, "CONTACTANOS")
    
    contact_lines = [
        "WhatsApp: +52 631-192-8993",
        "Showroom: +52 631-120-4943",
        "Email: adis.remodelacion@gmail.com",
        "Ubicacion: Nogales, Sonora | Rio Rico, AZ",
        "Facebook: ADIS Diseno & Remodelacion",
    ]
    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 9)
    for i, line in enumerate(contact_lines):
        c.drawCentredString(page_w/2, box_y - 1.0*cm - i*0.45*cm, line)
    
    if qr_path and os.path.exists(qr_path):
        qr_size = 3.5*cm
        qr_x = (page_w - qr_size) / 2
        qr_y = box_y - 5.2*cm
        c.setFillColor(DARK)
        c.roundRect(qr_x - 0.3*cm, qr_y - 0.3*cm, qr_size + 0.6*cm, qr_size + 1.0*cm, 8, fill=1, stroke=0)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.roundRect(qr_x - 0.3*cm, qr_y - 0.3*cm, qr_size + 0.6*cm, qr_size + 1.0*cm, 8, fill=0, stroke=1)
        c.drawImage(str(qr_path), qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(page_w/2, qr_y - 0.55*cm, "ESCANEA PARA COTIZAR POR WHATSAPP")
    
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(page_w/2, margin + 0.3*cm, "Todos los precios incluyen IVA | Envios disponibles a todo Mexico | Garantia de fabricante")


# ========== GENERACION PRINCIPAL ==========
print("=" * 50)
print("GENERANDO CATALOGO PDF PREMIUM ADIS")
print("=" * 50)

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    logo_prepared = tmpdir / 'logo_prepared.png'
    qr_path = tmpdir / 'qr_whatsapp.png'
    
    print("\n[1/5] Preparando logo...")
    prepare_logo(logo_prepared)
    
    print("[2/5] Generando QR de WhatsApp...")
    generate_qr(qr_path, WHATSAPP_URL, size=250)
    
    print("[3/5] Escaneando catalogo...")
    categories = scan_catalog()
    for cat in categories:
        total = len(cat['direct_products'])
        for sub in cat['subcategories']:
            total += len(sub['products'])
        cat['total_products'] = total
    
    all_sections = []
    for cat_idx, cat in enumerate(categories):
        for sub in cat['subcategories']:
            if sub['products']:
                all_sections.append({
                    'cat_idx': cat_idx,
                    'cat_name': cat['name'],
                    'sub_name': sub['name'],
                    'products': sub['products'],
                    'path': sub['path'],
                })
        if cat['direct_products']:
            all_sections.append({
                'cat_idx': cat_idx,
                'cat_name': cat['name'],
                'sub_name': cat['name'],
                'products': cat['direct_products'],
                'path': cat['path'],
            })
    
    total_pages = 1
    total_pages += 1
    total_pages += 1
    total_pages += 1
    for sec in all_sections:
        total_pages += 1
        total_pages += (len(sec['products']) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
    total_pages += 1
    
    print(f"       Categorias: {len(categories)}")
    print(f"       Secciones: {len(all_sections)}")
    print(f"       Paginas estimadas: {total_pages}")
    
    print("\n[4/5] Generando paginas...")
    print("       -> Portada de impacto")
    draw_cover(str(logo_prepared) if logo_prepared.exists() else None,
               str(qr_path) if qr_path.exists() else None)
    next_page()
    
    print("       -> Contenido / Guia")
    draw_content_page(len(all_sections), categories)
    c.bookmarkPage('indice')
    c.addOutlineEntry('INDICE', 'indice', level=0)
    next_page()
    
    print("       -> Ventajas competitivas")
    draw_benefits_page()
    next_page()
    
    print("       -> Proceso de compra")
    draw_process_page()
    next_page()
    
    section_idx = 0
    for sec in all_sections:
        dest = f"sec_{section_idx}"
        print(f"       -> {sec['cat_name']} | {sec['sub_name']} ({len(sec['products'])} productos)")
        
        draw_section_intro(sec['cat_name'], sec['sub_name'], sec['path'],
                          sec['products'], page_num + 1, total_pages)
        c.bookmarkPage(dest)
        c.addOutlineEntry(sec['cat_name'], dest, level=0)
        
        pages_drawn = draw_product_pages(sec['cat_name'], sec['sub_name'],
                                         sec['path'], sec['products'],
                                         page_num + 1, total_pages)
        
        section_idx += 1
    
    print("       -> Pagina de cierre")
    draw_final_page(str(qr_path) if qr_path.exists() else None)
    next_page()
    
    print("\n[5/5] Guardando PDF...")
    c.save()

print(f"\n{'='*50}")
print(f"PDF GENERADO EXITOSAMENTE")
print(f"{'='*50}")
print(f"Archivo: {OUTPUT_PDF}")
print(f"Total paginas: {page_num}")
print(f"\nCategorias incluidas:")
for cat in categories:
    print(f"  | {cat['name']}: {cat['total_products']} productos")
print(f"\nAbre el PDF y verifica que el logo aparezca correctamente.")
