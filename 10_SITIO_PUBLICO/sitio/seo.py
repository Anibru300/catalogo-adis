# -*- coding: utf-8 -*-
"""SEO: schemas, sitemap, robots, analytics. Extraido de generar_web.py en M3 (salida byte-identica)."""
from . import infra
from .infra import *  # noqa

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




def fb_pixel_script():
    """Facebook Pixel base. Reemplaza FB_PIXEL_ID por tu ID real."""
    FB_PIXEL_ID = 'FB_PIXEL_ID_PLACEHOLDER'
    if not FB_PIXEL_ID or FB_PIXEL_ID == 'FB_PIXEL_ID_PLACEHOLDER':
        return ''
    return f'''
  <!-- Meta Pixel Code -->
  <script>
    !function(f,b,e,v,n,t,s)
    {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', '{FB_PIXEL_ID}');
    fbq('track', 'PageView');
  </script>
  <noscript>
    <img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id={FB_PIXEL_ID}&ev=PageView&noscript=1"/>
  </noscript>
  <!-- End Meta Pixel Code -->'''




# ========== WHATSAPP & COTIZACIÓN HELPERS ==========




# ========== SCHEMA.ORG / SEO ==========

def head_common():
    """Bloque de performance y OG base común a todas las paginas."""
    return f'''<meta name="theme-color" content="#0F0F0F">
  <meta property="og:site_name" content="ADIS Diseño & Remodelación">
{og_locale()}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://www.googletagmanager.com">
  <link rel="preload" href="{p('style.css')}" as="style">
  <link rel="preload" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&family=Playfair+Display:wght@400;700&display=swap" as="style">'''




def og_image_tags(image_url):
    """Devuelve OG/Twitter image tags con URL absoluta y dimensiones por defecto."""
    return f'''<meta property="og:image" content="{image_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:image" content="{image_url}">
  <meta name="twitter:card" content="summary_large_image">'''




def breadcrumb_html(items):
    """Genera breadcrumbs visuales a partir de lista de (nombre, url).
    El ultimo elemento se muestra sin enlace.
    """
    if not items:
        return ''
    parts = []
    for i, (name, url) in enumerate(items):
        if i == len(items) - 1 or not url:
            parts.append(f'<span>{name}</span>')
        else:
            parts.append(f'<a href="{url}">{name}</a>')
    return f'''  <nav class="breadcrumbs breadcrumbs-page" aria-label="Breadcrumb">
    {' <span>/</span> '.join(parts)}
  </nav>
''' if parts else ''




def organization_schema():
    """Schema.org de Organization + LocalBusiness para ADIS. Refuerza SEO local MX/AZ."""
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
        "hasMap": CONTACTO.get("maps_url", ""),
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
        "priceRange": "$$",
        "paymentAccepted": "Efectivo, tarjeta, transferencia",
        "currenciesAccepted": "MXN, USD",
        "areaServed": [
            {"@type": "City", "name": "Heroica Nogales", "addressCountry": "MX"},
            {"@type": "City", "name": "Nogales", "addressCountry": "US"},
            {"@type": "City", "name": "Rio Rico", "addressCountry": "US"},
            {"@type": "City", "name": "Tucson", "addressCountry": "US"},
            {"@type": "City", "name": "Phoenix", "addressCountry": "US"},
            {"@type": "City", "name": "León", "addressCountry": "MX"}
        ],
        "contactPoint": [
            {
                "@type": "ContactPoint",
                "telephone": CONTACTO["tel_mx"],
                "contactType": "sales",
                "areaServed": "MX",
                "availableLanguage": ["Spanish"]
            },
            {
                "@type": "ContactPoint",
                "telephone": CONTACTO["tel_usa"],
                "contactType": "sales",
                "areaServed": "US",
                "availableLanguage": ["Spanish", "English"]
            }
        ]
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
    `image` acepta una URL (str) o una lista de URLs (galería).
    """
    cat_path = category + (f" > {subcategory}" if subcategory else "")
    if isinstance(image, str):
        image = [image]
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
    """Genera sitemap.xml con URLs públicas y prioridades jerárquicas."""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    url_entries = [
        (SITE_URL, '1.0'),
        (f"{SITE_URL}contacto.html", '0.9'),
        (f"{SITE_URL}nosotros.html", '0.8'),
        (f"{SITE_URL}aviso-de-privacidad.html", '0.5'),
    ]
    for cat in categories:
        url_entries.append((f"{SITE_URL}{cat['filename']}", '0.8'))
    url_entries.append((f"{SITE_URL}proyectos.html", '0.7'))
    url_entries.append((f"{SITE_URL}sabias-que.html", '0.6'))
    for cat_name in RESEARCH_DATA.keys():
        sq_slug = SABIAS_QUE_SLUGS.get(cat_name, 'otros')
        url_entries.append((f"{SITE_URL}sabias-que-{sq_slug}.html", '0.5'))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    for url, priority in url_entries:
        path = url.replace(SITE_URL, '')
        en_url = f"{SITE_URL}en/{path}"
        xml += (f'  <url><loc>{url}</loc>'
                f'<xhtml:link rel="alternate" hreflang="es" href="{url}"/>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>'
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{url}"/>'
                f'<lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>{priority}</priority></url>\n')
        xml += (f'  <url><loc>{en_url}</loc>'
                f'<xhtml:link rel="alternate" hreflang="es" href="{url}"/>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>'
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{url}"/>'
                f'<lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>{priority}</priority></url>\n')
    xml += '</urlset>'

    sitemap_path = OUTPUT_DIR / 'sitemap.xml'
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(xml)
    print("  sitemap.xml generado")




def generate_robots():
    """Genera robots.txt con referencia al sitemap. El panel de admin queda excluido."""
    content = f"User-agent: *\nAllow: /\nDisallow: /admin.html\nSitemap: {SITE_URL}sitemap.xml\n"
    robots_path = OUTPUT_DIR / 'robots.txt'
    with open(robots_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  robots.txt generado")


