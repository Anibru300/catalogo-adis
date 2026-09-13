# -*- coding: utf-8 -*-
"""Infraestructura del generador: config, estado de idioma, datos maestros. Extraido de generar_web.py en M3 (salida byte-identica)."""
import os


import sys


import re


import json


import shutil


import datetime


import unicodedata


from pathlib import Path


from urllib.parse import quote



try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False



# Forzar UTF-8 en stdout para evitar errores de codificación
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')



# ========== CONFIGURACIÓN ==========
# El proyecto se migro de Google Drive al Escritorio (Drive corrompia .git).
# BASE_DIR se deriva de la ubicacion de este script para que funcione en cualquier equipo.
BASE_DIR = Path(__file__).resolve().parents[2]  # sitio/ -> 10_SITIO_PUBLICO/ -> raiz del repo


CORE_DIR = BASE_DIR / '00_CORE'


import sys


sys.path.insert(0, str(CORE_DIR / 'i18n'))


sys.path.insert(0, str(CORE_DIR / 'shared'))


import json as _json


PLATAFORMA = _json.loads((CORE_DIR / 'config' / 'plataforma.json').read_text(encoding='utf-8'))


CATALOG_DIR = Path(PLATAFORMA['catalog_dir'])


OUTPUT_DIR = BASE_DIR / 'public'



# ========== CAPTACION DE LEADS Y RESENAS (Google Apps Script) ==========
# Sigue los pasos de admin/GUIA_CONFIGURACION.md para crear la hoja de Google
# y el Apps Script, despliega el script como app web y pega su URL aqui.
# Mientras esten vacios, el sitio funciona igual (formulario solo abre WhatsApp).
LEADS_URL = PLATAFORMA['url_backend']    # Recibe los envios del formulario de contacto (pestaña Leads)


REVIEWS_URL = PLATAFORMA['url_backend']  # Mismo script; expone las resenas para el sitio



CONTACTO = {
    'whatsapp': '15208392877',
    'whatsapp_msg': 'Hola ADIS, vi el catálogo y me interesa obtener información sobre sus productos.',
    'email': 'adis.remodelacion@gmail.com',
    # Teléfono de contacto en México (showroom Nogales). El WhatsApp principal se mantiene en 15208392877.
    'tel_mx': '+52 631-120-4943',
    'tel_mx_link': '+526311204943',
    'tel_usa': '+1 (520) 839-2877',
    'tel_usa_link': '+15208392877',
    'tel_showroom': '+52 631-120-4943',
    'ubicacion': 'Nogales, Sonora · Rio Rico, AZ',
    'direccion': 'C. Alfonso Acosta 16 Local 3, Col. 5 de Mayo, 84000 Heroica Nogales, Sonora',
    'maps_url': 'https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8',
    'horarios': 'Martes a domingo 10:00-19:00',
    'facebook': 'https://www.facebook.com/p/Adis-Dise%C3%B1o-Remodelaci%C3%B3n-61579849591594/',
    # Reemplaza por el enlace de tu perfil de Google Business Profile cuando lo tengas.
    'google_business_url': ''
}




# ========== TRADUCCIONES MANUALES ES/EN ==========
# Diccionario centralizado para el sistema i18n híbrido.
# Los textos dinámicos (nombres de productos, FAQs) se mantienen en español.
from translations import TRANSLATIONS  # dict en 00_CORE/i18n/translations.py (M1)


from web_utils import *  # helpers puros: minify, json_ld, svg_icon, whatsapp, md, slugify (M1)




# ========== ICONOS SVG (reemplazan emojis del sistema) ==========
# Set de iconos de trazo fino en color dorado (#C5A059) o según uso.
# Se inyectan inline para no depender de fuentes externas ni de emojis.



def t(key, lang=None):
    """Devuelve la traducción de una clave. Fallback a español y luego a la clave.
    Si lang es None, usa el idioma de generación actual (CUR_LANG)."""
    if lang is None:
        lang = CUR_LANG
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get('es', key))




def _prefix_links(html_text):
    """Los links .html dentro de traducciones ya resuelven al idioma correcto
    (mismo directorio en /en/); no requieren prefijo."""
    return html_text




def i18n(key, html=False):
    """Envuelve texto traducible en un span data-i18n para el toggle JS.
    Si html=True, el contenido puede incl etiquetas HTML y se cambia con innerHTML.
    """
    esc_es = t(key, 'es').replace('"', '&quot;')
    esc_en = t(key, 'en').replace('"', '&quot;')
    html_attr = ' data-i18n-html="true"' if html else ''
    return f'<span data-i18n="{key}"{html_attr} data-es="{esc_es}" data-en="{esc_en}">{_prefix_links(t(key))}</span>'




def i18n_fmt(key, html=False, **kwargs):
    """Igual que i18n pero formatea placeholders {var} en ambos idiomas."""
    es = t(key, 'es').format(**kwargs)
    en = t(key, 'en').format(**kwargs)
    esc_es = es.replace('"', '&quot;')
    esc_en = en.replace('"', '&quot;')
    html_attr = ' data-i18n-html="true"' if html else ''
    default = es if CUR_LANG == 'es' else en
    return f'<span data-i18n="{key}"{html_attr} data-es="{esc_es}" data-en="{esc_en}">{_prefix_links(default)}</span>'




# ========== CONFIGURACIÓN DEL SITIO ==========
# URL base del sitio (punycode del dominio adis-diseño.com).
SITE_URL = PLATAFORMA['site_url']



# ========== CONTEXTO DE IDIOMA (BUILD TIME) ==========
# El sitio se genera dos veces: ES en public/ y EN en public/en/.
CUR_LANG = 'es'


CUR_PREFIX = ''  # '../' cuando se genera la versión EN en /en/




def set_lang(lang):
    """Establece el idioma de generación actual ('es' o 'en')."""
    global CUR_LANG, CUR_PREFIX
    CUR_LANG = lang
    CUR_PREFIX = '../' if lang == 'en' else ''




def p(path):
    """Prefija una ruta relativa según el idioma de generación.
    Los assets (img, css, media, pdf, json) viven en raíz -> llevan '../' en /en/.
    Los links a páginas .html NO llevan prefijo: en /en/ apuntan a la versión EN
    (mismo directorio), manteniendo al usuario en su idioma al navegar."""
    if not path or path.startswith(('http', 'mailto:', 'tel:', '#', 'data:')):
        return path
    if CUR_PREFIX and not path.split('#')[0].endswith('.html'):
        return CUR_PREFIX + path
    return path




def hreflang_tags(es_path):
    """Genera los link rel=alternate hreflang para el par ES/EN de una página."""
    es_url = SITE_URL + es_path
    en_url = SITE_URL + 'en/' + es_path
    return (f'  <link rel="alternate" hreflang="es" href="{es_url}">\n'
            f'  <link rel="alternate" hreflang="en" href="{en_url}">\n'
            f'  <link rel="alternate" hreflang="x-default" href="{es_url}">')




def out_dir():
    """Directorio de salida según idioma: public/ (es) o public/en/ (en)."""
    return OUTPUT_DIR if CUR_LANG == 'es' else OUTPUT_DIR / 'en'




def page_url(es_path):
    """URL canonical de la página actual según el idioma de generación."""
    if CUR_LANG == 'en':
        return SITE_URL + 'en/' + es_path
    return SITE_URL + es_path




def html_lang():
    return 'en' if CUR_LANG == 'en' else 'es'




# ========== TRADUCCIONES DE CATÁLOGO (categorías, subcategorías, productos) ==========
try:
    with open(CORE_DIR / 'i18n' / 'traducciones_productos.json', encoding='utf-8') as _f:
        _CAT_TR = json.load(_f)
except Exception:
    _CAT_TR = {}




def cat_display(name):
    """Nombre de categoría según idioma de generación (fallback ES)."""
    if CUR_LANG == 'en':
        return _CAT_TR.get('categories', {}).get(name, name)
    return name




def subcat_display(name):
    """Nombre de subcategoría según idioma de generación (fallback ES)."""
    if CUR_LANG == 'en':
        return _CAT_TR.get('subcategories', {}).get(name, name)
    return name




def product_display(name):
    """Nombre de producto según idioma de generación (fallback ES)."""
    if CUR_LANG == 'en':
        return _CAT_TR.get('names', {}).get(name, name)
    return name




def og_locale():
    """Meta og:locale + alternate según idioma de generación."""
    if CUR_LANG == 'en':
        return '  <meta property="og:locale" content="en_US">\n  <meta property="og:locale:alternate" content="es_MX">'
    return '  <meta property="og:locale" content="es_MX">\n  <meta property="og:locale:alternate" content="en_US">'



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
    'VIGAS PVC': {
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
GA_MEASUREMENT_ID = 'G-6DL4217NSC'



# ========== RESEARCH DATA (from investigacion/) ==========
try:
    with open(CORE_DIR / 'i18n' / 'investigacion_data.json', 'r', encoding='utf-8') as f:
        RESEARCH_DATA = json.load(f)
except Exception:
    RESEARCH_DATA = {}



# Versión en inglés (mismas claves de categoría, campos traducidos)
try:
    with open(CORE_DIR / 'i18n' / 'investigacion_data_en.json', 'r', encoding='utf-8') as f:
        RESEARCH_DATA_EN = json.load(f)
except Exception:
    RESEARCH_DATA_EN = {}




# Nombres EN de las categorías de investigación (claves de RESEARCH_DATA)
RESEARCH_CAT_EN = {
    'PLACAS PVC': 'PVC Panels',
    'LAMBRIN WPC': 'WPC Fluted Wall Panels',
    'REVESTIMIENTO FLEXIBLE': 'Flexible Stone Veneer',
    'PLAFON PVC LAMINADO WOOD STYLE': 'PVC Ceiling Panels',
    'PLAFÓN PVC LAMINADO WOOD STYLE': 'PVC Ceiling Panels',
    'PANELES TRIDIMENSIONALES 3D': '3D Wall Panels',
    'PISOS': 'Flooring',
    'ZACATE SINTETICO': 'Artificial Grass',
    'ZACATE SINTÉTICO': 'Artificial Grass',
    'CLADDING  PLACAS TIPO PIEDRA': 'Stone-look Cladding',
    'VIGAS PVC': 'PVC Beams',
}



# Slugs para paginas de sabias-que (deben coincidir con generate_sabias_que)
SABIAS_QUE_SLUGS = {
    'PLACAS PVC': 'pvc',
    'LAMBRIN WPC': 'wpc',
    'REVESTIMIENTO FLEXIBLE': 'revestimiento',
    'PLAFON PVC LAMINADO WOOD STYLE': 'plafon',
    'PLAFÓN PVC LAMINADO WOOD STYLE': 'plafon',
    'PANELES TRIDIMENSIONALES 3D': '3d',
    'VIGAS PVC': 'vigas',
    'PISOS': 'pisos',
    'ZACATE SINTETICO': 'zacate',
    'ZACATE SINTÉTICO': 'zacate',
    'CLADDING  PLACAS TIPO PIEDRA': 'cladding',
}



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




# Títulos descriptivos para videos de proyectos (visibles en home y proyectos.html)
VIDEO_CAPTIONS = {
    'video-01.mp4': 'Sala de estar con lambrín',
    'video-02.mp4': 'Baño con hojas PVC',
    'video-03.mp4': 'Pared con molduras decorativas',
    'video-04.mp4': 'Hojas PVC con diseño único',
    'video-05.mp4': 'Puerta con lambrín negro',
    'video-06.mp4': 'Sala de entretenimiento',
    'video-07.mp4': 'Salón de uñas remodelado',
    'video-08.mp4': 'Sala con lambrín y arte',
    'video-habitacion.mp4': 'Remodelación de habitación',
    'video-consultorio.mp4': 'Remodelación de consultorio',
}




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


