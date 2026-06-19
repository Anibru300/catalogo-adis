# -*- coding: utf-8 -*-
import os
import sys
import re
import json
import shutil
import unicodedata
from pathlib import Path

# Forzar UTF-8 en stdout para evitar errores de codificación
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ========== CONFIGURACIÓN ==========
BASE_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')

CONTACTO = {
    'whatsapp': '15208392877',
    'whatsapp_msg': 'Hola ADIS, vi el catálogo y me interesa obtener información sobre sus productos.',
    'email': 'adis.remodelacion@gmail.com',
    'tel_mx': '+1 (520) 839-2877',
    'tel_usa': '+1 (520) 839-2877',
    'tel_showroom': '+52 631-120-4943',
    'ubicacion': 'Nogales, Sonora · Rio Rico, AZ',
    'direccion': 'C. Alfonso Acosta 16 Local 3, Col. 5 de Mayo, 84000 Heroica Nogales, Sonora',
    'maps_url': 'https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8',
    'horarios': 'Martes a domingo 10:00-19:00',
    'facebook': 'https://www.facebook.com/p/Adis-Dise%C3%B1o-Remodelaci%C3%B3n-61579849591594/'
}

# ========== CONFIGURACIÓN DEL SITIO ==========
# URL base del sitio. Cambia cuando conectes un dominio propio.
SITE_URL = 'https://adis-diseño.com/'

# ========== PRECIOS REFERENCIALES POR CATEGORÍA ==========
# Rangos de precios en MXN. Se usan en el chatbot como referencia.
PRICE_DATA = {
    'PLACAS PVC': {
        'unit': 'pieza',
        'range': '$850 - $1,400 MXN',
        'avg_m2': '$285 - $470 MXN/m²',
        'note': 'Depende del modelo y acabado (madera, mármol, espejo, textura)'
    },
    'LAMBRIN WPC': {
        'unit': 'caja',
        'range': '$1,200 - $2,100 MXN',
        'avg_m2': '$260 - $450 MXN/m²',
        'note': 'Interior más económico que exterior. Precio por caja (~2.8-3.1 m²)'
    },
    'REVESTIMIENTO FLEXIBLE': {
        'unit': 'pieza',
        'range': '$650 - $1,100 MXN',
        'avg_m2': '$320 - $540 MXN/m²',
        'note': 'Varía por diseño (concreto, piedra, madera)'
    },
    'PLAFÓN PVC LAMINADO WOOD STYLE': {
        'unit': 'pieza',
        'range': '$180 - $350 MXN',
        'avg_m2': '$150 - $290 MXN/m²',
        'note': 'Depende del diseño (laminado o ranurado)'
    },
    'PANELES TRIDIMENSIONALES 3D': {
        'unit': 'pieza',
        'range': '$280 - $550 MXN',
        'avg_m2': '$220 - $430 MXN/m²',
        'note': 'Varía por material (PVC o fibra de bambú)'
    },
    'VIGAS PVCWPCPU': {
        'unit': 'pieza',
        'range': '$450 - $1,200 MXN',
        'avg_m2': 'Por pieza según medida',
        'note': 'Varía por tamaño (70x50mm hasta 120x80mm)'
    },
    'PISOS': {
        'unit': 'caja',
        'range': '$900 - $2,500 MXN',
        'avg_m2': '$180 - $520 MXN/m²',
        'note': 'SPC más económico, WPC más cálido, deck sintético para exterior'
    },
    'ZACATE SINTÉTICO': {
        'unit': 'm²',
        'range': '$220 - $480 MXN/m²',
        'avg_m2': '$220 - $480 MXN/m²',
        'note': 'Depende de la altura (20-40mm) y densidad'
    },
    'CLADDING  PLACAS TIPO PIEDRA': {
        'unit': 'pieza',
        'range': '$550 - $1,050 MXN',
        'avg_m2': '$380 - $720 MXN/m²',
        'note': 'Imitación piedra real, mucho más ligero'
    }
}

# ========== GOOGLE ANALYTICS 4 ==========
# Reemplaza 'G-XXXXXXXXXX' por tu Measurement ID de Google Analytics 4.
# Obtén uno gratis en: https://analytics.google.com/analytics/web/#/
GA_MEASUREMENT_ID = 'G-XXXXXXXXXX'

def ga_script():
    if not GA_MEASUREMENT_ID or GA_MEASUREMENT_ID == 'G-XXXXXXXXXX':
        return ''
    return f'''
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_MEASUREMENT_ID}');
  </script>'''

# ========== RESEARCH DATA (from investigacion/) ==========
try:
    with open(BASE_DIR / 'investigacion_data.json', 'r', encoding='utf-8') as f:
        RESEARCH_DATA = json.load(f)
except Exception:
    RESEARCH_DATA = {}

# Slugs para paginas de sabias-que (deben coincidir con generate_sabias_que)
SABIAS_QUE_SLUGS = {
    'PLACAS PVC': 'pvc',
    'LAMBRIN WPC': 'wpc',
    'REVESTIMIENTO FLEXIBLE': 'revestimiento',
    'PLAFON PVC LAMINADO WOOD STYLE': 'plafon',
    'PLAFÓN PVC LAMINADO WOOD STYLE': 'plafon',
    'PANELES TRIDIMENSIONALES 3D': '3d',
    'VIGAS PVCWPCPU': 'vigas',
    'PISOS': 'pisos',
    'ZACATE SINTETICO': 'zacate',
    'ZACATE SINTÉTICO': 'zacate',
    'CLADDING  PLACAS TIPO PIEDRA': 'cladding',
}

def _copy_if_needed(src, dst):
    """Copia src a dst solo si dst no existe o tiene tamaño diferente."""
    try:
        if not dst.exists() or src.stat().st_size != dst.stat().st_size:
            shutil.copy2(src, dst)
            return True
    except Exception:
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    return False


def md_to_html(text):
    """Convierte Markdown básico a HTML."""
    if not text:
        return ''
    import re
    # Negritas
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Cursivas
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Headers h3
    text = re.sub(r'^###\s*(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    # Headers h4
    text = re.sub(r'^####\s*(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    # Listas
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item = stripped[2:]
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if stripped:
                result.append(f'<p>{stripped}</p>')
    if in_list:
        result.append('</ul>')
    return '\n'.join(result)

def generate_research_html(cat_name):
    """Genera seccion HTML con datos curiosos y FAQs de la investigacion."""
    if not RESEARCH_DATA:
        return ''
    # Buscar categoria por nombre aproximado
    research_key = None
    for key in RESEARCH_DATA:
        if cat_name.upper().replace(' ', '') in key.upper().replace(' ', '') or key.upper().replace(' ', '') in cat_name.upper().replace(' ', ''):
            research_key = key
            break
    if not research_key:
        return ''
    
    data = RESEARCH_DATA[research_key]
    html_parts = []
    
    # Datos curiosos
    if data.get('curiosos'):
        html_parts.append('''
  <section class="research-section">
    <div class="section-header">
      <h2>¿Sabías que?</h2>
      <div class="divider"></div>
      <p>Datos curiosos sobre este material</p>
    </div>
    <div class="research-content">
''')
        # Convertir datos curiosos a items
        curiosos_text = data['curiosos']
        # Dividir por parrafos que empiezan con **
        import re
        items = re.split(r'\n\n(?=\*\*)', curiosos_text)
        for item in items:
            item = item.strip()
            if item:
                html_parts.append(f'      <div class="research-item">{md_to_html(item)}</div>')
        html_parts.append('    </div>\n  </section>')
    
    # FAQs
    if data.get('faqs'):
        html_parts.append('''
  <section class="research-section">
    <div class="section-header">
      <h2>Preguntas Frecuentes</h2>
      <div class="divider"></div>
      <p>Respuestas a las dudas más comunes</p>
    </div>
    <div class="research-faqs">
''')
        faqs_text = data['faqs']
        # Extraer preguntas y respuestas
        qa_pairs = re.findall(r'\*\*❓\s*(.+?)\*\*\s*\n?>\s*(.+?)(?=\n\n\*\*❓|\Z)', faqs_text, re.DOTALL)
        for q, a in qa_pairs:
            q_clean = q.strip()
            a_clean = a.strip().replace('\n', ' ')
            html_parts.append(f'''      <div class="faq-item">
        <div class="faq-question">{q_clean}</div>
        <div class="faq-answer">{a_clean}</div>
      </div>''')
        html_parts.append('    </div>\n  </section>')
    
    return '\n'.join(html_parts)

# ========== CHATBOT KNOWLEDGE BASE ==========
CHATBOT_KB = {
    'horarios': {
        'lunes': 'Cerrado 🚪',
        'martes': '10:00 a 19:00',
        'miercoles': '9:00 a 19:00',
        'jueves': '9:00 a 19:00',
        'viernes': '9:00 a 19:00',
        'sabado': '9:00 a 19:00',
        'domingo': '9:00 a 15:00',
        'whatsapp': 'Atendemos WhatsApp a cualquier hora, excepto madrugada (aprox. 00:00 a 07:00)',
    },
    'envios': {
        'gratis': 'Nogales Sonora, Nogales AZ, Tucson',
        'nacional': 'Enviamos a todo México. El costo de envío corre por cuenta del cliente.',
        'tiempo_grandes': '2 a 3 días hábiles para pedidos grandes',
    },
    'pagos': {
        'metodos': 'Tarjeta de crédito, tarjeta de débito, transferencia bancaria y efectivo',
        'anticipo': 'En pedidos mayores a $10,000 se requiere 50% de anticipo',
    },
    'instalacion': {
        'disponible': True,
        'costo': 'Los precios del catálogo son solo por el material. La instalación se cotiza aparte.',
        'proceso': 'Un representante visita tu obra para medir y cotizar la instalación.',
    },
    'proyectos': {
        'tipos': 'Casas, oficinas, negocios, locales comerciales y cualquier espacio que requiera remodelación',
    },
    'cotizacion': {
        'tiempo': 'Menos de 24 horas',
        'incluye': 'Costos detallados y stock disponible',
        'sin_stock': 'Si no tenemos stock, estará disponible en 2 a 3 días',
    },
    'precios': {
        'iva': 'Todos los precios incluyen IVA',
        'mayorista': 'Ofrecemos descuento a mayorista',
    },
    'garantia': {
        'validacion': 'ADIS Diseño hace válida la garantía del fabricante',
        'pvc': '15 años',
        'wpc': '15 años',
        'spc': '12 años (residencial)',
        'zacate': '5 años',
    },
    'definiciones': {
        'pvc': 'Policloruro de Vinilo. Es un tipo de plástico muy usado en letreros, hojas rígidas, tuberías, anuncios y materiales de impresión porque es resistente, ligero y económico.',
        'wpc': 'Wood Plastic Composite (Compuesto de Madera y Plástico). Es un material hecho de fibras de madera mezcladas con plástico, muy usado en paneles, revestimientos, muebles y decoración porque parece madera pero resiste mejor la humedad y el desgaste.',
    },
    'venta': {
        'unidad': 'El tipo de unidad y cómo se vende viene en las fichas técnicas de cada categoría: por pieza, por hoja, tamaño de la hoja, etc.',
    },
    'productos_destacados': {
        'pvc_marmol': {
            'nombre': 'Hoja de PVC tipo Mármol',
            'descripcion': 'Solución decorativa perfecta para cualquier espacio interior. Añade elegancia a tu hogar, oficina o espacio comercial.',
            'caracteristicas': [
                'Fabricada con materiales de alta calidad',
                'Duradera y ligera, fácil de instalar y mantener',
                'Resistente al agua, las manchas y los arañazos',
                'Inversión que dura muchos años',
            ],
            'aplicaciones': 'Cocinas, baños, salas de estar y mucho más',
            'categoria_url': '1-placas-pvc.html',
        }
    },
    'respuestas': {
        'saludo': '¡Hola! 👋 Soy el asistente virtual de <strong>ADIS Diseño & Remodelación</strong>. Puedo ayudarte con información sobre nuestros productos, horarios, cotizaciones y más. ¿Qué necesitas?',
        'despedida': '¡Gracias por contactarnos! 😊 Si tienes más dudas, aquí estaré. También puedes escribirnos por WhatsApp al {tel_mx} o visitarnos en {ubicacion}. ¡Que tengas un excelente día!',
        'gracias': '¡Con gusto! 🙌 Estamos para servirte. ¿Hay algo más en lo que pueda ayudarte?',
        'no_entendi': 'Disculpa, no entendí muy bien. 😅 Puedo ayudarte con: productos, precios, cotizaciones, horarios, ubicación, envíos, instalación o garantías. ¿Cuál te interesa?',
    }
}

# Extensiones de imagen válidas
IMG_EXTS = ('.jpg', '.jpeg', '.png')


def is_image(filename):
    return filename.lower().endswith(IMG_EXTS)


def is_ficha(filename):
    """Detecta si un archivo es ficha técnica."""
    return 'ficha' in filename.lower() and is_image(filename)


def clean_name(folder_name):
    """Quita numeración inicial (ej: '1. Placas PVC' -> 'Placas PVC', '1.1 Tipo' -> 'Tipo')."""
    import re
    # Quita patrones como "1. ", "1.1 ", "9.1 ", "14. " al inicio
    cleaned = re.sub(r'^\d+(\.\d+)*\.?\s*', '', folder_name)
    return cleaned.strip()


def slugify(name):
    """Crea un slug seguro para URLs/archivos."""
    import unicodedata
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    return name.lower().replace(' ', '-').replace('_', '-').replace('.', '').replace('(', '').replace(')', '')[:40]


def sync_images(categories):
    """Copia imagenes de CATALOGO FINAL a Pagina/img/ para GitHub Pages (sync incremental)."""
    img_dir = BASE_DIR / 'img'
    img_dir.mkdir(parents=True, exist_ok=True)
    
    total = 0
    errors = []
    expected = set()
    for cat in categories:
        cat_img_dir = img_dir / cat["slug"]
        cat_img_dir.mkdir(parents=True, exist_ok=True)
        
        # Copiar productos directos
        for prod in cat["direct_products"]:
            src = cat["path"] / prod
            dst = cat_img_dir / prod
            expected.add(dst.resolve())
            if not src.exists():
                errors.append(f"  [ERROR] No existe: {src}")
                continue
            if _copy_if_needed(src, dst):
                total += 1
        
        # Copiar productos de subcategorias
        for sub in cat["subcategories"]:
            sub_img_dir = cat_img_dir / sub["slug"]
            sub_img_dir.mkdir(parents=True, exist_ok=True)
            for prod in sub["products"]:
                src = sub["path"] / prod
                dst = sub_img_dir / prod
                expected.add(dst.resolve())
                if not src.exists():
                    errors.append(f"  [ERROR] No existe: {src}")
                    continue
                if _copy_if_needed(src, dst):
                    total += 1
    
    if errors:
        print(f"ADVERTENCIA: {len(errors)} imagenes no se pudieron copiar:")
        for e in errors[:10]:
            print(e)
    print(f"Imagenes sincronizadas: {total} nuevas/actualizadas en {img_dir}")


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
        cat_slug = slugify(cat_folder)
        cat_filename = f"{cat_slug}.html"

        subcategories = []
        direct_products = []

        for item in sorted(os.listdir(cat_path)):
            item_path = cat_path / item
            if item_path.is_dir():
                sub_name = clean_name(item)
                sub_slug = slugify(item)
                products = get_products(item_path)
                ficha = get_ficha(item_path)
                subcategories.append({
                    'folder': item,
                    'name': sub_name,
                    'slug': sub_slug,
                    'products': products,
                    'ficha': ficha,
                    'path': item_path
                })
            elif is_image(item) and not is_ficha(item):
                direct_products.append(item)

        # Imagen representativa = primera imagen disponible
        thumb = None
        if subcategories:
            for sub in subcategories:
                if sub["products"]:
                    thumb = sub["path"] / sub["products"][0]
                    break
        if not thumb and direct_products:
            thumb = cat_path / direct_products[0]

        categories.append({
            'folder': cat_folder,
            'name': cat_name,
            'slug': cat_slug,
            'filename': cat_filename,
            'subcategories': subcategories,
            'direct_products': sorted(direct_products),
            'ficha': get_ficha(cat_path),
            'thumb': thumb,
            'path': cat_path
        })
    return categories


def mailto_link(product_name, category_name, subcategory_name=None):
    """Genera enlace mailto para cotización de producto."""
    subject = f"Cotizacion para {product_name}"
    body = f"Hola ADIS,%0D%0A%0D%0AMe interesa obtener una cotizacion para:%0D%0A%0D%0A"
    body += f"Producto: {product_name}%0D%0A"
    body += f"Categoria: {category_name}%0D%0A"
    if subcategory_name:
        body += f"Subcategoria: {subcategory_name}%0D%0A"
    body += f"%0D%0AFavor de contactarme para mas detalles.%0D%0A%0D%0AGracias."
    return f'mailto:{CONTACTO["email"]}?subject={subject}&body={body}'


# ========== CSS COMPLETO ==========
CSS = '''
:root { --gold: #C5A059; --gold-light: #E8D5A3; --black: #0F0F0F; --dark: #1A1A1A; --gray: #2A2A2A; --light: #F5F5F5; --white: #FFFFFF; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Montserrat', sans-serif;
  background: var(--black);
  color: var(--light);
  overflow-x: hidden;
  line-height: 1.6;
  padding-bottom: 90px;
}
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--dark); }
::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 4px; }

/* FONDO ANIMADO */
#bg-canvas {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0; pointer-events: none;
}

/* HEADER */
header {
  position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
  background: rgba(15,15,15,0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(197,160,89,0.2);
}
.header-inner {
  max-width: 1400px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.8rem 2rem;
}
.logo img {
  height: 55px; width: auto;
  filter: drop-shadow(0 0 8px rgba(197,160,89,0.3));
  transition: filter 0.3s ease;
}
.logo:hover img {
  filter: drop-shadow(0 0 15px rgba(197,160,89,0.6));
}
nav.desktop-nav { display: flex; gap: 2rem; align-items: center; }
nav.desktop-nav a {
  color: var(--light); text-decoration: none; font-size: 0.8rem;
  text-transform: uppercase; letter-spacing: 2px; font-weight: 600;
  position: relative; padding: 0.3rem 0; transition: color 0.3s;
}
nav.desktop-nav a::after {
  content: ''; position: absolute; bottom: 0; left: 0;
  width: 0; height: 2px; background: var(--gold); transition: width 0.3s;
}
nav.desktop-nav a:hover { color: var(--gold); }
nav.desktop-nav a:hover::after { width: 100%; }
.menu-btn {
  display: none; background: none; border: none; color: var(--gold);
  font-size: 1.5rem; cursor: pointer;
}
.mobile-menu {
  position: fixed; inset: 0; z-index: 999;
  background: rgba(15,15,15,0.98);
  display: none; flex-direction: column; align-items: center; justify-content: center;
  gap: 2rem;
}
.mobile-menu.active { display: flex; }
.mobile-menu a {
  color: var(--white); text-decoration: none; font-size: 1.2rem;
  text-transform: uppercase; letter-spacing: 3px; font-weight: 600;
}
.mobile-menu .close-menu {
  position: absolute; top: 1.5rem; right: 1.5rem;
  background: none; border: none; color: var(--gold); font-size: 2rem; cursor: pointer;
}

/* WHATSAPP FLOTANTE */
.whatsapp-float {
  position: fixed; bottom: 25px; right: 25px; z-index: 9999;
  width: 60px; height: 60px; background: #25D366;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 20px rgba(37,211,102,0.4);
  text-decoration: none; font-size: 1.8rem; color: white;
  transition: transform 0.3s, box-shadow 0.3s;
  animation: pulse-wa 2s infinite;
}
.whatsapp-float:hover { transform: scale(1.1); box-shadow: 0 6px 30px rgba(37,211,102,0.6); }
@keyframes pulse-wa {
  0% { box-shadow: 0 0 0 0 rgba(37,211,102,0.5); }
  70% { box-shadow: 0 0 0 15px rgba(37,211,102,0); }
  100% { box-shadow: 0 0 0 0 rgba(37,211,102,0); }
}
.wa-tooltip {
  position: absolute; right: 72px; top: 50%; transform: translateY(-50%) translateX(10px);
  background: var(--black); color: var(--white); padding: 0.5rem 0.9rem; border-radius: 8px;
  font-size: 0.78rem; font-weight: 600; white-space: nowrap; opacity: 0; visibility: hidden;
  transition: all 0.3s ease; border: 1px solid rgba(197,160,89,0.25); box-shadow: 0 4px 15px rgba(0,0,0,0.25);
}
.wa-tooltip::after {
  content: ''; position: absolute; right: -6px; top: 50%; transform: translateY(-50%);
  border-width: 6px 0 6px 6px; border-style: solid; border-color: transparent transparent transparent var(--black);
}
.whatsapp-float:hover .wa-tooltip { opacity: 1; visibility: visible; transform: translateY(-50%) translateX(0); }

/* MODAL COTIZAR POR WHATSAPP */
.wa-modal {
  position: fixed; inset: 0; z-index: 10000; background: rgba(15,15,15,0.92);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
  opacity: 0; visibility: hidden; transition: all 0.3s ease; backdrop-filter: blur(6px);
}
.wa-modal.active { opacity: 1; visibility: visible; }
.wa-modal-box {
  background: linear-gradient(145deg, rgba(26,26,26,0.98) 0%, rgba(15,15,15,0.98) 100%);
  border: 1px solid rgba(197,160,89,0.2); border-radius: 18px; width: 100%; max-width: 460px;
  padding: 1.8rem; position: relative; box-shadow: 0 25px 70px rgba(0,0,0,0.6);
  transform: translateY(20px) scale(0.97); transition: all 0.3s ease;
}
.wa-modal.active .wa-modal-box { transform: translateY(0) scale(1); }
.wa-modal-close {
  position: absolute; top: 0.8rem; right: 0.9rem; background: transparent; border: none;
  color: rgba(245,245,245,0.5); font-size: 1.3rem; cursor: pointer; transition: color 0.2s;
}
.wa-modal-close:hover { color: var(--gold); }
.wa-modal-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; color: var(--gold-light); margin-bottom: 0.4rem; text-align: center; }
.wa-modal-subtitle { color: rgba(245,245,245,0.6); font-size: 0.85rem; text-align: center; margin-bottom: 1.4rem; }
.wa-modal-field { margin-bottom: 0.9rem; }
.wa-modal-field label { display: block; font-size: 0.75rem; font-weight: 600; color: rgba(245,245,245,0.7); margin-bottom: 0.3rem; text-transform: uppercase; letter-spacing: 0.5px; }
.wa-modal-field input, .wa-modal-field select, .wa-modal-field textarea {
  width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(197,160,89,0.2);
  border-radius: 10px; padding: 0.7rem 0.9rem; color: var(--white); font-family: 'Montserrat', sans-serif;
  font-size: 0.9rem; transition: all 0.2s;
}
.wa-modal-field input:focus, .wa-modal-field select:focus, .wa-modal-field textarea:focus {
  outline: none; border-color: var(--gold); background: rgba(255,255,255,0.08); box-shadow: 0 0 0 3px rgba(197,160,89,0.1);
}
.wa-modal-field textarea { min-height: 80px; resize: vertical; }
.wa-modal-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem; }
.wa-modal-product { background: rgba(197,160,89,0.1); border: 1px dashed rgba(197,160,89,0.3); border-radius: 10px; padding: 0.7rem 0.9rem; color: var(--gold-light); font-size: 0.85rem; font-weight: 600; margin-bottom: 0.9rem; text-align: center; }
.wa-modal-submit {
  width: 100%; background: #25D366; color: white; border: none; border-radius: 12px;
  padding: 0.95rem; font-size: 1rem; font-weight: 700; cursor: pointer; transition: all 0.25s ease;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
}
.wa-modal-submit:hover { background: #1ebe57; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(37,211,102,0.35); }

/* STICKY CTA BAR */
.sticky-cta-bar {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 9998;
  display: grid; grid-template-columns: 1fr auto; gap: 0.6rem;
  padding: 0.7rem 1rem; background: rgba(15,15,15,0.96);
  border-top: 1px solid rgba(197,160,89,0.2); box-shadow: 0 -6px 30px rgba(0,0,0,0.35);
  transform: translateY(100%); transition: transform 0.35s ease;
}
.sticky-cta-bar.visible { transform: translateY(0); }
.sticky-cta-bar a { display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.75rem 1rem; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 0.85rem; transition: all 0.25s ease; }
.sticky-cta-wa { background: #25D366; color: white; }
.sticky-cta-wa:hover { background: #1ebe57; transform: translateY(-2px); }
.sticky-cta-pdf { background: rgba(197,160,89,0.15); color: var(--gold-light); border: 1px solid rgba(197,160,89,0.3); }
.sticky-cta-pdf:hover { background: rgba(197,160,89,0.25); }

/* SECCIONES GENERALES */
.section-wrap {
  position: relative; z-index: 1;
  padding: 5rem 2rem;
}
.section-wrap-alt {
  position: relative; z-index: 1;
  padding: 5rem 2rem;
  background: rgba(26,26,26,0.7);
  backdrop-filter: blur(4px);
  border-top: 1px solid rgba(197,160,89,0.08);
  border-bottom: 1px solid rgba(197,160,89,0.08);
}
.section-header {
  text-align: center; margin-bottom: 3rem;
}
.section-header h2 {
  font-family: 'Playfair Display', serif; font-size: 2.2rem; color: var(--white);
  margin-bottom: 0.5rem;
}
.section-header p {
  color: rgba(245,245,245,0.6); font-size: 0.95rem; max-width: 600px; margin: 0 auto;
}
.divider {
  width: 60px; height: 3px; background: var(--gold); margin: 1rem auto;
}

/* HERO HOME */
.hero-home {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  position: relative; padding: 5rem 2rem;
  text-align: center;
}
.hero-content {
  max-width: 800px; position: relative; z-index: 2;
}
.hero-content img {
  height: 140px; width: auto;
  filter: drop-shadow(0 0 25px rgba(197,160,89,0.5));
  margin-bottom: 2rem;
}
.hero-badge {
  display: inline-block; padding: 0.5rem 1.5rem;
  border: 1px solid var(--gold); color: var(--gold);
  font-size: 0.7rem; letter-spacing: 4px; text-transform: uppercase;
  margin-bottom: 1.5rem;
  background: rgba(15,15,15,0.5);
}
.hero-home h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  color: var(--white); line-height: 1.1; margin-bottom: 1rem;
}
.hero-home h1 em {
  color: var(--gold); font-style: normal;
  background: linear-gradient(90deg, var(--gold), var(--gold-light));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-home p {
  font-size: 1.05rem; color: rgba(245,245,245,0.75);
  line-height: 1.7; max-width: 550px; margin: 0 auto 2rem;
}
.btn-primary {
  display: inline-block; padding: 0.9rem 2.5rem;
  background: var(--gold); color: var(--black);
  font-size: 0.8rem; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; text-decoration: none;
  border: 2px solid var(--gold); transition: all 0.3s;
}
.btn-primary:hover {
  background: transparent; color: var(--gold);
}

/* INFO CARDS */
.info-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;
  max-width: 1200px; margin: 0 auto;
}
.info-card {
  background: rgba(42,42,42,0.75);
  backdrop-filter: blur(10px);
  padding: 2.5rem 2rem;
  border: 1px solid rgba(197,160,89,0.15);
  transition: all 0.3s ease; text-align: center;
  border-radius: 8px;
  text-decoration: none;
  color: var(--white);
  display: block;
}
.info-card:hover,
.info-card:visited,
.info-card:active,
.info-card:focus {
  border-color: var(--gold); transform: translateY(-6px);
  box-shadow: 0 15px 40px rgba(0,0,0,0.3);
  background: rgba(42,42,42,0.9);
  color: var(--white);
  text-decoration: none;
}
.info-card h3,
.info-card p {
  color: var(--white);
  text-decoration: none;
}
.info-card .icon {
  width: 55px; height: 55px; margin: 0 auto 1.2rem;
  border: 1px solid var(--gold); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: var(--gold); font-size: 1.4rem;
}
.info-card h3 {
  font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase;
  color: var(--white); margin-bottom: 0.6rem;
}
.info-card p {
  font-size: 0.82rem; color: rgba(245,245,245,0.65); line-height: 1.6;
}

/* CATEGORY GRID HOME */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  max-width: 1200px; margin: 0 auto;
}
.cat-card {
  position: relative; overflow: hidden;
  border-radius: 8px;
  transition: all 0.4s ease; cursor: pointer;
  text-decoration: none; color: inherit;
  display: block;
  height: 280px;
  border: 1px solid rgba(197,160,89,0.15);
}
.cat-card:hover {
  border-color: var(--gold);
  transform: translateY(-6px);
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}
.cat-card img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.6s ease;
}
.cat-card:hover img {
  transform: scale(1.1);
}
.cat-card-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.3) 50%, transparent 100%);
  display: flex; flex-direction: column; justify-content: flex-end;
  padding: 1.5rem;
}
.cat-card-overlay h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1.4rem; color: var(--white); margin-bottom: 0.3rem;
}
.cat-card-overlay span {
  font-size: 0.75rem; color: var(--gold); text-transform: uppercase;
  letter-spacing: 2px; font-weight: 600;
}

/* CATEGORIAS ESTRELLA */
.cat-card.featured {
  border: 2px solid var(--gold);
  box-shadow: 0 0 30px rgba(197,160,89,0.25);
  animation: starGlow 3s ease-in-out infinite;
}
@keyframes starGlow {
  0%, 100% { box-shadow: 0 0 30px rgba(197,160,89,0.25); }
  50% { box-shadow: 0 0 50px rgba(197,160,89,0.5); }
}
.star-badge {
  position: absolute; top: 12px; right: 12px; z-index: 2;
  background: var(--gold); color: var(--black);
  padding: 0.3rem 0.8rem; border-radius: 20px;
  font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; box-shadow: 0 4px 15px rgba(197,160,89,0.4);
}

/* SECCIÓN ESTRELLAS HOME */
.featured-section {
  padding: 5rem 2rem;
  position: relative; z-index: 1;
}
.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
  max-width: 1100px; margin: 0 auto;
}
.featured-card {
  position: relative; overflow: hidden;
  border-radius: 12px;
  height: 380px;
  border: 2px solid var(--gold);
  text-decoration: none; color: inherit; display: block;
  transition: all 0.4s ease;
  box-shadow: 0 0 40px rgba(197,160,89,0.2);
}
.featured-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 30px 60px rgba(197,160,89,0.35);
}
.featured-card img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.8s ease;
}
.featured-card:hover img {
  transform: scale(1.1);
}
.featured-card-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.4) 40%, transparent 70%);
  display: flex; flex-direction: column; justify-content: flex-end;
  padding: 2rem;
}
.featured-card-overlay .star-label {
  display: inline-block; width: fit-content;
  background: var(--gold); color: var(--black);
  padding: 0.4rem 1rem; border-radius: 20px;
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2px; margin-bottom: 1rem;
}
.featured-card-overlay h3 {
  font-family: 'Playfair Display', serif;
  font-size: 2rem; color: var(--white); margin-bottom: 0.5rem;
}
.featured-card-overlay p {
  font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.6;
  max-width: 400px;
}

/* HERO CATEGORIA ESTRELLA */
.hero-star-badge {
  display: inline-block;
  background: var(--gold); color: var(--black);
  padding: 0.5rem 1.5rem; border-radius: 25px;
  font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2px; margin-bottom: 1rem;
  box-shadow: 0 4px 20px rgba(197,160,89,0.4);
  animation: starGlowBadge 2.5s ease-in-out infinite;
}
@keyframes starGlowBadge {
  0%, 100% { box-shadow: 0 4px 20px rgba(197,160,89,0.4); }
  50% { box-shadow: 0 4px 35px rgba(197,160,89,0.7); }
}

/* HERO CATEGORÍA */
.hero-cat {
  padding: 8rem 2rem 3rem;
  text-align: center;
  position: relative; z-index: 1;
}
.hero-cat h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 4vw, 3.2rem);
  color: var(--white); margin-bottom: 0.6rem;
}
.hero-cat p {
  color: rgba(245,245,245,0.6); font-size: 1rem; max-width: 700px; margin: 0 auto;
}

/* SUBCATEGORÍA SECCIÓN */
.subcat-section {
  padding: 3rem 2rem;
  position: relative; z-index: 1;
}
.subcat-header {
  text-align: center; margin-bottom: 2.5rem;
}
.subcat-header h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1.6rem; color: var(--gold);
  margin-bottom: 0.5rem;
}
.subcat-header .subcat-count {
  font-size: 0.8rem; color: rgba(245,245,245,0.5);
  text-transform: uppercase; letter-spacing: 2px;
}
.subcat-divider {
  width: 40px; height: 2px; background: var(--gold);
  margin: 1rem auto;
}

/* FICHA TÉCNICA */
.ficha-section {
  padding: 2rem 2rem;
  position: relative; z-index: 1;
  text-align: center;
}
.ficha-btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.7rem 1.5rem;
  background: rgba(197,160,89,0.15);
  color: var(--gold);
  border: 1px solid var(--gold);
  text-decoration: none;
  font-size: 0.8rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1px;
  transition: all 0.3s;
  border-radius: 4px;
}
.ficha-btn:hover {
  background: var(--gold); color: var(--black);
}

/* PRODUCTOS GRID */
.products-section {
  padding: 2rem 2rem 4rem;
  position: relative; z-index: 1;
}
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2rem;
  max-width: 1400px; margin: 0 auto;
}
.product-card {
  background: rgba(42,42,42,0.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(197,160,89,0.1);
  overflow: hidden; transition: all 0.4s ease;
  border-radius: 8px;
}
.product-card:hover {
  border-color: rgba(197,160,89,0.4);
  box-shadow: 0 15px 50px rgba(0,0,0,0.4);
  transform: translateY(-6px);
  background: rgba(42,42,42,0.9);
}
.product-gallery {
  position: relative; height: 320px;
  background: #111; overflow: hidden;
}
.product-gallery img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.6s ease;
}
.product-card:hover .product-gallery img {
  transform: scale(1.05);
}
.product-info {
  padding: 1.2rem;
  text-align: center;
  border-top: 1px solid rgba(197,160,89,0.1);
}
.product-name {
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem; color: var(--gold);
  margin-bottom: 0.8rem;
}
.btn-cotizar {
  display: inline-block;
  padding: 0.6rem 1.5rem;
  background: var(--gold); color: var(--black);
  font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s;
}
.btn-cotizar:hover {
  background: transparent; color: var(--gold);
  box-shadow: inset 0 0 0 1px var(--gold);
}

/* FOOTER */
footer {
  padding: 3rem 2rem 2rem; text-align: center;
  position: relative; z-index: 1;
  background: rgba(15,15,15,0.8);
  backdrop-filter: blur(6px);
  border-top: 1px solid rgba(197,160,89,0.1);
}
.footer-logo img { height: 70px; width: auto; margin-bottom: 1rem; }
.footer-info {
  color: rgba(245,245,245,0.5); font-size: 0.85rem; line-height: 1.8;
  max-width: 500px; margin: 0 auto 1.5rem;
}
.footer-info strong { color: var(--gold); font-weight: 600; }
.copyright {
  font-size: 0.7rem; color: rgba(245,245,245,0.3); letter-spacing: 2px;
  border-top: 1px solid rgba(197,160,89,0.1); padding-top: 1.5rem;
}

/* CONTACTO */
.contact-section {
  padding: 8rem 2rem 4rem;
  max-width: 900px; margin: 0 auto;
  position: relative; z-index: 1;
}
.contact-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem;
  margin-top: 2rem;
}
.contact-card {
  background: rgba(42,42,42,0.75);
  backdrop-filter: blur(8px);
  padding: 2rem 1.5rem;
  border: 1px solid rgba(197,160,89,0.12);
  text-align: center; transition: all 0.3s;
  border-radius: 8px;
}
.contact-card:hover {
  border-color: var(--gold); transform: translateY(-5px);
  background: rgba(42,42,42,0.9);
}
.contact-card .icon {
  font-size: 2rem; margin-bottom: 0.8rem;
}
.contact-card h3 {
  font-size: 0.8rem; color: var(--white); text-transform: uppercase;
  letter-spacing: 2px; margin-bottom: 0.5rem;
}
.contact-card p, .contact-card a {
  font-size: 0.85rem; color: rgba(245,245,245,0.8);
  text-decoration: none;
}
.contact-card a:hover { color: var(--gold); }

/* BOTONES */
.btn-back, .btn-outline {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.8rem 1.8rem;
  font-size: 0.75rem; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; text-decoration: none;
  transition: all 0.3s; margin: 0 0.5rem 1rem 0;
  border-radius: 4px;
}
.btn-back {
  background: var(--gold); color: var(--black); border: 2px solid var(--gold);
}
.btn-back:hover { background: transparent; color: var(--gold); }
.btn-outline {
  background: transparent; color: var(--gold); border: 2px solid var(--gold);
}
.btn-outline:hover { background: var(--gold); color: var(--black); }

/* STATS SECTION */
.stats-section {
  padding: 4rem 2rem;
  position: relative; z-index: 1;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  max-width: 1000px; margin: 0 auto;
}
.stat-item {
  text-align: center;
  padding: 2rem;
  background: rgba(42,42,42,0.6);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(197,160,89,0.15);
  border-radius: 12px;
  transition: all 0.3s;
}
.stat-item:hover {
  border-color: var(--gold);
  transform: translateY(-5px);
}
.stat-number {
  font-family: 'Playfair Display', serif;
  font-size: 2.5rem;
  color: var(--gold);
  font-weight: 700;
}
.stat-label {
  font-size: 0.85rem;
  color: rgba(245,245,245,0.6);
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-top: 0.5rem;
}

/* SCROLL ANIMATIONS */
.reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: all 0.8s ease-out;
}
.reveal.active {
  opacity: 1;
  transform: translateY(0);
}

/* CHATBOT */
.chatbot-float {
  position: fixed;
  bottom: 25px;
  left: 25px;
  z-index: 9998;
  width: 60px;
  height: 60px;
  background: var(--gold);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(197,160,89,0.4);
  cursor: pointer;
  font-size: 1.8rem;
  color: var(--black);
  transition: transform 0.3s, box-shadow 0.3s;
  border: none;
}
.chatbot-float:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(197,160,89,0.6);
}
.chatbot-window {
  position: fixed;
  bottom: 95px;
  left: 25px;
  z-index: 9998;
  width: 350px;
  max-width: calc(100vw - 50px);
  background: var(--dark);
  border: 1px solid rgba(197,160,89,0.3);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  display: none;
  flex-direction: column;
  overflow: hidden;
  animation: chatPop 0.3s ease-out;
}
@keyframes chatPop {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.chatbot-window.active { display: flex; }
.chatbot-header {
  background: var(--gold);
  color: var(--black);
  padding: 1rem 1.2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chatbot-header h4 {
  font-family: 'Playfair Display', serif;
  font-size: 1rem;
  margin: 0;
}
.chatbot-close {
  background: none;
  border: none;
  color: var(--black);
  font-size: 1.2rem;
  cursor: pointer;
  font-weight: bold;
}
.chatbot-body {
  padding: 1.2rem;
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}
.chat-message {
  max-width: 85%;
  padding: 0.8rem 1rem;
  border-radius: 12px;
  font-size: 0.85rem;
  line-height: 1.5;
}
.chat-message.bot {
  background: rgba(197,160,89,0.15);
  color: var(--light);
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}
.chat-message.user {
  background: var(--gold);
  color: var(--black);
  align-self: flex-end;
  border-bottom-right-radius: 4px;
  font-weight: 600;
}
.chat-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.chat-option-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--gold);
  color: var(--gold);
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Montserrat', sans-serif;
}
.chat-option-btn:hover {
  background: var(--gold);
  color: var(--black);
}
.chat-whatsapp-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: #25D366;
  color: white;
  text-decoration: none;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-top: 0.5rem;
}
.chat-product-card {
  display: flex;
  gap: 0.8rem;
  padding: 0.7rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(197,160,89,0.15);
  border-radius: 10px;
  margin-bottom: 0.5rem;
  transition: all 0.2s;
}
.chat-product-card:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(197,160,89,0.3);
}
.chat-product-card img {
  width: 55px;
  height: 55px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(197,160,89,0.2);
  flex-shrink: 0;
}
.chat-product-info { flex: 1; min-width: 0; }
.chat-product-info a {
  color: var(--gold-light);
  font-weight: 600;
  font-size: 0.85rem;
  text-decoration: none;
  display: block;
  margin-bottom: 0.15rem;
}
.chat-product-info a:hover { color: var(--gold); }
.chat-product-cat {
  font-size: 0.72rem;
  color: rgba(245,245,245,0.55);
}
.chat-product-actions {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}
.chat-product-actions a, .chat-product-actions button {
  padding: 0.35rem 0.75rem;
  border-radius: 15px;
  font-size: 0.72rem;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-family: 'Montserrat', sans-serif;
  transition: all 0.2s;
}
.chat-product-actions .primary {
  background: var(--gold);
  color: var(--black);
  font-weight: 600;
}
.chat-product-actions .primary:hover { background: var(--gold-light); }
.chat-product-actions .secondary {
  background: transparent;
  border: 1px solid var(--gold);
  color: var(--gold);
}
.chat-product-actions .secondary:hover { background: var(--gold); color: var(--black); }
.chat-time {
  font-size: 0.65rem;
  color: rgba(245,245,245,0.4);
  margin-top: 0.25rem;
  text-align: right;
}
.chat-header-actions {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}
.chat-clear {
  background: rgba(0,0,0,0.15);
  border: none;
  color: var(--black);
  font-size: 0.75rem;
  padding: 0.3rem 0.6rem;
  border-radius: 12px;
  cursor: pointer;
  font-family: 'Montserrat', sans-serif;
  font-weight: 600;
}
.chat-clear:hover { background: rgba(0,0,0,0.25); }
.chat-context-hint {
  font-size: 0.75rem;
  color: rgba(245,245,245,0.5);
  font-style: italic;
  margin: -0.3rem 0 0.3rem;
}
.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 0.9rem 1rem;
  min-width: 50px;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  background: rgba(245,245,245,0.5);
  border-radius: 50%;
  animation: typingBounce 1.2s infinite ease-in-out;
}
.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.chatbot-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #ff4444;
  color: white;
  font-size: 0.65rem;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: none;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  z-index: 1;
}

/* SPECS BAR - ESPECIFICACIONES TECNICAS */
.specs-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  max-width: 1200px;
  margin: 0 auto 3rem;
  padding: 0 2rem;
}
.spec-item {
  background: rgba(42,42,42,0.6);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(197,160,89,0.15);
  border-radius: 10px;
  padding: 1.2rem 1rem;
  text-align: center;
  transition: all 0.3s;
}
.spec-item:hover {
  border-color: var(--gold);
  transform: translateY(-3px);
}
.spec-label {
  display: block;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--gold);
  margin-bottom: 0.4rem;
  font-weight: 600;
}
.spec-value {
  display: block;
  font-size: 0.85rem;
  color: rgba(245,245,245,0.8);
}

/* SUBCATEGORÍA NAV - ÍNDICE RÁPIDO */
.subcat-nav {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 0.6rem;
  max-width: 1000px; margin: 0 auto 2rem; padding: 0 2rem;
}
.subcat-nav a {
  display: inline-block; padding: 0.5rem 1.2rem;
  background: rgba(197,160,89,0.1); border: 1px solid rgba(197,160,89,0.25);
  color: var(--gold); text-decoration: none; font-size: 0.75rem;
  text-transform: uppercase; letter-spacing: 1px; border-radius: 20px;
  transition: all 0.3s;
}
.subcat-nav a:hover {
  background: var(--gold); color: var(--black); border-color: var(--gold);
}

/* BUSCADOR GLOBAL */
.search-box {
  position: relative; display: flex; align-items: center;
}
.search-box input {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(197,160,89,0.2);
  border-radius: 25px; padding: 0.5rem 2.5rem 0.5rem 1rem;
  color: var(--light); font-family: 'Montserrat', sans-serif; font-size: 0.8rem;
  width: 180px; transition: all 0.3s;
}
.search-box input:focus {
  outline: none; border-color: var(--gold); width: 260px; background: rgba(255,255,255,0.12);
}
.search-box input::placeholder { color: rgba(245,245,245,0.4); }
.search-box button {
  position: absolute; right: 8px; background: none; border: none;
  color: var(--gold); cursor: pointer; font-size: 1rem;
}
.search-dropdown {
  position: absolute; top: calc(100% + 10px); right: 0;
  width: 360px; max-height: 450px; overflow-y: auto;
  background: rgba(26,26,26,0.98); border: 1px solid rgba(197,160,89,0.25);
  border-radius: 16px; box-shadow: 0 25px 70px rgba(0,0,0,0.7);
  display: none; z-index: 1001; padding: 0.5rem 0;
  backdrop-filter: blur(20px);
}
.search-dropdown.active { display: block; animation: searchPop 0.2s ease-out; }
@keyframes searchPop {
  from { opacity: 0; transform: translateY(-8px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.search-dropdown-header {
  padding: 0.6rem 1rem; font-size: 0.65rem; text-transform: uppercase;
  letter-spacing: 2px; color: rgba(245,245,245,0.4); border-bottom: 1px solid rgba(197,160,89,0.1);
}
.search-item {
  display: flex; align-items: center; gap: 0.9rem;
  padding: 0.75rem 1rem; text-decoration: none;
  border-bottom: 1px solid rgba(197,160,89,0.06);
  transition: all 0.2s; cursor: pointer;
}
.search-item:hover, .search-item.active {
  background: rgba(197,160,89,0.12); border-left: 3px solid var(--gold);
  padding-left: calc(1rem - 3px);
}
.search-item img {
  width: 50px; height: 50px; object-fit: cover; border-radius: 8px;
  border: 1px solid rgba(197,160,89,0.15);
}
.search-item-info { flex: 1; min-width: 0; }
.search-item-name {
  color: var(--white); font-size: 0.82rem; font-weight: 600; display: block;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.search-item-name mark {
  background: rgba(197,160,89,0.3); color: var(--gold); border-radius: 2px; padding: 0 2px;
}
.search-item-cat {
  color: rgba(245,245,245,0.5); font-size: 0.72rem; display: block; margin-top: 2px;
}
.search-empty {
  padding: 2rem; text-align: center; color: rgba(245,245,245,0.5); font-size: 0.85rem;
}
.search-shortcut {
  display: inline-block; padding: 2px 6px; border-radius: 4px;
  background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15);
  font-size: 0.65rem; color: rgba(245,245,245,0.5); margin-left: 6px;
}
@media (max-width: 768px) {
  .search-box input { width: 140px; }
  .search-box input:focus { width: 200px; }
  .search-dropdown { width: calc(100vw - 40px); right: auto; left: -20px; }
}

/* WHATSAPP BOTÓN EN PRODUCTO */
.product-actions {
  display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 0.5rem;
}
.btn-whatsapp {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.5rem 1rem; background: #25D366; color: white;
  font-size: 0.7rem; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; text-decoration: none; border-radius: 4px;
  transition: all 0.3s;
}
.btn-whatsapp:hover { background: #1ebe57; transform: scale(1.05); }

/* LIGHTBOX */
.lightbox {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,0.95);
  display: none; align-items: center; justify-content: center;
  backdrop-filter: blur(10px);
}
.lightbox.active { display: flex; }
.lightbox img {
  max-width: 90vw; max-height: 85vh; object-fit: contain;
  border-radius: 8px; box-shadow: 0 20px 60px rgba(0,0,0,0.8);
}
.lightbox-close {
  position: absolute; top: 20px; right: 30px;
  background: none; border: none; color: var(--white);
  font-size: 2.5rem; cursor: pointer; transition: color 0.3s;
}
.lightbox-close:hover { color: var(--gold); }
.lightbox-caption {
  position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
  background: rgba(15,15,15,0.8); padding: 0.6rem 1.5rem;
  border-radius: 20px; color: var(--gold); font-size: 0.9rem;
  border: 1px solid rgba(197,160,89,0.3);
}
.product-gallery { cursor: pointer; }

/* FACEBOOK LINK */
.footer-social {
  display: flex; justify-content: center; gap: 1rem; margin: 1rem 0;
}
.footer-social a {
  display: inline-flex; align-items: center; justify-content: center;
  width: 42px; height: 42px; border-radius: 50%;
  border: 1px solid rgba(197,160,89,0.3); color: var(--gold);
  text-decoration: none; font-size: 1.2rem; transition: all 0.3s;
}
.footer-social a:hover {
  background: var(--gold); color: var(--black); border-color: var(--gold);
}

/* HERO CATEGORIA CON IMAGEN DE FONDO */
.hero-cat-bg {
  position: relative;
  min-height: 55vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 8rem 2rem 4rem;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.hero-cat-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(15,15,15,0.5) 0%, rgba(15,15,15,0.85) 70%, var(--black) 100%);
}
.hero-cat-bg .hero-cat-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
}
.hero-cat-bg h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  color: var(--white);
  margin-bottom: 1rem;
  text-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
.hero-cat-bg p {
  font-size: 1.1rem;
  color: rgba(245,245,245,0.85);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.7;
}
.hero-cat-badge {
  display: inline-block;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--gold);
  color: var(--gold);
  font-size: 0.7rem;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
  background: rgba(15,15,15,0.5);
}
.hero-cat-actions {
  display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-top: 1.8rem;
}
.hero-cat-actions .btn-primary { padding: 0.9rem 2rem; font-size: 0.9rem; }
.hero-star-badge {
  display: inline-block; padding: 0.35rem 1rem; background: var(--gold); color: var(--black);
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
  border-radius: 20px; margin-bottom: 1rem;
}

/* FILTROS FACETADOS */
.cat-filters { max-width: 1200px; margin: 0 auto 2rem; padding: 0 2rem; position: relative; z-index: 1; }
.cat-filters-inner {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(197,160,89,0.12);
  border-radius: 16px; padding: 1.2rem 1.5rem;
}
.cat-filter-search {
  width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(197,160,89,0.2);
  border-radius: 10px; padding: 0.8rem 1rem; color: var(--white); font-family: 'Montserrat', sans-serif;
  font-size: 0.9rem; margin-bottom: 1rem; transition: all 0.2s;
}
.cat-filter-search:focus { outline: none; border-color: var(--gold); background: rgba(255,255,255,0.08); box-shadow: 0 0 0 3px rgba(197,160,89,0.1); }
.cat-filter-search::placeholder { color: rgba(245,245,245,0.4); }
.cat-filter-chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.filter-chip {
  background: transparent; border: 1px solid rgba(197,160,89,0.25); color: rgba(245,245,245,0.7);
  padding: 0.4rem 0.9rem; border-radius: 20px; cursor: pointer; font-size: 0.8rem; font-weight: 500;
  transition: all 0.2s; font-family: 'Montserrat', sans-serif;
}
.filter-chip:hover, .filter-chip.active { background: var(--gold); color: var(--black); border-color: var(--gold); }
.cat-filter-count { text-align: right; font-size: 0.8rem; color: rgba(245,245,245,0.5); margin-top: 0.8rem; }

/* SUBCATEGORIA MEJORADA */
.subcat-section {
  padding: 4rem 2rem;
  position: relative;
  z-index: 1;
}
.subcat-header {
  text-align: center;
  margin-bottom: 3rem;
}
.subcat-header h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1.8rem;
  color: var(--gold);
  margin-bottom: 0.5rem;
}
.subcat-header .subcat-count {
  font-size: 0.8rem;
  color: rgba(245,245,245,0.5);
  text-transform: uppercase;
  letter-spacing: 2px;
}
.subcat-divider {
  width: 40px;
  height: 2px;
  background: var(--gold);
  margin: 1rem auto;
}

/* PRODUCTOS MEJORADOS */
.products-section {
  padding: 2rem 2rem 5rem;
  position: relative;
  z-index: 1;
}
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2.5rem;
  max-width: 1400px;
  margin: 0 auto;
}
.product-card {
  background: rgba(42,42,42,0.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(197,160,89,0.1);
  overflow: hidden;
  transition: all 0.4s ease;
  border-radius: 12px;
  position: relative;
}
.product-card:hover {
  border-color: rgba(197,160,89,0.4);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  transform: translateY(-8px);
  background: rgba(42,42,42,0.9);
}
.product-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  opacity: 0;
  transition: opacity 0.4s;
}
.product-card:hover::after {
  opacity: 1;
}
.product-gallery {
  position: relative;
  height: 380px;
  background: #111;
  overflow: hidden;
}
.product-gallery img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s ease;
}
.product-card:hover .product-gallery img {
  transform: scale(1.08);
}
.product-gallery::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60%;
  background: linear-gradient(to top, rgba(15,15,15,0.8), transparent);
  opacity: 0;
  transition: opacity 0.4s;
}
.product-card:hover .product-gallery::after {
  opacity: 1;
}
.product-info {
  padding: 1.5rem;
  text-align: center;
  border-top: 1px solid rgba(197,160,89,0.1);
}
.product-name {
  font-family: 'Playfair Display', serif;
  font-size: 1.25rem;
  color: var(--gold);
  margin-bottom: 1rem;
}
.btn-cotizar {
  display: inline-block;
  padding: 0.7rem 2rem;
  background: var(--gold);
  color: var(--black);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  text-decoration: none;
  border-radius: 30px;
  transition: all 0.3s;
}
.btn-cotizar:hover {
  background: transparent;
  color: var(--gold);
  box-shadow: inset 0 0 0 2px var(--gold);
}

/* CATEGORIA CARD MEJORADA */
.cat-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  transition: all 0.4s ease;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  display: block;
  height: 320px;
  border: 1px solid rgba(197,160,89,0.15);
}
.cat-card:hover {
  border-color: var(--gold);
  transform: translateY(-8px);
  box-shadow: 0 25px 60px rgba(0,0,0,0.6);
}
.cat-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.8s ease;
}
.cat-card:hover img {
  transform: scale(1.12);
}
.cat-card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.4) 50%, transparent 100%);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 2rem;
}
.cat-card-overlay h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1.6rem;
  color: var(--white);
  margin-bottom: 0.4rem;
}
.cat-card-overlay span {
  font-size: 0.8rem;
  color: var(--gold);
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 600;
}
.cat-card-overlay .cat-arrow {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  width: 40px;
  height: 40px;
  border: 1px solid var(--gold);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gold);
  font-size: 1.2rem;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.3s;
}
.cat-card:hover .cat-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* MEGA MENU & DROPDOWNS */
.mega-trigger { position: relative; }
.mega-trigger::after {
  content: '▼'; font-size: 0.6rem; margin-left: 0.3rem; color: var(--gold); opacity: 0.7; vertical-align: middle;
}
.mega-menu {
  position: absolute; top: calc(100% + 12px); left: 50%; transform: translateX(-50%) translateY(10px);
  width: 780px; max-width: 92vw; background: rgba(8,8,8,0.98); backdrop-filter: blur(24px);
  border: 2px solid rgba(197,160,89,0.55); border-radius: 18px; padding: 2rem;
  box-shadow: 0 40px 100px rgba(0,0,0,0.9), 0 0 0 1px rgba(197,160,89,0.1); opacity: 0; visibility: hidden; transition: all 0.35s ease;
  z-index: 1002; display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
}
.mega-trigger:hover .mega-menu { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
.mega-item {
  display: flex; align-items: center; gap: 1rem; padding: 1rem; border-radius: 12px;
  text-decoration: none; color: var(--light); transition: all 0.3s; border: 1px solid transparent;
  background: rgba(255,255,255,0.02);
}
.mega-item:hover { background: rgba(197,160,89,0.12); border-color: rgba(197,160,89,0.45); transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
.mega-item img { width: 52px; height: 52px; object-fit: cover; border-radius: 10px; border: 1px solid rgba(197,160,89,0.25); }
.mega-item span { font-size: 0.9rem; font-weight: 600; letter-spacing: 1px; }

/* DROPDOWN ¿SABÍAS QUE? */
.nav-dropdown {
  position: absolute; top: calc(100% + 12px); left: 50%; transform: translateX(-50%) translateY(10px);
  width: 520px; max-width: 92vw; background: rgba(8,8,8,0.98); backdrop-filter: blur(24px);
  border: 2px solid rgba(197,160,89,0.55); border-radius: 18px; padding: 1.5rem 2rem;
  box-shadow: 0 40px 100px rgba(0,0,0,0.9), 0 0 0 1px rgba(197,160,89,0.1); opacity: 0; visibility: hidden; transition: all 0.35s ease;
  z-index: 1002; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.6rem;
}
.mega-trigger:hover .nav-dropdown { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
.dropdown-item {
  display: flex; align-items: center; gap: 0.9rem; padding: 0.85rem 1rem; border-radius: 12px;
  text-decoration: none; color: var(--light); transition: all 0.3s; border: 1px solid transparent;
  background: rgba(255,255,255,0.02); font-size: 0.9rem; font-weight: 600; letter-spacing: 1px;
}
.dropdown-item:hover { background: rgba(197,160,89,0.12); border-color: rgba(197,160,89,0.45); transform: translateX(6px); }
.dropdown-icon { font-size: 1.4rem; width: 32px; text-align: center; }

/* SEARCH HERO */
.search-hero { max-width: 850px; margin: 3rem auto 0; position: relative; z-index: 2; text-align: center; }
.search-hero-title { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: var(--gold); margin-bottom: 1rem; letter-spacing: 1px; }
.search-hero-input {
  width: 100%; padding: 1.3rem 2rem 1.3rem 4rem; background: rgba(15,15,15,0.75);
  border: 3px solid rgba(197,160,89,0.5); border-radius: 60px; color: var(--white);
  font-family: 'Montserrat', sans-serif; font-size: 1.15rem; backdrop-filter: blur(12px);
  transition: all 0.3s; box-shadow: 0 8px 40px rgba(0,0,0,0.4);
}
.search-hero-input:focus { outline: none; border-color: var(--gold); box-shadow: 0 0 50px rgba(197,160,89,0.35); background: rgba(15,15,15,0.95); transform: scale(1.02); }
.search-hero-input::placeholder { color: rgba(245,245,245,0.5); font-weight: 500; }
.search-hero-icon { position: absolute; left: 1.5rem; top: 50%; transform: translateY(-50%); font-size: 1.5rem; color: var(--gold); pointer-events: none; }
.search-hero-hint { text-align: center; margin-top: 1rem; font-size: 0.8rem; color: rgba(245,245,245,0.5); letter-spacing: 1px; }

/* SPOTLIGHT OVERLAY */
.spotlight-overlay {
  position: fixed; inset: 0; z-index: 10000; background: rgba(0,0,0,0.92); backdrop-filter: blur(10px);
  display: none; align-items: flex-start; justify-content: center; padding-top: 15vh;
}
.spotlight-overlay.active { display: flex; animation: spotIn 0.2s ease; }
@keyframes spotIn { from { opacity: 0; } to { opacity: 1; } }
.spotlight-box { width: 100%; max-width: 700px; margin: 0 1rem; }
.spotlight-input-wrap { position: relative; margin-bottom: 1rem; }
.spotlight-input {
  width: 100%; padding: 1.2rem 1.5rem 1.2rem 3.5rem; background: rgba(42,42,42,0.9);
  border: 2px solid var(--gold); border-radius: 16px; color: var(--white);
  font-family: 'Montserrat', sans-serif; font-size: 1.2rem; backdrop-filter: blur(10px);
  box-shadow: 0 10px 60px rgba(197,160,89,0.2);
}
.spotlight-input:focus { outline: none; }
.spotlight-icon { position: absolute; left: 1.2rem; top: 50%; transform: translateY(-50%); font-size: 1.4rem; color: var(--gold); }
.spotlight-close {
  position: absolute; top: 2rem; right: 2rem; background: none; border: none; color: var(--gold);
  font-size: 2rem; cursor: pointer; transition: transform 0.3s;
}
.spotlight-close:hover { transform: rotate(90deg); }
.spotlight-results { max-height: 50vh; overflow-y: auto; background: rgba(26,26,26,0.95); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 0.5rem; }
.spotlight-item { display: flex; align-items: center; gap: 1rem; padding: 0.9rem 1rem; text-decoration: none; border-bottom: 1px solid rgba(197,160,89,0.06); transition: all 0.2s; border-radius: 8px; }
.spotlight-item:hover { background: rgba(197,160,89,0.12); }
.spotlight-item img { width: 55px; height: 55px; object-fit: cover; border-radius: 10px; border: 1px solid rgba(197,160,89,0.2); }
.spotlight-item-info { flex: 1; }
.spotlight-item-name { color: var(--white); font-weight: 600; font-size: 0.95rem; display: block; }
.spotlight-item-cat { color: rgba(245,245,245,0.5); font-size: 0.8rem; }

/* BREADCRUMBS */
.breadcrumbs {
  display: flex; align-items: center; gap: 0.5rem; justify-content: center;
  padding: 1rem 2rem; flex-wrap: wrap; font-size: 0.75rem; color: rgba(245,245,245,0.5); text-transform: uppercase; letter-spacing: 1px;
}
.breadcrumbs a { color: var(--gold); text-decoration: none; transition: opacity 0.3s; }
.breadcrumbs a:hover { opacity: 0.7; }
.breadcrumbs span { color: rgba(245,245,245,0.3); }

/* CAT NAV (prev/next) */
.cat-nav { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 2rem 3rem; gap: 1rem; }
.cat-nav-btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.5rem; background: rgba(42,42,42,0.6); border: 1px solid rgba(197,160,89,0.2); color: var(--gold); text-decoration: none; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; border-radius: 8px; transition: all 0.3s; }
.cat-nav-btn:hover { background: var(--gold); color: var(--black); border-color: var(--gold); }
.cat-nav-btn.next { margin-left: auto; }

/* MOBILE BOTTOM NAV */
.mobile-bottom-nav {
  display: none; position: fixed; bottom: 0; left: 0; right: 0; z-index: 9997;
  background: rgba(15,15,15,0.95); backdrop-filter: blur(12px);
  border-top: 1px solid rgba(197,160,89,0.15); padding: 0.6rem 0;
}
.mobile-bottom-nav a {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 0.2rem;
  color: rgba(245,245,245,0.5); text-decoration: none; font-size: 0.65rem; font-weight: 600; letter-spacing: 1px; transition: color 0.3s;
}
.mobile-bottom-nav a.active, .mobile-bottom-nav a:hover { color: var(--gold); }
.mobile-bottom-nav a span:first-child { font-size: 1.2rem; }

/* HEADER SEARCH MEJORADO */
.search-box input { width: 220px; border-width: 2px; font-size: 0.85rem; padding: 0.55rem 2.5rem 0.55rem 1.1rem; }
.search-box input:focus { width: 320px; border-color: var(--gold); box-shadow: 0 0 20px rgba(197,160,89,0.2); }

/* MOBILE */
@media (max-width: 768px) {
  .mega-menu, .nav-dropdown { display: none; }
  .search-box input { width: 160px; }
  .search-box input:focus { width: 220px; }
  .search-dropdown { width: calc(100vw - 40px); right: auto; left: -20px; }
  .mobile-bottom-nav { display: flex; }
  .cat-nav { flex-direction: column; }
  .spotlight-box { padding-top: 10vh; }
  .desktop-nav { display: none; }
  .menu-btn { display: block; }
  .hero-home h1 { font-size: 2.2rem; }
  .hero-content img { height: 100px; }
  .products-grid { grid-template-columns: 1fr; }
  .cat-grid { grid-template-columns: 1fr; }
  .info-grid { grid-template-columns: 1fr; }
  .header-inner { padding: 0.8rem 1rem; }
  .whatsapp-float { width: 50px; height: 50px; font-size: 1.5rem; }
  .wa-tooltip { display: none; }
  .chatbot-float { width: 50px; height: 50px; font-size: 1.5rem; }
  .chatbot-window { width: calc(100vw - 40px); left: 20px; }
  .stat-number { font-size: 2rem; }
  .hero-cat-bg { min-height: 45vh; }
  .hero-cat-actions { flex-direction: column; gap: 0.8rem; }
  .hero-cat-actions .btn-primary { width: 100%; }
  .product-gallery { height: 300px; }
  .wa-modal-box { margin: 1rem; padding: 1.4rem; }
  .wa-modal-row { grid-template-columns: 1fr; }
  .sticky-cta-bar { grid-template-columns: 1fr auto; padding: 0.6rem 0.8rem; }
  .sticky-cta-bar a { padding: 0.65rem 0.7rem; font-size: 0.78rem; }
  .cat-filters { padding: 0 1rem; }
  .cat-filters-inner { padding: 1rem; }
  .cat-filter-search { padding: 0.7rem 0.8rem; font-size: 0.85rem; }
  body { padding-bottom: 80px; }
}

/* PRODUCTO DESTACADO - PVC MARMOL */
.featured-product-section { padding: 5rem 2rem; background: linear-gradient(135deg, rgba(15,15,15,0.97) 0%, rgba(26,26,26,0.95) 100%); position: relative; overflow: hidden; }
.featured-product-section::before { content: ''; position: absolute; top: -50%; right: -20%; width: 600px; height: 600px; background: radial-gradient(circle, rgba(197,160,89,0.08) 0%, transparent 70%); border-radius: 50%; pointer-events: none; }
.featured-product-wrap { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; }
.featured-product-image { position: relative; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
.featured-product-image img { width: 100%; height: 100%; object-fit: cover; display: block; }
.featured-product-image::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(15,15,15,0.6) 0%, transparent 50%); }
.featured-product-badge { position: absolute; top: 1rem; left: 1rem; background: var(--gold); color: var(--black); padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; z-index: 2; }
.featured-product-content h3 { font-family: 'Playfair Display', serif; font-size: 2.2rem; color: var(--gold-light); margin-bottom: 0.5rem; }
.featured-product-content .subtitle { color: rgba(245,245,245,0.6); font-size: 0.95rem; margin-bottom: 1.5rem; font-weight: 300; }
.featured-product-content p { color: rgba(245,245,245,0.85); line-height: 1.8; margin-bottom: 1.2rem; font-size: 0.92rem; }
.featured-product-features { list-style: none; margin: 1.5rem 0; }
.featured-product-features li { display: flex; align-items: flex-start; gap: 0.7rem; margin-bottom: 0.8rem; color: rgba(245,245,245,0.8); font-size: 0.9rem; }
.featured-product-features li::before { content: '✓'; color: var(--gold); font-weight: 700; flex-shrink: 0; }
.featured-product-cta { display: inline-flex; align-items: center; gap: 0.5rem; background: var(--gold); color: var(--black); padding: 0.85rem 2rem; border-radius: 30px; text-decoration: none; font-weight: 600; font-size: 0.9rem; margin-top: 1rem; transition: all 0.3s ease; }
.featured-product-cta:hover { background: var(--gold-light); transform: translateY(-2px); }
@media (max-width: 768px) { .featured-product-wrap { grid-template-columns: 1fr; gap: 2rem; } .featured-product-content h3 { font-size: 1.7rem; } }

/* RESEARCH SECTIONS - FAQs y Datos Curiosos */
.research-section { padding: 4rem 2rem; max-width: 1100px; margin: 0 auto; }
.research-content { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
.research-item { background: rgba(255,255,255,0.03); border: 1px solid rgba(197,160,89,0.12); border-radius: 12px; padding: 1.5rem; transition: all 0.3s ease; }
.research-item:hover { border-color: rgba(197,160,89,0.3); transform: translateY(-3px); background: rgba(255,255,255,0.05); }
.research-item p { color: rgba(245,245,245,0.8); font-size: 0.88rem; line-height: 1.7; margin-bottom: 0.5rem; }
.research-item p strong { color: var(--gold-light); }
.research-item h3, .research-item h4 { color: var(--gold); font-size: 1rem; margin-bottom: 0.6rem; font-family: 'Montserrat', sans-serif; }
.research-faqs { display: flex; flex-direction: column; gap: 1rem; }
.faq-item { background: rgba(255,255,255,0.03); border: 1px solid rgba(197,160,89,0.12); border-radius: 12px; padding: 1.2rem 1.5rem; }
.faq-question { color: var(--gold-light); font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem; }
.faq-answer { color: rgba(245,245,245,0.75); font-size: 0.87rem; line-height: 1.7; }
@media (max-width: 768px) { .research-content { grid-template-columns: 1fr; } }

/* REAL SHEETS GALLERY */
.real-sheets-section { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
.real-sheets-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.real-sheets-item { border-radius: 12px; overflow: hidden; position: relative; aspect-ratio: 3/4; cursor: pointer; }
.real-sheets-item img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }
.real-sheets-item:hover img { transform: scale(1.08); }
.real-sheets-item::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(15,15,15,0.5) 0%, transparent 40%); opacity: 0; transition: opacity 0.3s ease; }
.real-sheets-item:hover::after { opacity: 1; }
.real-sheets-badge { position: absolute; bottom: 1rem; left: 1rem; background: var(--gold); color: var(--black); padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; z-index: 2; }
@media (max-width: 768px) { .real-sheets-grid { grid-template-columns: repeat(2, 1fr); } }

/* SABIAS QUE - PAGINA INTERACTIVA */
.sq-hero { padding: 8rem 2rem 3rem; text-align: center; background: linear-gradient(135deg, rgba(15,15,15,0.95) 0%, rgba(26,26,26,0.9) 100%); position: relative; }
.sq-hero h1 { font-family: 'Playfair Display', serif; font-size: 2.8rem; color: var(--gold-light); margin-bottom: 0.6rem; }
.sq-hero p { color: rgba(245,245,245,0.5); font-size: 1rem; max-width: 500px; margin: 0 auto; }

.sq-tabs { display: flex; justify-content: center; gap: 0.5rem; padding: 1.5rem 1rem; flex-wrap: wrap; max-width: 1100px; margin: 0 auto; border-bottom: 1px solid rgba(197,160,89,0.1); }
.sq-tab { background: transparent; border: 1px solid rgba(197,160,89,0.15); color: rgba(245,245,245,0.6); padding: 0.5rem 1.2rem; border-radius: 20px; cursor: pointer; font-family: 'Montserrat', sans-serif; font-size: 0.8rem; font-weight: 500; transition: all 0.3s ease; }
.sq-tab:hover { border-color: var(--gold); color: var(--gold-light); }
.sq-tab.active { background: var(--gold); color: var(--black); border-color: var(--gold); font-weight: 600; }

.sq-content { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem 3rem; }
.sq-panel { display: none; }
.sq-panel.active { display: block; animation: sqFadeIn 0.4s ease; }
@keyframes sqFadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Hero imagen por categoria */
.sq-cat-hero { height: 220px; border-radius: 16px; margin: 1.5rem 0; background-size: cover; background-position: center; position: relative; overflow: hidden; }
.sq-cat-overlay { position: absolute; inset: 0; background: linear-gradient(to top, rgba(15,15,15,0.9) 0%, rgba(15,15,15,0.3) 60%, transparent 100%); display: flex; align-items: flex-end; padding: 1.5rem; }
.sq-cat-overlay h2 { color: var(--gold-light); font-family: 'Playfair Display', serif; font-size: 1.6rem; margin: 0; }

.sq-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
@media (max-width: 900px) { .sq-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .sq-grid { grid-template-columns: 1fr; } }

.sq-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(197,160,89,0.1); border-radius: 14px; padding: 1.4rem; position: relative; overflow: hidden; transition: all 0.35s ease; text-align: center; }
.sq-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gold); transform: scaleX(0); transition: transform 0.35s ease; }
.sq-card:hover { border-color: rgba(197,160,89,0.3); transform: translateY(-5px); box-shadow: 0 12px 30px rgba(0,0,0,0.25); }
.sq-card:hover::before { transform: scaleX(1); }
.sq-card-icon { font-size: 2rem; margin-bottom: 0.6rem; display: block; }
.sq-card h3 { color: var(--gold-light); font-size: 0.92rem; margin-bottom: 0.5rem; font-family: 'Montserrat', sans-serif; font-weight: 600; line-height: 1.4; }
.sq-card p { color: rgba(245,245,245,0.6); font-size: 0.82rem; line-height: 1.6; margin: 0; }
.sq-card-number { position: absolute; top: 0.8rem; right: 1rem; font-size: 2rem; font-weight: 800; color: rgba(255,255,255,0.25); font-family: 'Playfair Display', serif; line-height: 1; }
.sq-card-readmore { color: var(--gold); font-size: 0.75rem; cursor: pointer; margin-top: 0.4rem; display: inline-block; font-weight: 600; transition: color 0.2s; border-bottom: 1px dotted rgba(197,160,89,0.4); }
.sq-card-readmore:hover { color: var(--gold-light); border-bottom-color: var(--gold); }
.sq-short, .sq-full { display: inline; }

/* FAQ Acordeon */
.sq-faqs { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.8rem; }
@media (max-width: 768px) { .sq-faqs { grid-template-columns: 1fr; } }
.sq-faq-item { background: rgba(255,255,255,0.03); border: 1px solid rgba(197,160,89,0.08); border-radius: 10px; overflow: hidden; }
.sq-faq-q { padding: 1rem 1.2rem; color: var(--gold-light); font-weight: 600; font-size: 0.88rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.3s; }
.sq-faq-q:hover { background: rgba(197,160,89,0.04); }
.sq-faq-q::after { content: '+'; font-size: 1.2rem; color: var(--gold); transition: transform 0.3s; flex-shrink: 0; margin-left: 0.5rem; }
.sq-faq-item.open .sq-faq-q::after { transform: rotate(45deg); }
.sq-faq-a { max-height: 0; overflow: hidden; transition: max-height 0.35s ease, padding 0.35s ease; padding: 0 1.2rem; color: rgba(245,245,245,0.65); font-size: 0.82rem; line-height: 1.6; }
.sq-faq-item.open .sq-faq-a { max-height: 400px; padding: 0 1.2rem 1rem; }

@media (max-width: 768px) { .sq-hero h1 { font-size: 2.2rem; } .sq-cat-hero { height: 160px; } .sq-tab { padding: 0.4rem 0.9rem; font-size: 0.75rem; } }

/* Index de Sabias Que */
.sq-index-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; padding: 1.5rem 0 3rem; }
@media (max-width: 900px) { .sq-index-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .sq-index-grid { grid-template-columns: 1fr; } }
.sq-index-card { display: block; background: rgba(255,255,255,0.03); border: 1px solid rgba(197,160,89,0.1); border-radius: 16px; overflow: hidden; text-decoration: none; transition: all 0.35s ease; }
.sq-index-card:hover { border-color: rgba(197,160,89,0.35); transform: translateY(-6px); box-shadow: 0 16px 40px rgba(0,0,0,0.3); }
.sq-index-img { height: 160px; background-size: cover; background-position: center; }
.sq-index-info { padding: 1.2rem; }
.sq-index-info h3 { color: var(--gold-light); font-size: 1rem; font-family: 'Montserrat', sans-serif; font-weight: 600; margin-bottom: 0.4rem; }
.sq-index-info span { color: var(--gold); font-size: 0.8rem; }

/* Sección de descargas de catálogos PDF */
.downloads-section { background: linear-gradient(180deg, rgba(197,160,89,0.06) 0%, transparent 100%); }
.downloads-lead { max-width: 650px; margin: 0 auto 3rem; text-align: center; color: rgba(245,245,245,0.75); font-size: 1.05rem; line-height: 1.7; }
.downloads-main { display: flex; justify-content: center; margin-bottom: 3.5rem; }
.download-complete { display: inline-flex; align-items: center; gap: 1.2rem; background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%); color: var(--black); padding: 1.3rem 2.6rem; border-radius: 16px; text-decoration: none; font-weight: 800; font-size: 1.15rem; transition: all 0.35s ease; box-shadow: 0 10px 32px rgba(197,160,89,0.3); position: relative; overflow: hidden; }
.download-complete::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent); transition: left 0.6s ease; }
.download-complete:hover { transform: translateY(-5px) scale(1.02); box-shadow: 0 18px 44px rgba(197,160,89,0.4); }
.download-complete:hover::before { left: 100%; }
.download-complete .icon { font-size: 2rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2)); }
.download-complete .sub { display: block; font-size: 0.78rem; font-weight: 600; opacity: 0.8; margin-top: 3px; }
.download-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.4rem; max-width: 1200px; margin: 0 auto; }
.download-card { display: flex; align-items: center; gap: 1.1rem; background: linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%); border: 1px solid rgba(197,160,89,0.15); border-radius: 16px; padding: 1.2rem 1.4rem; text-decoration: none; transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; }
.download-card::after { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 80% 20%, rgba(197,160,89,0.08) 0%, transparent 50%); opacity: 0; transition: opacity 0.35s ease; pointer-events: none; }
.download-card:hover { background: linear-gradient(145deg, rgba(197,160,89,0.1) 0%, rgba(197,160,89,0.03) 100%); border-color: rgba(197,160,89,0.45); transform: translateY(-5px) scale(1.01); box-shadow: 0 14px 34px rgba(0,0,0,0.3), 0 0 0 1px rgba(197,160,89,0.1); }
.download-card:hover::after { opacity: 1; }
.download-card .icon { font-size: 2.4rem; flex-shrink: 0; filter: drop-shadow(0 3px 6px rgba(0,0,0,0.25)); transition: transform 0.35s ease; }
.download-card:hover .icon { transform: scale(1.15) rotate(-5deg); }
.download-card .info { flex: 1; min-width: 0; }
.download-card .info h4 { color: var(--white); font-size: 1.05rem; font-weight: 700; margin-bottom: 0.25rem; letter-spacing: 0.2px; }
.download-card .info span { color: var(--gold); font-size: 0.78rem; font-weight: 600; }
.download-card .arrow { color: var(--gold); font-size: 1.3rem; transition: all 0.35s ease; background: rgba(197,160,89,0.1); width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.download-card:hover .arrow { background: var(--gold); color: var(--black); transform: translateY(3px); }
@media (max-width: 600px) { .download-complete { width: 100%; justify-content: center; padding: 1.1rem 1.5rem; font-size: 1rem; } .download-grid { grid-template-columns: 1fr; gap: 1rem; } .download-card { padding: 1rem 1.2rem; } .download-card .icon { font-size: 2rem; } }
'''


def generate_style():
    """Escribe el CSS completo en style.css."""
    css_path = BASE_DIR / 'style.css'
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(CSS.strip())
    print(f"  style.css generado ({len(CSS):,} caracteres)")


# ========== PARTICLES JS ==========
PARTICLES_JS = '''(function() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w, h, particles = [];
  const COUNT = 70;
  const CONNECT_DIST = 140;
  const COLOR = 'rgba(197, 160, 89, ';
  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();
  class Particle {
    constructor() {
      this.x = Math.random() * w;
      this.y = Math.random() * h;
      this.vx = (Math.random() - 0.5) * 0.5;
      this.vy = (Math.random() - 0.5) * 0.5;
      this.r = Math.random() * 2.5 + 0.8;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > w) this.vx *= -1;
      if (this.y < 0 || this.y > h) this.vy *= -1;
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = COLOR + '0.6)';
      ctx.fill();
    }
  }
  for (let i = 0; i < COUNT; i++) particles.push(new Particle());
  function animate() {
    ctx.clearRect(0, 0, w, h);
    for (let p of particles) { p.update(); p.draw(); }
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        let dx = particles[i].x - particles[j].x;
        let dy = particles[i].y - particles[j].y;
        let dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < CONNECT_DIST) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = COLOR + (0.2 * (1 - dist/CONNECT_DIST)) + ')';
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(animate);
  }
  animate();
})();'''


# ========== WHATSAPP & COTIZACIÓN HELPERS ==========

def whatsapp_url(phone, message):
    """Construye URL de WhatsApp con mensaje prellenado y seguro."""
    import urllib.parse
    return 'https://wa.me/' + phone + '?text=' + urllib.parse.quote(message, safe='')


def build_whatsapp_message(product, category, subcategory=None, nombre='', ciudad='', metros='', uso='', comentario=''):
    """Construye mensaje enriquecido para cotización por WhatsApp."""
    lines = ['Hola ADIS, soy ' + (nombre or 'un cliente interesado') + '. Me interesa cotizar:']
    lines.append('Producto: ' + product)
    lines.append('Categoría: ' + category)
    if subcategory:
        lines.append('Subcategoría: ' + subcategory)
    if ciudad:
        lines.append('Ubicación de la obra: ' + ciudad)
    if metros:
        lines.append('Metros cuadrados aproximados: ' + metros)
    if uso:
        lines.append('Uso: ' + uso)
    if comentario:
        lines.append('Comentario: ' + comentario)
    lines.append('Favor de contactarme para más detalles. ¡Gracias!')
    return '\n'.join(lines)


# ========== SCHEMA.ORG / SEO ==========
def json_ld(data):
    """Envuelve un diccionario en un script JSON-LD."""
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False, indent=2)}</script>'


def organization_schema():
    """Schema.org de Organization + LocalBusiness para ADIS."""
    return json_ld({
        "@context": "https://schema.org",
        "@type": ["Organization", "LocalBusiness"],
        "@id": f"{SITE_URL}#organization",
        "name": "ADIS Diseño & Remodelación",
        "alternateName": "ADIS",
        "url": SITE_URL,
        "logo": f"{SITE_URL}LOGO%20ADIS.png",
        "image": f"{SITE_URL}LOGO%20ADIS.png",
        "telephone": CONTACTO["tel_mx"],
        "email": CONTACTO["email"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": CONTACTO.get("direccion", ""),
            "addressLocality": "Heroica Nogales",
            "addressRegion": "Sonora",
            "postalCode": "84000",
            "addressCountry": "MX"
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": "31.3014",
            "longitude": "-110.9386"
        },
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "opens": "10:00",
                "closes": "19:00"
            },
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": "Sunday",
                "opens": "10:00",
                "closes": "19:00"
            }
        ],
        "sameAs": [
            CONTACTO["facebook"]
        ],
        "priceRange": "$"
    })


def website_schema():
    """Schema.org de WebSite con buscador integrado."""
    return json_ld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "ADIS Diseño & Remodelación",
        "url": SITE_URL,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{SITE_URL}?q={{search_term_string}}"
            },
            "query-input": "required name=search_term_string"
        }
    })


def breadcrumb_schema(items):
    """Schema.org de BreadcrumbList.
    items: lista de tuplas (nombre, url).
    """
    return json_ld({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url
            }
            for i, (name, url) in enumerate(items)
        ]
    })


def product_schema(name, category, subcategory, image, url, description=''):
    """Schema.org de Product para una tarjeta de producto.
    No incluye precio porque la política es cotizar por WhatsApp.
    """
    cat_path = category + (f" > {subcategory}" if subcategory else "")
    return json_ld({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "image": image,
        "url": url,
        "brand": {
            "@type": "Brand",
            "name": "ADIS Diseño & Remodelación"
        },
        "category": cat_path,
        "description": description or f"{name} de {cat_path}. Disponible en ADIS Diseño & Remodelación. Cotiza por WhatsApp.",
        "availability": "https://schema.org/InStock"
    })


def faqpage_schema(faqs):
    """Schema.org de FAQPage.
    faqs: lista de tuplas (pregunta, respuesta).
    """
    return json_ld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            }
            for q, a in faqs
        ]
    })


def generate_sitemap(categories):
    """Genera sitemap.xml con todas las URLs públicas."""
    urls = [
        SITE_URL,
        f"{SITE_URL}contacto.html",
        f"{SITE_URL}proyectos.html",
        f"{SITE_URL}sabias-que.html",
    ]
    for cat in categories:
        urls.append(f"{SITE_URL}{cat['filename']}")
    for cat_name in RESEARCH_DATA.keys():
        sq_slug = SABIAS_QUE_SLUGS.get(cat_name, 'otros')
        urls.append(f"{SITE_URL}sabias-que-{sq_slug}.html")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
    xml += '</urlset>'

    sitemap_path = BASE_DIR / 'sitemap.xml'
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(xml)
    print("  sitemap.xml generado")


def generate_robots():
    """Genera robots.txt con referencia al sitemap."""
    content = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n"
    robots_path = BASE_DIR / 'robots.txt'
    with open(robots_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  robots.txt generado")


def modal_cotizar_html():
    """Modal único de cotización por WhatsApp. Se inyecta una vez por página."""
    return '''
  <!-- MODAL COTIZAR WHATSAPP -->
  <div class="wa-modal" id="waModal" onclick="closeWaModal(event)">
    <div class="wa-modal-box" onclick="event.stopPropagation()">
      <button class="wa-modal-close" onclick="closeWaModal()">&#10005;</button>
      <h3>Cotizar por WhatsApp</h3>
      <p class="wa-modal-subtitle">Completa tus datos y te responderemos con información y asesoría.</p>
      <form id="waModalForm" onsubmit="sendWaModal(event)">
        <input type="hidden" id="waModalProduct" value="">
        <input type="hidden" id="waModalCategory" value="">
        <input type="hidden" id="waModalSubcategory" value="">
        <div class="wa-modal-field">
          <label for="waModalNombre">Nombre *</label>
          <input type="text" id="waModalNombre" placeholder="Tu nombre" required>
        </div>
        <div class="wa-modal-field">
          <label for="waModalCiudad">Ciudad / Ubicación de la obra *</label>
          <input type="text" id="waModalCiudad" placeholder="Ej. Nogales, Sonora" required>
        </div>
        <div class="wa-modal-row">
          <div class="wa-modal-field">
            <label for="waModalMetros">m2 aproximados</label>
            <input type="number" id="waModalMetros" placeholder="Ej. 25" min="1" step="0.1">
          </div>
          <div class="wa-modal-field">
            <label for="waModalUso">Uso</label>
            <select id="waModalUso">
              <option value="Residencial">Residencial</option>
              <option value="Comercial">Comercial</option>
              <option value="Otro">Otro</option>
            </select>
          </div>
        </div>
        <div class="wa-modal-field">
          <label for="waModalComentario">Comentario (opcional)</label>
          <textarea id="waModalComentario" rows="3" placeholder="¿Alguna duda o requerimiento especial?"></textarea>
        </div>
        <div class="wa-modal-product" id="waModalProductLabel"></div>
        <button type="submit" class="wa-modal-submit">Enviar a WhatsApp</button>
      </form>
    </div>
  </div>
  <script>
    function openWaModal(product, category, subcategory) {
      document.getElementById('waModalProduct').value = product || '';
      document.getElementById('waModalCategory').value = category || '';
      document.getElementById('waModalSubcategory').value = subcategory || '';
      document.getElementById('waModalProductLabel').textContent = product + (subcategory ? ' - ' + subcategory : '');
      document.getElementById('waModal').classList.add('active');
      setTimeout(function() { document.getElementById('waModalNombre').focus(); }, 100);
    }
    function closeWaModal(e) {
      if (e && e.target !== e.currentTarget) return;
      document.getElementById('waModal').classList.remove('active');
    }
    function sendWaModal(e) {
      e.preventDefault();
      var phone = '15208392877';
      var product = document.getElementById('waModalProduct').value;
      var category = document.getElementById('waModalCategory').value;
      var subcategory = document.getElementById('waModalSubcategory').value;
      var nombre = document.getElementById('waModalNombre').value.trim();
      var ciudad = document.getElementById('waModalCiudad').value.trim();
      var metros = document.getElementById('waModalMetros').value.trim();
      var uso = document.getElementById('waModalUso').value;
      var comentario = document.getElementById('waModalComentario').value.trim();
      var msg = `Hola ADIS, soy ${nombre || 'un cliente interesado'}. Me interesa cotizar:
Producto: ${product}
Categoria: ${category}`;
      if (subcategory) msg += `\nSubcategoria: ${subcategory}`;
      if (ciudad) msg += `\nUbicacion de la obra: ${ciudad}`;
      if (metros) msg += `\nMetros cuadrados aproximados: ${metros}`;
      msg += `\nUso: ${uso}`;
      if (comentario) msg += `\nComentario: ${comentario}`;
      msg += `\nFavor de contactarme para mas detalles. ¡Gracias!`;
      window.open('https://wa.me/' + phone + '?text=' + encodeURIComponent(msg), '_blank');
      closeWaModal();
      e.target.reset();
    }
  </script>
'''


def _extract_keywords(name):
    """Extrae palabras clave normalizadas de un nombre de producto."""
    name_norm = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII').lower()
    tokens = re.findall(r'[a-z]+', name_norm)
    stopwords = {'de', 'del', 'la', 'el', 'en', 'y', 'o', 'con', 'sin', 'para', 'por', 'un', 'una', 'los', 'las'}
    return [t for t in tokens if t not in stopwords and len(t) > 2]


def category_filters_html(cat):
    """Genera panel de filtros facetados para una categoría."""
    chips = ['<button class="filter-chip active" data-subcategory="all">Todos</button>']
    for sub in cat["subcategories"]:
        if sub["products"]:
            chips.append(f'<button class="filter-chip" data-subcategory="{sub["name"].lower()}">{sub["name"]}</button>')
    has_direct = bool(cat["direct_products"])
    if has_direct:
        chips.append('<button class="filter-chip" data-subcategory="general">General</button>')
    if not cat["subcategories"] and not has_direct:
        return ''
    total = len(cat["direct_products"]) + sum(len(s["products"]) for s in cat["subcategories"])
    return f'''  <!-- FILTROS FACETADOS -->
  <section class="cat-filters reveal">
    <div class="cat-filters-inner">
      <input type="text" class="cat-filter-search" id="catFilterSearch" placeholder="Buscar producto..." autocomplete="off">
      <div class="cat-filter-chips">
        {''.join(chips)}
      </div>
      <div class="cat-filter-count" id="catFilterCount">{total} productos</div>
    </div>
  </section>
'''


def category_filters_js():
    """JavaScript para manejar los filtros facetados de categoría."""
    return '''
  <script>
    (function() {
      const search = document.getElementById('catFilterSearch');
      if (!search) return;
      const chips = document.querySelectorAll('.filter-chip');
      const cards = document.querySelectorAll('.product-card');
      const countEl = document.getElementById('catFilterCount');
      let activeSubcategory = 'all';
      function normalize(str) {
        return (str || '').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
      }
      function filter() {
        const term = normalize(search.value);
        let visible = 0;
        cards.forEach(function(card) {
          const name = normalize(card.dataset.name);
          const sub = card.dataset.subcategory || '';
          const keywords = normalize(card.dataset.keywords);
          const matchSearch = name.indexOf(term) !== -1 || keywords.indexOf(term) !== -1;
          const matchSub = activeSubcategory === 'all' || sub === activeSubcategory;
          const show = matchSearch && matchSub;
          card.style.display = show ? '' : 'none';
          if (show) visible++;
        });
        document.querySelectorAll('.subcat-section').forEach(function(sec) {
          const visibleCards = sec.querySelectorAll('.product-card:not([style*="display: none"])');
          sec.style.display = visibleCards.length ? '' : 'none';
        });
        if (countEl) countEl.textContent = visible + ' producto' + (visible !== 1 ? 's' : '');
      }
      search.addEventListener('input', filter);
      chips.forEach(function(chip) {
        chip.addEventListener('click', function() {
          activeSubcategory = chip.dataset.subcategory;
          chips.forEach(function(c) { c.classList.remove('active'); });
          chip.classList.add('active');
          filter();
        });
      });
    })();
  </script>'''


def product_card_html(prod_file, cat, sub=None):
    """Genera tarjeta de producto con CTA unificado a WhatsApp via modal."""
    prod_name = os.path.splitext(prod_file)[0]
    img_path = "img/{cat_slug}/{sub_slug}/{prod_file}".format(
        cat_slug=cat["slug"],
        sub_slug=sub["slug"] if sub else "",
        prod_file=prod_file
    ) if sub else "img/{cat_slug}/{prod_file}".format(cat_slug=cat["slug"], prod_file=prod_file)
    sub_name = sub["name"] if sub else None
    sub_arg = "'" + sub_name + "'" if sub_name else "null"
    cat_name = cat["name"]
    sub_name_lower = sub_name.lower() if sub_name else 'general'
    keywords = ' '.join(_extract_keywords(prod_name))
    return '''      <div class="product-card reveal" data-name="{prod_name_lower}" data-category="{cat_name}" data-subcategory="{sub_name_lower}" data-keywords="{keywords}">
        <div class="product-gallery" onclick="openLightbox('{img_path}', '{prod_name}')">
          <img src="{img_path}" alt="{prod_name}" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">{prod_name}</div>
          <div class="product-actions">
            <button type="button" class="btn-cotizar" onclick="openWaModal('{prod_name}', '{cat_name}', {sub_arg})">Cotizar por WhatsApp</button>
          </div>
        </div>
      </div>
'''.format(
        prod_name=prod_name,
        prod_name_lower=prod_name.lower(),
        cat_name=cat_name,
        img_path=img_path,
        sub_arg=sub_arg,
        sub_name_lower=sub_name_lower,
        keywords=keywords
    )


def generate_header(current_page='index'):
    """Genera el header HTML con mega-menu y search mejorado."""
    
    MEGA_ITEMS = [
        ('1-placas-pvc.html', 'img/1-placas-pvc/11-placas-pvc-tipo-madera/Adler.jpg', 'Placas PVC'),
        ('2-lambrin-wpc.html', 'img/2-lambrin-wpc/21-lambrin-interior/AMANECHER.jpg', 'Lambrín WPC'),
        ('3-revestimiento-flexible.html', 'img/3-revestimiento-flexible/CONCRETO%20Aparente.jpg', 'Revestimiento Flexible'),
        ('4-plafon-pvc.html', 'img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg', 'Plafón PVC'),
        ('5-paneles-tridimensionales.html', 'img/5-paneles-tridimensionales/51-blanco/Austin.jpg', 'Paneles 3D'),
        ('6-vigas-pvc.html', 'img/6-vigas-pvc/61-interior/BAHIA%201.jpg', 'Vigas PVC'),
        ('7-pisos.html', 'img/7-pisos/71-laminado/ACONCAGUA.jpg', 'Pisos'),
        ('8-zacate.html', 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg', 'Zacate'),
        ('9-cladding.html', 'img/9-cladding/91-placa-tipo-roca/BLACK.jpg', 'Cladding'),
    ]
    mega_html = '\n'.join([f'        <a href="{u}" class="mega-item"><img src="{i}" alt="{t}" loading="lazy"><span>{t}</span></a>' for u, i, t in MEGA_ITEMS])
    
    SABIAS_ITEMS = [
        ('sabias-que-pvc.html', '🔬', 'Placas PVC'),
        ('sabias-que-wpc.html', '🌲', 'Lambrín WPC'),
        ('sabias-que-revestimiento.html', '🪨', 'Revestimiento Flexible'),
        ('sabias-que-plafon.html', '&#127968;', 'Plafón PVC'),
        ('sabias-que-3d.html', '🎨', 'Paneles 3D'),
        ('sabias-que-vigas.html', '📐', 'Vigas PVC/WPC/PU'),
        ('sabias-que-pisos.html', '🏗️', 'Pisos'),
        ('sabias-que-zacate.html', '🌿', 'Zacate Sintético'),
        ('sabias-que-cladding.html', '⛰️', 'Cladding'),
    ]
    sabias_html = '\n'.join([f'        <a href="{u}" class="dropdown-item"><span class="dropdown-icon">{i}</span><span>{t}</span></a>' for u, i, t in SABIAS_ITEMS])
    
    nav_links = '<a href="index.html">Inicio</a>\n        <a href="index.html#categorias" class="mega-trigger">Catálogo\n          <div class="mega-menu">\n' + mega_html + '\n          </div>\n        </a>\n        <a href="sabias-que.html" class="mega-trigger">¿Sabías que?\n          <div class="nav-dropdown">\n' + sabias_html + '\n          </div>\n        </a>\n        <a href="proyectos.html">Proyectos</a>\n        <a href="contacto.html">Contacto</a>'
    if current_page != 'index':
        nav_links = '<a href="index.html">← Inicio</a>\n        <a href="index.html#categorias" class="mega-trigger">Catálogo\n          <div class="mega-menu">\n' + mega_html + '\n          </div>\n        </a>\n        <a href="sabias-que.html" class="mega-trigger">¿Sabías que?\n          <div class="nav-dropdown">\n' + sabias_html + '\n          </div>\n        </a>\n        <a href="proyectos.html">Proyectos</a>\n        <a href="contacto.html">Contacto</a>'

    return f'''  <header>
    <div class="header-inner">
      <a href="index.html" class="logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></a>
      <nav class="desktop-nav">
        {nav_links}
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Buscar producto..." autocomplete="off" title="Presiona / para buscar">
          <button onclick="openSpotlight()">&#128269;</button>
          <div class="search-dropdown" id="searchDropdown"></div>
        </div>
      </nav>
      <button class="menu-btn" onclick="toggleMenu()">&#9776;</button>
    </div>
  </header>

  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">&#10005;</button>
    <a href="index.html" onclick="toggleMenu()">Inicio</a>
    <a href="index.html#categorias" onclick="toggleMenu()">Catálogo</a>
    <a href="sabias-que.html" onclick="toggleMenu()">¿Sabías que?</a>
    <a href="proyectos.html" onclick="toggleMenu()">Proyectos</a>
    <a href="contacto.html" onclick="toggleMenu()">Contacto</a>
    <div class="search-box" style="margin-top:1rem;">
      <input type="text" id="searchInputMobile" placeholder="Buscar producto..." autocomplete="off" style="width:220px;">
      <button onclick="performSearchMobile()">&#128269;</button>
      <div class="search-dropdown" id="searchDropdownMobile"></div>
    </div>
  </div>
  
  <!-- SPOTLIGHT OVERLAY -->
  <div class="spotlight-overlay" id="spotlightOverlay" onclick="closeSpotlight(event)">
    <button class="spotlight-close" onclick="closeSpotlight(event)">&#10005;</button>
    <div class="spotlight-box">
      <div class="spotlight-input-wrap">
        <span class="spotlight-icon">&#128269;</span>
        <input type="text" class="spotlight-input" id="spotlightInput" placeholder="Buscar productos, categorías..." autocomplete="off">
      </div>
      <div class="spotlight-results" id="spotlightResults"></div>
    </div>
  </div>
'''


def generate_footer():
    chatbot_js = '''
  <script>
    function toggleMenu() { document.getElementById('mobileMenu').classList.toggle('active'); }
    
    // Scroll reveal
    (function() {
      const reveals = document.querySelectorAll('.reveal');
      if (!reveals.length) return;
      if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              entry.target.classList.add('active');
              io.unobserve(entry.target);
            }
          });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
        reveals.forEach(el => io.observe(el));
      } else {
        reveals.forEach(el => el.classList.add('active'));
      }
    })();
    
    // Counter animation for stats
    (function() {
      const counters = document.querySelectorAll('.stat-number[data-target]');
      if (!counters.length) return;
      const animate = function(el) {
        const target = parseInt(el.getAttribute('data-target'), 10);
        const duration = 2000;
        const start = performance.now();
        const step = function(now) {
          const progress = Math.min((now - start) / duration, 1);
          el.textContent = Math.floor(progress * target).toLocaleString();
          if (progress < 1) requestAnimationFrame(step);
          else el.textContent = target.toLocaleString();
        };
        requestAnimationFrame(step);
      };
      if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver(function(entries) {
          entries.forEach(function(entry) {
            if (entry.isIntersecting) {
              animate(entry.target);
              io.unobserve(entry.target);
            }
          });
        }, { threshold: 0.5 });
        counters.forEach(function(c) { io.observe(c); });
      } else {
        counters.forEach(animate);
      }
    })();
    
    // Chatbot Inteligente v3 - contexto, scoring, historial y tarjetas
    (function() {
      const chatWindow = document.getElementById('chatbotWindow');
      const chatBody = document.getElementById('chatbotBody');
      let allProducts = [];
      let researchData = {};
      let chatContext = loadContext();
      
      // === BASE DE CONOCIMIENTO DE PRODUCTOS ===
      // Regla clave: Nunca cambiar de producto durante la conversación, a menos que el usuario lo solicite explícitamente.
      const PRODUCT_KB = {
        placas_pvc: {
          name: 'Placas PVC',
          medidas: '2440 x 1220 x 5 mm (2.977 m² por pieza). Peso aprox. 10.5 kg/pz.',
          agua: '100% impermeables. No absorben agua, no se hinchan, no se deforman. Ideales para baños, cocinas y áreas húmedas.',
          exterior: 'No recomendadas para exterior directo. Son exclusivamente para interiores. Para exteriores recomendamos Cladding o Lambrín WPC exterior.',
          material: 'PVC rígido de alta calidad con aditivos estabilizadores UV. Superficie con acabado decorativo (madera, mármol, espejo o textura).',
          instalacion: 'Instalación en muro con adhesivo de contacto y/o clavos ocultos. La superficie debe estar limpia, seca, nivelada y desengrasada. Para placas tipo espejo se requiere perfil de aluminio obligatoriamente.',
          colores: 'Tipo madera (Adler, Solaria, Solden, Anton, etc.), Tipo mármol (Carrara, Onix, Cuarzo, Opalo, Perla, Topacio, Grafito, Jaspe, Agata, Arena, Obsidiana, etc.), Tipo espejo (dorado, plateado, metal) y Texturizadas (ASH, CEDAR, ENCINO, IPE, JATOBA, NOGAL, WENGE).',
          precio: '$850 - $1,400 MXN por pieza. Depende del modelo y acabado.',
          mantenimiento: 'Limpieza con paño suave humedecido en agua tibia y jabón neutro (pH 7). Para manchas difíciles usar alcohol isopropílico al 70%. Evitar acetona, thinner, solventes fuertes, estropajos metálicos y amoníaco concentrado.',
          usos: 'Muros interiores: cocinas, baños, salas de estar, recámaras, recepciones, muros de acento, fondos de TV, barras de cocina.',
          garantia: '15 años contra defectos de fábrica.',
          diferencias: 'Más ligero y económico que WPC. Mayor variedad de diseños decorativos que el Lambrín. No requiere barnizado ni sellado como la madera natural.'
        },
        lambrin_wpc: {
          name: 'Lambrín WPC',
          medidas: 'Interior: 219 x 26 x 3 mm (2.85 m²/caja). Exterior: 220 x 21 x 2.5 mm (3.08 m²/caja).',
          agua: 'Absorción de agua menor al 1%. No se hincha, no se cuartea, no se deforma con la humedad. Resiste lluvia, rocío y salpicaduras.',
          exterior: 'Sí, disponible en versión exterior (220 x 21 x 2.5 mm) diseñada para resistir UV, lluvia y cambios extremos de temperatura. La versión interior no debe usarse en exterior.',
          material: 'Wood Plastic Composite (WPC): 60-70% fibras de madera de alta calidad + 30-40% plástico HDPE reciclado. Aspecto natural de madera real sin el mantenimiento de esta.',
          instalacion: 'Sistema de clip oculto y/o tornillos en estructura metálica o madera tratada. No requiere adhesivo. Dejar junta de dilatación de 2-3 mm entre piezas.',
          colores: 'Interior: Amanecer, Amizade, Brasilia, Bahía, Estrelado, Fortaleza, Manaos, Nuvem, Río, Sabeiro, Sao Paulo, Sonho, Teak Aracaju, etc. Exterior: Charcoal, Dark Black, Teak, Redwood, Sliver Gray, etc.',
          precio: '$1,200 - $2,100 MXN por caja. La versión exterior es ligeramente más cara que la interior.',
          mantenimiento: 'Limpieza ocasional con agua y jabón neutro. No requiere barnizado, sellado ni pintura. Resistente a termitas y hongos.',
          usos: 'Revestimiento de muros interiores y exteriores, fachadas residenciales y comerciales, pérgolas, terrazas, cielos rasos exteriores, divisores de espacios.',
          garantia: '15 años contra defectos de fábrica.',
          diferencias: 'Aspecto más natural de madera real que las Placas PVC. Más resistente al agua que la madera natural o el MDF. Más duradero que el PVC en exteriores. No requiere mantenimiento periódico.'
        },
        revestimiento: {
          name: 'Revestimiento Flexible',
          medidas: 'Varían por modelo. Consultar ficha técnica específica.',
          agua: 'Resistente al agua y a la humedad. Ideal para zonas húmedas y exteriores protegidos.',
          exterior: 'Sí, puede usarse en exteriores protegidos. Resistente a rayos UV y cambios de temperatura moderados.',
          material: 'Polímero flexible de alta densidad con acabados que imitan concreto, piedra, ladrillo o madera.',
          instalacion: 'Adhesión con pegamento de contacto sobre superficie limpia y nivelada. Puede cortarse con tijera o cúter.',
          colores: 'Concreto aparente, concreto gris, granito blanco, granito imperial, granito oro, madera roble, entre otros.',
          precio: '$650 - $1,100 MXN por pieza.',
          mantenimiento: 'Limpieza con paño húmedo. No requiere tratamientos especiales.',
          usos: 'Muros interiores y exteriores, detalles decorativos, revestimiento de columnas, fondos de TV, barras de cocina.',
          garantia: 'Consultar ficha técnica.',
          diferencias: 'Mucho más ligero y flexible que el Cladding. Se adapta a curvas y esquinas. Más económico que la piedra real.'
        },
        plafon: {
          name: 'Plafón PVC',
          medidas: 'Laminado: 595 x 595 x 7 mm. Wood style: 250 x 8000 x 10 mm.',
          agua: '100% impermeable. No absorbe humedad, no se cuartea, no se deforma. Ideal para cocinas y baños.',
          exterior: 'No recomendado para exterior expuesto. Es para interiores.',
          material: 'PVC rígido con acabado laminado tipo madera o ranurado moderno.',
          instalacion: 'Instalación en estructura de aluminio o madera. Sistema de encaje tipo puzzle o sobre estructura visible.',
          colores: 'Sherwood y otros acabados tipo madera. También disponible en blanco y tonos modernos.',
          precio: '$180 - $350 MXN por pieza.',
          mantenimiento: 'Limpieza con paño húmedo. No requiere pintura ni barniz.',
          usos: 'Techos y cielos falsos de interiores: cocinas, baños, oficinas, consultorios, locales comerciales.',
          garantia: '15 años.',
          diferencias: 'Más económico y fácil de instalar que el plafón de yeso. Inmune a humedad y moho, a diferencia del MDF o madera.'
        },
        paneles_3d: {
          name: 'Paneles Tridimensionales 3D',
          medidas: '500 x 500 mm (varía por modelo).',
          agua: 'Los de PVC son resistentes al agua. Los de fibra de bambú requieren protección en zonas húmedas.',
          exterior: 'Solo los modelos de PVC específicos para exterior. Consultar ficha técnica.',
          material: 'PVC o fibra de bambú natural. Texturas en relieve con diseños geométricos y orgánicos.',
          instalacion: 'Adhesión con silicona o pegamento de contacto sobre muro limpio y nivelado.',
          colores: 'Blanco, grises, madera, negro, dorado. Algunos modelos se pueden pintar.',
          precio: '$280 - $550 MXN por pieza.',
          mantenimiento: 'Limpieza con paño seco o aspiradora de baja potencia. Para PVC: paño húmedo.',
          usos: 'Muros de acento, fondos de TV, cabeceras de cama, recepciones, salas, recámaras, locales comerciales.',
          garantia: '10 años.',
          diferencias: 'Agrega profundidad y relieve que las placas lisas no logran. Más decorativo que funcional.'
        },
        vigas: {
          name: 'Vigas PVC/WPC/PU',
          medidas: 'Varían desde 70x50 mm hasta 120x80 mm según modelo.',
          agua: 'Las de PVC y WPC son resistentes al agua. Las de PU requieren protección en exteriores.',
          exterior: 'Vigas PVC y WPC: sí. Vigas PU: solo interiores o exteriores protegidos.',
          material: 'PVC ligero, WPC (aspecto madera real) o PU (poliuretano, muy ligero y detallado).',
          instalacion: 'Instalación con tornillos, soportes metálicos o adhesivo de construcción según el peso y ubicación.',
          colores: 'Madera clara, madera oscura, nogal, caoba, blanco, gris.',
          precio: '$450 - $1,200 MXN por pieza.',
          mantenimiento: 'Limpieza con paño seco. No requiere barnizado ni sellado (PVC/WPC).',
          usos: 'Decoración de techos, pérgolas, porches, vigas falsas, marcos de puertas y ventanas.',
          garantia: '15 años (PVC/WPC).',
          diferencias: 'PVC: más ligero y económico. WPC: aspecto madera real. PU: máximo detalle decorativo.'
        },
        pisos: {
          name: 'Pisos',
          medidas: 'SPC: 1220 x 180 x 4-5.5 mm. WPC: 1220 x 180 x 5.5-8 mm. Laminado: 1215 x 195 x 8-12 mm.',
          agua: 'SPC: 100% impermeable. WPC: muy resistente al agua. Laminado: resistente a salpicaduras, no sumergible.',
          exterior: 'Deck sintético: sí, diseñado para exteriores. SPC/WPC/Laminado: solo interiores.',
          material: 'SPC: piedra + plástico. WPC: madera + plástico. Laminado: fibra de alta densidad (HDF). Deck: WPC exterior.',
          instalacion: 'Sistema click (encaje tipo puzzle). No requiere pegamento. Superficie nivelada y limpia. Dejar junta de dilatación perimetral.',
          colores: 'Maderas claras, medias y oscuras. Cements, grises, blancos. Imitaciones de mármol y piedra.',
          precio: '$900 - $2,500 MXN por caja. SPC más económico, WPC más cálido.',
          mantenimiento: 'Barrido regular y trapeado húmedo con jabón neutro. Evitar abrasivos y exceso de agua en laminado.',
          usos: 'Interiores residenciales y comerciales: recámaras, salas, cocinas, baños (SPC), oficinas, tiendas. Deck para terrazas y albercas.',
          garantia: 'SPC: 12 años residencial. WPC: 15 años. Laminado: 10-15 años.',
          diferencias: 'SPC: más duro y resistente al agua. WPC: más cálido al tacto y confortable. Laminado: más económico pero sensible al agua.'
        },
        zacate: {
          name: 'Zacate Sintético',
          medidas: 'Rollos de 2m o 4m de ancho. Altura: 20-40 mm.',
          agua: 'Drenaje integrado. No se encharca. Resistente a lluvia y rocío.',
          exterior: 'Sí, es exclusivamente para exteriores. Resistente a rayos UV.',
          material: 'Polietileno UV de alta densidad. Hilos texturizados que imitan pasto natural.',
          instalacion: 'Colocación sobre terreno nivelado con base de grava o cemento. Se fija con clavos en U o adhesivo.',
          colores: 'Verde natural, verde oscuro, verde-amarillo, mixtos.',
          precio: '$220 - $480 MXN por m².',
          mantenimiento: 'Barrido de hojas y residuos. Lavado ocasional con manguera. No requiere riego, poda ni fertilizantes.',
          usos: 'Jardines, terrazas, balcones, albercas, áreas de juego, rooftops, eventos, decoración de interiores (follaje).',
          garantia: '5 años contra decoloración por UV.',
          diferencias: 'No requiere riego, poda ni mantenimiento como el pasto natural. Más higiénico para mascotas y niños.'
        },
        cladding: {
          name: 'Cladding (Placas tipo piedra)',
          medidas: '1200 x 600 x 30-50 mm.',
          agua: 'Resistente al agua y a la intemperie. No absorbe humedad.',
          exterior: 'Sí, diseñado específicamente para exteriores. Resiste lluvia, viento, UV y cambios de temperatura.',
          material: 'Poliuretano o compuesto mineral de alta densidad. Imitación de piedra real con textura y color naturales.',
          instalacion: 'Adhesión con mortero especial o tornillos en estructura. Requiere nivelación previa y sellado de juntas.',
          colores: 'BLACK, WHITE, GRAY, BEIGE, BROWN, RUSTIC, CEMENT.',
          precio: '$550 - $1,050 MXN por pieza.',
          mantenimiento: 'Limpieza con manguera o cepillo suave. No requiere tratamientos químicos.',
          usos: 'Fachadas residenciales y comerciales, muros de contención decorativos, columnas, chimeneas, detalles arquitectónicos.',
          garantia: '10 años.',
          diferencias: 'Pesa 8-12 veces menos que la piedra real. Instalación más rápida y económica. No requiere cimentación especial.'
        }
      };
      
      function detectQuestionType(q) {
        if (/\\b(medida|dimension|tamano|largo|ancho|grueso|espesor|cuanto mide|que tan grande|que tan ancho)\\b/.test(q)) return 'medidas';
        if (/\\b(agua|mojar|moja|humedad|moho|impermeable|resistente al agua|resiste agua|se puede mojar|llover|lluvia)\\b/.test(q)) return 'agua';
        if (/\\b(exterior|interior|afuera|adentro|intemperie|sol|uv|exterior|exterio|afuera)\\b/.test(q)) return 'exterior';
        if (/\\b(material|de que esta hecho|de que es|composicion|compuesto|que tiene)\\b/.test(q)) return 'material';
        if (/\\b(instalar|instalacion|colocar|colocacion|poner|como se pone|como se instala)\\b/.test(q)) return 'instalacion';
        if (/\\b(color|colores|tono|tonalidad|acabado|diseño|modelo|hay en|tienen en)\\b/.test(q)) return 'colores';
        if (/\\b(precio|cuesta|cuanto|valor|costo|dinero|barato|caro)\\b/.test(q)) return 'precio';
        if (/\\b(mantenimiento|limpiar|limpieza|cuidado|conservar|durar|vida util)\\b/.test(q)) return 'mantenimiento';
        if (/\\b(uso|usar|donde se usa|para que sirve|aplicacion|aplicar|para que es|en que se usa)\\b/.test(q)) return 'usos';
        if (/\\b(garantia|garantiza|garantizar|cuanto dura la garantia)\\b/.test(q)) return 'garantia';
        if (/\\b(diferencia|comparar|versus|vs|mejor que|peor que|diferente a)\\b/.test(q)) return 'comparar';
        return null;
      }
      
      function answerFromKB(category, questionType) {
        if (!category || !PRODUCT_KB[category.name]) return null;
        const kb = PRODUCT_KB[category.name];
        const val = kb[questionType];
        if (!val) return null;
        const labels = {
          medidas: '📐 Medidas', agua: '💧 Resistencia al agua', exterior: '🌤️ Uso exterior/interior',
          material: '🧱 Material', instalacion: '🛠️ Instalación', colores: '🎨 Colores',
          precio: '💰 Precio', mantenimiento: '🧼 Mantenimiento', usos: '&#127968; Usos recomendados',
          garantia: '✅ Garantía', comparar: '⚖️ Diferencias'
        };
        return '<strong>' + labels[questionType] + ' — ' + kb.name + ':</strong><br><br>' + val;
      }
      
      function getKBOverview(catName) {
        const kb = PRODUCT_KB[catName];
        if (!kb) return null;
        return '📋 <strong>Ficha técnica de ' + kb.name + ':</strong><br><br>' +
          '📐 <strong>Medidas:</strong> ' + kb.medidas + '<br>' +
          '💧 <strong>Agua:</strong> ' + kb.agua + '<br>' +
          '🌤️ <strong>Exterior:</strong> ' + kb.exterior + '<br>' +
          '🧱 <strong>Material:</strong> ' + kb.material + '<br>' +
          '💰 <strong>Precio:</strong> ' + kb.precio + '<br>' +
          '✅ <strong>Garantía:</strong> ' + kb.garantia + '<br><br>' +
          '¿Te gustaría saber más sobre colores, instalación o mantenimiento?';
      }
      
      const WELCOME_VARIANTS = [
        '¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>.<br><br>Soy tu asistente virtual y puedo ayudarte con información sobre nuestros productos, horarios, precios, cotizaciones y más.<br><br>¿Qué necesitas? Escribe tu pregunta 👇',
        '¡Qué tal! 👋 Soy el asistente virtual de <strong>ADIS</strong>. Estoy aquí para ayudarte con:<br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios y ubicación 🕐📍<br><br>¿En qué puedo ayudarte?'
      ];
      
      let kb = {
        horarios: {
          lunes: 'Cerrado 🚪',
          martes: '10:00 a 19:00',
          miercoles: '9:00 a 19:00',
          jueves: '9:00 a 19:00',
          viernes: '9:00 a 19:00',
          sabado: '9:00 a 19:00',
          domingo: '9:00 a 15:00',
          whatsapp: 'Atendemos WhatsApp casi 24/7, excepto madrugada (aprox. 00:00 - 07:00)'
        },
        contacto: {
          whatsapp: '+1 (520) 839-2877',
          tel_showroom: '+52 631-120-4943',
          email: 'adis.remodelacion@gmail.com',
          ubicacion: 'Nogales, Sonora y Rio Rico, AZ',
          direccion: 'C. Alfonso Acosta 16 Local 3, Col. 5 de Mayo, 84000 Heroica Nogales, Sonora'
        },
        envios: {
          gratis: 'Nogales Sonora, Nogales AZ y Tucson',
          nacional: 'Enviamos a todo México. El costo corre por cuenta del cliente.',
          tiempo_grandes: '2 a 3 días hábiles para pedidos grandes'
        },
        pagos: {
          metodos: ['Tarjeta de crédito', 'Tarjeta de débito', 'Transferencia bancaria', 'Efectivo'],
          anticipo: 'Pedidos mayores a $10,000 requieren 50% de anticipo'
        },
        instalacion: {
          disponible: true,
          costo: 'Los precios son solo por el material. La instalación se cotiza aparte.',
          proceso: 'Un representante visita tu obra para medir y cotizar la instalación.'
        },
        proyectos: {
          tipos: 'Casas, oficinas, negocios, locales comerciales y cualquier espacio que requiera remodelación'
        },
        cotizacion: {
          tiempo: 'Menos de 24 horas',
          incluye: 'Costos detallados y stock disponible',
          sin_stock: 'Si no tenemos stock, estará disponible en 2 a 3 días'
        },
        precios: {
          iva: 'Todos los precios incluyen IVA',
          mayorista: 'Ofrecemos descuento a mayorista'
        },
        garantia: {
          validacion: 'ADIS Diseño hace válida la garantía del fabricante',
          pvc: '15 años',
          wpc: '15 años',
          spc: '12 años (residencial)',
          zacate: '5 años'
        },
        definiciones: {
          pvc: 'Policloruro de Vinilo. Es un tipo de plástico muy usado en letreros, hojas rígidas, tuberías, anuncios y materiales de impresión porque es resistente, ligero y económico.',
          wpc: 'Wood Plastic Composite (Compuesto de Madera y Plástico). Es un material hecho de fibras de madera mezcladas con plástico, muy usado en paneles, revestimientos, muebles y decoración porque parece madera pero resiste mejor la humedad y el desgaste.',
          spc: 'Stone Plastic Composite. Material de piso compuesto de piedra caliza y PVC. Muy resistente al agua, ideal para cocinas y baños. Instalación tipo click.',
          laminado: 'Piso laminado de alta densidad (HDF) con capa decorativa impresa. Económico y fácil de instalar. Recomendado para interiores de bajo tráfico.',
          cladding: 'Revestimiento de fachada que imita piedra natural. Pesa 8-12 veces menos que la piedra real, es más fácil de instalar y no requiere mantenimiento.'
        },
        especificaciones: {
          placas_pvc: 'Material: PVC rígido | Dimensiones: 2440 x 1220 x 5 mm | Presentación: 2.977 m²/pz, 1 pz/caja, 10.5 kg/pz | Garantía: 15 años | Uso: Interior',
          lambrin_wpc: 'Material: Wood Plastic Composite | Dimensiones: 219 x 26 x 3 mm (interior), 220 x 21 x 2.5 mm (exterior) | Presentación: 2.85 m²/caja (interior), 3.08 m²/caja (exterior) | Garantía: 15 años | Uso: Interior y exterior',
          paneles_3d: 'Material: PVC o fibra de bambú | Dimensiones: 500 x 500 mm (varía por modelo) | Presentación: por pieza | Garantía: 10 años | Uso: Interior',
          pisos_spc: 'Material: Stone Plastic Composite | Dimensiones: 1220 x 180 x 4-5.5 mm | Presentación: 8-10 piezas/caja (1.76-2.0 m²) | Garantía: 12 años residencial | Uso: Interior',
          plafon_pvc: 'Material: PVC | Dimensiones: 595 x 595 x 7 mm (laminado), 250 x 8000 x 10 mm (wood) | Presentación: por pieza | Garantía: 15 años | Uso: Interior',
          vigas_pvc: 'Material: PVC o WPC | Dimensiones: varían 70x50mm a 120x80mm | Presentación: por pieza | Garantía: 15 años | Uso: Interior/exterior',
          zacate: 'Material: Polietileno UV | Altura: 20-40 mm | Presentación: por metro cuadrado | Garantía: 5 años | Uso: Exterior',
          cladding: 'Material: Poliuretano o compuesto mineral | Dimensiones: 1200 x 600 x 30-50 mm | Presentación: por pieza | Garantía: 10 años | Uso: Exterior'
        },
        venta: {
          unidad: 'El tipo de unidad y cómo se vende viene en las fichas técnicas de cada categoría: por pieza, por hoja, tamaño de la hoja, etc.'
        }
      };
      
      // === NORMALIZACIÓN Y CORRECCIÓN ===
      const SYNONYMS = [
        {from: /\\b(meddia|medidas|medicion|mediciones|medir)\\b/g, to: 'medida'},
        {from: /\\b(especif|caciones|especificasiones|espeficaciones|caracteristicas)\\b/g, to: 'especificacion'},
        {from: /\\b(dimensiones|tamano|tamaño|tamanos|largo|ancho|grueso|espesor)\\b/g, to: 'dimension'},
        {from: /\\b(hojas|laminas|láminas|planchas)\\b/g, to: 'placa'},
        {from: /\\b(precio|precios|cuanto cuesta|cuanto valen|valor|costo|costos)\\b/g, to: 'precio'},
        {from: /\\b(cotizar|cotizacion|cotización|presupuesto|presupuestar)\\b/g, to: 'cotizacion'},
        {from: /\\b(envio|envíos|entrega|mandan|envian|domicilio|llevan|paqueteria)\\b/g, to: 'envio'},
        {from: /\\b(instalacion|instalan|colocan|ponen|colocacion|instalador)\\b/g, to: 'instalacion'},
        {from: /\\b(horario|horarios|hora|abierto|atencion|cierran|abren)\\b/g, to: 'horario'},
        {from: /\\b(ubicacion|direccion|donde|ubicados|showroom|tienda|local|direccion)\\b/g, to: 'ubicacion'},
        {from: /\\b(whatsapp|telefono|celular|numero|contacto|llamar|hablar|correo|email)\\b/g, to: 'contacto'},
        {from: /\\b(garantia|garantiza|garantias)\\b/g, to: 'garantia'},
        {from: /\\b(pago|pagos|tarjeta|credito|efectivo|transferencia|meses|debito|deposito)\\b/g, to: 'pago'},
        {from: /\\b(producto|catalogo|materiales|venden|tienen|ofrecen|disponen)\\b/g, to: 'producto'},
        {from: /\\b(mantenimiento|limpiar|limpieza|cuidado|conservar)\\b/g, to: 'mantenimiento'},
        {from: /\\b(gracias|thank|perfecto|excelente|muy amable)\\b/g, to: 'agradecimiento'},
        {from: /\\b(adios|bye|hasta luego|nos vemos|chao)\\b/g, to: 'despedida'},
        {from: /\\b(no|no es|otra cosa|cambio de tema|no gracias|nada mas|eso es todo)\\b/g, to: 'negacion'},
        {from: /\\b(ayuda|help|auxilio|soporte|asistencia)\\b/g, to: 'ayuda'},
        {from: /\\b(agua|mojar|moja|humedad|moho|impermeable|resistente al agua|resiste agua|se puede mojar|lloviendo|lluvia)\\b/g, to: 'resistencia_agua'},
        {from: /\\b(exterior|interior|interiores|exteriores|pared|muro|techo|piso|suelo|fachada)\\b/g, to: 'uso_espacio'}
      ];
      
      function normalizeQuery(raw) {
        let q = raw.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
        SYNONYMS.forEach(s => { q = q.replace(s.from, s.to); });
        return q.replace(/[^\\w\\s]/g, ' ').replace(/\\s+/g, ' ').trim();
      }
      
      // === SCORING DE INTENCIONES ===
      function scoreIntent(q) {
        const intents = [
          { name: 'saludo', words: ['hola','buenas','buenos','hey','hello','que tal','q tal'], score: 5 },
          { name: 'horario', words: ['horario','hora','abierto','atencion','cierran','abren'], score: 3 },
          { name: 'contacto', words: ['contacto','whatsapp','telefono','celular','numero','llamar','hablar','email','correo'], score: 3 },
          { name: 'ubicacion', words: ['ubicacion','donde','direccion','ubicados','local','tienda','showroom','nogales','rio rico'], score: 3 },
          { name: 'precio', words: ['precio','cuesta','cuanto','valor','cotizacion','cotizar','presupuesto'], score: 3 },
          { name: 'envio', words: ['envio','entrega','mandan','envian','domicilio','llevan','paqueteria'], score: 3 },
          { name: 'instalacion', words: ['instalacion','instalan','colocan','ponen','colocacion'], score: 3 },
          { name: 'pago', words: ['pago','pagos','tarjeta','credito','efectivo','transferencia','meses','debito'], score: 3 },
          { name: 'garantia', words: ['garantia','garantiza'], score: 3 },
          { name: 'producto', words: ['producto','catalogo','materiales','venden','tienen','ofrecen'], score: 2 },
          { name: 'mantenimiento', words: ['mantenimiento','limpiar','limpieza','cuidado'], score: 3 },
          { name: 'proyecto', words: ['casa','oficina','negocio','local','proyecto'], score: 2 },
          { name: 'medidas', words: ['medida','especificacion','dimension','ficha','hoja tecnica','tamano'], score: 4 },
          { name: 'definicion', words: ['que es','significa','definicion'], score: 2 },
          { name: 'agradecimiento', words: ['gracias','thank','perfecto','excelente'], score: 3 },
          { name: 'despedida', words: ['adios','bye','hasta luego','nos vemos'], score: 3 },
          { name: 'negacion', words: ['no es','otra cosa','cambio de tema','no gracias','nada'], score: 2 },
          { name: 'cotizar', words: ['cotizar','cotizacion','cotizacion guiada','quiero cotizar','me interesa','comprar','pedir','ordenar','cotiza'], score: 4 },
          { name: 'resistencia', words: ['resistencia_agua','resistencia','impermeable','durabilidad','aguanta','soporta'], score: 4 },
          { name: 'usos', words: ['uso_espacio','aplicacion','aplicación','donde se usa','para que sirve'], score: 3 },
          { name: 'ayuda', words: ['ayuda','help','auxilio','soporte'], score: 2 }
        ];
        
        let best = { name: 'default', score: 0 };
        for (let intent of intents) {
          let s = 0;
          for (let w of intent.words) {
            if (q.includes(w)) s += intent.score;
          }
          if (s > best.score) best = { name: intent.name, score: s };
        }
        return best;
      }
      
      function detectCategory(q) {
        const cats = [
          { name: 'placas_pvc', words: ['placa pvc','placas pvc','hoja pvc','lamina pvc','pvc rigido','pvc tipo madera','pvc espejo','pvc marmol'], labels: {short:'Placas PVC', url:'1-placas-pvc.html'} },
          { name: 'lambrin_wpc', words: ['lambrin wpc','lambrin','wpc'], labels: {short:'Lambrín WPC', url:'2-lambrin-wpc.html'} },
          { name: 'paneles_3d', words: ['panel 3d','paneles 3d','3d','tridimensional'], labels: {short:'Paneles 3D', url:'5-paneles-tridimensionales.html'} },
          { name: 'pisos', words: ['piso','pisos','spc','laminado','deck'], labels: {short:'Pisos', url:'7-pisos.html'} },
          { name: 'plafon', words: ['plafon','plafon pvc','cielo falso'], labels: {short:'Plafón PVC', url:'4-plafon-pvc.html'} },
          { name: 'vigas', words: ['viga','vigas','viga pvc','viga wpc'], labels: {short:'Vigas', url:'6-vigas-pvc.html'} },
          { name: 'zacate', words: ['zacate','pasto','cesped'], labels: {short:'Zacate', url:'8-zacate.html'} },
          { name: 'cladding', words: ['cladding','fachada','piedra'], labels: {short:'Cladding', url:'9-cladding.html'} },
          { name: 'revestimiento', words: ['revestimiento','concreto','flexible'], labels: {short:'Revestimiento', url:'3-revestimiento-flexible.html'} }
        ];
        
        let best = null, max = 0;
        for (let cat of cats) {
          let s = 0;
          for (let w of cat.words) if (q.includes(w)) s += 2;
          if (s > max) { max = s; best = cat; }
        }
        return best;
      }
      
      function isContextualQuestion(q, original) {
        const contextualStarters = /^(y|y las|y los|y el|y la|tambien|también|cuéntame|cuentame|más|mas|info|informacion|información|detalles|el primero|el segundo|el tercero|ese|esa|aquel|esa de|el de|las de|los de)\\b/;
        const followUpPatterns = /\\b(cuanto cuestan|cuanto valen|el precio|los precios|las medidas|las dimensiones|cuanto miden|mide|el color|los colores|tienen stock|hay stock|esta disponible|estan disponibles|no me gusta|no me gustaron|no es eso|otra cosa|algo mas|mostrame mas|ver mas|y eso|de esos|de estas|de esas)\\b/;
        return contextualStarters.test(q) || followUpPatterns.test(q) || q.length < 20 || original.length < 28;
      }
      
      function applyContext(q) {
        if (!chatContext.lastTopic && !chatContext.lastIntent && !chatContext.activeProduct) return q;
        const topic = chatContext.activeProduct || chatContext.lastTopic;
        if (/\\b(cuanto cuestan|cuanto valen|el precio|los precios|las medidas|las dimensiones|cuanto miden|mide|grueso|espesor|largo|ancho|detalles|info|informacion|agua|mojar|humedad|impermeable|resistente|exterior|interior|material|instalacion|colocar|color|colores|mantenimiento|limpiar|uso|usar|garantia|donde se usa|para que sirve)\\b/.test(q) && topic) {
          return topic.name.replace(/_/g,' ') + ' ' + q;
        }
        if (/^y\\b/.test(q) || q.includes('tambien') || q.includes('también') || q.includes('cuentame') || q.includes('cuéntame') || q.includes('mas informacion') || q.includes('más información')) {
          let prefix = '';
          if (topic) prefix += topic.name.replace(/_/g,' ') + ' ';
          return (prefix + q).trim();
        }
        return q;
      }
      
      // === HISTORIAL Y CONTEXTO ===
      function loadContext() {
        try {
          const saved = localStorage.getItem(CONTEXT_KEY);
          return saved ? JSON.parse(saved) : { lastTopic: null, lastIntent: null, lastProducts: [], lastResponseType: null, activeProduct: null };
        } catch(e) { return { lastTopic: null, lastIntent: null, lastProducts: [], lastResponseType: null, activeProduct: null }; }
      }
      function saveContext() {
        try { localStorage.setItem(CONTEXT_KEY, JSON.stringify(chatContext)); } catch(e) {}
      }
      function saveHistory(text, isUser) {
        try {
          let h = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
          h.push({ text, isUser, time: Date.now() });
          if (h.length > MAX_HISTORY) h = h.slice(-MAX_HISTORY);
          localStorage.setItem(HISTORY_KEY, JSON.stringify(h));
        } catch(e) {}
      }
      function getHistory() {
        try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch(e) { return []; }
      }
      window.clearAllChat = function() {
        localStorage.removeItem(HISTORY_KEY);
        localStorage.removeItem(CONTEXT_KEY);
        chatBody.innerHTML = '';
        chatContext = { lastTopic: null, lastIntent: null, lastProducts: [], lastResponseType: null, activeProduct: null };
        showWelcome();
      };
      
      // === UI ===
      function formatTime(ts) {
        if (!ts) return '';
        const d = new Date(ts);
        return d.toLocaleTimeString('es-MX', {hour:'2-digit', minute:'2-digit'});
      }
      
      function addMessage(text, isUser) {
        const msg = document.createElement('div');
        msg.className = 'chat-message ' + (isUser ? 'user' : 'bot');
        msg.innerHTML = text + '<div class="chat-time">' + formatTime(Date.now()) + '</div>';
        chatBody.appendChild(msg);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function renderHistory() {
        const h = getHistory();
        if (h.length === 0) return false;
        h.forEach(item => {
          const msg = document.createElement('div');
          msg.className = 'chat-message ' + (item.isUser ? 'user' : 'bot');
          msg.innerHTML = item.text + '<div class="chat-time">' + formatTime(item.time) + '</div>';
          chatBody.appendChild(msg);
        });
        return true;
      }
      
      function removeInputs() {
        const existing = chatBody.querySelector('.chat-input-wrap');
        if (existing) existing.remove();
      }
      
      function showQuickReplies(replies) {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        if (!replies || replies.length === 0) replies = ['Ver productos', 'Horarios', 'Cotización', 'Ubicación'];
        const opts = document.createElement('div');
        opts.className = 'chat-options';
        opts.innerHTML = replies.map(r => `<button class="chat-option-btn" onclick="chatBotProcess('${r.replace(/'/g, "\\'")}')">${r}</button>`).join('');
        chatBody.appendChild(opts);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function addInputField() {
        removeInputs();
        const wrap = document.createElement('div');
        wrap.className = 'chat-input-wrap';
        wrap.style.cssText = 'display:flex;gap:0.5rem;margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid rgba(197,160,89,0.15);';
        wrap.innerHTML = `<input type="text" id="chatTextInput" placeholder="Escribe tu pregunta..." autocomplete="off" style="flex:1;padding:0.6rem 1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(197,160,89,0.25);border-radius:20px;color:var(--light);font-family:'Montserrat',sans-serif;font-size:0.82rem;" onkeydown="if(event.key==='Enter'){chatBotProcess(this.value);this.value='';}"><button onclick="chatBotProcess(document.getElementById('chatTextInput').value);document.getElementById('chatTextInput').value='';" style="background:var(--gold);border:none;border-radius:50%;width:34px;height:34px;cursor:pointer;color:var(--black);font-size:0.9rem;flex-shrink:0;">➤</button>`;
        chatBody.appendChild(wrap);
        chatBody.scrollTop = chatBody.scrollHeight;
        setTimeout(() => { const inp = document.getElementById('chatTextInput'); if (inp) inp.focus(); }, 100);
      }
      
      // === TARJETAS DE PRODUCTO ===
      function formatProductCard(m) {
        const waText = encodeURIComponent('Hola ADIS, vi el ' + m.name + ' en el catálogo y me interesa cotizar');
        const priceTag = m.price ? `<div style="color:var(--gold);font-size:0.75rem;font-weight:600;margin-top:0.25rem;">💰 ${m.price} <span style="opacity:0.7;font-weight:400;">por ${m.price_unit || 'pieza'}</span></div>` : '';
        return `<div class="chat-product-card">
          <img src="${m.thumb}" alt="${m.name}" loading="lazy">
          <div class="chat-product-info">
            <a href="${m.url}" target="_blank">${m.name}</a>
            <div class="chat-product-cat">${m.category}${m.subcategory ? ' / ' + m.subcategory : ''}</div>
            ${priceTag}
            <div class="chat-product-actions">
              <a href="${m.url}" class="primary" target="_blank">Ver producto</a>
              <a href="https://wa.me/15208392877?text=${waText}" class="secondary" target="_blank">Cotizar</a>
            </div>
          </div>
        </div>`;
      }
      
      function findProductMatches(q, excludeIds) {
        if (!allProducts.length) return [];
        const terms = q.split(/\\s+/).filter(t => t.length > 2);
        // Búsqueda por nombre exacto (incluso con términos cortos como "gris", "negro")
        const shortTerms = q.split(/\\s+/).filter(t => t.length >= 3);
        return allProducts.map(p => {
          if (excludeIds && excludeIds.includes(p.name)) return { p, score: 0 };
          const text = normalizeQuery(p.name + ' ' + p.category + ' ' + (p.subcategory || ''));
          let score = 0;
          for (let t of terms) {
            if (text.includes(t)) score += 1;
          }
          const nameNorm = normalizeQuery(p.name);
          for (let t of terms) {
            if (nameNorm === t) score += 5;
            else if (nameNorm.startsWith(t)) score += 3;
          }
          // Bonus por coincidencias de color/modelo exacto
          for (let t of shortTerms) {
            if (nameNorm.includes(t)) score += 2;
          }
          return { p, score };
        }).filter(x => x.score > 0).sort((a,b) => b.score - a.score).slice(0, 3);
      }
      
      function findRelatedProducts(currentProducts) {
        if (!allProducts.length || !currentProducts.length) return [];
        const sameCat = currentProducts[0].category;
        const sameSub = currentProducts[0].subcategory;
        const excludeNames = currentProducts.map(p => p.name);
        // Buscar productos de la misma subcategoría, excluyendo los ya mostrados
        let candidates = allProducts.filter(p => 
          p.category === sameCat && 
          (!sameSub || p.subcategory === sameSub) && 
          !excludeNames.includes(p.name)
        );
        if (candidates.length === 0) {
          // Si no hay en la misma subcategoría, buscar en la misma categoría
          candidates = allProducts.filter(p => p.category === sameCat && !excludeNames.includes(p.name));
        }
        // Tomar hasta 3 aleatorios
        const shuffled = candidates.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, 3);
      }
      
      // === BÚSQUEDA EN "SABÍAS QUE" ===
      function searchResearch(q, category) {
        if (!researchData || Object.keys(researchData).length === 0) return null;
        const terms = q.split(/\\s+/).filter(t => t.length > 2);
        if (terms.length === 0) return null;
        
        let best = null, bestScore = 0;
        const cats = category ? [category.name] : Object.keys(researchData);
        
        for (let catKey of Object.keys(researchData)) {
          if (category && catKey !== category.name) continue;
          const cat = researchData[catKey];
          if (!cat) continue;
          
          for (let c of cat.curiosos || []) {
            const text = normalizeQuery(c.title + ' ' + c.content);
            let score = 0;
            for (let t of terms) {
              if (text.includes(t)) score += 1;
              if (normalizeQuery(c.title).includes(t)) score += 2;
            }
            if (score > bestScore) {
              bestScore = score;
              best = { type: 'curioso', category: cat.name, title: c.title, content: c.content };
            }
          }
          
          for (let f of cat.faqs || []) {
            const text = normalizeQuery(f.q + ' ' + f.a);
            let score = 0;
            for (let t of terms) {
              if (text.includes(t)) score += 1;
              if (normalizeQuery(f.q).includes(t)) score += 2;
            }
            if (score > bestScore) {
              bestScore = score;
              best = { type: 'faq', category: cat.name, title: f.q, content: f.a };
            }
          }
        }
        
        return bestScore >= 2 ? best : null;
      }
      
      function formatResearchAnswer(item) {
        const icon = item.type === 'faq' ? '❓' : '💡';
        const label = item.type === 'faq' ? 'Pregunta frecuente' : 'Dato curioso';
        return icon + ' <strong>' + label + ' — ' + item.category + '</strong><br><br><strong>' + item.title + '</strong><br><br>' + item.content;
      }
      
      // === SUGERENCIAS CONTEXTUALES ===
      function getSuggestions(intent, category, products) {
        if (products && products.length > 0) {
          return ['Ver ficha técnica', 'Cotizar este producto', 'Ver más productos', 'Hablar con asesor'];
        }
        if (category) {
          const catName = category.labels.short;
          const base = ['Ver ' + catName, 'Cotizar ' + catName, 'Hablar con asesor'];
          if (intent === 'medidas') return ['Precios de ' + catName, '¿Se puede mojar?', 'Colores de ' + catName].concat(base);
          if (intent === 'precio') return ['Medidas de ' + catName, 'Colores de ' + catName, '¿Para exterior?'].concat(base);
          if (intent === 'agua') return ['Medidas de ' + catName, 'Mantenimiento', 'Colores de ' + catName].concat(base);
          if (intent === 'exterior') return ['Medidas de ' + catName, 'Material', 'Instalación'].concat(base);
          if (intent === 'material') return ['Medidas', 'Colores', 'Precios'].concat(base);
          if (intent === 'instalacion') return ['Medidas', 'Material', 'Precios'].concat(base);
          if (intent === 'colores') return ['Ver ' + catName, 'Precios', 'Medidas'].concat(base);
          if (intent === 'mantenimiento') return ['Material', 'Precios', 'Garantía'].concat(base);
          if (intent === 'usos') return ['Medidas', 'Precios', 'Colores'].concat(base);
          if (intent === 'garantia') return ['Medidas', 'Precios', 'Mantenimiento'].concat(base);
          if (intent === 'comparar') return ['Ver ' + catName, 'Precios', 'Medidas'].concat(base);
          return ['Medidas de ' + catName, 'Precios de ' + catName, 'Colores de ' + catName, 'Hablar con asesor'];
        }
        if (intent === 'precio') return ['Solicitar cotización', 'Ver productos', 'Horarios', 'Hablar con asesor'];
        if (intent === 'medidas') return ['Ver productos', 'Cotización', 'Horarios', 'Hablar con asesor'];
        if (intent === 'horario') return ['Ubicación', 'Ver productos', 'Cotización', 'Hablar con asesor'];
        if (intent === 'ubicacion') return ['Horarios', 'Ver productos', 'Cotización', 'Hablar con asesor'];
        if (intent === 'envio') return ['Cotizar envío', 'Ver productos', 'Ubicación', 'Hablar con asesor'];
        if (intent === 'instalacion') return ['Cotizar instalación', 'Ver productos', 'Precios', 'Hablar con asesor'];
        return ['Ver productos', 'Horarios', 'Cotización', 'Ubicación', 'Hablar con asesor'];
      }
      
      // === RESPUESTAS POR INTENCIÓN ===
      function handleSpecs(category, q) {
        const specsMap = {
          placas_pvc: { text: kb.especificaciones.placas_pvc + '<br><br>💡 Las placas PVC miden <strong>2440 x 1220 x 5 mm</strong> (2.977 m² por pieza). Se venden por pieza individual. Peso: 10.5 kg/pz. Garantía: 15 años.', label: 'Placas PVC', url: '1-placas-pvc.html' },
          lambrin_wpc: { text: kb.especificaciones.lambrin_wpc + '<br><br>💡 Disponible en interior (219 x 26 x 3 mm) y exterior. Varía según modelo.', label: 'Lambrín WPC', url: '2-lambrin-wpc.html' },
          paneles_3d: { text: kb.especificaciones.paneles_3d, label: 'Paneles 3D', url: '5-paneles-tridimensionales.html' },
          pisos: { text: kb.especificaciones.pisos_spc + '<br><br>💡 Tenemos laminado, WPC, SPC y deck sintético. Las medidas varían según el tipo.', label: 'Pisos', url: '7-pisos.html' },
          plafon: { text: kb.especificaciones.plafon_pvc, label: 'Plafón PVC', url: '4-plafon-pvc.html' },
          vigas: { text: kb.especificaciones.vigas_pvc, label: 'Vigas', url: '6-vigas-pvc.html' },
          zacate: { text: kb.especificaciones.zacate, label: 'Zacate Sintético', url: '8-zacate.html' },
          cladding: { text: kb.especificaciones.cladding, label: 'Cladding', url: '9-cladding.html' },
          revestimiento: { text: 'Material: Polímero flexible | Dimensiones: varían según modelo | Aplicación: Muros interiores y exteriores | Resistente al agua y UV.', label: 'Revestimiento Flexible', url: '3-revestimiento-flexible.html' }
        };
        
        if (category && specsMap[category.name]) {
          const s = specsMap[category.name];
          return '📐 <strong>Especificaciones técnicas — ' + s.label + ':</strong><br><br>' + s.text;
        }
        let r = '📐 <strong>Especificaciones técnicas por categoría:</strong><br><br>';
        for (let key in specsMap) {
          const s = specsMap[key];
          r += '📋 <strong>' + s.label + ':</strong><br>' + s.text + '<br><br>';
        }
        r += '💡 Cada categoría en el catálogo tiene su ficha técnica completa con medidas exactas, contenido por caja y recomendaciones de instalación.';
        return r;
      }
      
      function respond(intent, category, q, original) {
        let r = '', suggestions = [];
        
        switch(intent) {
          case 'saludo':
            r = WELCOME_VARIANTS[Math.floor(Math.random() * WELCOME_VARIANTS.length)];
            suggestions = ['Ver productos', 'Horarios', 'Cotización', 'Ubicación', '¿Tienen envío?'];
            break;
          case 'horario':
            r = '🕐 <strong>Horarios de atención (Showroom):</strong><br><br>• <strong>Lunes:</strong> ' + kb.horarios.lunes + '<br>• <strong>Martes:</strong> ' + kb.horarios.martes + '<br>• <strong>Miércoles:</strong> ' + kb.horarios.miercoles + '<br>• <strong>Jueves:</strong> ' + kb.horarios.jueves + '<br>• <strong>Viernes:</strong> ' + kb.horarios.viernes + '<br>• <strong>Sábado:</strong> ' + kb.horarios.sabado + '<br>• <strong>Domingo:</strong> ' + kb.horarios.domingo + '<br><br>&#128172; ' + kb.horarios.whatsapp;
            break;
          case 'contacto':
            r = '📱 <strong>Contactos directos:</strong><br><br>• <strong>WhatsApp:</strong> ' + kb.contacto.whatsapp + '<br>• <strong>Showroom:</strong> ' + kb.contacto.tel_showroom + '<br>• <strong>Email:</strong> ' + kb.contacto.email + '<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20tengo%20una%20pregunta" target="_blank" class="chat-whatsapp-btn">&#128172; Abrir WhatsApp</a>';
            break;
          case 'ubicacion':
            r = '📍 <strong>ADIS Diseño & Remodelación</strong><br><br>&#127968; <strong>Dirección:</strong><br>' + kb.contacto.direccion + '<br><br>📱 <strong>WhatsApp:</strong> ' + kb.contacto.whatsapp + '<br>☎️ <strong>Showroom:</strong> ' + kb.contacto.tel_showroom + '<br>✉️ <strong>Email:</strong> ' + kb.contacto.email + '<br><br>🕐 Horario showroom: Martes a domingo (lunes cerrado)<br>📍 También atendemos en <strong>Rio Rico, AZ</strong><br><br><a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" style="color:#C5A059">🗺️ Ver en Google Maps →</a>';
            break;
          case 'precio':
            r = '💰 <strong>Precios y cotizaciones:</strong><br><br>• ' + kb.precios.iva + '<br>• ' + kb.precios.mayorista + '<br>• Los precios son <strong>solo por el material</strong> (por pieza, caja o metro cuadrado según categoría)<br><br>📋 <strong>Cotización detallada:</strong> ' + kb.cotizacion.tiempo + '<br>📦 <strong>Incluye:</strong> ' + kb.cotizacion.incluye + '<br>⏱️ <strong>Sin stock:</strong> ' + kb.cotizacion.sin_stock + '<br><br>🔨 ¿Requieres instalación? Un representante visita tu obra para cotizarla aparte.<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20quiero%20una%20cotización" target="_blank" class="chat-whatsapp-btn">📱 Solicitar cotización gratis</a>';
            break;
          case 'envio':
            r = '🚚 <strong>Envíos y entregas:</strong><br><br>🎁 <strong>Entrega GRATIS</strong> en: ' + kb.envios.gratis + '<br><br>📦 ' + kb.envios.nacional + '<br><br>⏱️ ' + kb.envios.tiempo_grandes + '<br><br>Envíanos tu dirección por WhatsApp para cotizar el envío exacto.<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20quiero%20cotizar%20un%20envío" target="_blank" class="chat-whatsapp-btn">📱 Cotizar envío</a>';
            break;
          case 'instalacion':
            r = '🛠️ <strong>Servicio de instalación:</strong><br><br>' + kb.instalacion.costo + '<br><br>👷 ' + kb.instalacion.proceso + '<br><br>💡 <strong>Consejos para instalación:</strong><br>• Superficie limpia, seca y nivelada<br>• Temperatura ideal: 15°C a 30°C<br>• Dejar junta de dilatación de 2-3 mm<br>• Corte con sierra circular / disco de carburo de tungsteno<br>• Para espejos: usar perfiles de aluminio obligatoriamente<br><br>✅ También vendemos materiales sueltos si prefieres instalar por tu cuenta.<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20quiero%20cotizar%20instalación" target="_blank" class="chat-whatsapp-btn">📱 Cotizar instalación</a>';
            break;
          case 'pago':
            r = '💳 <strong>Formas de pago:</strong><br><br>';
            kb.pagos.metodos.forEach(m => { r += '• ' + m + '<br>'; });
            r += '<br>⚠️ <strong>' + kb.pagos.anticipo + '</strong><br><br>Escríbenos para más detalles.<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20pregunto%20por%20formas%20de%20pago" target="_blank" class="chat-whatsapp-btn">📱 Preguntar por pagos</a>';
            break;
          case 'garantia':
            r = '✅ <strong>Garantía:</strong><br><br>🛡️ ' + kb.garantia.validacion + '<br><br>• Placas PVC: ' + kb.garantia.pvc + '<br>• Lambrín WPC: ' + kb.garantia.wpc + '<br>• Pisos SPC: ' + kb.garantia.spc + '<br>• Zacate sintético: ' + kb.garantia.zacate + '<br><br>La garantía cubre defectos de fábrica. Conserva tu ticket de compra.';
            break;
          case 'producto':
            r = '📦 <strong>Nuestros productos (250 productos en 9 categorías):</strong><br><br>• <strong>Placas PVC</strong> — 34 productos<br>• <strong>Lambrín WPC</strong> — 40 productos<br>• <strong>Paneles 3D</strong> — 24 productos<br>• <strong>Pisos</strong> — 78 productos<br>• <strong>Plafón PVC</strong> — 15 productos<br>• <strong>Vigas PVC/WPC</strong> — 15 productos<br>• <strong>Zacate sintético</strong> — 29 productos<br>• <strong>Cladding</strong> — 11 productos<br>• <strong>Revestimiento Flexible</strong> — 6 productos<br><br>&#127968; Atendemos: ' + kb.proyectos.tipos + '<br><br>💡 Escribe el nombre de un producto o categoría para saber más.';
            break;
          case 'mantenimiento':
            r = '🧼 <strong>Mantenimiento y limpieza:</strong><br><br>• <strong>Limpieza regular:</strong> Paño suave humedecido con agua tibia y jabón neutro (pH 7)<br>• <strong>Manchas difíciles:</strong> Alcohol isopropílico al 70% o limpiador multiusos suave<br>• <strong>Evitar:</strong> Acetona, thinner, solventes fuertes, estropajos metálicos y amoníaco concentrado<br>• <strong>Frecuencia:</strong> Residencial = mensual | Comercial = semanal<br>• <strong>Inspección anual:</strong> Revisar juntas de dilatación y selladores<br><br>💡 Los productos PVC y WPC no requieren barnizado ni sellado. Solo limpieza básica.<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20pregunto%20por%20mantenimiento" target="_blank" class="chat-whatsapp-btn">📱 Preguntar por mantenimiento</a>';
            break;
          case 'proyecto':
            r = '&#127968; <strong>Atendemos todo tipo de proyectos:</strong><br><br>' + kb.proyectos.tipos + '<br><br>Desde una pared de acento en casa hasta remodelaciones completas de locales comerciales. Cada proyecto es único y tenemos el material perfecto para ti.<br><br>💡 <strong>Consejo:</strong> Si no estás seguro de qué material elegir, contame:<br>• ¿Es interior o exterior?<br>• ¿Hay humedad o contacto con agua?<br>• ¿Qué estética buscas? (madera, mármol, moderno, rústico)<br><br><a href="https://wa.me/15208392877?text=Hola%20ADIS,%20tengo%20un%20proyecto%20de" target="_blank" class="chat-whatsapp-btn">📱 Contar mi proyecto</a>';
            break;
          case 'agradecimiento':
            r = '¡Con mucho gusto! 😊🙌 Estoy aquí para lo que necesites. Si tienes más dudas, escríbenos por WhatsApp al <strong>' + kb.contacto.whatsapp + '</strong> o visítanos en el showroom. ¡Que tengas un excelente día!';
            break;
          case 'despedida':
            r = '¡Hasta luego! 👋 Gracias por contactar a ADIS Diseño & Remodelación. Recuerda que puedes volver cuando quieras o escribirnos al WhatsApp. ¡Éxito con tu proyecto! &#127968;✨';
            break;
          case 'negacion':
            r = 'Perfecto, ¿en qué más puedo ayudarte? Puedo:<br>• Mostrarte productos 📦<br>• Darte precios 💰<br>• Contarte horarios 🕐<br>• Explicarte envíos 📍<br>• Ayudarte con una cotización 📝';
            suggestions = ['Ver productos', 'Horarios', 'Cotización', 'Ubicación'];
            break;
          case 'ayuda':
            r = '¡Claro! Puedo ayudarte con:<br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Formas de pago 💳<br>• Instalación 🛠️<br><br>Escribe tu pregunta o usa los botones de abajo.';
            break;
          case 'medidas':
            r = handleSpecs(category, q);
            break;
          case 'definicion':
            if (q.includes('pvc')) r = '&#128220; <strong>¿Qué es PVC?</strong><br><br>' + kb.definiciones.pvc + '<br><br>En ADIS lo usamos para placas decorativas, plafones y vigas con acabados que imitan madera, espejo y texturas.';
            else if (q.includes('wpc')) r = '📗 <strong>¿Qué es WPC?</strong><br><br>' + kb.definiciones.wpc + '<br><br>En ADIS lo usamos para lambrín de interior y exterior, pisos y revestimientos que lucen como madera real pero duran más.';
            else r = '&#128220; Puedo explicarte qué es <strong>PVC</strong>, <strong>WPC</strong>, <strong>SPC</strong>, <strong>laminado</strong> o <strong>cladding</strong>. ¿Cuál te interesa?';
            break;
          case 'resistencia':
            if (category) {
              const catName = category.labels.short;
              if (catName.includes('PVC')) r = '💧 <strong>Resistencia al agua — ' + catName + ':</strong><br><br>• 100% impermeable y resistente a la humedad<br>• No absorbe agua, no se hincha ni se deforma<br>• Ideal para baños, cocinas y áreas húmedas<br>• Resistente a moho y hongos<br>• Limpieza fácil con paño húmedo<br><br>💡 <strong>¿Se puede mojar?</strong> Sí, perfectamente. Solo evita sumergir los perfiles de aluminio si lleva espejo.';
              else if (catName.includes('WPC')) r = '💧 <strong>Resistencia al agua — ' + catName + ':</strong><br><br>• Absorción de agua menor al 1%<br>• No se hincha, no se cuartea, no se deforma<br>• Resistente a humedad, lluvia y rayos UV<br>• Ideal para exteriores y fachadas<br><br>💡 <strong>¿Se puede mojar?</strong> Sí, está diseñado para intemperie.';
              else if (catName.includes('Piso')) r = '💧 <strong>Resistencia al agua — ' + catName + ':</strong><br><br>• SPC: 100% impermeable, ideal baños y cocinas<br>• WPC: Resistente al agua, ideal recámaras<br>• Laminado: Resistente a salpicaduras, no sumergible<br><br>💡 Dime para qué espacio lo necesitas y te recomiendo el mejor.';
              else r = '💧 <strong>Resistencia al agua — ' + catName + ':</strong><br><br>Consulta la ficha técnica de cada modelo en el catálogo. La mayoría de nuestros materiales son resistentes a la humedad.';
            } else {
              r = '💧 <strong>Resistencia al agua por material:</strong><br><br>• <strong>Placas PVC:</strong> 100% impermeables<br>• <strong>Lambrín WPC:</strong> Absorción <1%, ideal exterior<br>• <strong>Pisos SPC:</strong> 100% impermeables<br>• <strong>Cladding:</strong> Resistente a lluvia y UV<br>• <strong>Zacate sintético:</strong> Drenaje integrado<br><br>💡 Dime qué producto te interesa y te doy los detalles específicos.';
            }
            break;
          case 'usos':
            if (category) {
              r = '&#127968; <strong>Usos recomendados — ' + category.labels.short + ':</strong><br><br>' + handleSpecs(category, q);
            } else {
              r = '&#127968; <strong>Usos por material:</strong><br><br>• <strong>Placas PVC:</strong> Muros interiores (baños, cocinas, salas, recepciones)<br>• <strong>Lambrín WPC:</strong> Muros interior y exterior, fachadas<br>• <strong>Pisos SPC/WPC:</strong> Interiores residenciales y comerciales<br>• <strong>Plafón PVC:</strong> Techos y cielos falsos<br>• <strong>Paneles 3D:</strong> Muros de acento, fondos de TV<br>• <strong>Vigas:</strong> Decoración de techos y pérgolas<br>• <strong>Zacate:</strong> Jardines, terrazas, balcones<br>• <strong>Cladding:</strong> Fachadas, muros exteriores<br><br>💡 Dime para qué espacio lo necesitas y te recomiendo el mejor material.';
            }
            break;
          default:
            r = 'Disculpa, no entendí muy bien. 😅 Puedo ayudarte con:<br><br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Formas de pago 💳<br>• Instalación 🛠️<br><br>Escribe tu pregunta o usa los botones de abajo.';
        }
        
        if (!suggestions.length) suggestions = getSuggestions(intent, category, []);
        chatContext.lastTopic = category || chatContext.lastTopic;
        chatContext.lastIntent = intent;
        chatContext.lastResponseType = 'info';
        saveContext();
        
        return { text: r, suggestions };
      }
      
      function findResponse(q, original) {
        let normalized = normalizeQuery(q);
        if (isContextualQuestion(normalized, original)) normalized = applyContext(normalized);
        
        // === 1. Referencias a productos previos ("el primero", "ese", etc.) ===
        if (chatContext.lastProducts.length > 0 && /(primero|segundo|tercero|ese|aquel|ultimo|último)/.test(normalized)) {
          const idx = normalized.includes('segundo') ? 1 : normalized.includes('tercero') ? 2 : 0;
          const p = chatContext.lastProducts[idx];
          if (p) {
            // Fijar el producto activo basado en el producto referenciado
            const cats = [
              { name: 'placas_pvc', words: ['placa pvc','placas pvc','hoja pvc','lamina pvc','pvc rigido','pvc tipo madera','pvc espejo','pvc marmol'], labels: {short:'Placas PVC', url:'1-placas-pvc.html'} },
              { name: 'lambrin_wpc', words: ['lambrin wpc','lambrin','wpc'], labels: {short:'Lambrín WPC', url:'2-lambrin-wpc.html'} },
              { name: 'paneles_3d', words: ['panel 3d','paneles 3d','3d','tridimensional'], labels: {short:'Paneles 3D', url:'5-paneles-tridimensionales.html'} },
              { name: 'pisos', words: ['piso','pisos','spc','laminado','deck'], labels: {short:'Pisos', url:'7-pisos.html'} },
              { name: 'plafon', words: ['plafon','plafon pvc','cielo falso'], labels: {short:'Plafón PVC', url:'4-plafon-pvc.html'} },
              { name: 'vigas', words: ['viga','vigas','viga pvc','viga wpc'], labels: {short:'Vigas', url:'6-vigas-pvc.html'} },
              { name: 'zacate', words: ['zacate','pasto','cesped'], labels: {short:'Zacate', url:'8-zacate.html'} },
              { name: 'cladding', words: ['cladding','fachada','piedra'], labels: {short:'Cladding', url:'9-cladding.html'} },
              { name: 'revestimiento', words: ['revestimiento','concreto','flexible'], labels: {short:'Revestimiento', url:'3-revestimiento-flexible.html'} }
            ];
            for (let cat of cats) {
              if (p.category && cat.words.some(w => p.category.toLowerCase().includes(w))) {
                chatContext.activeProduct = cat;
                break;
              }
            }
            chatContext.lastIntent = 'producto';
            saveContext();
            return { 
              text: 'Aquí tienes más información de <strong>' + p.name + '</strong>:<br><br>' + formatProductCard(p),
              suggestions: ['Cotizar este producto', 'Ver productos similares', 'Hablar con asesor']
            };
          }
        }
        
        // === 2. Detectar categoría y tipo de pregunta ===
        let intent = scoreIntent(normalized);
        let category = detectCategory(normalized);
        let questionType = detectQuestionType(normalized);
        
        // === 3. REGLA CLAVE: Fijar producto activo ===
        // Si el usuario menciona explícitamente una categoría → CAMBIA el producto activo
        // Si NO menciona categoría → MANTENER el producto activo actual
        if (category) {
          chatContext.activeProduct = category;
          chatContext.lastTopic = category;
        }
        const activeProduct = chatContext.activeProduct;
        
        // === 4. Respuestas rápidas generales (no dependen de producto) ===
        if (original.length < 30 && !category && !activeProduct) {
          if (intent.name === 'horario') {
            return { text: '🕐 <strong>Horario showroom:</strong> Martes a Domingo 10:00-19:00. Lunes cerrado.<br><br>¿Necesitas algo más?', suggestions: ['Ubicación', 'Ver productos', 'Cotización'] };
          }
          if (intent.name === 'contacto') {
            return { text: '📱 WhatsApp: ' + kb.contacto.whatsapp + '<br>☎️ Showroom: ' + kb.contacto.tel_showroom, suggestions: ['Abrir WhatsApp', 'Ubicación', 'Horarios'] };
          }
          if (intent.name === 'ubicacion') {
            return { text: '📍 ' + kb.contacto.direccion + '<br><br>🕐 Martes a domingo 10:00-19:00', suggestions: ['Ver en Google Maps', 'WhatsApp', 'Horarios'] };
          }
          if (intent.name === 'precio' && !questionType) {
            return { text: '💰 Los precios varían por material y modelo.<br><br>✅ Cotización gratis por WhatsApp con respuesta en menos de 24 horas.', suggestions: ['Solicitar cotización', 'Ver productos', 'Hablar con asesor'] };
          }
          if (intent.name === 'envio') {
            return { text: '🚚 Envío GRATIS en Nogales y Rio Rico. A otras ciudades cotizamos por WhatsApp.', suggestions: ['Cotizar envío', 'Ubicación', 'WhatsApp'] };
          }
        }
        
        // === 5. Cotización guiada ===
        if (intent.name === 'cotizar') {
          return startQuoteFlow();
        }
        
        // === 6. RESPUESTA DIRECTA DESDE KB (máxima prioridad si hay producto activo) ===
        // Si el usuario hace una pregunta técnica sobre un producto activo → responder EXACTAMENTE de ese producto
        if (questionType && activeProduct) {
          const kbAnswer = answerFromKB(activeProduct, questionType);
          if (kbAnswer) {
            chatContext.lastTopic = activeProduct;
            chatContext.lastIntent = questionType;
            chatContext.lastResponseType = 'info';
            saveContext();
            return {
              text: kbAnswer,
              suggestions: getSuggestions(questionType, activeProduct, [])
            };
          }
        }
        
        // Si hay tipo de pregunta pero NO hay producto activo → preguntar de qué producto habla
        if (questionType && !activeProduct) {
          return {
            text: '🤔 Para darte la información correcta, ¿sobre qué producto necesitas saber?<br><br>• <strong>Placas PVC</strong><br>• <strong>Lambrín WPC</strong><br>• <strong>Pisos</strong><br>• <strong>Plafón PVC</strong><br>• <strong>Paneles 3D</strong><br>• <strong>Vigas</strong><br>• <strong>Cladding</strong><br>• <strong>Zacate</strong><br>• <strong>Revestimiento Flexible</strong>',
            suggestions: ['Placas PVC', 'Lambrín WPC', 'Pisos', 'Plafón PVC', 'Paneles 3D', 'Cladding', 'Hablar con asesor']
          };
        }
        
        // === 7. Recomendador inteligente (solo si NO hay producto activo o el usuario pide explícitamente recomendación) ===
        if (!activeProduct || /\\b(recomienda|recomiendame|recomendar|que me recomiendas|que sugieres|sugerencia|mejor opcion|mejor opción)\\b/.test(normalized)) {
          const recommendation = getRecommendation(normalized, category);
          if (recommendation) {
            return { text: recommendation.text, suggestions: recommendation.suggestions };
          }
        }
        
        // === 8. Comparaciones (SOLO si el usuario lo pide explícitamente) ===
        if (/\\b(diferencia|comparar|versus|vs|mejor que|peor que|diferente a|comparacion|comparación)\\b/.test(normalized)) {
          if ((normalized.includes('wpc') && normalized.includes('pvc')) || (normalized.includes('pvc') && normalized.includes('wpc'))) {
            return {
              text: '🆚 <strong>WPC vs PVC:</strong><br><br><strong>WPC (Wood Plastic Composite):</strong><br>• 60-70% fibras de madera + 30-40% plástico HDPE<br>• Aspecto más natural tipo madera real<br>• Absorción de agua menor al 1% — no se hincha ni se deforma<br>• Ideal para exteriores (resistente a UV y lluvia)<br>• Vida útil: 25-30 años | Garantía: 15 años<br><br><strong>PVC:</strong><br>• Plástico 100% con aditivos estabilizadores UV<br>• Más ligero y fácil de instalar<br>• Ideal para interiores<br>• Mayor variedad de diseños (madera, espejo, mármol, textura)<br>• Vida útil: 20-25 años | Garantía: 15 años<br><br>💡 <strong>¿Cuál elegir?</strong><br>• Exteriores / fachadas → <strong>WPC</strong><br>• Interiores / cocinas / baños → <strong>PVC</strong> (más económico)',
              suggestions: ['Ver Lambrín WPC', 'Ver Placas PVC', 'Cotizar', 'Hablar con asesor']
            };
          }
          if (activeProduct) {
            const kb = PRODUCT_KB[activeProduct.name];
            if (kb && kb.diferencias) {
              return {
                text: '<strong>⚖️ Diferencias — ' + kb.name + ':</strong><br><br>' + kb.diferencias,
                suggestions: getSuggestions('comparar', activeProduct, [])
              };
            }
          }
        }
        
        // === 9. Mármol específico (solo si no hay producto activo o si el usuario lo menciona explícitamente) ===
        if (!activeProduct && (normalized.includes('marmol') || normalized.includes('marble'))) {
          return { 
            text: '🏛️ <strong>Hoja de PVC tipo Mármol</strong><br><br>Es una solución decorativa perfecta para cualquier espacio interior. Añade un toque de elegancia a tu hogar, oficina o espacio comercial.<br><br>✨ <strong>Características:</strong><br>• Fabricada con PVC rígido de alta calidad<br>• Dimensiones: 2440 x 1220 x 5 mm (2.977 m² por pieza)<br>• Duradera y ligera, fácil de instalar y mantener<br>• 100% resistente al agua, manchas y arañazos<br>• No requiere sellado ni barnizado<br>• Garantía: 15 años<br><br>&#127968; <strong>Aplicaciones:</strong> Cocinas, baños, salas de estar, recepciones, muros de acento y más.<br><br>🎨 <strong>Diseños disponibles:</strong> Carrara, Carrara Oscuro, Aurora Dorada, Onix, Cuarzo, Opalo, Perla, Topacio, Grafito, Jaspe, Agata, Arena, Obsidiana y más.<br><br>💡 <strong>Consejo:</strong> Para instalación en espejos se requiere perfil de aluminio obligatoriamente.',
            suggestions: ['Ver Placas PVC', 'Cotizar mármol PVC', 'Medidas', 'Hablar con asesor']
          };
        }
        
        // === 10. Clarificación inteligente para términos ambiguos (solo si NO hay producto activo) ===
        const ambiguousTerms = ['pvc','wpc','piso','pisos','placa','placas','viga','vigas','panel','paneles'];
        const isAmbiguous = ambiguousTerms.includes(normalized.trim()) || (normalized.trim().length < 5 && !category);
        if (isAmbiguous && !activeProduct) {
          const clarifications = {
            'pvc': '🤔 <strong>¿Qué tipo de PVC te interesa?</strong><br><br>• <strong>Placas PVC</strong> — Muros decorativos (madera, mármol, espejo, textura)<br>• <strong>Plafón PVC</strong> — Techos y cielos falsos<br>• <strong>Vigas PVC</strong> — Decoración de interiores y exteriores',
            'wpc': '🤔 <strong>¿Qué tipo de WPC te interesa?</strong><br><br>• <strong>Lambrín WPC</strong> — Revestimiento de muros interior/exterior<br>• <strong>Pisos WPC</strong> — Pisos cálidos y resistentes<br>• <strong>Vigas WPC</strong> — Decoración tipo madera real',
            'piso': '🤔 <strong>¿Qué tipo de piso buscas?</strong><br><br>• <strong>SPC</strong> — Muy resistente al agua<br>• <strong>WPC</strong> — Cálido y confortable<br>• <strong>Laminado</strong> — Económico<br>• <strong>Deck sintético</strong> — Para exteriores',
            'pisos': '🤔 <strong>¿Qué tipo de piso buscas?</strong><br><br>• <strong>SPC</strong> — Muy resistente al agua<br>• <strong>WPC</strong> — Cálido y confortable<br>• <strong>Laminado</strong> — Económico<br>• <strong>Deck sintético</strong> — Para exteriores',
            'placa': '🤔 <strong>¿Qué tipo de placa te interesa?</strong><br><br>• <strong>Placas PVC</strong> — Decorativas para muros<br>• <strong>Paneles 3D</strong> — Con relieve y textura<br>• <strong>Cladding</strong> — Imitación piedra para exterior',
            'placas': '🤔 <strong>¿Qué tipo de placa te interesa?</strong><br><br>• <strong>Placas PVC</strong> — Decorativas para muros<br>• <strong>Paneles 3D</strong> — Con relieve y textura<br>• <strong>Cladding</strong> — Imitación piedra para exterior',
            'viga': '🤔 <strong>¿Qué tipo de viga te interesa?</strong><br><br>• <strong>Vigas PVC</strong> — Ligeras, gran variedad<br>• <strong>Vigas WPC</strong> — Aspecto madera real',
            'vigas': '🤔 <strong>¿Qué tipo de viga te interesa?</strong><br><br>• <strong>Vigas PVC</strong> — Ligeras, gran variedad<br>• <strong>Vigas WPC</strong> — Aspecto madera real',
            'panel': '🤔 <strong>¿Qué tipo de panel te interesa?</strong><br><br>• <strong>Paneles 3D</strong> — Decorativos con relieve<br>• <strong>Placas PVC</strong> — Lisas tipo madera/mármol<br>• <strong>Cladding</strong> — Imitación piedra',
            'paneles': '🤔 <strong>¿Qué tipo de panel te interesa?</strong><br><br>• <strong>Paneles 3D</strong> — Decorativos con relieve<br>• <strong>Placas PVC</strong> — Lisas tipo madera/mármol<br>• <strong>Cladding</strong> — Imitación piedra'
          };
          const term = normalized.trim();
          if (clarifications[term]) {
            return { text: clarifications[term], suggestions: ['Ver catálogo completo', 'Hablar con asesor', 'Cotizar'] };
          }
        }
        
        // === 11. Memoria profunda: "otro", "otro color", "otro similar" ===
        if (/\\b(otro|otra|otros|otras|otro color|otro modelo|otro diseño|otra opcion|otra opción|algo similar|parecido|mas de esos|más de esos|muestrame mas|mostrame mas)\\b/.test(normalized) && chatContext.lastProducts.length > 0) {
          const related = findRelatedProducts(chatContext.lastProducts);
          if (related.length > 0) {
            chatContext.lastProducts = related;
            chatContext.lastIntent = 'producto';
            chatContext.lastResponseType = 'products';
            saveContext();
            return {
              text: '✨ <strong>Otras opciones similares:</strong><br><br>' + related.map(formatProductCard).join('') + '<br>¿Alguna de estas te interesa?',
              suggestions: getSuggestions('producto', chatContext.lastTopic, related)
            };
          }
        }
        
        // === 12. Manejar rechazos / negaciones ===
        if (/\\b(no me gusta|no me gustaron|no es eso|no eso|otra cosa|algo diferente|no quiero eso|no es lo que busco|busco otra)\\b/.test(normalized)) {
          if (activeProduct || chatContext.lastTopic) {
            chatContext.activeProduct = null;
            chatContext.lastTopic = null;
            chatContext.lastIntent = 'negacion';
            saveContext();
            return {
              text: 'Entendido. 😊 ¿Qué tipo de acabado o material te gustaría explorar?<br><br>Puedo mostrarte:<br>• Diseños tipo madera 🪵<br>• Acabados tipo mármol 🏛️<br>• Texturas modernas 🎨<br>• Opciones en espejo ✨<br>• Colores específicos 🎨<br><br>Dime qué tienes en mente.',
              suggestions: ['Tipo madera', 'Tipo mármol', 'Espejo', 'Colores oscuros', 'Ver todo el catálogo', 'Hablar con asesor']
            };
          }
          return respond('negacion', category, normalized, original);
        }
        
        // === 13. Respuestas concisas para preguntas simples después de ver productos ===
        if (original.length < 35 && !category && activeProduct && chatContext.lastResponseType === 'products') {
          if (/\\b(precio|cuesta|valen)\\b/.test(normalized)) {
            const lastProds = chatContext.lastProducts;
            const priceInfo = lastProds.length > 0 && lastProds[0].price ? 
              '<br><br>💰 Rango de estos modelos: <strong>' + lastProds[0].price + '</strong> por ' + (lastProds[0].price_unit || 'pieza') + '.' : '';
            return {
              text: 'Los precios varían por modelo y acabado.' + priceInfo + '<br><br>✅ Envío gratis en Nogales y Rio Rico. Mayoreo desde 10 cajas.<br><br>¿Te gustaría una cotización exacta?',
              suggestions: ['Cotizar ' + activeProduct.labels.short, 'Ver más modelos', 'Hablar con asesor']
            };
          }
        }
        
        // === 14. Detección de urgencia ===
        const urgencyWords = /\\b(urgente|urgencia|prisa|rapido|rápido|ya|ahora|hoy|mañana|lo antes posible|express|express)\\b/;
        const isUrgent = urgencyWords.test(normalized);
        
        // === 15. Búsqueda de productos (solo si no es pregunta directa de info) ===
        const prodMatches = findProductMatches(normalized);
        if (prodMatches.length > 0 && original.length > 2) {
          const products = prodMatches.map(x => x.p);
          chatContext.lastProducts = products;
          chatContext.lastTopic = category || chatContext.lastTopic || activeProduct;
          chatContext.lastIntent = 'producto';
          chatContext.lastResponseType = 'products';
          saveContext();
          let urgencyMsg = '';
          if (isUrgent) {
            urgencyMsg = '<br>⚡ <strong>Entrega urgente:</strong> Si tu material está en stock, puede salir hoy mismo. Si no, el tiempo de reposición es de 2-5 días hábiles. Escríbenos por WhatsApp para confirmar disponibilidad.';
          }
          return {
            text: '🔎 <strong>Encontré estos productos:</strong><br><br>' + products.map(formatProductCard).join('') + urgencyMsg + '<br>¿Te gustaría cotizar alguno?',
            suggestions: getSuggestions('producto', chatContext.lastTopic, products)
          };
        }
        
        // === 16. respond() con intents generales ===
        const respondResult = respond(intent.name, category, normalized, original);
        if (respondResult.text && !respondResult.text.includes('no entendí')) {
          if (isUrgent && respondResult.text) {
            respondResult.text += '<br><br>⚡ <strong>Urgente:</strong> Si necesitas el material rápido, escríbenos al WhatsApp para confirmar stock inmediatamente.';
          }
          return respondResult;
        }
        
        // === 17. Búsqueda en "Sabías que" (último recurso) ===
        const researchMatch = searchResearch(normalized, activeProduct || category ? { name: (activeProduct || category).name } : null);
        if (researchMatch) {
          chatContext.lastTopic = category || chatContext.lastTopic || activeProduct;
          chatContext.lastIntent = 'research';
          saveContext();
          return {
            text: formatResearchAnswer(researchMatch) + '<br><br>📚 Sacado de <a href="sabias-que.html" style="color:#C5A059">¿Sabías que?</a>',
            suggestions: (activeProduct || category) ? ['Ver ' + (activeProduct || category).labels.short, 'Cotizar ' + (activeProduct || category).labels.short, 'Más datos curiosos', 'Hablar con asesor'] : ['Ver datos curiosos', 'Ver productos', 'Cotización', 'Hablar con asesor']
          };
        }
        
        // === 18. FALLBACK SEGURO: Si hay producto activo pero no sabemos responder ===
        if (activeProduct) {
          return {
            text: '🤔 No tengo ese dato confirmado en la información de <strong>' + activeProduct.labels.short + '</strong>, pero puedo ayudarte a contactar a un asesor para validarlo.<br><br>📱 <strong>' + kb.contacto.whatsapp + '</strong><br><br>Un experto te responderá en menos de 24 horas.',
            suggestions: ['Hablar con asesor', 'Ver ' + activeProduct.labels.short, 'Cotizar ' + activeProduct.labels.short]
          };
        }
        
        // === 19. Urgencia sin resultado ===
        if (isUrgent) {
          return {
            text: '⚡ Entiendo que lo necesitas con urgencia.<br><br>📱 Te recomiendo escribirnos directo al WhatsApp <strong>' + kb.contacto.whatsapp + '</strong> para confirmar stock y tiempos de entrega inmediatamente.<br><br>También puedo ayudarte a hacer una cotización guiada.',
            suggestions: ['Cotización urgente', 'WhatsApp', 'Ver productos']
          };
        }
        
        return respondResult;
      }
      
      // === FORMULARIO DE COTIZACIÓN GUIADA ===
      function startQuoteFlow() {
        chatContext.quoteState = 'category';
        chatContext.quoteData = {};
        saveContext();
        return {
          text: '📝 <strong>Cotización guiada</strong><br><br>Te voy a hacer unas preguntas para armar tu cotización. Al final podrás enviarla por WhatsApp con todos los detalles.<br><br><strong>Paso 1 de 6:</strong> ¿Qué producto o categoría te interesa?',
          suggestions: ['Placas PVC', 'Lambrín WPC', 'Pisos SPC', 'Paneles 3D', 'Plafón PVC', 'Cladding', 'Zacate']
        };
      }
      
      function handleQuoteStep(text, q) {
        const data = chatContext.quoteData;
        const state = chatContext.quoteState;
        
        if (state === 'category') {
          data.category = text;
          chatContext.quoteState = 'space';
          saveContext();
          return {
            text: '✅ Producto: <strong>' + text + '</strong><br><br><strong>Paso 2 de 6:</strong> ¿Para qué espacio lo necesitas?',
            suggestions: ['Baño', 'Cocina', 'Sala', 'Recámara', 'Fachada', 'Jardín', 'Oficina']
          };
        }
        if (state === 'space') {
          data.space = text;
          chatContext.quoteState = 'm2';
          saveContext();
          return {
            text: '✅ Espacio: <strong>' + text + '</strong><br><br><strong>Paso 3 de 6:</strong> ¿Aproximadamente cuántos metros cuadrados necesitas?',
            suggestions: ['5 m²', '10 m²', '20 m²', '30 m²', '50 m²', 'No sé, ayúdame']
          };
        }
        if (state === 'm2') {
          data.m2 = text;
          chatContext.quoteState = 'install';
          saveContext();
          return {
            text: '✅ Metraje: <strong>' + text + '</strong><br><br><strong>Paso 4 de 6:</strong> ¿Necesitas instalación?',
            suggestions: ['Sí, con instalación', 'No, solo material', 'Quiero que me asesoren']
          };
        }
        if (state === 'install') {
          data.install = text;
          chatContext.quoteState = 'location';
          saveContext();
          return {
            text: '✅ Instalación: <strong>' + text + '</strong><br><br><strong>Paso 5 de 6:</strong> ¿En qué ciudad/colonia será la obra?',
            suggestions: ['Nogales, Sonora', 'Nogales, AZ', 'Tucson, AZ', 'Otra ciudad']
          };
        }
        if (state === 'location') {
          data.location = text;
          chatContext.quoteState = 'contact';
          saveContext();
          return {
            text: '✅ Ubicación: <strong>' + text + '</strong><br><br><strong>Paso 6 de 6:</strong> ¿Cuál es tu nombre y teléfono? (opcional)',
            suggestions: ['Prefiero no decir', 'Solo enviar por WhatsApp']
          };
        }
        if (state === 'contact') {
          data.contact = text;
          chatContext.quoteState = 'summary';
          saveContext();
          return renderQuoteSummary();
        }
        return renderQuoteSummary();
      }
      
      function renderQuoteSummary() {
        const data = chatContext.quoteData;
        chatContext.quoteState = null;
        saveContext();
        return {
          text: '📋 <strong>Resumen de tu cotización:</strong><br><br>• <strong>Producto:</strong> ' + data.category + '<br>• <strong>Espacio:</strong> ' + data.space + '<br>• <strong>Metraje:</strong> ' + data.m2 + '<br>• <strong>Instalación:</strong> ' + data.install + '<br>• <strong>Ubicación:</strong> ' + data.location + '<br>' + (data.contact && data.contact !== 'Prefiero no decir' && data.contact !== 'Solo enviar por WhatsApp' ? '• <strong>Contacto:</strong> ' + data.contact + '<br>' : '') + '<br>✅ Revisa que todo esté correcto y envía la cotización por WhatsApp. Un asesor te responderá en menos de 24 horas.',
          suggestions: ['Enviar cotización por WhatsApp', 'Hacer otra cotización', 'Hablar con asesor']
        };
      }
      
      function sendQuoteToWhatsApp() {
        const data = chatContext.quoteData;
        if (!data || !data.category) return;
        const msg = `Hola ADIS, solicito cotización guiada desde el catálogo:\\n\\n• Producto: ${data.category}\\n• Espacio: ${data.space}\\n• Metraje: ${data.m2}\\n• Instalación: ${data.install}\\n• Ubicación: ${data.location}\\n${data.contact && data.contact !== 'Prefiero no decir' && data.contact !== 'Solo enviar por WhatsApp' ? '• Contacto: ' + data.contact + '\\n' : ''}\\nQuedo atento a su respuesta. Gracias.`;
        window.open('https://wa.me/15208392877?text=' + encodeURIComponent(msg), '_blank');
      }
      
      // === RECOMENDADOR INTELIGENTE ===
      function getRecommendation(q, category) {
        const recoMap = [
          {
            words: ['bano','regadera','ducha','humedad','moho','cocina','salpicaduras'],
            text: '🚿 <strong>Para baños y cocinas te recomendamos:</strong><br><br>• <strong>Placas PVC</strong> — 100% impermeables, ideales para muros. Acabados tipo mármol, espejo o madera.<br>• <strong>Pisos SPC</strong> — Resistentes al agua, instalación tipo click.<br>• <strong>Lambrín WPC</strong> — También resiste humedad, aspecto natural de madera.<br><br>💡 Todas tienen garantía de 12-15 años.',
            suggestions: ['Ver Placas PVC', 'Ver Pisos SPC', 'Cotizar para baño/cocina', 'Hablar con asesor']
          },
          {
            words: ['fachada','exterior','sol','lluvia','uv','exterior casa','pared exterior'],
            text: '&#127968; <strong>Para exteriores y fachadas te recomendamos:</strong><br><br>• <strong>Lambrín WPC exterior</strong> — No se deforma con la humedad ni el sol.<br>• <strong>Cladding</strong> — Imitación de piedra real, pesa 8-12 veces menos.<br>• <strong>Zacate sintético</strong> — Para jardines, verde todo el año sin mantenimiento.<br><br>💡 Estos materiales están diseñados para resistir intemperie.',
            suggestions: ['Ver Lambrín WPC exterior', 'Ver Cladding', 'Ver Zacate', 'Cotizar fachada']
          },
          {
            words: ['piso','pisos','suelo','piso para','baldosa'],
            text: '🏗️ <strong>Para pisos te recomendamos:</strong><br><br>• <strong>SPC</strong> — Muy resistente al agua, ideal cocinas y baños.<br>• <strong>WPC</strong> — Más cálido y confortable, ideal recámaras.<br>• <strong>Laminado</strong> — Más económico, para interiores de bajo tráfico.<br>• <strong>Deck sintético</strong> — Para exteriores y terrazas.',
            suggestions: ['Ver Pisos SPC', 'Ver Pisos WPC', 'Ver Laminado', 'Cotizar pisos']
          },
          {
            words: ['techo','cielo','plafon','plafond','cielo falso'],
            text: '🏢 <strong>Para plafones y cielos falsos te recomendamos:</strong><br><br>• <strong>Plafón PVC laminado</strong> — Imitación madera, inmune a humedad y moho.<br>• <strong>Plafón PVC ranurado</strong> — Diseño moderno, fácil instalación.<br><br>💡 No se cuartea, no absorbe humedad y no requiere mantenimiento.',
            suggestions: ['Ver Plafón PVC', 'Cotizar plafón', 'Hablar con asesor']
          },
          {
            words: ['muro 3d','panel decorativo','pared decorativa','relieve','textura pared'],
            text: '🎨 <strong>Para muros decorativos te recomendamos:</strong><br><br>• <strong>Paneles 3D</strong> — Transforman cualquier muro en una obra de arte. Disponibles en blanco, grises, madera, negro y dorado.<br><br>💡 Ideales para recámaras, salas, recepciones y fondos de TV.',
            suggestions: ['Ver Paneles 3D', 'Cotizar paneles 3D', 'Hablar con asesor']
          },
          {
            words: ['jardin','pasto','cesped','follaje','terraza verde','jardinera'],
            text: '🌿 <strong>Para jardines y exteriores verdes te recomendamos:</strong><br><br>• <strong>Zacate sintético</strong> — Verde todo el año sin riego ni poda.<br>• <strong>Follaje sintético</strong> — Para muros verdes y jardineras.<br><br>💡 Resistente a rayos UV, con garantía de 5 años.',
            suggestions: ['Ver Zacate', 'Cotizar zacate', 'Hablar con asesor']
          },
          {
            words: ['viga','vigas','viga decorativa','trabe','cubierta madera'],
            text: '🪵 <strong>Para vigas decorativas te recomendamos:</strong><br><br>• <strong>Vigas PVC</strong> — Más ligeras, fáciles de instalar, gran variedad de diseños.<br>• <strong>Vigas WPC</strong> — Aspecto de madera real sin mantenimiento.<br><br>💡 Ideales para interior y exterior.',
            suggestions: ['Ver Vigas', 'Cotizar vigas', 'Hablar con asesor']
          }
        ];
        
        let best = null, bestScore = 0;
        for (let reco of recoMap) {
          let score = 0;
          for (let w of reco.words) if (q.includes(w)) score += 1;
          if (score > bestScore) { bestScore = score; best = reco; }
        }
        // Si hay categoría detectada, bajar umbral para que recomendaciones parciales funcionen
        return bestScore >= (category ? 1 : 2) ? best : null;
      }
      
      // === EVENTOS ===
      window.toggleChat = function() {
        const wasActive = chatWindow.classList.contains('active');
        chatWindow.classList.toggle('active');
        if (!wasActive && chatWindow.classList.contains('active')) {
          clearBadge();
          if (chatBody.children.length === 0) {
            if (!renderHistory()) {
              showWelcome();
            } else {
              addInputField();
            }
          }
        }
      };
      
      window.chatBotProcess = function(rawText) {
        if (!rawText || !rawText.trim()) return;
        const text = rawText.trim();
        addMessage(text, true);
        saveHistory(text, true);
        removeInputs();
        
        const q = text.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
        
        // Manejar acciones especiales de botones
        if (text === 'Enviar cotización por WhatsApp') {
          sendQuoteToWhatsApp();
          setTimeout(() => {
            addMessage('✅ Se abrió WhatsApp con tu cotización. Envía el mensaje y un asesor te atenderá pronto. ¡Gracias por contactarnos! 🙌', false);
            saveHistory('✅ Se abrió WhatsApp con tu cotización. Envía el mensaje y un asesor te atenderá pronto. ¡Gracias por contactarnos! 🙌', false);
            showQuickReplies(['Ver productos', 'Hacer otra cotización', 'Hablar con asesor']);
            addInputField();
          }, 600);
          return;
        }
        if (text === 'Hacer otra cotización') {
          const result = startQuoteFlow();
          showTyping();
          setTimeout(() => {
            hideTyping();
            addMessage(result.text, false);
            saveHistory(result.text, false);
            showQuickReplies(result.suggestions);
            addInputField();
          }, 700);
          return;
        }
        
        let result;
        if (chatContext.quoteState) {
          result = handleQuoteStep(text, q);
        } else {
          result = findResponse(q, text);
        }
        
        showTyping();
        setTimeout(() => {
          hideTyping();
          addMessage(result.text, false);
          saveHistory(result.text, false);
          showQuickReplies(result.suggestions);
          addInputField();
        }, 700);
      };
      
      function showWelcome() {
        const msg = WELCOME_VARIANTS[Math.floor(Math.random() * WELCOME_VARIANTS.length)];
        addMessage(msg, false);
        saveHistory(msg, false);
        showQuickReplies(['Ver productos', 'Horarios', 'Cotización', 'Ubicación', '¿Tienen envío?']);
        addInputField();
      }
      
      // === UI PROFESIONAL: TYPING, BADGE, ETC. ===
      function showTyping() {
        hideTyping();
        const typing = document.createElement('div');
        typing.className = 'chat-message bot typing-indicator';
        typing.id = 'typingIndicator';
        typing.innerHTML = '<span></span><span></span><span></span>';
        chatBody.appendChild(typing);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function hideTyping() {
        const t = document.getElementById('typingIndicator');
        if (t) t.remove();
      }
      
      function incrementBadge() {
        if (!chatWindow.classList.contains('active')) {
          unreadCount++;
          const badge = document.getElementById('chatBadge');
          if (badge) {
            badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
            badge.style.display = 'flex';
          }
        }
      }
      
      function clearBadge() {
        unreadCount = 0;
        const badge = document.getElementById('chatBadge');
        if (badge) badge.style.display = 'none';
      }
      
      // Sobrescribir addMessage para incluir badge en mensajes del bot
      const originalAddMessage = addMessage;
      addMessage = function(text, isUser) {
        originalAddMessage(text, isUser);
        if (!isUser) incrementBadge();
      };
      
      // Cargar productos y datos de investigación
      fetch('products.json')
        .then(r => r.json())
        .then(data => { 
          allProducts = data.products || [];
          researchData = data.research || {};
        })
        .catch(() => { 
          allProducts = [];
          researchData = {};
        });
    })();

  </script>
'''
    return f"""  <footer>
    <div class="footer-logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></div>
    <div class="footer-info">
      <strong>ADI&#39;S DISEÑO & REMODELACIÓN</strong><br>
      Creando espacios, reinventando hogares.<br>
      {CONTACTO['ubicacion']}<br>
      Tel. MX: {CONTACTO['tel_mx']} · Tel. USA: {CONTACTO['tel_usa']}<br>
      {CONTACTO['email']}
    </div>
    <div class="footer-social">
      <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO["whatsapp_msg"].replace(' ', '%20')}" target="_blank" title="WhatsApp">&#128172;</a>
      <a href="{CONTACTO['facebook']}" target="_blank" title="Facebook">&#128220;</a>
    </div>
    <div class="copyright">© 2026 ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.</div>
  </footer>

  <!-- MOBILE BOTTOM NAV -->
  <nav class="mobile-bottom-nav">
    <a href="index.html"><span>&#127968;</span><span>Inicio</span></a>
    <a href="index.html#categorias"><span>&#128194;</span><span>Catálogo</span></a>
    <a href="proyectos.html"><span>&#128444;</span><span>Proyectos</span></a>
    <a href="contacto.html"><span>&#128222;</span><span>Contacto</span></a>
  </nav>

  <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO["whatsapp_msg"].replace(' ', '%20')}" class="whatsapp-float" target="_blank" title="Contáctanos por WhatsApp" aria-label="WhatsApp">
    <svg viewBox="0 0 24 24" width="32" height="32" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.008-.57-.008-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
    <span class="wa-tooltip">¿Dudas? Escribenos</span>
  </a>

  <button class="chatbot-float" onclick="toggleChat()" title="Asistente Virtual">&#129302;<span class="chatbot-badge" id="chatBadge">0</span></button>
  <div class="chatbot-window" id="chatbotWindow">
    <div class="chatbot-header">
      <h4>&#129302; Asistente ADIS</h4>
      <div class="chat-header-actions">
        <button class="chat-clear" onclick="clearAllChat()" title="Nueva conversación">&#128465;</button>
        <button class="chatbot-close" onclick="toggleChat()">&#10005;</button>
      </div>
    </div>
    <div class="chatbot-body" id="chatbotBody"></div>
  </div>


{chatbot_js}"""


def generate_index(categories):
    meta_desc = "Catálogo oficial de ADIS Diseño & Remodelación. Recubrimientos de alta gama: Placas PVC, Lambrín WPC, Plafón, Paneles 3D, Vigas, Pisos, Zacate y Cladding. Nogales, Sonora."
    meta_keywords = "ADIS, diseño, remodelación, paneles, WPC, PVC, recubrimientos, Nogales, Sonora, pisos, zacate, cladding"

    STAR_CATEGORIES = {'Lambrin WPC', 'Placas PVC'}
    
    # Tarjetas estrella (sección destacada)
    featured_cards = ''
    cat_cards = ''
    
    for cat in categories:
        total_prods = len(cat["direct_products"])
        for sub in cat["subcategories"]:
            total_prods += len(sub["products"])

        thumb_src = ''
        if cat["subcategories"] and cat["subcategories"][0]["products"]:
            thumb_src = f'img/{cat["slug"]}/{cat["subcategories"][0]["slug"]}/{cat["subcategories"][0]["products"][0]}'
        elif cat["direct_products"]:
            thumb_src = f'img/{cat["slug"]}/{cat["direct_products"][0]}'
        
        is_star = cat["name"] in STAR_CATEGORIES
        
        if is_star:
            desc = ''
            if cat["name"] == 'Lambrin WPC':
                desc = 'Wood Plastic Composite de alta gama. Resistente a la humedad, rayos UV y perfecto para interiores y exteriores. Nuestro producto más solicitado.'
            elif cat["name"] == 'Placas PVC':
                desc = 'Paneles rígidos tipo madera, texturizados y espejo. Acabado profesional con instalación rápida y garantía extendida.'
            
            featured_cards += f'''      <a href="{cat["filename"]}" class="featured-card reveal">
        <img src="{thumb_src}" alt="{cat["name"]}" loading="lazy">
        <div class="featured-card-overlay">
          <div class="star-label">&#11088; Producto Estrella</div>
          <h3>{cat["name"]}</h3>
          <p>{desc}</p>
        </div>
      </a>
'''
        
        star_badge = '<div class="star-badge">&#11088; Estrella</div>' if is_star else ''
        featured_class = ' featured' if is_star else ''
        
        cat_cards += f'''      <a href="{cat["filename"]}" class="cat-card reveal{featured_class}">
        {star_badge}<img src="{thumb_src}" alt="{cat["name"]}" loading="lazy">
        <div class="cat-card-overlay">
          <div class="cat-arrow">→</div>
          <h3>{cat["name"]}</h3>
          <span>{total_prods} productos</span>
        </div>
      </a>
'''

    info_cards = '''      <a href="1-placas-pvc.html" class="info-card">
        <div class="icon">✦</div>
        <h3>Placas PVC</h3>
        <p>Paneles rígidos de alta calidad tipo madera, texturizados y espejo. Ideales para interiores.</p>
      </a>
      <a href="2-lambrin-wpc.html" class="info-card">
        <div class="icon">◈</div>
        <h3>Lambrín WPC</h3>
        <p>Wood Plastic Composite para interior y exterior. Resistente a la humedad y rayos UV.</p>
      </a>
      <a href="7-pisos.html" class="info-card">
        <div class="icon">◉</div>
        <h3>Pisos & Zacate</h3>
        <p>Laminados, WPC, SPC, deck sintético y pasto artificial para todo tipo de espacios.</p>
      </a>
      <a href="5-paneles-tridimensionales.html" class="info-card">
        <div class="icon">✚</div>
        <h3>Cladding & 3D</h3>
        <p>Paneles decorativos tridimensionales y revestimientos de alta gama para fachadas.</p>
      </a>
'''

    # Iconos representativos por categoría
    CAT_ICONS = {
        'Placas PVC': '🪵',
        'Lambrin WPC': '🌲',
        'Revestimiento Flexible': '🪨',
        'Plafon PVC': '&#127968;',
        'Paneles tridimensionales': '🎨',
        'Vigas PVC': '📐',
        'Pisos': '🏗️',
        'Zacate': '🌿',
        'Cladding': '⛰️',
    }

    # Tarjetas de descarga por categoría
    downloads_html = ''
    for cat in categories:
        cat_slug_pdf = cat["name"].lower().replace(' ', '-').replace('ñ','n').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        pdf_name = f'catalogo_{cat_slug_pdf}.pdf'
        total_prods = len(cat["direct_products"])
        for sub in cat["subcategories"]:
            total_prods += len(sub["products"])
        icon = CAT_ICONS.get(cat["name"], '📄')
        downloads_html += f'''      <a href="catalogos/pdf/{pdf_name}" class="download-card" download>
        <span class="icon">{icon}</span>
        <div class="info">
          <h4>{cat["name"]}</h4>
          <span>{total_prods} productos · PDF</span>
        </div>
        <span class="arrow">⬇</span>
      </a>
'''

    pdf_url = "catalogos/pdf/catalogo_premium.pdf"

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="LOGO ADIS.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADIS | Diseño & Remodelación</title>
  <meta name="description" content="{meta_desc}">
  <meta name="keywords" content="{meta_keywords}">
  <meta property="og:title" content="ADIS | Diseño & Remodelación">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="ADIS | Diseño & Remodelación">
  <meta name="twitter:description" content="{meta_desc}">
  <meta name="twitter:image" content="{SITE_URL}LOGO%20ADIS.png">
  <link rel="canonical" href="{SITE_URL}">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
{ga_script()}
{organization_schema()}
{website_schema()}
</head>
<body>
  <canvas id="bg-canvas"></canvas>

{generate_header("index")}

  <!-- INICIO -->
  <section class="hero-home" id="inicio">
    <div class="hero-content">
      <img src="LOGO ADIS.png" alt="ADIS Logo">
      <div class="hero-badge">Catálogo 2025 — 2026</div>
      <h1>Transforma tus espacios con <em>ADIS</em></h1>
      <p>Recubrimientos de alta gama para interior y exterior. PVC, WPC, paneles 3D, pisos, zacate y cladding.</p>
      <a href="#categorias" class="btn-primary">Explorar Catálogo</a>
      <div class="search-hero">
        <div class="search-hero-title">🔎 Busca entre 250 productos</div>
        <span class="search-hero-icon">&#128269;</span>
        <input type="text" class="search-hero-input" id="searchHeroInput" placeholder="Escribe el nombre de un producto, color o material..." autocomplete="off" onfocus="openSpotlight()">
        <div class="search-hero-hint">Presiona <kbd style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:4px;font-family:inherit;">/</kbd> para buscar desde cualquier página</div>
      </div>
    </div>
  </section>

  <!-- NOSOTROS -->
  <section class="section-wrap-alt reveal" id="nosotros">
    <div class="section-header">
      <h2>Sobre ADIS</h2>
      <div class="divider"></div>
      <p>En ADI'S DISEÑO & REMODELACIÓN nos especializamos en ofrecer soluciones funcionales, estéticas y duraderas.</p>
    </div>
    <div class="info-grid">
{info_cards}    </div>
  </section>

  <!-- STATS -->
  <section class="stats-section reveal">
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-number" data-target="250">0</div>
        <div class="stat-label">Productos</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" data-target="9">0</div>
        <div class="stat-label">Categorías</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" data-target="50">0</div>
        <div class="stat-label">Proyectos Realizados</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" data-target="100">0</div>
        <div class="stat-label">Clientes Satisfechos</div>
      </div>
    </div>
  </section>

  <!-- PRODUCTOS ESTRELLA -->
  <section class="featured-section reveal" id="estrellas">
    <div class="section-header">
      <h2>&#11088; Productos Estrella</h2>
      <div class="divider"></div>
      <p>Los favoritos de nuestros clientes. Calidad premium que transforma cualquier espacio.</p>
    </div>
    <div class="featured-grid">
{featured_cards}    </div>
  </section>

  <!-- PRODUCTO DESTACADO: PVC MARMOL -->
  <section class="featured-product-section reveal" id="pvc-marmol">
    <div class="featured-product-wrap">
      <div class="featured-product-image">
        <span class="featured-product-badge">Producto Destacado</span>
        <img src="img/1-placas-pvc/Carrara%20Oscuro.jpg" alt="Hoja de PVC tipo Mármol Carrara Oscuro" loading="lazy">
      </div>
      <div class="featured-product-content">
        <h3>Hoja de PVC tipo Mármol</h3>
        <div class="subtitle">Elegancia y durabilidad para cualquier espacio interior</div>
        <p>La lámina de <strong>PVC tipo mármol</strong> es la solución decorativa perfecta si buscas añadir un toque de elegancia a tu hogar, oficina o espacio comercial. Fabricada con materiales de alta calidad, es a la vez <strong>duradera y ligera</strong>, por lo que es fácil de instalar y mantener.</p>
        <ul class="featured-product-features">
          <li>Resistente al <strong>agua, manchas y arañazos</strong></li>
          <li>Inversión que <strong>dura muchos años</strong></li>
          <li>Ideal para <strong>cocinas, baños, salas de estar</strong> y más</li>
          <li>Acabado profesional con <strong>garantía extendida</strong></li>
        </ul>
        <a href="1-placas-pvc.html" class="featured-product-cta">Ver en catálogo →</a>
      </div>
    </div>
  </section>

  <!-- CATÁLOGO -->
  <section class="section-wrap reveal" id="categorias">
    <div class="section-header">
      <h2>Nuestro Catálogo</h2>
      <div class="divider"></div>
      <p>Selecciona una categoría para ver los productos con su ficha técnica.</p>
    </div>
    <div class="cat-grid">
{cat_cards}    </div>
  </section>

  <!-- DESCARGAS DE CATÁLOGOS PDF -->
  <section class="section-wrap downloads-section reveal" id="descargas">
    <div class="section-header">
      <h2>📥 Descargas</h2>
      <div class="divider"></div>
      <p class="downloads-lead">Descarga nuestros catálogos en PDF para consultarlos sin conexión o compartirlos con tu cliente.</p>
    </div>
    <div class="downloads-main">
      <a href="catalogos/pdf/catalogo_premium.pdf" class="download-complete" download>
        <span class="icon">📚</span>
        <div>
          <div>Descargar catálogo completo</div>
          <span class="sub">Todas las categorías en un solo PDF</span>
        </div>
      </a>
    </div>
    <div class="download-grid">
{downloads_html}    </div>
  </section>

{generate_testimonios()}

{modal_cotizar_html()}
{generate_footer()}
</body>
</html>
'''
    with open(BASE_DIR / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ index.html generado")


def generate_contacto():
    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="LOGO ADIS.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contacto | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Contacta a ADIS Diseño & Remodelación. WhatsApp, teléfono MX, teléfono USA y correo electrónico.">
  <meta property="og:title" content="Contacto | ADIS Diseño & Remodelación">
  <meta property="og:description" content="Contacta a ADIS Diseño & Remodelación. WhatsApp, teléfono MX, teléfono USA y correo electrónico.">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{SITE_URL}contacto.html">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Contacto | ADIS Diseño & Remodelación">
  <meta name="twitter:description" content="Contacta a ADIS Diseño & Remodelación. WhatsApp, teléfono MX, teléfono USA y correo electrónico.">
  <meta name="twitter:image" content="{SITE_URL}LOGO%20ADIS.png">
  <link rel="canonical" href="{SITE_URL}contacto.html">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
{ga_script()}
{organization_schema()}
{breadcrumb_schema([('Inicio', SITE_URL), ('Contacto', f'{SITE_URL}contacto.html')])}
</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header("contacto")}

  <section class="hero-cat" style="padding-top: 8rem;">
    <h1>Contacto</h1>
    <p>Estamos listos para ayudarte a transformar tu espacio. Contáctanos por cualquier medio.</p>
  </section>

  <section class="section-wrap">
    <div class="section-header">
      <h2>¿Cómo podemos ayudarte?</h2>
      <div class="divider"></div>
    </div>
    <div class="contact-grid">
      <div class="contact-card">
        <div class="icon">📱</div>
        <h3>WhatsApp MX</h3>
        <a href="https://wa.me/{CONTACTO["whatsapp"]}" target="_blank">{CONTACTO["tel_mx"]}</a>
      </div>
      <div class="contact-card">
        <div class="icon">&#128222;</div>
        <h3>Teléfono USA</h3>
        <a href="tel:+15208392877">{CONTACTO["tel_usa"]}</a>
      </div>
      <div class="contact-card">
        <div class="icon">✉️</div>
        <h3>Correo</h3>
        <a href="mailto:{CONTACTO["email"]}">{CONTACTO["email"]}</a>
      </div>
      <div class="contact-card">
        <div class="icon">📍</div>
        <h3>Ubicación</h3>
        <p>{CONTACTO["ubicacion"]}</p>
      </div>
      <div class="contact-card">
        <div class="icon">&#128220;</div>
        <h3>Facebook</h3>
        <a href="{CONTACTO["facebook"]}" target="_blank">Visitar página</a>
      </div>
    </div>
    <div style="text-align: center; margin-top: 3rem; max-width: 900px; margin: 3rem auto 0;">
      <div style="border-radius: 8px; overflow: hidden; border: 1px solid rgba(197,160,89,0.2); margin-bottom: 1.5rem;">
        <iframe src="https://maps.google.com/maps?q=31.3088527,-110.9308403&z=17&output=embed" width="100%" height="400" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
      </div>
      <a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" class="btn-outline">📍 Ver en Google Maps</a>
    </div>
    <div style="text-align: center; margin-top: 3rem;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
    </div>
  </section>

{generate_footer()}
</body>
</html>
'''
    with open(BASE_DIR / 'contacto.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ contacto.html generado")


def generate_category_page(cat, categories):
    """Genera página de una categoría con subcategorías y productos."""
    import unicodedata

    # Prev / Next navegación entre categorías
    cat_index = [i for i, c in enumerate(categories) if c["slug"] == cat["slug"]][0]
    prev_cat = categories[cat_index - 1] if cat_index > 0 else None
    next_cat = categories[cat_index + 1] if cat_index < len(categories) - 1 else None
    
    cat_nav_html = ''
    if prev_cat or next_cat:
        nav_parts = []
        if prev_cat:
            nav_parts.append(f'<a href="{prev_cat["filename"]}" class="cat-nav-btn">← {prev_cat["name"]}</a>')
        if next_cat:
            nav_parts.append(f'<a href="{next_cat["filename"]}" class="cat-nav-btn next">{next_cat["name"]} →</a>')
        cat_nav_html = '  <div class="cat-nav">\n    ' + '\n    '.join(nav_parts) + '\n  </div>\n'

    # Breadcrumbs
    breadcrumbs_html = f'''  <div class="breadcrumbs">
    <a href="index.html">Inicio</a> <span>/</span> <a href="index.html#categorias">Catálogo</a> <span>/</span> <span style="color:var(--gold);">{cat["name"]}</span>
  </div>
'''

    # Seleccionar imagen de fondo representativa para el hero
    hero_bg = ''
    if cat["subcategories"] and cat["subcategories"][0]["products"]:
        hero_bg = f'img/{cat["slug"]}/{cat["subcategories"][0]["slug"]}/{cat["subcategories"][0]["products"][0]}'
    elif cat["direct_products"]:
        hero_bg = f'img/{cat["slug"]}/{cat["direct_products"][0]}'

    # Reordenar subcategorías: Placas PVC debe tener tipo espejo primero
    subs = list(cat["subcategories"])
    if cat["name"] == 'Placas PVC':
        subs.sort(key=lambda s: 0 if 'espejo' in s["name"].lower() else 1)

    # Índice de subcategorías
    subcat_nav_links = ''
    for sub in subs:
        if sub["products"]:
            sub_slug = sub["slug"]
            sub_name = sub["name"]
            subcat_nav_links += f'<a href="#{sub_slug}">{sub_name}</a>' + '\n    '
    subcat_nav_html = f'''  <div class="subcat-nav">
    {subcat_nav_links}</div>
''' if subcat_nav_links else ''

    # Set para deduplicación por nombre normalizado
    seen_products = set()
    def norm_name(prod_file):
        name = os.path.splitext(prod_file)[0]
        return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII').lower().replace(' ', '')
    def is_dup(prod_file):
        key = norm_name(prod_file)
        if key in seen_products:
            return True
        seen_products.add(key)
        return False

    sections_html = ''
    
    # Para Placas PVC: productos directos PRIMERO (son los más vendidos - tipo espejo)
    accessories_html = ''
    if cat["name"] == 'Placas PVC' and cat["direct_products"]:
        direct_products_html = ''
        acc_names = {'perfil', 'angulo'}
        main_products = []
        acc_products = []
        for prod_file in cat["direct_products"]:
            stem = os.path.splitext(prod_file)[0].lower().replace(' ', '')
            if any(stem.startswith(a) for a in acc_names):
                acc_products.append(prod_file)
            else:
                main_products.append(prod_file)
        
        for prod_file in main_products:
            if is_dup(prod_file):
                continue
            direct_products_html += product_card_html(prod_file, cat)
        
        for prod_file in acc_products:
            if is_dup(prod_file):
                continue
            accessories_html += product_card_html(prod_file, cat)
        
        cat_specs = generate_specs_table('Placas PVC Tipo espejo')
        sections_html += f'''  <section class="subcat-section reveal">
    <div class="subcat-header">
      <h3>&#11088; Más Vendidos — Placas PVC Tipo Espejo</h3>
      <span class="subcat-count">{len(main_products)} productos</span>
      <div class="subcat-divider"></div>
    </div>
{cat_specs}    <div class="products-grid">
{direct_products_html}    </div>
  </section>
'''

    # Construir secciones de subcategorías
    for sub in subs:
        if not sub["products"]:
            continue

        specs_html = generate_specs_table(sub["name"])

        products_html = ''
        for prod_file in sub["products"]:
            if is_dup(prod_file):
                continue
            products_html += product_card_html(prod_file, cat, sub)

        sections_html += f'''  <section class="subcat-section reveal" id="{sub["slug"]}">
    <div class="subcat-header">
      <h3>{sub["name"]}</h3>
      <span class="subcat-count">{len(sub["products"])} productos</span>
      <div class="subcat-divider"></div>
    </div>
{specs_html}    <div class="products-grid">
{products_html}    </div>
  </section>
'''

    # Sección de accesorios para Placas PVC (al final del catálogo)
    if cat["name"] == 'Placas PVC' and accessories_html:
        acc_count = accessories_html.strip().count('product-card reveal')
        acc_specs = generate_specs_table('Accesorios placas PVC')
        sections_html += f'''  <section class="subcat-section reveal" id="accesorios">
    <div class="subcat-header">
      <h3>🔩 Accesorios</h3>
      <span class="subcat-count">{acc_count} producto{"s" if acc_count != 1 else ""}</span>
      <div class="subcat-divider"></div>
    </div>
{acc_specs}    <div class="products-grid">
{accessories_html}    </div>
  </section>
'''

    # Productos directos para otras categorías (no Placas PVC que ya se mostró arriba)
    if cat["name"] != 'Placas PVC' and cat["direct_products"]:
        direct_products_html = ''
        for prod_file in cat["direct_products"]:
            if is_dup(prod_file):
                continue
            direct_products_html += product_card_html(prod_file, cat)

        # Clave de specs para productos directos según categoría
        direct_specs_map = {
            '3-revestimiento-flexible': 'Revestimiento Flexible',
            '4-plafon-pvc': 'Plafon PVC directos',
            '9-cladding': 'Cladding',
        }
        direct_specs_key = direct_specs_map.get(cat["slug"])
        direct_specs = generate_specs_table(direct_specs_key) if direct_specs_key else ''

        sections_html += f'''  <section class="subcat-section reveal">
    <div class="subcat-header">
      <h3>Productos {cat["name"]}</h3>
      <span class="subcat-count">{len(cat["direct_products"])} productos</span>
      <div class="subcat-divider"></div>
    </div>
{direct_specs}    <div class="products-grid">
{direct_products_html}    </div>
  </section>
'''

    # Galería de hojas reales (solo para Placas PVC)
    real_sheets_html = ''
    if cat["name"] == 'Placas PVC':
        media_dir = BASE_DIR / 'media'
        try:
            real_imgs = sorted([f for f in os.listdir(media_dir) if f.startswith('pvc-real-') and f.lower().endswith(('.jpg', '.jpeg'))])
        except (OSError, PermissionError):
            real_imgs = []
        if real_imgs:
            gallery_items = ''
            for img in real_imgs:
                gallery_items += f'''      <div class="real-sheets-item" onclick="openLightbox('media/{img}', 'Hoja real de PVC')">
        <img src="media/{img}" alt="Hoja real de PVC" loading="lazy">
        <span class="real-sheets-badge">Foto Real</span>
      </div>
'''
            real_sheets_html = f'''  <section class="real-sheets-section">
    <div class="section-header">
      <h2>Hojas Reales de PVC</h2>
      <div class="divider"></div>
      <p>Fotos reales de nuestro showroom. Sin filtros, sin edits.</p>
    </div>
    <div class="real-sheets-grid">
{gallery_items}    </div>
  </section>
'''

    wa_hero_url = whatsapp_url(CONTACTO["whatsapp"], "Hola ADIS, vi el catalogo de " + cat["name"] + " y quiero asesoria para elegir el mejor producto para mi proyecto.")
    pdf_url = "catalogos/pdf/catalogo_" + cat["slug"] + ".pdf"

    # Schemas de productos para esta categoría
    product_schemas_html = ''
    for sub in cat["subcategories"]:
        for prod_file in sub["products"]:
            prod_name = os.path.splitext(prod_file)[0]
            img_url = f"{SITE_URL}img/{cat['slug']}/{sub['slug']}/{prod_file}"
            prod_url = f"{SITE_URL}{cat['filename']}#{sub['slug']}"
            product_schemas_html += product_schema(prod_name, cat["name"], sub["name"], img_url, prod_url) + '\n'
    for prod_file in cat["direct_products"]:
        prod_name = os.path.splitext(prod_file)[0]
        img_url = f"{SITE_URL}img/{cat['slug']}/{prod_file}"
        prod_url = f"{SITE_URL}{cat['filename']}"
        product_schemas_html += product_schema(prod_name, cat["name"], None, img_url, prod_url) + '\n'

    breadcrumb_html = breadcrumb_schema([
        ("Inicio", SITE_URL),
        ("Catálogo", f"{SITE_URL}index.html#categorias"),
        (cat["name"], f"{SITE_URL}{cat['filename']}")
    ])

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="LOGO ADIS.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cat["name"]} | ADIS Catálogo</title>
  <meta name="description" content="{cat["name"]} - ADIS Diseño & Remodelación. Explora nuestros {cat['total_products']} productos y solicita tu cotización.">
  <meta property="og:title" content="{cat["name"]} | ADIS Catálogo">
  <meta property="og:description" content="{cat["name"]} - ADIS Diseño & Remodelación. Explora nuestros {cat['total_products']} productos y solicita tu cotización.">
  <meta property="og:image" content="{SITE_URL}{hero_bg}">
  <meta property="og:url" content="{SITE_URL}{cat["filename"]}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{cat["name"]} | ADIS Catálogo">
  <meta name="twitter:description" content="{cat["name"]} - ADIS Diseño & Remodelación. Explora nuestros {cat['total_products']} productos y solicita tu cotización.">
  <meta name="twitter:image" content="{SITE_URL}{hero_bg}">
  <link rel="canonical" href="{SITE_URL}{cat["filename"]}">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
{ga_script()}
{organization_schema()}
{breadcrumb_html}
{product_schemas_html}</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header(cat["slug"])}
{breadcrumbs_html}
  <section class="hero-cat-bg" style="background-image: url('{hero_bg}');">
    <div class="hero-cat-content">
      {'<div class="hero-star-badge">&#11088; Producto Estrella</div>' if cat["name"] in ("Lambrin WPC", "Placas PVC") else '<div class="hero-cat-badge">Categoría</div>'}
      <h1>{cat["name"]}</h1>
      <p>Explora nuestra línea de {cat["name"].lower()} con {cat["total_products"]} productos disponibles. Solicita tu cotización.</p>
      <div class="hero-cat-actions">
        <a href="{wa_hero_url}" class="btn-primary" target="_blank">Asesoria por WhatsApp</a>
        <a href="{pdf_url}" class="btn-outline" download>Descargar catalogo PDF</a>
      </div>
    </div>
  </section>

{subcat_nav_html}{real_sheets_html}
{category_filters_html(cat)}
{sections_html}
{cat_nav_html}
  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
      <a href="contacto.html" class="btn-outline">Contactar</a>
    </div>
  </section>

{generate_testimonios()}
{modal_cotizar_html()}
{category_filters_js()}
{generate_footer()}
</body>
</html>
'''
    filepath = BASE_DIR / cat["filename"]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'{cat["filename"]} generado')


def sync_media():
    """Copia TODAS las fotos y videos de Material de Facebock a media/ con nombres limpios (sync incremental)."""
    src_dir = BASE_DIR / 'Material de Facebock'
    media_dir = BASE_DIR / 'media'
    if not src_dir.exists():
        return
    media_dir.mkdir(parents=True, exist_ok=True)
    
    img_exts = ('.jpg', '.jpeg', '.png')
    vid_exts = ('.mp4', '.mov', '.webm')
    
    # Mapeo manual para archivos conocidos con nombres limpios
    known_names = {
        'antes.jpg': 'antes.jpg',
        'despues.jpg': 'despues.jpg',
        'ejemplo de tapiz.jpg': 'ejemplo-tapiz.jpg',
        '666284575_122140320836994986_788780118445842656_n.jpg': 'proyecto-recepcion.jpg',
        '670492075_122140320794994986_7881130192341646317_n.jpg': 'proyecto-recepcion-thumb.jpg',
        '647152617_122136539756994986_7884244820762960889_n.jpg': 'equipo-adis.jpg',
        'Remoledacion de habitacion.mp4': 'video-habitacion.mp4',
        'remoledacion de consultorio.mp4': 'video-consultorio.mp4',
    }
    
    # Escanear recursivamente todas las subcarpetas
    all_files = []
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.lower().endswith(img_exts + vid_exts):
                all_files.append((Path(root) / f, f))
    all_files.sort(key=lambda x: x[1])
    
    # Generar mapeo fuente -> destino con contadores reiniciados (nombres estables mientras no cambien las fuentes)
    auto_img = 0
    auto_vid = 0
    auto_pvc = 0
    mapping = {}
    expected_names = set()
    for fpath, fname in all_files:
        if fname in known_names:
            dst_name = known_names[fname]
        elif 'pvc' in fpath.parent.name.lower() or 'pvc' in fname.lower():
            auto_pvc += 1
            ext = Path(fname).suffix.lower()
            dst_name = f'pvc-real-{auto_pvc:02d}{ext}'
        elif fname.lower().endswith(img_exts):
            auto_img += 1
            ext = Path(fname).suffix.lower()
            dst_name = f'proyecto-{auto_img:02d}{ext}'
        elif fname.lower().endswith(vid_exts):
            auto_vid += 1
            ext = Path(fname).suffix.lower()
            dst_name = f'video-{auto_vid:02d}{ext}'
        else:
            continue
        mapping[fpath] = dst_name
        expected_names.add(dst_name.lower())
    
    # Eliminar archivos huérfanos en media/ (ya no tienen fuente en el mapeo actual)
    removed = 0
    for existing in list(media_dir.iterdir()):
        if existing.is_file() and existing.name.lower() not in expected_names:
            try:
                existing.unlink()
                removed += 1
            except Exception:
                pass
    
    copied = 0
    errors = []
    for src_path, dst_name in mapping.items():
        if not src_path.exists():
            errors.append(f"  [ERROR] No existe: {src_path}")
            continue
        dst = media_dir / dst_name
        if _copy_if_needed(src_path, dst):
            copied += 1
    if errors:
        print(f"ADVERTENCIA: {len(errors)} archivos de media no se pudieron copiar:")
        for e in errors[:10]:
            print(e)
    print(f"Media sincronizada: {copied} copiados, {removed} huérfanos eliminados ({auto_img} imgs + {auto_pvc} pvc + {auto_vid} vids)")


# Datos extraídos de fichas técnicas
SPECS_DATA = {
    # 1. Placas PVC
    'Placas PVC tipo madera': {
        'Material': 'PVC',
        'Dimensiones': '2440 x 1220 x 3 mm',
        'Presentación': '2.977 m²/pz, 1 pz/Caja, 19 kg/pz',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Placas PVC Texturizadas': {
        'Material': 'PVC',
        'Dimensiones': '2440 x 1220 x 5 mm',
        'Presentación': '2.977 m²/pz, 1 pz/Caja, 10.5 kg/pz',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Placas PVC Tipo espejo': {
        'Material': 'PVC',
        'Dimensiones': '2440 x 1220 x 5 mm',
        'Presentación': '2.977 m²/pz, 1 pz/Caja, 10.5 kg/pz',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    # 2. Lambrin WPC
    'Lambrin Interior': {
        'Material': 'WPC',
        'Dimensiones': '2900 x 160 x 24 mm',
        'Presentación': '0.464 m²/pz, 14 pz/Caja, 6.496 m²/caja, 30.5 Kg/caja',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Lambrin Exterior': {
        'Material': 'WPC',
        'Dimensiones': '2850 x 200 x 26 mm',
        'Presentación': '2.28 m²/Caja, 4 pz/Caja, 34 kg/Caja',
        'Garantía': '10 años',
        'Uso': 'Exterior',
    },
    'Desigual': {
        'Material': 'WPC',
        'Dimensiones': '2900 x 149 x 14 mm',
        'Presentación': '0.4321 m²/pz, 4.321 m²/caja, 10 pz/caja, 26 kg/caja',
        'Garantía': 'Consultar ficha técnica',
        'Uso': 'Interior',
    },
    'Media luna': {
        'Material': 'WPC',
        'Dimensiones': '2900 x 159 x 15 mm',
        'Presentación': '4.611 m²/caja, 10 pzas/Caja',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Media luna PS': {
        'Material': 'PS (Poliestireno)',
        'Dimensiones': '2900 x 152 x 12 mm',
        'Presentación': '6.171 m²/caja, 14 pzas/Caja',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    # 3. Revestimiento Flexible
    'Revestimiento Flexible': {
        'Material': 'Revestimiento flexible',
        'Dimensiones': '900 x 600 mm / 1200 x 600 mm',
        'Presentación': '0.54/0.72 m²/pz, 13.5/0.72 m²/Caja, 25/1 pz/Caja',
        'Garantía': '35 años',
        'Uso': 'Interior',
    },
    # 4. Plafon PVC
    'Plafon pvc laminado': {
        'Material': 'PVC',
        'Dimensiones': '2900 x 250 x 8 mm',
        'Presentación': '0.725 m²/pz, 10 pz/Caja, 7.25 m²/Caja, 2.92 kg/m²',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Plafon Laminado wood': {
        'Material': 'PVC',
        'Dimensiones': '2800 x 300 x 9 mm',
        'Presentación': '0.84 m²/pz, 10 pz/Caja, 8.4 m²/Caja, 2.8 kg/m²',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Plafon Ranurado': {
        'Material': 'PVC',
        'Dimensiones': '2900 x 250 x 8 mm',
        'Presentación': 'Por pieza, 2.90 m largo x 0.25 m ancho',
        'Garantía': '15 años',
        'Uso': 'Interior',
        'Acabado': 'Ranurado decorativo',
    },
    'Plafon PVC directos': {
        'Material': 'PVC',
        'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Accesorios placas PVC': {
        'Material': 'PVC',
        'Dimensiones': 'Perfil T: 7 x 3 x 2440 mm / Ángulo: 8 x 8 x 2440 mm',
        'Presentación': 'Por pieza',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    # 5. Paneles tridimensionales
    'Blanco': {
        'Material': 'PVC / Compuesto',
        'Dimensiones': '500 x 500 mm, Espesor varias',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja, 2.5/10 m²/caja',
        'Garantía': '1 año',
        'Uso': 'Residencial y comercial',
    },
    'Grises': {
        'Material': 'PVC / Compuesto',
        'Dimensiones': '500 x 500 mm, Espesor varias',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja, 2.5/10 m²/caja',
        'Garantía': '1 año',
        'Uso': 'Residencial y comercial',
    },
    'Madera': {
        'Material': 'PVC / Compuesto',
        'Dimensiones': '500 x 500 mm, Espesor varias',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja, 2.5/10 m²/caja',
        'Garantía': '1 año',
        'Uso': 'Residencial y comercial',
    },
    'Negro': {
        'Material': 'PVC / Compuesto',
        'Dimensiones': '500 x 500 mm, Espesor varias',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja, 2.5/10 m²/caja',
        'Garantía': '1 año',
        'Uso': 'Residencial y comercial',
    },
    'Oro': {
        'Material': 'PVC / Compuesto',
        'Dimensiones': '500 x 500 mm, Espesor varias',
        'Presentación': '0.25 m²/pz, 10/40 pz/caja, 2.5/10 m²/caja',
        'Garantía': '1 año',
        'Uso': 'Residencial y comercial',
    },
    # 6. Vigas PVC
    'Interior': {
        'Material': 'WPC',
        'Dimensiones': '2900 x 100 x 50 mm / 2900 x 50 x 50 mm',
        'Presentación': '1 pz/Caja',
        'Garantía': '15 años',
        'Uso': 'Interior',
    },
    'Exterior': {
        'Material': 'WPC',
        'Dimensiones': '2850 x 120 x 70 mm',
        'Presentación': '1 pz/Caja',
        'Garantía': '15 años sin carga',
        'Uso': 'Exterior',
    },
    # 7. Pisos
    'Laminado': {
        'Material': 'Laminado',
        'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica',
        'Garantía': 'Consultar ficha técnica',
        'Uso': 'Residencial',
    },
    'WPC': {
        'Material': 'WPC',
        'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica',
        'Garantía': 'Consultar ficha técnica',
        'Uso': 'Residencial',
    },
    'SPC': {
        'Material': 'SPC',
        'Dimensiones': '625 x 125 mm, Espesor 5+IXPE 1.5 mm',
        'Presentación': '1.875 m²/Caja, 20.25 kg/Caja',
        'Garantía': '12 años (Residencial) / 3 años (Comercial)',
        'Uso': 'Residencial / Comercial ligero',
    },
    'Deck Sintetico': {
        'Material': 'WPC / Compuesto',
        'Dimensiones': '2200 x 145 x 22.5 mm',
        'Presentación': '1.276 m²/Caja, 4 pz/Caja, 20 kg/Caja',
        'Garantía': '18 años',
        'Uso': 'Residencial',
    },
    # 8. Zacate
    'Follaje Sintetico': {
        'Material': 'Polietileno / Sintético',
        'Dimensiones': '25 x 25 cm',
        'Presentación': 'Consultar ficha técnica',
        'Garantía': '5 años',
        'Uso': 'Exterior / Decorativo',
    },
    'Pasto Recreativo': {
        'Material': 'Polietileno / Sintético',
        'Dimensiones': '3.75 x 2.5 m / 3.98 x 30 m (rollos)',
        'Presentación': '93.75 m²/Rollo, 119.4 m²/Rollo',
        'Garantía': 'Consultar ficha técnica',
        'Uso': 'Exterior / Recreativo',
    },
    # 9. Cladding
    'Cladding': {
        'Material': 'WPC / Compuesto',
        'Dimensiones': '2900 x 99 x 14 mm',
        'Presentación': '3.445 m²/caja, 12 pz/Caja',
        'Garantía': '15 años',
        'Uso': 'Exterior',
    },
    'Placa tipo roca': {
        'Material': 'WPC / Compuesto',
        'Dimensiones': '1200 x 600 x 35 mm',
        'Presentación': '4 pza/caja, 0.72 m²/pza, 2.3 kg/pza',
        'Garantía': '3 años (Interior)',
        'Uso': 'Interior',
    },
}


def generate_specs_table(product_name):
    """Genera tabla de especificaciones técnicas en formato texto."""
    data = SPECS_DATA.get(product_name, {})
    items = []
    # Campos principales en orden fijo (sin Garantía por ahora)
    main_labels = ('Material', 'Dimensiones', 'Presentación', 'Uso')
    for label in main_labels:
        value = data.get(label, 'Consultar ficha técnica')
        items.append(f'<div class="spec-item"><span class="spec-label">{label}</span><span class="spec-value">{value}</span></div>')
    # Campos adicionales definidos en la ficha técnica (ej. Acabado)
    for label, value in data.items():
        if label not in main_labels and label != 'Garantía':
            items.append(f'<div class="spec-item"><span class="spec-label">{label}</span><span class="spec-value">{value}</span></div>')
    return '    <div class="specs-bar reveal">\n      ' + '\n      '.join(items) + '\n    </div>\n'


def generate_testimonios():
    """Genera formulario de testimonios que envía a WhatsApp para revisión manual."""
    return '''
  <!-- TESTIMONIOS -->
  <section class="section-wrap reveal" style="padding-top: 2rem;">
    <div class="section-header">
      <h2>Testimonios de Clientes</h2>
      <div class="divider"></div>
      <p>¿Ya usaste nuestros productos? Comparte tu experiencia y ayuda a otros a decidirse.</p>
    </div>
    <div style="max-width: 1100px; margin: 0 auto; padding: 0 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">Excelente calidad en las placas PVC tipo espejo. Transformaron completamente mi sala de estar. La instalación fue súper rápida y el acabado se ve de lujo.</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">MG</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">María G.</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — Placas PVC, Nogales</div>
          </div>
        </div>
      </div>
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">Compré el lambrín WPC para el exterior de mi consultorio y quedó espectacular. Resiste perfectamente el sol y la lluvia. 100% recomendado.</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">CR</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">Dr. Carlos R.</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — Lambrín WPC, Rio Rico</div>
          </div>
        </div>
      </div>
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">El equipo de ADIS me ayudó a elegir los pisos SPC para toda mi casa. Me dieron asesoría de primera y el precio fue muy competitivo. Quedé encantada.</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">FL</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">Familia López</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — Pisos SPC, Nogales</div>
          </div>
        </div>
      </div>
    </div>
    <div style="max-width: 600px; margin: 0 auto; padding: 0 1rem;">
      <form id="testimonioForm" onsubmit="enviarTestimonio(event)" style="display: flex; flex-direction: column; gap: 1rem;">
        <input type="text" id="tNombre" placeholder="Tu nombre" required
          style="padding: 0.9rem 1.2rem; background: rgba(42,42,42,0.8); border: 1px solid rgba(197,160,89,0.3); border-radius: 8px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 0.9rem; backdrop-filter: blur(8px); transition: all 0.3s;"
          onfocus="this.style.borderColor='var(--gold)';this.style.boxShadow='0 0 15px rgba(197,160,89,0.15)'" onblur="this.style.borderColor='rgba(197,160,89,0.3)';this.style.boxShadow='none'">
        <textarea id="tComentario" placeholder="¿Qué te pareció el producto o servicio?" required rows="4"
          style="padding: 0.9rem 1.2rem; background: rgba(42,42,42,0.8); border: 1px solid rgba(197,160,89,0.3); border-radius: 8px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 0.9rem; backdrop-filter: blur(8px); resize: vertical; transition: all 0.3s;"
          onfocus="this.style.borderColor='var(--gold)';this.style.boxShadow='0 0 15px rgba(197,160,89,0.15)'" onblur="this.style.borderColor='rgba(197,160,89,0.3)';this.style.boxShadow='none'"></textarea>
        <input type="text" id="tProducto" placeholder="Producto o categoría que compraste (opcional)"
          style="padding: 0.9rem 1.2rem; background: rgba(42,42,42,0.8); border: 1px solid rgba(197,160,89,0.3); border-radius: 8px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 0.9rem; backdrop-filter: blur(8px); transition: all 0.3s;"
          onfocus="this.style.borderColor='var(--gold)';this.style.boxShadow='0 0 15px rgba(197,160,89,0.15)'" onblur="this.style.borderColor='rgba(197,160,89,0.3)';this.style.boxShadow='none'">
        <button type="submit" class="btn-primary" style="align-self: center; margin-top: 0.5rem;">&#128233; Enviar Testimonio</button>
      </form>
      <div style="text-align: center; margin-top: 1.2rem; font-size: 0.8rem; color: rgba(245,245,245,0.5); line-height: 1.6;">
        Los testimonios son revisados antes de publicarse.<br>
        También puedes enviarlos directamente por 
        <a href="https://wa.me/15208392877?text=Hola%20ADIS,%20quiero%20dejar%20un%20testimonio" target="_blank" style="color: var(--gold); text-decoration: none; font-weight: 600;">WhatsApp &#128172;</a>
      </div>
    </div>
  </section>
  <script>
    function enviarTestimonio(e) {
      e.preventDefault();
      const nombre = document.getElementById('tNombre').value.trim();
      const comentario = document.getElementById('tComentario').value.trim();
      const producto = document.getElementById('tProducto').value.trim();
      let msg = 'Hola ADIS, soy ' + nombre + '. Quiero dejar un testimonio:';
      msg += '%0A%0A' + comentario;
      msg += '%0A%0AProducto/Categoría: ' + (producto || 'No especificado');
      msg += '%0A%0APágina: ' + window.location.href;
      window.open('https://wa.me/15208392877?text=' + encodeURIComponent(msg.replace(/%0A/g, '\\n')), '_blank');
      alert('¡Gracias ' + nombre + '! Tu testimonio se envió por WhatsApp. Será revisado y publicado pronto.');
      e.target.reset();
    }
  </script>
'''

def _extract_curiosos_cards(text):
    """Extrae tarjetas de datos curiosos del texto markdown."""
    import re
    clean_text = text.replace('---', '').strip()
    items = re.split(r'\n\n+(?=#{2,3} |\*\*)', clean_text)
    cards = ''
    item_count = 0
    for item in items:
        item = item.strip()
        if not item or len(item) < 20:
            continue
        title = None
        title_match = re.search(r'#{2,3}\s*(.+?)(?:\n|$)', item)
        if title_match:
            title = title_match.group(1)
        else:
            title_match = re.search(r'^\*\*\s*(.+?)\s*\*\*', item)
            if title_match:
                title = title_match.group(1)
        if not title:
            continue
        title = re.sub(r'^[\s\U0001F300-\U0001F9FF]+', '', title).strip()
        if not title:
            continue
        if title_match and title_match.group(0).startswith('#'):
            desc = re.sub(r'#{2,3}\s*.+?(?:\n|$)', '', item, count=1)
        else:
            desc = re.sub(r'^\*\*\s*' + re.escape(title) + r'\s*\*\*', '', item)
        desc = desc.strip()
        desc = re.sub(r'\s+', ' ', desc)
        if not desc:
            continue
        desc = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', desc)
        item_count += 1
        icons = ['🔬', '🌍', '🔥', '🖨️', '⚖️', '🧪', '🌲', '🌧️', '&#127968;', '📐', '🪨', '🎨']
        icon = icons[(item_count-1) % len(icons)]
        if len(desc) > 130:
            desc_trunc = desc[:127] + '...'
            card_p = f'''<p class="sq-card-text">
      <span class="sq-short">{desc_trunc}</span>
      <span class="sq-full" style="display:none">{desc}</span>
      <span class="sq-card-readmore" onclick="sqToggle(this)">Leer más</span>
    </p>'''
        else:
            card_p = f'<p class="sq-card-text">{desc}</p>'
        cards += f'''      <div class="sq-card">
        <span class="sq-card-number">{item_count:02d}</span>
        <span class="sq-card-icon">{icon}</span>
        <h3>{title}</h3>
        {card_p}
      </div>
'''
    return cards


def _extract_faqs_html(text):
    """Extrae FAQs del texto markdown."""
    import re
    clean_faqs = text.replace('---', '').strip()
    qa_pairs = re.findall(r'\*\*❓\s*(.+?)\*\*\s*\n?>?\s*(.+?)(?=\n\n\*\*❓|\Z)', clean_faqs, re.DOTALL)
    if not qa_pairs:
        qa_pairs = re.findall(r'#{2,3}\s*(.+?)(?:\n|$)\s*\n?(.+?)(?=\n#{2,3}|\Z)', clean_faqs, re.DOTALL)
    faqs = ''
    for q, a in qa_pairs:
        q_clean = q.strip()
        a_clean = a.strip().replace('\n', ' ')
        a_clean = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', a_clean)
        if len(a_clean) > 200:
            a_clean = a_clean[:197] + '...'
        faqs += f'''      <div class="sq-faq-item">
        <div class="sq-faq-q" onclick="this.parentElement.classList.toggle('open')">{q_clean}</div>
        <div class="sq-faq-a">{a_clean}</div>
      </div>
'''
    return faqs


def _extract_curiosos_data(text):
    """Extrae datos curiosos como lista de diccionarios {title, content} para el chatbot."""
    import re
    clean_text = text.replace('---', '').strip()
    items = re.split(r'\n\n+(?=#{2,3} |\*\*)', clean_text)
    result = []
    for item in items:
        item = item.strip()
        if not item or len(item) < 20:
            continue
        title = None
        title_match = re.search(r'#{2,3}\s*(.+?)(?:\n|$)', item)
        if title_match:
            title = title_match.group(1)
        else:
            title_match = re.search(r'^\*\*\s*(.+?)\s*\*\*', item)
            if title_match:
                title = title_match.group(1)
        if not title:
            continue
        title = re.sub(r'^[\s\U0001F300-\U0001F9FF]+', '', title).strip()
        if not title:
            continue
        if title_match and title_match.group(0).startswith('#'):
            desc = re.sub(r'#{2,3}\s*.+?(?:\n|$)', '', item, count=1)
        else:
            desc = re.sub(r'^\*\*\s*' + re.escape(title) + r'\s*\*\*', '', item)
        desc = desc.strip()
        desc = re.sub(r'\s+', ' ', desc)
        if not desc:
            continue
        desc = re.sub(r'\*\*(.+?)\*\*', r'\1', desc)
        result.append({'title': title, 'content': desc})
    return result


def _extract_faqs_data(text):
    """Extrae FAQs como lista de diccionarios {q, a} para el chatbot."""
    import re
    clean_faqs = text.replace('---', '').strip()
    qa_pairs = re.findall(r'\*\*❓\s*(.+?)\*\*\s*\n?>?\s*(.+?)(?=\n\n\*\*❓|\Z)', clean_faqs, re.DOTALL)
    if not qa_pairs:
        qa_pairs = re.findall(r'#{2,3}\s*(.+?)(?:\n|$)\s*\n?(.+?)(?=\n#{2,3}|\Z)', clean_faqs, re.DOTALL)
    result = []
    for q, a in qa_pairs:
        q_clean = q.strip()
        a_clean = a.strip().replace('\n', ' ')
        a_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', a_clean)
        result.append({'q': q_clean, 'a': a_clean})
    return result


def generate_sabias_que():
    """Genera pagina indice de Sabias Que y 9 paginas individuales por categoria."""
    if not RESEARCH_DATA:
        return
    
    cat_images = {
        'PLACAS PVC': 'img/1-placas-pvc/Carrara%20Oscuro.jpg',
        'LAMBRIN WPC': 'img/2-lambrin-wpc/21-lambrin-interior/AMANECHER.jpg',
        'REVESTIMIENTO FLEXIBLE': 'img/3-revestimiento-flexible/CONCRETO%20Aparente.jpg',
        'PLAFON PVC LAMINADO WOOD STYLE': 'img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg',
        'PLAFÓN PVC LAMINADO WOOD STYLE': 'img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg',
        'PANELES TRIDIMENSIONALES 3D': 'img/5-paneles-tridimensionales/51-blanco/Austin.jpg',
        'VIGAS PVCWPCPU': 'img/6-vigas-pvc/61-interior/BAHIA%201.jpg',
        'PISOS': 'img/7-pisos/71-laminado/ACONCAGUA.jpg',
        'ZACATE SINTETICO': 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg',
        'ZACATE SINTÉTICO': 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg',
        'CLADDING  PLACAS TIPO PIEDRA': 'img/9-cladding/91-placa-tipo-roca/BLACK.jpg',
    }
    
    # Generar paginas individuales
    for cat_name, data in RESEARCH_DATA.items():
        slug = SABIAS_QUE_SLUGS.get(cat_name, 'otros')
        cat_img = cat_images.get(cat_name, 'LOGO%20ADIS.png')
        
        curiosos_cards = _extract_curiosos_cards(data['curiosos']) if data.get('curiosos') else ''
        faqs_html = _extract_faqs_html(data['faqs']) if data.get('faqs') else ''
        faqs_data = _extract_faqs_data(data['faqs']) if data.get('faqs') else []
        faq_schema_html = faqpage_schema([(f['q'], f['a']) for f in faqs_data]) if faqs_data else ''
        page_url = f"{SITE_URL}sabias-que-{slug}.html"
        
        page_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="LOGO ADIS.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cat_name} — ¿Sabías que? | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Datos curiosos y preguntas frecuentes sobre {cat_name}.">
  <meta property="og:title" content="{cat_name} — ¿Sabías que? | ADIS">
  <meta property="og:description" content="Datos curiosos y preguntas frecuentes sobre {cat_name}.">
  <meta property="og:image" content="{SITE_URL}{cat_img}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{cat_name} — ¿Sabías que? | ADIS">
  <meta name="twitter:description" content="Datos curiosos y preguntas frecuentes sobre {cat_name}.">
  <meta name="twitter:image" content="{SITE_URL}{cat_img}">
  <link rel="canonical" href="{page_url}">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
{ga_script()}
{organization_schema()}
{breadcrumb_schema([('Inicio', SITE_URL), ('¿Sabías que?', f'{SITE_URL}sabias-que.html'), (cat_name, page_url)])}
{faq_schema_html}</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header("sabias-que")}

  <section class="sq-hero">
    <h1>¿Sabías que?</h1>
    <p>Conoce todo sobre <strong>{cat_name}</strong></p>
  </section>

  <div style="max-width:1100px;margin:0 auto;padding:0 1.5rem;">
    <a href="sabias-que.html" style="display:inline-flex;align-items:center;gap:0.4rem;color:var(--gold);text-decoration:none;font-size:0.85rem;margin-bottom:1rem;">← Volver al índice</a>
  </div>

  <div class="sq-content" style="padding-top:0;">
    <div class="sq-cat-hero" style="background-image: url('{cat_img}');">
      <div class="sq-cat-overlay">
        <h2>{cat_name}</h2>
      </div>
    </div>
    <div class="section-header" style="margin:2rem 0 1.5rem;">
      <h2 style="font-size:1.4rem;">Datos Curiosos</h2>
      <div class="divider"></div>
    </div>
    <div class="sq-grid">
{curiosos_cards}    </div>
{('<div class="section-header" style="margin:2.5rem 0 1.5rem;"><h2 style="font-size:1.4rem;">Preguntas Frecuentes</h2><div class="divider"></div></div><div class="sq-faqs">' + faqs_html + '</div>') if faqs_html else ''}
  </div>

{generate_footer()}
<script>
function sqToggle(el) {{
  var card = el.closest('.sq-card');
  var shortEl = card.querySelector('.sq-short');
  var fullEl = card.querySelector('.sq-full');
  if (!shortEl || !fullEl) return;
  if (fullEl.style.display === 'none') {{
    shortEl.style.display = 'none';
    fullEl.style.display = 'inline';
    el.textContent = 'Leer menos';
  }} else {{
    shortEl.style.display = 'inline';
    fullEl.style.display = 'none';
    el.textContent = 'Leer más';
  }}
}}
</script>
</body>
</html>
'''
        with open(BASE_DIR / f'sabias-que-{slug}.html', 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"✅ sabias-que-{slug}.html generado ({cat_name})")
    
    # Generar pagina indice
    index_cards = ''
    for cat_name in RESEARCH_DATA.keys():
        slug = SABIAS_QUE_SLUGS.get(cat_name, 'otros')
        cat_img = cat_images.get(cat_name, 'LOGO%20ADIS.png')
        index_cards += f'''    <a href="sabias-que-{slug}.html" class="sq-index-card">
      <div class="sq-index-img" style="background-image:url('{cat_img}');"></div>
      <div class="sq-index-info">
        <h3>{cat_name}</h3>
        <span>Ver datos curiosos y FAQs →</span>
      </div>
    </a>
'''
    
    index_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="LOGO ADIS.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>¿Sabías que? | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Datos curiosos, FAQs y consejos sobre nuestros productos: PVC, WPC, paneles 3D, pisos, zacate y cladding.">
  <meta property="og:title" content="¿Sabías que? | ADIS">
  <meta property="og:description" content="Descubre datos sorprendentes sobre nuestros materiales de construcción.">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{SITE_URL}sabias-que.html">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="¿Sabías que? | ADIS">
  <meta name="twitter:description" content="Descubre datos sorprendentes sobre nuestros materiales de construcción.">
  <meta name="twitter:image" content="{SITE_URL}LOGO%20ADIS.png">
  <link rel="canonical" href="{SITE_URL}sabias-que.html">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
{ga_script()}
{organization_schema()}
{breadcrumb_schema([('Inicio', SITE_URL), ('¿Sabías que?', f'{SITE_URL}sabias-que.html')])}
</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header("sabias-que")}

  <section class="sq-hero">
    <h1>¿Sabías que?</h1>
    <p>Datos sorprendentes y respuestas a tus dudas sobre nuestros materiales.</p>
  </section>

  <div class="sq-content">
    <div class="sq-index-grid">
{index_cards}    </div>
  </div>

{generate_footer()}
</body>
</html>
'''
    with open(BASE_DIR / 'sabias-que.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    print("✅ sabias-que.html (indice) generado")


def generate_proyectos():
    """Genera página de proyectos con carruseles de antes/después y galería dinámica."""
    media_dir = BASE_DIR / 'media'
    
    img_exts = ('.jpg', '.jpeg', '.png')
    vid_exts = ('.mp4', '.mov', '.webm')
    
    try:
        all_files = sorted([f for f in os.listdir(media_dir) if f.lower().endswith(img_exts + vid_exts)]) if media_dir.exists() else []
    except (OSError, PermissionError):
        all_files = []
    
    images = [f for f in all_files if f.lower().endswith(img_exts)]
    videos = [f for f in all_files if f.lower().endswith(vid_exts)]
    
    # Detectar TODAS las parejas antes/despues
    def stem_no_ext(fname):
        return Path(fname).stem.lower()
    
    # Buscar pares: "antes" + "despues" con mismo sufijo numérico
    ba_pairs = []
    used = set()
    for img in images:
        s = stem_no_ext(img)
        if s.startswith('antes'):
            suffix = s[5:].strip()  # ej: "", "1", "2"
            despues_name = f'despues {suffix}'.strip() if suffix else 'despues'
            # Buscar archivo despues correspondiente
            match = None
            for d in images:
                if stem_no_ext(d) == despues_name:
                    match = d
                    break
            if match:
                ba_pairs.append((img, match))
                used.add(img)
                used.add(match)
    
    # Secciones de antes/después (carrusel por cada par)
    ba_sections = ''
    for i, (antes, despues) in enumerate(ba_pairs, 1):
        label = f'Remodelación {i}' if len(ba_pairs) > 1 else 'Antes y Después'
        ba_sections += f'''  <section class="section-wrap reveal">
    <div class="section-header">
      <h2>{label}</h2>
      <div class="divider"></div>
      <p>Desliza para ver la transformación completa.</p>
    </div>
    <div class="carousel-wrap">
      <div class="carousel" id="carousel-ba-{i}">
        <div class="carousel-slide">
          <img src="media/{antes}" alt="Antes" loading="lazy" onclick="openLightbox('media/{antes}', 'Antes - {label}')">
          <div class="carousel-label" style="background: rgba(197,160,89,0.2);">Antes</div>
        </div>
        <div class="carousel-slide">
          <img src="media/{despues}" alt="Después" loading="lazy" onclick="openLightbox('media/{despues}', 'Después - {label}')">
          <div class="carousel-label" style="background: var(--gold); color: var(--black);">Después</div>
        </div>
      </div>
      <button class="carousel-btn prev" onclick="moveCarousel('carousel-ba-{i}', -1)">&#10094;</button>
      <button class="carousel-btn next" onclick="moveCarousel('carousel-ba-{i}', 1)">&#10095;</button>
    </div>
  </section>
'''
    
    # Fotos sueltas (no usadas en pares) → carrusel general
    # Excluir fotos de producto (hojas sueltas) de la galeria de proyectos
    loose_images = [f for f in images if f not in used and not f.startswith('pvc-real-')]
    gallery_section = ''
    if loose_images:
        slides = ''
        for img in loose_images:
            name = Path(img).stem.replace('-', ' ').replace('_', ' ').title()
            slides += f'''        <div class="carousel-slide">
          <img src="media/{img}" alt="{name}" loading="lazy" onclick="openLightbox('media/{img}', '{name}')">
        </div>
'''
        gallery_section = f'''  <section class="section-wrap-alt reveal">
    <div class="section-header">
      <h2>Galería de Proyectos</h2>
      <div class="divider"></div>
      <p>Trabajos reales con nuestros materiales de alta gama.</p>
    </div>
    <div class="carousel-wrap">
      <div class="carousel" id="carousel-gallery">
{slides}      </div>
      <button class="carousel-btn prev" onclick="moveCarousel('carousel-gallery', -1)">&#10094;</button>
      <button class="carousel-btn next" onclick="moveCarousel('carousel-gallery', 1)">&#10095;</button>
    </div>
  </section>
'''
    
    # Videos
    videos_html = ''
    for vid in videos:
        name = Path(vid).stem.replace('-', ' ').replace('_', ' ').title()
        poster = loose_images[0] if loose_images else (images[0] if images else '')
        poster_attr = f' poster="media/{poster}"' if poster else ''
        videos_html += f'''      <div class="video-card reveal">
        <video class="auto-video" muted loop playsinline{poster_attr}>
          <source src="media/{vid}" type="video/mp4">
        </video>
        <div class="product-info">
          <div class="product-name">{name}</div>
        </div>
      </div>
'''
    
    video_section = ''
    if videos_html:
        video_section = f'''  <section class="section-wrap reveal">
    <div class="section-header">
      <h2>Videos de Remodelaciones</h2>
      <div class="divider"></div>
      <p>Transformaciones capturadas en video.</p>
    </div>
    <div class="video-grid">
{videos_html}    </div>
  </section>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="LOGO ADIS.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Proyectos Reales | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Galería de proyectos reales de ADIS Diseño & Remodelación. Antes y después, remodelaciones de interiores y exteriores.">
  <meta property="og:title" content="Proyectos Reales | ADIS Diseño & Remodelación">
  <meta property="og:description" content="Galería de proyectos reales de ADIS Diseño & Remodelación. Antes y después, remodelaciones de interiores y exteriores.">
  <meta property="og:image" content="media/despues.jpg">
  <meta property="og:url" content="{SITE_URL}proyectos.html">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Proyectos Reales | ADIS Diseño & Remodelación">
  <meta name="twitter:description" content="Galería de proyectos reales de ADIS Diseño & Remodelación. Antes y después, remodelaciones de interiores y exteriores.">
  <meta name="twitter:image" content="{SITE_URL}media/despues.jpg">
  <link rel="canonical" href="{SITE_URL}proyectos.html">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
{ga_script()}
{organization_schema()}
{breadcrumb_schema([('Inicio', SITE_URL), ('Proyectos', f'{SITE_URL}proyectos.html')])}
  <style>
    /* CAROUSEL */
    .carousel-wrap {{ position: relative; max-width: 900px; margin: 0 auto; overflow: hidden; border-radius: 12px; border: 1px solid rgba(197,160,89,0.2); }}
    .carousel {{ display: flex; transition: transform 0.5s ease; }}
    .carousel-slide {{ min-width: 100%; position: relative; }}
    .carousel-slide img {{ width: 100%; height: 500px; object-fit: cover; display: block; cursor: pointer; }}
    .carousel-label {{ position: absolute; bottom: 20px; left: 20px; padding: 0.5rem 1.2rem; border-radius: 25px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; backdrop-filter: blur(8px); }}
    .carousel-btn {{ position: absolute; top: 50%; transform: translateY(-50%); background: rgba(15,15,15,0.7); border: 1px solid var(--gold); color: var(--gold); width: 45px; height: 45px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; transition: all 0.3s; z-index: 2; }}
    .carousel-btn:hover {{ background: var(--gold); color: var(--black); }}
    .carousel-btn.prev {{ left: 15px; }}
    .carousel-btn.next {{ right: 15px; }}
    .video-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: 0 auto; }}
    .video-card video {{ width: 100%; border-radius: 8px; }}
    @media (max-width: 768px) {{ .carousel-slide img {{ height: 280px; }} .carousel-btn {{ width: 36px; height: 36px; font-size: 1rem; }} }}
  </style>
{ga_script()}\n</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header("proyectos")}

  <section class="hero-cat">
    <h1>Proyectos Reales</h1>
    <p>Transformaciones que hablan por sí solas. Conoce nuestro trabajo.</p>
  </section>

{ba_sections}{gallery_section}{video_section}
  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
      <a href="contacto.html" class="btn-outline">Contactar</a>
    </div>
  </section>

  <script>
    // Carrusel
    const carouselState = {{}};
    function moveCarousel(id, dir) {{
      const el = document.getElementById(id);
      if (!el) return;
      const slides = el.children.length;
      if (!carouselState[id]) carouselState[id] = 0;
      carouselState[id] = (carouselState[id] + dir + slides) % slides;
      el.style.transform = 'translateX(-' + (carouselState[id] * 100) + '%)';
    }}
    // Auto-play carruseles
    setInterval(() => {{
      document.querySelectorAll('.carousel').forEach(car => {{
        moveCarousel(car.id, 1);
      }});
    }}, 5000);
    
    // Autoplay videos when visible
    (function() {{
      const videos = document.querySelectorAll('.auto-video');
      const observer = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
          if (entry.isIntersecting) {{
            entry.target.play();
          }} else {{
            entry.target.pause();
          }}
        }});
      }}, {{ threshold: 0.5 }});
      videos.forEach(v => observer.observe(v));
    }})();
  </script>
{generate_footer()}
</body>
</html>
'''
    with open(BASE_DIR / 'proyectos.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("proyectos.html generado (carruseles)")
    with open(BASE_DIR / 'proyectos.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("proyectos.html generado")


def main():
    print("Escaneando CATALOGO FINAL...")
    categories = scan_catalog()
    print(f"Encontradas {len(categories)} categorias")

    print("\nSincronizando imagenes...")
    sync_images(categories)

    print("\nSincronizando media...")
    sync_media()

    # Calcular totales por categoria
    for cat in categories:
        total = len(cat["direct_products"])
        for sub in cat["subcategories"]:
            total += len(sub["products"])
        cat["total_products"] = total

    print("\nGenerando archivos...")
    generate_style()
    generate_sitemap(categories)
    generate_robots()
    generate_index(categories)
    generate_contacto()
    generate_proyectos()
    generate_sabias_que()

    for cat in categories:
        generate_category_page(cat, categories)

    # Generar products.json para el buscador
    products_data = []
    for cat in categories:
        cat_price = PRICE_DATA.get(cat["name"], {})
        for sub in cat["subcategories"]:
            for prod in sub["products"]:
                products_data.append({
                    'name': os.path.splitext(prod)[0],
                    'category': cat["name"],
                    'subcategory': sub["name"],
                    'url': f'{cat["filename"]}#{sub["slug"]}',
                    'thumb': f'img/{cat["slug"]}/{sub["slug"]}/{prod}',
                    'price': cat_price.get('range', 'Consultar'),
                    'price_unit': cat_price.get('unit', 'pieza'),
                    'price_note': cat_price.get('note', '')
                })
        for prod in cat["direct_products"]:
            products_data.append({
                'name': os.path.splitext(prod)[0],
                'category': cat["name"],
                'subcategory': None,
                'url': cat["filename"],
                'thumb': f'img/{cat["slug"]}/{prod}',
                'price': cat_price.get('range', 'Consultar'),
                'price_unit': cat_price.get('unit', 'pieza'),
                'price_note': cat_price.get('note', '')
            })
    # Construir datos de investigación para el chatbot
    research_output = {}
    if RESEARCH_DATA:
        research_cat_slugs = {
            'PLACAS PVC': 'placas_pvc',
            'LAMBRIN WPC': 'lambrin_wpc',
            'REVESTIMIENTO FLEXIBLE': 'revestimiento',
            'PLAFON PVC LAMINADO WOOD STYLE': 'plafon',
            'PLAFÓN PVC LAMINADO WOOD STYLE': 'plafon',
            'PANELES TRIDIMENSIONALES 3D': 'paneles_3d',
            'VIGAS PVCWPCPU': 'vigas',
            'PISOS': 'pisos',
            'ZACATE SINTETICO': 'zacate',
            'ZACATE SINTÉTICO': 'zacate',
            'CLADDING  PLACAS TIPO PIEDRA': 'cladding',
        }
        for cat_name, data in RESEARCH_DATA.items():
            slug = research_cat_slugs.get(cat_name)
            if not slug:
                continue
            curiosos = _extract_curiosos_data(data.get('curiosos', ''))
            faqs = _extract_faqs_data(data.get('faqs', ''))
            if curiosos or faqs:
                research_output[slug] = {
                    'name': cat_name,
                    'slug': slug,
                    'curiosos': curiosos,
                    'faqs': faqs
                }
    
    output_data = {'products': products_data, 'research': research_output}
    with open(BASE_DIR / 'products.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\nproducts.json generado con {len(products_data)} productos y datos de {len(research_output)} categorías de investigación")

    print("\nSitio web generado exitosamente en:", BASE_DIR)
    print(f"   - {len(categories)} categorias")
    total_products = sum(len(c["direct_products"]) + sum(len(s["products"]) for s in c["subcategories"]) for c in categories)
    print(f"   - {total_products} productos totales")


if __name__ == '__main__':
    main()
