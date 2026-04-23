import os
import html as html_module

base_dir = r'G:\Mi unidad\ADIS DISEÑO\Catalogo'
output_file = os.path.join(base_dir, 'catalogo.html')

# Mapeo de carpetas a nombres de categoría y fichas técnicas
CATEGORY_CONFIG = {
    'MURO MARMOL DIGITAL': {
        'title': 'Muro Mármol Digital',
        'specs': [
            'Material: Panel de alto brillo',
            'Acabado: Mármol digital UV',
            'Resistencia: Humedad / Rayos UV',
            'Uso: Interiores',
            'Ficha: Consultar especificaciones'
        ]
    },
    'FACHADA Y MURO INTERIOR FLEXIBLE': {
        'title': 'Fachada y Muro Interior Flexible',
        'specs': [
            'Material: Lámina flexible',
            'Acabado: Textura natural',
            'Resistencia: Flexible / Adherible',
            'Uso: Interiores y fachadas',
            'Ficha: Consultar especificaciones'
        ]
    },
    'LAMBIRN WPC INTERIOR': {
        'title': 'Lambrín WPC Interior',
        'specs': [
            'Material: WPC Interior',
            'Medidas: 2900 x 160 x 24 mm',
            'Cobertura: 0.464 m² / pz',
            'Presentación: 14 pz / caja (6.496 m²)',
            'Peso: 30.5 kg / caja',
            'Garantía: 15 años'
        ]
    },
    'LAMBRIN WPC EXTERIOR': {
        'title': 'Lambrín WPC Exterior',
        'specs': [
            'Material: WPC Exterior',
            'Medidas: 2850 x 200 x 26 mm',
            'Cobertura: 0.57 m² / pz',
            'Presentación: 4 pz / caja (2.28 m²)',
            'Peso: 34 kg / caja',
            'Garantía: 10 años ext. / 15 años int.'
        ]
    },
    'PANELES PVC INTERIORES': {
        'title': 'Paneles PVC Interiores',
        'specs': [
            'Material: Panel PVC Interior',
            'Medidas: 2800 x 300 x 9 mm',
            'Cobertura: 0.84 m² / pz',
            'Presentación: 10 pz / caja (8.4 m²)',
            'Peso: 2.8 kg/m²',
            'Garantía: 15 años'
        ]
    },
    'PANELES DECORATIVOS 3D': {
        'title': 'Paneles Decorativos 3D',
        'specs': [
            'Material: Panel Decorativo 3D',
            'Medidas: 500 x 500 x 40/10 mm',
            'Cobertura: 0.25 m² / pz',
            'Presentación: 10 pz / caja (2.5 m²)',
            'Garantía: 1 año',
            'Pintura: A base de aceite'
        ]
    },
    'PANELES METALICOS AUTO ADERIBLES': {
        'title': 'Paneles Metálicos Autoadheribles',
        'specs': [
            'Material: Panel metálico autoadherible',
            'Espesor: 3 mm',
            'Presentación: 5 pz / caja',
            'Garantía: 3 años',
            'Acabado: Metal cepillado / reflectivo',
            'Instalación: Autoadherible'
        ]
    },
    'Paneles XPC 3D autoadheribles': {
        'title': 'Paneles XPC 3D Autoadheribles',
        'specs': [
            'Material: Panel XPC 3D autoadherible',
            'Medidas: 300 x 300 x 4 mm',
            'Cobertura: 0.09 m² / pz',
            'Presentación: 10 pz / caja (0.9 m²)',
            'Garantía: 1 año',
            'Instalación: Autoadherible'
        ]
    },
    'Muros Reflexions': {
        'title': 'Muros Reflexions',
        'specs': [
            'Material: Placa reflectiva',
            'Medidas: 2440 x 1220 x 5 mm',
            'Cobertura: 2.977 m² / pz',
            'Presentación: 1 pz / caja',
            'Peso: 10.5 kg / pz',
            'Garantía: 15 años'
        ]
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
    return name.lower().replace(' ', '-').replace('_', '-').replace('ñ','n').replace('ó','o').replace('á','a').replace('é','e').replace('í','i').replace('ú','u').replace('&','and')[:40]

def escape_html(text):
    return html_module.escape(text)

# Leer carpetas y archivos
categories = []
for folder in CATEGORY_ORDER:
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files.sort()
    config = CATEGORY_CONFIG.get(folder, {'title': folder, 'specs': ['Ficha: Consultar especificaciones']})
    categories.append({
        'folder': folder,
        'id': safe_id(folder),
        'title': config['title'],
        'specs': config['specs'],
        'products': files
    })

# Generar HTML
html_parts = []
html_parts.append('''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Catálogo ADIS | Diseño & Remodelación</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --gold: #C5A059;
      --gold-light: #E8D5A3;
      --black: #0F0F0F;
      --dark: #1A1A1A;
      --gray: #2A2A2A;
      --light: #F5F5F5;
      --white: #FFFFFF;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Montserrat', sans-serif;
      background: var(--black);
      color: var(--light);
      overflow-x: hidden;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--dark); }
    ::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 4px; }

    header {
      position: fixed; top: 0; left: 0; width: 100%; z-index: 1000;
      background: rgba(15,15,15,0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(197,160,89,0.2);
    }
    .header-inner {
      max-width: 1400px; margin: 0 auto;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0.8rem 2rem;
    }
    .logo {
      display: flex; align-items: center; gap: 0.8rem; text-decoration: none;
    }
    .logo img {
      height: 50px; width: auto;
    }
    .logo-text { display: flex; flex-direction: column; }
    .logo-text span:first-child {
      font-size: 1.3rem; font-weight: 700; color: var(--white);
      letter-spacing: 3px; line-height: 1;
    }
    .logo-text span:last-child {
      font-size: 0.6rem; color: var(--gold);
      letter-spacing: 4px; text-transform: uppercase; margin-top: 2px;
    }
    nav.desktop-nav { display: flex; gap: 1.5rem; align-items: center; }
    nav.desktop-nav a {
      color: var(--light); text-decoration: none; font-size: 0.75rem;
      text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;
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

    .hero {
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      position: relative; padding: 6rem 2rem 4rem;
      background: radial-gradient(ellipse at center, #1a1a1a 0%, #0f0f0f 70%);
      overflow: hidden;
    }
    .hero::before {
      content: ''; position: absolute; inset: 0;
      background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c5a059' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
      opacity: 0.5;
    }
    .hero-content {
      max-width: 900px; text-align: center; position: relative; z-index: 2;
    }
    .hero-badge {
      display: inline-block; padding: 0.4rem 1.2rem;
      border: 1px solid var(--gold); color: var(--gold);
      font-size: 0.7rem; letter-spacing: 4px; text-transform: uppercase;
      margin-bottom: 2rem;
    }
    .hero h1 {
      font-family: 'Playfair Display', serif;
      font-size: clamp(2.5rem, 6vw, 5rem);
      color: var(--white); line-height: 1.1; margin-bottom: 1.5rem;
    }
    .hero h1 em {
      color: var(--gold); font-style: normal;
      background: linear-gradient(90deg, var(--gold), var(--gold-light));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p {
      font-size: 1.1rem; color: rgba(245,245,245,0.7);
      line-height: 1.8; max-width: 700px; margin: 0 auto 2.5rem;
    }
    .hero-buttons {
      display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;
    }
    .btn {
      padding: 0.9rem 2.2rem; font-family: 'Montserrat', sans-serif;
      font-size: 0.8rem; font-weight: 700; letter-spacing: 2px;
      text-transform: uppercase; text-decoration: none; cursor: pointer;
      border: 2px solid var(--gold); transition: all 0.3s ease;
    }
    .btn-primary {
      background: var(--gold); color: var(--black);
    }
    .btn-primary:hover {
      background: transparent; color: var(--gold);
    }
    .btn-outline {
      background: transparent; color: var(--gold);
    }
    .btn-outline:hover {
      background: var(--gold); color: var(--black);
    }
    .scroll-indicator {
      position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%);
      display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
      animation: bounce 2s infinite;
    }
    .scroll-indicator span {
      font-size: 0.6rem; letter-spacing: 3px; text-transform: uppercase; color: var(--gold);
    }
    .scroll-line {
      width: 1px; height: 40px; background: linear-gradient(to bottom, var(--gold), transparent);
    }

    .info-section {
      padding: 5rem 2rem; background: var(--dark);
      border-top: 1px solid rgba(197,160,89,0.1);
    }
    .container {
      max-width: 1200px; margin: 0 auto;
    }
    .section-header {
      text-align: center; margin-bottom: 3rem;
    }
    .section-header h2 {
      font-family: 'Playfair Display', serif; font-size: 2.2rem; color: var(--white);
      margin-bottom: 0.8rem;
    }
    .section-header p {
      color: rgba(245,245,245,0.6); font-size: 0.95rem; max-width: 600px; margin: 0 auto;
    }
    .divider {
      width: 60px; height: 3px; background: var(--gold); margin: 1rem auto;
    }
    .info-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 2rem;
    }
    .info-card {
      background: var(--gray); padding: 2rem; border: 1px solid rgba(197,160,89,0.1);
      transition: all 0.3s ease; text-align: center;
    }
    .info-card:hover {
      border-color: var(--gold); transform: translateY(-5px);
      box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    .info-card .icon {
      width: 50px; height: 50px; margin: 0 auto 1rem;
      border: 1px solid var(--gold); border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: var(--gold); font-size: 1.3rem;
    }
    .info-card h3 {
      font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase;
      color: var(--white); margin-bottom: 0.5rem;
    }
    .info-card p {
      font-size: 0.8rem; color: rgba(245,245,245,0.6); line-height: 1.6;
    }

    .cat-nav {
      position: sticky; top: 69px; z-index: 100;
      background: rgba(26,26,26,0.98);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(197,160,89,0.15);
      padding: 1rem 2rem;
    }
    .cat-nav-inner {
      max-width: 1400px; margin: 0 auto;
      display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;
    }
    .cat-link {
      padding: 0.5rem 1rem; background: transparent;
      border: 1px solid rgba(197,160,89,0.3); color: var(--light);
      font-family: 'Montserrat', sans-serif; font-size: 0.7rem;
      font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase;
      text-decoration: none; cursor: pointer; transition: all 0.3s;
    }
    .cat-link:hover, .cat-link.active {
      background: var(--gold); border-color: var(--gold); color: var(--black);
    }

    .category {
      padding: 4rem 2rem;
    }
    .category:nth-child(odd) { background: var(--black); }
    .category:nth-child(even) { background: var(--dark); }
    .cat-title {
      display: flex; align-items: center; gap: 1rem; margin-bottom: 3rem;
      justify-content: center;
    }
    .cat-title h2 {
      font-family: 'Playfair Display', serif; font-size: 1.8rem; color: var(--white); text-align: center;
    }
    .cat-title .line {
      flex: 1; max-width: 80px; height: 1px; background: rgba(197,160,89,0.4);
    }
    .products-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 2rem; max-width: 1400px; margin: 0 auto;
    }

    .product-card {
      background: var(--gray);
      border: 1px solid rgba(197,160,89,0.08);
      overflow: hidden; transition: all 0.4s ease;
      display: flex; flex-direction: column;
    }
    .product-card:hover {
      border-color: rgba(197,160,89,0.4);
      box-shadow: 0 15px 50px rgba(0,0,0,0.4);
      transform: translateY(-8px);
    }
    .product-specs {
      padding: 1.5rem;
      border-bottom: 1px solid rgba(197,160,89,0.1);
    }
    .product-header {
      display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;
      gap: 0.5rem;
    }
    .product-name {
      font-family: 'Playfair Display', serif; font-size: 1.3rem; color: var(--white);
    }
    .product-code {
      font-size: 0.6rem; color: var(--gold); letter-spacing: 1.5px;
      text-transform: uppercase; background: rgba(197,160,89,0.1);
      padding: 0.2rem 0.5rem; border-radius: 2px; white-space: nowrap;
    }
    .specs-list {
      list-style: none; display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem 1rem;
    }
    .specs-list li {
      font-size: 0.72rem; color: rgba(245,245,245,0.6);
      display: flex; align-items: center; gap: 0.4rem;
    }
    .specs-list li::before {
      content: '•'; color: var(--gold); font-size: 1rem; line-height: 0;
    }
    .specs-list .full-width { grid-column: 1 / -1; }
    .product-gallery {
      position: relative; flex: 1; min-height: 220px;
      background: #111; overflow: hidden;
    }
    .product-gallery img {
      width: 100%; height: 100%; object-fit: cover;
      transition: transform 0.6s ease; display: block;
    }
    .product-card:hover .product-gallery img {
      transform: scale(1.05);
    }
    .gallery-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 50%);
      opacity: 0; transition: opacity 0.3s;
      display: flex; align-items: flex-end; justify-content: center;
      padding-bottom: 1rem;
    }
    .product-card:hover .gallery-overlay { opacity: 1; }
    .gallery-btn {
      padding: 0.5rem 1.2rem; background: var(--gold); color: var(--black);
      font-size: 0.7rem; font-weight: 700; letter-spacing: 1px;
      text-transform: uppercase; border: none; cursor: pointer;
      transition: transform 0.3s;
    }
    .gallery-btn:hover { transform: scale(1.05); }
    .no-image {
      width: 100%; height: 100%; display: flex; flex-direction: column;
      align-items: center; justify-content: center; background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
      color: rgba(245,245,245,0.3); gap: 0.5rem; min-height: 220px;
    }
    .no-image span:first-child { font-size: 2rem; color: var(--gold); opacity: 0.3; }
    .no-image span:last-child { font-size: 0.75rem; letter-spacing: 2px; text-transform: uppercase; }

    .lightbox {
      position: fixed; inset: 0; z-index: 2000;
      background: rgba(0,0,0,0.95);
      display: none; align-items: center; justify-content: center;
      padding: 2rem;
    }
    .lightbox.active { display: flex; }
    .lightbox img {
      max-width: 90vw; max-height: 85vh; object-fit: contain;
      border: 1px solid rgba(197,160,89,0.2);
    }
    .lightbox-close {
      position: absolute; top: 2rem; right: 2rem;
      background: none; border: none; color: var(--gold);
      font-size: 2.5rem; cursor: pointer; line-height: 1;
    }
    .lightbox-caption {
      position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%);
      color: var(--white); font-size: 0.9rem; letter-spacing: 2px;
      text-transform: uppercase; background: rgba(0,0,0,0.6);
      padding: 0.5rem 1.5rem;
    }

    footer {
      background: var(--black); border-top: 1px solid rgba(197,160,89,0.1);
      padding: 4rem 2rem 2rem; text-align: center;
    }
    .footer-logo {
      display: inline-flex; align-items: center; gap: 0.8rem; margin-bottom: 1.5rem;
    }
    .footer-logo img { height: 60px; width: auto; }
    .footer-info {
      color: rgba(245,245,245,0.5); font-size: 0.85rem; line-height: 1.8;
      max-width: 500px; margin: 0 auto 2rem;
    }
    .footer-info strong { color: var(--gold); font-weight: 600; }
    .social-links {
      display: flex; gap: 1rem; justify-content: center; margin-bottom: 2rem;
    }
    .social-links a {
      width: 40px; height: 40px; border: 1px solid rgba(197,160,89,0.3);
      display: flex; align-items: center; justify-content: center;
      color: var(--gold); text-decoration: none; font-size: 0.8rem;
      transition: all 0.3s;
    }
    .social-links a:hover { background: var(--gold); color: var(--black); }
    .copyright {
      font-size: 0.7rem; color: rgba(245,245,245,0.3); letter-spacing: 2px;
      border-top: 1px solid rgba(197,160,89,0.1); padding-top: 1.5rem;
    }

    @keyframes bounce {
      0%, 20%, 50%, 80%, 100% { transform: translateX(-50%) translateY(0); }
      40% { transform: translateX(-50%) translateY(-10px); }
      60% { transform: translateX(-50%) translateY(-5px); }
    }

    @media (max-width: 768px) {
      .desktop-nav { display: none; }
      .menu-btn { display: block; }
      .hero h1 { font-size: 2.2rem; }
      .products-grid { grid-template-columns: 1fr; }
      .specs-list { grid-template-columns: 1fr; }
      .cat-nav-inner { gap: 0.4rem; }
      .cat-link { padding: 0.4rem 0.8rem; font-size: 0.6rem; }
      .header-inner { padding: 0.8rem 1rem; }
      .product-header { flex-direction: column; }
    }
  </style>
</head>
<body>

  <header id="header">
    <div class="header-inner">
      <a href="#" class="logo">
        <img src="LOGO ADIS.png" alt="ADIS Logo">
      </a>
      <nav class="desktop-nav">
        <a href="#inicio">Inicio</a>
        <a href="#nosotros">Nosotros</a>
''')

# Navegación desktop
for cat in categories:
    html_parts.append(f'        <a href="#{cat["id"]}">{cat["title"]}</a>\n')
html_parts.append('''        <a href="#contacto">Contacto</a>
      </nav>
      <button class="menu-btn" onclick="toggleMenu()">☰</button>
    </div>
  </header>

  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">✕</button>
    <a href="#inicio" onclick="toggleMenu()">Inicio</a>
    <a href="#nosotros" onclick="toggleMenu()">Nosotros</a>
''')

# Navegación móvil
for cat in categories:
    html_parts.append(f'    <a href="#{cat["id"]}" onclick="toggleMenu()">{cat["title"]}</a>\n')
html_parts.append('''    <a href="#contacto" onclick="toggleMenu()">Contacto</a>
  </div>

  <section class="hero" id="inicio">
    <div class="hero-content">
      <div class="hero-badge">Catálogo 2025 — 2026</div>
      <h1>Transforma tus espacios con <em>ADIS</em></h1>
      <p>En ADI'S DISEÑO & REMODELACIÓN ofrecemos soluciones integrales en recubrimientos: muros de mármol digital, lambrines WPC para interior y exterior, paneles PVC, decorativos 3D, metálicos autoadheribles, XPC y muros reflections.</p>
      <div class="hero-buttons">
        <a href="#muro-marmol-digital" class="btn btn-primary">Ver Catálogo</a>
        <a href="#contacto" class="btn btn-outline">Contáctanos</a>
      </div>
    </div>
    <div class="scroll-indicator">
      <span>Explorar</span>
      <div class="scroll-line"></div>
    </div>
  </section>

  <section class="info-section" id="nosotros">
    <div class="container">
      <div class="section-header">
        <h2>Sobre ADIS</h2>
        <div class="divider"></div>
        <p>En ADI'S DISEÑO & REMODELACIÓN nos especializamos en ofrecer soluciones funcionales, estéticas y duraderas para la transformación de espacios interiores y exteriores.</p>
      </div>
      <div class="info-grid">
        <div class="info-card">
          <div class="icon">✦</div>
          <h3>Mármol Digital</h3>
          <p>Paneles de alto brillo con acabados digitales que imitan mármol, piedra y texturas exclusivas.</p>
        </div>
        <div class="info-card">
          <div class="icon">◈</div>
          <h3>WPC Interior / Exterior</h3>
          <p>Lambrines de Wood Plastic Composite resistentes a la humedad, rayos UV y fáciles de instalar.</p>
        </div>
        <div class="info-card">
          <div class="icon">◉</div>
          <h3>PVC & 3D</h3>
          <p>Paneles PVC livianos y paneles decorativos 3D autoadheribles para crear ambientes únicos.</p>
        </div>
        <div class="info-card">
          <div class="icon">✚</div>
          <h3>Metálicos & Reflections</h3>
          <p>Acabados metálicos autoadheribles y placas tipo espejo para un toque de lujo y modernidad.</p>
        </div>
      </div>
    </div>
  </section>

  <div class="cat-nav">
    <div class="cat-nav-inner">
''')

# Cat-nav links
for cat in categories:
    html_parts.append(f'      <a href="#{cat["id"]}" class="cat-link">{cat["title"]}</a>\n')
html_parts.append('''    </div>
  </div>

''')

# Generar categorías
for idx, cat in enumerate(categories):
    html_parts.append(f'  <section class="category" id="{cat["id"]}">\n')
    html_parts.append('    <div class="cat-title">\n')
    html_parts.append('      <div class="line"></div>\n')
    html_parts.append(f'      <h2>{cat["title"]}</h2>\n')
    html_parts.append('      <div class="line"></div>\n')
    html_parts.append('    </div>\n')
    html_parts.append('    <div class="products-grid">\n')
    
    for prod_file in cat['products']:
        prod_name = os.path.splitext(prod_file)[0]
        # Limpiar nombre para código
        prod_code = prod_name.upper().replace(' ', '-').replace('Ñ','N').replace('Ó','O').replace('Á','A').replace('É','E').replace('Í','I').replace('Ú','U')[:15]
        img_path = f'{cat["folder"]}/{prod_file}'
        img_path_escaped = img_path.replace("'", "\\'")
        prod_name_escaped = prod_name.replace("'", "\\'")
        
        html_parts.append('      <div class="product-card">\n')
        html_parts.append('        <div class="product-specs">\n')
        html_parts.append('          <div class="product-header">\n')
        html_parts.append(f'            <div class="product-name">{escape_html(prod_name)}</div>\n')
        html_parts.append(f'            <div class="product-code">{escape_html(prod_code)}</div>\n')
        html_parts.append('          </div>\n')
        html_parts.append('          <ul class="specs-list">\n')
        for spec in cat['specs']:
            html_parts.append(f'            <li>{escape_html(spec)}</li>\n')
        html_parts.append('          </ul>\n')
        html_parts.append('        </div>\n')
        html_parts.append(f'        <div class="product-gallery" onclick="openLightbox(\'{img_path_escaped}\', \'{prod_name_escaped}\')">\n')
        html_parts.append(f'          <img src="{img_path_escaped}" alt="{prod_name_escaped}" loading="lazy">\n')
        html_parts.append('          <div class="gallery-overlay"><button class="gallery-btn">Ampliar</button></div>\n')
        html_parts.append('        </div>\n')
        html_parts.append('      </div>\n')
    
    html_parts.append('    </div>\n')
    html_parts.append('  </section>\n\n')

# Footer y scripts
html_parts.append('''  <footer id="contacto">
    <div class="footer-logo">
      <img src="LOGO ADIS.png" alt="ADIS Logo">
    </div>
    <div class="footer-info">
      <strong>ADI'S DISEÑO & REMODELACIÓN</strong><br>
      Creando espacios, reinventando hogares.<br>
      Nogales, Sonora · Rio Rico, AZ · Decosonora<br>
      Tel. MX: +52 631-192-8993 · Tel. USA: +1 (520) 839-2877<br>
      adis.remodelacion@gmail.com
    </div>
    <div class="social-links">
      <a href="#" title="Facebook">f</a>
      <a href="#" title="Instagram">i</a>
      <a href="#" title="WhatsApp">w</a>
    </div>
    <div class="copyright">
      © 2026 ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.
    </div>
  </footer>

  <div class="lightbox" id="lightbox" onclick="closeLightbox(event)">
    <button class="lightbox-close" onclick="closeLightbox(event)">✕</button>
    <img src="" alt="" id="lightboxImg">
    <div class="lightbox-caption" id="lightboxCaption"></div>
  </div>

  <script>
    function toggleMenu() {
      document.getElementById('mobileMenu').classList.toggle('active');
    }
    function openLightbox(src, caption) {
      const lb = document.getElementById('lightbox');
      document.getElementById('lightboxImg').src = src;
      document.getElementById('lightboxCaption').textContent = caption;
      lb.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
    function closeLightbox(e) {
      if (e.target.id === 'lightbox' || e.target.classList.contains('lightbox-close')) {
        document.getElementById('lightbox').classList.remove('active');
        document.body.style.overflow = '';
      }
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.getElementById('lightbox').classList.remove('active');
        document.body.style.overflow = '';
      }
    });

    const sections = document.querySelectorAll('.category');
    const navLinks = document.querySelectorAll('.cat-link');
    window.addEventListener('scroll', () => {
      let current = '';
      sections.forEach(section => {
        const sectionTop = section.offsetTop - 150;
        if (scrollY >= sectionTop) current = section.getAttribute('id');
      });
      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) link.classList.add('active');
      });
    });

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.product-card').forEach(card => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(30px)';
      card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      observer.observe(card);
    });
  </script>

</body>
</html>
''')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(''.join(html_parts))

print(f'Catálogo generado: {output_file}')
print(f'Total categorías: {len(categories)}')
for cat in categories:
    print(f'  - {cat["title"]}: {len(cat["products"])} productos')
