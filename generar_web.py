import os

base_dir = r'G:\Mi unidad\ADIS DISEÑO\Catalogo'

CATEGORY_CONFIG = {
    'MURO MARMOL DIGITAL': {
        'title': 'Muro Mármol Digital',
        'specs': [
            ['Material', 'Panel de alto brillo con acabado digital UV'],
            ['Acabado', 'Mármol digital UV'],
            ['Resistencia', 'Humedad / Rayos UV'],
            ['Uso', 'Interiores'],
            ['Garantía', '15 años']
        ],
        'desc': 'Paneles de alto brillo con acabados digitales que imitan mármol, piedra y texturas exclusivas. Ideales para muros interiores de alto impacto visual.',
        'calc': {'area_pz': 0.84, 'pz_caja': 10, 'label': 'm² / pz'}
    },
    'FACHADA Y MURO INTERIOR FLEXIBLE': {
        'title': 'Fachada y Muro Interior Flexible',
        'specs': [
            ['Material', 'Lámina flexible'],
            ['Acabado', 'Textura natural'],
            ['Resistencia', 'Flexible / Adherible'],
            ['Uso', 'Interiores y fachadas'],
            ['Garantía', 'Consultar']
        ],
        'desc': 'Láminas flexibles para fachada y muro interior con textura que imita concreto, granito y madera. Se adaptan a cualquier superficie.',
        'calc': None
    },
    'LAMBIRN WPC INTERIOR': {
        'title': 'Lambrín WPC Interior',
        'specs': [
            ['Material', 'WPC (Wood Plastic Composite)'],
            ['Medidas', '2900 x 160 x 24 mm'],
            ['Cobertura', '0.464 m² / pieza'],
            ['Presentación', '14 pz / caja (6.496 m²)'],
            ['Peso', '30.5 kg / caja'],
            ['Garantía', '15 años']
        ],
        'desc': 'Listones de WPC para revestimiento interior de paredes. Resistentes a la humedad, fáciles de instalar y con acabados tipo madera naturales.',
        'calc': {'area_pz': 0.464, 'pz_caja': 14, 'label': 'm² / pz'}
    },
    'LAMBRIN WPC EXTERIOR': {
        'title': 'Lambrín WPC Exterior',
        'specs': [
            ['Material', 'WPC Exterior'],
            ['Medidas', '2850 x 200 x 26 mm'],
            ['Cobertura', '0.57 m² / pieza'],
            ['Presentación', '4 pz / caja (2.28 m²)'],
            ['Peso', '34 kg / caja'],
            ['Garantía', '10 años ext. / 15 años int.']
        ],
        'desc': 'Lambrines de WPC diseñados para resistir condiciones climáticas exteriores. Ideales para fachadas, terrazas y pérgolas.',
        'calc': {'area_pz': 0.57, 'pz_caja': 4, 'label': 'm² / pz'}
    },
    'PANELES PVC INTERIORES': {
        'title': 'Paneles PVC Interiores',
        'specs': [
            ['Material', 'PVC rígido'],
            ['Medidas', '2800 x 300 x 9 mm'],
            ['Cobertura', '0.84 m² / pieza'],
            ['Presentación', '10 pz / caja (8.4 m²)'],
            ['Peso', '2.8 kg/m²'],
            ['Garantía', '15 años']
        ],
        'desc': 'Paneles de PVC livianos y resistentes para interiores. Fáciles de instalar, limpiar y mantener. Perfectos para cocinas y baños.',
        'calc': {'area_pz': 0.84, 'pz_caja': 10, 'label': 'm² / pz'}
    },
    'PANELES DECORATIVOS 3D': {
        'title': 'Paneles Decorativos 3D',
        'specs': [
            ['Material', 'Panel Decorativo 3D'],
            ['Medidas', '500 x 500 x 40/10 mm'],
            ['Cobertura', '0.25 m² / pieza'],
            ['Presentación', '10 pz / caja (2.5 m²)'],
            ['Garantía', '1 año'],
            ['Pintura', 'A base de aceite']
        ],
        'desc': 'Paneles tridimensionales con relieve decorativo. Pintables y fáciles de instalar. Ideales para muros de accento en residencias y comercios.',
        'calc': {'area_pz': 0.25, 'pz_caja': 10, 'label': 'm² / pz'}
    },
    'PANELES METALICOS AUTO ADERIBLES': {
        'title': 'Paneles Metálicos Autoadheribles',
        'specs': [
            ['Material', 'Panel metálico autoadherible'],
            ['Espesor', '3 mm'],
            ['Presentación', '5 pz / caja'],
            ['Garantía', '3 años'],
            ['Instalación', 'Autoadherible'],
            ['Uso', 'Interiores']
        ],
        'desc': 'Mosaicos metálicos con acabado cepillado y reflectivo. Autoadheribles para una instalación rápida y sin complicaciones.',
        'calc': None
    },
    'Paneles XPC 3D autoadheribles': {
        'title': 'Paneles XPC 3D Autoadheribles',
        'specs': [
            ['Material', 'Panel XPC 3D autoadherible'],
            ['Medidas', '300 x 300 x 4 mm'],
            ['Cobertura', '0.09 m² / pieza'],
            ['Presentación', '10 pz / caja (0.9 m²)'],
            ['Garantía', '1 año'],
            ['Instalación', 'Autoadherible']
        ],
        'desc': 'Paneles XPC con patrón 3D y autoadhesivo. Diseños modernos tipo ladrillo y geométricos para transformar cualquier ambiente.',
        'calc': {'area_pz': 0.09, 'pz_caja': 10, 'label': 'm² / pz'}
    },
    'Muros Reflexions': {
        'title': 'Muros Reflexions',
        'specs': [
            ['Material', 'Placa reflectiva'],
            ['Medidas', '2440 x 1220 x 5 mm'],
            ['Cobertura', '2.977 m² / pieza'],
            ['Presentación', '1 pz / caja'],
            ['Peso', '10.5 kg / pieza'],
            ['Garantía', '15 años']
        ],
        'desc': 'Placas con acabado altamente reflectivo tipo espejo, dorado o metal cepillado. Un toque de lujo y modernidad para interiores.',
        'calc': {'area_pz': 2.977, 'pz_caja': 1, 'label': 'm² / pz'}
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

def safe_filename(name):
    return name.lower().replace(' ', '-').replace('_', '-').replace('ñ','n').replace('ó','o').replace('á','a').replace('é','e').replace('í','i').replace('ú','u').replace('(', '').replace(')', '').replace('.', '')[:40] + '.html'

categories = []
for folder in CATEGORY_ORDER:
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files.sort()
    config = CATEGORY_CONFIG.get(folder, {'title': folder, 'specs': [], 'desc': '', 'calc': None})
    categories.append({
        'folder': folder,
        'filename': safe_filename(folder),
        'title': config['title'],
        'specs': config['specs'],
        'desc': config['desc'],
        'calc': config['calc'],
        'products': files
    })

META_DESC = "Catálogo oficial de ADIS Diseño & Remodelación. Recubrimientos de alta gama: mármol digital, WPC, PVC, paneles 3D, metálicos y reflections. Nogales, Sonora."
META_KEYWORDS = "ADIS, diseño, remodelación, paneles, WPC, PVC, mármol digital, 3D, recubrimientos, Nogales, Sonora"

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

/* FONDO ANIMADO COBERTURA TOTAL */
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

/* HERO HOME - CENTRADO VERTICAL */
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

/* INFO CARDS - TRANSPARENTES CON BLUR */
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

/* CATEGORY GRID HOME - TARJETAS TRANSPARENTES */
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

/* FICHA TÉCNICA */
.ficha-section {
  padding: 3rem 2rem;
  position: relative; z-index: 1;
  background: rgba(15,15,15,0.6);
  backdrop-filter: blur(6px);
  border-top: 1px solid rgba(197,160,89,0.1);
  border-bottom: 1px solid rgba(197,160,89,0.1);
}
.ficha-table {
  width: 100%; max-width: 800px; margin: 0 auto;
  border-collapse: collapse; font-size: 0.9rem;
  background: rgba(42,42,42,0.6);
  backdrop-filter: blur(8px);
}
.ficha-table th {
  background: var(--gold); color: var(--black);
  padding: 1rem; text-align: left;
  text-transform: uppercase; letter-spacing: 1px; font-weight: 700;
}
.ficha-table td {
  padding: 0.9rem 1rem; color: rgba(245,245,245,0.85);
  border-bottom: 1px solid rgba(197,160,89,0.08);
}
.ficha-table tr:nth-child(even) td {
  background: rgba(255,255,255,0.03);
}
.ficha-table td:first-child {
  font-weight: 600; color: var(--white); width: 35%;
}
.ficha-desc {
  max-width: 800px; margin: 0 auto 2rem;
  color: rgba(245,245,245,0.75); font-size: 1rem;
  line-height: 1.7; text-align: center;
}

/* CALCULADORA */
.calc-box {
  max-width: 500px; margin: 2rem auto 0;
  background: rgba(42,42,42,0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(197,160,89,0.2);
  padding: 2rem; border-radius: 10px;
}
.calc-box h3 {
  font-family: 'Playfair Display', serif; color: var(--gold);
  font-size: 1.2rem; margin-bottom: 1.2rem; text-align: center;
}
.calc-row {
  display: flex; gap: 1rem; margin-bottom: 1rem;
  align-items: center;
}
.calc-row label {
  font-size: 0.85rem; color: rgba(245,245,245,0.8); white-space: nowrap;
}
.calc-row input {
  flex: 1; padding: 0.6rem; background: rgba(15,15,15,0.6);
  border: 1px solid rgba(197,160,89,0.3); color: var(--white);
  font-family: 'Montserrat', sans-serif; font-size: 0.95rem;
  border-radius: 4px;
}
.calc-row input:focus {
  outline: none; border-color: var(--gold);
}
.calc-result {
  text-align: center; padding-top: 0.5rem;
  font-size: 0.9rem; color: var(--light);
}
.calc-result strong {
  color: var(--gold); font-size: 1.1rem;
}

/* PRODUCTOS GRID */
.products-section {
  padding: 4rem 2rem;
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
.product-name {
  padding: 1.2rem;
  text-align: center;
  font-family: 'Playfair Display', serif;
  font-size: 1.2rem; color: var(--gold);
  border-top: 1px solid rgba(197,160,89,0.1);
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
  .ficha-table { font-size: 0.8rem; }
  .calc-row { flex-direction: column; align-items: stretch; }
  .whatsapp-float { width: 50px; height: 50px; font-size: 1.5rem; }
}
'''

with open(os.path.join(base_dir, 'style.css'), 'w', encoding='utf-8') as f:
    f.write(CSS.strip())

# ========== INDEX (HOME) ==========
home_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADIS | Diseño & Remodelación</title>
  <meta name="description" content="{META_DESC}">
  <meta name="keywords" content="{META_KEYWORDS}">
  <meta property="og:title" content="ADIS | Diseño & Remodelación">
  <meta property="og:description" content="{META_DESC}">
  <meta property="og:image" content="https://anibru300.github.io/catalogo-adis/LOGO%20ADIS.png">
  <meta property="og:url" content="https://anibru300.github.io/catalogo-adis/">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="bg-canvas"></canvas>

  <header>
    <div class="header-inner">
      <a href="index.html" class="logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></a>
      <nav class="desktop-nav">
        <a href="index.html">Inicio</a>
        <a href="#nosotros">Nosotros</a>
        <a href="#categorias">Catálogo</a>
        <a href="contacto.html">Contacto</a>
      </nav>
      <button class="menu-btn" onclick="toggleMenu()">☰</button>
    </div>
  </header>

  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">✕</button>
    <a href="index.html" onclick="toggleMenu()">Inicio</a>
    <a href="#nosotros" onclick="toggleMenu()">Nosotros</a>
    <a href="#categorias" onclick="toggleMenu()">Catálogo</a>
    <a href="contacto.html" onclick="toggleMenu()">Contacto</a>
  </div>

  <!-- INICIO -->
  <section class="hero-home" id="inicio">
    <div class="hero-content">
      <img src="LOGO ADIS.png" alt="ADIS Logo">
      <div class="hero-badge">Catálogo 2025 — 2026</div>
      <h1>Transforma tus espacios con <em>ADIS</em></h1>
      <p>Recubrimientos de alta gama para interior y exterior. Mármol digital, WPC, PVC, 3D, metálicos y reflections.</p>
      <a href="#categorias" class="btn-primary">Explorar Catálogo</a>
    </div>
  </section>

  <!-- NOSOTROS -->
  <section class="section-wrap-alt" id="nosotros">
    <div class="section-header">
      <h2>Sobre ADIS</h2>
      <div class="divider"></div>
      <p>En ADI'S DISEÑO & REMODELACIÓN nos especializamos en ofrecer soluciones funcionales, estéticas y duraderas.</p>
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
        <p>Acabados metálicos autoadheribles y placas tipo espejo para un toque de lujo.</p>
      </div>
    </div>
  </section>

  <!-- CATÁLOGO -->
  <section class="section-wrap" id="categorias">
    <div class="section-header">
      <h2>Nuestro Catálogo</h2>
      <div class="divider"></div>
      <p>Selecciona una categoría para ver los productos con su ficha técnica.</p>
    </div>
    <div class="cat-grid">
'''
for cat in categories:
    thumb = f"{cat['folder']}/{cat['products'][0]}" if cat['products'] else ''
    home_html += f'''      <a href="{cat['filename']}" class="cat-card">
        <img src="{thumb}" alt="{cat['title']}">
        <div class="cat-card-overlay">
          <h3>{cat['title']}</h3>
          <span>{len(cat['products'])} productos</span>
        </div>
      </a>
'''
home_html += '''    </div>
  </section>

  <footer id="contacto">
    <div class="footer-logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></div>
    <div class="footer-info">
      <strong>ADI'S DISEÑO & REMODELACIÓN</strong><br>
      Creando espacios, reinventando hogares.<br>
      Nogales, Sonora · Rio Rico, AZ<br>
      Tel. MX: +52 631-192-8993 · Tel. USA: +1 (520) 839-2877<br>
      adis.remodelacion@gmail.com
    </div>
    <div class="copyright">© 2026 ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.</div>
  </footer>

  <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20vi%20el%20catálogo%20y%20me%20interesa..." class="whatsapp-float" target="_blank" title="Contáctanos por WhatsApp">💬</a>

  <script>function toggleMenu(){{document.getElementById('mobileMenu').classList.toggle('active');}}</script>
  <script>''' + PARTICLES_JS + '''</script>
</body>
</html>
'''
with open(os.path.join(base_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(home_html)

# ========== CONTACTO ==========
contact_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contacto | ADIS Diseño & Remodelación</title>
  <meta name="description" content="Contacta a ADIS Diseño & Remodelación. WhatsApp, teléfono MX, teléfono USA y correo electrónico.">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="bg-canvas"></canvas>
  <header>
    <div class="header-inner">
      <a href="index.html" class="logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></a>
      <nav class="desktop-nav">
        <a href="index.html">Inicio</a>
        <a href="index.html#categorias">Catálogo</a>
        <a href="contacto.html">Contacto</a>
      </nav>
      <button class="menu-btn" onclick="toggleMenu()">☰</button>
    </div>
  </header>
  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">✕</button>
    <a href="index.html" onclick="toggleMenu()">Inicio</a>
    <a href="index.html#categorias" onclick="toggleMenu()">Catálogo</a>
    <a href="contacto.html" onclick="toggleMenu()">Contacto</a>
  </div>

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
        <a href="https://wa.me/526311928993" target="_blank">+52 631-192-8993</a>
      </div>
      <div class="contact-card">
        <div class="icon">📞</div>
        <h3>Teléfono USA</h3>
        <a href="tel:+15208392877">+1 (520) 839-2877</a>
      </div>
      <div class="contact-card">
        <div class="icon">✉️</div>
        <h3>Correo</h3>
        <a href="mailto:adis.remodelacion@gmail.com">adis.remodelacion@gmail.com</a>
      </div>
      <div class="contact-card">
        <div class="icon">📍</div>
        <h3>Ubicación</h3>
        <p>Nogales, Sonora<br>Rio Rico, AZ</p>
      </div>
    </div>
    <div style="text-align: center; margin-top: 3rem;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
    </div>
  </section>

  <footer>
    <div class="footer-logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></div>
    <div class="footer-info">
      <strong>ADI'S DISEÑO & REMODELACIÓN</strong><br>
      Creando espacios, reinventando hogares.<br>
      Nogales, Sonora · Rio Rico, AZ<br>
      Tel. MX: +52 631-192-8993 · Tel. USA: +1 (520) 839-2877<br>
      adis.remodelacion@gmail.com
    </div>
    <div class="copyright">© 2026 ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.</div>
  </footer>

  <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20vi%20el%20catálogo%20y%20me%20interesa..." class="whatsapp-float" target="_blank" title="Contáctanos por WhatsApp">💬</a>

  <script>function toggleMenu(){{document.getElementById('mobileMenu').classList.toggle('active');}}</script>
  <script>''' + PARTICLES_JS + '''</script>
</body>
</html>
'''
with open(os.path.join(base_dir, 'contacto.html'), 'w', encoding='utf-8') as f:
    f.write(contact_html)

# ========== PÁGINAS DE CATEGORÍAS ==========
for cat in categories:
    calc_html = ''
    if cat['calc']:
        area = cat['calc']['area_pz']
        pz_caja = cat['calc']['pz_caja']
        label = cat['calc']['label']
        calc_html = f'''
    <div class="calc-box">
      <h3>📐 Calculadora de Materiales</h3>
      <div class="calc-row">
        <label>Metros cuadrados:</label>
        <input type="number" id="m2" placeholder="Ej: 10" min="0" step="0.1" oninput="calcular()">
      </div>
      <div class="calc-result" id="resultado">Ingresa los m² para calcular</div>
    </div>
    <script>
      function calcular(){{
        var m2 = parseFloat(document.getElementById('m2').value);
        if (!m2 || m2 <= 0){{ document.getElementById('resultado').innerHTML = 'Ingresa los m² para calcular'; return; }}
        var pz = Math.ceil(m2 / {area});
        var cajas = Math.ceil(pz / {pz_caja});
        document.getElementById('resultado').innerHTML = 'Necesitas <strong>' + pz + ' piezas</strong> (' + cajas + ' caja' + (cajas>1?'s':'') + ')<br><span style="font-size:0.75rem;color:rgba(245,245,245,0.5)">Basado en {label}</span>';
      }}
    </script>
'''
    else:
        calc_html = '''
    <div class="calc-box">
      <h3>📐 Calculadora de Materiales</h3>
      <div class="calc-result">Consulta la ficha técnica o contáctanos para calcular los materiales necesarios.</div>
    </div>
'''

    cat_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{cat['title']} | ADIS Catálogo</title>
  <meta name="description" content="{cat['title']} - ADIS Diseño & Remodelación. {cat['desc']}">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <canvas id="bg-canvas"></canvas>
  <header>
    <div class="header-inner">
      <a href="index.html" class="logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></a>
      <nav class="desktop-nav">
        <a href="index.html">← Inicio</a>
        <a href="index.html#categorias">Catálogo</a>
        <a href="contacto.html">Contacto</a>
      </nav>
      <button class="menu-btn" onclick="toggleMenu()">☰</button>
    </div>
  </header>
  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">✕</button>
    <a href="index.html" onclick="toggleMenu()">← Inicio</a>
    <a href="index.html#categorias" onclick="toggleMenu()">Catálogo</a>
    <a href="contacto.html" onclick="toggleMenu()">Contacto</a>
  </div>

  <section class="hero-cat">
    <h1>{cat['title']}</h1>
    <p>{cat['desc']}</p>
  </section>

  <section class="ficha-section">
    <div class="section-header">
      <h2>Ficha Técnica</h2>
      <div class="divider"></div>
    </div>
    <p class="ficha-desc">{cat['desc']}</p>
    <table class="ficha-table">
      <thead><tr><th>Especificación</th><th>Detalle</th></tr></thead>
      <tbody>
'''
    for spec in cat['specs']:
        cat_html += f'''        <tr><td>{spec[0]}</td><td>{spec[1]}</td></tr>
'''
    cat_html += f'''      </tbody>
    </table>
    {calc_html}
  </section>

  <section class="products-section">
    <div class="section-header">
      <h2>Productos</h2>
      <div class="divider"></div>
    </div>
    <div class="products-grid">
'''
    for prod_file in cat['products']:
        prod_name = os.path.splitext(prod_file)[0]
        img_path = f"{cat['folder']}/{prod_file}"
        cat_html += f'''      <div class="product-card">
        <div class="product-gallery">
          <img src="{img_path}" alt="{prod_name}" loading="lazy">
        </div>
        <div class="product-name">{prod_name}</div>
      </div>
'''
    cat_html += f'''    </div>
    <div style="text-align: center; margin-top: 3rem;">
      <a href="index.html" class="btn-back">← Volver al Inicio</a>
      <a href="catalogo_adis.pdf" class="btn-outline" target="_blank">📄 Descargar PDF</a>
    </div>
  </section>

  <footer>
    <div class="footer-logo"><img src="LOGO ADIS.png" alt="ADIS Logo"></div>
    <div class="footer-info">
      <strong>ADI'S DISEÑO & REMODELACIÓN</strong><br>
      Creando espacios, reinventando hogares.<br>
      Nogales, Sonora · Rio Rico, AZ<br>
      Tel. MX: +52 631-192-8993 · Tel. USA: +1 (520) 839-2877<br>
      adis.remodelacion@gmail.com
    </div>
    <div class="copyright">© 2026 ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.</div>
  </footer>

  <a href="https://wa.me/526311928993?text=Hola%20ADIS,%20vi%20el%20catálogo%20y%20me%20interesa..." class="whatsapp-float" target="_blank" title="Contáctanos por WhatsApp">💬</a>

  <script>function toggleMenu(){{document.getElementById('mobileMenu').classList.toggle('active');}}</script>
  <script>''' + PARTICLES_JS + '''</script>
</body>
</html>
'''
    with open(os.path.join(base_dir, cat['filename']), 'w', encoding='utf-8') as f:
        f.write(cat_html)

print("Sitio completo generado exitosamente.")
