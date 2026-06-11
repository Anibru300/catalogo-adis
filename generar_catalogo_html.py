# -*- coding: utf-8 -*-
import os, re
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright

BASE_DIR    = Path(r'G:\Mi unidad\ADIS DISEÑO\Pagina')
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')
MEDIA_DIR   = BASE_DIR / 'media'
LOGO_PATH   = BASE_DIR / 'logo nuevo.jpeg'
QR_PATH     = BASE_DIR / 'codigo QR.jpeg'
OUTPUT_HTML = BASE_DIR / 'catalogo_premium.html'
OUTPUT_PDF  = BASE_DIR / 'catalogo.pdf'

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
    return ' '.join(result)

def file_url(p):
    # Convierte Path de Windows a URL file:///
    s = str(p).replace('\\', '/')
    # Windows path G:/folder -> file:///G:/folder
    if len(s) >= 2 and s[1] == ':':
        s = '/' + s[0] + ':' + s[2:]
    return 'file://' + quote(s, safe='/:#')

def scan_catalog():
    cats = []
    exts = ('.jpg','.jpeg','.png')
    for folder in sorted(os.listdir(CATALOG_DIR)):
        p = CATALOG_DIR / folder
        if not p.is_dir(): continue
        name = clean_folder(folder)
        subs = []
        direct = []
        for item in sorted(os.listdir(p)):
            ip = p / item
            if ip.is_dir():
                prods = [f for f in sorted(os.listdir(ip)) if f.lower().endswith(exts) and 'ficha' not in f.lower()]
                if prods:
                    subs.append({'name': clean_folder(item), 'products': prods, 'path': ip})
            elif item.lower().endswith(exts) and 'ficha' not in item.lower():
                direct.append(item)
        if direct:
            subs.append({'name': name, 'products': sorted(direct), 'path': p})
        cats.append({'name': name, 'subs': subs})
    return cats

SPECS = {
    'Placas PVC': {'Material':'PVC','Dimensiones':'2440×1220mm','Presentación':'2.98m²/pz','Garantía':'15 años','Uso':'Interior'},
    'Lambrin WPC': {'Material':'WPC','Dimensiones':'2900×160mm','Presentación':'Consultar','Garantía':'15 años','Uso':'Int/Ext'},
    'Revestimiento Flexible': {'Material':'Flexible','Dimensiones':'900×600mm','Presentación':'0.54m²/pz','Garantía':'35 años','Uso':'Int/Ext'},
    'Plafon PVC': {'Material':'PVC','Dimensiones':'2900×250mm','Presentación':'Consultar','Garantía':'15 años','Uso':'Interior'},
    'Paneles tridimensionales': {'Material':'PVC/Compuesto','Dimensiones':'500×500mm','Presentación':'0.25m²/pz','Garantía':'1 año','Uso':'Res/Com'},
    'Vigas PVC': {'Material':'WPC/PVC','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'15 años','Uso':'Int/Ext'},
    'Pisos': {'Material':'Varios','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'10-25 años','Uso':'Res/Com'},
    'Zacate': {'Material':'Polietileno','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'5-12 años','Uso':'Int/Ext'},
    'Cladding': {'Material':'PU/Poliuretano','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'Consultar','Uso':'Int/Ext'},
}

BENEFITS = {
    'Placas PVC': [('Impermeable','Ideal cocinas y baños'),('Antibacteriano','Higiénico, fácil limpieza'),('Resistente','No se deforma'),('Duradero','15+ años')],
    'Lambrin WPC': [('Natural','Textura real de madera'),('Indestructible','No se pudre'),('Sin mantenimiento','Sin barniz'),('Ecológico','Madera reciclada')],
    'Revestimiento Flexible': [('Flexible','Cualquier superficie'),('35 años','Garantía máxima'),('Int/Ext','Versátil'),('Ligero','No sobrecarga')],
    'Plafon PVC': [('Impermeable','Humedad cero'),('Fácil limpieza','Mantenimiento mínimo'),('Decorativo','Múltiples acabados'),('Duradero','15 años')],
    'Paneles tridimensionales': [('Impacto visual','Diseño arquitectónico'),('Fácil','Instalación sencilla'),('Pintable','Personalizable'),('Acústico','Insonorización')],
    'Vigas PVC': [('Realista','Imita madera'),('Impermeable','Resiste humedad'),('Ligero','Fácil instalar'),('Int/Ext','Ambos ambientes')],
    'Pisos': [('Variedad','Múltiples materiales'),('Resistente','Alto tráfico'),('Fácil','Instalación rápida'),('Garantía','Hasta 25 años')],
    'Zacate': [('Siempre verde','Sin riego'),('Anti-UV','No se decolora'),('Drenaje','No encharca'),('Pet friendly','Seguro')],
    'Cladding': [('Piedra real','Natural'),('Ligero','Fácil instalar'),('Versátil','Int/Ext'),('Térmico','Aislante')],
}

SABIAS_QUE = [
    {'icono':'💧','texto':'Los pisos SPC son 100% resistentes al agua, ideales para cocinas y baños.'},
    {'icono':'🌲','texto':'El WPC combina fibras de madera y polímeros para ofrecer la belleza natural de la madera sin mantenimiento.'},
    {'icono':'🪨','texto':'Los revestimientos flexibles se adaptan a superficies curvas sin perder su apariencia de piedra natural.'},
    {'icono':'🧼','texto':'Las placas PVC previenen la acumulación de humedad y son extremadamente fáciles de limpiar.'},
    {'icono':'☀️','texto':'El pasto sintético premium incorpora protección UV para conservar su color durante años.'},
    {'icono':'🏠','texto':'El cladding mejora la estética de fachadas y protege los muros exteriores del clima.'},
    {'icono':'🔇','texto':'Los paneles 3D no solo decoran: también mejoran la insonorización de tus espacios.'},
]

AMBIENT = {
    'Placas PVC': MEDIA_DIR/'pvc-real-01.jpeg',
    'Lambrin WPC': MEDIA_DIR/'proyecto-02.jpeg',
    'Revestimiento Flexible': MEDIA_DIR/'proyecto-07.jpeg',
    'Plafon PVC': MEDIA_DIR/'pvc-real-04.jpeg',
    'Paneles tridimensionales': MEDIA_DIR/'proyecto-01.jpeg',
    'Vigas PVC': MEDIA_DIR/'proyecto-06.jpeg',
    'Pisos': MEDIA_DIR/'pvc-real-01.jpeg',
    'Zacate': MEDIA_DIR/'proyecto-recepcion.jpg',
    'Cladding': MEDIA_DIR/'ejemplo-tapiz.jpg',
}

def get_ambient(cat_name):
    return AMBIENT.get(cat_name)

def get_spec(cat_name):
    return SPECS.get(cat_name, {'Material':'Consultar','Dimensiones':'Consultar','Presentación':'Consultar','Garantía':'Consultar','Uso':'Consultar'})

def get_benefits(cat_name):
    return BENEFITS.get(cat_name, [('Calidad','Premium'),('Duradero','Larga vida'),('Fácil','Instalación sencilla'),('Elegante','Diseño moderno')])

def get_sku(cat_name, prod_file, idx):
    cc = re.sub(r'[^a-zA-Z]', '', cat_name)[:3].upper()
    ps = re.sub(r'[^a-zA-Z0-9]', '', clean_product(prod_file))[:5].upper()
    return f"{cc}-{ps}-{idx:02d}"

# ========== GENERAR HTML ==========
def build_html(cats):
    total_prods = sum(sum(len(s['products']) for s in c['subs']) for c in cats)
    logo_url = file_url(LOGO_PATH)
    qr_url = file_url(QR_PATH)
    
    # Portada fondo
    bg_portada = MEDIA_DIR / 'proyecto-recepcion.jpg'
    if not bg_portada.exists(): bg_portada = MEDIA_DIR / 'despues.jpg'
    bg_url = file_url(bg_portada) if bg_portada.exists() else ''
    
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap');
        @page { size: A4 portrait; margin: 0; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { font-family: 'Montserrat', sans-serif; background: #080808; color: #F0F0F0; font-size: 10pt; }
        .page { width: 210mm; min-height: 297mm; padding: 14mm 18mm; position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; }
        .page:last-child { page-break-after: auto; }
        
        /* Tipografía */
        h1 { font-family: 'Playfair Display', serif; font-size: 32pt; font-weight: 700; color: #F0F0F0; line-height: 1.1; }
        h2 { font-family: 'Playfair Display', serif; font-size: 22pt; font-weight: 700; color: #C9A84C; line-height: 1.2; }
        h3 { font-size: 11pt; font-weight: 700; color: #F0F0F0; text-transform: uppercase; letter-spacing: 1px; }
        .muted { color: #888; font-size: 9pt; }
        .gold { color: #C9A84C; }
        
        /* Header/Footer */
        .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #2A2A2A; padding-bottom: 6px; margin-bottom: 10px; }
        .header img { height: 22px; }
        .header span { font-size: 8pt; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .footer { margin-top: auto; border-top: 1px solid #2A2A2A; padding-top: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 7.5pt; color: #777; }
        .back-btn { position: absolute; top: 14mm; right: 18mm; background: #1A1A1A; border: 1px solid #555; color: #C9A84C; padding: 3px 10px; border-radius: 3px; font-size: 7.5pt; font-weight: 700; text-decoration: none; }
        
        /* Portada */
        .cover { background-size: cover; background-position: center; position: relative; justify-content: center; align-items: center; text-align: center; padding: 0; }
        .cover-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.80); }
        .cover-frame { position: absolute; inset: 12mm; border: 1.5px solid #C9A84C; border-radius: 10px; pointer-events: none; }
        .cover-frame2 { position: absolute; inset: 15mm; border: 0.5px solid #8A7340; border-radius: 8px; pointer-events: none; }
        .cover-content { position: relative; z-index: 2; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20mm; }
        .cover-content img { max-width: 110mm; max-height: 85mm; object-fit: contain; margin-bottom: 15mm; }
        .cover-content h1 { font-family: 'Montserrat', sans-serif; font-size: 28pt; font-weight: 800; letter-spacing: 2px; margin-bottom: 4mm; }
        .cover-content .sub { font-size: 11pt; color: #E5C97A; margin-bottom: 6mm; }
        .cover-content .line { width: 50mm; height: 1px; background: #C9A84C; margin-bottom: 6mm; }
        .cover-content .year { font-size: 9pt; color: #888; }
        
        /* Índice */
        .index-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 8mm; }
        .index-card { background: #121212; border: 1px solid #222; border-radius: 6px; overflow: hidden; display: flex; flex-direction: column; transition: border-color 0.2s; text-decoration: none; color: inherit; page-break-inside: avoid; }
        .index-card:hover { border-color: #C9A84C; }
        .index-card.destacado { border: 2px solid #C9A84C; }
        .index-card img { width: 100%; height: 38mm; object-fit: cover; }
        .index-card-body { padding: 8px; flex: 1; display: flex; flex-direction: column; }
        .index-card-body h4 { font-size: 9.5pt; font-weight: 700; color: #F0F0F0; text-transform: uppercase; margin-bottom: 2px; }
        .index-card-body .count { font-size: 8pt; color: #C9A84C; font-weight: 700; margin-bottom: 3px; }
        .index-card-body p { font-size: 7.5pt; color: #888; line-height: 1.3; margin-bottom: 4px; flex: 1; }
        .index-card-body .cta { font-size: 7.5pt; color: #8A7340; font-weight: 700; text-align: center; }
        .index-card .badge { background: #C9A84C; color: #080808; font-size: 6.5pt; font-weight: 800; text-align: center; padding: 2px; text-transform: uppercase; }
        
        /* Categoría intro */
        .cat-intro { display: flex; flex-direction: column; gap: 8px; }
        .cat-header { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #C9A84C; padding-bottom: 4px; margin-bottom: 2px; }
        .cat-header h1 { font-size: 26pt; }
        .cat-header .count { font-size: 10pt; color: #C9A84C; font-weight: 700; }
        .cat-desc { font-size: 9.5pt; color: #CCC; line-height: 1.4; max-width: 85%; }
        .cat-img { width: 100%; height: 52mm; object-fit: cover; border-radius: 4px; margin: 4px 0; }
        .specs-box { background: #121212; border-radius: 4px; padding: 6px 10px; display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 8pt; color: #BBB; }
        .specs-box span strong { color: #C9A84C; }
        .benefits { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 4px; }
        .benefit { background: #181818; border-radius: 4px; padding: 5px 8px; border-left: 2px solid #C9A84C; }
        .benefit b { color: #C9A84C; font-size: 8pt; display: block; margin-bottom: 1px; }
        .benefit span { color: #888; font-size: 7.5pt; }
        .banner-sq { background: #121212; border: 1px solid #333; border-radius: 4px; padding: 6px 10px; margin-top: 6px; display: flex; align-items: center; gap: 8px; font-size: 8pt; color: #BBB; }
        .banner-sq .icon { font-size: 14pt; }
        .banner-sq b { color: #C9A84C; margin-right: 4px; }
        
        /* Productos grid */
        .prod-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; flex: 1; }
        .prod-card { background: #181818; border: 1px solid #222; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; page-break-inside: avoid; }
        .prod-card .img-wrap { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; padding: 6px; }
        .prod-card img { max-width: 100%; max-height: 100%; object-fit: contain; }
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
        .final img.logo { max-width: 60mm; margin-bottom: 10mm; }
        .final h2 { margin-bottom: 4mm; }
        .final .contact-box { background: #121212; border: 1px solid #222; border-radius: 6px; padding: 10px 20px; margin: 8mm 0; max-width: 130mm; }
        .final .contact-box p { font-size: 9pt; color: #CCC; margin: 3px 0; }
        .final .qr-wrap { background: #fff; padding: 8px; border-radius: 6px; display: inline-block; margin-top: 6mm; }
        .final .qr-wrap img { width: 35mm; height: 35mm; display: block; }
        .final .qr-label { font-size: 8pt; color: #C9A84C; margin-top: 3mm; font-weight: 700; }
    </style>
    """
    
    body_parts = []
    
    # ===== PORTADA =====
    body_parts.append(f'''<div class="page cover" style="background-image:url('{bg_url}');">
        <div class="cover-overlay"></div>
        <div class="cover-frame"></div>
        <div class="cover-frame2"></div>
        <div class="cover-content">
            <img src="{logo_url}" alt="ADIS">
            <div class="sub">Materiales premium para arquitectura e interiorismo</div>
            <div class="line"></div>
            <div class="year">CATÁLOGO 2025 &nbsp;|&nbsp; ADIS DISEÑO & REMODELACIÓN<br>Nogales, Sonora &nbsp;|&nbsp; Río Rico, AZ</div>
        </div>
    </div>''')
    
    # ===== ÍNDICE =====
    idx_html = ['<div class="page" id="indice">']
    idx_html.append('<div style="text-align:center; margin-bottom:8px;"><h2 style="font-size:26pt;">ÍNDICE</h2><div style="width:30mm;height:1px;background:#C9A84C;margin:4px auto 0;"></div><p class="muted" style="margin-top:4px;">Selecciona una categoría para navegar</p></div>')
    idx_html.append('<div class="index-grid">')
    for i, cat in enumerate(cats):
        n = sum(len(s['products']) for s in cat['subs'])
        desc = cat['name']
        amb = get_ambient(cat['name'])
        img = file_url(amb) if amb and amb.exists() else ''
        destacado = 'destacado' if cat['name'] in ('Placas PVC','Lambrin WPC') else ''
        badge = '<div class="badge">★ Categoría Destacada ★</div>' if cat['name'] in ('Placas PVC','Lambrin WPC') else ''
        idx_html.append(f'''<a href="#cat_{i}" class="index-card {destacado}">
            <img src="{img}" alt="{cat['name']}">
            <div class="index-card-body">
                <h4>{cat['name'].upper()}</h4>
                <div class="count">{n} productos</div>
                <p>{desc}</p>
                <div class="cta">VER CATEGORÍA →</div>
            </div>
            {badge}
        </a>''')
    idx_html.append('</div>')
    idx_html.append('<div class="footer"><span>ADIS Diseño & Remodelación</span><span>Página 2</span><span>adis-diseño.com | +52 631-192-8993</span></div>')
    idx_html.append('</div>')
    body_parts.append('\n'.join(idx_html))
    
    # ===== CATEGORÍAS =====
    global_idx = 0
    for ci, cat in enumerate(cats):
        n_total = sum(len(s['products']) for s in cat['subs'])
        amb = get_ambient(cat['name'])
        amb_img = file_url(amb) if amb and amb.exists() else ''
        spec = get_spec(cat['name'])
        bens = get_benefits(cat['name'])
        sq = SABIAS_QUE[ci % len(SABIAS_QUE)]
        
        # Intro
        intro_html = [f'<div class="page cat-intro" id="cat_{ci}">']
        intro_html.append('<div class="header"><img src="'+logo_url+'" alt="ADIS"><span>'+cat['name'].upper()+'</span><a href="#indice" class="back-btn">← Índice</a></div>')
        intro_html.append(f'<div class="cat-header"><h1>{cat["name"].upper()}</h1><div class="count">{n_total} PRODUCTOS</div></div>')
        intro_html.append(f'<p class="cat-desc">{cat["name"]}. Soluciones decorativas premium de alta calidad.</p>')
        if amb_img:
            intro_html.append(f'<img src="{amb_img}" class="cat-img" alt="{cat["name"]}">')
        spec_html = ' '.join([f'<span><strong>{k}:</strong> {v}</span>' for k,v in spec.items()])
        intro_html.append(f'<div class="specs-box">{spec_html}</div>')
        intro_html.append('<div class="benefits">')
        for btitle, bdesc in bens:
            intro_html.append(f'<div class="benefit"><b>{btitle}</b><span>{bdesc}</span></div>')
        intro_html.append('</div>')
        intro_html.append(f'<div class="banner-sq"><span class="icon">{sq["icono"]}</span><b>¿SABÍAS QUE?</b> {sq["texto"]}</div>')
        intro_html.append('<div class="footer"><span>ADIS Diseño & Remodelación</span><span>Página '+str(len(body_parts)+1)+'</span><span>adis-diseño.com | +52 631-192-8993</span></div>')
        intro_html.append('</div>')
        body_parts.append('\n'.join(intro_html))
        
        # Productos combinados
        all_prods = []
        for sub in cat['subs']:
            for p in sub['products']:
                all_prods.append({'file':p, 'path':sub['path'], 'sub_name':sub['name']})
        
        per_page = 9
        for pi in range(0, len(all_prods), per_page):
            group = all_prods[pi:pi+per_page]
            prod_html = ['<div class="page">']
            prod_html.append('<div class="header"><img src="'+logo_url+'" alt="ADIS"><span>'+cat['name'].upper()+'</span><a href="#indice" class="back-btn">← Índice</a></div>')
            prod_html.append('<div class="prod-grid">')
            for idx, prod in enumerate(group):
                src = prod['path'] / prod['file']
                img = file_url(src)
                name = clean_product(prod['file'])
                sku = get_sku(cat['name'], prod['file'], pi+idx+1)
                sub_label = prod['sub_name'] if len(cat['subs'])>1 else ''
                prod_html.append(f'''<div class="prod-card">
                    <div class="img-wrap"><img src="{img}" alt="{name}"></div>
                    <div class="info">
                        <div class="name" title="{name}">{name}</div>
                        <div class="sku">{sku}</div>
                        {f'<div class="sub">{sub_label}</div>' if sub_label else ''}
                    </div>
                </div>''')
            prod_html.append('</div>')
            prod_html.append('<div class="footer"><span>ADIS Diseño & Remodelación</span><span>Página '+str(len(body_parts)+1)+'</span><span>adis-diseño.com | +52 631-192-8993</span></div>')
            prod_html.append('</div>')
            body_parts.append('\n'.join(prod_html))
        
        global_idx += len(all_prods)
        
        # Comparativa Pisos
        if cat['name'] == 'Pisos':
            comp_html = ['<div class="page">']
            comp_html.append('<div class="header"><img src="'+logo_url+'" alt="ADIS"><span>COMPARATIVA</span><a href="#indice" class="back-btn">← Índice</a></div>')
            comp_html.append('<div style="text-align:center; margin-bottom:8px;"><h2>COMPARATIVA DE PISOS</h2><p class="muted">Encuentra el piso ideal según tus necesidades</p></div>')
            comp_html.append('<table class="comp-table"><thead><tr><th>Característica</th><th>Laminado</th><th>SPC</th><th>WPC</th></tr></thead><tbody>')
            rows = [
                ['Resistencia al agua','Moderada','<span class="ok">✓ 100%</span>','<span class="ok">✓ Impermeable</span>'],
                ['Uso recomendado','Residencial','Res / Comercial','Exterior / Residencial'],
                ['Instalación','Sistema click','Sistema click','Click / Atornillado'],
                ['Resistencia impacto','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span><span class="bar empty"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span>'],
                ['Confort acústico','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span><span class="bar empty"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar"></span>','<span class="bar"></span><span class="bar"></span><span class="bar"></span><span class="bar empty"></span><span class="bar empty"></span>'],
                ['Garantía','10 años','12 años','15 años'],
            ]
            for row in rows:
                comp_html.append('<tr><td style="text-align:left; font-weight:600;">'+row[0]+'</td><td>'+row[1]+'</td><td>'+row[2]+'</td><td>'+row[3]+'</td></tr>')
            comp_html.append('</tbody></table>')
            comp_html.append('<div class="footer"><span>ADIS Diseño & Remodelación</span><span>Página '+str(len(body_parts)+1)+'</span><span>adis-diseño.com | +52 631-192-8993</span></div>')
            comp_html.append('</div>')
            body_parts.append('\n'.join(comp_html))
    
    # ===== FINAL =====
    final_html = ['<div class="page final">']
    final_html.append('<img src="'+logo_url+'" class="logo" alt="ADIS">')
    final_html.append('<h2>Gracias por preferirnos</h2>')
    final_html.append('<p style="color:#BBB; font-size:10pt; margin-bottom:8mm;">Estamos listos para transformar tu espacio</p>')
    final_html.append('<div class="contact-box">')
    final_html.append('<p><strong style="color:#C9A84C;">CONTACTO</strong></p>')
    final_html.append('<p>WhatsApp: +52 631-192-8993</p>')
    final_html.append('<p>Showroom: +52 631-120-4943</p>')
    final_html.append('<p>Email: adis.remodelacion@gmail.com</p>')
    final_html.append('<p>Web: adis-diseño.com</p>')
    final_html.append('<p>Nogales, Sonora | Río Rico, AZ</p>')
    final_html.append('</div>')
    final_html.append(f'<div class="qr-wrap"><img src="{qr_url}" alt="QR"></div>')
    final_html.append('<div class="qr-label">Escanea para visitarnos</div>')
    final_html.append('<div class="footer"><span>ADIS Diseño & Remodelación</span><span>Última página</span><span>adis-diseño.com | +52 631-192-8993</span></div>')
    final_html.append('</div>')
    body_parts.append('\n'.join(final_html))
    
    full_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Catálogo ADIS 2025</title>
{css}
</head>
<body>
{''.join(body_parts)}
</body>
</html>'''
    return full_html

# ========== EJECUTAR ==========
print("Escaneando catálogo...")
cats = scan_catalog()
print(f"Categorías: {len(cats)}")
print(f"Productos: {sum(sum(len(s['products']) for s in c['subs']) for c in cats)}")

print("Generando HTML...")
html = build_html(cats)
with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"HTML guardado: {OUTPUT_HTML}")

print("Convirtiendo a PDF con Playwright...")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(file_url(OUTPUT_HTML))
    page.wait_for_timeout(2000)  # esperar carga de fuentes e imágenes
    page.pdf(
        path=str(OUTPUT_PDF),
        format='A4',
        print_background=True,
        margin={'top':'0','right':'0','bottom':'0','left':'0'}
    )
    browser.close()

print(f"PDF generado: {OUTPUT_PDF}")
import os
sz = os.path.getsize(OUTPUT_PDF)
print(f"Tamaño: {sz/1024/1024:.1f} MB")
