# -*- coding: utf-8 -*-
"""
Generador de catálogos individuales por categoría ADIS 2025
Crea un HTML por cada categoría en catalogos/html/
Mismo diseño premium que catalogo_premium.html
"""

import os, re, shutil, json, sys
from pathlib import Path
from urllib.parse import quote
from PIL import Image
import qrcode

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR    = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')
PRODUCTS_JSON = BASE_DIR / 'products.json'
MEDIA_DIR   = BASE_DIR / 'media'
LOGO_PATH   = BASE_DIR / 'logo nuevo.jpeg'
QR_PATH     = BASE_DIR / 'codigo QR.jpeg'
OUTPUT_DIR  = BASE_DIR / 'catalogos' / 'html'
IMG_DIR     = BASE_DIR / 'catalogos' / 'html' / 'catalogo_img'

if not PRODUCTS_JSON.exists():
    raise FileNotFoundError(f'No se encontró {PRODUCTS_JSON}.')

# ========== DATOS ENRIQUECIDOS ==========
SPECS = {
    'Placas PVC': {
        'Material':'PVC', 'Dimensiones':'2440×1220mm', 'Espesor':'3-5mm',
        'Presentación':'2.98m²/pz', 'Uso':'Interior',
        'Resistencia al agua':'100%', 'Resistencia UV':'Moderada',
        'Mantenimiento':'Limpieza húmeda', 'Instalación':'Adhesivo / Clavos'
    },
    'Lambrin WPC': {
        'Material':'WPC', 'Dimensiones':'2900×160mm', 'Espesor':'12-24mm',
        'Presentación':'Consultar', 'Uso':'Int/Ext',
        'Resistencia al agua':'100%', 'Resistencia UV':'Alta',
        'Mantenimiento':'Limpieza seca', 'Instalación':'Click / Tornillos'
    },
    'Revestimiento Flexible': {
        'Material':'Flexible', 'Dimensiones':'900×600mm', 'Espesor':'2-4mm',
        'Presentación':'0.54m²/pz', 'Uso':'Int/Ext',
        'Resistencia al agua':'100%', 'Resistencia UV':'Alta',
        'Mantenimiento':'Limpieza húmeda', 'Instalación':'Adhesivo'
    },
    'Plafon PVC': {
        'Material':'PVC', 'Dimensiones':'2900×250mm', 'Espesor':'8-9mm',
        'Presentación':'Consultar', 'Uso':'Interior',
        'Resistencia al agua':'100%', 'Resistencia UV':'Baja',
        'Mantenimiento':'Limpieza húmeda', 'Instalación':'Clip / Adhesivo'
    },
    'Paneles tridimensionales': {
        'Material':'PVC/Compuesto', 'Dimensiones':'500×500mm', 'Espesor':'1-2mm',
        'Presentación':'0.25m²/pz', 'Uso':'Res/Com',
        'Resistencia al agua':'Moderada', 'Resistencia UV':'Baja',
        'Mantenimiento':'Limpieza seca', 'Instalación':'Adhesivo'
    },
    'Vigas PVC': {
        'Material':'WPC/PVC', 'Dimensiones':'Consultar', 'Espesor':'Consultar',
        'Presentación':'1pz/caja', 'Uso':'Int/Ext',
        'Resistencia al agua':'100%', 'Resistencia UV':'Alta',
        'Mantenimiento':'Limpieza seca', 'Instalación':'Tornillos / Soporte'
    },
    'Pisos': {
        'Material':'Varios', 'Dimensiones':'Consultar', 'Espesor':'4-8mm',
        'Presentación':'Consultar', 'Uso':'Res/Com',
        'Resistencia al agua':'Variable', 'Resistencia UV':'Moderada',
        'Mantenimiento':'Limpieza húmeda', 'Instalación':'Click / Pegado'
    },
    'Zacate': {
        'Material':'Polietileno', 'Dimensiones':'Consultar', 'Espesor':'Consultar',
        'Presentación':'Por m²', 'Uso':'Exterior',
        'Resistencia al agua':'Drenaje', 'Resistencia UV':'Alta',
        'Mantenimiento':'Aspirado / Agua', 'Instalación':'Rollo'
    },
    'Cladding': {
        'Material':'PU/Poliuretano', 'Dimensiones':'Consultar', 'Espesor':'Consultar',
        'Presentación':'Consultar', 'Uso':'Int/Ext',
        'Resistencia al agua':'Alta', 'Resistencia UV':'Alta',
        'Mantenimiento':'Limpieza húmeda', 'Instalación':'Adhesivo / Tornillos'
    },
}

BENEFITS = {
    'Placas PVC': [('Impermeable','Ideal cocinas y baños'),('Antibacteriano','Higiénico, fácil limpieza'),('Resistente','No se deforma'),('Duradero','15+ años')],
    'Lambrin WPC': [('Natural','Textura real de madera'),('Indestructible','No se pudre'),('Sin mantenimiento','Sin barniz'),('Ecológico','Madera reciclada')],
    'Revestimiento Flexible': [('Flexible','Cualquier superficie'),('Int/Ext','Versátil'),('Ligero','No sobrecarga'),('Natural','Aspecto piedra real')],
    'Plafon PVC': [('Impermeable','Humedad cero'),('Fácil limpieza','Mantenimiento mínimo'),('Decorativo','Múltiples acabados'),('Duradero','15 años')],
    'Paneles tridimensionales': [('Impacto visual','Diseño arquitectónico'),('Fácil','Instalación sencilla'),('Pintable','Personalizable'),('Acústico','Insonorización')],
    'Vigas PVC': [('Realista','Imita madera'),('Impermeable','Resiste humedad'),('Ligero','Fácil instalar'),('Int/Ext','Ambos ambientes')],
    'Pisos': [('Variedad','Múltiples materiales'),('Resistente','Alto tráfico'),('Fácil','Instalación rápida'),('Garantía','Hasta 25 años')],
    'Zacate': [('Siempre verde','Sin riego'),('Anti-UV','No se decolora'),('Drenaje','No encharca'),('Pet friendly','Seguro')],
    'Cladding': [('Piedra real','Natural'),('Ligero','Fácil instalar'),('Versátil','Int/Ext'),('Térmico','Aislante')],
}

SABIAS_QUE = {
    'Placas PVC':    {'icono':'🧼', 'texto':'Las placas PVC previenen la acumulación de humedad y son extremadamente fáciles de limpiar.'},
    'Lambrin WPC':   {'icono':'🌲', 'texto':'El WPC combina fibras de madera y polímeros para ofrecer la belleza natural de la madera sin mantenimiento.'},
    'Revestimiento Flexible': {'icono':'🪨', 'texto':'Los revestimientos flexibles se adaptan a superficies curvas sin perder su apariencia de piedra natural.'},
    'Plafon PVC':    {'icono':'🧼', 'texto':'Las placas PVC previenen la acumulación de humedad y son extremadamente fáciles de limpiar.'},
    'Paneles tridimensionales': {'icono':'🔇', 'texto':'Los paneles 3D no solo decoran: también mejoran la insonorización de tus espacios.'},
    'Vigas PVC':     {'icono':'🏠', 'texto':'El cladding mejora la estética de fachadas y protege los muros exteriores del clima.'},
    'Pisos':         {'icono':'💧', 'texto':'Los pisos SPC son 100% resistentes al agua, ideales para cocinas y baños.'},
    'Zacate':        {'icono':'☀️', 'texto':'El pasto sintético premium incorpora protección UV para conservar su color durante años.'},
    'Cladding':      {'icono':'🏠', 'texto':'El cladding mejora la estética de fachadas y protege los muros exteriores del clima.'},
}

AMBIENT = {
    'Placas PVC': MEDIA_DIR/'pvc-real-01.jpeg',
    'Lambrin WPC': BASE_DIR / 'img' / '2-lambrin-wpc' / '23-desigual' / 'Bahia.jpg',
    'Revestimiento Flexible': BASE_DIR / 'img' / '3-revestimiento-flexible' / 'CONCRETO Aparente.jpg',
    'Plafon PVC': BASE_DIR / 'img' / '4-plafon-pvc' / 'York.jpg',
    'Paneles tridimensionales': BASE_DIR / 'img' / '5-paneles-tridimensionales' / '51-blanco' / 'Austin.jpg',
    'Vigas PVC': BASE_DIR / 'img' / '6-vigas-pvc' / '61-interior' / 'BAHIA 1.jpg',
    'Pisos': BASE_DIR / 'img' / '7-pisos' / '73-spc' / 'CONCRETE.jpg',
    'Zacate': BASE_DIR / 'img' / '8-zacate' / '81-follaje-sintetico' / 'AMAZONAS-A.jpg',
    'Cladding': BASE_DIR / 'img' / '9-cladding' / 'Esquiner 35X45X2900MM.jpg',
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

PROYECTOS = [
    ('Antes', MEDIA_DIR/'antes.jpg'), ('Despues', MEDIA_DIR/'despues.jpg'),
    ('Proyecto_1', MEDIA_DIR/'proyecto-01.jpeg'), ('Proyecto_2', MEDIA_DIR/'proyecto-02.jpeg'),
    ('Proyecto_3', MEDIA_DIR/'proyecto-03.jpeg'), ('Proyecto_4', MEDIA_DIR/'proyecto-04.jpeg'),
    ('Instalacion', MEDIA_DIR/'proyecto-05.jpeg'), ('Recepcion', MEDIA_DIR/'proyecto-recepcion.jpg'),
]

COMPARATIVA_PISOS = [
    ['Característica','Laminado','SPC','WPC'],
    ['Resistencia al agua','Moderada','<span class="ok">✓ 100%</span>','<span class="ok">✓ Impermeable</span>'],
    ['Uso recomendado','Residencial','Res / Comercial','Exterior / Residencial'],
    ['Instalación','Sistema click','Sistema click','Click / Atornillado'],
    ['Resistencia impacto','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span><span class="bar empty"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span>'],
    ['Confort acústico','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span><span class="bar empty"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span><span class="bar empty"></span>'],
    ['Garantía','10 años','12 años','15 años'],
]

# ========== UTILIDADES ==========
def rel_path(p):
    return './catalogo_img/' + quote(str(p.name), safe='')

def slugify(name):
    import unicodedata
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.lower().replace(' ', '-').replace('_', '-')[:50]

def clean_product(name):
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
    return ' '.join(result)

def get_sku(cat_name, prod_name, idx):
    cc = re.sub(r'[^a-zA-Z]', '', cat_name)[:3].upper()
    ps = re.sub(r'[^a-zA-Z0-9]', '', clean_product(prod_name))[:5].upper()
    return f"{cc}-{ps}-{idx:02d}"

def is_accesorio(name):
    n = name.lower()
    palabras = ['angulo','perfil','esquinero','soporte','cople','accesorio','tapa','union','clip','remate','esquina']
    return any(p in n for p in palabras)

def prepare_cat_products(subs):
    """Devuelve productos ordenados: normales primero, accesorios unicos al final."""
    normales = []
    accs = []
    for sub_name, sub_prods in subs.items():
        for p in sub_prods:
            p2 = {**p, 'sub_name': sub_name}
            if is_accesorio(p['name']):
                accs.append(p2)
            else:
                normales.append(p2)
    vistos = set()
    accs_unique = []
    for p in accs:
        key = clean_product(p['name']).lower()
        if key not in vistos:
            vistos.add(key)
            accs_unique.append(p)
    return normales + accs_unique

def optimize_and_copy(src, dst, max_dim=500, quality=72, bg=(8,8,8)):
    try:
        src = Path(src)
        if not src.exists():
            print(f'  [AVISO] No existe: {src}')
            return False
        with Image.open(src) as im:
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            if im.mode in ('RGBA','P'):
                background = Image.new('RGB', im.size, bg)
                if im.mode == 'P': im = im.convert('RGBA')
                background.paste(im, mask=im.split()[-1]); im = background
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            dst = Path(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        print(f'  Error: {src} -> {e}')
        return False

def gen_qr(path, text, size=180):
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
        qr.add_data(text); qr.make(fit=True)
        img = qr.make_image(fill_color="#C9A84C", back_color="#080808")
        img = img.resize((size,size), Image.Resampling.LANCZOS)
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path); return True
    except Exception as e:
        print(f'QR error: {e}'); return False

def load_products():
    with open(PRODUCTS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    prods = data.get('products', [])
    from collections import OrderedDict
    cats = OrderedDict()
    for p in prods:
        c = p.get('category','')
        s = p.get('subcategory') or 'General'
        if c not in cats:
            cats[c] = OrderedDict()
        if s not in cats[c]:
            cats[c][s] = []
        cats[c][s].append(p)
    return cats


# ========== HTML POR CATEGORÍA ==========
def build_category_html(cat_name, subs, prods, img_dir, cat_index):
    n_total = len(prods)
    logo_opt = img_dir / "logo.jpg"
    qr_opt = img_dir / "qr.jpg"
    logo_url = rel_path(logo_opt)
    qr_url = rel_path(qr_opt)
    amb_opt = img_dir / f"amb_{cat_index}.jpg"
    amb_img = rel_path(amb_opt) if amb_opt.exists() else ''
    cat_qr = img_dir / f"qr_cat_{cat_index}.png"
    cat_qr_url = rel_path(cat_qr) if cat_qr.exists() else qr_url

    spec = SPECS.get(cat_name, {
        'Material':'Consultar','Dimensiones':'Consultar','Espesor':'Consultar',
        'Presentación':'Consultar','Uso':'Consultar',
        'Resistencia al agua':'Consultar','Resistencia UV':'Consultar',
        'Mantenimiento':'Consultar','Instalación':'Consultar'
    })
    bens = BENEFITS.get(cat_name, [('Calidad','Premium'),('Duradero','Larga vida'),('Fácil','Instalación sencilla'),('Elegante','Diseño moderno')])
    sq = SABIAS_QUE.get(cat_name, {'icono':'✨','texto':'Consulta nuestros productos premium en adis-diseño.com'})

    css = """
    <style>
        @page { size: A4 portrait; margin: 0; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; background: #080808; color: #F0F0F0; font-size: 10pt; }

        .page { width: 210mm; min-height: 297mm; padding: 14mm 18mm; position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; background: #080808; }
        .page:last-child { page-break-after: auto; }

        h1 { font-family: Georgia, 'Times New Roman', serif; font-size: 32pt; font-weight: 700; color: #F0F0F0; line-height: 1.1; }
        h2 { font-family: Georgia, 'Times New Roman', serif; font-size: 22pt; font-weight: 700; line-height: 1.2; color: #E5C97A; }
        h3 { font-size: 11pt; font-weight: 700; color: #F0F0F0; text-transform: uppercase; letter-spacing: 1px; }
        .muted { color: #888; font-size: 9pt; }
        .gold { color: #C9A84C; }

        .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #2A2A2A; padding-bottom: 6px; margin-bottom: 10px; position: relative; }
        .header img { height: 22px; }
        .header span { font-size: 8pt; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .footer { margin-top: auto; border-top: 1px solid #2A2A2A; padding-top: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 7.5pt; color: #777; }
        .back-btn { background: rgba(26,26,26,0.9); border: 1px solid #444; color: #C9A84C; padding: 3px 12px; border-radius: 3px; font-size: 7.5pt; font-weight: 700; text-decoration: none; position: absolute; left: 50%; transform: translateX(-50%); top: 0; }

        /* Portada */
        .cover { position: relative; justify-content: center; align-items: center; text-align: center; padding: 0; background: #080808; overflow: hidden; }
        .cover::before { content:''; position: absolute; inset: 0; background: radial-gradient(circle at 30% 30%, rgba(201,168,76,0.12) 0%, transparent 40%); z-index: 1; }
        .cover-frame { position: absolute; inset: 12mm; border: 1.5px solid #C9A84C; border-radius: 12px; pointer-events: none; z-index: 2; }
        .cover-frame2 { position: absolute; inset: 15mm; border: 0.5px solid #8A7340; border-radius: 10px; pointer-events: none; z-index: 2; }
        .cover-content { position: relative; z-index: 3; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 22mm; }
        .cover-content img { max-width: 115mm; max-height: 90mm; object-fit: contain; margin-bottom: 10mm; filter: drop-shadow(0 15px 40px rgba(0,0,0,0.6)); }
        .cover-content h1 { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 28pt; font-weight: 800; letter-spacing: 3px; margin-bottom: 4mm; color: #E5C97A; }
        .cover-content .sub { font-size: 11pt; color: #E5C97A; margin-bottom: 6mm; letter-spacing: 1px; }
        .cover-content .line { width: 55mm; height: 1.5px; background: linear-gradient(90deg, transparent, #C9A84C, transparent); margin-bottom: 6mm; }
        .cover-content .year { font-size: 9pt; color: #888; line-height: 1.6; }

        /* Separador */
        .separator { justify-content: center; align-items: center; text-align: center; background-size: cover; background-position: center; position: relative; }
        .separator::before { content:''; position: absolute; inset: 0; background: rgba(0,0,0,0.55); }
        .sep-content { position: relative; z-index: 2; flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .sep-content h1 { font-size: 52pt; letter-spacing: 5px; margin-bottom: 5mm; color: #F0F0F0; }
        .sep-content .line { width: 40mm; height: 1.5px; background: linear-gradient(90deg, transparent, #C9A84C, transparent); margin: 0 auto 4mm; }
        .sep-content p { font-size: 10pt; color: #BBB; }

        /* Intro */
        .cat-intro { display: flex; flex-direction: column; gap: 6px; }
        .cat-header { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1.5px solid #C9A84C; padding-bottom: 4px; margin-bottom: 2px; }
        .cat-header h1 { font-size: 26pt; color: #F0F0F0; }
        .cat-header .count { font-size: 10pt; color: #C9A84C; font-weight: 700; }
        .cat-desc { font-size: 9.5pt; color: #CCC; line-height: 1.4; max-width: 85%; }
        .cat-img { width: 100%; height: 42mm; object-fit: cover; border-radius: 4px; margin: 2px 0; border: 1px solid #222; }
        .benefits { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 2px; }
        .benefit { background: #181818; border-radius: 4px; padding: 4px 7px; border-left: 2px solid #C9A84C; }
        .benefit b { color: #C9A84C; font-size: 8pt; display: block; margin-bottom: 1px; }
        .benefit span { color: #888; font-size: 7.5pt; }
        .banner-sq { background: #121212; border: 1px solid #333; border-radius: 4px; padding: 5px 8px; margin-top: 4px; display: flex; align-items: center; gap: 8px; font-size: 8pt; color: #BBB; }
        .banner-sq .icon { font-size: 13pt; }
        .banner-sq b { color: #C9A84C; margin-right: 4px; }
        .qr-box { display: flex; align-items: center; gap: 8px; margin-top: 4px; padding: 5px 8px; background: #121212; border: 1px solid #333; border-radius: 4px; }
        .qr-box img { width: 18mm; height: 18mm; }
        .qr-box span { font-size: 7.5pt; color: #888; }

        .ficha-table { width: 100%; border-collapse: collapse; margin-top: 3px; }
        .ficha-table td { padding: 2px 5px; font-size: 7pt; border-bottom: 1px solid #222; }
        .ficha-table td:nth-child(odd) { color: #C9A84C; font-weight: 700; background: #121212; width: 18%; }
        .ficha-table td:nth-child(even) { color: #CCC; background: #181818; width: 32%; }
        .ficha-table tr:nth-child(even) td:nth-child(odd) { background: #0f0f0f; }
        .ficha-table tr:nth-child(even) td:nth-child(even) { background: #151515; }

        /* Productos */
        .prod-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; flex: 1; }
        .prod-card { background: #181818; border: 1px solid #222; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; page-break-inside: avoid; }
        .prod-card .img-wrap { width: 100%; height: 50mm; overflow: hidden; display: flex; align-items: center; justify-content: center; }
        .prod-card .img-wrap img { width: 100%; height: 100%; object-fit: cover; }
        .prod-card .info { padding: 5px 6px 6px; border-top: 1px solid #222; }
        .prod-card .name { font-size: 7.5pt; font-weight: 700; color: #F0F0F0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 1px; }
        .prod-card .sku { font-family: 'Courier New', monospace; font-size: 6.5pt; color: #C9A84C; font-weight: 700; }
        .prod-card .sub { font-size: 6.5pt; color: #666; margin-top: 1px; }

        /* Comparativa */
        .comp-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
        .comp-table th { background: #C9A84C; color: #080808; font-size: 8.5pt; font-weight: 700; padding: 6px 8px; text-align: center; border: 1px solid #333; }
        .comp-table td { background: #121212; color: #CCC; font-size: 8pt; padding: 5px 8px; text-align: center; border: 1px solid #222; }
        .comp-table tr:nth-child(even) td { background: #181818; }
        .comp-table .ok { color: #4CAF50; font-weight: 700; }
        .comp-table .bar { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #C9A84C; margin: 0 1px; }
        .comp-table .bar.empty { background: #333; }

        /* Final */
        .final { text-align: center; justify-content: center; align-items: center; }
        .final img.logo { max-width: 60mm; margin-bottom: 10mm; filter: drop-shadow(0 5px 15px rgba(0,0,0,0.4)); }
        .final h2 { margin-bottom: 4mm; }
        .final .contact-box { background: #121212; border: 1px solid #222; border-radius: 6px; padding: 10px 20px; margin: 8mm 0; max-width: 130mm; }
        .final .contact-box p { font-size: 9pt; color: #CCC; margin: 3px 0; }
        .final .qr-wrap { background: #fff; padding: 8px; border-radius: 6px; display: inline-block; margin-top: 6mm; }
        .final .qr-wrap img { width: 35mm; height: 35mm; display: block; }
        .final .qr-label { font-size: 8pt; color: #C9A84C; margin-top: 3mm; font-weight: 700; }
    </style>
    """

    body_parts = []
    page_counter = 1

    def footer(page_text):
        return f'<div class="footer"><span>ADIS Diseño & Remodelación</span><span>{page_text}</span><span>adis-diseño.com | +1 (520) 839-2877</span></div>'

    # Portada
    body_parts.append(f'''<div class="page cover">
        <div class="cover-frame"></div>
        <div class="cover-frame2"></div>
        <div class="cover-content">
            <img src="{logo_url}" alt="ADIS">
            <h1>CATÁLOGO<br>{cat_name.upper()}</h1>
            <div class="sub">Materiales premium para arquitectura e interiorismo</div>
            <div class="line"></div>
            <div class="year">CATÁLOGO 2025 &nbsp;|&nbsp; ADIS DISEÑO & REMODELACIÓN<br>Nogales, Sonora &nbsp;|&nbsp; Río Rico, AZ</div>
        </div>
    </div>''')
    page_counter += 1

    # Separador con ambiente
    if amb_img:
        body_parts.append(f'''<div class="page separator" style="background-image:url('{amb_img}');">
            <div class="sep-content">
                <h1>{cat_name.upper()}</h1>
                <div class="line"></div>
                <p>{n_total} productos &nbsp;|&nbsp; Ficha técnica incluida</p>
            </div>
            {footer(f'Página {page_counter}')}
        </div>''')
        page_counter += 1

    # Intro integrada
    intro_html = [f'<div class="page cat-intro">']
    intro_html.append('<div class="header"><img src="'+logo_url+'" alt="ADIS"><span>'+cat_name.upper()+'</span></div>')
    intro_html.append(f'<div class="cat-header"><h1>{cat_name.upper()}</h1><div class="count">{n_total} PRODUCTOS</div></div>')
    intro_html.append(f'<p class="cat-desc">{CAT_DESC.get(cat_name, cat_name + ". Soluciones decorativas premium de alta calidad.")}</p>')
    if amb_img:
        intro_html.append(f'<img src="{amb_img}" class="cat-img" alt="{cat_name}">')
    intro_html.append('<div class="benefits">')
    for btitle, bdesc in bens:
        intro_html.append(f'<div class="benefit"><b>{btitle}</b><span>{bdesc}</span></div>')
    intro_html.append('</div>')
    intro_html.append(f'<div class="banner-sq"><span class="icon">{sq["icono"]}</span><b>¿SABÍAS QUE?</b> {sq["texto"]}</div>')
    intro_html.append(f'<div class="qr-box"><img src="{cat_qr_url}" alt="QR"><span>Escanea para cotizar {cat_name} por WhatsApp</span></div>')
    intro_html.append(f'<div style="margin-top:4px;"><h3 style="font-size:9pt; color:#C9A84C; margin-bottom:2px;">FICHA TÉCNICA</h3><table class="ficha-table">')
    spec_items = list(spec.items())
    for i in range(0, len(spec_items), 2):
        k1, v1 = spec_items[i]
        if i+1 < len(spec_items):
            k2, v2 = spec_items[i+1]
            intro_html.append(f'<tr><td>{k1}</td><td>{v1}</td><td>{k2}</td><td>{v2}</td></tr>')
        else:
            intro_html.append(f'<tr><td>{k1}</td><td colspan="3">{v1}</td></tr>')
    intro_html.append('</table></div>')
    intro_html.append(footer(f'Página {page_counter}'))
    intro_html.append('</div>')
    body_parts.append('\n'.join(intro_html))
    page_counter += 1

    # Productos
    per_page = 9
    for pi in range(0, len(prods), per_page):
        group = prods[pi:pi+per_page]
        prod_html = ['<div class="page">']
        prod_html.append('<div class="header"><img src="'+logo_url+'" alt="ADIS"><span>'+cat_name.upper()+'</span></div>')
        prod_html.append('<div class="prod-grid">')
        for idx, prod in enumerate(group):
            opt_name = f"opt_{cat_index}_{pi + idx}.jpg"
            opt_path = img_dir / opt_name
            img_url = rel_path(opt_path) if opt_path.exists() else prod.get('thumb','')
            name = clean_product(prod['name'])
            sku = get_sku(cat_name, prod['name'], pi + idx + 1)
            sub_label = prod['sub_name'] if len(subs) > 1 else ''
            sub_label_html = f'<div class="sub">{sub_label}</div>' if sub_label else ''
            prod_html.append(f'''<div class="prod-card">
                <div class="img-wrap"><img src="{img_url}" alt="{name}"></div>
                <div class="info">
                    <div class="name" title="{name}">{name}</div>
                    <div class="sku">{sku}</div>
                    {sub_label_html}
                </div>
            </div>''')
        prod_html.append('</div>')
        prod_html.append(footer(f'Página {page_counter}'))
        prod_html.append('</div>')
        body_parts.append('\n'.join(prod_html))
        page_counter += 1

    # Comparativa Pisos
    if cat_name == 'Pisos':
        comp_html = ['<div class="page">']
        comp_html.append('<div class="header"><img src="'+logo_url+'" alt="ADIS"><span>COMPARATIVA</span></div>')
        comp_html.append('<div style="text-align:center; margin-bottom:8px;"><h2>COMPARATIVA DE PISOS</h2><p class="muted">Encuentra el piso ideal según tus necesidades</p></div>')
        comp_html.append('<table class="comp-table"><thead><tr><th>Característica</th><th>Laminado</th><th>SPC</th><th>WPC</th></tr></thead><tbody>')
        for row in COMPARATIVA_PISOS[1:]:
            comp_html.append('<tr><td style="text-align:left; font-weight:600;">'+row[0]+'</td><td>'+row[1]+'</td><td>'+row[2]+'</td><td>'+row[3]+'</td></tr>')
        comp_html.append('</tbody></table>')
        comp_html.append(footer(f'Página {page_counter}'))
        comp_html.append('</div>')
        body_parts.append('\n'.join(comp_html))
        page_counter += 1

    # Final
    final_html = ['<div class="page final">']
    final_html.append('<img src="'+logo_url+'" class="logo" alt="ADIS">')
    final_html.append('<h2>Gracias por preferirnos</h2>')
    final_html.append('<p style="color:#BBB; font-size:10pt; margin-bottom:8mm;">Estamos listos para transformar tu espacio</p>')
    final_html.append('<div class="contact-box">')
    final_html.append('<p><strong style="color:#C9A84C;">CONTACTO</strong></p>')
    final_html.append('<p>WhatsApp: +1 (520) 839-2877</p>')
    final_html.append('<p>Showroom: +52 631-120-4943</p>')
    final_html.append('<p>Email: adis.remodelacion@gmail.com</p>')
    final_html.append('<p>Web: adis-diseño.com</p>')
    final_html.append('<p>Nogales, Sonora | Río Rico, AZ</p>')
    final_html.append('</div>')
    final_html.append(f'<div class="qr-wrap"><img src="{qr_url}" alt="QR"></div>')
    final_html.append('<div class="qr-label">Escanea para visitarnos</div>')
    final_html.append(footer('Última página'))
    final_html.append('</div>')
    body_parts.append('\n'.join(final_html))

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Catálogo {cat_name} | ADIS 2025</title>
{css}
</head>
<body>
{''.join(body_parts)}
</body>
</html>'''

# ========== EJECUTAR ==========
print("Cargando products.json...")
cats = load_products()
print(f"Categorías: {len(cats)}")
print(f"Productos: {sum(sum(len(s) for s in cat.values()) for cat in cats.values())}")

# Preparar listas de productos ordenadas
cats_prepared = {cat_name: prepare_cat_products(subs) for cat_name, subs in cats.items()}

# Preparar carpeta de imágenes
if IMG_DIR.exists():
    shutil.rmtree(IMG_DIR)
IMG_DIR.mkdir(parents=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\nOptimizando imágenes...")
total_imgs = 0
for ci, (cat_name, subs) in enumerate(cats.items()):
    amb = AMBIENT.get(cat_name)
    if amb and amb.exists():
        optimize_and_copy(amb, IMG_DIR / f"amb_{ci}.jpg", max_dim=600, quality=70)
    for pi, p in enumerate(cats_prepared[cat_name]):
        src = BASE_DIR / p['thumb']
        optimize_and_copy(src, IMG_DIR / f"opt_{ci}_{pi}.jpg", max_dim=380, quality=60)
        total_imgs += 1
print(f"  {total_imgs} imágenes optimizadas")

# Logo, QR, proyectos
optimize_and_copy(LOGO_PATH, IMG_DIR / "logo.jpg", max_dim=600, quality=85)
optimize_and_copy(QR_PATH, IMG_DIR / "qr.jpg", max_dim=400, quality=85)
for label, pimg in PROYECTOS:
    if pimg.exists():
        optimize_and_copy(pimg, IMG_DIR / f"proj_{label}.jpg", max_dim=600, quality=75)

# QR por categoría
print("Generando QR por categoría...")
for ci, cat_name in enumerate(cats.keys()):
    msg = f"Hola ADIS, me interesa comprar {cat_name}, ¿me puedes dar más información?".replace(' ', '%20')
    url = f"https://wa.me/15208392877?text={msg}"
    gen_qr(IMG_DIR / f"qr_cat_{ci}.png", url, size=180)

# Generar HTML por categoría
print("\nGenerando catálogos individuales...")
for ci, (cat_name, subs) in enumerate(cats.items()):
    html = build_category_html(cat_name, subs, cats_prepared[cat_name], IMG_DIR, ci)
    filename = f"catalogo_{slugify(cat_name)}.html"
    out_path = OUTPUT_DIR / filename
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [OK] {filename} ({len(cats_prepared[cat_name])} productos)")

print(f"\nCatálogos guardados en: {OUTPUT_DIR}")
