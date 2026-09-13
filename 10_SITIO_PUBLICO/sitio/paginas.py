# -*- coding: utf-8 -*-
"""Paginas: index, categorias, contacto, nosotros, proyectos, sabias-que, privacidad. Extraido de generar_web.py en M3 (salida byte-identica)."""
from . import infra
from .infra import *  # noqa
from .datos import *  # noqa
from .seo import *  # noqa
from .componentes import *  # noqa
from .componentes import _extract_curiosos_cards, _extract_faqs_data, _extract_faqs_html  # guion bajo


def generate_index(categories):
    meta_desc_es = "Recubrimientos en Nogales, Sonora y Arizona: placas PVC, lambrín WPC, paneles 3D, plafón, pisos, zacate y cladding. Cotiza gratis con ADIS Diseño & Remodelación. Enviamos a Nogales, Tucson, Phoenix y Rio Rico."
    meta_desc_en = "Wall coverings in Nogales, Sonora & Arizona: PVC panels, WPC slats, 3D panels, PVC ceilings, flooring, synthetic grass and cladding. Get a free quote from ADIS Design & Remodeling. We ship to Nogales, Tucson, Phoenix and Rio Rico."
    meta_keywords = "recubrimientos Nogales, paneles PVC Sonora, remodelación Nogales Sonora, wall panels Nogales AZ, remodeling materials Arizona, lambrín WPC Nogales, plafón PVC, pisos Nogales, zacate sintético, cladding, ADIS"

    STAR_CATEGORIES = {'Lambrin WPC', 'Placas PVC'}

    # Fotos reales de proyectos para la sección Transformaciones
    trans_imgs = sorted(f.name for f in (OUTPUT_DIR / 'media').glob('proyecto-*.jpeg'))[:8]

    # Conteo real de productos para evitar cifras inconsistentes
    total_products_global = sum(
        len(cat["direct_products"]) + sum(len(sub["products"]) for sub in cat["subcategories"])
        for cat in categories
    )
    
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
            desc_key = ''
            if cat["name"] == 'Lambrin WPC':
                desc_key = 'featured_wpc_desc'
            elif cat["name"] == 'Placas PVC':
                desc_key = 'featured_pvc_desc'
            
            featured_cards += f'''      <a href="{p(cat["filename"])}" class="featured-card reveal">
        {picture_tag(thumb_src, cat_display(cat["name"]))}
        <div class="featured-card-overlay">
          <div class="star-label">&#11088; {i18n('featured_star_label')}</div>
          <h3>{cat_display(cat["name"])}</h3>
          <p>{i18n(desc_key, html=True)}</p>
        </div>
      </a>
'''
        
        if is_star:
            star_badge = f'<div class="star-badge">&#11088; {i18n("featured_star_badge")}</div>'
        elif cat['slug'] == '9-cladding':
            star_badge = f'<div class="star-badge new-badge">&#10024; {i18n("badge_new")}</div>'
        else:
            star_badge = ''
        featured_class = ' featured' if is_star else ''
        
        cat_cards += f'''      <a href="{p(cat["filename"])}" class="cat-card reveal{featured_class}">
        {star_badge}{picture_tag(thumb_src, cat_display(cat["name"]))}
        <div class="cat-card-overlay">
          <div class="cat-arrow">→</div>
          <h3>{cat_display(cat["name"])}</h3>
          <span>{total_prods} {i18n('trust_products')}</span>
        </div>
      </a>
'''

    info_cards = f'''      <a href="{p('1-placas-pvc.html')}" class="info-card">
        <div class="icon">✦</div>
        <h3>{i18n('info_pvc_title')}</h3>
        <p>{i18n('info_pvc_desc', html=True)}</p>
      </a>
      <a href="{p('2-lambrin-wpc.html')}" class="info-card">
        <div class="icon">◈</div>
        <h3>{i18n('info_wpc_title')}</h3>
        <p>{i18n('info_wpc_desc', html=True)}</p>
      </a>
      <a href="{p('7-pisos.html')}" class="info-card">
        <div class="icon">◉</div>
        <h3>{i18n('info_flooring_title')}</h3>
        <p>{i18n('info_flooring_desc', html=True)}</p>
      </a>
      <a href="{p('5-paneles-tridimensionales.html')}" class="info-card">
        <div class="icon">✚</div>
        <h3>{i18n('info_cladding_title')}</h3>
        <p>{i18n('info_cladding_desc', html=True)}</p>
      </a>
'''

    # Iconos representativos por categoría
    CAT_ICONS = {
        'Placas PVC': svg_icon('layers', size=28),
        'Lambrin WPC': svg_icon('tree', size=28),
        'Revestimiento Flexible': svg_icon('square', size=28),
        'Plafon PVC': svg_icon('home', size=28),
        'Paneles tridimensionales': svg_icon('palette', size=28),
        'Vigas PVC': svg_icon('ruler', size=28),
        'Pisos': svg_icon('grid', size=28),
        'Zacate': svg_icon('leaf', size=28),
        'Cladding': svg_icon('mountain', size=28),
    }

    # Tarjetas de descarga por categoría
    downloads_html = ''
    for cat in categories:
        cat_slug_pdf = cat["name"].lower().replace(' ', '-').replace('ñ','n').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        pdf_name = f'catalogo_{cat_slug_pdf}.pdf'
        total_prods = len(cat["direct_products"])
        for sub in cat["subcategories"]:
            total_prods += len(sub["products"])
        icon = CAT_ICONS.get(cat["name"], svg_icon('bookmark', size=28))
        downloads_html += f'''      <a href="{p('catalogos/pdf/' + pdf_name)}" class="download-card" download>
        <span class="icon">{icon}</span>
        <div class="info">
          <h4>{cat["name"]}</h4>
          <span>{total_prods} {i18n('download_products')}</span>
        </div>
        <span class="arrow">⬇</span>
      </a>
'''

    pdf_url = "catalogos/pdf/catalogo_premium.pdf"

    # Videos destacados para home
    media_dir = OUTPUT_DIR / 'media'
    try:
        home_videos = sorted([f for f in os.listdir(media_dir) if f.lower().endswith(('.mp4', '.mov', '.webm'))])[:3]
    except (OSError, PermissionError):
        home_videos = []
    videos_home_html = ''
    if home_videos:
        vcards = ''
        for vid in home_videos:
            name = video_caption(vid)
            mime = video_mime_type(vid)
            stem = Path(vid).stem
            # Buscar poster con el mismo nombre base en media/
            poster_candidates = [f'media/{stem}{ext}' for ext in ['.jpg', '.jpeg', '.png', '.webp']]
            poster_attr = ''
            for cand in poster_candidates:
                if (media_dir / Path(cand).name).exists():
                    poster_attr = f' poster="{cand}"'
                    break
            vcards += f'''      <div class="video-card reveal">
        <video class="auto-video" muted loop playsinline preload="metadata"{poster_attr}>
          <source src="{p('media/' + vid)}" type="{mime}">
        </video>
        <div class="video-card-caption">{name}</div>
      </div>
'''
        videos_home_html = f'''  <!-- VIDEOS DE PROYECTOS -->
  <section class="section-wrap videos-home-section reveal" id="videos">
    <div class="section-header">
      <h2>{i18n('videos_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('videos_subtitle', html=True)}</p>
    </div>
    <div class="video-grid">
{vcards}    </div>
    <div style="text-align: center; margin-top: 2rem;">
      <a href="{p('proyectos.html')}" class="btn-outline">{i18n('videos_more')}</a>
    </div>
  </section>
'''

    html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('title_index')}</title>
  <meta name="description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="{meta_keywords}">
  <meta name="geo.region" content="MX-SON">
  <meta name="geo.placename" content="Heroica Nogales, Sonora, México">
  <meta name="geo.position" content="31.3014;-110.9386">
  <meta name="ICBM" content="31.3014, -110.9386">
  <meta property="og:title" content="{t('title_index')}">
  <meta property="og:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{page_url('index.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t('title_index')}">
  <meta name="twitter:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="twitter:image" content="{SITE_URL}LOGO%20ADIS.png">
  <link rel="canonical" href="{page_url('index.html')}">
  {hreflang_tags('index.html')}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script('index.html')}
{organization_schema()}
{website_schema()}
</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>

{generate_header("index", "index.html")}

  <!-- INICIO -->
  <section class="hero-home" id="inicio">
    <video class="hero-video" autoplay muted loop playsinline preload="metadata" poster="{p('media/despues 2.jpeg')}">
      <source src="{p('media/video-01.mp4')}" type="video/mp4">
    </video>
    <script>if (matchMedia('(prefers-reduced-motion: reduce)').matches) {{ var hv = document.querySelector('.hero-video'); if (hv) {{ hv.removeAttribute('autoplay'); hv.pause(); }} }}</script>
    <div class="hero-content">
      {logo_tag()}
      <div class="hero-badge">{i18n('hero_badge')}</div>
      <h1>{i18n('hero_title', html=True)}</h1>
      <p>{i18n('hero_subtitle', html=True)}</p>
      <div class="hero-actions">
        <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO['whatsapp_msg'].replace(' ', '%20')}" class="btn-primary btn-wa" target="_blank" onclick="gtag('event','whatsapp_click',{{'location':'hero_home'}})">{i18n('cta_quote_whatsapp')}</a>
        <a href="#categorias" class="btn-secondary">{i18n('cta_view_catalog')}</a>
      </div>
      <p class="hero-note">{i18n('hero_note', html=True)}</p>
      <div class="search-hero">
        <div class="search-hero-title" style="display:flex;align-items:center;justify-content:center;gap:0.5rem;">{svg_icon('search', size=24)} {i18n_fmt('search_title', count=total_products_global)}</div>
        <span class="search-hero-icon">{svg_icon('search', size=22, color='var(--gold)')}</span>
        <input type="text" class="search-hero-input" id="searchHeroInput" placeholder="{t('search_placeholder')}" autocomplete="off" onfocus="openSpotlight()">
        <div class="search-hero-hint">{i18n('search_hint')}</div>
      </div>
    </div>
  </section>

  <!-- BENEFICIOS / POR QUÉ ELEGIR ADIS -->
  <section class="section-wrap benefits-section reveal" id="beneficios">
    <div class="section-header">
      <h2>{i18n('benefits_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('benefits_subtitle', html=True)}</p>
    </div>
    <div class="benefits-grid">
      <div class="benefit-card">
        <div class="benefit-icon">{svg_icon('truck', size=40)}</div>
        <h3>{i18n('benefit_shipping_title')}</h3>
        <p>{i18n('benefit_shipping_desc', html=True)}</p>
      </div>
      <div class="benefit-card">
        <div class="benefit-icon">{svg_icon('shield', size=40)}</div>
        <h3>{i18n('benefit_warranty_title')}</h3>
        <p>{i18n('benefit_warranty_desc', html=True)}</p>
      </div>
      <div class="benefit-card">
        <div class="benefit-icon">{svg_icon('hands', size=40)}</div>
        <h3>{i18n('benefit_advice_title')}</h3>
        <p>{i18n('benefit_advice_desc', html=True)}</p>
      </div>
      <div class="benefit-card">
        <div class="benefit-icon">{svg_icon('bolt', size=40)}</div>
        <h3>{i18n('benefit_install_title')}</h3>
        <p>{i18n('benefit_install_desc', html=True)}</p>
      </div>
    </div>
    <div class="trust-banner">
      <div class="trust-item">{svg_icon('layers', size=28)}<div><span>{total_products_global}+</span>{i18n('trust_products')}</div></div>
      <div class="trust-item">{svg_icon('home', size=28)}<div><span>50+</span>{i18n('trust_projects')}</div></div>
      <div class="trust-item">{svg_icon('truck', size=28)}<div>{i18n('benefit_shipping_title')}</div></div>
      <div class="trust-item">{svg_icon('shield', size=28)}<div>{i18n('benefit_warranty_title')}</div></div>
      <div class="trust-item">{svg_icon('bolt', size=28)}<div>{i18n('benefit_install_title')}</div></div>
    </div>
  </section>

  <!-- NOSOTROS -->
  <section class="section-wrap-alt reveal" id="nosotros">
    <div class="section-header">
      <h2>{i18n('about_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('about_subtitle', html=True)}</p>
    </div>
    <div class="info-grid">
{info_cards}    </div>
  </section>

  <!-- STATS -->
  <section class="stats-section reveal">
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-number" data-target="{total_products_global}">0</div>
        <div class="stat-label">{i18n('stat_products')}</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" data-target="9">0</div>
        <div class="stat-label">{i18n('stat_categories')}</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" data-target="50">0</div>
        <div class="stat-label">{i18n('stat_projects_done')}</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" data-target="100">0</div>
        <div class="stat-label">{i18n('stat_happy_clients')}</div>
      </div>
    </div>
  </section>

  <!-- PRODUCTOS ESTRELLA -->
  <section class="featured-section reveal" id="estrellas">
    <div class="section-header">
      <h2>&#11088; {i18n('featured_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('featured_subtitle', html=True)}</p>
    </div>
    <div class="featured-grid">
{featured_cards}    </div>
  </section>

  <!-- PRODUCTO DESTACADO: PVC MARMOL -->
  <section class="featured-product-section reveal" id="pvc-marmol">
    <div class="featured-product-wrap">
      <div class="featured-product-image">
        <span class="featured-product-badge">{i18n('featured_marble_title')}</span>
        {picture_tag('img/1-placas-pvc/Carrara Oscuro.jpg', t('featured_marble_title'))}
      </div>
      <div class="featured-product-content">
        <h3>{i18n('featured_marble_title')}</h3>
        <div class="subtitle">{i18n('featured_marble_subtitle')}</div>
        <p>{i18n('featured_marble_text', html=True)}</p>
        <ul class="featured-product-features">
          <li>{i18n('featured_marble_bullet1', html=True)}</li>
          <li>{i18n('featured_marble_bullet2', html=True)}</li>
          <li>{i18n('featured_marble_bullet3', html=True)}</li>
          <li>{i18n('featured_marble_bullet4', html=True)}</li>
        </ul>
        <a href="{p('1-placas-pvc.html')}" class="featured-product-cta">{i18n('featured_marble_cta')}</a>
      </div>
    </div>
  </section>

{calculator_html(categories)}

{transformations_html(trans_imgs)}

  <!-- SERVICIO EN ARIZONA -->
  <section class="section-wrap arizona-section reveal" id="arizona">
    <div class="section-header">
      <h2>{i18n('arizona_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('arizona_subtitle', html=True)}</p>
    </div>
    <div class="arizonaz-grid">
      <div class="arizona-card"><span>🇺🇸</span><h3>{i18n('arizona_nogales_title')}</h3><p>{i18n('arizona_nogales_desc', html=True)}</p></div>
      <div class="arizona-card"><span>🇺🇸</span><h3>{i18n('arizona_riorico_title')}</h3><p>{i18n('arizona_riorico_desc', html=True)}</p></div>
      <div class="arizona-card"><span>🇺🇸</span><h3>{i18n('arizona_tucson_title')}</h3><p>{i18n('arizona_tucson_desc', html=True)}</p></div>
      <div class="arizona-card"><span>🇺🇸</span><h3>{i18n('arizona_phoenix_title')}</h3><p>{i18n('arizona_phoenix_desc', html=True)}</p></div>
    </div>
    <div style="text-align: center; margin-top: 2rem;">
      <a href="{whatsapp_url(CONTACTO['whatsapp'], 'Hola ADIS, estoy en Arizona y quiero cotizar materiales de remodelacion.')}" class="btn-primary btn-wa" target="_blank" onclick="gtag('event','whatsapp_click',{{'location':'arizona_home'}})">{i18n('arizona_cta')}</a>
    </div>
  </section>

  <!-- CATÁLOGO -->
  <section class="section-wrap reveal" id="categorias">
    <div class="section-header">
      <h2>{i18n('catalog_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('catalog_subtitle', html=True)}</p>
    </div>
    <div class="cat-grid">
{cat_cards}    </div>
  </section>

  <!-- DESCARGAS DE CATÁLOGOS PDF -->
  <section class="section-wrap downloads-section reveal" id="descargas">
    <div class="section-header">
      <h2>{i18n('downloads_title')}</h2>
      <div class="divider"></div>
      <p class="downloads-lead">{i18n('downloads_subtitle', html=True)}</p>
    </div>
    <div class="downloads-main">
      <a href="{p('catalogos/pdf/catalogo_premium.pdf')}" class="download-complete" download>
        <span class="icon">📚</span>
        <div>
          <div>{i18n('download_complete')}</div>
          <span class="sub">{i18n('download_complete_sub')}</span>
        </div>
      </a>
    </div>
    <div class="download-grid">
{downloads_html}    </div>
  </section>

{videos_home_html}

{generate_lead_banner()}

{generate_testimonios()}

{modal_cotizar_html()}

  <script>
    // Autoplay videos en home cuando son visibles
    (function() {{
      const videos = document.querySelectorAll('.auto-video');
      if (!videos.length || !('IntersectionObserver' in window)) return;
      const observer = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
          if (entry.isIntersecting) {{
            entry.target.play();
          }} else {{
            entry.target.pause();
          }}
        }});
      }}, {{ threshold: 0.3 }});
      videos.forEach(v => observer.observe(v));
    }})();
  </script>
{generate_footer()}
</body>
</html>
'''
    with open(out_dir() / 'index.html', 'w', encoding='utf-8') as f:
        f.write(minify_html(html))
    print("✅ index.html generado")




def generate_contacto():
    meta_desc_es = "Cotiza recubrimientos en Nogales, Sonora y Arizona. Contacta a ADIS Diseño & Remodelación por WhatsApp, teléfono o email. Placas PVC, lambrín WPC, paneles 3D, plafón, pisos y más. Enviamos a Tucson, Phoenix y Rio Rico."
    meta_desc_en = "Quote wall coverings in Nogales, Sonora & Arizona. Contact ADIS Design & Remodeling via WhatsApp, phone or email. PVC panels, WPC slats, 3D panels, PVC ceilings, flooring and more. We ship to Tucson, Phoenix and Rio Rico."
    html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('title_contacto')}</title>
  <meta name="description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="cotizar recubrimientos Nogales, contacto ADIS, paneles PVC Sonora, wall panels Nogales AZ, remodeling materials Arizona, WhatsApp ADIS">
  <meta name="geo.region" content="MX-SON">
  <meta name="geo.placename" content="Heroica Nogales, Sonora, México">
  <meta name="geo.position" content="31.3014;-110.9386">
  <meta name="ICBM" content="31.3014, -110.9386">
  <meta property="og:title" content="Cotizar Recubrimientos Nogales Sonora · Arizona | Contacto ADIS">
  <meta property="og:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{page_url('contacto.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Cotizar Recubrimientos Nogales Sonora · Arizona | Contacto ADIS">
  <meta name="twitter:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="twitter:image" content="{SITE_URL}LOGO%20ADIS.png">
  <link rel="canonical" href="{page_url('contacto.html')}">
  {hreflang_tags('contacto.html')}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script('contacto.html')}
{organization_schema()}
{breadcrumb_schema([(t('bc_home'), SITE_URL), (t('nav_contact'), page_url('contacto.html'))])}
</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header("contacto", "contacto.html")}
{breadcrumb_html([(t('bc_home'), p('index.html')), (t('nav_contact'), '')])}

  <section class="hero-cat" style="padding-top: 8rem;">
    <h1>{i18n('contact_title', html=True)}</h1>
    <p>{i18n('contact_subtitle', html=True)}</p>
  </section>

  <section class="section-wrap contact-section">
    <div class="contact-layout">
      <!-- Formulario de cotización -->
      <div class="contact-form-panel reveal">
        <div class="section-header" style="text-align:left; margin-bottom:1.5rem;">
          <h2 style="font-size:1.6rem;">{i18n('contact_form_title')}</h2>
          <div class="divider" style="margin:0.8rem 0;"></div>
          <p style="margin:0;">{i18n('contact_form_subtitle', html=True)}</p>
        </div>
        <form id="contactForm" onsubmit="sendContactForm(event)">
          <div class="form-row">
            <div class="form-field">
              <label for="cfNombre">{i18n('form_name')}</label>
              <input type="text" id="cfNombre" placeholder="{t('form_name_placeholder')}" required>
            </div>
            <div class="form-field">
              <label for="cfTelefono">{i18n('form_phone')}</label>
              <input type="tel" id="cfTelefono" placeholder="{t('form_phone_placeholder')}" required>
            </div>
          </div>
          <div class="form-field">
            <label for="cfEmail">{i18n('form_email')}</label>
            <input type="email" id="cfEmail" placeholder="{t('form_email_placeholder')}">
          </div>
          <div class="form-row">
            <div class="form-field">
              <label for="cfCiudad">{i18n('form_city')}</label>
              <input type="text" id="cfCiudad" placeholder="{t('form_city_placeholder')}" required>
            </div>
            <div class="form-field">
              <label for="cfMetros">{i18n('form_sqm')}</label>
              <input type="number" id="cfMetros" placeholder="{t('form_sqm_placeholder')}" min="1" step="0.1">
            </div>
          </div>
          <div class="form-field">
            <label for="cfProducto">{i18n('form_product')}</label>
            <select id="cfProducto">
              <option value="No estoy seguro">{t('form_product_unsure')}</option>
              <option value="Placas PVC">Placas PVC</option>
              <option value="Lambrín WPC">Lambrín WPC</option>
              <option value="Revestimiento Flexible">Revestimiento Flexible</option>
              <option value="Plafón PVC">Plafón PVC</option>
              <option value="Paneles 3D">Paneles 3D</option>
              <option value="Vigas PVC/WPC/PU">Vigas PVC/WPC/PU</option>
              <option value="Pisos">Pisos</option>
              <option value="Zacate Sintético">Zacate Sintético</option>
              <option value="Cladding">Cladding</option>
            </select>
          </div>
          <div class="form-field">
            <label for="cfMensaje">{i18n('form_message')}</label>
            <textarea id="cfMensaje" rows="3" placeholder="{t('form_message_placeholder')}"></textarea>
          </div>
          <div class="form-field" style="display:none !important;" aria-hidden="true">
            <label for="cfEmpresa">Empresa</label>
            <input type="text" id="cfEmpresa" name="empresa" tabindex="-1" autocomplete="off">
          </div>
          <button type="submit" class="btn-primary btn-wa" style="width:100%; justify-content:center; display:flex; gap:0.5rem;">{i18n('form_submit')}</button>
          <p class="form-note">{i18n('form_note', html=True)}</p>
        </form>
      </div>

      <!-- Datos de contacto -->
      <div class="contact-info-panel reveal">
        <div class="contact-card">
          <div class="icon">{svg_icon('chat', size=32)}</div>
          <h3>{i18n('contact_whatsapp')}</h3>
          <a href="https://wa.me/{CONTACTO["whatsapp"]}" target="_blank">{CONTACTO["tel_usa"]}</a>
          <p class="contact-card-note">{i18n('contact_whatsapp_note', html=True)}</p>
        </div>
        <div class="contact-card">
          <div class="icon">{svg_icon('phone', size=32)}</div>
          <h3>{i18n('contact_phone_mx')}</h3>
          <a href="tel:{CONTACTO['tel_mx_link']}">{CONTACTO["tel_mx"]}</a>
        </div>
        <div class="contact-card">
          <div class="icon">{svg_icon('phone', size=32)}</div>
          <h3>{i18n('contact_phone_us')}</h3>
          <a href="tel:{CONTACTO['tel_usa_link']}">{CONTACTO["tel_usa"]}</a>
        </div>
        <div class="contact-card">
          <div class="icon">{svg_icon('mail', size=32)}</div>
          <h3>{i18n('contact_email')}</h3>
          <a href="mailto:{CONTACTO["email"]}">{CONTACTO["email"]}</a>
        </div>
        <div class="contact-card">
          <div class="icon">{svg_icon('map-pin', size=32)}</div>
          <h3>{i18n('contact_location')}</h3>
          <p>{CONTACTO["ubicacion"]}<br>{CONTACTO["direccion"]}</p>
          <a href="{CONTACTO['maps_url']}" target="_blank" class="btn-outline" style="margin-top:0.8rem; display:inline-block;">{i18n('contact_map')}</a>
        </div>
        <div class="contact-card">
          <div class="icon">{svg_icon('clock', size=32)}</div>
          <h3>{i18n('contact_hours')}</h3>
          <p>{CONTACTO["horarios"]}</p>
        </div>
      </div>
    </div>

    <div style="text-align: center; margin-top: 3rem; max-width: 900px; margin: 3rem auto 0;">
      <div style="border-radius: 8px; overflow: hidden; border: 1px solid rgba(197,160,89,0.2); margin-bottom: 1.5rem;">
        <iframe src="https://maps.google.com/maps?q=31.3088527,-110.9308403&z=17&output=embed" width="100%" height="400" style="border:0;" allowfullscreen="" loading="lazy" title="{t('contact_location')}"></iframe>
      </div>
    </div>
    <div style="text-align: center; margin-top: 2rem;">
      <a href="{p('index.html')}" class="btn-back">{i18n('contact_back_home')}</a>
    </div>
  </section>

  <script>
    function sendContactForm(e) {{
      e.preventDefault();
      var nombre = document.getElementById('cfNombre').value.trim();
      var tel = document.getElementById('cfTelefono').value.trim();
      var email = document.getElementById('cfEmail').value.trim();
      var ciudad = document.getElementById('cfCiudad').value.trim();
      var metros = document.getElementById('cfMetros').value.trim();
      var producto = document.getElementById('cfProducto').value;
      var mensaje = document.getElementById('cfMensaje').value.trim();
      var lines = ['{t("contact_form_message")}'];
      lines.push('{t("contact_form_name")}: ' + nombre);
      lines.push('{t("contact_form_phone")}: ' + tel);
      if (email) lines.push('{t("contact_form_email")}: ' + email);
      lines.push('{t("contact_form_city")}: ' + ciudad);
      if (metros) lines.push('{t("contact_form_sqm")}: ' + metros);
      lines.push('{t("contact_form_product")}: ' + producto);
      if (mensaje) lines.push('{t("contact_form_message_label")}: ' + mensaje);
      lines.push('{t("contact_form_closing")}');
      var url = 'https://wa.me/{CONTACTO["whatsapp"]}?text=' + encodeURIComponent(lines.join('\\n'));
      // Captacion del lead en Google Sheets (no bloquea el envio por WhatsApp)
      try {{
        if (typeof ADIS_LEADS_URL === 'string' && ADIS_LEADS_URL) {{
          var lead = {{ type: 'lead', nombre: nombre, telefono: tel, email: email, ciudad: ciudad,
            metros: metros, producto: producto, mensaje: mensaje,
            pagina: window.location.href,
            idioma: (typeof ADIS_DEFAULT_LANG !== 'undefined' ? ADIS_DEFAULT_LANG : 'es'),
            empresa: document.getElementById('cfEmpresa').value }};
          fetch(ADIS_LEADS_URL, {{ method: 'POST', headers: {{ 'Content-Type': 'text/plain;charset=utf-8' }}, body: JSON.stringify(lead) }}).catch(function() {{}});
        }}
      }} catch (err) {{}}
      if (typeof gtag === 'function') gtag('event', 'enviar_cotizacion', {{ location: 'contacto_form' }});
      if (typeof fbq === 'function') fbq('track', 'Lead');
      window.open(url, '_blank');
    }}
  </script>

{generate_footer()}
</body>
</html>
'''
    with open(out_dir() / 'contacto.html', 'w', encoding='utf-8') as f:
        f.write(minify_html(html))
    print("✅ contacto.html generado")




def generate_nosotros():
    """Genera la pagina Nosotros."""
    meta_desc_es = "Conoce a ADIS Diseño & Remodelación. Somos especialistas en recubrimientos PVC, WPC, paneles 3D, pisos y cladding en Nogales, Sonora y Arizona."
    meta_desc_en = "Meet ADIS Design & Remodeling. Specialists in PVC, WPC, 3D panels, flooring and cladding in Nogales, Sonora & Arizona."
    html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('title_nosotros')}</title>
  <meta name="description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="ADIS Diseño Remodelación, nosotros ADIS, recubrimientos Nogales, paneles PVC Sonora, remodeling Arizona">
  <meta property="og:title" content="{t('title_nosotros')}">
  <meta property="og:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  {og_image_tags(f'{SITE_URL}LOGO%20ADIS.png')}
  <meta property="og:url" content="{page_url('nosotros.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:title" content="{t('title_nosotros')}">
  <meta name="twitter:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <link rel="canonical" href="{page_url('nosotros.html')}">
  {hreflang_tags('nosotros.html')}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script('nosotros.html')}
{organization_schema()}
{breadcrumb_schema([(t('bc_home'), SITE_URL), (t('nav_about'), page_url('nosotros.html'))])}
</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header("nosotros", "nosotros.html")}
{breadcrumb_html([(t('bc_home'), p('index.html')), (t('nav_about'), '')])}

  <section class="about-hero">
    <div class="about-hero-content">
      <div class="hero-badge">{i18n('about_hero_badge')}</div>
      <h1>{i18n('about_title')}</h1>
      <p>{i18n('about_subtitle')}</p>
    </div>
  </section>

  <section class="about-section reveal">
    <div class="section-header">
      <h2>{i18n('about_history_title')}</h2>
      <div class="divider"></div>
    </div>
    <p style="text-align:center; max-width:800px; margin:0 auto 3rem; color:rgba(245,245,245,0.7); line-height:1.8;">{i18n('about_history_text')}</p>
    <div class="about-grid">
      <div class="about-card">
        <div class="icon">{svg_icon('shield', size=32)}</div>
        <h3>{i18n('about_value_quality')}</h3>
        <p>{i18n('about_value_quality_desc')}</p>
      </div>
      <div class="about-card">
        <div class="icon">{svg_icon('hands', size=32)}</div>
        <h3>{i18n('about_value_service')}</h3>
        <p>{i18n('about_value_service_desc')}</p>
      </div>
      <div class="about-card">
        <div class="icon">{svg_icon('truck', size=32)}</div>
        <h3>{i18n('about_value_binational')}</h3>
        <p>{i18n('about_value_binational_desc')}</p>
      </div>
      <div class="about-card">
        <div class="icon">{svg_icon('bolt', size=32)}</div>
        <h3>{i18n('about_value_commitment')}</h3>
        <p>{i18n('about_value_commitment_desc')}</p>
      </div>
    </div>
  </section>

  <section class="section-wrap-alt reveal">
    <div class="about-team">
      <img src="{p('media/equipo-adis.jpg')}" alt="Equipo ADIS">
      <div class="about-team-text">
        <h2>{i18n('about_team_title')}</h2>
        <p>{i18n('about_team_text')}</p>
        <ul class="about-values-list">
          <li>{i18n('about_value_quality')}</li>
          <li>{i18n('about_value_service')}</li>
          <li>{i18n('about_value_binational')}</li>
          <li>{i18n('about_value_commitment')}</li>
        </ul>
        <a href="{p('proyectos.html')}" class="btn-secondary" style="margin-top:1.5rem;">{i18n('about_team_cta')}</a>
      </div>
    </div>
  </section>

  <section class="about-section reveal">
    <div class="section-header">
      <h2>{i18n('about_why_title')}</h2>
      <div class="divider"></div>
    </div>
    <div class="about-grid">
      <div class="about-card">
        <div class="icon">{svg_icon('search', size=32)}</div>
        <h3>{i18n('about_why_1_title')}</h3>
        <p>{i18n('about_why_1_text')}</p>
      </div>
      <div class="about-card">
        <div class="icon">{svg_icon('truck', size=32)}</div>
        <h3>{i18n('about_why_2_title')}</h3>
        <p>{i18n('about_why_2_text')}</p>
      </div>
      <div class="about-card">
        <div class="icon">{svg_icon('layers', size=32)}</div>
        <h3>{i18n('about_why_3_title')}</h3>
        <p>{i18n('about_why_3_text')}</p>
      </div>
      <div class="about-card">
        <div class="icon">{svg_icon('image', size=32)}</div>
        <h3>{i18n('about_why_4_title')}</h3>
        <p>{i18n('about_why_4_text')}</p>
      </div>
    </div>
  </section>

  <section class="section-wrap reveal" style="text-align:center;">
    <h2 style="font-family:'Playfair Display',serif; color:var(--white); font-size:clamp(1.8rem,4vw,2.5rem); margin-bottom:1rem;">{i18n('about_cta_title')}</h2>
    <p style="color:rgba(245,245,245,0.65); margin-bottom:2rem;">{i18n('about_cta_subtitle')}</p>
    <div style="display:flex; gap:1rem; justify-content:center; flex-wrap:wrap;">
      <a href="{whatsapp_url(CONTACTO['whatsapp'], 'Hola ADIS, vi su pagina de Nosotros y quiero cotizar un proyecto.')}" class="btn-primary btn-wa" target="_blank" onclick="gtag('event','whatsapp_click',{{'location':'about_cta'}})">{i18n('cta_quote_whatsapp')}</a>
      <a href="{p('index.html#categorias')}" class="btn-secondary">{i18n('cta_view_catalog')}</a>
    </div>
  </section>

{generate_footer()}
</body>
</html>
'''
    with open(out_dir() / 'nosotros.html', 'w', encoding='utf-8') as f:
        f.write(minify_html(html))
    print("✅ nosotros.html generado")




def generate_privacy():
    """Genera la pagina de Aviso de Privacidad."""
    meta_desc_es = "Aviso de privacidad de ADIS Diseño & Remodelación. Conoce como protegemos tus datos personales."
    meta_desc_en = "Privacy notice of ADIS Design & Remodeling. Learn how we protect your personal data."
    effective_date = datetime.datetime.now().strftime('%d/%m/%Y')
    html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('title_privacidad')}</title>
  <meta name="description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="aviso de privacidad ADIS, proteccion de datos, privacidad Nogales, privacy notice">
  <meta property="og:title" content="{t('title_privacidad')}">
  <meta property="og:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  {og_image_tags(f'{SITE_URL}LOGO%20ADIS.png')}
  <meta property="og:url" content="{page_url('aviso-de-privacidad.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:title" content="{t('title_privacidad')}">
  <meta name="twitter:description" content="{(meta_desc_en if infra.CUR_LANG == 'en' else meta_desc_es)}">
  <link rel="canonical" href="{page_url('aviso-de-privacidad.html')}">
  {hreflang_tags('aviso-de-privacidad.html')}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script('aviso-de-privacidad.html')}
{organization_schema()}
{breadcrumb_schema([(t('bc_home'), SITE_URL), (t('footer_links_privacy'), page_url('aviso-de-privacidad.html'))])}
</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header("privacy", "aviso-de-privacidad.html")}
{breadcrumb_html([(t('bc_home'), p('index.html')), (t('footer_links_privacy'), '')])}

  <section class="hero-cat" style="padding-top: 8rem;">
    <h1>{i18n('privacy_title')}</h1>
    <p>{i18n('privacy_subtitle')}</p>
  </section>

  <section class="privacy-section reveal">
    <div class="privacy-document">
      <h1>{i18n('privacy_title')}</h1>
      <span class="effective">{i18n_fmt('privacy_effective', date=effective_date)}</span>

      <h2>{i18n('privacy_responsible_title')}</h2>
      <p>{i18n('privacy_responsible_text')}</p>

      <h2>{i18n('privacy_data_title')}</h2>
      <p>{i18n('privacy_data_text')}</p>

      <h2>{i18n('privacy_purpose_title')}</h2>
      <p>{i18n('privacy_purpose_text')}</p>

      <h2>{i18n('privacy_arco_title')}</h2>
      <p>{i18n('privacy_arco_text')}</p>

      <h2>{i18n('privacy_security_title')}</h2>
      <p>{i18n('privacy_security_text')}</p>

      <h2>{i18n('privacy_changes_title')}</h2>
      <p>{i18n('privacy_changes_text')}</p>

      <h2>{i18n('privacy_contact_title')}</h2>
      <p>{i18n_fmt('privacy_contact_text', whatsapp=CONTACTO['whatsapp'], email=CONTACTO['email'], ubicacion=CONTACTO['ubicacion'])}</p>
    </div>
  </section>

{generate_footer()}
</body>
</html>
'''
    with open(out_dir() / 'aviso-de-privacidad.html', 'w', encoding='utf-8') as f:
        f.write(minify_html(html))
    print("✅ aviso-de-privacidad.html generado")




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
            nav_parts.append(f'<a href="{p(prev_cat["filename"])}" class="cat-nav-btn">← {cat_display(prev_cat["name"])}</a>')
        if next_cat:
            nav_parts.append(f'<a href="{p(next_cat["filename"])}" class="cat-nav-btn next">{cat_display(next_cat["name"])} →</a>')
        cat_nav_html = '  <div class="cat-nav">\n    ' + '\n    '.join(nav_parts) + '\n  </div>\n'

    # Breadcrumbs
    breadcrumbs_html = f'''  <div class="breadcrumbs">
    <a href="{p('index.html')}">{i18n('breadcrumb_home')}</a> <span>/</span> <a href="{p('index.html#categorias')}">{i18n('breadcrumb_catalog')}</a> <span>/</span> <span style="color:var(--gold);">{cat_display(cat["name"])}</span>
  </div>
'''

    # Seleccionar imagen de fondo representativa para el hero
    hero_bg = ''
    if cat["subcategories"] and cat["subcategories"][0]["products"]:
        hero_bg = f'img/{cat["slug"]}/{cat["subcategories"][0]["slug"]}/{cat["subcategories"][0]["products"][0]}'
    elif cat["direct_products"]:
        hero_bg = f'img/{cat["slug"]}/{cat["direct_products"][0]}'
    hero_bg_quoted = quote(hero_bg, safe='/') if hero_bg else ''

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
            subcat_nav_links += f'<a href="#{sub_slug}">{subcat_display(sub_name)}</a>' + '\n    '
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
      <h3>&#11088; {i18n('cat_best_sellers')}</h3>
      <span class="subcat-count">{len(main_products)} <span data-i18n="filter_count_unit" data-es="productos" data-en="products">productos</span></span>
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
      <h3>{subcat_display(sub["name"])}</h3>
      <span class="subcat-count">{len(sub["products"])} <span data-i18n="filter_count_unit" data-es="productos" data-en="products">productos</span></span>
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
      <h3>{i18n('cat_accessories')}</h3>
      <span class="subcat-count">{acc_count} <span data-i18n="filter_count_unit" data-es="productos" data-en="products">{'productos' if acc_count != 1 else 'producto'}</span></span>
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
      <h3>{i18n_fmt('cat_products', category=cat_display(cat["name"]))}</h3>
      <span class="subcat-count">{len(cat["direct_products"])} <span data-i18n="filter_count_unit" data-es="productos" data-en="products">productos</span></span>
      <div class="subcat-divider"></div>
    </div>
{direct_specs}    <div class="products-grid">
{direct_products_html}    </div>
  </section>
'''

    # Galería de hojas reales (solo para Placas PVC)
    real_sheets_html = ''
    if cat["name"] == 'Placas PVC':
        media_dir = OUTPUT_DIR / 'media'
        try:
            real_imgs = sorted([f for f in os.listdir(media_dir) if f.startswith('pvc-real-') and f.lower().endswith(('.jpg', '.jpeg'))])
        except (OSError, PermissionError):
            real_imgs = []
        if real_imgs:
            gallery_items = ''
            for img in real_imgs:
                gallery_items += f'''      <div class="real-sheets-item" onclick="openLightbox('{p('media/' + img)}', '{t("cat_real_sheets_title")}')">
        {picture_tag(f'media/{img}', t('cat_real_sheets_title'))}
        <span class="real-sheets-badge">{i18n('cat_real_sheets_badge')}</span>
      </div>
'''
            real_sheets_html = f'''  <section class="real-sheets-section">
    <div class="section-header">
      <h2>{i18n('cat_real_sheets_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('cat_real_sheets_subtitle')}</p>
    </div>
    <div class="real-sheets-grid">
{gallery_items}    </div>
  </section>
'''

    if infra.CUR_LANG == 'en':
        wa_hero_url = whatsapp_url(CONTACTO["whatsapp"], "Hello ADIS, I saw the " + cat_display(cat["name"]) + " catalog and I would like advice to choose the best product for my project.")
    else:
        wa_hero_url = whatsapp_url(CONTACTO["whatsapp"], "Hola ADIS, vi el catalogo de " + cat["name"] + " y quiero asesoria para elegir el mejor producto para mi proyecto.")
    cat_slug_pdf = cat["name"].lower().replace(' ', '-').replace('ñ','n').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
    pdf_url = f"catalogos/pdf/catalogo_{cat_slug_pdf}.pdf"

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
        (t('bc_home'), SITE_URL),
        (t('bc_catalog'), f"{SITE_URL}index.html#categorias"),
        (cat_display(cat["name"]), page_url(cat['filename']))
    ])

    # SEO por categoría con foco local Nogales/Sonora
    CAT_SEO = {
        'Placas PVC': {
            'es': ('Placas PVC en Nogales, Sonora | ADIS Catálogo', 'Placas PVC tipo madera, mármol y espejo en Nogales, Sonora. Más de {n} modelos. Cotiza instalación con ADIS Diseño & Remodelación. Enviamos a Sonora y Arizona.'),
            'en': ('PVC Panels in Nogales, Sonora | ADIS Catalog', 'Wood-look, marble and mirror PVC panels in Nogales, Sonora. Over {n} models. Get an installation quote with ADIS Design & Remodeling. We ship to Sonora and Arizona.')},
        'Lambrin WPC': {
            'es': ('Lambrín WPC en Nogales, Sonora | ADIS Catálogo', 'Lambrín WPC interior y exterior en Nogales, Sonora. Acabado de madera real sin mantenimiento. Cotiza con ADIS. Envíos a Sonora y Arizona.'),
            'en': ('WPC Fluted Wall Panels in Nogales, Sonora | ADIS Catalog', 'Interior and exterior WPC fluted wall panels in Nogales, Sonora. Real wood look without maintenance. Quote with ADIS. Shipping to Sonora and Arizona.')},
        'Revestimiento Flexible': {
            'es': ('Revestimiento Flexible en Nogales, Sonora | ADIS', 'Revestimiento flexible tipo concreto, piedra y madera en Nogales, Sonora. Ligero, flexible y fácil de instalar. Cotiza con ADIS.'),
            'en': ('Flexible Stone Veneer in Nogales, Sonora | ADIS', 'Flexible veneer in concrete, stone and wood looks in Nogales, Sonora. Lightweight, flexible and easy to install. Quote with ADIS.')},
        'Plafon PVC': {
            'es': ('Plafón PVC en Nogales, Sonora | ADIS Catálogo', 'Plafón PVC laminado y wood style para techos en Nogales, Sonora. Impermeable y de fácil instalación. Cotiza con ADIS.'),
            'en': ('PVC Ceiling Panels in Nogales, Sonora | ADIS Catalog', 'Laminated and wood-style PVC ceiling panels in Nogales, Sonora. Waterproof and easy to install. Quote with ADIS.')},
        'Paneles tridimensionales': {
            'es': ('Paneles 3D en Nogales, Sonora | ADIS Catálogo', 'Paneles decorativos 3D en Nogales, Sonora. Texturas modernas para muros de acento. Cotiza con ADIS Diseño & Remodelación.'),
            'en': ('3D Wall Panels in Nogales, Sonora | ADIS Catalog', 'Decorative 3D wall panels in Nogales, Sonora. Modern textures for accent walls. Quote with ADIS Design & Remodeling.')},
        'Vigas PVC': {
            'es': ('Vigas Decorativas PVC/WPC/PU en Nogales | ADIS', 'Vigas decorativas de PVC, WPC y PU en Nogales, Sonora. Imitación madera real sin mantenimiento. Cotiza con ADIS.'),
            'en': ('Decorative PVC/WPC/PU Beams in Nogales | ADIS', 'Decorative PVC, WPC and PU beams in Nogales, Sonora. Real wood look without maintenance. Quote with ADIS.')},
        'Pisos': {
            'es': ('Pisos Laminados, WPC y SPC en Nogales, Sonora | ADIS', 'Pisos laminados, WPC, SPC y deck sintético en Nogales, Sonora. Resistentes al agua y fáciles de instalar. Cotiza con ADIS.'),
            'en': ('Laminate, WPC and SPC Flooring in Nogales, Sonora | ADIS', 'Laminate, WPC, SPC and synthetic deck flooring in Nogales, Sonora. Water resistant and easy to install. Quote with ADIS.')},
        'Zacate': {
            'es': ('Zacate Sintético en Nogales, Sonora | ADIS Catálogo', 'Pasto artificial y zacate sintético en Nogales, Sonora. Para jardín, terraza y negocio. Cotiza con ADIS.'),
            'en': ('Artificial Grass in Nogales, Sonora | ADIS Catalog', 'Artificial grass and synthetic turf in Nogales, Sonora. For garden, terrace and business. Quote with ADIS.')},
        'Cladding': {
            'es': ('Cladding Tipo Piedra en Nogales, Sonora | ADIS', 'Cladding y placas tipo piedra en Nogales, Sonora. Revestimiento ligero para fachadas y muros. Cotiza con ADIS.'),
            'en': ('Stone-Look Cladding in Nogales, Sonora | ADIS', 'Stone-look cladding and panels in Nogales, Sonora. Lightweight veneer for facades and walls. Quote with ADIS.')},
    }
    cat_name_disp = cat_display(cat['name'])
    seo_entry = CAT_SEO.get(cat['name'], {}).get(infra.CUR_LANG) or CAT_SEO.get(cat['name'], {}).get('es')
    if seo_entry:
        cat_title, cat_desc_template = seo_entry
    elif infra.CUR_LANG == 'en':
        cat_title, cat_desc_template = (f"{cat_name_disp} in Nogales, Sonora | ADIS Catalog", f"{cat_name_disp} in Nogales, Sonora. Explore {cat['total_products']} products and request your quote with ADIS Design & Remodeling.")
    else:
        cat_title, cat_desc_template = (f"{cat['name']} en Nogales, Sonora | ADIS Catálogo", f"{cat['name']} en Nogales, Sonora. Explora {cat['total_products']} productos y solicita tu cotización con ADIS Diseño & Remodelación.")
    cat_desc = cat_desc_template.format(n=cat['total_products'])

    html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{cat_title}</title>
  <meta name="description" content="{cat_desc}">
  <meta name="keywords" content="{cat['name'].lower()} Nogales, {cat['name'].lower()} Sonora, recubrimientos Nogales, ADIS {cat['name'].lower()}, cotizar {cat['name'].lower()}">
  <meta property="og:title" content="{cat_title}">
  <meta property="og:description" content="{cat_desc}">
  <meta property="og:image" content="{SITE_URL}{hero_bg_quoted}">
  <meta property="og:url" content="{page_url(cat["filename"])}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{cat_title}">
  <meta name="twitter:description" content="{cat_desc}">
  <meta name="twitter:image" content="{SITE_URL}{hero_bg_quoted}">
  <link rel="canonical" href="{page_url(cat["filename"])}">
  {hreflang_tags(cat["filename"])}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script(cat["filename"])}
{organization_schema()}
{breadcrumb_html}
{product_schemas_html}</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header(cat["slug"], cat["filename"])}
{breadcrumbs_html}
  <section class="hero-cat-bg" style="background-image: url('{p(hero_bg)}');">
    <div class="hero-cat-content">
      {'<div class="hero-star-badge">&#11088; ' + i18n('featured_star_label') + '</div>' if cat["name"] in ("Lambrin WPC", "Placas PVC") else '<div class="hero-cat-badge">' + i18n('cat_badge') + '</div>'}
      <h1>{cat_display(cat["name"])}</h1>
      <p>{i18n_fmt('cat_hero_subtitle', category=cat_display(cat["name"]), count=cat["total_products"])}</p>
      <div class="hero-cat-actions">
        <a href="{wa_hero_url}" class="btn-primary btn-wa" target="_blank" onclick="gtag('event','whatsapp_click',{{'location':'hero_category','category':'{cat['name']}'}})">{i18n('cta_quote_whatsapp')}</a>
        <a href="tel:{CONTACTO['tel_mx_link']}" class="btn-outline" onclick="gtag('event','contacto_click',{{'tipo':'tel_mx','location':'hero_category'}})">{i18n('cat_cta_call')}</a>
        <a href="{p(pdf_url)}" class="btn-outline" download onclick="gtag('event','pdf_download',{{'category':'{cat['name']}'}})">{i18n('cat_cta_download')}</a>
      </div>
    </div>
  </section>

{subcat_nav_html}{real_sheets_html}
{category_filters_html(cat)}
{sections_html}
{cat_nav_html}
  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="{p('index.html')}" class="btn-back">{i18n('cat_back_home')}</a>
      <a href="{p('contacto.html')}" class="btn-outline">{i18n('cat_contact')}</a>
    </div>
  </section>

{calculator_html(categories, preselect=cat['name'])}

  <!-- CTA FINAL DE CATEGORÍA -->
  <section class="section-wrap cta-final-section reveal" style="padding-top: 2rem; padding-bottom: 2rem;">
    <div class="cta-final-box">
      <h2>{i18n_fmt('cat_cta_final_title', category=cat_display(cat['name']))}</h2>
      <p>{i18n('cat_cta_final_subtitle', html=True)}</p>
      <div class="hero-cat-actions" style="justify-content: center;">
        <a href="{wa_hero_url}" class="btn-primary btn-wa" target="_blank" onclick="gtag('event','whatsapp_click',{{'location':'cta_final_category','category':'{cat['name']}'}})">{i18n('sticky_quote_category')} {cat_display(cat['name'])}</a>
        <a href="{p('contacto.html')}" class="btn-secondary">{i18n('cat_cta_final_form')}</a>
      </div>
    </div>
  </section>

{generate_testimonios()}
{modal_cotizar_html()}
{category_filters_js()}
{generate_footer()}
</body>
</html>
'''
    filepath = out_dir() / cat["filename"]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(minify_html(html))
    print(f'{cat["filename"]} generado')




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
        'VIGAS PVC': 'img/6-vigas-pvc/61-interior/BAHIA%201.jpg',
        'PISOS': 'img/7-pisos/71-laminado/ACONCAGUA.jpg',
        'ZACATE SINTETICO': 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg',
        'ZACATE SINTÉTICO': 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg',
        'CLADDING  PLACAS TIPO PIEDRA': 'img/9-cladding/91-placa-tipo-roca/BLACK.jpg',
    }
    
    # Generar paginas individuales
    for cat_name in RESEARCH_DATA.keys():
        data = research_data(cat_name)
        cat_name_disp = research_cat_display(cat_name)
        slug = SABIAS_QUE_SLUGS.get(cat_name, 'otros')
        cat_img = cat_images.get(cat_name, 'LOGO%20ADIS.png')
        
        curiosos_cards = _extract_curiosos_cards(data['curiosos']) if data.get('curiosos') else ''
        faqs_html = _extract_faqs_html(data['faqs']) if data.get('faqs') else ''
        faqs_data = _extract_faqs_data(data['faqs']) if data.get('faqs') else []
        faq_schema_html = faqpage_schema([(f['q'], f['a']) for f in faqs_data]) if faqs_data else ''
        sq_filename = f"sabias-que-{slug}.html"
        sq_url = page_url(sq_filename)
        
        page_html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('sabias_slug_title').format(cat=cat_name_disp)}</title>
  <meta name="description" content="{t('sabias_slug_desc').format(cat=cat_name_disp)}">
  <meta property="og:title" content="{t('sabias_slug_title').format(cat=cat_name_disp)}">
  <meta property="og:description" content="{t('sabias_slug_desc').format(cat=cat_name_disp)}">
  <meta property="og:image" content="{SITE_URL}{cat_img}">
  <meta property="og:url" content="{page_url(sq_filename)}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t('sabias_slug_title').format(cat=cat_name_disp)}">
  <meta name="twitter:description" content="{t('sabias_slug_desc').format(cat=cat_name_disp)}">
  <meta name="twitter:image" content="{SITE_URL}{cat_img}">
  <link rel="canonical" href="{page_url(sq_filename)}">
  {hreflang_tags(sq_filename)}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script(sq_filename)}
{organization_schema()}
{breadcrumb_schema([(t('bc_home'), SITE_URL), (t('bc_sabias'), f'{SITE_URL}sabias-que.html'), (cat_name_disp, sq_url)])}
{faq_schema_html}</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header("sabias-que", sq_filename)}
{breadcrumb_html([(t('bc_home'), p('index.html')), (t('bc_sabias'), p('sabias-que.html')), (cat_name_disp, '')])}

  <section class="sq-hero">
    <h1>{i18n('sq_title')}</h1>
    <p>{i18n_fmt('sq_subtitle_known', category=cat_name_disp, html=True)}</p>
  </section>

  <div style="max-width:1100px;margin:0 auto;padding:0 1.5rem;">
    <a href="{p('sabias-que.html')}" style="display:inline-flex;align-items:center;gap:0.4rem;color:var(--gold);text-decoration:none;font-size:0.85rem;margin-bottom:1rem;">{i18n('sq_back_index')}</a>
  </div>

  <div class="sq-content" style="padding-top:0;">
    <div class="sq-cat-hero" style="background-image: url('{p(cat_img)}');">
      <div class="sq-cat-overlay">
        <h2>{cat_name_disp}</h2>
      </div>
    </div>
    <div class="section-header" style="margin:2rem 0 1.5rem;">
      <h2 style="font-size:1.4rem;">{i18n('sq_curiosos_title')}</h2>
      <div class="divider"></div>
    </div>
    <div class="sq-grid">
{curiosos_cards}    </div>
{('<div class="section-header" style="margin:2.5rem 0 1.5rem;"><h2 style="font-size:1.4rem;">' + i18n('sq_faqs_title') + '</h2><div class="divider"></div></div><div class="sq-faqs">' + faqs_html + '</div>') if faqs_html else ''}
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
    el.textContent = '{t("sq_card_readless")}';
  }} else {{
    shortEl.style.display = 'inline';
    fullEl.style.display = 'none';
    el.textContent = '{t("sq_card_readmore")}';
  }}
}}
</script>
</body>
</html>
'''
        with open(out_dir() / f'sabias-que-{slug}.html', 'w', encoding='utf-8') as f:
            f.write(minify_html(page_html))
        print(f"✅ sabias-que-{slug}.html generado ({cat_name_disp}) [{infra.CUR_LANG}]")
    
    # Generar pagina indice
    index_cards = ''
    for cat_name in RESEARCH_DATA.keys():
        slug = SABIAS_QUE_SLUGS.get(cat_name, 'otros')
        cat_img = cat_images.get(cat_name, 'LOGO%20ADIS.png')
        index_cards += f'''    <a href="{p('sabias-que-' + slug + '.html')}" class="sq-index-card">
      <div class="sq-index-img" style="background-image:url('{p(cat_img)}');"></div>
      <div class="sq-index-info">
        <h3>{research_cat_display(cat_name)}</h3>
        <span>{i18n('sq_see_more')}</span>
      </div>
    </a>
'''
    
    index_html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('title_sabias')}</title>
  <meta name="description" content="{t('sabias_meta_desc')}">
  <meta property="og:title" content="{t('title_sabias')}">
  <meta property="og:description" content="{t('sabias_meta_desc')}">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{page_url('sabias-que.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t('title_sabias')}">
  <meta name="twitter:description" content="{t('sabias_meta_desc')}">
  <meta name="twitter:image" content="{SITE_URL}LOGO%20ADIS.png">
  <link rel="canonical" href="{page_url('sabias-que.html')}">
  {hreflang_tags('sabias-que.html')}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script('sabias-que.html')}
{organization_schema()}
{breadcrumb_schema([(t('bc_home'), SITE_URL), (t('bc_sabias'), page_url('sabias-que.html'))])}
</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header("sabias-que", "sabias-que.html")}
{breadcrumb_html([(t('bc_home'), p('index.html')), (t('bc_sabias'), '')])}

  <section class="sq-hero">
    <h1>{i18n('sq_title')}</h1>
    <p>{i18n('sq_subtitle')}</p>
  </section>

  <div class="sq-content">
    <div class="sq-index-grid">
{index_cards}    </div>
  </div>

{generate_footer()}
</body>
</html>
'''
    with open(out_dir() / 'sabias-que.html', 'w', encoding='utf-8') as f:
        f.write(minify_html(index_html))
    print("✅ sabias-que.html (indice) generado")




def generate_proyectos():
    """Genera página de proyectos con carruseles de antes/después y galería dinámica."""
    media_dir = OUTPUT_DIR / 'media'
    
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
        label = f'{t("projects_remodeling")} {i}' if len(ba_pairs) > 1 else t("projects_beforeafter_title")
        antes_url, despues_url = p(f'media/{antes}'), p(f'media/{despues}')
        ba_sections += f'''  <section class="section-wrap reveal">
    <div class="section-header">
      <h2>{label}</h2>
      <div class="divider"></div>
      <p>{i18n('projects_carousel_hint')}</p>
    </div>
    <div class="ba-slider">
      {picture_tag(f'media/{despues}', t('projects_after'), cls='ba-after')}
      {picture_tag(f'media/{antes}', t('projects_before'), cls='ba-before')}
      <div class="ba-handle"><div class="ba-handle-btn">&#10094;&#10095;</div></div>
      <div class="ba-label ba-label-before">{i18n('projects_before')}</div>
      <div class="ba-label ba-label-after">{i18n('projects_after')}</div>
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
            img_url = p(f'media/{img}')
            slides += f'''        <div class="carousel-slide">
          {picture_tag(f'media/{img}', name, onclick=f"openLightbox('{img_url}', '{name}')")}
        </div>
'''
        gallery_section = f'''  <section class="section-wrap-alt reveal">
    <div class="section-header">
      <h2>{i18n('projects_gallery_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('projects_gallery_subtitle')}</p>
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
        name = video_caption(vid)
        mime = video_mime_type(vid)
        poster = loose_images[0] if loose_images else (images[0] if images else '')
        poster_attr = f' poster="{p("media/" + poster)}"' if poster else ''
        videos_html += f'''      <div class="video-card reveal">
        <video class="auto-video" muted loop playsinline{poster_attr}>
          <source src="{p('media/' + vid)}" type="{mime}">
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
      <h2>{i18n('projects_videos_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('projects_videos_subtitle')}</p>
    </div>
    <div class="video-grid">
{videos_html}    </div>
  </section>
'''
    
    html = f'''<!DOCTYPE html>
<html lang="{html_lang()}">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/png" href="{p('LOGO ADIS.png')}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {head_common()}
  <title>{t('title_proyectos')}</title>
  <meta name="description" content="{t('proyectos_meta_desc')}">
  <meta name="keywords" content="proyectos ADIS, antes y despues, remodelaciones Nogales, remodelaciones Arizona, placas PVC instaladas, lambrin WPC">
  <meta property="og:title" content="{t('title_proyectos')}">
  <meta property="og:description" content="{t('proyectos_meta_desc')}">
  {og_image_tags(f'{SITE_URL}media/despues.jpg')}
  <meta property="og:url" content="{page_url('proyectos.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:title" content="{t('title_proyectos')}">
  <meta name="twitter:description" content="{t('proyectos_meta_desc')}">
  <meta name="twitter:title" content="{t('title_proyectos')}">
  <meta name="twitter:description" content="{t('proyectos_meta_desc')}">
  <meta name="twitter:image" content="{SITE_URL}media/despues.jpg">
  <link rel="canonical" href="{page_url('proyectos.html')}">
  {hreflang_tags('proyectos.html')}
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p('style.css')}">
{ga_script()}
{fb_pixel_script()}
{translate_script('proyectos.html')}
{organization_schema()}
{breadcrumb_schema([(t('bc_home'), SITE_URL), (t('nav_projects'), page_url('proyectos.html'))])}
  <style>
    /* CAROUSEL */
    .carousel-wrap {{ position: relative; max-width: 900px; margin: 0 auto; overflow: hidden; border-radius: 12px; border: 1px solid rgba(197,160,89,0.2); }}
    /* SLIDER ANTES/DESPUÉS INTERACTIVO */
    .ba-slider {{ --pos: 50%; position: relative; max-width: 900px; margin: 0 auto; border-radius: 12px; overflow: hidden; border: 1px solid rgba(197,160,89,0.25); aspect-ratio: 16/10; user-select: none; -webkit-user-select: none; touch-action: pan-y; cursor: ew-resize; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }}
    .ba-slider picture {{ position: absolute; inset: 0; display: block; margin: 0; }}
    .ba-slider img {{ width: 100%; height: 100%; object-fit: cover; pointer-events: none; display: block; }}
    .ba-before {{ clip-path: inset(0 calc(100% - var(--pos)) 0 0); }}
    .ba-handle {{ position: absolute; top: 0; bottom: 0; left: var(--pos); width: 3px; background: var(--gold); transform: translateX(-50%); box-shadow: 0 0 12px rgba(197,160,89,0.6); pointer-events: none; }}
    .ba-handle-btn {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 48px; height: 48px; border-radius: 50%; background: var(--gold); color: var(--black); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.05rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }}
    .ba-label {{ position: absolute; bottom: 14px; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; backdrop-filter: blur(8px); pointer-events: none; }}
    .ba-label-before {{ left: 14px; background: rgba(15,15,15,0.6); color: var(--white); }}
    .ba-label-after {{ right: 14px; background: var(--gold); color: var(--black); }}
    @media (max-width: 768px) {{ .ba-slider {{ aspect-ratio: 4/3; }} }}
    .carousel {{ display: flex; transition: transform 0.5s ease; }}
    .carousel-slide {{ min-width: 100%; position: relative; }}
    .carousel-slide img {{ width: 100%; height: 500px; object-fit: cover; display: block; cursor: pointer; }}
    .carousel-label {{ position: absolute; bottom: 20px; left: 20px; padding: 0.5rem 1.2rem; border-radius: 25px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; backdrop-filter: blur(8px); }}
    .carousel-btn {{ position: absolute; top: 50%; transform: translateY(-50%); background: rgba(15,15,15,0.7); border: 1px solid var(--gold); color: var(--gold); width: 45px; height: 45px; border-radius: 50%; cursor: pointer; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; transition: all 0.3s; z-index: 2; }}
    .carousel-btn:hover {{ background: var(--gold); color: var(--black); }}
    .carousel-btn.prev {{ left: 15px; }}
    .carousel-btn.next {{ right: 15px; }}
    .video-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr)); gap: 1.5rem; max-width: 1200px; margin: 0 auto; }}
    .video-card video {{ width: 100%; border-radius: 8px; }}
    @media (max-width: 768px) {{ .carousel-slide img {{ height: 280px; }} .carousel-btn {{ width: 44px; height: 44px; font-size: 1rem; }} }}
  </style>
</head>
<body>
  <script>document.documentElement.classList.add('js-enabled');</script>
  <canvas id="bg-canvas"></canvas>
{generate_header("proyectos", "proyectos.html")}
{breadcrumb_html([(t('bc_home'), p('index.html')), (t('nav_projects'), '')])}

  <section class="hero-cat">
    <h1>{i18n('projects_title')}</h1>
    <p>{i18n('projects_subtitle')}</p>
  </section>

{ba_sections}{gallery_section}{video_section}
  <section class="section-wrap" style="padding-top: 1rem;">
    <div style="text-align: center;">
      <a href="{p('index.html')}" class="btn-back">{i18n('cat_back_home')}</a>
      <a href="{p('contacto.html')}" class="btn-outline">{i18n('cat_contact')}</a>
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
    // Slider Antes/Después arrastrable (mouse + táctil)
    document.querySelectorAll('.ba-slider').forEach(sl => {{
      const setPos = x => {{
        const r = sl.getBoundingClientRect();
        const pct = Math.max(2, Math.min(98, (x - r.left) / r.width * 100));
        sl.style.setProperty('--pos', pct + '%');
      }};
      let dragging = false;
      sl.addEventListener('pointerdown', e => {{ dragging = true; sl.setPointerCapture(e.pointerId); setPos(e.clientX); }});
      sl.addEventListener('pointermove', e => {{ if (dragging) setPos(e.clientX); }});
      ['pointerup', 'pointercancel'].forEach(ev => sl.addEventListener(ev, () => {{ dragging = false; }}));
    }});
    // Swipe táctil en carruseles + pausa de autoplay al interactuar
    let userInteracted = false;
    document.querySelectorAll('.carousel').forEach(car => {{
      let x0 = null;
      car.addEventListener('touchstart', e => {{ x0 = e.touches[0].clientX; }}, {{ passive: true }});
      car.addEventListener('touchend', e => {{
        if (x0 === null) return;
        const dx = e.changedTouches[0].clientX - x0;
        if (Math.abs(dx) > 40) {{ userInteracted = true; moveCarousel(car.id, dx < 0 ? 1 : -1); }}
        x0 = null;
      }}, {{ passive: true }});
      car.addEventListener('pointerdown', () => {{ userInteracted = true; }});
    }});
    // Auto-play carruseles: solo desktop, respeta reduced-motion y pausa del usuario
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isMobileView = matchMedia('(max-width: 768px)').matches;
    if (!reduceMotion && !isMobileView) {{
      setInterval(() => {{
        if (userInteracted) return;
        document.querySelectorAll('.carousel').forEach(car => {{
          moveCarousel(car.id, 1);
        }});
      }}, 5000);
    }}
    
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
    with open(out_dir() / 'proyectos.html', 'w', encoding='utf-8') as f:
        f.write(minify_html(html))
    print("proyectos.html generado")


