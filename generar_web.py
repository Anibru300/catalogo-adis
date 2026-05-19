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
    'ubicacion': 'Nogales, Sonora · Rio Rico, AZ',
    'facebook': 'https://www.facebook.com/p/Adis-Dise%C3%B1o-Remodelaci%C3%B3n-61579849591594/'
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
            
            # Copiar ficha tecnica de subcategoria si existe
            if sub['ficha']:
                src = sub['path'] / sub['ficha']
                dst = sub_img_dir / sub['ficha']
                shutil.copy2(src, dst)
        
        # Copiar ficha tecnica de categoria si existe
        if cat['ficha']:
            src = cat['path'] / cat['ficha']
            dst = cat_img_dir / cat['ficha']
            shutil.copy2(src, dst)
    
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

/* MOBILE */
@media (max-width: 768px) {
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
    """Genera el header HTML."""
    nav_links = '<a href="index.html">Inicio</a>\n        <a href="index.html#categorias">Catálogo</a>\n        <a href="proyectos.html">Proyectos</a>\n        <a href="contacto.html">Contacto</a>'
    if current_page != 'index':
        nav_links = '<a href="index.html">← Inicio</a>\n        <a href="index.html#categorias">Catálogo</a>\n        <a href="proyectos.html">Proyectos</a>\n        <a href="contacto.html">Contacto</a>'

    return f'''  <header>
    <div class="header-inner">
      <a href="index.html" class="logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></a>
      <nav class="desktop-nav">
        {nav_links}
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Buscar producto..." autocomplete="off" title="Presiona / para buscar">
          <button onclick="performSearch()">🔍</button>
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
'''


def generate_footer():
    chatbot_js = '''
  <script>
    // Toggle mobile menu
    function toggleMenu() { document.getElementById('mobileMenu').classList.toggle('active'); }
    
    // Chatbot
    (function() {
      const chatWindow = document.getElementById('chatbotWindow');
      const chatBody = document.getElementById('chatbotBody');
      
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
      
      function showOptions() {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        
        const opts = document.createElement('div');
        opts.className = 'chat-options';
        opts.innerHTML = `
          <button class="chat-option-btn" onclick="chatOption('ubicacion')">📍 Ubicación</button>
          <button class="chat-option-btn" onclick="chatOption('fichas')">📋 Fichas técnicas</button>
          <button class="chat-option-btn" onclick="chatOption('venta')">📦 ¿Cómo se venden?</button>
          <button class="chat-option-btn" onclick="chatOption('precios')">💰 Precios</button>
          <button class="chat-option-btn" onclick="chatOption('whatsapp')">💬 Hablar con asesor</button>
        `;
        chatBody.appendChild(opts);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      window.chatOption = function(key) {
        const existing = chatBody.querySelector('.chat-options');
        if (existing) existing.remove();
        
        const responses = {
          ubicacion: `📍 <strong>Nogales, Sonora</strong> y atendemos también en <strong>Rio Rico, AZ</strong>.<br><br>Puedes ver nuestra ubicación exacta en la página de <a href="contacto.html" style="color:#C5A059">Contacto</a> o en <a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" style="color:#C5A059">Google Maps →</a>`,
          fichas: `📋 Cada producto tiene su ficha técnica disponible.<br><br>Ve al <a href="index.html#categorias" style="color:#C5A059">Catálogo</a>, selecciona la categoría y subcategoría que te interesa, y haz clic en <strong>"Ver Ficha Técnica"</strong>.`,
          venta: `📦 Vendemos por pieza, caja o metro cuadrado según el producto.<br><br>Usa la <strong>calculadora de materiales</strong> en cada categoría para saber cuánto necesitas, o solicita una <strong>cotización</strong> directamente desde cualquier producto.`,
          precios: `💰 Los precios varían según el producto y la cantidad.<br><br>¿Te gustaría que un asesor te prepare una cotización personalizada?<br><a href="https://wa.me/526311928993?text=Hola%20ADIS,%20quiero%20una%20cotización" target="_blank" class="chat-whatsapp-btn">📱 Solicitar cotización</a>`,
          whatsapp: `💬 Te conecto con un asesor por WhatsApp...`
        };
        
        const labels = {
          ubicacion: '📍 Ubicación',
          fichas: '📋 Fichas técnicas',
          venta: '📦 ¿Cómo se venden?',
          precios: '💰 Precios',
          whatsapp: '💬 Hablar con asesor'
        };
        
        addMessage(labels[key], true);
        
        if (key === 'whatsapp') {
          setTimeout(() => {
            window.open('https://wa.me/526311928993?text=Hola%20ADIS,%20tengo%20una%20pregunta', '_blank');
            addMessage('✅ Se abrió WhatsApp. Un asesor te atenderá pronto.', false);
            setTimeout(showOptions, 1000);
          }, 500);
        } else {
          setTimeout(() => {
            addMessage(responses[key], false);
            setTimeout(showOptions, 500);
          }, 400);
        }
      };
      
      function showWelcome() {
        addMessage('¡Hola! 👋 Soy el <strong>asistente virtual de ADIS</strong>.<br>¿En qué puedo ayudarte hoy?', false);
        setTimeout(showOptions, 300);
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

    // Buscador global mejorado
    (function() {
      let allProducts = [];
      let debounceTimer = null;
      let activeIndex = -1;
      let currentResults = [];
      
      fetch('products.json')
        .then(r => r.json())
        .then(data => { allProducts = data; })
        .catch(() => { allProducts = []; });
      
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

        cat_cards += f'''      <a href="{cat['filename']}" class="cat-card reveal">
        <img src="{thumb_src}" alt="{cat['name']}" loading="lazy">
        <div class="cat-card-overlay">
          <div class="cat-arrow">→</div>
          <h3>{cat['name']}</h3>
          <span>{total_prods} productos</span>
        </div>
      </a>
'''

    info_cards = '''      <div class="info-card">
        <div class="icon">✦</div>
        <h3>Placas PVC</h3>
        <p>Paneles rígidos de alta calidad tipo madera, texturizados y espejo. Ideales para interiores.</p>
      </div>
      <div class="info-card">
        <div class="icon">◈</div>
        <h3>Lambrín WPC</h3>
        <p>Wood Plastic Composite para interior y exterior. Resistente a la humedad y rayos UV.</p>
      </div>
      <div class="info-card">
        <div class="icon">◉</div>
        <h3>Pisos & Zacate</h3>
        <p>Laminados, WPC, SPC, deck sintético y pasto artificial para todo tipo de espacios.</p>
      </div>
      <div class="info-card">
        <div class="icon">✚</div>
        <h3>Cladding & 3D</h3>
        <p>Paneles decorativos tridimensionales y revestimientos de alta gama para fachadas.</p>
      </div>
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

    # Seleccionar imagen de fondo representativa para el hero
    hero_bg = ''
    if cat['subcategories'] and cat['subcategories'][0]['products']:
        hero_bg = f"img/{cat['slug']}/{cat['subcategories'][0]['slug']}/{cat['subcategories'][0]['products'][0]}"
    elif cat['direct_products']:
        hero_bg = f"img/{cat['slug']}/{cat['direct_products'][0]}"

    # Índice de subcategorías
    subcat_nav_links = ''
    for sub in cat['subcategories']:
        if sub['products']:
            sub_slug = sub['slug']
            sub_name = sub['name']
            subcat_nav_links += f'<a href="#{sub_slug}">{sub_name}</a>' + '\n    '
    subcat_nav_html = f'''  <div class="subcat-nav">
    {subcat_nav_links}</div>
''' if subcat_nav_links else ''

    # Construir secciones de subcategorías
    subcat_sections = ''
    for sub in cat['subcategories']:
        if not sub['products']:
            continue

        # Especificaciones técnicas de subcategoría
        specs_html = generate_specs_table(sub['name'])

        # Productos de subcategoría
        products_html = ''
        for prod_file in sub['products']:
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

        subcat_sections += f'''  <section class="subcat-section reveal" id="{sub['slug']}">
    <div class="subcat-header">
      <h3>{sub['name']}</h3>
      <span class="subcat-count">{len(sub['products'])} productos</span>
      <div class="subcat-divider"></div>
    </div>
{specs_html}    <div class="products-grid">
{products_html}    </div>
  </section>
'''

    # Productos directos (sin subcategoría)
    direct_section = ''
    if cat['direct_products']:
        direct_products_html = ''
        for prod_file in cat['direct_products']:
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

        direct_section = f'''  <section class="subcat-section reveal">
    <div class="subcat-header">
      <h3>Productos {cat['name']}</h3>
      <span class="subcat-count">{len(cat['direct_products'])} productos</span>
      <div class="subcat-divider"></div>
    </div>
    <div class="products-grid">
{direct_products_html}    </div>
  </section>
'''

    # Especificaciones generales de categoría (si tiene productos directos)
    cat_specs = ''
    if cat['direct_products']:
        cat_specs = generate_specs_table(cat['name'])

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

  <section class="hero-cat-bg" style="background-image: url('{hero_bg}');">
    <div class="hero-cat-content">
      <div class="hero-cat-badge">Categoría</div>
      <h1>{cat['name']}</h1>
      <p>Explora nuestra línea de {cat['name'].lower()} con {cat['total_products']} productos disponibles. Solicita tu cotización.</p>
    </div>
  </section>

{subcat_nav_html}{subcat_sections}
{direct_section}

  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
      <a href="contacto.html" class="btn-outline">Contactar</a>
    </div>
  </section>

{generate_footer()}
</body>
</html>
'''
    filepath = BASE_DIR / cat['filename']
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"{cat['filename']} generado")


def sync_media():
    """Copia fotos y videos de Material de Facebock a media/"""
    src_dir = BASE_DIR / 'Material de Facebock'
    media_dir = BASE_DIR / 'media'
    if not src_dir.exists():
        return
    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir(parents=True)
    
    mapping = {
        'antes.jpg': 'antes.jpg',
        'despues.jpg': 'despues.jpg',
        'ejemplo de tapiz.jpg': 'ejemplo-tapiz.jpg',
        '666284575_122140320836994986_788780118445842656_n.jpg': 'proyecto-recepcion.jpg',
        '670492075_122140320794994986_7881130192341646317_n.jpg': 'proyecto-recepcion-thumb.jpg',
        '647152617_122136539756994986_7884244820762960889_n.jpg': 'equipo-adis.jpg',
        'Remoledacion de habitacion.mp4': 'video-habitacion.mp4',
        'remoledacion de consultorio.mp4': 'video-consultorio.mp4',
    }
    fb_videos = sorted([f for f in os.listdir(src_dir) if f.endswith('.mp4') and f not in mapping])
    for i, fv in enumerate(fb_videos):
        mapping[fv] = f'video-proyecto-{i+1}.mp4'
    
    copied = 0
    for src_name, dst_name in mapping.items():
        src = src_dir / src_name
        if src.exists():
            shutil.copy2(src, media_dir / dst_name)
            copied += 1
    print(f"Media sincronizada: {copied} archivos")


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


def generate_proyectos():
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
    .before-after {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 1000px; margin: 0 auto; }}
    .before-after img {{ width: 100%; height: 300px; object-fit: cover; border-radius: 8px; }}
    .ba-label {{ text-align: center; color: var(--gold); font-family: 'Playfair Display', serif; font-size: 1.2rem; margin-top: 0.5rem; }}
    .video-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: 0 auto; }}
    .video-card video {{ width: 100%; border-radius: 8px; }}
    @media (max-width: 768px) {{ .before-after {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <canvas id="bg-canvas"></canvas>
{generate_header('proyectos')}

  <section class="hero-cat">
    <h1>Proyectos Reales</h1>
    <p>Transformaciones que hablan por sí solas. Conoce nuestro trabajo.</p>
  </section>

  <section class="section-wrap">
    <div class="section-header">
      <h2>Antes y Después</h2>
      <div class="divider"></div>
      <p>De una sala común a un espacio de lujo con nuestros recubrimientos.</p>
    </div>
    <div class="before-after">
      <div>
        <img src="media/antes.jpg" alt="Antes" loading="lazy">
        <div class="ba-label">Antes</div>
      </div>
      <div>
        <img src="media/despues.jpg" alt="Después" loading="lazy">
        <div class="ba-label">Después</div>
      </div>
    </div>
  </section>

  <section class="section-wrap-alt">
    <div class="section-header">
      <h2>Galería de Proyectos</h2>
      <div class="divider"></div>
    </div>
    <div class="products-grid">
      <div class="product-card">
        <div class="product-gallery">
          <img src="media/ejemplo-tapiz.jpg" alt="Pared con tapiz y lambrín" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">Pared con Tapiz y Lambrín WPC</div>
        </div>
      </div>
      <div class="product-card">
        <div class="product-gallery">
          <img src="media/proyecto-recepcion.jpg" alt="Recepción con lambrín WPC" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">Recepción con Lambrín WPC</div>
        </div>
      </div>
      <div class="product-card">
        <div class="product-gallery">
          <img src="media/equipo-adis.jpg" alt="Equipo ADIS en obra" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name">Equipo ADIS en Obra</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section-wrap">
    <div class="section-header">
      <h2>Videos de Remodelaciones</h2>
      <div class="divider"></div>
    </div>
    <div class="video-grid">
      <div class="video-card">
        <video class="auto-video" muted loop playsinline poster="media/despues.jpg">
          <source src="media/video-habitacion.mp4" type="video/mp4">
        </video>
        <div class="product-info">
          <div class="product-name">Remodelación de Habitación</div>
        </div>
      </div>
      <div class="video-card">
        <video class="auto-video" muted loop playsinline poster="media/proyecto-recepcion.jpg">
          <source src="media/video-consultorio.mp4" type="video/mp4">
        </video>
        <div class="product-info">
          <div class="product-name">Remodelación de Consultorio</div>
        </div>
      </div>
    </div>
  </section>

  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
      <a href="contacto.html" class="btn-outline">Contactar</a>
    </div>
  </section>

  <script>
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
