# -*- coding: utf-8 -*-
"""Orquestacion del build (main). Extraido de generar_web.py en M3 (salida byte-identica)."""
from .infra import *  # noqa
from .infra import _CAT_TR  # nombre con guion bajo: no sale en import *
from .datos import *  # noqa
from .seo import *  # noqa
from .componentes import *  # noqa
from .componentes import _extract_curiosos_data, _extract_faqs_data, _extract_curiosos_cards, _extract_faqs_html  # guion bajo: no salen en import *
from .paginas import *  # noqa


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
    ensure_logo_webp()
    generate_style()
    generate_sitemap(categories)
    generate_robots()

    # Panel de administracion (archivo estatico; no se traduce ni va al sitemap)
    admin_src = BASE_DIR / 'admin' / 'index.html'
    if admin_src.exists():
        # M1: inyectar config central en la copia (salida identica si los valores no cambiaron)
        # Bytes->str->bytes para preservar finales de linea exactos (autocrlf).
        admin_html = admin_src.read_bytes().decode('utf-8')
        admin_html = re.sub(r"(API_URL:\s*')[^']*(')", lambda m: m.group(1) + PLATAFORMA['url_backend'] + m.group(2), admin_html, count=1)
        admin_html = re.sub(r"(WHATSAPP:\s*')[^']*(')", lambda m: m.group(1) + PLATAFORMA['whatsapp'] + m.group(2), admin_html, count=1)
        (OUTPUT_DIR / 'admin.html').write_bytes(admin_html.encode('utf-8'))
        print("admin.html copiado al sitio (config inyectada desde 00_CORE/config/plataforma.json)")

    for lang in ('es', 'en'):
        set_lang(lang)
        print(f"\n===== Generando version {lang.upper()} -> {out_dir()} =====")
        (OUTPUT_DIR / 'en').mkdir(parents=True, exist_ok=True)
        generate_index(categories)
        generate_contacto()
        generate_nosotros()
        generate_privacy()
        generate_proyectos()
        generate_sabias_que()

        for cat in categories:
            generate_category_page(cat, categories)

    set_lang('es')

    # Generar products.json para el buscador
    products_data = []
    for cat in categories:
        cat_price = PRICE_DATA.get(cat["name"], {})
        for sub in cat["subcategories"]:
            for prod in sub["products"]:
                products_data.append({
                    'name': os.path.splitext(prod)[0],
                    'name_en': _CAT_TR.get('names', {}).get(os.path.splitext(prod)[0], os.path.splitext(prod)[0]),
                    'category': cat["name"],
                    'category_en': _CAT_TR.get('categories', {}).get(cat["name"], cat["name"]),
                    'subcategory': sub["name"],
                    'subcategory_en': _CAT_TR.get('subcategories', {}).get(sub["name"], sub["name"]),
                    'url': f'{cat["filename"]}#{sub["slug"]}',
                    'thumb': f'img/{cat["slug"]}/{sub["slug"]}/{prod}',
                    'price': cat_price.get('range', 'Consultar'),
                    'price_unit': cat_price.get('unit', 'pieza'),
                    'price_note': cat_price.get('note', '')
                })
        for prod in cat["direct_products"]:
            products_data.append({
                'name': os.path.splitext(prod)[0],
                'name_en': _CAT_TR.get('names', {}).get(os.path.splitext(prod)[0], os.path.splitext(prod)[0]),
                'category': cat["name"],
                'category_en': _CAT_TR.get('categories', {}).get(cat["name"], cat["name"]),
                'subcategory': None,
                'subcategory_en': None,
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
            'VIGAS PVC': 'vigas',
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
    # Versión EN de los datos de investigación para el chatbot
    research_output_en = {}
    if RESEARCH_DATA_EN and RESEARCH_DATA:
        for cat_name, data in RESEARCH_DATA_EN.items():
            slug = research_cat_slugs.get(cat_name)
            if not slug:
                continue
            curiosos = _extract_curiosos_data(data.get('curiosos', ''))
            faqs = _extract_faqs_data(data.get('faqs', ''))
            if curiosos or faqs:
                research_output_en[slug] = {
                    'name': cat_name,
                    'slug': slug,
                    'curiosos': curiosos,
                    'faqs': faqs
                }
    
    output_data = {'products': products_data, 'research': research_output, 'research_en': research_output_en}
    with open(OUTPUT_DIR / 'products.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\nproducts.json generado con {len(products_data)} productos y datos de {len(research_output)} categorías de investigación")

    print("\nSitio web generado exitosamente en:", OUTPUT_DIR)
    print(f"   - {len(categories)} categorias")
    total_products = sum(len(c["direct_products"]) + sum(len(s["products"]) for s in c["subcategories"]) for c in categories)
    print(f"   - {total_products} productos totales")




if __name__ == '__main__':
    main()


