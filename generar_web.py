# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
from pathlib import Path

# Forzar UTF-8 en stdout para evitar errores de codificación
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ========== CONFIGURACIÓN ==========
BASE_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')

CONTACTO = {
    'whatsapp': '526311928993',
    'whatsapp_msg': 'Hola ADIS, vi el catálogo y me interesa obtener información sobre sus productos.',
    'email': 'adis.remodelacion@gmail.com',
    'tel_mx': '+52 631-192-8993',
    'tel_usa': '+1 (520) 839-2877',
    'tel_showroom': '+52 631-120-4943',
    'ubicacion': 'Nogales, Sonora · Rio Rico, AZ',
    'facebook': 'https://www.facebook.com/p/Adis-Dise%C3%B1o-Remodelaci%C3%B3n-61579849591594/'
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
    """Copia imagenes de CATALOGO FINAL a Pagina/img/ para GitHub Pages."""
    img_dir = BASE_DIR / 'img'
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir(parents=True)
    
    total = 0
    for cat in categories:
        cat_img_dir = img_dir / cat['slug']
        cat_img_dir.mkdir(exist_ok=True)
        
        # Copiar productos directos
        for prod in cat['direct_products']:
            src = cat['path'] / prod
            dst = cat_img_dir / prod
            shutil.copy2(src, dst)
            total += 1
        
        # Copiar productos de subcategorias
        for sub in cat['subcategories']:
            sub_img_dir = cat_img_dir / sub['slug']
            sub_img_dir.mkdir(exist_ok=True)
            for prod in sub['products']:
                src = sub['path'] / prod
                dst = sub_img_dir / prod
                shutil.copy2(src, dst)
                total += 1
            
    
    print(f"Imagenes sincronizadas: {total} en {img_dir}")


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
                if sub['products']:
                    thumb = sub['path'] / sub['products'][0]
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
    return f"mailto:{CONTACTO['email']}?subject={subject}&body={body}"


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
}
.info-card:hover {
  border-color: var(--gold); transform: translateY(-6px);
  box-shadow: 0 15px 40px rgba(0,0,0,0.3);
  background: rgba(42,42,42,0.9);
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

/* MEGA MENU */
.mega-trigger { position: relative; }
.mega-menu {
  position: absolute; top: calc(100% + 10px); left: 50%; transform: translateX(-50%) translateY(10px);
  width: 720px; max-width: 90vw; background: rgba(26,26,26,0.98); backdrop-filter: blur(20px);
  border: 1px solid rgba(197,160,89,0.25); border-radius: 16px; padding: 1.5rem;
  box-shadow: 0 30px 80px rgba(0,0,0,0.8); opacity: 0; visibility: hidden; transition: all 0.3s ease;
  z-index: 1002; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem;
}
.mega-trigger:hover .mega-menu { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
.mega-item {
  display: flex; align-items: center; gap: 0.8rem; padding: 0.7rem; border-radius: 10px;
  text-decoration: none; color: var(--light); transition: all 0.3s; border: 1px solid transparent;
}
.mega-item:hover { background: rgba(197,160,89,0.1); border-color: rgba(197,160,89,0.3); transform: translateY(-2px); }
.mega-item img { width: 45px; height: 45px; object-fit: cover; border-radius: 8px; border: 1px solid rgba(197,160,89,0.2); }
.mega-item span { font-size: 0.8rem; font-weight: 600; letter-spacing: 1px; }

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
  .mega-menu { display: none; }
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
  .chatbot-float { width: 50px; height: 50px; font-size: 1.5rem; }
  .chatbot-window { width: calc(100vw - 40px); left: 20px; }
  .stat-number { font-size: 2rem; }
  .hero-cat-bg { min-height: 45vh; }
  .product-gallery { height: 300px; }
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
'''

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


def generate_style():
    with open(BASE_DIR / 'style.css', 'w', encoding='utf-8') as f:
        f.write(CSS.strip())
    print("✅ style.css generado")


def generate_header(current_page='index'):
    """Genera el header HTML con mega-menu y search mejorado."""
    
    MEGA_ITEMS = [
        ('1-placas-pvc.html', 'img/1-placas-pvc/11-placas-pvc-tipo-madera/Adler.jpg', 'Placas PVC'),
        ('2-lambrin-wpc.html', 'img/2-lambrin-wpc/21-lambrin-interior/AMANECHER.jpg', 'Lambrín WPC'),
        ('3-revestimiento-flexible.html', 'img/3-revestimiento-flexible/CONCRETO Aparente.jpg', 'Revestimiento Flexible'),
        ('4-plafon-pvc.html', 'img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg', 'Plafón PVC'),
        ('5-paneles-tridimensionales.html', 'img/5-paneles-tridimensionales/51-blanco/Austin.jpg', 'Paneles 3D'),
        ('6-vigas-pvc.html', 'img/6-vigas-pvc/61-interior/BAHIA 1.jpg', 'Vigas PVC'),
        ('7-pisos.html', 'img/7-pisos/71-laminado/ACONCAGUA.jpg', 'Pisos'),
        ('8-zacate.html', 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg', 'Zacate'),
        ('9-cladding.html', 'img/9-cladding/91-placa-tipo-roca/BLACK.jpg', 'Cladding'),
    ]
    mega_html = '\n'.join([f'        <a href="{u}" class="mega-item"><img src="{i}" alt="{t}" loading="lazy"><span>{t}</span></a>' for u, i, t in MEGA_ITEMS])
    
    nav_links = '<a href="index.html">Inicio</a>\n        <a href="index.html#categorias" class="mega-trigger">Catálogo\n          <div class="mega-menu">\n' + mega_html + '\n          </div>\n        </a>\n        <a href="proyectos.html">Proyectos</a>\n        <a href="contacto.html">Contacto</a>'
    if current_page != 'index':
        nav_links = '<a href="index.html">← Inicio</a>\n        <a href="index.html#categorias" class="mega-trigger">Catálogo\n          <div class="mega-menu">\n' + mega_html + '\n          </div>\n        </a>\n        <a href="proyectos.html">Proyectos</a>\n        <a href="contacto.html">Contacto</a>'

    return f'''  <header>
    <div class="header-inner">
      <a href="index.html" class="logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></a>
      <nav class="desktop-nav">
        {nav_links}
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Buscar producto..." autocomplete="off" title="Presiona / para buscar">
          <button onclick="openSpotlight()">🔍</button>
          <div class="search-dropdown" id="searchDropdown"></div>
        </div>
      </nav>
      <button class="menu-btn" onclick="toggleMenu()">☰</button>
    </div>
  </header>

  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">✕</button>
    <a href="index.html" onclick="toggleMenu()">Inicio</a>
    <a href="index.html#categorias" onclick="toggleMenu()">Catálogo</a>
    <a href="proyectos.html" onclick="toggleMenu()">Proyectos</a>
    <a href="contacto.html" onclick="toggleMenu()">Contacto</a>
    <div class="search-box" style="margin-top:1rem;">
      <input type="text" id="searchInputMobile" placeholder="Buscar producto..." autocomplete="off" style="width:220px;">
      <button onclick="performSearchMobile()">🔍</button>
      <div class="search-dropdown" id="searchDropdownMobile"></div>
    </div>
  </div>
  
  <!-- SPOTLIGHT OVERLAY -->
  <div class="spotlight-overlay" id="spotlightOverlay" onclick="closeSpotlight(event)">
    <button class="spotlight-close" onclick="closeSpotlight(event)">✕</button>
    <div class="spotlight-box">
      <div class="spotlight-input-wrap">
        <span class="spotlight-icon">🔍</span>
        <input type="text" class="spotlight-input" id="spotlightInput" placeholder="Buscar productos, categorías..." autocomplete="off">
      </div>
      <div class="spotlight-results" id="spotlightResults"></div>
    </div>
  </div>
'''


def generate_footer():
    chatbot_js = '''
  <script>
    // Toggle mobile menu
    function toggleMenu() { document.getElementById('mobileMenu').classList.toggle('active'); }
    
    // Chatbot Inteligente v2
    (function() {
      const chatWindow = document.getElementById('chatbotWindow');
      const chatBody = document.getElementById('chatbotBody');
      let allProducts = [];
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
          whatsapp: '+52 631-192-8993',
          tel_showroom: '+52 631-120-4943',
          email: 'adis.remodelacion@gmail.com',
          ubicacion: 'Nogales, Sonora y Rio Rico, AZ'
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
          wpc: 'Wood Plastic Composite (Compuesto de Madera y Plástico). Es un material hecho de fibras de madera mezcladas con plástico, muy usado en paneles, revestimientos, muebles y decoración porque parece madera pero resiste mejor la humedad y el desgaste.'
        },
        venta: {
          unidad: 'El tipo de unidad y cómo se vende viene en las fichas técnicas de cada categoría: por pieza, por hoja, tamaño de la hoja, etc.'
        }
      };
      
      fetch('products.json')
        .then(r => r.json())
        .then(data => { allProducts = data; })
        .catch(() => { allProducts = []; });
      
      window.toggleChat = function() {
        chatWindow.classList.toggle('active');
        if (chatWindow.classList.contains('active') && chatBody.children.length === 0) {
          showWelcome();
        }
      };
      
      function addMessage(text, isUser) {
        const msg = document.createElement('div');
        msg.className = 'chat-message ' + (isUser ? 'user' : 'bot');
        msg.innerHTML = text;
        chatBody.appendChild(msg);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function removeInputs() {
        const existing = chatBody.querySelector('.chat-input-wrap');
        if (existing) existing.remove();
      }
      
      function showQuickReplies(replies) {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        const opts = document.createElement('div');
        opts.className = 'chat-options';
        opts.innerHTML = replies.map(r => `<button class="chat-option-btn" onclick="chatBotProcess('${r.replace(/'/g, "\'")}')">${r}</button>`).join('');
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
      
      window.chatBotProcess = function(rawText) {
        if (!rawText || !rawText.trim()) return;
        const text = rawText.trim();
        addMessage(text, true);
        removeInputs();
        
        const q = text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
        const response = findResponse(q, text);
        
        setTimeout(() => {
          addMessage(response, false);
          showQuickReplies(['Ver productos', 'Horarios', 'Cotización', 'Ubicación', 'Hablar con asesor']);
          addInputField();
        }, 500);
      };
      
      function findResponse(q, original) {
        // SALUDO
        if (/^(hola|buenas|buenos|hey|hi|hello|que tal|q tal)/.test(q)) {
          return '¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>. Soy tu asistente virtual y puedo ayudarte con:<br><br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Información técnica 📋<br><br>¿Qué necesitas? Escribe tu pregunta o usa los botones de abajo.';
        }
        
        // HORARIOS
        if (q.includes('horario') || q.includes('hora') || q.includes('abierto') || q.includes('atencion') || q.includes('cierran') || q.includes('abren')) {
          let r = '🕐 <strong>Horarios de atención (Showroom):</strong><br><br>';
          r += '• <strong>Lunes:</strong> ' + kb.horarios.lunes + '<br>';
          r += '• <strong>Martes:</strong> ' + kb.horarios.martes + '<br>';
          r += '• <strong>Miércoles:</strong> ' + kb.horarios.miercoles + '<br>';
          r += '• <strong>Jueves:</strong> ' + kb.horarios.jueves + '<br>';
          r += '• <strong>Viernes:</strong> ' + kb.horarios.viernes + '<br>';
          r += '• <strong>Sábado:</strong> ' + kb.horarios.sabado + '<br>';
          r += '• <strong>Domingo:</strong> ' + kb.horarios.domingo + '<br><br>';
          r += '💬 ' + kb.horarios.whatsapp;
          return r;
        }
        if (q.includes('lunes')) return 'Los <strong>lunes</strong> estamos <strong>cerrados</strong> 🚪 en showroom, pero WhatsApp está disponible. Te atendemos de martes a domingo. ¿Te gustaría saber otro horario?';
        if (q.includes('domingo')) return 'Los <strong>domingos</strong> abrimos de <strong>9:00 a 15:00</strong> ☀️. Es un buen día para venir a conocer nuestros productos sin prisa.';
        if (q.includes('sabado')) return 'Los <strong>sábados</strong> atendemos de <strong>9:00 a 19:00</strong> 💪. Es nuestro día con más afluencia, te recomiendo venir temprano.';
        
        // CONTACTO / WHATSAPP / TELEFONO
        if (q.includes('whatsapp') || q.includes('telefono') || q.includes('celular') || q.includes('numero') || q.includes('llamar') || q.includes('contacto') || q.includes('hablar')) {
          return '📱 <strong>Contactos directos:</strong><br><br>• <strong>WhatsApp:</strong> ' + kb.contacto.whatsapp + '<br>• <strong>Showroom:</strong> ' + kb.contacto.tel_showroom + '<br>• <strong>Email:</strong> ' + kb.contacto.email + '<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20tengo%20una%20pregunta" target="_blank" class="chat-whatsapp-btn">💬 Abrir WhatsApp</a>';
        }
        
        // UBICACION
        if (q.includes('ubicacion') || q.includes('donde') || q.includes('direccion') || q.includes('ubicados') || q.includes('local') || q.includes('tienda') || q.includes('showroom') || q.includes('nogales') || q.includes('rio rico')) {
          return '📍 <strong>Nuestra tienda física está en Nogales, Sonora</strong><br><br>📌 Puedes ver la dirección exacta y el mapa en nuestra página de <a href="contacto.html" style="color:#C5A059">Contacto</a> o en <a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" style="color:#C5A059">Google Maps →</a><br><br>🏠 ¡Tenemos showroom! Ven a ver y tocar los materiales antes de comprar. También atendemos en <strong>Rio Rico, AZ</strong>.';
        }
        
        // PRECIOS / COTIZACION
        if (q.includes('precio') || q.includes('cuesta') || q.includes('cuanto') || q.includes('valor') || q.includes('cotizacion') || q.includes('cotizar') || q.includes('presupuesto')) {
          let r = '💰 <strong>Precios y cotizaciones:</strong><br><br>';
          r += '• ' + kb.precios.iva + '<br>';
          r += '• ' + kb.precios.mayorista + '<br>';
          r += '• Los precios son <strong>solo por el material</strong> (por pieza, caja o metro cuadrado según categoría)<br><br>';
          r += '📋 <strong>Cotización detallada:</strong> ' + kb.cotizacion.tiempo + '<br>';
          r += '📦 <strong>Incluye:</strong> ' + kb.cotizacion.incluye + '<br>';
          r += '⏱️ <strong>Sin stock:</strong> ' + kb.cotizacion.sin_stock + '<br><br>';
          r += '🔨 ¿Requieres instalación? Un representante visita tu obra para cotizarla aparte.<br><br>';
          r += '<a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20una%20cotización" target="_blank" class="chat-whatsapp-btn">📱 Solicitar cotización gratis</a>';
          return r;
        }
        
        // ENVIO / ENTREGA
        if (q.includes('envio') || q.includes('entrega') || q.includes('mandan') || q.includes('envian') || q.includes('domicilio') || q.includes('llevan')) {
          let r = '🚚 <strong>Envíos y entregas:</strong><br><br>';
          r += '🎁 <strong>Entrega GRATIS</strong> en: ' + kb.envios.gratis + '<br><br>';
          r += '📦 ' + kb.envios.nacional + '<br><br>';
          r += '⏱️ ' + kb.envios.tiempo_grandes + '<br><br>';
          r += 'Envíanos tu dirección por WhatsApp para cotizar el envío exacto.<br><br>';
          r += '<a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20cotizar%20un%20envío" target="_blank" class="chat-whatsapp-btn">📱 Cotizar envío</a>';
          return r;
        }
        
        // INSTALACION
        if (q.includes('instalacion') || q.includes('instalan') || q.includes('colocan') || q.includes('ponen') || q.includes('colocacion')) {
          let r = '🛠️ <strong>Servicio de instalación:</strong><br><br>';
          r += kb.instalacion.costo + '<br><br>';
          r += '👷 ' + kb.instalacion.proceso + '<br><br>';
          r += '✅ También vendemos materiales sueltos si prefieres instalar por tu cuenta.<br><br>';
          r += '<a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20cotizar%20instalación" target="_blank" class="chat-whatsapp-btn">📱 Cotizar instalación</a>';
          return r;
        }
        
        // PAGO / FORMAS DE PAGO
        if (q.includes('pago') || q.includes('pagos') || q.includes('tarjeta') || q.includes('credito') || q.includes('efectivo') || q.includes('transferencia') || q.includes('meses') || q.includes('debito')) {
          let r = '💳 <strong>Formas de pago:</strong><br><br>';
          kb.pagos.metodos.forEach(m => { r += '• ' + m + '<br>'; });
          r += '<br>⚠️ <strong>' + kb.pagos.anticipo + '</strong><br><br>';
          r += 'Escríbenos para más detalles.<br><br>';
          r += '<a href="https://wa.me/526311928993?text=Hola%20ADIS,%20pregunto%20por%20formas%20de%20pago" target="_blank" class="chat-whatsapp-btn">📱 Preguntar por pagos</a>';
          return r;
        }
        
        // GARANTIA
        if (q.includes('garantia') || q.includes('garantiza')) {
          let r = '✅ <strong>Garantía:</strong><br><br>';
          r += '🛡️ ' + kb.garantia.validacion + '<br><br>';
          r += '• Placas PVC: ' + kb.garantia.pvc + '<br>';
          r += '• Lambrín WPC: ' + kb.garantia.wpc + '<br>';
          r += '• Pisos SPC: ' + kb.garantia.spc + '<br>';
          r += '• Zacate sintético: ' + kb.garantia.zacate + '<br><br>';
          r += 'La garantía cubre defectos de fábrica. Conserva tu ticket de compra.';
          return r;
        }
        
        // PRODUCTOS / CATALOGO / MATERIALES / PROYECTOS
        if (q.includes('producto') || q.includes('catalogo') || q.includes('materiales') || q.includes('que venden') || q.includes('tienen') || q.includes('ofrecen')) {
          return '📦 <strong>Nuestros productos:</strong><br><br>• Placas PVC (tipo madera, texturizadas, espejo, mármol)<br>• Lambrín WPC (interior y exterior)<br>• Paneles 3D decorativos<br>• Pisos (Laminado, WPC, SPC, Deck)<br>• Plafón PVC<br>• Vigas PVC<br>• Zacate sintético y follaje<br>• Cladding y revestimientos<br><br>🏠 Atendemos: ' + kb.proyectos.tipos + '<br><br>👉 <a href="index.html#categorias" style="color:#C5A059">Ver catálogo completo</a>';
        }
        
        // PVC TIPO MARMOL
        if (q.includes('marmol') || q.includes('marble') || (q.includes('pvc') && q.includes('marmol'))) {
          return '🏛️ <strong>Hoja de PVC tipo Mármol</strong><br><br>Es una solución decorativa perfecta para cualquier espacio interior. Añade un toque de elegancia a tu hogar, oficina o espacio comercial.<br><br>✨ <strong>Características:</strong><br>• Fabricada con materiales de alta calidad<br>• Duradera y ligera, fácil de instalar y mantener<br>• Resistente al agua, manchas y arañazos<br>• Inversión que dura muchos años<br><br>🏠 <strong>Aplicaciones:</strong> Cocinas, baños, salas de estar y más<br><br>👉 <a href="1-placas-pvc.html" style="color:#C5A059">Ver en catálogo →</a>';
        }
        
        // DIFERENCIAS ENTRE MATERIALES
        if ((q.includes('wpc') && q.includes('pvc')) || q.includes('diferencia wpc') || q.includes('wpc o pvc')) {
          return '🆚 <strong>WPC vs PVC:</strong><br><br><strong>WPC (Wood Plastic Composite):</strong><br>• Mezcla de madera y plástico<br>• Aspecto más natural tipo madera real<br>• Ideal para exteriores (resistente a UV y lluvia)<br>• Más pesado y robusto<br><br><strong>PVC:</strong><br>• Plástico 100%<br>• Más ligero y fácil de instalar<br>• Ideal para interiores<br>• Mayor variedad de diseños (madera, espejo, textura)<br><br>¿Te ayudo a elegir según tu proyecto? 💬';
        }
        if (q.includes('spc') && (q.includes('wpc') || q.includes('diferencia') || q.includes('pvc'))) {
          return '🆚 <strong>SPC vs WPC vs Laminado:</strong><br><br><strong>SPC (Stone Plastic Composite):</strong><br>• Muy resistente al agua 💧<br>• Ideal para cocinas y baños<br>• Instalación rápida tipo click<br><br><strong>WPC:</strong><br>• Más cálido y confortable al caminar<br>• Buen aislamiento térmico y acústico<br>• Ideal para recámaras y salas<br><br><strong>Laminado:</strong><br>• Más económico<br>• Recomendado para áreas de bajo tráfico<br><br>¿Para qué espacio es? Te recomiendo el mejor.';
        }
        
        // BUSQUEDA DE PRODUCTOS POR NOMBRE
        if (allProducts.length > 0) {
          const terms = q.split(/\s+/).filter(t => t.length > 2);
          const matches = allProducts.filter(p => {
            const text = (p.name + ' ' + p.category + ' ' + (p.subcategory || '')).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
            return terms.some(t => text.includes(t));
          }).slice(0, 3);
          
          if (matches.length > 0) {
            let r = '🔎 <strong>Encontré estos productos:</strong><br><br>';
            matches.forEach(m => {
              r += `<div style="display:flex;gap:0.6rem;align-items:center;margin-bottom:0.6rem;padding:0.5rem;background:rgba(197,160,89,0.08);border-radius:8px;"><img src="${m.thumb}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;border:1px solid rgba(197,160,89,0.2);"><div><a href="${m.url}" style="color:#C5A059;font-weight:600;font-size:0.85rem;">${m.name}</a><div style="font-size:0.72rem;color:rgba(245,245,245,0.5);">${m.category}${m.subcategory ? ' / ' + m.subcategory : ''}</div></div></div>`;
            });
            r += '<br>¿Quieres que te ayude con algo específico de estos productos?';
            return r;
          }
        }
        
        // AGRADECIMIENTO / DESPEDIDA
        if (q.includes('gracias') || q.includes('thank') || q.includes('perfecto') || q.includes('excelente')) {
          return '¡Con mucho gusto! 😊🙌 Estoy aquí para lo que necesites. Si tienes más dudas, escríbenos por WhatsApp al <strong>' + kb.contacto.whatsapp + '</strong> o visítanos en el showroom. ¡Que tengas un excelente día!';
        }
        if (q.includes('adios') || q.includes('bye') || q.includes('hasta luego') || q.includes('nos vemos')) {
          return '¡Hasta luego! 👋 Gracias por contactar a ADIS Diseño & Remodelación. Recuerda que puedes volver cuando quieras o escribirnos al WhatsApp. ¡Éxito con tu proyecto! 🏠✨';
        }
        
        // TIPO DE PROYECTO / A QUIEN ATIENDEN
        if (q.includes('casa') || q.includes('oficina') || q.includes('negocio') || q.includes('local') || q.includes('proyecto')) {
          return '🏠 <strong>Atendemos todo tipo de proyectos:</strong><br><br>' + kb.proyectos.tipos + '<br><br>Desde una pared de acento en casa hasta remodelaciones completas de locales comerciales. ¿Cuéntanos sobre tu proyecto? 💬<br><br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20tengo%20un%20proyecto%20de" target="_blank" class="chat-whatsapp-btn">📱 Contar mi proyecto</a>';
        }
        
        // DEFINICIONES PVC / WPC
        if (q.includes('que es pvc') || q.includes('significa pvc') || q.includes('pvc significa') || q.includes('definicion pvc')) {
          return '📘 <strong>¿Qué es PVC?</strong><br><br>' + kb.definiciones.pvc + '<br><br>En ADIS lo usamos para placas decorativas, plafones y vigas con acabados que imitan madera, espejo y texturas.';
        }
        if (q.includes('que es wpc') || q.includes('significa wpc') || q.includes('wpc significa') || q.includes('definicion wpc')) {
          return '📗 <strong>¿Qué es WPC?</strong><br><br>' + kb.definiciones.wpc + '<br><br>En ADIS lo usamos para lambrín de interior y exterior, pisos y revestimientos que lucen como madera real pero duran más.';
        }
        
        // UNIDAD DE VENTA / FICHAS TECNICAS
        if (q.includes('unidad') || q.includes('como se vende') || q.includes('ficha tecnica') || q.includes('hoja tecnica') || q.includes('pieza') || q.includes('hoja') || q.includes('tamano') || q.includes('medida')) {
          return '📐 <strong>Unidad de venta y especificaciones:</strong><br><br>' + kb.venta.unidad + '<br><br>👉 Revisa las fichas técnicas en cada categoría del catálogo para ver: medidas, contenido por caja, peso, espesor y recomendaciones de instalación.<br><br><a href="index.html#categorias" style="color:#C5A059">Ir al catálogo →</a>';
        }
        
        // DEFAULT
        return 'Disculpa, no entendí muy bien. 😅 Puedo ayudarte con:<br><br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Formas de pago 💳<br>• Instalación 🛠️<br><br>Escribe tu pregunta o usa los botones de abajo.';
      }
      
      function showWelcome() {
        addMessage('¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>.<br><br>Soy tu asistente virtual y puedo ayudarte con información sobre nuestros productos, horarios, precios, cotizaciones y más.<br><br>¿Qué necesitas? Escribe tu pregunta 👇', false);
        showQuickReplies(['Ver productos', 'Horarios', 'Cotización', 'Ubicación', '¿Tienen envío?']);
        addInputField();
      }
    })();
    
    // Scroll reveal animations
    (function() {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('active');
          }
        });
      }, { threshold: 0.1 });
      
      document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    })();
    
    // Animate stats on scroll
    (function() {
      const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            entry.target.classList.add('counted');
            const target = parseInt(entry.target.dataset.target);
            const duration = 2000;
            const start = performance.now();
            
            function update(currentTime) {
              const elapsed = currentTime - start;
              const progress = Math.min(elapsed / duration, 1);
              const ease = 1 - Math.pow(1 - progress, 3);
              entry.target.textContent = Math.floor(ease * target);
              if (progress < 1) requestAnimationFrame(update);
            }
            requestAnimationFrame(update);
          }
        });
      }, { threshold: 0.5 });
      
      document.querySelectorAll('.stat-number').forEach(el => statsObserver.observe(el));
    })();
  </script>
  <script>''' + PARTICLES_JS + '''</script>

  <!-- Lightbox Modal -->
  <div class="lightbox" id="lightbox" onclick="closeLightbox(event)">
    <button class="lightbox-close" onclick="closeLightbox(event)">✕</button>
    <img id="lightboxImg" src="" alt="">
    <div class="lightbox-caption" id="lightboxCaption"></div>
  </div>

  <script>
    // Lightbox
    function openLightbox(src, caption) {
      const lb = document.getElementById('lightbox');
      const img = document.getElementById('lightboxImg');
      const cap = document.getElementById('lightboxCaption');
      img.src = src;
      cap.textContent = caption || '';
      lb.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
    function closeLightbox(e) {
      if (e && e.target !== e.currentTarget && !e.target.classList.contains('lightbox-close')) return;
      document.getElementById('lightbox').classList.remove('active');
      document.body.style.overflow = '';
    }
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closeLightbox();
    });

    // Spotlight overlay
    window.openSpotlight = function() {
      document.getElementById('spotlightOverlay').classList.add('active');
      const inp = document.getElementById('spotlightInput');
      if (inp) { setTimeout(() => inp.focus(), 100); }
      if (typeof spotlightSearch === 'function') spotlightSearch(inp ? inp.value : '');
    };
    window.closeSpotlight = function(e) {
      if (e && e.target !== e.currentTarget && !e.target.classList.contains('spotlight-close')) return;
      document.getElementById('spotlightOverlay').classList.remove('active');
    };
    
    // Buscador global mejorado
    (function() {
      let allProducts = [];
      let debounceTimer = null;
      let activeIndex = -1;
      let currentResults = [];
      let spotlightResults = [];
      let spotlightIndex = -1;
      
      fetch('products.json')
        .then(r => r.json())
        .then(data => { allProducts = data; })
        .catch(() => { allProducts = []; });
      
      // Spotlight search
      window.spotlightSearch = function(query) {
        const container = document.getElementById('spotlightResults');
        if (!query || query.length < 2) {
          if (container) container.innerHTML = '<div style="padding:2rem;text-align:center;color:rgba(245,245,245,0.5);">Escribe al menos 2 caracteres para buscar...</div>';
          return;
        }
        const q = normalize(query);
        const terms = q.split(/\s+/).filter(t => t.length > 0);
        const scored = allProducts.map(p => {
          const name = normalize(p.name);
          const cat = normalize(p.category);
          const sub = normalize(p.subcategory || '');
          let score = 0;
          for (const t of terms) {
            if (name.startsWith(t)) score += 10;
            else if (name.includes(t)) score += 5;
            if (sub.startsWith(t)) score += 3;
            else if (sub.includes(t)) score += 2;
            if (cat.includes(t)) score += 1;
          }
          return { p, score };
        }).filter(x => x.score > 0).sort((a,b) => b.score - a.score).slice(0, 10);
        
        spotlightResults = scored.map(x => x.p);
        spotlightIndex = -1;
        
        if (!container) return;
        if (scored.length === 0) {
          container.innerHTML = '<div style="padding:2rem;text-align:center;color:rgba(245,245,245,0.5);">No se encontraron productos</div>';
        } else {
          container.innerHTML = scored.map((x, i) => `
            <a href="${x.p.url}" class="spotlight-item" data-sindex="${i}" onclick="closeSpotlight()">
              <img src="${x.p.thumb}" alt="${x.p.name}" loading="lazy">
              <div class="spotlight-item-info">
                <span class="spotlight-item-name">${highlight(x.p.name, query)}</span>
                <span class="spotlight-item-cat">${x.p.category}${x.p.subcategory ? ' / ' + x.p.subcategory : ''}</span>
              </div>
            </a>
          `).join('');
        }
      };
      
      const spotInput = document.getElementById('spotlightInput');
      if (spotInput) {
        spotInput.addEventListener('input', e => {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(() => spotlightSearch(e.target.value), 150);
        });
        spotInput.addEventListener('keydown', e => {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            spotlightIndex = Math.min(spotlightIndex + 1, spotlightResults.length - 1);
            updateSpotlightActive();
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            spotlightIndex = Math.max(spotlightIndex - 1, -1);
            updateSpotlightActive();
          } else if (e.key === 'Enter') {
            e.preventDefault();
            if (spotlightIndex >= 0 && spotlightResults[spotlightIndex]) {
              window.location.href = spotlightResults[spotlightIndex].url;
              closeSpotlight();
            }
          } else if (e.key === 'Escape') {
            closeSpotlight();
          }
        });
      }
      
      function updateSpotlightActive() {
        document.querySelectorAll('.spotlight-item').forEach((el, i) => {
          el.style.background = i === spotlightIndex ? 'rgba(197,160,89,0.15)' : '';
        });
        const active = document.querySelector('.spotlight-item[data-sindex="' + spotlightIndex + '"]');
        if (active) active.scrollIntoView({ block: 'nearest' });
      }
      
      function normalize(str) {
        return (str || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      }
      
      function highlight(text, query) {
        const nq = normalize(query);
        const nt = normalize(text);
        let out = '';
        let last = 0;
        let idx = nt.indexOf(nq);
        while (idx >= 0 && nq.length > 0) {
          out += text.slice(last, idx);
          const end = idx + nq.length;
          out += '<mark>' + text.slice(idx, end) + '</mark>';
          last = end;
          idx = nt.indexOf(nq, last);
        }
        out += text.slice(last);
        return out;
      }
      
      function doSearch(query, dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!query || query.length < 2) {
          dropdown.classList.remove('active');
          currentResults = [];
          activeIndex = -1;
          return;
        }
        const q = normalize(query);
        const terms = q.split(/\s+/).filter(t => t.length > 0);
        
        const scored = allProducts.map(p => {
          const name = normalize(p.name);
          const cat = normalize(p.category);
          const sub = normalize(p.subcategory || '');
          let score = 0;
          for (const t of terms) {
            if (name.startsWith(t)) score += 10;
            else if (name.includes(t)) score += 5;
            if (sub.startsWith(t)) score += 3;
            else if (sub.includes(t)) score += 2;
            if (cat.includes(t)) score += 1;
          }
          return { p, score };
        }).filter(x => x.score > 0).sort((a,b) => b.score - a.score).slice(0, 8);
        
        currentResults = scored.map(x => x.p);
        activeIndex = -1;
        
        if (scored.length === 0) {
          dropdown.innerHTML = '<div class="search-empty">No se encontraron productos</div>';
        } else {
          dropdown.innerHTML = '<div class="search-dropdown-header">' + scored.length + ' resultado' + (scored.length > 1 ? 's' : '') + ' encontrado' + (scored.length > 1 ? 's' : '') + '</div>' +
            scored.map((x, i) => `
              <a href="${x.p.url}" class="search-item" data-index="${i}" onclick="clearSearch()">
                <img src="${x.p.thumb}" alt="${x.p.name}" loading="lazy">
                <div class="search-item-info">
                  <span class="search-item-name">${highlight(x.p.name, query)}</span>
                  <span class="search-item-cat">${x.p.category}${x.p.subcategory ? ' / ' + x.p.subcategory : ''}</span>
                </div>
              </a>
            `).join('');
        }
        dropdown.classList.add('active');
      }
      
      window.clearSearch = function() {
        const dd = document.getElementById('searchDropdown');
        const dm = document.getElementById('searchDropdownMobile');
        if (dd) dd.classList.remove('active');
        if (dm) dm.classList.remove('active');
      };
      
      function setupInput(inputId, dropdownId) {
        const input = document.getElementById(inputId);
        if (!input) return;
        input.addEventListener('input', e => {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(() => doSearch(e.target.value, dropdownId), 150);
        });
        input.addEventListener('focus', e => doSearch(e.target.value, dropdownId));
        input.addEventListener('keydown', e => {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, currentResults.length - 1);
            updateActive(dropdownId);
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, -1);
            updateActive(dropdownId);
          } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0 && currentResults[activeIndex]) {
              window.location.href = currentResults[activeIndex].url;
              clearSearch();
            }
          } else if (e.key === 'Escape') {
            clearSearch();
            input.blur();
          }
        });
      }
      
      function updateActive(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        dropdown.querySelectorAll('.search-item').forEach((el, i) => {
          el.classList.toggle('active', i === activeIndex);
        });
        const active = dropdown.querySelector('.search-item.active');
        if (active) active.scrollIntoView({ block: 'nearest' });
      }
      
      setupInput('searchInput', 'searchDropdown');
      setupInput('searchInputMobile', 'searchDropdownMobile');
      
      // Shortcut "/" para enfocar buscador
      document.addEventListener('keydown', e => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
          e.preventDefault();
          const inp = document.getElementById('searchInput');
          if (inp) { inp.focus(); }
        }
      });
      
      document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box')) clearSearch();
      });
    })();
  </script>
'''
    return f'''  <footer>
    <div class="footer-logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></div>
    <div class="footer-info">
      <strong>ADI'S DISEÑO & REMODELACIÓN</strong><br>
      Creando espacios, reinventando hogares.<br>
      {CONTACTO['ubicacion']}<br>
      Tel. MX: {CONTACTO['tel_mx']} · Tel. USA: {CONTACTO['tel_usa']}<br>
      {CONTACTO['email']}
    </div>
    <div class="footer-social">
      <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO['whatsapp_msg'].replace(' ', '%20')}" target="_blank" title="WhatsApp">💬</a>
      <a href="{CONTACTO['facebook']}" target="_blank" title="Facebook">📘</a>
    </div>
    <div class="copyright">© 2026 ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.</div>
  </footer>

  <!-- MOBILE BOTTOM NAV -->
  <nav class="mobile-bottom-nav">
    <a href="index.html"><span>🏠</span><span>Inicio</span></a>
    <a href="index.html#categorias"><span>📂</span><span>Catálogo</span></a>
    <a href="proyectos.html"><span>🖼️</span><span>Proyectos</span></a>
    <a href="contacto.html"><span>📞</span><span>Contacto</span></a>
  </nav>

  <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO['whatsapp_msg'].replace(' ', '%20')}" class="whatsapp-float" target="_blank" title="Contáctanos por WhatsApp">💬</a>

  <button class="chatbot-float" onclick="toggleChat()" title="Asistente Virtual">🤖</button>
  <div class="chatbot-window" id="chatbotWindow">
    <div class="chatbot-header">
      <h4>🤖 Asistente ADIS</h4>
      <button class="chatbot-close" onclick="toggleChat()">✕</button>
    </div>
    <div class="chatbot-body" id="chatbotBody"></div>
  </div>

{chatbot_js}'''


def generate_index(categories):
    meta_desc = "Catálogo oficial de ADIS Diseño & Remodelación. Recubrimientos de alta gama: Placas PVC, Lambrín WPC, Plafón, Paneles 3D, Vigas, Pisos, Zacate y Cladding. Nogales, Sonora."
    meta_keywords = "ADIS, diseño, remodelación, paneles, WPC, PVC, recubrimientos, Nogales, Sonora, pisos, zacate, cladding"

    STAR_CATEGORIES = {'Lambrin WPC', 'Placas PVC'}
    
    # Tarjetas estrella (sección destacada)
    featured_cards = ''
    cat_cards = ''
    
    for cat in categories:
        total_prods = len(cat['direct_products'])
        for sub in cat['subcategories']:
            total_prods += len(sub['products'])

        thumb_src = ''
        if cat['subcategories'] and cat['subcategories'][0]['products']:
            thumb_src = f"img/{cat['slug']}/{cat['subcategories'][0]['slug']}/{cat['subcategories'][0]['products'][0]}"
        elif cat['direct_products']:
            thumb_src = f"img/{cat['slug']}/{cat['direct_products'][0]}"
        
        is_star = cat['name'] in STAR_CATEGORIES
        
        if is_star:
            desc = ''
            if cat['name'] == 'Lambrin WPC':
                desc = 'Wood Plastic Composite de alta gama. Resistente a la humedad, rayos UV y perfecto para interiores y exteriores. Nuestro producto más solicitado.'
            elif cat['name'] == 'Placas PVC':
                desc = 'Paneles rígidos tipo madera, texturizados y espejo. Acabado profesional con instalación rápida y garantía extendida.'
            
            featured_cards += f'''      <a href="{cat['filename']}" class="featured-card reveal">
        <img src="{thumb_src}" alt="{cat['name']}" loading="lazy">
        <div class="featured-card-overlay">
          <div class="star-label">⭐ Producto Estrella</div>
          <h3>{cat['name']}</h3>
          <p>{desc}</p>
        </div>
      </a>
'''
        
        star_badge = '<div class="star-badge">⭐ Estrella</div>' if is_star else ''
        featured_class = ' featured' if is_star else ''
        
        cat_cards += f'''      <a href="{cat['filename']}" class="cat-card reveal{featured_class}">
        {star_badge}<img src="{thumb_src}" alt="{cat['name']}" loading="lazy">
        <div class="cat-card-overlay">
          <div class="cat-arrow">→</div>
          <h3>{cat['name']}</h3>
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

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADIS | Diseño & Remodelación</title>
  <meta name="description" content="{meta_desc}">
  <meta name="keywords" content="{meta_keywords}">
  <meta property="og:title" content="ADIS | Diseño & Remodelación">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:image" content="https://anibru300.github.io/catalogo-adis/LOGO%20ADIS.png">
  <meta property="og:url" content="https://anibru300.github.io/catalogo-adis/">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="bg-canvas"></canvas>

{generate_header('index')}

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
        <span class="search-hero-icon">🔍</span>
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
      <h2>⭐ Productos Estrella</h2>
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
        <img src="img/1-placas-pvc/12-placas-pvc-texturizadas/Carrara Oscuro.jpg" alt="Hoja de PVC tipo Mármol Carrara Oscuro" loading="lazy">
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

{generate_testimonios()}
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contacto | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Contacta a ADIS Diseño & Remodelación. WhatsApp, teléfono MX, teléfono USA y correo electrónico.">
  <meta property="og:title" content="Contacto | ADIS Diseño & Remodelación">
  <meta property="og:description" content="Contacta a ADIS Diseño & Remodelación. WhatsApp, teléfono MX, teléfono USA y correo electrónico.">
  <meta property="og:image" content="https://anibru300.github.io/catalogo-adis/LOGO%20ADIS.png">
  <meta property="og:url" content="https://anibru300.github.io/catalogo-adis/contacto.html">
  <meta property="og:type" content="website">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header('contacto')}

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
        <a href="https://wa.me/{CONTACTO['whatsapp']}" target="_blank">{CONTACTO['tel_mx']}</a>
      </div>
      <div class="contact-card">
        <div class="icon">📞</div>
        <h3>Teléfono USA</h3>
        <a href="tel:+15208392877">{CONTACTO['tel_usa']}</a>
      </div>
      <div class="contact-card">
        <div class="icon">✉️</div>
        <h3>Correo</h3>
        <a href="mailto:{CONTACTO['email']}">{CONTACTO['email']}</a>
      </div>
      <div class="contact-card">
        <div class="icon">📍</div>
        <h3>Ubicación</h3>
        <p>{CONTACTO['ubicacion']}</p>
      </div>
      <div class="contact-card">
        <div class="icon">📘</div>
        <h3>Facebook</h3>
        <a href="{CONTACTO['facebook']}" target="_blank">Visitar página</a>
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
    cat_index = [i for i, c in enumerate(categories) if c['slug'] == cat['slug']][0]
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
    <a href="index.html">Inicio</a> <span>/</span> <a href="index.html#categorias">Catálogo</a> <span>/</span> <span style="color:var(--gold);">{cat['name']}</span>
  </div>
'''

    # Seleccionar imagen de fondo representativa para el hero
    hero_bg = ''
    if cat['subcategories'] and cat['subcategories'][0]['products']:
        hero_bg = f"img/{cat['slug']}/{cat['subcategories'][0]['slug']}/{cat['subcategories'][0]['products'][0]}"
    elif cat['direct_products']:
        hero_bg = f"img/{cat['slug']}/{cat['direct_products'][0]}"

    # Reordenar subcategorías: Placas PVC debe tener tipo espejo primero
    subs = list(cat['subcategories'])
    if cat['name'] == 'Placas PVC':
        subs.sort(key=lambda s: 0 if 'espejo' in s['name'].lower() else 1)

    # Índice de subcategorías
    subcat_nav_links = ''
    for sub in subs:
        if sub['products']:
            sub_slug = sub['slug']
            sub_name = sub['name']
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
    if cat['name'] == 'Placas PVC' and cat['direct_products']:
        direct_products_html = ''
        for prod_file in cat['direct_products']:
            if is_dup(prod_file):
                continue
            prod_name = os.path.splitext(prod_file)[0]
            mailto = mailto_link(prod_name, cat['name'])
            direct_products_html += f'''      <div class="product-card reveal">
        <div class="product-gallery" onclick="openLightbox('img/{cat['slug']}/{prod_file}', '{prod_name}')">
          <img src="img/{cat['slug']}/{prod_file}" alt="{prod_name}" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">{prod_name}</div>
          <div class="product-actions">
            <a href="{mailto}" class="btn-cotizar">Solicitar Cotización</a>
            <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20me%20interesa%20cotizar%20el%20producto%20{prod_name.replace(' ', '%20')}%20de%20la%20categoría%20{cat['name'].replace(' ', '%20')}" class="btn-whatsapp" target="_blank">WhatsApp</a>
          </div>
        </div>
      </div>
'''
        
        cat_specs = generate_specs_table('Placas PVC Tipo espejo')
        sections_html += f'''  <section class="subcat-section reveal">
    <div class="subcat-header">
      <h3>⭐ Más Vendidos — Placas PVC Tipo Espejo</h3>
      <span class="subcat-count">{len(cat['direct_products'])} productos</span>
      <div class="subcat-divider"></div>
    </div>
{cat_specs}    <div class="products-grid">
{direct_products_html}    </div>
  </section>
'''

    # Construir secciones de subcategorías
    for sub in subs:
        if not sub['products']:
            continue

        specs_html = generate_specs_table(sub['name'])

        products_html = ''
        for prod_file in sub['products']:
            if is_dup(prod_file):
                continue
            prod_name = os.path.splitext(prod_file)[0]
            mailto = mailto_link(prod_name, cat['name'], sub['name'])
            products_html += f'''      <div class="product-card reveal">
        <div class="product-gallery" onclick="openLightbox('img/{cat['slug']}/{sub['slug']}/{prod_file}', '{prod_name}')">
          <img src="img/{cat['slug']}/{sub['slug']}/{prod_file}" alt="{prod_name}" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">{prod_name}</div>
          <div class="product-actions">
            <a href="{mailto}" class="btn-cotizar">Solicitar Cotización</a>
            <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20me%20interesa%20cotizar%20el%20producto%20{prod_name.replace(' ', '%20')}%20de%20la%20categoría%20{cat['name'].replace(' ', '%20')}%20/%20subcategoría%20{sub['name'].replace(' ', '%20')}" class="btn-whatsapp" target="_blank">WhatsApp</a>
          </div>
        </div>
      </div>
'''

        sections_html += f'''  <section class="subcat-section reveal" id="{sub['slug']}">
    <div class="subcat-header">
      <h3>{sub['name']}</h3>
      <span class="subcat-count">{len(sub['products'])} productos</span>
      <div class="subcat-divider"></div>
    </div>
{specs_html}    <div class="products-grid">
{products_html}    </div>
  </section>
'''

    # Productos directos para otras categorías (no Placas PVC que ya se mostró arriba)
    if cat['name'] != 'Placas PVC' and cat['direct_products']:
        direct_products_html = ''
        for prod_file in cat['direct_products']:
            if is_dup(prod_file):
                continue
            prod_name = os.path.splitext(prod_file)[0]
            mailto = mailto_link(prod_name, cat['name'])
            direct_products_html += f'''      <div class="product-card reveal">
        <div class="product-gallery" onclick="openLightbox('img/{cat['slug']}/{prod_file}', '{prod_name}')">
          <img src="img/{cat['slug']}/{prod_file}" alt="{prod_name}" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">{prod_name}</div>
          <div class="product-actions">
            <a href="{mailto}" class="btn-cotizar">Solicitar Cotización</a>
            <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20me%20interesa%20cotizar%20el%20producto%20{prod_name.replace(' ', '%20')}%20de%20la%20categoría%20{cat['name'].replace(' ', '%20')}" class="btn-whatsapp" target="_blank">WhatsApp</a>
          </div>
        </div>
      </div>
'''

        sections_html += f'''  <section class="subcat-section reveal">
    <div class="subcat-header">
      <h3>Productos {cat['name']}</h3>
      <span class="subcat-count">{len(cat['direct_products'])} productos</span>
      <div class="subcat-divider"></div>
    </div>
    <div class="products-grid">
{direct_products_html}    </div>
  </section>
'''

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cat['name']} | ADIS Catálogo</title>
  <meta name="description" content="{cat['name']} - ADIS Diseño & Remodelación. Explora nuestros productos y solicita tu cotización.">
  <meta property="og:title" content="{cat['name']} | ADIS Catálogo">
  <meta property="og:description" content="{cat['name']} - ADIS Diseño & Remodelación. Explora nuestros productos y solicita tu cotización.">
  <meta property="og:image" content="{hero_bg}">
  <meta property="og:url" content="https://anibru300.github.io/catalogo-adis/{cat['filename']}">
  <meta property="og:type" content="website">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header(cat['slug'])}
{breadcrumbs_html}
  <section class="hero-cat-bg" style="background-image: url('{hero_bg}');">
    <div class="hero-cat-content">
      {'<div class="hero-star-badge">⭐ Producto Estrella</div>' if cat['name'] in ("Lambrin WPC", "Placas PVC") else '<div class="hero-cat-badge">Categoría</div>'}
      <h1>{cat['name']}</h1>
      <p>Explora nuestra línea de {cat['name'].lower()} con {cat['total_products']} productos disponibles. Solicita tu cotización.</p>
    </div>
  </section>

{subcat_nav_html}{sections_html}
{cat_nav_html}
  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
      <a href="contacto.html" class="btn-outline">Contactar</a>
    </div>
  </section>

{generate_testimonios()}
{generate_footer()}
</body>
</html>
'''
    filepath = BASE_DIR / cat['filename']
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"{cat['filename']} generado")


def sync_media():
    """Copia TODAS las fotos y videos de Material de Facebock a media/ con nombres limpios."""
    src_dir = BASE_DIR / 'Material de Facebock'
    media_dir = BASE_DIR / 'media'
    if not src_dir.exists():
        return
    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir(parents=True)
    
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
    
    all_files = sorted([f for f in os.listdir(src_dir) if f.lower().endswith(img_exts + vid_exts)])
    
    # Contadores para nombres automáticos
    auto_img = 0
    auto_vid = 0
    mapping = {}
    
    for fname in all_files:
        if fname in known_names:
            mapping[fname] = known_names[fname]
        elif fname.lower().endswith(img_exts):
            auto_img += 1
            ext = Path(fname).suffix.lower()
            mapping[fname] = f'proyecto-{auto_img:02d}{ext}'
        elif fname.lower().endswith(vid_exts):
            auto_vid += 1
            ext = Path(fname).suffix.lower()
            mapping[fname] = f'video-{auto_vid:02d}{ext}'
    
    copied = 0
    for src_name, dst_name in mapping.items():
        src = src_dir / src_name
        if src.exists():
            shutil.copy2(src, media_dir / dst_name)
            copied += 1
    print(f"Media sincronizada: {copied} archivos ({auto_img} imgs + {auto_vid} vids nuevos)")


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
        'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica',
        'Garantía': 'Consultar ficha técnica',
        'Uso': 'Exterior',
    },
    'Desigual': {
        'Material': 'WPC',
        'Dimensiones': 'Consultar ficha técnica',
        'Presentación': 'Consultar ficha técnica',
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
    for label in ('Material', 'Dimensiones', 'Presentación', 'Garantía', 'Uso'):
        value = data.get(label, 'Consultar ficha técnica')
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
            <div style="font-size: 0.75rem; color: var(--gold);">⭐⭐⭐⭐⭐ — Placas PVC, Nogales</div>
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
            <div style="font-size: 0.75rem; color: var(--gold);">⭐⭐⭐⭐⭐ — Lambrín WPC, Rio Rico</div>
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
            <div style="font-size: 0.75rem; color: var(--gold);">⭐⭐⭐⭐⭐ — Pisos SPC, Nogales</div>
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
        <button type="submit" class="btn-primary" style="align-self: center; margin-top: 0.5rem;">📩 Enviar Testimonio</button>
      </form>
      <div style="text-align: center; margin-top: 1.2rem; font-size: 0.8rem; color: rgba(245,245,245,0.5); line-height: 1.6;">
        Los testimonios son revisados antes de publicarse.<br>
        También puedes enviarlos directamente por 
        <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20dejar%20un%20testimonio" target="_blank" style="color: var(--gold); text-decoration: none; font-weight: 600;">WhatsApp 💬</a>
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
      window.open('https://wa.me/526311928993?text=' + encodeURIComponent(msg.replace(/%0A/g, '\n')), '_blank');
      alert('¡Gracias ' + nombre + '! Tu testimonio se envió por WhatsApp. Será revisado y publicado pronto.');
      e.target.reset();
    }
  </script>
'''

def generate_proyectos():
    """Genera página de proyectos con carruseles de antes/después y galería dinámica."""
    media_dir = BASE_DIR / 'media'
    
    img_exts = ('.jpg', '.jpeg', '.png')
    vid_exts = ('.mp4', '.mov', '.webm')
    
    all_files = sorted([f for f in os.listdir(media_dir) if f.lower().endswith(img_exts + vid_exts)]) if media_dir.exists() else []
    
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
    loose_images = [f for f in images if f not in used]
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Proyectos Reales | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Galería de proyectos reales de ADIS Diseño & Remodelación. Antes y después, remodelaciones de interiores y exteriores.">
  <meta property="og:title" content="Proyectos Reales | ADIS Diseño & Remodelación">
  <meta property="og:description" content="Galería de proyectos reales de ADIS Diseño & Remodelación. Antes y después, remodelaciones de interiores y exteriores.">
  <meta property="og:image" content="media/despues.jpg">
  <meta property="og:url" content="https://anibru300.github.io/catalogo-adis/proyectos.html">
  <meta property="og:type" content="website">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
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
</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header('proyectos')}

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
        total = len(cat['direct_products'])
        for sub in cat['subcategories']:
            total += len(sub['products'])
        cat['total_products'] = total

    print("\nGenerando archivos...")
    generate_style()
    generate_index(categories)
    generate_contacto()
    generate_proyectos()

    for cat in categories:
        generate_category_page(cat, categories)

    # Generar products.json para el buscador
    products_data = []
    for cat in categories:
        for sub in cat['subcategories']:
            for prod in sub['products']:
                products_data.append({
                    'name': os.path.splitext(prod)[0],
                    'category': cat['name'],
                    'subcategory': sub['name'],
                    'url': f"{cat['filename']}#{sub['slug']}",
                    'thumb': f"img/{cat['slug']}/{sub['slug']}/{prod}"
                })
        for prod in cat['direct_products']:
            products_data.append({
                'name': os.path.splitext(prod)[0],
                'category': cat['name'],
                'subcategory': None,
                'url': cat['filename'],
                'thumb': f"img/{cat['slug']}/{prod}"
            })
    with open(BASE_DIR / 'products.json', 'w', encoding='utf-8') as f:
        json.dump(products_data, f, ensure_ascii=False, indent=2)
    print(f"\nproducts.json generado con {len(products_data)} productos")

    print("\nSitio web generado exitosamente en:", BASE_DIR)
    print(f"   - {len(categories)} categorias")
    total_products = sum(len(c['direct_products']) + sum(len(s['products']) for s in c['subcategories']) for c in categories)
    print(f"   - {total_products} productos totales")


if __name__ == '__main__':
    main()
