# -*- coding: utf-8 -*-
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
BASE_DIR = Path(__file__).resolve().parent
CATALOG_DIR = Path(r'G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL')
OUTPUT_DIR = BASE_DIR / 'public'

# ========== CAPTACION DE LEADS Y RESENAS (Google Apps Script) ==========
# Sigue los pasos de admin/GUIA_CONFIGURACION.md para crear la hoja de Google
# y el Apps Script, despliega el script como app web y pega su URL aqui.
# Mientras esten vacios, el sitio funciona igual (formulario solo abre WhatsApp).
LEADS_URL = 'https://script.google.com/macros/s/AKfycbwia7Zk4sEleYA3dgNWBxRyV9HWyFdfckCmQbPQTxVDrhOLijJAhbUonjvDh5o2eZQW/exec'    # Recibe los envios del formulario de contacto (pestaña Leads)
REVIEWS_URL = 'https://script.google.com/macros/s/AKfycbwia7Zk4sEleYA3dgNWBxRyV9HWyFdfckCmQbPQTxVDrhOLijJAhbUonjvDh5o2eZQW/exec'  # Mismo script; expone las resenas para el sitio

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
TRANSLATIONS = {
    # Navegación
    'nav_home': {'es': 'Inicio', 'en': 'Home'},
    'nav_catalog': {'es': 'Catálogo', 'en': 'Catalog'},
    'nav_did_you_know': {'es': '¿Sabías que?', 'en': 'Did you know?'},
    # Menú categorías
    'menu_placas_pvc': {'es': 'Placas PVC', 'en': 'PVC Panels'},
    'menu_lambrin_wpc': {'es': 'Lambrín WPC', 'en': 'WPC Slats'},
    'menu_revestimiento': {'es': 'Revestimiento Flexible', 'en': 'Flexible Cladding'},
    'menu_plafon': {'es': 'Plafón PVC', 'en': 'PVC Ceiling'},
    'menu_paneles_3d': {'es': 'Paneles 3D', 'en': '3D Panels'},
    'menu_vigas': {'es': 'Vigas PVC', 'en': 'PVC Beams'},
    'menu_pisos': {'es': 'Pisos', 'en': 'Flooring'},
    'menu_zacate': {'es': 'Zacate', 'en': 'Synthetic Grass'},
    'menu_cladding': {'es': 'Cladding', 'en': 'Cladding'},
    'nav_projects': {'es': 'Proyectos', 'en': 'Projects'},
    'nav_contact': {'es': 'Contacto', 'en': 'Contact'},
    'nav_back_home': {'es': '← Inicio', 'en': '← Home'},
    'search_placeholder': {'es': 'Buscar producto...', 'en': 'Search products...'},
    'search_mobile_placeholder': {'es': 'Buscar producto...', 'en': 'Search products...'},
    'search_title': {'es': 'Busca entre {count} productos', 'en': 'Search {count}+ products'},
    'search_hint': {'es': 'Presiona / para buscar desde cualquier página', 'en': 'Press / to search from any page'},
    'search_start_typing': {'es': 'Escribe para buscar productos...', 'en': 'Type to search products...'},
    'search_no_results': {'es': 'No se encontraron productos', 'en': 'No products found'},
    'search_results_count': {'es': '{count} resultados', 'en': '{count} results'},
    'search_view_product': {'es': 'Ver producto', 'en': 'View product'},
    'search_quote': {'es': 'Cotizar', 'en': 'Quote'},
    'search_all_results': {'es': 'Ver todos los resultados', 'en': 'See all results'},

    # Hero home
    'hero_badge': {'es': 'Catálogo 2025 — 2026', 'en': '2025 — 2026 Catalog'},
    'hero_title': {'es': 'Recubrimientos PVC, WPC y paneles 3D en <em>Tucson, Arizona</em>, Nogales Sonora y Nogales Arizona', 'en': 'PVC, WPC & 3D Wall Panels in <em>Tucson, Arizona</em>, Nogales Sonora & Nogales Arizona'},
    'hero_subtitle': {'es': 'Transforma tu hogar o negocio con placas PVC, lambrín WPC, plafón, pisos, zacate sintético y cladding. Enviamos a Nogales, Sonora y Arizona. Cotiza gratis hoy.', 'en': 'Transform your home or business with PVC panels, WPC slats, PVC ceilings, flooring, synthetic grass and cladding. We ship to Nogales, Sonora & Arizona. Get a free quote today.'},
    'cta_quote_whatsapp': {'es': 'Cotizar gratis por WhatsApp', 'en': 'Free quote via WhatsApp'},
    'cta_view_catalog': {'es': 'Ver catálogo', 'en': 'View catalog'},
    'hero_note': {'es': '¿Prefieres que te llamemos? <a href="contacto.html">Llena el formulario de cotización</a> y te contactamos.', 'en': 'Prefer a call? <a href="contacto.html">Fill out the quote form</a> and we will contact you.'},

    # Sticky CTA
    'sticky_quote': {'es': 'Cotizar por WhatsApp', 'en': 'Quote via WhatsApp'},
    'sticky_call': {'es': 'Llamar', 'en': 'Call'},
    'sticky_quote_category': {'es': 'Cotizar', 'en': 'Quote'},
    'sticky_quote_project': {'es': 'Cotizar proyecto', 'en': 'Quote project'},

    # Beneficios
    'benefits_title': {'es': '¿Por qué elegir ADIS?', 'en': 'Why choose ADIS?'},
    'benefits_subtitle': {'es': 'Materiales premium, asesoría personalizada y entrega en Nogales, Sonora y Arizona.', 'en': 'Premium materials, personalized advice and delivery to Nogales, Sonora & Arizona.'},
    'benefit_shipping_title': {'es': 'Envíos locales', 'en': 'Local delivery'},
    'benefit_shipping_desc': {'es': 'Entrega en Nogales, Sonora y Arizona. También enviamos a todo México.', 'en': 'Delivery in Nogales, Sonora & Arizona. We also ship throughout Mexico.'},
    'benefit_warranty_title': {'es': 'Garantía real', 'en': 'Real warranty'},
    'benefit_warranty_desc': {'es': 'Hasta 15 años de garantía en placas PVC, WPC y plafón. Calidad comprobada.', 'en': 'Up to 15 years warranty on PVC panels, WPC and PVC ceilings. Proven quality.'},
    'benefit_advice_title': {'es': 'Asesoría sin costo', 'en': 'Free advice'},
    'benefit_advice_desc': {'es': 'Te ayudamos a elegir el mejor material según tu proyecto, clima y presupuesto.', 'en': 'We help you choose the best material for your project, climate and budget.'},
    'benefit_install_title': {'es': 'Instalación profesional', 'en': 'Professional installation'},
    'benefit_install_desc': {'es': 'Contamos con equipo de instalación para que tu remodelación quede perfecta.', 'en': 'We have an installation team so your remodeling turns out perfect.'},

    # Trust banner
    'trust_products': {'es': 'productos', 'en': 'products'},
    'trust_projects': {'es': 'proyectos', 'en': 'projects'},
    'trust_categories': {'es': 'categorías', 'en': 'categories'},
    'trust_warranty': {'es': 'años garantía', 'en': 'years warranty'},

    # Precios
    'prices_title': {'es': 'Precios orientativos', 'en': 'Reference prices'},
    'prices_subtitle': {'es': 'Conoce rangos aproximados por categoría. El precio final depende del modelo, acabado y metros de tu proyecto.', 'en': 'See approximate ranges by category. Final price depends on model, finish and square footage of your project.'},
    'prices_cta': {'es': 'Pedir cotización exacta', 'en': 'Get exact quote'},
    'price_unit_piece': {'es': 'MXN/pz', 'en': 'MXN/pc'},
    'price_unit_box': {'es': 'MXN/caja', 'en': 'MXN/box'},
    'price_unit_m2': {'es': 'MXN/m²', 'en': 'MXN/m²'},

    # Nosotros
    'about_title': {'es': 'Sobre ADIS', 'en': 'About ADIS'},
    'about_subtitle': {'es': 'En ADI\'S DISEÑO & REMODELACIÓN nos especializamos en ofrecer soluciones funcionales, estéticas y duraderas.', 'en': 'At ADIS DESIGN & REMODELING we specialize in functional, aesthetic and durable solutions.'},
    'info_pvc_title': {'es': 'Placas PVC', 'en': 'PVC Panels'},
    'info_pvc_desc': {'es': 'Paneles rígidos de alta calidad tipo madera, texturizados y espejo. Ideales para interiores.', 'en': 'High-quality rigid panels in wood look, textured and mirror finishes. Ideal for interiors.'},
    'info_wpc_title': {'es': 'Lambrín WPC', 'en': 'WPC Slats'},
    'info_wpc_desc': {'es': 'Wood Plastic Composite para interior y exterior. Resistente a la humedad y rayos UV.', 'en': 'Wood Plastic Composite for indoor and outdoor use. Resistant to moisture and UV rays.'},
    'info_flooring_title': {'es': 'Pisos & Zacate', 'en': 'Flooring & Grass'},
    'info_flooring_desc': {'es': 'Laminados, WPC, SPC, deck sintético y pasto artificial para todo tipo de espacios.', 'en': 'Laminate, WPC, SPC, synthetic deck and artificial grass for all kinds of spaces.'},
    'info_cladding_title': {'es': 'Cladding & 3D', 'en': 'Cladding & 3D'},
    'info_cladding_desc': {'es': 'Paneles decorativos tridimensionales y revestimientos de alta gama para fachadas.', 'en': 'Three-dimensional decorative panels and high-end cladding for facades.'},

    # Stats
    'stat_products': {'es': 'Productos', 'en': 'Products'},
    'stat_categories': {'es': 'Categorías', 'en': 'Categories'},
    'stat_projects_done': {'es': 'Proyectos Realizados', 'en': 'Projects Done'},
    'stat_happy_clients': {'es': 'Clientes Satisfechos', 'en': 'Happy Clients'},

    # Productos estrella
    'featured_title': {'es': 'Productos Estrella', 'en': 'Star Products'},
    'featured_subtitle': {'es': 'Los favoritos de nuestros clientes. Calidad premium que transforma cualquier espacio.', 'en': 'Our customers\' favorites. Premium quality that transforms any space.'},
    'featured_star_label': {'es': 'Producto Estrella', 'en': 'Star Product'},
    'featured_star_badge': {'es': 'Más vendido', 'en': 'Best seller'},
    'badge_new': {'es': 'Nuevo', 'en': 'New'},
    'featured_wpc_desc': {'es': 'Wood Plastic Composite de alta gama. Resistente a la humedad, rayos UV y perfecto para interiores y exteriores. Nuestro producto más solicitado.', 'en': 'High-end Wood Plastic Composite. Moisture and UV resistant, perfect for indoors and outdoors. Our most requested product.'},
    'featured_pvc_desc': {'es': 'Paneles rígidos tipo madera, texturizados y espejo. Acabado profesional con instalación rápida y garantía extendida.', 'en': 'Rigid wood-look, textured and mirror panels. Professional finish with fast installation and extended warranty.'},

    # Producto destacado
    'featured_marble_title': {'es': 'Hoja de PVC tipo Mármol', 'en': 'Marble-look PVC Sheet'},
    'featured_marble_subtitle': {'es': 'Elegancia y durabilidad para cualquier espacio interior', 'en': 'Elegance and durability for any indoor space'},
    'featured_marble_text': {'es': 'La lámina de <strong>PVC tipo mármol</strong> es la solución decorativa perfecta si buscas añadir un toque de elegancia a tu hogar, oficina o espacio comercial. Fabricada con materiales de alta calidad, es a la vez <strong>duradera y ligera</strong>, por lo que es fácil de instalar y mantener.', 'en': 'The <strong>marble-look PVC sheet</strong> is the perfect decorative solution if you want to add a touch of elegance to your home, office or commercial space. Made with high-quality materials, it is <strong>durable and lightweight</strong>, making it easy to install and maintain.'},
    'featured_marble_bullet1': {'es': 'Resistente al <strong>agua, manchas y arañazos</strong>', 'en': 'Resistant to <strong>water, stains and scratches</strong>'},
    'featured_marble_bullet2': {'es': 'Inversión que <strong>dura muchos años</strong>', 'en': 'Investment that <strong>lasts for many years</strong>'},
    'featured_marble_bullet3': {'es': 'Ideal para <strong>cocinas, baños, salas de estar</strong> y más', 'en': 'Ideal for <strong>kitchens, bathrooms, living rooms</strong> and more'},
    'featured_marble_bullet4': {'es': 'Acabado profesional con <strong>garantía extendida</strong>', 'en': 'Professional finish with <strong>extended warranty</strong>'},
    'featured_marble_cta': {'es': 'Ver en catálogo →', 'en': 'View in catalog →'},

    # Catálogo home
    'catalog_title': {'es': 'Nuestro Catálogo', 'en': 'Our Catalog'},
    'catalog_subtitle': {'es': 'Selecciona una categoría para ver los productos con su ficha técnica.', 'en': 'Select a category to see products with technical specs.'},

    # Descargas
    'downloads_title': {'es': 'Descargas', 'en': 'Downloads'},
    'downloads_subtitle': {'es': 'Descarga nuestros catálogos en PDF para consultarlos sin conexión o compartirlos con tu cliente.', 'en': 'Download our PDF catalogs to consult offline or share with your client.'},
    'download_complete': {'es': '📚 Descargar catálogo completo', 'en': '📚 Download complete catalog'},
    'download_complete_sub': {'es': 'Todas las categorías en un solo PDF', 'en': 'All categories in one PDF'},
    'download_products': {'es': 'productos · PDF', 'en': 'products · PDF'},

    # Arizona
    'arizona_title': {'es': 'Servimos en Arizona', 'en': 'We serve Arizona'},
    'arizona_subtitle': {'es': 'Enviamos materiales de remodelación a Nogales AZ, Rio Rico, Tucson y Phoenix. Atención en español y cotizaciones en USD/MXN.', 'en': 'We ship remodeling materials to Nogales AZ, Rio Rico, Tucson and Phoenix. Spanish-speaking service and quotes in USD/MXN.'},
    'arizona_nogales_title': {'es': 'Nogales, AZ', 'en': 'Nogales, AZ'},
    'arizona_nogales_desc': {'es': 'Showroom fronterizo y entregas coordinadas.', 'en': 'Border showroom and coordinated deliveries.'},
    'arizona_riorico_title': {'es': 'Rio Rico, AZ', 'en': 'Rio Rico, AZ'},
    'arizona_riorico_desc': {'es': 'Envíos directos para proyectos residenciales.', 'en': 'Direct shipping for residential projects.'},
    'arizona_tucson_title': {'es': 'Tucson, AZ', 'en': 'Tucson, AZ'},
    'arizona_tucson_desc': {'es': 'Materiales para remodelación de interiores y exteriores.', 'en': 'Materials for interior and exterior remodeling.'},
    'arizona_phoenix_title': {'es': 'Phoenix, AZ', 'en': 'Phoenix, AZ'},
    'arizona_phoenix_desc': {'es': 'Cotizaciones y envíos para proyectos grandes.', 'en': 'Quotes and shipping for large projects.'},
    'arizona_cta': {'es': 'Cotizar desde Arizona', 'en': 'Quote from Arizona'},

    # Videos home
    'videos_title': {'es': '🎬 Proyectos en video', 'en': '🎬 Projects in video'},
    'videos_subtitle': {'es': 'Remodelaciones reales que muestran el antes y después de nuestros materiales.', 'en': 'Real remodelings showing before and after with our materials.'},
    'videos_more': {'es': 'Ver más proyectos', 'en': 'See more projects'},

    # Testimonios
    'testimonials_title': {'es': 'Testimonios de Clientes', 'en': 'Customer Testimonials'},
    'testimonials_subtitle': {'es': '¿Ya usaste nuestros productos? Comparte tu experiencia y ayuda a otros a decidirse.', 'en': 'Have you used our products? Share your experience and help others decide.'},
    'testimonials_name': {'es': 'Tu nombre', 'en': 'Your name'},
    'testimonials_comment': {'es': '¿Qué te pareció el producto o servicio?', 'en': 'What did you think of the product or service?'},
    'testimonials_product': {'es': 'Producto o categoría que compraste (opcional)', 'en': 'Product or category you purchased (optional)'},
    'testimonials_send': {'es': 'Enviar Testimonio', 'en': 'Send Testimonial'},
    'testimonials_review': {'es': 'Los testimonios son revisados antes de publicarse.', 'en': 'Testimonials are reviewed before being published.'},
    'testimonials_whatsapp': {'es': 'También puedes enviarlos directamente por', 'en': 'You can also send them directly via'},
    'testimonial_maria_text': {'es': 'Excelente calidad en las placas PVC tipo espejo. Transformaron completamente mi sala de estar. La instalación fue súper rápida y el acabado se ve de lujo.', 'en': 'Excellent quality in the mirror-finish PVC panels. They completely transformed my living room. Installation was super fast and the finish looks luxurious.'},
    'testimonial_maria_name': {'es': 'María G.', 'en': 'María G.'},
    'testimonial_maria_meta': {'es': 'Placas PVC, Nogales', 'en': 'PVC Panels, Nogales'},
    'testimonial_carlos_text': {'es': 'Compré el lambrín WPC para el exterior de mi consultorio y quedó espectacular. Resiste perfectamente el sol y la lluvia. 100% recomendado.', 'en': 'I bought WPC slats for the exterior of my office and it looks spectacular. It withstands sun and rain perfectly. 100% recommended.'},
    'testimonial_carlos_name': {'es': 'Dr. Carlos R.', 'en': 'Dr. Carlos R.'},
    'testimonial_carlos_meta': {'es': 'Lambrín WPC, Rio Rico', 'en': 'WPC Slats, Rio Rico'},
    'testimonial_lopez_text': {'es': 'El equipo de ADIS me ayudó a elegir los pisos SPC para toda mi casa. Me dieron asesoría de primera y el precio fue muy competitivo. Quedé encantada.', 'en': 'The ADIS team helped me choose SPC flooring for my entire house. They gave me first-class advice and the price was very competitive. I was delighted.'},
    'testimonial_lopez_name': {'es': 'Familia López', 'en': 'López Family'},
    'testimonial_lopez_meta': {'es': 'Pisos SPC, Nogales', 'en': 'SPC Flooring, Nogales'},
    'testimonial_roberto_text': {'es': 'Excelente servicio desde Tucson. Envían materiales a Arizona y la atención por WhatsApp fue muy rápida. El cladding para mi fachada quedó impecable.', 'en': 'Excellent service from Tucson. They ship materials to Arizona and WhatsApp support was very fast. The cladding for my facade turned out impeccable.'},
    'testimonial_roberto_name': {'es': 'Roberto M.', 'en': 'Roberto M.'},
    'testimonial_roberto_meta': {'es': 'Cladding, Tucson AZ', 'en': 'Cladding, Tucson AZ'},
    'testimonial_thanks': {'es': '¡Gracias ', 'en': 'Thank you '},
    'testimonial_thanks_end': {'es': '! Tu testimonio se envió por WhatsApp. Será revisado y publicado pronto.', 'en': '! Your testimonial was sent via WhatsApp. It will be reviewed and published soon.'},

    # Footer
    'footer_slogan': {'es': 'Creando espacios, reinventando hogares.', 'en': 'Creating spaces, reinventing homes.'},
    'footer_copyright_suffix': {'es': 'ADIS DISEÑO & REMODELACIÓN. TODOS LOS DERECHOS RESERVADOS.', 'en': 'ADIS DESIGN & REMODELING. ALL RIGHTS RESERVED.'},
    'footer_whatsapp': {'es': 'WhatsApp', 'en': 'WhatsApp'},
    'footer_facebook': {'es': 'Facebook', 'en': 'Facebook'},

    # Mobile bottom nav
    'mobile_nav_home': {'es': 'Inicio', 'en': 'Home'},
    'mobile_nav_catalog': {'es': 'Catálogo', 'en': 'Catalog'},
    'mobile_nav_projects': {'es': 'Proyectos', 'en': 'Projects'},
    'mobile_nav_contact': {'es': 'Contacto', 'en': 'Contact'},

    # Categorías
    'cat_badge': {'es': 'Categoría', 'en': 'Category'},
    'cat_hero_subtitle': {'es': 'Explora nuestra línea de {category} con {count} productos disponibles. Solicita tu cotización.', 'en': 'Explore our {category} line with {count} products available. Request your quote.'},
    'cat_cta_advice': {'es': 'Asesoría por WhatsApp', 'en': 'Advice via WhatsApp'},
    'cat_cta_download': {'es': 'Descargar catálogo PDF', 'en': 'Download PDF catalog'},
    'cat_cta_call': {'es': 'Llamar', 'en': 'Call'},
    'cat_cta_final_title': {'es': '¿Listo para transformar tu espacio con {category}?', 'en': 'Ready to transform your space with {category}?'},
    'cat_cta_final_subtitle': {'es': 'Solicita tu cotización gratis. Respondemos en menos de 24 h y enviamos a Nogales, Sonora y Arizona.', 'en': 'Request your free quote. We respond in less than 24 hours and ship to Nogales, Sonora & Arizona.'},
    'cat_cta_final_form': {'es': 'Llenar formulario', 'en': 'Fill form'},
    'cat_back_home': {'es': '← Volver al Inicio', 'en': '← Back to Home'},
    'cat_contact': {'es': 'Contactar', 'en': 'Contact'},
    'calc_title': {'es': '¿Cuánto material necesito?', 'en': 'How much material do I need?'},
    'calc_subtitle': {'es': 'Ingresa las medidas de tu muro y calcula los m² a cotizar.', 'en': 'Enter your wall measurements and calculate the square meters to quote.'},
    'calc_height': {'es': 'Alto del muro (m)', 'en': 'Wall height (m)'},
    'calc_width': {'es': 'Ancho del muro (m)', 'en': 'Wall width (m)'},
    'calc_product': {'es': 'Producto de interés', 'en': 'Product of interest'},
    'calc_button': {'es': 'Calcular material', 'en': 'Calculate material'},
    'calc_error': {'es': 'Ingresa medidas válidas (mayores a 0).', 'en': 'Please enter valid measurements (greater than 0).'},
    'calc_note_tpl': {'es': 'Área: {m} m² + 10% de desperdicio por cortes y ajustes.', 'en': 'Area: {m} m² + 10% extra for cuts and adjustments.'},
    'calc_wa_msg': {'es': 'Hola ADIS, quiero cotizar {c}. Mi muro mide {a} m de alto x {b} m de ancho = {m} m2. Con el 10% de desperdicio serian aproximadamente {t} m2. ¿Me pueden dar precio y disponibilidad?', 'en': 'Hello ADIS, I would like a quote for {c}. My wall is {a} m high x {b} m wide = {m} m2. With 10% waste it would be about {t} m2. Can you give me pricing and availability?'},
    'trans_title': {'es': 'Transformaciones reales de clientes', 'en': 'Real customer transformations'},
    'trans_subtitle': {'es': 'Fotos reales de proyectos ADIS. Sin filtros, sin edición.', 'en': 'Real photos from ADIS projects. No filters, no editing.'},
    'trans_cta': {'es': 'Ver todos los proyectos', 'en': 'See all projects'},
    'topbar_text': {'es': 'Envíos a Nogales y Tucson · Cotización gratis hoy', 'en': 'We ship to Nogales & Tucson · Free quote today'},
    'cat_best_sellers': {'es': 'Más Vendidos — Placas PVC', 'en': 'Best Sellers — PVC Panels'},
    'cat_accessories': {'es': 'Accesorios', 'en': 'Accessories'},
    'cat_products': {'es': 'Productos {category}', 'en': '{category} Products'},
    'cat_real_sheets_title': {'es': 'Hojas Reales de PVC', 'en': 'Real PVC Sheets'},
    'cat_real_sheets_subtitle': {'es': 'Fotos reales de nuestro showroom. Sin filtros, sin edición.', 'en': 'Real photos from our showroom. No filters, no editing.'},
    'cat_real_sheets_badge': {'es': 'Foto Real', 'en': 'Real Photo'},

    # Contacto
    'contact_title': {'es': 'Cotiza recubrimientos en Nogales, Sonora', 'en': 'Quote wall coverings in Nogales, Sonora'},
    'contact_subtitle': {'es': 'Placas PVC, lambrín WPC, paneles 3D, plafón, pisos, zacate y cladding. Respuesta en menos de 24 horas.', 'en': 'PVC panels, WPC slats, 3D panels, PVC ceilings, flooring, synthetic grass and cladding. Response in less than 24 hours.'},
    'contact_form_title': {'es': 'Solicita tu cotización gratis', 'en': 'Request your free quote'},
    'contact_form_subtitle': {'es': 'Cuéntanos tu proyecto y te contactamos con precios y disponibilidad.', 'en': 'Tell us about your project and we will contact you with prices and availability.'},
    'form_name': {'es': 'Nombre *', 'en': 'Name *'},
    'form_name_placeholder': {'es': 'Tu nombre', 'en': 'Your name'},
    'form_phone': {'es': 'Teléfono *', 'en': 'Phone *'},
    'form_phone_placeholder': {'es': 'Ej. 631 123 4567', 'en': 'e.g. 631 123 4567'},
    'form_email': {'es': 'Correo electrónico', 'en': 'Email'},
    'form_email_placeholder': {'es': 'tu@email.com', 'en': 'you@email.com'},
    'form_city': {'es': 'Ciudad / Ubicación de la obra *', 'en': 'City / Project location *'},
    'form_city_placeholder': {'es': 'Ej. Nogales, Sonora', 'en': 'e.g. Nogales, Sonora'},
    'form_sqm': {'es': 'm² aproximados', 'en': 'Approx. m²'},
    'form_sqm_placeholder': {'es': 'Ej. 30', 'en': 'e.g. 30'},
    'form_product': {'es': 'Producto de interés', 'en': 'Product of interest'},
    'form_product_unsure': {'es': 'No estoy seguro, necesito asesoría', 'en': "I'm not sure, I need advice"},
    'form_message': {'es': 'Mensaje', 'en': 'Message'},
    'form_message_placeholder': {'es': '¿Alguna duda o requerimiento especial?', 'en': 'Any questions or special requirements?'},
    'form_submit': {'es': 'Enviar cotización por WhatsApp', 'en': 'Send quote via WhatsApp'},
    'form_note': {'es': 'También puedes llamarnos o escribirnos directamente.', 'en': 'You can also call or write us directly.'},
    'contact_whatsapp': {'es': 'WhatsApp', 'en': 'WhatsApp'},
    'contact_whatsapp_note': {'es': 'Respuesta en menos de 24 h', 'en': 'Response in less than 24 h'},
    'contact_phone_mx': {'es': 'Teléfono México', 'en': 'Mexico Phone'},
    'contact_phone_us': {'es': 'Teléfono USA', 'en': 'USA Phone'},
    'contact_email': {'es': 'Correo', 'en': 'Email'},
    'contact_location': {'es': 'Ubicación', 'en': 'Location'},
    'contact_map': {'es': 'Ver en Google Maps', 'en': 'View on Google Maps'},
    'contact_hours': {'es': 'Horario', 'en': 'Hours'},
    'contact_back_home': {'es': '← Volver al Inicio', 'en': '← Back to Home'},
    'contact_form_message': {'es': 'Hola ADIS, solicito una cotización:', 'en': 'Hello ADIS, I request a quote:'},
    'contact_form_name': {'es': 'Nombre', 'en': 'Name'},
    'contact_form_phone': {'es': 'Teléfono', 'en': 'Phone'},
    'contact_form_city': {'es': 'Ciudad/Obra', 'en': 'City/Project'},
    'contact_form_sqm': {'es': 'm² aproximados', 'en': 'Approx. m²'},
    'contact_form_product': {'es': 'Producto', 'en': 'Product'},
    'contact_form_message_label': {'es': 'Mensaje', 'en': 'Message'},
    'contact_form_closing': {'es': 'Favor de contactarme. ¡Gracias!', 'en': 'Please contact me. Thank you!'},

    # Proyectos
    'projects_title': {'es': 'Proyectos Reales', 'en': 'Real Projects'},
    'projects_subtitle': {'es': 'Transformaciones que hablan por sí solas. Conoce nuestro trabajo en Nogales, Sonora y Arizona.', 'en': 'Transformations that speak for themselves. See our work in Nogales, Sonora & Arizona.'},
    'projects_cta_quote': {'es': 'Cotizar mi proyecto', 'en': 'Quote my project'},
    'projects_cta_form': {'es': 'Enviar formulario', 'en': 'Send form'},
    'projects_before': {'es': 'Antes', 'en': 'Before'},
    'projects_after': {'es': 'Después', 'en': 'After'},
    'projects_remodeling': {'es': 'Remodelación', 'en': 'Remodeling'},
    'projects_beforeafter_title': {'es': 'Antes y Después', 'en': 'Before and After'},
    'projects_gallery_title': {'es': 'Galería de Proyectos', 'en': 'Project Gallery'},
    'projects_gallery_subtitle': {'es': 'Trabajos reales con nuestros materiales de alta gama.', 'en': 'Real jobs with our high-end materials.'},
    'projects_videos_title': {'es': 'Videos de Remodelaciones', 'en': 'Remodeling Videos'},
    'projects_videos_subtitle': {'es': 'Transformaciones capturadas en video.', 'en': 'Transformations captured on video.'},
    'projects_carousel_hint': {'es': 'Desliza para ver la transformación completa.', 'en': 'Swipe to see the full transformation.'},

    # ¿Sabías que?
    'sq_title': {'es': '¿Sabías que?', 'en': 'Did you know?'},
    'sq_subtitle': {'es': 'Datos sorprendentes y respuestas a tus dudas sobre nuestros materiales.', 'en': 'Surprising facts and answers to your questions about our materials.'},
    'sq_subtitle_known': {'es': 'Conoce todo sobre <strong>{category}</strong>', 'en': 'Learn all about <strong>{category}</strong>'},
    'sq_index_title': {'es': '¿Sabías que? | ADIS Diseño & Remodelación', 'en': 'Did you know? | ADIS Design & Remodeling'},
    'sq_index_desc': {'es': 'Datos curiosos, FAQs y consejos sobre nuestros productos: PVC, WPC, paneles 3D, pisos, zacate y cladding.', 'en': 'Curious facts, FAQs and tips about our products: PVC, WPC, 3D panels, flooring, synthetic grass and cladding.'},
    'sq_breadcrumb_home': {'es': 'Inicio', 'en': 'Home'},
    'sq_breadcrumb_sq': {'es': '¿Sabías que?', 'en': 'Did you know?'},
    'sq_see_more': {'es': 'Ver datos curiosos y FAQs →', 'en': 'See facts and FAQs →'},
    'sq_card_readmore': {'es': 'Leer más', 'en': 'Read more'},
    'sq_card_readless': {'es': 'Leer menos', 'en': 'Read less'},
    'sq_back_index': {'es': '← Volver al índice', 'en': '← Back to index'},
    'sq_curiosos_title': {'es': 'Datos Curiosos', 'en': 'Curious Facts'},
    'sq_faqs_title': {'es': 'Preguntas Frecuentes', 'en': 'Frequently Asked Questions'},

    # Filtros
    'filter_all': {'es': 'Todos', 'en': 'All'},
    'filter_count_unit': {'es': 'productos', 'en': 'products'},
    'filter_count_singular': {'es': 'producto', 'en': 'product'},
    'filter_placeholder': {'es': 'Buscar producto...', 'en': 'Search products...'},

    # Modal cotizar
    'modal_title': {'es': 'Cotizar por WhatsApp', 'en': 'Quote via WhatsApp'},
    'modal_subtitle': {'es': 'Completa tus datos y te responderemos con información y asesoría.', 'en': 'Fill in your details and we will respond with information and advice.'},
    'modal_name': {'es': 'Nombre *', 'en': 'Name *'},
    'modal_name_placeholder': {'es': 'Tu nombre', 'en': 'Your name'},
    'modal_city': {'es': 'Ciudad / Ubicación de la obra *', 'en': 'City / Project location *'},
    'modal_city_placeholder': {'es': 'Ej. Nogales, Sonora', 'en': 'e.g. Nogales, Sonora'},
    'modal_sqm': {'es': 'm² aproximados', 'en': 'Approx. m²'},
    'modal_sqm_placeholder': {'es': 'Ej. 25', 'en': 'e.g. 25'},
    'modal_use': {'es': 'Uso', 'en': 'Use'},
    'modal_use_residential': {'es': 'Residencial', 'en': 'Residential'},
    'modal_use_commercial': {'es': 'Comercial', 'en': 'Commercial'},
    'modal_use_other': {'es': 'Otro', 'en': 'Other'},
    'modal_comment': {'es': 'Comentario (opcional)', 'en': 'Comment (optional)'},
    'modal_comment_placeholder': {'es': '¿Alguna duda o requerimiento especial?', 'en': 'Any questions or special requirements?'},
    'modal_submit': {'es': 'Enviar a WhatsApp', 'en': 'Send to WhatsApp'},
    'modal_message': {'es': 'Hola ADIS, soy ', 'en': 'Hello ADIS, I am '},
    'modal_message_end': {'es': '. Me interesa cotizar:', 'en': '. I am interested in quoting:'},

    # Chatbot
    'chatbot_title': {'es': 'Asistente ADIS', 'en': 'ADIS Assistant'},
    'chatbot_badge': {'es': '0', 'en': '0'},
    'chatbot_new_chat': {'es': 'Nueva conversación', 'en': 'New chat'},
    'chatbot_close': {'es': 'Cerrar', 'en': 'Close'},
    'chatbot_welcome_1': {'es': '¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>.<br><br>Soy tu asistente virtual y puedo ayudarte con información sobre nuestros productos, horarios, precios, cotizaciones y más.<br><br>¿Qué necesitas? Escribe tu pregunta 👇', 'en': 'Hello! 👋 Welcome to <strong>ADIS Design & Remodeling</strong>.<br><br>I am your virtual assistant and I can help you with information about our products, hours, prices, quotes and more.<br><br>What do you need? Type your question 👇'},
    'chatbot_welcome_2': {'es': '¡Qué tal! 👋 Soy el asistente virtual de <strong>ADIS</strong>. Estoy aquí para ayudarte con:<br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios y ubicación 🕐📍<br><br>¿En qué puedo ayudarte?', 'en': 'Hi there! 👋 I am the virtual assistant of <strong>ADIS</strong>. I am here to help you with:<br>• Products and catalog 📦<br>• Prices and quotes 💰<br>• Hours and location 🕐📍<br><br>How can I help you?'},
    'chatbot_label_measures': {'es': '📐 Medidas', 'en': '📐 Measurements'},
    'chatbot_label_water': {'es': '💧 Resistencia al agua', 'en': '💧 Water resistance'},
    'chatbot_label_exterior': {'es': '🌤️ Uso exterior/interior', 'en': '🌤️ Outdoor/indoor use'},
    'chatbot_label_material': {'es': '🧱 Material', 'en': '🧱 Material'},
    'chatbot_label_install': {'es': '🛠️ Instalación', 'en': '🛠️ Installation'},
    'chatbot_label_colors': {'es': '🎨 Colores', 'en': '🎨 Colors'},
    'chatbot_label_price': {'es': '💰 Precio', 'en': '💰 Price'},
    'chatbot_label_maintenance': {'es': '🧼 Mantenimiento', 'en': '🧼 Maintenance'},
    'chatbot_label_uses': {'es': '🏠 Usos recomendados', 'en': '🏠 Recommended uses'},
    'chatbot_label_warranty': {'es': '✅ Garantía', 'en': '✅ Warranty'},
    'chatbot_label_compare': {'es': 'Diferencias', 'en': 'Differences'},
    'chatbot_overview': {'es': '📋 <strong>Ficha técnica de', 'en': '📋 <strong>Technical sheet of'},
    'chatbot_overview_end': {'es': ':</strong><br><br>', 'en': ':</strong><br><br>'},
    'chatbot_ask_more': {'es': '¿Te gustaría saber más sobre colores, instalación o mantenimiento?', 'en': 'Would you like to know more about colors, installation or maintenance?'},
    'chatbot_hours_monday': {'es': 'Cerrado 🚪', 'en': 'Closed 🚪'},
    'chatbot_hours_tuesday': {'es': '10:00 a 19:00', 'en': '10:00 AM to 7:00 PM'},
    'chatbot_hours_wednesday': {'es': '9:00 a 19:00', 'en': '9:00 AM to 7:00 PM'},
    'chatbot_hours_thursday': {'es': '9:00 a 19:00', 'en': '9:00 AM to 7:00 PM'},
    'chatbot_hours_friday': {'es': '9:00 a 19:00', 'en': '9:00 AM to 7:00 PM'},
    'chatbot_hours_saturday': {'es': '9:00 a 19:00', 'en': '9:00 AM to 7:00 PM'},
    'chatbot_hours_sunday': {'es': '9:00 a 15:00', 'en': '9:00 AM to 3:00 PM'},
    'chatbot_fallback': {'es': 'No estoy seguro de entender tu pregunta. ¿Puedes reformularla? Puedo ayudarte con medidas, colores, precios, instalación, usos o cotizaciones. También puedes escribirnos por WhatsApp.', 'en': "I'm not sure I understand your question. Can you rephrase it? I can help with measurements, colors, prices, installation, uses or quotes. You can also write to us on WhatsApp."},
    'chatbot_no_products': {'es': 'No encontré productos para mostrarte. Intenta con otra palabra o escríbenos por WhatsApp.', 'en': 'I found no products to show you. Try another word or write to us on WhatsApp.'},
    'chatbot_quote_prompt': {'es': 'Para darte una cotización más precisa, ¿podrías decirme:<br>1. ¿Qué producto te interesa?<br>2. ¿Cuántos m² aproximados?<br>3. ¿Es para interior o exterior?<br>4. ¿En qué ciudad está el proyecto?<br><br>Con esa info te paso precios y opciones.', 'en': 'To give you a more accurate quote, could you tell me:<br>1. Which product interests you?<br>2. Approximate m²?<br>3. Indoor or outdoor?<br>4. What city is the project in?<br><br>With that info I can give you prices and options.'},
    'chatbot_greeting': {'es': '¡Hola! 👋 Puedo ayudarte con información sobre nuestros productos, precios, instalación y cotizaciones. ¿Qué necesitas?', 'en': 'Hello! 👋 I can help you with information about our products, prices, installation and quotes. What do you need?'},
    'chatbot_bye': {'es': '¡Gracias por contactarnos! Quedo atento si tienes más dudas. 😊', 'en': 'Thank you for contacting us! I remain attentive if you have more questions. 😊'},
    'chatbot_thanks': {'es': '¡Con gusto! 😊 Si necesitas más ayuda, aquí estoy.', 'en': 'Gladly! 😊 If you need more help, I am here.'},
    'chatbot_location': {'es': '📍 Nuestro showroom está en {direccion}.<br>Horario: {horario}<br>WhatsApp: {whatsapp}', 'en': '📍 Our showroom is at {direccion}.<br>Hours: {horario}<br>WhatsApp: {whatsapp}'},
    'chatbot_source': {'es': '📚 Sacado de <a href="sabias-que.html" style="color:#C5A059">¿Sabías que?</a>', 'en': '📚 From <a href="sabias-que.html" style="color:#C5A059">Did you know?</a>'},
    'chatbot_quick_questions': {'es': 'Preguntas rápidas:', 'en': 'Quick questions:'},
    'chatbot_input_placeholder': {'es': 'Escribe tu pregunta...', 'en': 'Type your question...'},
    'chatbot_view_product': {'es': 'Ver producto', 'en': 'View product'},
    'chatbot_quote': {'es': 'Cotizar', 'en': 'Quote'},
    'chatbot_qr_products': {'es': 'Ver productos', 'en': 'View products'},
    'chatbot_qr_hours': {'es': 'Horarios', 'en': 'Hours'},
    'chatbot_qr_quote': {'es': 'Cotización', 'en': 'Quote'},
    'chatbot_qr_location': {'es': 'Ubicación', 'en': 'Location'},
    'chatbot_qr_tech_sheet': {'es': 'Ver ficha técnica', 'en': 'View tech sheet'},
    'chatbot_qr_quote_product': {'es': 'Cotizar este producto', 'en': 'Quote this product'},
    'chatbot_qr_more_products': {'es': 'Ver más productos', 'en': 'View more products'},
    'chatbot_qr_advisor': {'es': 'Hablar con asesor', 'en': 'Talk to advisor'},
    'chatbot_qr_request_quote': {'es': 'Solicitar cotización', 'en': 'Request quote'},
    'chatbot_faq_label': {'es': 'Pregunta frecuente', 'en': 'Frequently asked question'},
    'chatbot_curiosity_label': {'es': 'Dato curioso', 'en': 'Curious fact'},

    # WhatsApp mensajes prellenados (se mantienen en español por operación del negocio)
    # Los textos visibles de botones sí se traducen.

    # Misc
    'wa_tooltip': {'es': 'Cotiza gratis por WhatsApp', 'en': 'Free quote via WhatsApp'},
    'breadcrumb_home': {'es': 'Inicio', 'en': 'Home'},
    'breadcrumb_catalog': {'es': 'Catálogo', 'en': 'Catalog'},

    # Navegación extendida
    'nav_about': {'es': 'Nosotros', 'en': 'About us'},
    'nav_privacy': {'es': 'Aviso de privacidad', 'en': 'Privacy notice'},

    # Página Nosotros
    'about_title': {'es': 'Nosotros', 'en': 'About us'},
    'about_subtitle': {'es': 'Diseñamos y remodelamos espacios en Nogales, Sonora y Arizona con materiales premium.', 'en': 'We design and remodel spaces in Nogales, Sonora & Arizona with premium materials.'},
    'about_hero_badge': {'es': 'ADIS Diseño & Remodelación', 'en': 'ADIS Design & Remodeling'},
    'about_history_title': {'es': 'Nuestra historia', 'en': 'Our story'},
    'about_history_text': {'es': 'Somos un equipo apasionado por transformar espacios. Desde Nogales, Sonora, atendemos proyectos residenciales y comerciales, y enviamos materiales a Arizona. Combinamos asesoría personalizada, productos de alta calidad y un servicio boutique que acompaña al cliente desde la cotización hasta la instalación.', 'en': 'We are a team passionate about transforming spaces. From Nogales, Sonora, we serve residential and commercial projects, and ship materials to Arizona. We combine personalized advice, high-quality products and boutique service that accompanies the client from quote to installation.'},
    'about_mission_title': {'es': 'Misión', 'en': 'Mission'},
    'about_mission_text': {'es': 'Crear espacios funcionales, elegantes y duraderos con recubrimientos innovadores que superen las expectativas de nuestros clientes.', 'en': 'Create functional, elegant and durable spaces with innovative coverings that exceed our clients expectations.'},
    'about_values_title': {'es': 'Valores', 'en': 'Values'},
    'about_value_quality': {'es': 'Calidad premium', 'en': 'Premium quality'},
    'about_value_service': {'es': 'Atención personalizada', 'en': 'Personalized service'},
    'about_value_commitment': {'es': 'Compromiso con el cliente', 'en': 'Commitment to the customer'},
    'about_value_binational': {'es': 'Servicio binacional', 'en': 'Binational service'},
    'about_value_quality_desc': {'es': 'Materiales duraderos y acabados que destacan.', 'en': 'Durable materials and finishes that stand out.'},
    'about_value_service_desc': {'es': 'Te acompañamos en cada etapa de tu proyecto.', 'en': 'We accompany you at every stage of your project.'},
    'about_value_binational_desc': {'es': 'Enviamos a Nogales, Sonora y Arizona.', 'en': 'We ship to Nogales, Sonora & Arizona.'},
    'about_value_commitment_desc': {'es': 'Cotización clara y respuesta en menos de 24 h.', 'en': 'Clear quote and response in less than 24 hours.'},
    'about_team_title': {'es': 'El equipo ADIS', 'en': 'The ADIS team'},
    'about_team_text': {'es': 'Un grupo de especialistas en recubrimientos, diseño de interiores y atención al cliente, listos para hacer realidad tu proyecto.', 'en': 'A group of specialists in coverings, interior design and customer service, ready to make your project a reality.'},
    'about_team_cta': {'es': 'Conoce nuestro trabajo', 'en': 'See our work'},
    'about_why_title': {'es': '¿Por qué elegir ADIS?', 'en': 'Why choose ADIS?'},
    'about_why_1_title': {'es': 'Asesoría de especialistas', 'en': 'Specialist advice'},
    'about_why_1_text': {'es': 'Te ayudamos a elegir el material ideal según tu espacio, estilo y presupuesto.', 'en': 'We help you choose the ideal material according to your space, style and budget.'},
    'about_why_2_title': {'es': 'Envío a Nogales y Arizona', 'en': 'Shipping to Nogales & Arizona'},
    'about_why_2_text': {'es': 'Entrega rápida y coordinada en ambos lados de la frontera.', 'en': 'Fast and coordinated delivery on both sides of the border.'},
    'about_why_3_title': {'es': 'Más de 250 productos', 'en': 'More than 250 products'},
    'about_why_3_text': {'es': 'Amplio catálogo de placas PVC, lambrín WPC, paneles 3D, pisos, zacate y cladding.', 'en': 'Large catalog of PVC panels, WPC slats, 3D panels, flooring, synthetic grass and cladding.'},
    'about_why_4_title': {'es': 'Proyectos reales', 'en': 'Real projects'},
    'about_why_4_text': {'es': 'Galería de trabajos terminados para que veas el acabado antes de decidir.', 'en': 'Gallery of finished work so you can see the finish before deciding.'},
    'about_cta_title': {'es': 'Hablemos de tu proyecto', 'en': "Let's talk about your project"},
    'about_cta_subtitle': {'es': 'Cotiza sin compromiso y recibe atención en menos de 24 horas.', 'en': 'Get a free quote and receive attention in less than 24 hours.'},

    # Página Aviso de privacidad
    'privacy_title': {'es': 'Aviso de Privacidad', 'en': 'Privacy Notice'},
    'privacy_subtitle': {'es': 'En ADIS Diseño & Remodelación protegemos tu información personal.', 'en': 'At ADIS Design & Remodeling we protect your personal information.'},
    'privacy_responsible_title': {'es': 'Responsable del tratamiento de datos', 'en': 'Data controller'},
    'privacy_responsible_text': {'es': "ADI'S DISEÑO & REMODELACIÓN, con domicilio en Nogales, Sonora, es responsable de recabar, usar y proteger tus datos personales.", 'en': "ADI'S DESIGN & REMODELING, located in Nogales, Sonora, is responsible for collecting, using and protecting your personal data."},
    'privacy_data_title': {'es': 'Datos que recabamos', 'en': 'Data we collect'},
    'privacy_data_text': {'es': 'Nombre, teléfono, correo electrónico, dirección del proyecto y datos necesarios para cotizar e instalar los productos contratados.', 'en': 'Name, phone, email, project address and data necessary to quote and install the contracted products.'},
    'privacy_purpose_title': {'es': 'Finalidades del uso de datos', 'en': 'Purposes of data use'},
    'privacy_purpose_text': {'es': 'Proveer cotizaciones, coordinar entregas e instalaciones, dar seguimiento a tu proyecto y enviar información promocional (solo si autorizas).', 'en': 'Provide quotes, coordinate deliveries and installations, follow up on your project and send promotional information (only if authorized).'},
    'privacy_arco_title': {'es': 'Derechos ARCO', 'en': 'ARCO rights'},
    'privacy_arco_text': {'es': 'Tienes derecho a Acceder, Rectificar, Cancelar u Oponerte al uso de tus datos. Para ejercerlos, escríbenos por WhatsApp o correo electrónico.', 'en': 'You have the right to Access, Rectify, Cancel or Oppose the use of your data. To exercise them, write to us via WhatsApp or email.'},
    'privacy_security_title': {'es': 'Seguridad de la información', 'en': 'Information security'},
    'privacy_security_text': {'es': 'Implementamos medidas administrativas, técnicas y físicas para proteger tus datos contra daño, pérdida o uso no autorizado.', 'en': 'We implement administrative, technical and physical measures to protect your data against damage, loss or unauthorized use.'},
    'privacy_changes_title': {'es': 'Cambios al aviso', 'en': 'Changes to this notice'},
    'privacy_changes_text': {'es': 'Cualquier modificación a este aviso se publicará en esta página. Te recomendamos revisarla periódicamente.', 'en': 'Any modification to this notice will be published on this page. We recommend reviewing it periodically.'},
    'privacy_contact_title': {'es': 'Contacto', 'en': 'Contact'},
    'privacy_contact_text': {'es': 'WhatsApp: {whatsapp} | Email: {email} | Ubicación: {ubicacion}', 'en': 'WhatsApp: {whatsapp} | Email: {email} | Location: {ubicacion}'},
    'privacy_effective': {'es': 'Última actualización: {date}', 'en': 'Last updated: {date}'},

    # Lead capture banner
    'lead_title': {'es': '¿Tienes un proyecto en mente?', 'en': 'Do you have a project in mind?'},
    'lead_subtitle': {'es': 'Cuéntanos qué necesitas y te asesoramos gratis por WhatsApp en menos de 24 h.', 'en': 'Tell us what you need and we will advise you for free via WhatsApp in less than 24 hours.'},
    'lead_name': {'es': 'Tu nombre', 'en': 'Your name'},
    'lead_phone': {'es': 'Teléfono', 'en': 'Phone'},
    'lead_project': {'es': '¿Qué tipo de proyecto es?', 'en': 'What type of project is it?'},
    'lead_project_placeholder': {'es': 'Ej. remodelación de sala, fachada comercial, baño...', 'en': 'E.g. living room remodel, commercial facade, bathroom...'},
    'lead_button': {'es': 'Pedir asesoría gratis', 'en': 'Request free advice'},
    'lead_note': {'es': 'Al enviar, abriremos WhatsApp con tu mensaje. Sin spam.', 'en': 'By sending, we will open WhatsApp with your message. No spam.'},
    'lead_whatsapp_msg': {'es': 'Hola ADIS, mi nombre es {name} y mi teléfono es {phone}. Tengo un proyecto de: {project}. Me gustaría recibir asesoría.', 'en': 'Hello ADIS, my name is {name} and my phone is {phone}. I have a project: {project}. I would like to receive advice.'},

    # Reviews
    'reviews_title': {'es': 'Lo que dicen nuestros clientes', 'en': 'What our customers say'},
    'reviews_subtitle': {'es': 'Reseñas verificadas de proyectos reales.', 'en': 'Verified reviews from real projects.'},
    'reviews_badge': {'es': 'Reseña verificada', 'en': 'Verified review'},
    'reviews_google_cta': {'es': 'Ver más reseñas en Google', 'en': 'See more reviews on Google'},
    'reviews_write': {'es': 'Escribir una reseña', 'en': 'Write a review'},

    # Footer legal
    'footer_links_about': {'es': 'Nosotros', 'en': 'About us'},
    'footer_links_privacy': {'es': 'Aviso de privacidad', 'en': 'Privacy notice'},
    'footer_links_legal': {'es': 'Legal', 'en': 'Legal'},

    # Títulos de página (SEO)
    'title_index': {'es': 'Recubrimientos en Nogales, Sonora · Arizona | ADIS Diseño & Remodelación', 'en': 'Wall Coverings in Nogales, Sonora · Arizona | ADIS Design & Remodeling'},
    'title_contacto': {'es': 'Cotizar Recubrimientos Nogales Sonora · Arizona | Contacto ADIS', 'en': 'Quote Wall Coverings Nogales Sonora · Arizona | Contact ADIS'},
    'title_nosotros': {'es': 'Nosotros | ADIS Diseño & Remodelación · Nogales Sonora', 'en': 'About Us | ADIS Design & Remodeling · Nogales Sonora'},
    'title_privacidad': {'es': 'Aviso de Privacidad | ADIS Diseño & Remodelación', 'en': 'Privacy Notice | ADIS Design & Remodeling'},
    'title_sabias': {'es': '¿Sabías que? | ADIS Diseño & Remodelación', 'en': 'Did You Know? | ADIS Design & Remodeling'},
    'title_proyectos': {'es': 'Proyectos Reales | ADIS Diseño & Remodelación', 'en': 'Real Projects | ADIS Design & Remodeling'},
    'sabias_meta_desc': {'es': 'Datos curiosos, FAQs y consejos sobre nuestros productos: PVC, WPC, paneles 3D, pisos, zacate y cladding.', 'en': 'Fun facts, FAQs and tips about our products: PVC, WPC, 3D panels, flooring, artificial grass and cladding.'},
    'sabias_slug_desc': {'es': 'Datos curiosos y preguntas frecuentes sobre {cat}.', 'en': 'Fun facts and frequently asked questions about {cat}.'},
    'sabias_slug_title': {'es': '{cat} — ¿Sabías que? | ADIS Diseño & Remodelación', 'en': '{cat} — Did You Know? | ADIS Design & Remodeling'},
    'proyectos_meta_desc': {'es': 'Galería de proyectos reales de ADIS Diseño & Remodelación. Antes y después, remodelaciones de interiores y exteriores.', 'en': 'Gallery of real projects by ADIS Design & Remodeling. Before and after, interior and exterior remodels.'},

    # Breadcrumbs
    'bc_home': {'es': 'Inicio', 'en': 'Home'},
    'bc_sabias': {'es': '¿Sabías que?', 'en': 'Did You Know?'},
    'bc_catalog': {'es': 'Catálogo', 'en': 'Catalog'},

    # Secciones de investigación
    'research_curiosos_sub': {'es': 'Datos curiosos sobre este material', 'en': 'Fun facts about this material'},
    'research_faqs_title': {'es': 'Preguntas Frecuentes', 'en': 'Frequently Asked Questions'},
    'research_faqs_sub': {'es': 'Respuestas a las dudas más comunes', 'en': 'Answers to the most common questions'},
}


# ========== ICONOS SVG (reemplazan emojis del sistema) ==========
# Set de iconos de trazo fino en color dorado (#C5A059) o según uso.
# Se inyectan inline para no depender de fuentes externas ni de emojis.
ICONS_SVG = {
    'whatsapp': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5a8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    'chat': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5a8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    'truck': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    'shield': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    'hands': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M17 11l-5-5-5 5M17 18l-5-5-5 5"/></svg>',
    'bolt': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    'home': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    'grid': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    'image': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
    'phone': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.56 12.56 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.56 12.56 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
    'facebook': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>',
    'robot': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>',
    'trash': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    'x': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    'bookmark': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
    'play': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>',
    'layers': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    'tree': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22v-8m0-4V2"/><path d="M12 8a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.4"/><path d="M12 8a4 4 0 0 0-4 4c0 1.5.8 2.8 2 3.4"/><path d="M12 8a6 6 0 0 1 6 6c0 2.2-1.2 4.1-3 5.1"/><path d="M12 8a6 6 0 0 0-6 6c0 2.2 1.2 4.1 3 5.1"/></svg>',
    'square': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>',
    'palette': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.062a1.63 1.63 0 0 1 1.653-1.574H16.5c2.485 0 4.5-2.015 4.5-4.5S19 2 12 2z"/></svg>',
    'ruler': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16 2l6 6L8 22l-6-6L16 2"/><path d="M7.5 10.5l2 2"/><path d="M10.5 7.5l2 2"/><path d="M13.5 4.5l2 2"/></svg>',
    'leaf': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.6C13.4 5.5 17.3 6 21 10c0 0-3 9-10 10z"/><path d="M11 20v-7"/><path d="M11 13c-2.5 0-4.5-2-4.5-4.5"/></svg>',
    'mountain': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8 16l2-4 2 4 3-6 3 6H5l3-6 2 4z"/></svg>',
    'search': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    'map-pin': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    'clock': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    'download': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    'file-text': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    'send': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    'globe': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    'menu': '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
}


def svg_icon(name, size=20, color='#C5A059'):
    """Devuelve un icono SVG inline del set propio."""
    template = ICONS_SVG.get(name, '')
    if not template:
        return ''
    return template.format(size=size, color=color)


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
SITE_URL = 'https://xn--adis-diseo-19a.com/'

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
    with open(BASE_DIR / 'traducciones_productos.json', encoding='utf-8') as _f:
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


def translate_script(page_file='index.html'):
    """Toggle ES/EN: navega a la página contraparte real (/en/ o raíz).
    Mantiene el swap JS data-i18n como respaldo para contenido dinámico."""
    if CUR_LANG == 'en':
        link = '../' + page_file
        label, aria = 'ES', 'Cambiar a español'
    else:
        link = 'en/' + page_file
        label, aria = 'EN', 'Switch to English'
    return f'''
  <!-- ADIS i18n Toggle -->
  <script>
    (function() {{
      function unescapeHtml(str) {{
        return str.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
      }}
      window.adisSetLang = function(lang) {{
        localStorage.setItem('adis_lang', lang);
        document.querySelectorAll('[data-i18n]').forEach(function(el) {{
          var raw = el.getAttribute('data-' + lang);
          if (raw === null) return;
          var text = unescapeHtml(raw);
          if (el.hasAttribute('data-i18n-html')) {{
            el.innerHTML = text;
          }} else {{
            el.textContent = text;
          }}
        }});
        if (typeof gtag === 'function') {{
          gtag('event', 'cambiar_idioma', {{ idioma: lang, location: 'translate_toggle' }});
        }}
      }};
      document.addEventListener('DOMContentLoaded', function() {{
        // La URL manda: esta página es '{CUR_LANG}'. Se sincroniza localStorage
        // para que chatbot y buscador usen el mismo idioma de la página.
        adisSetLang('{CUR_LANG}');
      }});
    }})();
  </script>
  <link rel="prefetch" href="{link}" as="document">
  <!-- End ADIS i18n Toggle -->
'''


def translate_toggle(page_file='index.html'):
    """Botón ES/EN visible en el header (arriba a la derecha), mobile-first."""
    if CUR_LANG == 'en':
        link = '../' + page_file
        label, aria, hl = 'ES', 'Cambiar a español', 'es'
    else:
        link = 'en/' + page_file
        label, aria, hl = 'EN', 'Switch to English', 'en'
    globe = svg_icon('globe', size=15, color='currentColor')
    return (f'<a id="translateToggle" class="translate-toggle" href="{link}" '
            f'hreflang="{hl}" aria-label="{aria}" title="{aria}">{globe}<span>{label}</span></a>')


def tracking_script():
    """Script de tracking de eventos para Google Analytics 4."""
    return '''
  <script>
    (function() {
      function gtagEvent(name, params) {
        if (typeof gtag === 'function') {
          gtag('event', name, params || {});
        }
      }
      
      // WhatsApp flotante
      var waFloat = document.querySelector('.whatsapp-float');
      if (waFloat) {
        waFloat.addEventListener('click', function() {
          gtagEvent('whatsapp_click', { location: 'float' });
        });
      }
      
      // Botones Cotizar por WhatsApp en tarjetas
      document.querySelectorAll('.btn-cotizar').forEach(function(btn) {
        btn.addEventListener('click', function() {
          gtagEvent('cotizar_click', { location: 'product_card' });
        });
      });
      
      // Envio del modal de cotizacion
      var waModalForm = document.getElementById('waModalForm');
      if (waModalForm) {
        waModalForm.addEventListener('submit', function() {
          gtagEvent('enviar_cotizacion', { location: 'modal' });
        });
      }
      
      // Descargas de PDF
      document.querySelectorAll('a[download]').forEach(function(link) {
        link.addEventListener('click', function() {
          gtagEvent('pdf_download', { file: link.getAttribute('href') });
        });
      });
      
      // Boton WhatsApp en hero de categoria
      document.querySelectorAll('.hero-cat-actions .btn-primary').forEach(function(btn) {
        btn.addEventListener('click', function() {
          gtagEvent('whatsapp_click', { location: 'hero_categoria' });
        });
      });
      
      // Buscador desktop
      var searchInput = document.getElementById('searchInput');
      if (searchInput) {
        searchInput.addEventListener('change', function() {
          var term = searchInput.value.trim();
          if (term) gtagEvent('busqueda', { term: term });
        });
      }
      
      // Buscador mobile
      var searchInputMobile = document.getElementById('searchInputMobile');
      if (searchInputMobile) {
        searchInputMobile.addEventListener('change', function() {
          var term = searchInputMobile.value.trim();
          if (term) gtagEvent('busqueda', { term: term, location: 'mobile' });
        });
      }
      
      // Tarjetas de categoria
      document.querySelectorAll('.cat-card').forEach(function(card) {
        card.addEventListener('click', function() {
          gtagEvent('ver_categoria', { categoria: card.querySelector('h3') ? card.querySelector('h3').textContent : '' });
        });
      });
      
      // Tarjetas de producto estrella
      document.querySelectorAll('.featured-card').forEach(function(card) {
        card.addEventListener('click', function() {
          gtagEvent('ver_producto_estrella', { producto: card.querySelector('h3') ? card.querySelector('h3').textContent : '' });
        });
      });
      
      // Links de contacto (telefono/email)
      document.querySelectorAll('a[href^="tel:"], a[href^="mailto:"]').forEach(function(link) {
        link.addEventListener('click', function() {
          gtagEvent('contacto_click', { tipo: link.getAttribute('href').split(':')[0] });
        });
      });
    })();
  </script>'''

# ========== RESEARCH DATA (from investigacion/) ==========
try:
    with open(BASE_DIR / 'investigacion_data.json', 'r', encoding='utf-8') as f:
        RESEARCH_DATA = json.load(f)
except Exception:
    RESEARCH_DATA = {}

# Versión en inglés (mismas claves de categoría, campos traducidos)
try:
    with open(BASE_DIR / 'investigacion_data_en.json', 'r', encoding='utf-8') as f:
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


def research_cat_display(cat_key):
    """Nombre visible de una categoría de investigación según idioma."""
    if CUR_LANG == 'en':
        return RESEARCH_CAT_EN.get(cat_key, cat_key.title())
    return cat_key.title()


def research_data(cat_key):
    """Datos de investigación de una categoría según idioma de generación."""
    if CUR_LANG == 'en':
        return RESEARCH_DATA_EN.get(cat_key) or RESEARCH_DATA.get(cat_key, {})
    return RESEARCH_DATA.get(cat_key, {})

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


def _webp_path_for(dst_path):
    """Devuelve rutas WebP full y 600w para una imagen destino."""
    p = Path(dst_path)
    webp = p.with_suffix('.webp')
    webp600 = p.parent / (p.stem + '-600w.webp')
    return webp, webp600


def _ensure_webp(src_path, dst_path, max_width=None, quality=85):
    """Genera una versión WebP de src_path en dst_path. Retorna True si se generó."""
    if not HAS_PIL:
        return False
    try:
        with Image.open(src_path) as im:
            im = im.convert('RGB')
            if max_width and im.width > max_width:
                ratio = max_width / im.width
                new_size = (max_width, int(im.height * ratio))
                im = im.resize(new_size, Image.LANCZOS)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst_path, 'WEBP', quality=quality, method=6)
            return True
    except Exception as e:
        print(f"  [WEBP] Error generando {dst_path}: {e}")
        return False


def _generate_image_variants(src, dst):
    """Copia imagen y genera variantes WebP si Pillow está disponible."""
    copied = _copy_if_needed(src, dst)
    if HAS_PIL:
        webp, webp600 = _webp_path_for(dst)
        if copied or not webp.exists():
            _ensure_webp(src, webp, max_width=1600, quality=82)
        if copied or not webp600.exists():
            _ensure_webp(src, webp600, max_width=600, quality=78)
    return copied


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
    
    data = research_data(research_key)
    html_parts = []
    
    # Datos curiosos
    if data.get('curiosos'):
        html_parts.append(f'''
  <section class="research-section">
    <div class="section-header">
      <h2>{t('bc_sabias')}</h2>
      <div class="divider"></div>
      <p>{t('research_curiosos_sub')}</p>
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
        html_parts.append(f'''
  <section class="research-section">
    <div class="section-header">
      <h2>{t('research_faqs_title')}</h2>
      <div class="divider"></div>
      <p>{t('research_faqs_sub')}</p>
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
    img_dir = OUTPUT_DIR / 'img'
    img_dir.mkdir(parents=True, exist_ok=True)
    
    total = 0
    webp_total = 0
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
            copied = _generate_image_variants(src, dst)
            if copied:
                total += 1
            webp, webp600 = _webp_path_for(dst)
            if webp.exists():
                webp_total += 1
        
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
                copied = _generate_image_variants(src, dst)
                if copied:
                    total += 1
                webp, webp600 = _webp_path_for(dst)
                if webp.exists():
                    webp_total += 1
    
    if errors:
        print(f"ADVERTENCIA: {len(errors)} imagenes no se pudieron copiar:")
        for e in errors[:10]:
            print(e)
    print(f"Imagenes sincronizadas: {total} nuevas/actualizadas en {img_dir}")
    print(f"Variantes WebP listas: {webp_total}")


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
  min-width: 44px; min-height: 44px; align-items: center; justify-content: center;
}
.header-actions { display: flex; align-items: center; gap: 0.9rem; }
.admin-link {
  display: flex; align-items: center; justify-content: center;
  min-width: 44px; min-height: 44px; opacity: 0.5; transition: opacity 0.25s;
}
.admin-link:hover { opacity: 1; }
.topbar {
  background: var(--gold); color: var(--black);
  text-align: center; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase;
  padding: 0.4rem 1rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
}
.topbar svg { flex-shrink: 0; }
.mobile-menu {
  position: fixed; inset: 0; z-index: 10001;
  background: rgba(15,15,15,0.98);
  display: none; flex-direction: column; align-items: center; justify-content: center;
  gap: 1.2rem; overflow-y: auto; padding: 4.5rem 1rem 2rem;
}
.mobile-menu.active { display: flex; }
.mobile-menu a {
  color: var(--white); text-decoration: none; font-size: 1.2rem;
  text-transform: uppercase; letter-spacing: 3px; font-weight: 600;
  padding: 0.5rem 1rem;
}
.mobile-menu-cats {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem;
  max-width: 360px; margin-top: 0.5rem; padding-top: 1.2rem;
  border-top: 1px solid rgba(197,160,89,0.2);
}
.mobile-menu-cats a {
  font-size: 0.68rem; letter-spacing: 1px; padding: 0.55rem 0.8rem;
  border: 1px solid rgba(197,160,89,0.35); border-radius: 999px;
  color: rgba(245,245,245,0.85); min-height: 44px;
  display: inline-flex; align-items: center;
}
.mobile-menu-lang { margin-top: 0.5rem; }
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

/* BOTÓN TRADUCTOR (en el header, arriba a la derecha - mobile first) */
.translate-toggle {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: var(--gold); color: var(--black);
  padding: 0.5rem 0.95rem; border-radius: 999px; border: none;
  font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 0.8rem;
  letter-spacing: 1px; text-decoration: none; cursor: pointer;
  box-shadow: 0 2px 14px rgba(197,160,89,0.45);
  transition: transform 0.3s, box-shadow 0.3s;
  animation: langPulse 2s ease-in-out 3;
}
.translate-toggle:hover { transform: scale(1.08); box-shadow: 0 4px 22px rgba(197,160,89,0.65); }
.translate-toggle svg { display: block; }
@keyframes langPulse {
  0%, 100% { box-shadow: 0 2px 14px rgba(197,160,89,0.45); transform: scale(1); }
  50% { box-shadow: 0 2px 26px rgba(197,160,89,0.9); transform: scale(1.07); }
}
[data-i18n] { display: inline; }

@media (max-width: 768px) {
  .translate-toggle { padding: 0.45rem 0.8rem; font-size: 0.75rem; gap: 0.3rem; letter-spacing: 0.5px; }
}

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
  max-height: 90vh; overflow-y: auto;
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
  font-size: 1rem; transition: all 0.2s;
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

/* CTA FINAL DE CATEGORÍA */
.cta-final-section { padding: 2rem; }
.cta-final-box {
  max-width: 900px; margin: 0 auto;
  background: linear-gradient(145deg, rgba(26,26,26,0.95) 0%, rgba(15,15,15,0.95) 100%);
  border: 1px solid rgba(197,160,89,0.2); border-radius: 18px;
  padding: 2.5rem 2rem; text-align: center;
}
.cta-final-box h2 { font-family: 'Playfair Display', serif; color: var(--gold-light); font-size: 1.7rem; margin-bottom: 0.8rem; }
.cta-final-box p { color: rgba(245,245,245,0.75); margin-bottom: 1.5rem; }

/* PRECIOS ORIENTATIVOS */
.prices-section { background: linear-gradient(180deg, rgba(15,15,15,0.95) 0%, rgba(26,26,26,0.9) 100%); }
.prices-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.2rem;
  max-width: 1100px; margin: 0 auto 2rem;
}
.price-card {
  background: rgba(42,42,42,0.6); border: 1px solid rgba(197,160,89,0.12);
  border-radius: 12px; padding: 1.5rem 1rem; text-align: center; transition: all 0.3s;
}
.price-card:hover { border-color: var(--gold); transform: translateY(-3px); }
.price-card h4 { color: var(--gold-light); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.6rem; }
.price-range { font-size: 1.3rem; font-weight: 800; color: var(--white); margin-bottom: 0.5rem; }
.price-range span { font-size: 0.75rem; font-weight: 600; color: var(--gold); display: block; }
.price-card p { font-size: 0.8rem; color: rgba(245,245,245,0.6); }

/* VIDEOS HOME */
.video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; max-width: 1100px; margin: 0 auto; }
.video-card { background: rgba(42,42,42,0.5); border-radius: 12px; overflow: hidden; border: 1px solid rgba(197,160,89,0.15); }
.video-card video { width: 100%; display: block; aspect-ratio: 16/9; object-fit: cover; }
.video-card-caption { padding: 0.8rem; text-align: center; font-size: 0.8rem; color: var(--gold-light); font-weight: 600; }

/* ARIZONA SECTION */
.arizona-section { background: linear-gradient(180deg, rgba(26,26,26,0.95) 0%, rgba(15,15,26,0.95) 100%); }
.arizonaz-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.2rem;
  max-width: 1000px; margin: 0 auto;
}
.arizona-card {
  background: rgba(42,42,42,0.5); border: 1px solid rgba(197,160,89,0.12);
  border-radius: 12px; padding: 1.5rem 1rem; text-align: center; transition: all 0.3s;
}
.arizona-card:hover { border-color: var(--gold); transform: translateY(-4px); }
.arizona-card span { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
.arizona-card h3 { color: var(--gold-light); font-size: 1rem; margin-bottom: 0.4rem; }
.arizona-card p { font-size: 0.8rem; color: rgba(245,245,245,0.6); }

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
  position: relative; padding: 7rem 2rem 5rem;
  text-align: center;
  background: url('media/despues 2.jpeg') center/cover no-repeat;
  z-index: 1;
}
.hero-home::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(15,15,15,0.88) 0%, rgba(15,15,15,0.65) 60%, rgba(15,15,15,0.5) 100%);
  z-index: 1;
}
.hero-video {
  position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: cover; z-index: 0;
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
  position: relative; overflow: hidden;
}
.btn-primary::after {
  content: ''; position: absolute; top: 0; left: -80%;
  width: 50%; height: 100%;
  background: linear-gradient(100deg, transparent 0%, rgba(255,255,255,0.35) 50%, transparent 100%);
  transform: skewX(-20deg);
  animation: btnShine 4.5s ease-in-out infinite;
  pointer-events: none;
}
@keyframes btnShine {
  0%, 55% { left: -80%; }
  100% { left: 180%; }
}
@media (prefers-reduced-motion: reduce) {
  .btn-primary::after { animation: none; display: none; }
}
.btn-primary:hover {
  background: transparent; color: var(--gold);
}
.btn-secondary {
  display: inline-block; padding: 0.9rem 2.5rem;
  background: transparent; color: var(--gold);
  font-size: 0.8rem; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; text-decoration: none;
  border: 2px solid var(--gold); transition: all 0.3s;
}
.btn-secondary:hover {
  background: var(--gold); color: var(--black);
}
.btn-wa { background: #25D366; color: white; border-color: #25D366; }
.btn-wa:hover { background: transparent; color: #25D366; }
.hero-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-bottom: 1rem; }
.hero-actions .btn-primary, .hero-actions .btn-secondary { margin: 0; }
.hero-note { font-size: 0.85rem; color: rgba(245,245,245,0.6); }
.hero-note a { color: var(--gold); text-decoration: underline; }
.hero-note a:hover { color: var(--gold-light); }

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

/* BENEFICIOS */
.benefits-section { background: linear-gradient(180deg, rgba(15,15,15,0.95) 0%, rgba(26,26,26,0.9) 100%); }
.benefits-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem;
  max-width: 1100px; margin: 0 auto 3rem;
}
.benefit-card {
  background: rgba(42,42,42,0.6);
  border: 1px solid rgba(197,160,89,0.12);
  border-radius: 12px;
  padding: 2rem 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
}
.benefit-card:hover {
  border-color: var(--gold);
  transform: translateY(-5px);
  background: rgba(42,42,42,0.8);
}
.benefit-icon { display: flex; justify-content: center; align-items: center; margin-bottom: 1rem; }
.benefit-icon svg { width: 44px; height: 44px; }
/* Iconos con 'pop' escalonado al hacer scroll (desktop; en móvil estáticos) */
.js-enabled .reveal .benefit-icon { opacity: 0; transform: scale(0.2) rotate(-10deg); transition: opacity 0.5s ease, transform 0.55s cubic-bezier(0.34, 1.56, 0.64, 1); }
.js-enabled .reveal.active .benefit-icon { opacity: 1; transform: scale(1) rotate(0); }
.js-enabled .reveal.active .benefit-card:nth-child(2) .benefit-icon { transition-delay: 0.12s; }
.js-enabled .reveal.active .benefit-card:nth-child(3) .benefit-icon { transition-delay: 0.24s; }
.js-enabled .reveal.active .benefit-card:nth-child(4) .benefit-icon { transition-delay: 0.36s; }
@media (max-width: 768px) {
  .js-enabled .reveal .benefit-icon { opacity: 1; transform: none; transition: none; }
}
@media (prefers-reduced-motion: reduce) {
  .js-enabled .reveal .benefit-icon { opacity: 1 !important; transform: none !important; transition: none !important; }
}
.benefit-card h3 {
  font-size: 0.9rem; color: var(--white); text-transform: uppercase;
  letter-spacing: 2px; margin-bottom: 0.6rem;
}
.benefit-card p {
  font-size: 0.82rem; color: rgba(245,245,245,0.65); line-height: 1.6;
}
.trust-banner {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 2rem;
  max-width: 900px; margin: 0 auto;
  padding: 1.5rem 2rem;
  background: rgba(197,160,89,0.08);
  border: 1px solid rgba(197,160,89,0.15);
  border-radius: 12px;
}
.trust-item { display: flex; align-items: center; gap: 0.7rem; text-align: left; }
.trust-item > svg { flex-shrink: 0; }
.trust-item span {
  display: block;
  font-family: 'Playfair Display', serif;
  font-size: 1.7rem; color: var(--gold);
  font-weight: 700; line-height: 1.1;
}
.trust-item {
  font-size: 0.75rem; color: rgba(245,245,245,0.7);
  text-transform: uppercase; letter-spacing: 1px;
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
.cat-card picture, .featured-card picture, .product-gallery picture,
.featured-product-image picture { display: block; width: 100%; height: 100%; }
.mega-item picture { display: block; width: 52px; height: 52px; flex-shrink: 0; }
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
.star-badge.new-badge {
  background: #2E9E6B; color: #fff;
  box-shadow: 0 4px 15px rgba(46,158,107,0.4);
}

/* SECCIÓN ESTRELLAS HOME */
.featured-section {
  padding: 5rem 2rem;
  position: relative; z-index: 1;
}
.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(350px, 100%), 1fr));
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

/* BREADCRUMBS */
.breadcrumbs {
  padding: 8.5rem 2rem 0;
  font-size: 0.75rem;
  color: rgba(245,245,245,0.5);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  max-width: 1200px;
  margin: 0 auto;
}
.breadcrumbs a {
  color: rgba(245,245,245,0.6);
  text-decoration: none;
  transition: color 0.3s;
}
.breadcrumbs a:hover { color: var(--gold); }
.breadcrumbs span { color: var(--gold); margin: 0 0.4rem; }
@media (max-width: 768px) { .breadcrumbs { padding-top: 7rem; } .breadcrumbs a { display: inline-block; padding: 0.6rem 0; } }

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
  padding: 10rem 2rem 3rem;
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
.footer-info a { color: var(--gold); text-decoration: none; }
.footer-info a:hover { color: var(--gold-light); text-decoration: underline; }
.footer-social a svg { width: 22px; height: 22px; }
.copyright {
  font-size: 0.7rem; color: rgba(245,245,245,0.3); letter-spacing: 2px;
  border-top: 1px solid rgba(197,160,89,0.1); padding-top: 1.5rem;
}

/* CONTACTO */
.contact-section {
  padding: 10rem 2rem 4rem;
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

/* CONTACTO LAYOUT Y FORMULARIO */
.contact-layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 3rem;
  align-items: start;
  max-width: 1200px;
  margin: 0 auto;
}
.contact-form-panel, .contact-info-panel {
  background: rgba(26,26,26,0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(197,160,89,0.12);
  border-radius: 12px;
  padding: 2rem;
}
.contact-info-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.contact-info-panel .contact-card {
  text-align: left;
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.contact-info-panel .contact-card .icon {
  font-size: 1.6rem;
  margin-bottom: 0.3rem;
}
.contact-card-note {
  font-size: 0.75rem;
  color: var(--gold);
  margin-top: 0.2rem;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.form-field {
  margin-bottom: 1rem;
}
.form-field label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(245,245,245,0.7);
  margin-bottom: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(197,160,89,0.2);
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  color: var(--white);
  font-family: 'Montserrat', sans-serif;
  font-size: 1rem;
  transition: all 0.2s;
}
.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  outline: none;
  border-color: var(--gold);
  background: rgba(255,255,255,0.08);
  box-shadow: 0 0 0 3px rgba(197,160,89,0.1);
}
.form-field input::placeholder,
.form-field textarea::placeholder {
  color: rgba(245,245,245,0.35);
}
.form-field select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23C5A059'%3E%3Cpath d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
}
.form-field select option {
  background: #1A1A1A;
  color: var(--white);
}
.form-note {
  text-align: center;
  font-size: 0.75rem;
  color: rgba(245,245,245,0.5);
  margin-top: 0.8rem;
}

/* STATS SECTION */
.stats-section {
  padding: 4rem 2rem;
  position: relative; z-index: 1;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
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
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}
.js-enabled .reveal {
  opacity: 0;
  transform: translateY(40px);
}
.js-enabled .reveal.active {
  opacity: 1;
  transform: translateY(0);
}
@media (max-width: 768px) {
  .reveal, .js-enabled .reveal, .js-enabled .reveal.active {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .reveal, .js-enabled .reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }
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
  display: flex; align-items: center; gap: 0.5rem;
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
.lightbox-nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(15,15,15,0.7); border: 1px solid var(--gold); color: var(--gold);
  font-size: 1.3rem; cursor: pointer; display: none;
  align-items: center; justify-content: center; transition: all 0.3s; z-index: 2;
}
.lightbox-nav.visible { display: flex; }
.lightbox-nav:hover { background: var(--gold); color: var(--black); }
.lightbox-nav.prev { left: 12px; }
.lightbox-nav.next { right: 12px; }
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
  padding: 10rem 2rem 4rem;
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
.breadcrumbs-page {
  display: flex; align-items: center; gap: 0.5rem; justify-content: center;
  padding: 1rem 2rem; flex-wrap: wrap; font-size: 0.75rem; color: rgba(245,245,245,0.5); text-transform: uppercase; letter-spacing: 1px;
}
.breadcrumbs-page a { color: var(--gold); text-decoration: none; transition: opacity 0.3s; }
.breadcrumbs-page a:hover { opacity: 0.7; }
.breadcrumbs-page span { color: rgba(245,245,245,0.3); }

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
  flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 0.2rem;
  color: rgba(245,245,245,0.5); text-decoration: none; font-size: 0.65rem; font-weight: 600; letter-spacing: 1px; transition: color 0.3s;
}
.mobile-bottom-nav a.active, .mobile-bottom-nav a:hover { color: var(--gold); }
.mobile-bottom-nav a span:first-child { display: flex; justify-content: center; align-items: center; }
.mobile-bottom-nav a span:first-child svg { width: 22px; height: 22px; }

/* HEADER SEARCH MEJORADO */
.search-box input { width: 220px; border-width: 2px; font-size: 0.85rem; padding: 0.55rem 2.5rem 0.55rem 1.1rem; }
.search-box input:focus { width: 320px; border-color: var(--gold); box-shadow: 0 0 20px rgba(197,160,89,0.2); }

/* MOBILE */
@media (max-width: 768px) {
  .mega-menu, .nav-dropdown { display: none; }
  .search-box input { width: 160px; font-size: 1rem; }
  .search-box input:focus { width: 220px; }
  .search-dropdown { width: calc(100vw - 40px); right: auto; left: -20px; }
  .mobile-bottom-nav { display: flex; }
  .cat-nav { flex-direction: column; }
  .spotlight-box { padding-top: 10vh; }
  nav.desktop-nav { display: none; }
  .menu-btn { display: inline-flex; }
  .hero-home { min-height: auto; padding: 7rem 1rem 1.5rem; }
  .topbar { font-size: 0.6rem; letter-spacing: 0.3px; padding: 0.35rem 0.5rem; }
  .section-wrap, .section-wrap-alt { padding: 3.5rem 1rem; }
  .featured-grid { grid-template-columns: 1fr; }
  .hero-home h1 { font-size: clamp(1.7rem, 7.5vw, 2.2rem); }
  .hero-content { padding: 1rem 0; }
  .hero-content img { height: 90px; margin-bottom: 1.2rem; }
  .hero-badge { font-size: 0.6rem; padding: 0.4rem 1rem; margin-bottom: 1rem; }
  .hero-home p { font-size: 0.95rem; margin-bottom: 1.5rem; }
  .btn-primary { padding: 0.8rem 1.8rem; font-size: 0.75rem; width: 100%; max-width: 320px; }
  .search-hero { margin-top: 1.5rem; }
  .search-hero-title { font-size: 1.1rem; }
  .search-hero-input { padding: 0.9rem 1.2rem 0.9rem 3rem; font-size: 1rem; border-width: 2px; }
  .search-hero-icon { left: 1rem; font-size: 1.2rem; }
  .search-hero-hint { font-size: 0.7rem; }
  .products-grid { grid-template-columns: 1fr; }
  .cat-grid { grid-template-columns: 1fr; }
  .info-grid { grid-template-columns: 1fr; }
  .header-inner { padding: 0.8rem 1rem; }
  .whatsapp-float { width: 50px; height: 50px; font-size: 1.5rem; }
  .wa-tooltip { display: none; }
  .chatbot-float { width: 50px; height: 50px; font-size: 1.5rem; }
  .chatbot-window { width: calc(100vw - 40px); left: 20px; }
  .stat-number { font-size: 2rem; }
  .hero-cat-bg { min-height: 32vh; padding: 7.5rem 1rem 2rem; }
  .hero-cat-bg h1 { font-size: clamp(1.8rem, 8vw, 2.5rem); }
  .hero-cat-actions { flex-direction: column; gap: 0.8rem; }
  .hero-cat-actions .btn-primary { width: 100%; }
  .product-gallery { height: auto; aspect-ratio: 4/5; background: transparent; }
  .product-card { border-radius: 12px; }
  .product-info { padding: 1rem; }
  .product-name { font-size: 1rem; margin-bottom: 0.7rem; }
  .btn-cotizar { padding: 0.7rem 1.2rem; font-size: 0.75rem; min-height: 44px; }
  .wa-modal-box { margin: 1rem; padding: 1.4rem; }
  .wa-modal-row { grid-template-columns: 1fr; }
  .cat-card { height: 260px; }
  .cat-card-overlay { padding: 1.2rem; }
  .cat-card-overlay h3 { font-size: 1.3rem; }
  .cat-card-overlay span { font-size: 0.7rem; }
  .cat-filters { padding: 0 1rem; }
  .cat-filters-inner { padding: 1rem; }
  .cat-filter-search { padding: 0.7rem 0.8rem; font-size: 1rem; }
  .cat-filter-chips { gap: 0.5rem; }
  .filter-chip { padding: 0.5rem 0.8rem; font-size: 0.75rem; min-height: 44px; display: inline-flex; align-items: center; }
  .logo img { height: 45px; }
  .mobile-bottom-nav { padding: 0.7rem 0 0.9rem; }
  .mobile-bottom-nav a { font-size: 0.7rem; gap: 0.3rem; min-height: 48px; padding: 0.4rem 0; }
  .mobile-bottom-nav a span:first-child { font-size: 1.3rem; display: flex; justify-content: center; align-items: center; }
  .mobile-bottom-nav a span:first-child svg { width: 22px; height: 22px; }
  body { padding-bottom: 130px; }
  .hero-actions { flex-direction: column; align-items: center; }
  .whatsapp-float { bottom: 108px; }
  .chatbot-float { bottom: 108px; }
  .hero-actions .btn-primary, .hero-actions .btn-secondary { width: 100%; max-width: 320px; }
  .contact-layout { grid-template-columns: 1fr; gap: 2rem; }
  .contact-form-panel, .contact-info-panel { padding: 1.5rem; }
  .form-row { grid-template-columns: 1fr; gap: 0; }
  .benefits-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .trust-banner { gap: 1rem; padding: 1rem; }
  .trust-item span { font-size: 1.3rem; }
}

@media (max-width: 480px) {
  .hero-home h1 { font-size: 1.7rem; }
  .hero-content img { height: 75px; }
  .hero-cat-bg { min-height: 28vh; }
  .hero-cat-bg h1 { font-size: 1.6rem; }
  .product-gallery { aspect-ratio: 1/1; }
  .cat-card { height: 220px; }
  .real-sheets-grid { grid-template-columns: repeat(2, 1fr); gap: 0.5rem; }
  .section-header h2 { font-size: 1.4rem; }
  .benefit-card { padding: 1.2rem 0.6rem; }
  .benefit-card h3 { font-size: 0.78rem; letter-spacing: 1px; overflow-wrap: break-word; }
  .mobile-bottom-nav a { font-size: 0.6rem; letter-spacing: 0.5px; }
  .btn-primary { padding: 0.7rem 1rem; }
  .btn-cotizar { width: 100%; }
  .subcat-section { padding: 2rem 1rem; }
  .subcat-header h3 { font-size: 1.3rem; }
  .real-sheets-section { padding: 2.5rem 1rem; }
  .real-sheets-grid { grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
  .section-header h2 { font-size: 1.6rem; }
  .contact-section { padding: 7.5rem 1rem 2rem; }
  .specs-bar { padding: 0 1rem; margin-bottom: 2rem; }
  .spec-item { padding: 1rem 0.6rem; }
}

/* PRODUCTO DESTACADO - PVC MARMOL */
.featured-product-section { padding: 5rem 2rem; background: linear-gradient(135deg, rgba(15,15,15,0.97) 0%, rgba(26,26,26,0.95) 100%); position: relative; overflow: hidden; }
.featured-product-section::before { content: ''; position: absolute; top: -50%; right: 0; width: 600px; height: 600px; background: radial-gradient(circle, rgba(197,160,89,0.08) 0%, transparent 70%); border-radius: 50%; pointer-events: none; }
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
.sq-hero { padding: 10rem 2rem 3rem; text-align: center; background: linear-gradient(135deg, rgba(15,15,15,0.95) 0%, rgba(26,26,26,0.9) 100%); position: relative; }
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

/* FOOTER LEGAL LINKS */
.footer-links { margin-top: 1.5rem; display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
.footer-links a { color: rgba(245,245,245,0.5); text-decoration: none; transition: color 0.3s; }
.footer-links a:hover { color: var(--gold); }

/* ABOUT PAGE */
.about-hero { min-height: 60vh; display: flex; align-items: center; justify-content: center; position: relative; padding: 10rem 2rem 4rem; text-align: center; background: url('media/proyecto-recepcion.jpg') center/cover no-repeat; }
.about-hero::before { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(15,15,15,0.9) 0%, rgba(15,15,15,0.7) 100%); }
.about-hero-content { position: relative; z-index: 2; max-width: 800px; }
.about-hero-content h1 { font-family: 'Playfair Display', serif; font-size: clamp(2.2rem, 5vw, 3.5rem); color: var(--white); margin-bottom: 1rem; }
.about-hero-content p { color: rgba(245,245,245,0.75); font-size: 1.1rem; max-width: 600px; margin: 0 auto; }
.about-section { padding: 5rem 2rem; max-width: 1100px; margin: 0 auto; }
.about-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 2rem; margin-top: 3rem; }
.about-card { background: rgba(42,42,42,0.5); border: 1px solid rgba(197,160,89,0.12); padding: 2rem; border-radius: 8px; text-align: center; transition: all 0.3s; }
.about-card:hover { transform: translateY(-5px); border-color: rgba(197,160,89,0.3); background: rgba(42,42,42,0.7); }
.about-card .icon { color: var(--gold); margin-bottom: 1rem; }
.about-card h3 { color: var(--white); font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.8rem; }
.about-card p { color: rgba(245,245,245,0.65); font-size: 0.88rem; line-height: 1.6; }
.about-team { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; max-width: 1000px; margin: 0 auto; }
.about-team img { width: 100%; border-radius: 8px; border: 1px solid rgba(197,160,89,0.2); }
.about-team-text h2 { color: var(--gold-light); font-family: 'Playfair Display', serif; font-size: 2rem; margin-bottom: 1rem; }
.about-team-text p { color: rgba(245,245,245,0.7); line-height: 1.7; margin-bottom: 1.5rem; }
.about-values-list { list-style: none; display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1.5rem; }
.about-values-list li { color: rgba(245,245,245,0.8); font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; }
.about-values-list li::before { content: ''; display: inline-block; width: 6px; height: 6px; background: var(--gold); border-radius: 50%; }
@media (max-width: 768px) { .about-team { grid-template-columns: 1fr; } .about-values-list { grid-template-columns: 1fr; } }

/* PRIVACY PAGE */
.privacy-section { padding: 8rem 2rem 4rem; max-width: 800px; margin: 0 auto; }
.privacy-document { background: rgba(42,42,42,0.4); border: 1px solid rgba(197,160,89,0.12); border-radius: 8px; padding: 3rem; }
.privacy-document h1 { font-family: 'Playfair Display', serif; color: var(--white); font-size: 2rem; margin-bottom: 0.5rem; }
.privacy-document .effective { color: var(--gold); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2rem; display: block; }
.privacy-document h2 { color: var(--gold-light); font-size: 1.1rem; margin: 2rem 0 0.8rem; }
.privacy-document p { color: rgba(245,245,245,0.75); line-height: 1.7; font-size: 0.92rem; margin-bottom: 1rem; }
.privacy-document ul { margin-left: 1.2rem; color: rgba(245,245,245,0.75); line-height: 1.8; font-size: 0.92rem; }
.privacy-document a { color: var(--gold); }

/* LEAD CAPTURE BANNER */
.lead-section { padding: 4rem 2rem; background: linear-gradient(135deg, rgba(197,160,89,0.08) 0%, rgba(15,15,15,0) 100%); border-top: 1px solid rgba(197,160,89,0.1); border-bottom: 1px solid rgba(197,160,89,0.1); }
.lead-container { max-width: 800px; margin: 0 auto; text-align: center; }
.lead-container h2 { font-family: 'Playfair Display', serif; color: var(--white); font-size: clamp(1.6rem, 4vw, 2.2rem); margin-bottom: 0.5rem; }
.lead-container p { color: rgba(245,245,245,0.65); margin-bottom: 2rem; }
.lead-form { display: flex; flex-direction: column; gap: 1rem; max-width: 500px; margin: 0 auto; }
.lead-form input, .lead-form textarea { padding: 0.9rem 1.2rem; background: rgba(15,15,15,0.6); border: 1px solid rgba(197,160,89,0.25); border-radius: 6px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 1rem; }
.lead-form input:focus, .lead-form textarea:focus { outline: none; border-color: var(--gold); }
.lead-form button { justify-content: center; display: inline-flex; align-items: center; gap: 0.5rem; }
.lead-note { font-size: 0.75rem; color: rgba(245,245,245,0.4); margin-top: 1rem; }

/* REVIEWS SECTION */
.reviews-section { padding: 5rem 2rem; }
.reviews-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr)); gap: 2rem; margin-top: 3rem; }
.review-card { background: rgba(42,42,42,0.5); border: 1px solid rgba(197,160,89,0.12); border-radius: 8px; padding: 2rem; position: relative; transition: all 0.3s; }
.review-card:hover { border-color: rgba(197,160,89,0.3); transform: translateY(-5px); }
.review-badge { position: absolute; top: 1rem; right: 1rem; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: var(--gold); border: 1px solid rgba(197,160,89,0.3); padding: 0.2rem 0.6rem; border-radius: 20px; }
.review-stars { color: var(--gold); font-size: 1rem; margin-bottom: 1rem; letter-spacing: 2px; }
.review-card p { color: rgba(245,245,245,0.75); font-size: 0.9rem; line-height: 1.7; margin-bottom: 1.5rem; font-style: italic; }
.review-author { color: var(--white); font-weight: 600; font-size: 0.85rem; }
.review-meta { color: rgba(245,245,245,0.5); font-size: 0.75rem; }
.reviews-cta { text-align: center; margin-top: 2.5rem; }

/* TRANSFORMACIONES REALES */
.transform-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; max-width: 1100px; margin: 0 auto 2rem; }
.transform-item { border-radius: 12px; overflow: hidden; border: 1px solid rgba(197,160,89,0.2); cursor: pointer; position: relative; aspect-ratio: 1/1; }
.transform-item picture, .transform-item img { display: block; width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }
.transform-item:hover img { transform: scale(1.07); }
.transform-item::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(15,15,15,0.35) 0%, transparent 45%); pointer-events: none; }
.transform-cta { text-align: center; }
@media (max-width: 768px) {
  .transform-grid { grid-template-columns: repeat(2, 1fr); gap: 0.7rem; }
}

/* CALCULADORA DE MATERIAL */
.calc-box { max-width: 800px; margin: 0 auto; background: rgba(26,26,26,0.8); border: 1px solid rgba(197,160,89,0.25); border-radius: 18px; padding: 2.5rem; box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
.calc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.calc-field label { display: block; font-size: 0.75rem; font-weight: 600; color: rgba(245,245,245,0.7); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.4rem; }
.calc-field input, .calc-field select { width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(197,160,89,0.25); border-radius: 10px; padding: 0.85rem 1rem; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 1rem; }
.calc-field input:focus, .calc-field select:focus { outline: none; border-color: var(--gold); box-shadow: 0 0 0 3px rgba(197,160,89,0.12); }
.calc-field select option { background: #1A1A1A; color: var(--white); }
.calc-btn { width: 100%; justify-content: center; border: none; cursor: pointer; }
.calc-result { text-align: center; margin-top: 1.8rem; padding-top: 1.8rem; border-top: 1px solid rgba(197,160,89,0.2); }
.calc-m2 { font-family: 'Playfair Display', serif; font-size: 3rem; color: var(--gold); font-weight: 700; line-height: 1; }
.calc-result p { color: rgba(245,245,245,0.7); font-size: 0.9rem; margin: 0.6rem 0 1.2rem; }
.calc-result .btn-wa { display: inline-flex; }
@media (max-width: 768px) {
  .calc-box { padding: 1.5rem; }
  .calc-grid { grid-template-columns: 1fr 1fr; }
  .calc-field:last-child { grid-column: 1 / -1; }
  .calc-m2 { font-size: 2.4rem; }
}

/* TÁCTIL: sin hover pegado + feedback :active en dispositivos touch */
@media (hover: none) {
  .product-card:hover, .cat-card:hover, .info-card:hover, .benefit-card:hover,
  .featured-card:hover, .mega-item:hover, .review-card:hover, .sq-card:hover,
  .real-sheets-item:hover { transform: none; }
  .featured-card:hover img, .cat-card:hover img, .product-gallery:hover img { transform: none; }
  .btn-primary:hover, .btn-secondary:hover, .btn-cotizar:hover, .filter-chip:hover { transform: none; }
  .product-card:active, .cat-card:active, .featured-card:active, .sq-card:active { transform: scale(0.98); }
  .btn-primary:active, .btn-secondary:active, .btn-cotizar:active, .filter-chip:active,
  .carousel-btn:active, .lightbox-nav:active { transform: scale(0.94); filter: brightness(1.15); }
}
'''


def minify_css(css):
    """Minifica CSS básico usando stdlib."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
    css = re.sub(r';}', '}', css)
    return css.strip()


def minify_html(html):
    """Minifica HTML conservando scripts y contenido inline."""
    # Eliminar comentarios HTML excepto condicionales
    html = re.sub(r'<!--(?!\[if).*?-->', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Reducir espacios entre tags
    html = re.sub(r'>\s+<', '><', html)
    return html.strip()


def generate_style():
    """Escribe el CSS completo en style.css."""
    css_path = OUTPUT_DIR / 'style.css'
    css_min = minify_css(CSS.strip())
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_min)
    print(f"  style.css generado ({len(css_min):,} caracteres)")


# ========== PARTICLES JS ==========
PARTICLES_JS = '''(function() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w, h, particles = [], rafId = null;
  const COUNT = window.innerWidth < 768 ? 30 : 70;
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
    rafId = requestAnimationFrame(animate);
  }
  // Eficiencia: no animar con reduced-motion; pausar cuando la pestaña no es visible
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduceMotion) {
    animate();
    document.addEventListener('visibilitychange', function() {
      if (document.hidden) {
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      } else if (!rafId) {
        animate();
      }
    });
  }
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
    """Envuelve un diccionario en un script JSON-LD compacto."""
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False, separators=(",", ":"))}</script>'


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


def transformations_html(images):
    """Grid de fotos reales de proyectos (UGC) con lightbox."""
    if not images:
        return ''
    items = '\n'.join(
        f'      <div class="transform-item">{picture_tag(f"media/{img}", t("trans_title"), onclick=f"openLightbox(\'{p("media/" + img)}\', \'{t("trans_title")}\')")}</div>'
        for img in images)
    return f'''  <!-- TRANSFORMACIONES REALES -->
  <section class="section-wrap-alt reveal" id="transformaciones">
    <div class="section-header">
      <h2>{i18n('trans_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('trans_subtitle')}</p>
    </div>
    <div class="transform-grid">
{items}
    </div>
    <div class="transform-cta">
      <a href="{p('proyectos.html')}" class="btn-secondary">{i18n('trans_cta')}</a>
    </div>
  </section>
'''


def calculator_html(categories, preselect=None):
    """Sección calculadora de m² con CTA a WhatsApp (i18n)."""
    options = '\n'.join(
        f'        <option value="{cat_display(c["name"])}"{" selected" if preselect and c["name"] == preselect else ""}>{cat_display(c["name"])}</option>'
        for c in categories)
    return f'''  <!-- CALCULADORA DE MATERIAL -->
  <section class="section-wrap calc-section reveal" id="calculadora">
    <div class="calc-box">
      <div class="section-header">
        <h2>{i18n('calc_title')}</h2>
        <div class="divider"></div>
        <p>{i18n('calc_subtitle')}</p>
      </div>
      <div class="calc-grid">
        <div class="calc-field"><label for="calcAlto">{i18n('calc_height')}</label><input type="number" id="calcAlto" min="0" step="0.1" placeholder="2.4" inputmode="decimal"></div>
        <div class="calc-field"><label for="calcAncho">{i18n('calc_width')}</label><input type="number" id="calcAncho" min="0" step="0.1" placeholder="3.0" inputmode="decimal"></div>
        <div class="calc-field"><label for="calcCat">{i18n('calc_product')}</label><select id="calcCat">
{options}
        </select></div>
      </div>
      <button type="button" class="btn-primary calc-btn" onclick="adisCalc()">{i18n('calc_button')}</button>
      <div class="calc-result" id="calcResult" style="display:none;">
        <div class="calc-m2"><span id="calcM2">0</span> m²</div>
        <p id="calcNote"></p>
        <a href="#" id="calcWa" class="btn-primary btn-wa" target="_blank" onclick="gtag('event','whatsapp_click',{{'location':'calculadora'}})">{i18n('cta_quote_whatsapp')}</a>
      </div>
    </div>
  </section>
  <script>
    function adisCalc() {{
      var alto = parseFloat(document.getElementById('calcAlto').value) || 0;
      var ancho = parseFloat(document.getElementById('calcAncho').value) || 0;
      var cat = document.getElementById('calcCat').value;
      var res = document.getElementById('calcResult');
      res.style.display = 'block';
      var area = alto * ancho;
      if (area <= 0) {{
        document.getElementById('calcM2').textContent = '—';
        document.getElementById('calcNote').textContent = '{t('calc_error')}';
        document.getElementById('calcWa').style.display = 'none';
        return;
      }}
      var total = Math.round(area * 1.1 * 10) / 10;
      document.getElementById('calcM2').textContent = total.toFixed(1);
      document.getElementById('calcNote').textContent = '{t('calc_note_tpl')}'.replace('{{m}}', area.toFixed(1));
      var msg = '{t('calc_wa_msg')}'.replace('{{c}}', cat).replace('{{a}}', alto).replace('{{b}}', ancho).replace('{{m}}', area.toFixed(1)).replace('{{t}}', total.toFixed(1));
      var wa = document.getElementById('calcWa');
      wa.href = 'https://wa.me/{CONTACTO['whatsapp']}?text=' + encodeURIComponent(msg);
      wa.style.display = 'inline-flex';
    }}
  </script>
'''


def modal_cotizar_html():
    """Modal único de cotización por WhatsApp. Se inyecta una vez por página."""
    return f'''
  <!-- MODAL COTIZAR WHATSAPP -->
  <div class="wa-modal" id="waModal" onclick="closeWaModal(event)">
    <div class="wa-modal-box" onclick="event.stopPropagation()">
      <button class="wa-modal-close" onclick="closeWaModal()">{svg_icon('x', size=20, color='var(--gold)')}</button>
      <h3>{i18n('modal_title')}</h3>
      <p class="wa-modal-subtitle">{i18n('modal_subtitle')}</p>
      <form id="waModalForm" onsubmit="sendWaModal(event)">
        <input type="hidden" id="waModalProduct" value="">
        <input type="hidden" id="waModalCategory" value="">
        <input type="hidden" id="waModalSubcategory" value="">
        <div class="wa-modal-field">
          <label for="waModalNombre">{i18n('modal_name')}</label>
          <input type="text" id="waModalNombre" placeholder="{t('modal_name_placeholder')}" required>
        </div>
        <div class="wa-modal-field">
          <label for="waModalCiudad">{i18n('modal_city')}</label>
          <input type="text" id="waModalCiudad" placeholder="{t('modal_city_placeholder')}" required>
        </div>
        <div class="wa-modal-row">
          <div class="wa-modal-field">
            <label for="waModalMetros">{i18n('modal_sqm')}</label>
            <input type="number" id="waModalMetros" placeholder="{t('modal_sqm_placeholder')}" min="1" step="0.1">
          </div>
          <div class="wa-modal-field">
            <label for="waModalUso">{i18n('modal_use')}</label>
            <select id="waModalUso">
              <option value="Residencial">{t('modal_use_residential')}</option>
              <option value="Comercial">{t('modal_use_commercial')}</option>
              <option value="Otro">{t('modal_use_other')}</option>
            </select>
          </div>
        </div>
        <div class="wa-modal-field">
          <label for="waModalComentario">{i18n('modal_comment')}</label>
          <textarea id="waModalComentario" rows="3" placeholder="{t('modal_comment_placeholder')}"></textarea>
        </div>
        <div class="wa-modal-product" id="waModalProductLabel"></div>
        <button type="submit" class="wa-modal-submit">{i18n('modal_submit')}</button>
      </form>
    </div>
  </div>
''' + '''
  <!-- LIGHTBOX -->
  <div class="lightbox" id="lightbox" onclick="closeLightbox(event)">
    <button class="lightbox-close" onclick="closeLightbox(event)"><svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="var(--gold)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    <img src="" alt="" id="lightboxImg">
    <button class="lightbox-nav prev" onclick="navLightbox(-1, event)" aria-label="Anterior">&#10094;</button>
    <button class="lightbox-nav next" onclick="navLightbox(1, event)" aria-label="Siguiente">&#10095;</button>
    <div class="lightbox-caption" id="lightboxCaption"></div>
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
      var msg = 'Hola ADIS, soy ' + (nombre || 'un cliente interesado') + '. Me interesa cotizar:\\nProducto: ' + product + '\\nCategoria: ' + category;
      if (subcategory) msg += '\\nSubcategoria: ' + subcategory;
      if (ciudad) msg += '\\nUbicacion de la obra: ' + ciudad;
      if (metros) msg += '\\nMetros cuadrados aproximados: ' + metros;
      msg += '\\nUso: ' + uso;
      if (comentario) msg += '\\nComentario: ' + comentario;
      msg += '\\nFavor de contactarme para mas detalles. ¡Gracias!';
      window.open('https://wa.me/' + phone + '?text=' + encodeURIComponent(msg), '_blank');
      closeWaModal();
      e.target.reset();
    }
    // Lightbox con navegación (flechas, teclado y swipe táctil)
    var lbImages = [];
    var lbIndex = 0;
    function lbCollect() {
      lbImages = [];
      document.querySelectorAll('[onclick*="openLightbox"]').forEach(function(el) {
        var m = el.getAttribute('onclick').match(/openLightbox\\('([^']*)'\\s*(?:,\\s*'([^']*)')?/);
        if (m) lbImages.push({ src: m[1], caption: m[2] || '' });
      });
    }
    function lbShow(i) {
      var item = lbImages[i];
      if (!item) return;
      document.getElementById('lightboxImg').src = item.src;
      document.getElementById('lightboxCaption').textContent = item.caption;
      var showNav = lbImages.length > 1;
      document.querySelectorAll('.lightbox-nav').forEach(function(b) {
        b.classList.toggle('visible', showNav);
      });
    }
    function openLightbox(src, caption) {
      var lb = document.getElementById('lightbox');
      if (!lb) return;
      if (!lbImages.length) lbCollect();
      lbIndex = 0;
      for (var i = 0; i < lbImages.length; i++) { if (lbImages[i].src === src) { lbIndex = i; break; } }
      lbShow(lbIndex);
      lb.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
    function navLightbox(dir, e) {
      if (e) e.stopPropagation();
      if (lbImages.length < 2) return;
      lbIndex = (lbIndex + dir + lbImages.length) % lbImages.length;
      lbShow(lbIndex);
    }
    function closeLightbox(e) {
      var lb = document.getElementById('lightbox');
      if (!lb) return;
      if (e && e.target !== e.currentTarget && !e.target.classList.contains('lightbox-close')) return;
      lb.classList.remove('active');
      document.body.style.overflow = '';
    }
    document.addEventListener('keydown', function(e) {
      var lb = document.getElementById('lightbox');
      if (!lb || !lb.classList.contains('active')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') navLightbox(-1);
      if (e.key === 'ArrowRight') navLightbox(1);
    });
    (function() {
      var lb = document.getElementById('lightbox');
      if (!lb) return;
      var x0 = null;
      lb.addEventListener('touchstart', function(e) { x0 = e.touches[0].clientX; }, { passive: true });
      lb.addEventListener('touchend', function(e) {
        if (x0 === null) return;
        var dx = e.changedTouches[0].clientX - x0;
        if (Math.abs(dx) > 40) navLightbox(dx < 0 ? 1 : -1);
        x0 = null;
      }, { passive: true });
    })();
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
    chips = [f'<button class="filter-chip active" data-subcategory="all">{i18n("filter_all")}</button>']
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
      <input type="text" class="cat-filter-search" id="catFilterSearch" placeholder="{t('filter_placeholder')}" autocomplete="off">
      <div class="cat-filter-chips">
        {''.join(chips)}
      </div>
      <div class="cat-filter-count" id="catFilterCount">{total} <span data-i18n="filter_count_unit" data-es="productos" data-en="products">productos</span></div>
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
        if (countEl) countEl.innerHTML = visible + ' <span data-i18n="filter_count_unit" data-es="productos" data-en="products">' + (visible !== 1 ? 'productos' : 'producto') + '</span>';
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


def webp_srcset(img_path):
    """Devuelve rutas WebP para una imagen relativa si existen (URL-encoded para srcset)."""
    p = Path(img_path)
    webp = p.with_suffix('.webp').as_posix().replace(' ', '%20')
    webp600 = (p.parent / (p.stem + '-600w.webp')).as_posix().replace(' ', '%20')
    return webp, webp600


def ensure_logo_webp():
    """Genera versión WebP ligera del logo (287KB PNG -> ~20-30KB WebP)."""
    if not HAS_PIL:
        return
    src = OUTPUT_DIR / 'LOGO ADIS.png'
    dst = OUTPUT_DIR / 'LOGO ADIS.webp'
    if src.exists() and (not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime):
        _ensure_webp(src, dst, max_width=320, quality=85)


def logo_tag():
    """Logo con WebP optimizado y fallback PNG (header, hero, footer)."""
    webp = p('LOGO ADIS.webp').replace(' ', '%20')
    png = p('LOGO ADIS.png')
    return (f'<picture><source srcset="{webp}" type="image/webp">'
            f'<img src="{png}" alt="ADIS Logo"></picture>')


def picture_tag(img_path, alt, loading='lazy', onclick=None, cls=''):
    """Genera un tag <picture> con fallback WebP."""
    webp_path, webp600 = webp_srcset(img_path)
    attrs = f' onclick="{onclick}"' if onclick else ''
    cls_attr = f' class="{cls}"' if cls else ''
    return f'''<picture{cls_attr}>
            <source srcset="{p(webp_path)}" type="image/webp">
            <source srcset="{p(webp600)}" media="(max-width: 600px)" type="image/webp">
            <img src="{p(img_path)}" alt="{alt}" loading="{loading}"{attrs}>
          </picture>'''


def product_card_html(prod_file, cat, sub=None):
    """Genera tarjeta de producto con CTA unificado a WhatsApp via modal."""
    prod_name = os.path.splitext(prod_file)[0]
    img_path = "img/{cat_slug}/{sub_slug}/{prod_file}".format(
        cat_slug=cat["slug"],
        sub_slug=sub["slug"] if sub else "",
        prod_file=prod_file
    ) if sub else "img/{cat_slug}/{prod_file}".format(cat_slug=cat["slug"], prod_file=prod_file)
    webp_path, webp600 = webp_srcset(img_path)
    sub_name = sub["name"] if sub else None
    sub_arg = "'" + sub_name + "'" if sub_name else "null"
    cat_name = cat["name"]
    prod_name_disp = product_display(prod_name)
    cat_name_disp = cat_display(cat_name)
    sub_name_disp = subcat_display(sub_name) if sub_name else None
    prod_name_lower = prod_name.lower()
    sub_name_lower = sub_name.lower() if sub_name else 'general'
    keywords = ' '.join(_extract_keywords(prod_name))
    button_html = f'<button type="button" class="btn-cotizar" onclick="openWaModal(\'{prod_name_disp}\', \'{cat_name_disp}\', {sub_arg})">{i18n("modal_title")}</button>'
    return f'''      <div class="product-card reveal" data-name="{prod_name_lower}" data-category="{cat_name_disp}" data-subcategory="{sub_name_lower}" data-keywords="{keywords}">
        <div class="product-gallery" onclick="openLightbox('{p(img_path)}', '{prod_name_disp}')">
          {picture_tag(img_path, prod_name_disp)}
        </div>
        <div class="product-info">
          <div class="product-name">{prod_name_disp}</div>
          <div class="product-actions">
            {button_html}
          </div>
        </div>
      </div>
'''


def generate_header(current_page='index', page_file='index.html'):
    """Genera el header HTML con mega-menu, search mejorado y toggle de idioma."""
    
    MEGA_ITEMS = [
        ('1-placas-pvc.html', 'img/1-placas-pvc/11-placas-pvc-tipo-madera/Adler.jpg', 'menu_placas_pvc'),
        ('2-lambrin-wpc.html', 'img/2-lambrin-wpc/21-lambrin-interior/AMANECHER.jpg', 'menu_lambrin_wpc'),
        ('3-revestimiento-flexible.html', 'img/3-revestimiento-flexible/CONCRETO%20Aparente.jpg', 'menu_revestimiento'),
        ('4-plafon-pvc.html', 'img/4-plafon-pvc/41-plafon-pvc-laminado/SHERWOOD.jpg', 'menu_plafon'),
        ('5-paneles-tridimensionales.html', 'img/5-paneles-tridimensionales/51-blanco/Austin.jpg', 'menu_paneles_3d'),
        ('6-vigas-pvc.html', 'img/6-vigas-pvc/61-interior/BAHIA%201.jpg', 'menu_vigas'),
        ('7-pisos.html', 'img/7-pisos/71-laminado/ACONCAGUA.jpg', 'menu_pisos'),
        ('8-zacate.html', 'img/8-zacate/81-follaje-sintetico/AMAZONAS-A.jpg', 'menu_zacate'),
        ('9-cladding.html', 'img/9-cladding/91-placa-tipo-roca/BLACK.jpg', 'menu_cladding'),
    ]
    mega_html = '\n'.join([f'        <a href="{p(u)}" class="mega-item">{picture_tag(i, t(k))}<span>{i18n(k)}</span></a>' for u, i, k in MEGA_ITEMS])
    
    SABIAS_ITEMS = [
        ('sabias-que-pvc.html', 'menu_placas_pvc'),
        ('sabias-que-wpc.html', 'menu_lambrin_wpc'),
        ('sabias-que-revestimiento.html', 'menu_revestimiento'),
        ('sabias-que-plafon.html', 'menu_plafon'),
        ('sabias-que-3d.html', 'menu_paneles_3d'),
        ('sabias-que-vigas.html', 'menu_vigas'),
        ('sabias-que-pisos.html', 'menu_pisos'),
        ('sabias-que-zacate.html', 'menu_zacate'),
        ('sabias-que-cladding.html', 'menu_cladding'),
    ]
    sabias_html = '\n'.join([f'        <a href="{p(u)}" class="dropdown-item"><span>{i18n(k)}</span></a>' for u, k in SABIAS_ITEMS])
    
    nav_links = f'''<a href="{p('index.html')}">{i18n("nav_home")}</a>
        <a href="{p('index.html#categorias')}" class="mega-trigger">{i18n("nav_catalog")}
          <div class="mega-menu">
{mega_html}
          </div>
        </a>
        <a href="{p('sabias-que.html')}" class="mega-trigger">{i18n("nav_did_you_know")}
          <div class="nav-dropdown">
{sabias_html}
          </div>
        </a>
        <a href="{p('proyectos.html')}">{i18n("nav_projects")}</a>
        <a href="{p('nosotros.html')}">{i18n("nav_about")}</a>
        <a href="{p('contacto.html')}">{i18n("nav_contact")}</a>'''
    if current_page != 'index':
        nav_links = f'''<a href="{p('index.html')}">{i18n("nav_back_home")}</a>
        <a href="{p('index.html#categorias')}" class="mega-trigger">{i18n("nav_catalog")}
          <div class="mega-menu">
{mega_html}
          </div>
        </a>
        <a href="{p('sabias-que.html')}" class="mega-trigger">{i18n("nav_did_you_know")}
          <div class="nav-dropdown">
{sabias_html}
          </div>
        </a>
        <a href="{p('proyectos.html')}">{i18n("nav_projects")}</a>
        <a href="{p('nosotros.html')}">{i18n("nav_about")}</a>
        <a href="{p('contacto.html')}">{i18n("nav_contact")}</a>'''
    mobile_cats = '\n'.join([f'      <a href="{p(u)}" onclick="toggleMenu()">{i18n(k)}</a>' for u, i, k in MEGA_ITEMS])

    return f'''  <header>
    <div class="topbar">{svg_icon('truck', size=15, color='var(--black)')}<span>{i18n('topbar_text')}</span></div>
    <div class="header-inner">
      <a href="{p('index.html')}" class="logo">{logo_tag()}</a>
      <a href="{p('admin.html')}" class="admin-link" title="Panel administrativo" aria-label="Panel administrativo">{svg_icon('shield', size=20, color='var(--gold)')}</a>
      <nav class="desktop-nav">
        {nav_links}
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="{t('search_placeholder')}" autocomplete="off" title="{t('search_hint')}">
          <button onclick="openSpotlight()">{svg_icon('search', size=18, color='var(--gold)')}</button>
          <div class="search-dropdown" id="searchDropdown"></div>
        </div>
      </nav>
      <div class="header-actions">
        {translate_toggle(page_file)}
        <button class="menu-btn" onclick="toggleMenu()">{svg_icon('menu', size=22, color='var(--gold)')}</button>
      </div>
    </div>
  </header>

  <div class="mobile-menu" id="mobileMenu">
    <button class="close-menu" onclick="toggleMenu()">{svg_icon('x', size=22, color='var(--gold)')}</button>
    <a href="{p('index.html')}" onclick="toggleMenu()">{i18n("nav_home")}</a>
    <a href="{p('index.html#categorias')}" onclick="toggleMenu()">{i18n("nav_catalog")}</a>
    <a href="{p('sabias-que.html')}" onclick="toggleMenu()">{i18n("nav_did_you_know")}</a>
    <a href="{p('proyectos.html')}" onclick="toggleMenu()">{i18n("nav_projects")}</a>
    <a href="{p('nosotros.html')}" onclick="toggleMenu()">{i18n("nav_about")}</a>
    <a href="{p('contacto.html')}" onclick="toggleMenu()">{i18n("nav_contact")}</a>
    <div class="mobile-menu-cats">
{mobile_cats}
    </div>
    <div class="mobile-menu-lang">{translate_toggle(page_file)}</div>
    <div class="search-box" style="margin-top:0.5rem;">
      <input type="text" id="searchInputMobile" placeholder="{t('search_mobile_placeholder')}" autocomplete="off" style="width:220px;">
      <button onclick="performSearchMobile()">{svg_icon('search', size=18, color='var(--gold)')}</button>
      <div class="search-dropdown" id="searchDropdownMobile"></div>
    </div>
  </div>
  
  <!-- SPOTLIGHT OVERLAY -->
  <div class="spotlight-overlay" id="spotlightOverlay" onclick="closeSpotlight(event)">
    <button class="spotlight-close" onclick="closeSpotlight(event)">{svg_icon('x', size=24, color='var(--gold)')}</button>
    <div class="spotlight-box">
      <div class="spotlight-input-wrap">
        <span class="spotlight-icon">{svg_icon('search', size=20, color='var(--gold)')}</span>
        <input type="text" class="spotlight-input" id="spotlightInput" placeholder="{t('search_placeholder')}" autocomplete="off">
      </div>
      <div class="spotlight-results" id="spotlightResults"></div>
    </div>
  </div>
'''


def generate_footer():
    chatbot_js = '''
  <script>
    var ADIS_PREFIX = '__ADIS_PREFIX__';
    var ADIS_DEFAULT_LANG = '__ADIS_LANG__';
    var ADIS_LEADS_URL = '__ADIS_LEADS_URL__';
    var ADIS_REVIEWS_URL = '__ADIS_REVIEWS_URL__';
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
      const CHATBOT_I18N = {
  'input_placeholder': {es: 'Escribe tu pregunta...', en: 'Type your question...'},
  'view_product': {es: 'Ver producto', en: 'View product'},
  'quote': {es: 'Cotizar', en: 'Quote'},
  'view_products': {es: 'Ver productos', en: 'View products'},
  'hours': {es: 'Horarios', en: 'Hours'},
  'quotation': {es: 'Cotización', en: 'Quote'},
  'location': {es: 'Ubicación', en: 'Location'},
  'view_datasheet': {es: 'Ver ficha técnica', en: 'View technical sheet'},
  'quote_this_product': {es: 'Cotizar este producto', en: 'Quote this product'},
  'view_more_products': {es: 'Ver más productos', en: 'View more products'},
  'talk_to_advisor': {es: 'Hablar con asesor', en: 'Talk to advisor'},
  'do_you_ship': {es: '¿Tienen envío?', en: 'Do you ship?'},
  'open_whatsapp': {es: 'Abrir WhatsApp', en: 'Open WhatsApp'},
  'view_on_google_maps': {es: 'Ver en Google Maps', en: 'View on Google Maps'},
  'send_quote_whatsapp': {es: 'Enviar cotización por WhatsApp', en: 'Send quote via WhatsApp'},
  'make_another_quote': {es: 'Hacer otra cotización', en: 'Make another quote'},
  'whatsapp': {es: 'WhatsApp', en: 'WhatsApp'},
  'label_measures': {es: '📐 Medidas', en: '📐 Measurements'},
  'label_water': {es: '💧 Resistencia al agua', en: '💧 Water resistance'},
  'label_exterior': {es: '🌤️ Uso exterior/interior', en: '🌤️ Outdoor/indoor use'},
  'label_material': {es: '🧱 Material', en: '🧱 Material'},
  'label_install': {es: '🛠️ Instalación', en: '🛠️ Installation'},
  'label_colors': {es: '🎨 Colores', en: '🎨 Colors'},
  'label_price': {es: '💰 Precio', en: '💰 Price'},
  'label_maintenance': {es: '🧼 Mantenimiento', en: '🧼 Maintenance'},
  'label_uses': {es: '🏠 Usos recomendados', en: '🏠 Recommended uses'},
  'label_warranty': {es: '✅ Garantía', en: '✅ Warranty'},
  'label_compare': {es: '⚖️ Diferencias', en: '⚖️ Differences'},
  'label_faq': {es: 'Pregunta frecuente', en: 'Frequently asked question'},
  'label_curiosity': {es: 'Dato curioso', en: 'Curious fact'},
  'welcome_1': {es: '¡Hola! 👋 Bienvenido a <strong>ADIS Diseño & Remodelación</strong>.<br><br>Soy tu asistente virtual y puedo ayudarte con información sobre nuestros productos, horarios, precios, cotizaciones y más.<br><br>¿Qué necesitas? Escribe tu pregunta 👇', en: 'Hello! 👋 Welcome to <strong>ADIS Design & Remodeling</strong>.<br><br>I am your virtual assistant and I can help you with information about our products, hours, prices, quotes and more.<br><br>What do you need? Type your question 👇'},
  'welcome_2': {es: '¡Qué tal! 👋 Soy el asistente virtual de <strong>ADIS</strong>. Estoy aquí para ayudarte con:<br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios y ubicación 🕐📍<br><br>¿En qué puedo ayudarte?', en: 'Hi there! 👋 I am the virtual assistant of <strong>ADIS</strong>. I am here to help you with:<br>• Products and catalog 📦<br>• Prices and quotes 💰<br>• Hours and location 🕐📍<br><br>How can I help you?'},
  'hours_title': {es: '🕐 Horarios de atención (Showroom):', en: '🕐 Showroom hours:'},
  'hours_monday_label': {es: 'Lunes:', en: 'Monday:'},
  'hours_tuesday_label': {es: 'Martes:', en: 'Tuesday:'},
  'hours_wednesday_label': {es: 'Miércoles:', en: 'Wednesday:'},
  'hours_thursday_label': {es: 'Jueves:', en: 'Thursday:'},
  'hours_friday_label': {es: 'Viernes:', en: 'Friday:'},
  'hours_saturday_label': {es: 'Sábado:', en: 'Saturday:'},
  'hours_sunday_label': {es: 'Domingo:', en: 'Sunday:'},
  'hours_monday': {es: 'Cerrado 🚪', en: 'Closed 🚪'},
  'hours_tuesday': {es: '10:00 a 19:00', en: '10:00 AM to 7:00 PM'},
  'hours_wednesday': {es: '9:00 a 19:00', en: '9:00 AM to 7:00 PM'},
  'hours_thursday': {es: '9:00 a 19:00', en: '9:00 AM to 7:00 PM'},
  'hours_friday': {es: '9:00 a 19:00', en: '9:00 AM to 7:00 PM'},
  'hours_saturday': {es: '9:00 a 19:00', en: '9:00 AM to 7:00 PM'},
  'hours_sunday': {es: '9:00 a 15:00', en: '9:00 AM to 3:00 PM'},
  'hours_whatsapp_note': {es: 'Atendemos WhatsApp casi 24/7, excepto madrugada (aprox. 00:00 - 07:00)', en: 'We attend WhatsApp almost 24/7, except early morning (approx. 00:00 - 07:00)'},
  'hours_short': {es: '🕐 <strong>Horario showroom:</strong> Martes a Domingo 10:00-19:00. Lunes cerrado.<br><br>¿Necesitas algo más?', en: '🕐 <strong>Showroom hours:</strong> Tuesday to Sunday 10:00 AM-7:00 PM. Monday closed.<br><br>Do you need anything else?'},
  'contact_title': {es: '📱 Contactos directos:', en: '📱 Direct contacts:'},
  'contact_whatsapp_label': {es: 'WhatsApp:', en: 'WhatsApp:'},
  'contact_showroom_label': {es: 'Showroom:', en: 'Showroom:'},
  'contact_email_label': {es: 'Email:', en: 'Email:'},
  'contact_open_whatsapp': {es: '💬 Abrir WhatsApp', en: '💬 Open WhatsApp'},
  'contact_short': {es: '📱 WhatsApp: {whatsapp}<br>☎️ Showroom: {tel_showroom}', en: '📱 WhatsApp: {whatsapp}<br>☎️ Showroom: {tel_showroom}'},
  'location_title': {es: '📍 ADIS Diseño & Remodelación', en: '📍 ADIS Design & Remodeling'},
  'location_address_label': {es: '🏠 Dirección:', en: '🏠 Address:'},
  'location_hours_note': {es: '🕐 Horario showroom: Martes a domingo (lunes cerrado)', en: '🕐 Showroom hours: Tuesday to Sunday (Monday closed)'},
  'location_also_serves': {es: '📍 También atendemos en <strong>Rio Rico, AZ</strong>', en: '📍 We also serve <strong>Rio Rico, AZ</strong>'},
  'location_view_map': {es: '🗺️ Ver en Google Maps →', en: '🗺️ View on Google Maps →'},
  'location_short': {es: '📍 {direccion}<br><br>🕐 Martes a domingo 10:00-19:00', en: '📍 {direccion}<br><br>🕐 Tuesday to Sunday 10:00 AM-7:00 PM'},
  'price_title': {es: '💰 Precios y cotizaciones:', en: '💰 Prices and quotes:'},
  'price_includes_iva': {es: 'Todos los precios incluyen IVA', en: 'All prices include VAT'},
  'price_wholesale': {es: 'Ofrecemos descuento a mayorista', en: 'We offer wholesale discount'},
  'price_material_only': {es: 'Los precios son <strong>solo por el material</strong> (por pieza, caja o metro cuadrado según categoría)', en: 'Prices are <strong>for material only</strong> (per piece, box or square meter depending on category)'},
  'price_quote_detail': {es: '📋 Cotización detallada:', en: '📋 Detailed quote:'},
  'price_quote_includes': {es: '📦 Incluye:', en: '📦 Includes:'},
  'price_quote_no_stock': {es: '⏱️ Sin stock:', en: '⏱️ Out of stock:'},
  'price_install_question': {es: '🔨 ¿Requieres instalación? Un representante visita tu obra para cotizarla aparte.', en: '🔨 Do you need installation? A representative visits your site to quote it separately.'},
  'price_request_quote': {es: '📱 Solicitar cotización gratis', en: '📱 Request free quote'},
  'price_short': {es: '💰 Los precios varían por material y modelo.<br><br>✅ Cotización gratis por WhatsApp con respuesta en menos de 24 horas.', en: '💰 Prices vary by material and model.<br><br>✅ Free quote via WhatsApp with response in less than 24 hours.'},
  'shipping_title': {es: '🚚 Envíos y entregas:', en: '🚚 Shipping and delivery:'},
  'shipping_free': {es: '🎁 Entrega GRATIS en: {zonas}', en: '🎁 FREE delivery in: {zonas}'},
  'shipping_national': {es: '📦 Enviamos a todo México. El costo corre por cuenta del cliente.', en: '📦 We ship throughout Mexico. Cost is borne by the customer.'},
  'shipping_large_orders': {es: '⏱️ {tiempo} para pedidos grandes', en: '⏱️ {tiempo} for large orders'},
  'shipping_quote_address': {es: 'Envíanos tu dirección por WhatsApp para cotizar el envío exacto.', en: 'Send us your address via WhatsApp to quote exact shipping.'},
  'shipping_quote_button': {es: '📱 Cotizar envío', en: '📱 Quote shipping'},
  'shipping_short': {es: '🚚 Envío GRATIS en Nogales y Rio Rico. A otras ciudades cotizamos por WhatsApp.', en: '🚚 FREE shipping in Nogales and Rio Rico. To other cities we quote via WhatsApp.'},
  'install_title': {es: '🛠️ Servicio de instalación:', en: '🛠️ Installation service:'},
  'install_cost_note': {es: 'Los precios son solo por el material. La instalación se cotiza aparte.', en: 'Prices are for material only. Installation is quoted separately.'},
  'install_process': {es: '👷 Un representante visita tu obra para medir y cotizar la instalación.', en: '👷 A representative visits your site to measure and quote installation.'},
  'install_tips_title': {es: '💡 Consejos para instalación:', en: '💡 Installation tips:'},
  'install_tips': {es: '• Superficie limpia, seca y nivelada<br>• Temperatura ideal: 15°C a 30°C<br>• Dejar junta de dilatación de 2-3 mm<br>• Corte con sierra circular / disco de carburo de tungsteno<br>• Para espejos: usar perfiles de aluminio obligatoriamente', en: '• Clean, dry and level surface<br>• Ideal temperature: 15°C to 30°C<br>• Leave 2-3 mm expansion joint<br>• Cut with circular saw / tungsten carbide disc<br>• For mirrors: aluminum profiles are mandatory'},
  'install_also_sell_materials': {es: '✅ También vendemos materiales sueltos si prefieres instalar por tu cuenta.', en: '✅ We also sell loose materials if you prefer to install yourself.'},
  'install_quote_button': {es: '📱 Cotizar instalación', en: '📱 Quote installation'},
  'payment_title': {es: '💳 Formas de pago:', en: '💳 Payment methods:'},
  'payment_credit_card': {es: 'Tarjeta de crédito', en: 'Credit card'},
  'payment_debit_card': {es: 'Tarjeta de débito', en: 'Debit card'},
  'payment_transfer': {es: 'Transferencia bancaria', en: 'Bank transfer'},
  'payment_cash': {es: 'Efectivo', en: 'Cash'},
  'payment_advance': {es: 'Pedidos mayores a $10,000 requieren 50% de anticipo', en: 'Orders over $10,000 require 50% advance payment'},
  'payment_write_us': {es: 'Escríbenos para más detalles.', en: 'Write to us for more details.'},
  'payment_ask_button': {es: '📱 Preguntar por pagos', en: '📱 Ask about payments'},
  'warranty_title': {es: '✅ Garantía:', en: '✅ Warranty:'},
  'warranty_validation': {es: '🛡️ ADIS Diseño hace válida la garantía del fabricante', en: '🛡️ ADIS Design honors the manufacturer warranty'},
  'warranty_keep_ticket': {es: 'La garantía cubre defectos de fábrica. Conserva tu ticket de compra.', en: 'Warranty covers factory defects. Keep your purchase receipt.'},
  'catalog_title': {es: '📦 Nuestros productos (250 productos en 9 categorías):', en: '📦 Our products (250 products in 9 categories):'},
  'catalog_list': {es: '• <strong>Placas PVC</strong> — 34 productos<br>• <strong>Lambrín WPC</strong> — 40 productos<br>• <strong>Paneles 3D</strong> — 24 productos<br>• <strong>Pisos</strong> — 78 productos<br>• <strong>Plafón PVC</strong> — 15 productos<br>• <strong>Vigas PVC/WPC</strong> — 15 productos<br>• <strong>Zacate sintético</strong> — 29 productos<br>• <strong>Cladding</strong> — 11 productos<br>• <strong>Revestimiento Flexible</strong> — 6 productos', en: '• <strong>PVC Panels</strong> — 34 products<br>• <strong>WPC Slats</strong> — 40 products<br>• <strong>3D Panels</strong> — 24 products<br>• <strong>Flooring</strong> — 78 products<br>• <strong>PVC Ceilings</strong> — 15 products<br>• <strong>PVC/WPC Beams</strong> — 15 products<br>• <strong>Synthetic Grass</strong> — 29 products<br>• <strong>Cladding</strong> — 11 products<br>• <strong>Flexible Cladding</strong> — 6 products'},
  'catalog_hint': {es: '💡 Escribe el nombre de un producto o categoría para saber más.', en: '💡 Type the name of a product or category to learn more.'},
  'maintenance_title': {es: '🧼 Mantenimiento y limpieza:', en: '🧼 Maintenance and cleaning:'},
  'maintenance_regular': {es: '• <strong>Limpieza regular:</strong> Paño suave humedecido con agua tibia y jabón neutro (pH 7)', en: '• <strong>Regular cleaning:</strong> Soft cloth dampened with warm water and neutral soap (pH 7)'},
  'maintenance_stains': {es: '• <strong>Manchas difíciles:</strong> Alcohol isopropílico al 70% o limpiador multiusos suave', en: '• <strong>Stubborn stains:</strong> 70% isopropyl alcohol or mild multi-purpose cleaner'},
  'maintenance_avoid': {es: '• <strong>Evitar:</strong> Acetona, thinner, solventes fuertes, estropajos metálicos y amoníaco concentrado', en: '• <strong>Avoid:</strong> Acetone, thinner, strong solvents, metal scouring pads and concentrated ammonia'},
  'maintenance_frequency': {es: '• <strong>Frecuencia:</strong> Residencial = mensual | Comercial = semanal', en: '• <strong>Frequency:</strong> Residential = monthly | Commercial = weekly'},
  'maintenance_annual': {es: '• <strong>Inspección anual:</strong> Revisar juntas de dilatación y selladores', en: '• <strong>Annual inspection:</strong> Check expansion joints and sealants'},
  'maintenance_no_seal': {es: '💡 Los productos PVC y WPC no requieren barnizado ni sellado. Solo limpieza básica.', en: '💡 PVC and WPC products do not require varnishing or sealing. Just basic cleaning.'},
  'maintenance_ask_button': {es: '📱 Preguntar por mantenimiento', en: '📱 Ask about maintenance'},
  'projects_title': {es: '🏠 Atendemos todo tipo de proyectos:', en: '🏠 We serve all kinds of projects:'},
  'projects_description': {es: 'Desde una pared de acento en casa hasta remodelaciones completas de locales comerciales. Cada proyecto es único y tenemos el material perfecto para ti.', en: 'From an accent wall at home to complete commercial space remodelings. Every project is unique and we have the perfect material for you.'},
  'projects_tip_title': {es: '💡 Consejo:', en: '💡 Tip:'},
  'projects_tip': {es: 'Si no estás seguro de qué material elegir, contame:<br>• ¿Es interior o exterior?<br>• ¿Hay humedad o contacto con agua?<br>• ¿Qué estética buscas? (madera, mármol, moderno, rústico)', en: 'If you are not sure which material to choose, tell me:<br>• Is it indoor or outdoor?<br>• Is there humidity or water contact?<br>• What look are you going for? (wood, marble, modern, rustic)'},
  'projects_share_button': {es: '📱 Contar mi proyecto', en: '📱 Tell us about my project'},
  'thanks': {es: '¡Con mucho gusto! 😊🙌 Estoy aquí para lo que necesites. Si tienes más dudas, escríbenos por WhatsApp al <strong>{whatsapp}</strong> o visítanos en el showroom. ¡Que tengas un excelente día!', en: 'Gladly! 😊🙌 I am here for whatever you need. If you have more questions, write to us on WhatsApp at <strong>{whatsapp}</strong> or visit our showroom. Have a great day!'},
  'bye': {es: '¡Hasta luego! 👋 Gracias por contactar a ADIS Diseño & Remodelación. Recuerda que puedes volver cuando quieras o escribirnos al WhatsApp. ¡Éxito con tu proyecto! 🏠✨', en: 'Goodbye! 👋 Thank you for contacting ADIS Design & Remodeling. Remember you can come back anytime or write to us on WhatsApp. Success with your project! 🏠✨'},
  'negation': {es: 'Perfecto, ¿en qué más puedo ayudarte? Puedo:<br>• Mostrarte productos 📦<br>• Darte precios 💰<br>• Contarte horarios 🕐<br>• Explicarte envíos 📍<br>• Ayudarte con una cotización 📝', en: 'Great, what else can I help you with? I can:<br>• Show you products 📦<br>• Give you prices 💰<br>• Tell you our hours 🕐<br>• Explain shipping 📍<br>• Help you with a quote 📝'},
  'help': {es: '¡Claro! Puedo ayudarte con:<br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Formas de pago 💳<br>• Instalación 🛠️<br><br>Escribe tu pregunta o usa los botones de abajo.', en: 'Of course! I can help you with:<br>• Products and catalog 📦<br>• Prices and quotes 💰<br>• Business hours 🕐<br>• Location and shipping 📍<br>• Payment methods 💳<br>• Installation 🛠️<br><br>Type your question or use the buttons below.'},
  'fallback': {es: 'Disculpa, no entendí muy bien. 😅 Puedo ayudarte con:<br><br>• Productos y catálogo 📦<br>• Precios y cotizaciones 💰<br>• Horarios de atención 🕐<br>• Ubicación y envíos 📍<br>• Formas de pago 💳<br>• Instalación 🛠️<br><br>Escribe tu pregunta o usa los botones de abajo.', en: 'Sorry, I didn\\'t quite understand. 😅 I can help you with:<br><br>• Products and catalog 📦<br>• Prices and quotes 💰<br>• Business hours 🕐<br>• Location and shipping 📍<br>• Payment methods 💳<br>• Installation 🛠️<br><br>Type your question or use the buttons below.'},
  'def_pvc_title': {es: '📜 ¿Qué es PVC?', en: '📜 What is PVC?'},
  'def_pvc_text': {es: 'Policloruro de Vinilo. Es un tipo de plástico muy usado en letreros, hojas rígidas, tuberías, anuncios y materiales de impresión porque es resistente, ligero y económico.', en: 'Polyvinyl Chloride. It is a type of plastic widely used in signs, rigid sheets, pipes, advertisements and printing materials because it is resistant, lightweight and economical.'},
  'def_pvc_usage': {es: 'En ADIS lo usamos para placas decorativas, plafones y vigas con acabados que imitan madera, espejo y texturas.', en: 'At ADIS we use it for decorative panels, ceilings and beams with finishes that imitate wood, mirror and textures.'},
  'def_wpc_title': {es: '📗 ¿Qué es WPC?', en: '📗 What is WPC?'},
  'def_wpc_text': {es: 'Wood Plastic Composite (Compuesto de Madera y Plástico). Es un material hecho de fibras de madera mezcladas con plástico, muy usado en paneles, revestimientos, muebles y decoración porque parece madera pero resiste mejor la humedad y el desgaste.', en: 'Wood Plastic Composite. It is a material made of wood fibers mixed with plastic, widely used in panels, cladding, furniture and decoration because it looks like wood but resists moisture and wear better.'},
  'def_wpc_usage': {es: 'En ADIS lo usamos para lambrín de interior y exterior, pisos y revestimientos que lucen como madera real pero duran más.', en: 'At ADIS we use it for indoor and outdoor slats, flooring and cladding that look like real wood but last longer.'},
  'def_ask': {es: '📜 Puedo explicarte qué es <strong>PVC</strong>, <strong>WPC</strong>, <strong>SPC</strong>, <strong>laminado</strong> o <strong>cladding</strong>. ¿Cuál te interesa?', en: '📜 I can explain what <strong>PVC</strong>, <strong>WPC</strong>, <strong>SPC</strong>, <strong>laminate</strong> or <strong>cladding</strong> is. Which one interests you?'},
  'water_pvc_title': {es: '💧 Resistencia al agua — {name}:', en: '💧 Water resistance — {name}:'},
  'water_pvc_points': {es: '• 100% impermeable y resistente a la humedad<br>• No absorbe agua, no se hincha ni se deforma<br>• Ideal para baños, cocinas y áreas húmedas<br>• Resistente a moho y hongos<br>• Limpieza fácil con paño húmedo', en: '• 100% waterproof and moisture resistant<br>• Does not absorb water, swell or deform<br>• Ideal for bathrooms, kitchens and humid areas<br>• Resistant to mold and fungi<br>• Easy cleaning with damp cloth'},
  'water_pvc_tip': {es: '💡 <strong>¿Se puede mojar?</strong> Sí, perfectamente. Solo evita sumergir los perfiles de aluminio si lleva espejo.', en: '💡 <strong>Can it get wet?</strong> Yes, perfectly. Just avoid submerging the aluminum profiles if it has mirror finish.'},
  'water_wpc_title': {es: '💧 Resistencia al agua — {name}:', en: '💧 Water resistance — {name}:'},
  'water_wpc_points': {es: '• Absorción de agua menor al 1%<br>• No se hincha, no se cuartea, no se deforma<br>• Resistente a humedad, lluvia y rayos UV<br>• Ideal para exteriores y fachadas', en: '• Water absorption less than 1%<br>• Does not swell, crack or deform<br>• Resistant to moisture, rain and UV rays<br>• Ideal for outdoors and facades'},
  'water_wpc_tip': {es: '💡 <strong>¿Se puede mojar?</strong> Sí, está diseñado para intemperie.', en: '💡 <strong>Can it get wet?</strong> Yes, it is designed for outdoor weather.'},
  'water_floor_title': {es: '💧 Resistencia al agua — {name}:', en: '💧 Water resistance — {name}:'},
  'water_floor_points': {es: '• SPC: 100% impermeable, ideal baños y cocinas<br>• WPC: Resistente al agua, ideal recámaras<br>• Laminado: Resistente a salpicaduras, no sumergible', en: '• SPC: 100% waterproof, ideal for bathrooms and kitchens<br>• WPC: Water resistant, ideal for bedrooms<br>• Laminate: Resistant to splashes, not submersible'},
  'water_floor_tip': {es: '💡 Dime para qué espacio lo necesitas y te recomiendo el mejor.', en: '💡 Tell me what space you need it for and I will recommend the best one.'},
  'water_generic_title': {es: '💧 Resistencia al agua — {name}:', en: '💧 Water resistance — {name}:'},
  'water_generic_text': {es: 'Consulta la ficha técnica de cada modelo en el catálogo. La mayoría de nuestros materiales son resistentes a la humedad.', en: 'Check the technical sheet for each model in the catalog. Most of our materials are resistant to moisture.'},
  'water_overview_title': {es: '💧 Resistencia al agua por material:', en: '💧 Water resistance by material:'},
  'water_overview_points': {es: '• <strong>Placas PVC:</strong> 100% impermeables<br>• <strong>Lambrín WPC:</strong> Absorción <1%, ideal exterior<br>• <strong>Pisos SPC:</strong> 100% impermeables<br>• <strong>Cladding:</strong> Resistente a lluvia y UV<br>• <strong>Zacate sintético:</strong> Drenaje integrado', en: '• <strong>PVC Panels:</strong> 100% waterproof<br>• <strong>WPC Slats:</strong> Absorption <1%, ideal outdoors<br>• <strong>SPC Flooring:</strong> 100% waterproof<br>• <strong>Cladding:</strong> Resistant to rain and UV<br>• <strong>Synthetic Grass:</strong> Integrated drainage'},
  'water_overview_tip': {es: '💡 Dime qué producto te interesa y te doy los detalles específicos.', en: '💡 Tell me which product interests you and I will give you the specific details.'},
  'uses_title': {es: '🏠 Usos recomendados — {name}:', en: '🏠 Recommended uses — {name}:'},
  'uses_overview_title': {es: '🏠 Usos por material:', en: '🏠 Uses by material:'},
  'uses_overview_points': {es: '• <strong>Placas PVC:</strong> Muros interiores (baños, cocinas, salas, recepciones)<br>• <strong>Lambrín WPC:</strong> Muros interior y exterior, fachadas<br>• <strong>Pisos SPC/WPC:</strong> Interiores residenciales y comerciales<br>• <strong>Plafón PVC:</strong> Techos y cielos falsos<br>• <strong>Paneles 3D:</strong> Muros de acento, fondos de TV<br>• <strong>Vigas:</strong> Decoración de techos y pérgolas<br>• <strong>Zacate:</strong> Jardines, terrazas, balcones<br>• <strong>Cladding:</strong> Fachadas, muros exteriores', en: '• <strong>PVC Panels:</strong> Indoor walls (bathrooms, kitchens, living rooms, receptions)<br>• <strong>WPC Slats:</strong> Indoor and outdoor walls, facades<br>• <strong>SPC/WPC Flooring:</strong> Residential and commercial interiors<br>• <strong>PVC Ceilings:</strong> Ceilings and drop ceilings<br>• <strong>3D Panels:</strong> Accent walls, TV backdrops<br>• <strong>Beams:</strong> Ceiling and pergola decoration<br>• <strong>Synthetic Grass:</strong> Gardens, terraces, balconies<br>• <strong>Cladding:</strong> Facades, exterior walls'},
  'uses_tip': {es: '💡 Dime para qué espacio lo necesitas y te recomiendo el mejor material.', en: '💡 Tell me what space you need it for and I will recommend the best material.'},
  'no_data_for_product': {es: '🤔 No tengo ese dato confirmado en la información de <strong>{name}</strong>, pero puedo ayudarte a contactar a un asesor para validarlo.<br><br>📱 <strong>{whatsapp}</strong><br><br>Un experto te responderá en menos de 24 horas.', en: '🤔 I don\\'t have that data confirmed for <strong>{name}</strong>, but I can help you contact an advisor to verify it.<br><br>📱 <strong>{whatsapp}</strong><br><br>An expert will answer in less than 24 hours.'},
  'found_products': {es: '🔎 <strong>Encontré estos productos:</strong><br><br>{cards}{urgency}<br>¿Te gustaría cotizar alguno?', en: '🔎 <strong>I found these products:</strong><br><br>{cards}{urgency}<br>Would you like to quote any of them?'},
  'other_options': {es: '✨ <strong>Otras opciones similares:</strong><br><br>{cards}<br>¿Alguna de estas te interesa?', en: '✨ <strong>Other similar options:</strong><br><br>{cards}<br>Does any of these interest you?'},
  'product_info': {es: 'Aquí tienes más información de <strong>{name}</strong>:<br><br>{card}', en: 'Here is more information about <strong>{name}</strong>:<br><br>{card}'},
  'urgent_msg': {es: '<br>⚡ <strong>Entrega urgente:</strong> Si tu material está en stock, puede salir hoy mismo. Si no, el tiempo de reposición es de 2-5 días hábiles. Escríbenos por WhatsApp para confirmar disponibilidad.', en: '<br>⚡ <strong>Urgent delivery:</strong> If your material is in stock, it can ship today. If not, restocking time is 2-5 business days. Write to us on WhatsApp to confirm availability.'},
  'urgent_add': {es: '<br><br>⚡ <strong>Urgente:</strong> Si necesitas el material rápido, escríbenos al WhatsApp para confirmar stock inmediatamente.', en: '<br><br>⚡ <strong>Urgent:</strong> If you need the material quickly, write to us on WhatsApp to confirm stock immediately.'},
  'urgent_fallback': {es: '⚡ Entiendo que lo necesitas con urgencia.<br><br>📱 Te recomiendo escribirnos directo al WhatsApp <strong>{whatsapp}</strong> para confirmar stock y tiempos de entrega inmediatamente.<br><br>También puedo ayudarte a hacer una cotización guiada.', en: '⚡ I understand you need it urgently.<br><br>📱 I recommend writing directly to WhatsApp <strong>{whatsapp}</strong> to confirm stock and delivery times immediately.<br><br>I can also help you with a guided quote.'},
  'which_product': {es: '🤔 Para darte la información correcta, ¿sobre qué producto necesitas saber?<br><br>• <strong>Placas PVC</strong><br>• <strong>Lambrín WPC</strong><br>• <strong>Pisos</strong><br>• <strong>Plafón PVC</strong><br>• <strong>Paneles 3D</strong><br>• <strong>Vigas</strong><br>• <strong>Cladding</strong><br>• <strong>Zacate</strong><br>• <strong>Revestimiento Flexible</strong>', en: '🤔 To give you the correct information, which product do you need to know about?<br><br>• <strong>PVC Panels</strong><br>• <strong>WPC Slats</strong><br>• <strong>Flooring</strong><br>• <strong>PVC Ceilings</strong><br>• <strong>3D Panels</strong><br>• <strong>Beams</strong><br>• <strong>Cladding</strong><br>• <strong>Synthetic Grass</strong><br>• <strong>Flexible Cladding</strong>'},
  'price_context': {es: 'Los precios varían por modelo y acabado.{price_info}<br><br>✅ Envío gratis en Nogales y Rio Rico. Mayoreo desde 10 cajas.<br><br>¿Te gustaría una cotización exacta?', en: 'Prices vary by model and finish.{price_info}<br><br>✅ Free shipping in Nogales and Rio Rico. Wholesale from 10 boxes.<br><br>Would you like an exact quote?'},
  'price_range_info': {es: '<br><br>💰 Rango de estos modelos: <strong>{price}</strong> por {unit}.', en: '<br><br>💰 Price range for these models: <strong>{price}</strong> per {unit}.'},
  'rejection': {es: 'Entendido. 😊 ¿Qué tipo de acabado o material te gustaría explorar?<br><br>Puedo mostrarte:<br>• Diseños tipo madera 🪵<br>• Acabados tipo mármol 🏛️<br>• Texturas modernas 🎨<br>• Opciones en espejo ✨<br>• Colores específicos 🎨<br><br>Dime qué tienes en mente.', en: 'Understood. 😊 What type of finish or material would you like to explore?<br><br>I can show you:<br>• Wood designs 🪵<br>• Marble finishes 🏛️<br>• Modern textures 🎨<br>• Mirror options ✨<br>• Specific colors 🎨<br><br>Tell me what you have in mind.'},
  'quote_flow_start': {es: '📝 <strong>Cotización guiada</strong><br><br>Te voy a hacer unas preguntas para armar tu cotización. Al final podrás enviarla por WhatsApp con todos los detalles.<br><br><strong>Paso 1 de 6:</strong> ¿Qué producto o categoría te interesa?', en: '📝 <strong>Guided quote</strong><br><br>I will ask you a few questions to build your quote. At the end you can send it via WhatsApp with all the details.<br><br><strong>Step 1 of 6:</strong> What product or category interests you?'},
  'quote_step': {es: '✅ {field}: <strong>{value}</strong><br><br><strong>{step}:</strong> {question}', en: '✅ {field}: <strong>{value}</strong><br><br><strong>{step}:</strong> {question}'},
  'quote_field_product': {es: 'Producto', en: 'Product'},
  'quote_field_space': {es: 'Espacio', en: 'Space'},
  'quote_field_m2': {es: 'Metraje', en: 'Square meters'},
  'quote_field_install': {es: 'Instalación', en: 'Installation'},
  'quote_field_location': {es: 'Ubicación', en: 'Location'},
  'quote_step_2': {es: 'Paso 2 de 6', en: 'Step 2 of 6'},
  'quote_step_3': {es: 'Paso 3 de 6', en: 'Step 3 of 6'},
  'quote_step_4': {es: 'Paso 4 de 6', en: 'Step 4 of 6'},
  'quote_step_5': {es: 'Paso 5 de 6', en: 'Step 5 of 6'},
  'quote_step_6': {es: 'Paso 6 de 6', en: 'Step 6 of 6'},
  'quote_question_space': {es: '¿Para qué espacio lo necesitas?', en: 'What space do you need it for?'},
  'quote_question_m2': {es: '¿Aproximadamente cuántos metros cuadrados necesitas?', en: 'Approximately how many square meters do you need?'},
  'quote_question_install': {es: '¿Necesitas instalación?', en: 'Do you need installation?'},
  'quote_question_location': {es: '¿En qué ciudad/colonia será la obra?', en: 'In what city/neighborhood will the project be?'},
  'quote_question_contact': {es: '¿Cuál es tu nombre y teléfono? (opcional)', en: 'What is your name and phone? (optional)'},
  'quote_summary': {es: '📋 <strong>Resumen de tu cotización:</strong><br><br>• <strong>Producto:</strong> {category}<br>• <strong>Espacio:</strong> {space}<br>• <strong>Metraje:</strong> {m2}<br>• <strong>Instalación:</strong> {install}<br>• <strong>Ubicación:</strong> {location}<br>{contact}✅ Revisa que todo esté correcto y envía la cotización por WhatsApp. Un asesor te responderá en menos de 24 horas.', en: '📋 <strong>Quote summary:</strong><br><br>• <strong>Product:</strong> {category}<br>• <strong>Space:</strong> {space}<br>• <strong>Square meters:</strong> {m2}<br>• <strong>Installation:</strong> {install}<br>• <strong>Location:</strong> {location}<br>{contact}✅ Please review that everything is correct and send the quote via WhatsApp. An advisor will respond in less than 24 hours.'},
  'quote_summary_contact': {es: '• <strong>Contacto:</strong> {contact}<br>', en: '• <strong>Contact:</strong> {contact}<br>'},
  'quote_sent': {es: '✅ Se abrió WhatsApp con tu cotización. Envía el mensaje y un asesor te atenderá pronto. ¡Gracias por contactarnos! 🙌', en: '✅ WhatsApp opened with your quote. Send the message and an advisor will attend you soon. Thank you for contacting us! 🙌'},
  'maps_opened': {es: '🗺️ Se abrió Google Maps con la ubicación de nuestro showroom.', en: '🗺️ Google Maps opened with the location of our showroom.'},
  'quote_prefers_not': {es: 'Prefiero no decir', en: 'Prefer not to say'},
  'quote_whatsapp_only': {es: 'Solo enviar por WhatsApp', en: 'Send via WhatsApp only'},
  'suggest_bathroom': {es: 'Baño', en: 'Bathroom'},
  'suggest_kitchen': {es: 'Cocina', en: 'Kitchen'},
  'suggest_living': {es: 'Sala', en: 'Living room'},
  'suggest_bedroom': {es: 'Recámara', en: 'Bedroom'},
  'suggest_facade': {es: 'Fachada', en: 'Facade'},
  'suggest_garden': {es: 'Jardín', en: 'Garden'},
  'suggest_office': {es: 'Oficina', en: 'Office'},
  'suggest_5m2': {es: '5 m²', en: '5 m²'},
  'suggest_10m2': {es: '10 m²', en: '10 m²'},
  'suggest_20m2': {es: '20 m²', en: '20 m²'},
  'suggest_30m2': {es: '30 m²', en: '30 m²'},
  'suggest_50m2': {es: '50 m²', en: '50 m²'},
  'suggest_dont_know': {es: 'No sé, ayúdame', en: 'I don\\'t know, help me'},
  'suggest_with_install': {es: 'Sí, con instalación', en: 'Yes, with installation'},
  'suggest_only_material': {es: 'No, solo material', en: 'No, only material'},
  'suggest_advice': {es: 'Quiero que me asesoren', en: 'I want advice'},
  'suggest_nogales_son': {es: 'Nogales, Sonora', en: 'Nogales, Sonora'},
  'suggest_nogales_az': {es: 'Nogales, AZ', en: 'Nogales, AZ'},
  'suggest_tucson': {es: 'Tucson, AZ', en: 'Tucson, AZ'},
  'suggest_other_city': {es: 'Otra ciudad', en: 'Other city'},
  'suggest_measures_of': {es: 'Medidas de {cat}', en: 'Measurements of {cat}'},
  'suggest_prices_of': {es: 'Precios de {cat}', en: 'Prices of {cat}'},
  'suggest_colors_of': {es: 'Colores de {cat}', en: 'Colors of {cat}'},
  'suggest_view_of': {es: 'Ver {cat}', en: 'View {cat}'},
  'suggest_quote_of': {es: 'Cotizar {cat}', en: 'Quote {cat}'},
  'suggest_can_get_wet': {es: '¿Se puede mojar?', en: 'Can it get wet?'},
  'suggest_exterior': {es: '¿Para exterior?', en: 'For outdoor use?'},
  'suggest_maintenance': {es: 'Mantenimiento', en: 'Maintenance'},
  'suggest_material': {es: 'Material', en: 'Material'},
  'suggest_installation': {es: 'Instalación', en: 'Installation'},
  'suggest_warranty': {es: 'Garantía', en: 'Warranty'},
  'suggest_request_quote': {es: 'Solicitar cotización', en: 'Request quote'},
  'suggest_quote_shipping': {es: 'Cotizar envío', en: 'Quote shipping'},
  'suggest_quote_install': {es: 'Cotizar instalación', en: 'Quote installation'},
  'suggest_view_similar': {es: 'Ver productos similares', en: 'View similar products'},
  'reco_bath_title': {es: '🚿 Para baños y cocinas te recomendamos:', en: '🚿 For bathrooms and kitchens we recommend:'},
  'reco_bath_text': {es: '• <strong>Placas PVC</strong> — 100% impermeables, ideales para muros. Acabados tipo mármol, espejo o madera.<br>• <strong>Pisos SPC</strong> — Resistentes al agua, instalación tipo click.<br>• <strong>Lambrín WPC</strong> — También resiste humedad, aspecto natural de madera.<br><br>💡 Todas tienen garantía de 12-15 años.', en: '• <strong>PVC Panels</strong> — 100% waterproof, ideal for walls. Marble, mirror or wood finishes.<br>• <strong>SPC Flooring</strong> — Water resistant, click installation.<br>• <strong>WPC Slats</strong> — Also resists moisture, natural wood look.<br><br>💡 All have 12-15 year warranty.'},
  'reco_exterior_title': {es: '🏠 Para exteriores y fachadas te recomendamos:', en: '🏠 For outdoors and facades we recommend:'},
  'reco_exterior_text': {es: '• <strong>Lambrín WPC exterior</strong> — No se deforma con la humedad ni el sol.<br>• <strong>Cladding</strong> — Imitación de piedra real, pesa 8-12 veces menos.<br>• <strong>Zacate sintético</strong> — Para jardines, verde todo el año sin mantenimiento.<br><br>💡 Estos materiales están diseñados para resistir intemperie.', en: '• <strong>Exterior WPC Slats</strong> — Does not deform with moisture or sun.<br>• <strong>Cladding</strong> — Real stone imitation, weighs 8-12 times less.<br>• <strong>Synthetic Grass</strong> — For gardens, green all year without maintenance.<br><br>💡 These materials are designed to withstand the weather.'},
  'reco_floor_title': {es: '🏗️ Para pisos te recomendamos:', en: '🏗️ For flooring we recommend:'},
  'reco_floor_text': {es: '• <strong>SPC</strong> — Muy resistente al agua, ideal cocinas y baños.<br>• <strong>WPC</strong> — Más cálido y confortable, ideal recámaras.<br>• <strong>Laminado</strong> — Más económico, para interiores de bajo tráfico.<br>• <strong>Deck sintético</strong> — Para exteriores y terrazas.', en: '• <strong>SPC</strong> — Very water resistant, ideal for kitchens and bathrooms.<br>• <strong>WPC</strong> — Warmer and more comfortable, ideal for bedrooms.<br>• <strong>Laminate</strong> — More economical, for low-traffic interiors.<br>• <strong>Synthetic Deck</strong> — For outdoors and terraces.'},
  'reco_ceiling_title': {es: '🏢 Para plafones y cielos falsos te recomendamos:', en: '🏢 For ceilings and drop ceilings we recommend:'},
  'reco_ceiling_text': {es: '• <strong>Plafón PVC laminado</strong> — Imitación madera, inmune a humedad y moho.<br>• <strong>Plafón PVC ranurado</strong> — Diseño moderno, fácil instalación.<br><br>💡 No se cuartea, no absorbe humedad y no requiere mantenimiento.', en: '• <strong>Laminated PVC Ceiling</strong> — Wood imitation, immune to moisture and mold.<br>• <strong>Grooved PVC Ceiling</strong> — Modern design, easy installation.<br><br>💡 Does not crack, does not absorb moisture and requires no maintenance.'},
  'reco_wall_title': {es: '🎨 Para muros decorativos te recomendamos:', en: '🎨 For decorative walls we recommend:'},
  'reco_wall_text': {es: '• <strong>Paneles 3D</strong> — Transforman cualquier muro en una obra de arte. Disponibles en blanco, grises, madera, negro y dorado.<br><br>💡 Ideales para recámaras, salas, recepciones y fondos de TV.', en: '• <strong>3D Panels</strong> — Transform any wall into a work of art. Available in white, gray, wood, black and gold.<br><br>💡 Ideal for bedrooms, living rooms, receptions and TV backdrops.'},
  'reco_garden_title': {es: '🌿 Para jardines y exteriores verdes te recomendamos:', en: '🌿 For green gardens and outdoors we recommend:'},
  'reco_garden_text': {es: '• <strong>Zacate sintético</strong> — Verde todo el año sin riego ni poda.<br>• <strong>Follaje sintético</strong> — Para muros verdes y jardineras.<br><br>💡 Resistente a rayos UV, con garantía de 5 años.', en: '• <strong>Synthetic Grass</strong> — Green all year without irrigation or pruning.<br>• <strong>Synthetic Foliage</strong> — For green walls and planters.<br><br>💡 UV resistant, with 5-year warranty.'},
  'reco_beam_title': {es: '🪵 Para vigas decorativas te recomendamos:', en: '🪵 For decorative beams we recommend:'},
  'reco_beam_text': {es: '• <strong>Vigas PVC</strong> — Más ligeras, fáciles de instalar, gran variedad de diseños.<br>• <strong>Vigas WPC</strong> — Aspecto de madera real sin mantenimiento.<br><br>💡 Ideales para interior y exterior.', en: '• <strong>PVC Beams</strong> — Lighter, easy to install, wide variety of designs.<br>• <strong>WPC Beams</strong> — Real wood look without maintenance.<br><br>💡 Ideal for indoors and outdoors.'},
  'clarify_pvc_title': {es: '🤔 ¿Qué tipo de PVC te interesa?', en: '🤔 What type of PVC interests you?'},
  'clarify_pvc_text': {es: '• <strong>Placas PVC</strong> — Muros decorativos (madera, mármol, espejo, textura)<br>• <strong>Plafón PVC</strong> — Techos y cielos falsos<br>• <strong>Vigas PVC</strong> — Decoración de interiores y exteriores', en: '• <strong>PVC Panels</strong> — Decorative walls (wood, marble, mirror, texture)<br>• <strong>PVC Ceilings</strong> — Ceilings and drop ceilings<br>• <strong>PVC Beams</strong> — Interior and exterior decoration'},
  'clarify_wpc_title': {es: '🤔 ¿Qué tipo de WPC te interesa?', en: '🤔 What type of WPC interests you?'},
  'clarify_wpc_text': {es: '• <strong>Lambrín WPC</strong> — Revestimiento de muros interior/exterior<br>• <strong>Pisos WPC</strong> — Pisos cálidos y resistentes<br>• <strong>Vigas WPC</strong> — Decoración tipo madera real', en: '• <strong>WPC Slats</strong> — Indoor/outdoor wall cladding<br>• <strong>WPC Flooring</strong> — Warm and resistant floors<br>• <strong>WPC Beams</strong> — Real wood look decoration'},
  'clarify_floor_title': {es: '🤔 ¿Qué tipo de piso buscas?', en: '🤔 What type of flooring are you looking for?'},
  'clarify_floor_text': {es: '• <strong>SPC</strong> — Muy resistente al agua<br>• <strong>WPC</strong> — Cálido y confortable<br>• <strong>Laminado</strong> — Económico<br>• <strong>Deck sintético</strong> — Para exteriores', en: '• <strong>SPC</strong> — Very water resistant<br>• <strong>WPC</strong> — Warm and comfortable<br>• <strong>Laminate</strong> — Economical<br>• <strong>Synthetic Deck</strong> — For outdoors'},
  'clarify_plate_title': {es: '🤔 ¿Qué tipo de placa te interesa?', en: '🤔 What type of panel interests you?'},
  'clarify_plate_text': {es: '• <strong>Placas PVC</strong> — Decorativas para muros<br>• <strong>Paneles 3D</strong> — Con relieve y textura<br>• <strong>Cladding</strong> — Imitación piedra para exterior', en: '• <strong>PVC Panels</strong> — Decorative wall panels<br>• <strong>3D Panels</strong> — With relief and texture<br>• <strong>Cladding</strong> — Stone imitation for outdoors'},
  'clarify_beam_title': {es: '🤔 ¿Qué tipo de viga te interesa?', en: '🤔 What type of beam interests you?'},
  'clarify_beam_text': {es: '• <strong>Vigas PVC</strong> — Ligeras, gran variedad<br>• <strong>Vigas WPC</strong> — Aspecto madera real', en: '• <strong>PVC Beams</strong> — Lightweight, wide variety<br>• <strong>WPC Beams</strong> — Real wood look'},
  'clarify_panel_title': {es: '🤔 ¿Qué tipo de panel te interesa?', en: '🤔 What type of panel interests you?'},
  'clarify_panel_text': {es: '• <strong>Paneles 3D</strong> — Decorativos con relieve<br>• <strong>Placas PVC</strong> — Lisas tipo madera/mármol<br>• <strong>Cladding</strong> — Imitación piedra', en: '• <strong>3D Panels</strong> — Decorative with relief<br>• <strong>PVC Panels</strong> — Smooth wood/marble look<br>• <strong>Cladding</strong> — Stone imitation'},
  'view_full_catalog': {es: 'Ver catálogo completo', en: 'View full catalog'},
  'menu_placas_pvc': {es: 'Placas PVC', en: 'PVC Panels'},
  'menu_lambrin_wpc': {es: 'Lambrín WPC', en: 'WPC Slats'},
  'menu_revestimiento': {es: 'Revestimiento Flexible', en: 'Flexible Cladding'},
  'menu_plafon': {es: 'Plafón PVC', en: 'PVC Ceiling'},
  'menu_paneles_3d': {es: 'Paneles 3D', en: '3D Panels'},
  'menu_vigas': {es: 'Vigas PVC', en: 'PVC Beams'},
  'menu_pisos': {es: 'Pisos', en: 'Flooring'},
  'menu_zacate': {es: 'Zacate', en: 'Synthetic Grass'},
  'menu_cladding': {es: 'Cladding', en: 'Cladding'},
  'compare_pvc_wpc_title': {es: '🆚 WPC vs PVC:', en: '🆚 WPC vs PVC:'},
  'compare_pvc_wpc_wpc': {es: '<strong>WPC (Wood Plastic Composite):</strong><br>• 60-70% fibras de madera + 30-40% plástico HDPE<br>• Aspecto más natural tipo madera real<br>• Absorción de agua menor al 1% — no se hincha ni se deforma<br>• Ideal para exteriores (resistente a UV y lluvia)<br>• Vida útil: 25-30 años | Garantía: 15 años', en: '<strong>WPC (Wood Plastic Composite):</strong><br>• 60-70% wood fibers + 30-40% HDPE plastic<br>• More natural real wood look<br>• Water absorption less than 1% — does not swell or deform<br>• Ideal for outdoors (UV and rain resistant)<br>• Useful life: 25-30 years | Warranty: 15 years'},
  'compare_pvc_wpc_pvc': {es: '<strong>PVC:</strong><br>• Plástico 100% con aditivos estabilizadores UV<br>• Más ligero y fácil de instalar<br>• Ideal para interiores<br>• Mayor variedad de diseños (madera, espejo, mármol, textura)<br>• Vida útil: 20-25 años | Garantía: 15 años', en: '<strong>PVC:</strong><br>• 100% plastic with UV stabilizer additives<br>• Lighter and easier to install<br>• Ideal for indoors<br>• Greater variety of designs (wood, mirror, marble, texture)<br>• Useful life: 20-25 years | Warranty: 15 years'},
  'compare_pvc_wpc_tip': {es: '💡 <strong>¿Cuál elegir?</strong><br>• Exteriores / fachadas → <strong>WPC</strong><br>• Interiores / cocinas / baños → <strong>PVC</strong> (más económico)', en: '💡 <strong>Which to choose?</strong><br>• Outdoors / facades → <strong>WPC</strong><br>• Indoors / kitchens / bathrooms → <strong>PVC</strong> (more economical)'},
  'compare_diff_title': {es: '<strong>⚖️ Diferencias — {name}:</strong>', en: '<strong>⚖️ Differences — {name}:</strong>'},
  'marble_title': {es: '🏛️ Hoja de PVC tipo Mármol', en: '🏛️ Marble-look PVC Sheet'},
  'marble_intro': {es: 'Es una solución decorativa perfecta para cualquier espacio interior. Añade un toque de elegancia a tu hogar, oficina o espacio comercial.', en: 'It is a perfect decorative solution for any indoor space. It adds a touch of elegance to your home, office or commercial space.'},
  'marble_features_title': {es: '✨ Características:', en: '✨ Features:'},
  'marble_features': {es: '• Fabricada con PVC rígido de alta calidad<br>• Dimensiones: 2440 x 1220 x 5 mm (2.977 m² por pieza)<br>• Duradera y ligera, fácil de instalar y mantener<br>• 100% resistente al agua, manchas y arañazos<br>• No requiere sellado ni barnizado<br>• Garantía: 15 años', en: '• Made with high-quality rigid PVC<br>• Dimensions: 2440 x 1220 x 5 mm (2.977 m² per piece)<br>• Durable and lightweight, easy to install and maintain<br>• 100% resistant to water, stains and scratches<br>• Does not require sealing or varnishing<br>• Warranty: 15 years'},
  'marble_apps_title': {es: '🏠 Aplicaciones:', en: '🏠 Applications:'},
  'marble_apps': {es: 'Cocinas, baños, salas de estar, recepciones, muros de acento y más.', en: 'Kitchens, bathrooms, living rooms, receptions, accent walls and more.'},
  'marble_designs_title': {es: '🎨 Diseños disponibles:', en: '🎨 Available designs:'},
  'marble_designs': {es: 'Carrara, Carrara Oscuro, Aurora Dorada, Onix, Cuarzo, Opalo, Perla, Topacio, Grafito, Jaspe, Agata, Arena, Obsidiana y más.', en: 'Carrara, Dark Carrara, Golden Aurora, Onyx, Quartz, Opal, Pearl, Topaz, Graphite, Jasper, Agate, Sand, Obsidian and more.'},
  'marble_tip': {es: '💡 Consejo: Para instalación en espejos se requiere perfil de aluminio obligatoriamente.', en: '💡 Tip: Aluminum profiles are mandatory for mirror installation.'},
  'research_source': {es: '📚 Sacado de <a href="sabias-que.html" style="color:#C5A059">¿Sabías que?</a>', en: '📚 From <a href="sabias-que.html" style="color:#C5A059">Did you know?</a>'},
  'more_curiosities': {es: 'Más datos curiosos', en: 'More curious facts'},
  'curious_facts': {es: 'Ver datos curiosos', en: 'View curious facts'},
  'wa_general': {es: 'Hola ADIS, tengo una pregunta', en: 'Hello ADIS, I have a question'},
  'wa_quote': {es: 'Hola ADIS, quiero una cotización', en: 'Hello ADIS, I want a quote'},
  'wa_shipping': {es: 'Hola ADIS, quiero cotizar un envío', en: 'Hello ADIS, I want to quote shipping'},
  'wa_install': {es: 'Hola ADIS, quiero cotizar instalación', en: 'Hello ADIS, I want to quote installation'},
  'wa_maintenance': {es: 'Hola ADIS, pregunto por mantenimiento', en: 'Hello ADIS, asking about maintenance'},
  'wa_payments': {es: 'Hola ADIS, pregunto por formas de pago', en: 'Hello ADIS, asking about payment methods'},
  'wa_project': {es: 'Hola ADIS, tengo un proyecto de', en: 'Hello ADIS, I have a project of'},
  'wa_product_interest': {es: 'Hola ADIS, vi el {name} en el catálogo y me interesa cotizar', en: 'Hello ADIS, I saw the {name} in the catalog and I am interested in a quote'},
  'wa_urgent_quote': {es: 'Cotización urgente', en: 'Urgent quote'},
  'kb_shipping_free': {es: 'Nogales Sonora, Nogales AZ y Tucson', en: 'Nogales Sonora, Nogales AZ and Tucson'},
  'kb_shipping_national': {es: 'Enviamos a todo México. El costo corre por cuenta del cliente.', en: 'We ship throughout Mexico. Cost is borne by the customer.'},
  'kb_shipping_time': {es: '2 a 3 días hábiles para pedidos grandes', en: '2 to 3 business days for large orders'},
  'kb_projects_types': {es: 'Casas, oficinas, negocios, locales comerciales y cualquier espacio que requiera remodelación', en: 'Houses, offices, businesses, commercial spaces and any space that requires remodeling'},
  'kb_quote_time': {es: 'Menos de 24 horas', en: 'Less than 24 hours'},
  'kb_quote_includes': {es: 'Costos detallados y stock disponible', en: 'Detailed costs and available stock'},
  'kb_quote_no_stock': {es: 'Si no tenemos stock, estará disponible en 2 a 3 días', en: 'If we do not have stock, it will be available in 2 to 3 days'},
  'kb_venta_unidad': {es: 'El tipo de unidad y cómo se vende viene en las fichas técnicas de cada categoría: por pieza, por hoja, tamaño de la hoja, etc.', en: 'The unit type and how it is sold is in the technical sheets of each category: per piece, per sheet, sheet size, etc.'},
  'specs_placas_pvc': {es: 'Material: PVC rígido | Dimensiones: 2440 x 1220 x 5 mm | Presentación: 2.977 m²/pz, 1 pz/caja, 10.5 kg/pz | Garantía: 15 años | Uso: Interior', en: 'Material: Rigid PVC | Dimensions: 2440 x 1220 x 5 mm | Presentation: 2.977 m²/pc, 1 pc/box, 10.5 kg/pc | Warranty: 15 years | Use: Indoor'},
  'specs_lambrin_wpc': {es: 'Material: Wood Plastic Composite | Dimensiones: 219 x 26 x 3 mm (interior), 220 x 21 x 2.5 mm (exterior) | Presentación: 2.85 m²/caja (interior), 3.08 m²/caja (exterior) | Garantía: 15 años | Uso: Interior y exterior', en: 'Material: Wood Plastic Composite | Dimensions: 219 x 26 x 3 mm (indoor), 220 x 21 x 2.5 mm (outdoor) | Presentation: 2.85 m²/box (indoor), 3.08 m²/box (outdoor) | Warranty: 15 years | Use: Indoor and outdoor'},
  'specs_paneles_3d': {es: 'Material: PVC o fibra de bambú | Dimensiones: 500 x 500 mm (varía por modelo) | Presentación: por pieza | Garantía: 10 años | Uso: Interior', en: 'Material: PVC or bamboo fiber | Dimensions: 500 x 500 mm (varies by model) | Presentation: per piece | Warranty: 10 years | Use: Indoor'},
  'specs_pisos_spc': {es: 'Material: Stone Plastic Composite | Dimensiones: 1220 x 180 x 4-5.5 mm | Presentación: 8-10 piezas/caja (1.76-2.0 m²) | Garantía: 12 años residencial | Uso: Interior', en: 'Material: Stone Plastic Composite | Dimensions: 1220 x 180 x 4-5.5 mm | Presentation: 8-10 pieces/box (1.76-2.0 m²) | Warranty: 12 years residential | Use: Indoor'},
  'specs_plafon_pvc': {es: 'Material: PVC | Dimensiones: 595 x 595 x 7 mm (laminado), 250 x 8000 x 10 mm (wood) | Presentación: por pieza | Garantía: 15 años | Uso: Interior', en: 'Material: PVC | Dimensions: 595 x 595 x 7 mm (laminated), 250 x 8000 x 10 mm (wood) | Presentation: per piece | Warranty: 15 years | Use: Indoor'},
  'specs_vigas_pvc': {es: 'Material: PVC o WPC | Dimensiones: varían 70x50mm a 120x80mm | Presentación: por pieza | Garantía: 15 años | Uso: Interior/exterior', en: 'Material: PVC or WPC | Dimensions: vary 70x50mm to 120x80mm | Presentation: per piece | Warranty: 15 years | Use: Indoor/outdoor'},
  'specs_zacate': {es: 'Material: Polietileno UV | Altura: 20-40 mm | Presentación: por metro cuadrado | Garantía: 5 años | Uso: Exterior', en: 'Material: UV polyethylene | Height: 20-40 mm | Presentation: per square meter | Warranty: 5 years | Use: Outdoor'},
  'specs_cladding': {es: 'Material: Poliuretano o compuesto mineral | Dimensiones: 1200 x 600 x 30-50 mm | Presentación: por pieza | Garantía: 10 años | Uso: Exterior', en: 'Material: Polyurethane or mineral composite | Dimensions: 1200 x 600 x 30-50 mm | Presentation: per piece | Warranty: 10 years | Use: Outdoor'},
  'specs_revestimiento': {es: 'Material: Polímero flexible | Dimensiones: varían según modelo | Aplicación: Muros interiores y exteriores | Resistente al agua y UV.', en: 'Material: Flexible polymer | Dimensions: vary by model | Application: Indoor and outdoor walls | Water and UV resistant.'},
  'specs_placas_extra': {es: '💡 Las placas PVC miden <strong>2440 x 1220 x 5 mm</strong> (2.977 m² por pieza). Se venden por pieza individual. Peso: 10.5 kg/pz. Garantía: 15 años.', en: '💡 PVC panels measure <strong>2440 x 1220 x 5 mm</strong> (2.977 m² per piece). Sold individually. Weight: 10.5 kg/pc. Warranty: 15 years.'},
  'specs_lambrin_extra': {es: '💡 Disponible en interior (219 x 26 x 3 mm) y exterior. Varía según modelo.', en: '💡 Available in indoor (219 x 26 x 3 mm) and outdoor. Varies by model.'},
  'specs_pisos_extra': {es: '💡 Tenemos laminado, WPC, SPC y deck sintético. Las medidas varían según el tipo.', en: '💡 We have laminate, WPC, SPC and synthetic deck. Dimensions vary by type.'},
  'specs_all_intro': {es: '📐 <strong>Especificaciones técnicas por categoría:</strong><br><br>', en: '📐 <strong>Technical specifications by category:</strong><br><br>'},
  'specs_all_outro': {es: '💡 Cada categoría en el catálogo tiene su ficha técnica completa con medidas exactas, contenido por caja y recomendaciones de instalación.', en: '💡 Each category in the catalog has its complete technical sheet with exact measurements, contents per box and installation recommendations.'},
  'kb_answer_header': {es: '<strong>{label} — {name}:</strong><br><br>{value}', en: '<strong>{label} — {name}:</strong><br><br>{value}'},
  'overview_header': {es: '📋 <strong>Ficha técnica de {name}:</strong><br><br>', en: '📋 <strong>Technical sheet of {name}:</strong><br><br>'},
  'overview_ask_more': {es: '¿Te gustaría saber más sobre colores, instalación o mantenimiento?', en: 'Would you like to know more about colors, installation or maintenance?'},
  'research_answer': {es: '{icon} <strong>{label} — {category}</strong><br><br><strong>{title}</strong><br><br>{content}', en: '{icon} <strong>{label} — {category}</strong><br><br><strong>{title}</strong><br><br>{content}'},
  'product_price_label': {es: 'por', en: 'per'},
  'wa_quote_summary': {es: `Hola ADIS, solicito cotización guiada desde el catálogo:\n\n• Producto: {category}\n• Espacio: {space}\n• Metraje: {m2}\n• Instalación: {install}\n• Ubicación: {location}\n{contact}Quedo atento a su respuesta. Gracias.`, en: `Hello ADIS, I request a guided quote from the catalog:\n\n• Product: {category}\n• Space: {space}\n• Square meters: {m2}\n• Installation: {install}\n• Location: {location}\n{contact}I look forward to your response. Thank you.`},

  'warranty_pvc_label': {es: 'Placas PVC:', en: 'PVC Panels:'},
  'warranty_wpc_label': {es: 'Lambrín WPC:', en: 'WPC Slats:'},
  'warranty_spc_label': {es: 'Pisos SPC:', en: 'SPC Flooring:'},
  'warranty_zacate_label': {es: 'Zacate sintético:', en: 'Synthetic Grass:'},
  'response_thanks_subject': {es: '¡Con mucho gusto! 😊🙌 Estoy aquí para lo que necesites. Si tienes más dudas, escríbenos por WhatsApp al <strong>{whatsapp}</strong> o visítanos en el showroom. ¡Que tengas un excelente día!', en: 'Gladly! 😊🙌 I am here for whatever you need. If you have more questions, write to us on WhatsApp at <strong>{whatsapp}</strong> or visit our showroom. Have a great day!'},
};

      function getLang() { return localStorage.getItem('adis_lang') || ADIS_DEFAULT_LANG; }
      function ct(key, vars) {
        const dict = CHATBOT_I18N[key];
        const lang = getLang();
        let txt = (dict && dict[lang]) || (dict && dict.es) || key;
        if (vars) {
          for (let k in vars) {
            txt = txt.replace(new RegExp('{' + k + '}', 'g'), vars[k]);
          }
        }
        return txt;
      }
      function kbval(kb, key) {
        const v = kb[key];
        if (!v) return '';
        if (typeof v === 'object' && v.es && v.en) return v[getLang()] || v.es;
        return v;
      }

      const chatWindow = document.getElementById('chatbotWindow');
      const chatBody = document.getElementById('chatbotBody');
      let allProducts = [];
      let researchData = {};
      let chatContext = loadContext();
      
      // === BASE DE CONOCIMIENTO DE PRODUCTOS ===
      // Regla clave: Nunca cambiar de producto durante la conversación, a menos que el usuario lo solicite explícitamente.
      const PRODUCT_KB = {
        placas_pvc: {
          name: { es: 'Placas PVC', en: 'PVC Panels' },
          medidas: { es: '2440 x 1220 x 5 mm (2.977 m² por pieza). Peso aprox. 10.5 kg/pz.', en: '2440 x 1220 x 5 mm (2.977 m² per piece). Approx. weight 10.5 kg/pc.' },
          agua: { es: '100% impermeables. No absorben agua, no se hinchan, no se deforman. Ideales para baños, cocinas y áreas húmedas.', en: '100% waterproof. They do not absorb water, swell or deform. Ideal for bathrooms, kitchens and humid areas.' },
          exterior: { es: 'No recomendadas para exterior directo. Son exclusivamente para interiores. Para exteriores recomendamos Cladding o Lambrín WPC exterior.', en: 'Not recommended for direct outdoor use. They are exclusively for indoors. For outdoors we recommend Cladding or exterior WPC Slats.' },
          material: { es: 'PVC rígido de alta calidad con aditivos estabilizadores UV. Superficie con acabado decorativo (madera, mármol, espejo o textura).', en: 'High-quality rigid PVC with UV stabilizer additives. Surface with decorative finish (wood, marble, mirror or texture).' },
          instalacion: { es: 'Instalación en muro con adhesivo de contacto y/o clavos ocultos. La superficie debe estar limpia, seca, nivelada y desengrasada. Para placas tipo espejo se requiere perfil de aluminio obligatoriamente.', en: 'Wall installation with contact adhesive and/or hidden nails. Surface must be clean, dry, level and degreased. Mirror panels require aluminum profiles.' },
          colores: { es: 'Tipo madera (Adler, Solaria, Solden, Anton, etc.), Tipo mármol (Carrara, Onix, Cuarzo, Opalo, Perla, Topacio, Grafito, Jaspe, Agata, Arena, Obsidiana, etc.), Tipo espejo (dorado, plateado, metal) y Texturizadas (ASH, CEDAR, ENCINO, IPE, JATOBA, NOGAL, WENGE).', en: 'Wood look (Adler, Solaria, Solden, Anton, etc.), Marble look (Carrara, Onyx, Quartz, Opal, Pearl, Topaz, Graphite, Jasper, Agate, Sand, Obsidian, etc.), Mirror look (gold, silver, metal) and Textured (ASH, CEDAR, ENCINO, IPE, JATOBA, NOGAL, WENGE).' },
          precio: { es: '$850 - $1,400 MXN por pieza. Depende del modelo y acabado.', en: '$850 - $1,400 MXN per piece. Depends on model and finish.' },
          mantenimiento: { es: 'Limpieza con paño suave humedecido en agua tibia y jabón neutro (pH 7). Para manchas difíciles usar alcohol isopropílico al 70%. Evitar acetona, thinner, solventes fuertes, estropajos metálicos y amoníaco concentrado.', en: 'Clean with soft cloth dampened in warm water and neutral soap (pH 7). For stubborn stains use 70% isopropyl alcohol. Avoid acetone, thinner, strong solvents, metal scouring pads and concentrated ammonia.' },
          usos: { es: 'Muros interiores: cocinas, baños, salas de estar, recámaras, recepciones, muros de acento, fondos de TV, barras de cocina.', en: 'Indoor walls: kitchens, bathrooms, living rooms, bedrooms, receptions, accent walls, TV backdrops, kitchen bars.' },
          garantia: { es: '15 años contra defectos de fábrica.', en: '15 years against factory defects.' },
          diferencias: { es: 'Más ligero y económico que WPC. Mayor variedad de diseños decorativos que el Lambrín. No requiere barnizado ni sellado como la madera natural.', en: 'Lighter and more economical than WPC. Greater variety of decorative designs than WPC Slats. Does not require varnishing or sealing like natural wood.' },
        },
        lambrin_wpc: {
          name: { es: 'Lambrín WPC', en: 'WPC Slats' },
          medidas: { es: 'Interior: 219 x 26 x 3 mm (2.85 m²/caja). Exterior: 220 x 21 x 2.5 mm (3.08 m²/caja).', en: 'Indoor: 219 x 26 x 3 mm (2.85 m²/box). Outdoor: 220 x 21 x 2.5 mm (3.08 m²/box).' },
          agua: { es: 'Absorción de agua menor al 1%. No se hincha, no se cuartea, no se deforma con la humedad. Resiste lluvia, rocío y salpicaduras.', en: 'Water absorption less than 1%. Does not swell, crack or deform with moisture. Resists rain, dew and splashes.' },
          exterior: { es: 'Sí, disponible en versión exterior (220 x 21 x 2.5 mm) diseñada para resistir UV, lluvia y cambios extremos de temperatura. La versión interior no debe usarse en exterior.', en: 'Yes, available in outdoor version (220 x 21 x 2.5 mm) designed to resist UV, rain and extreme temperature changes. Indoor version should not be used outdoors.' },
          material: { es: 'Wood Plastic Composite (WPC): 60-70% fibras de madera de alta calidad + 30-40% plástico HDPE reciclado. Aspecto natural de madera real sin el mantenimiento de esta.', en: 'Wood Plastic Composite (WPC): 60-70% high-quality wood fibers + 30-40% recycled HDPE plastic. Natural real wood look without the maintenance.' },
          instalacion: { es: 'Sistema de clip oculto y/o tornillos en estructura metálica o madera tratada. No requiere adhesivo. Dejar junta de dilatación de 2-3 mm entre piezas.', en: 'Hidden clip system and/or screws on metal structure or treated wood. No adhesive required. Leave 2-3 mm expansion joint between pieces.' },
          colores: { es: 'Interior: Amanecer, Amizade, Brasilia, Bahía, Estrelado, Fortaleza, Manaos, Nuvem, Río, Sabeiro, Sao Paulo, Sonho, Teak Aracaju, etc. Exterior: Charcoal, Dark Black, Teak, Redwood, Sliver Gray, etc.', en: 'Indoor: Amanecer, Amizade, Brasilia, Bahía, Estrelado, Fortaleza, Manaos, Nuvem, Río, Sabeiro, Sao Paulo, Sonho, Teak Aracaju, etc. Outdoor: Charcoal, Dark Black, Teak, Redwood, Silver Gray, etc.' },
          precio: { es: '$1,200 - $2,100 MXN por caja. La versión exterior es ligeramente más cara que la interior.', en: '$1,200 - $2,100 MXN per box. Outdoor version is slightly more expensive than indoor.' },
          mantenimiento: { es: 'Limpieza ocasional con agua y jabón neutro. No requiere barnizado, sellado ni pintura. Resistente a termitas y hongos.', en: 'Occasional cleaning with water and neutral soap. Does not require varnishing, sealing or painting. Resistant to termites and fungi.' },
          usos: { es: 'Revestimiento de muros interiores y exteriores, fachadas residenciales y comerciales, pérgolas, terrazas, cielos rasos exteriores, divisores de espacios.', en: 'Interior and exterior wall cladding, residential and commercial facades, pergolas, terraces, outdoor ceilings, space dividers.' },
          garantia: { es: '15 años contra defectos de fábrica.', en: '15 years against factory defects.' },
          diferencias: { es: 'Aspecto más natural de madera real que las Placas PVC. Más resistente al agua que la madera natural o el MDF. Más duradero que el PVC en exteriores. No requiere mantenimiento periódico.', en: 'More natural real wood look than PVC Panels. More water resistant than natural wood or MDF. More durable than PVC outdoors. Does not require periodic maintenance.' },
        },
        revestimiento: {
          name: { es: 'Revestimiento Flexible', en: 'Flexible Cladding' },
          medidas: { es: 'Varían por modelo. Consultar ficha técnica específica.', en: 'Vary by model. Check specific technical sheet.' },
          agua: { es: 'Resistente al agua y a la humedad. Ideal para zonas húmedas y exteriores protegidos.', en: 'Resistant to water and moisture. Ideal for humid areas and protected outdoors.' },
          exterior: { es: 'Sí, puede usarse en exteriores protegidos. Resistente a rayos UV y cambios de temperatura moderados.', en: 'Yes, can be used in protected outdoor areas. Resistant to UV rays and moderate temperature changes.' },
          material: { es: 'Polímero flexible de alta densidad con acabados que imitan concreto, piedra, ladrillo o madera.', en: 'High-density flexible polymer with finishes that imitate concrete, stone, brick or wood.' },
          instalacion: { es: 'Adhesión con pegamento de contacto sobre superficie limpia y nivelada. Puede cortarse con tijera o cúter.', en: 'Adhesion with contact glue on clean and level surface. Can be cut with scissors or cutter.' },
          colores: { es: 'Concreto aparente, concreto gris, granito blanco, granito imperial, granito oro, madera roble, entre otros.', en: 'Exposed concrete, gray concrete, white granite, imperial granite, gold granite, oak wood, among others.' },
          precio: { es: '$650 - $1,100 MXN por pieza.', en: '$650 - $1,100 MXN per piece.' },
          mantenimiento: { es: 'Limpieza con paño húmedo. No requiere tratamientos especiales.', en: 'Clean with damp cloth. Does not require special treatments.' },
          usos: { es: 'Muros interiores y exteriores, detalles decorativos, revestimiento de columnas, fondos de TV, barras de cocina.', en: 'Indoor and outdoor walls, decorative details, column cladding, TV backdrops, kitchen bars.' },
          garantia: { es: 'Consultar ficha técnica.', en: 'Check technical sheet.' },
          diferencias: { es: 'Mucho más ligero y flexible que el Cladding. Se adapta a curvas y esquinas. Más económico que la piedra real.', en: 'Much lighter and more flexible than Cladding. Adapts to curves and corners. More economical than real stone.' },
        },
        plafon: {
          name: { es: 'Plafón PVC', en: 'PVC Ceiling' },
          medidas: { es: 'Laminado: 595 x 595 x 7 mm. Wood style: 250 x 8000 x 10 mm.', en: 'Laminated: 595 x 595 x 7 mm. Wood style: 250 x 8000 x 10 mm.' },
          agua: { es: '100% impermeable. No absorbe humedad, no se cuartea, no se deforma. Ideal para cocinas y baños.', en: '100% waterproof. Does not absorb moisture, crack or deform. Ideal for kitchens and bathrooms.' },
          exterior: { es: 'No recomendado para exterior expuesto. Es para interiores.', en: 'Not recommended for exposed outdoor use. It is for indoors.' },
          material: { es: 'PVC rígido con acabado laminado tipo madera o ranurado moderno.', en: 'Rigid PVC with laminated wood-look or modern grooved finish.' },
          instalacion: { es: 'Instalación en estructura de aluminio o madera. Sistema de encaje tipo puzzle o sobre estructura visible.', en: 'Installation on aluminum or wood structure. Puzzle-type fitting system or on visible structure.' },
          colores: { es: 'Sherwood y otros acabados tipo madera. También disponible en blanco y tonos modernos.', en: 'Sherwood and other wood-look finishes. Also available in white and modern tones.' },
          precio: { es: '$180 - $350 MXN por pieza.', en: '$180 - $350 MXN per piece.' },
          mantenimiento: { es: 'Limpieza con paño húmedo. No requiere pintura ni barniz.', en: 'Clean with damp cloth. Does not require paint or varnish.' },
          usos: { es: 'Techos y cielos falsos de interiores: cocinas, baños, oficinas, consultorios, locales comerciales.', en: 'Indoor ceilings and drop ceilings: kitchens, bathrooms, offices, clinics, commercial spaces.' },
          garantia: { es: '15 años.', en: '15 years.' },
          diferencias: { es: 'Más económico y fácil de instalar que el plafón de yeso. Inmune a humedad y moho, a diferencia del MDF o madera.', en: 'More economical and easier to install than gypsum ceiling. Immune to moisture and mold, unlike MDF or wood.' },
        },
        paneles_3d: {
          name: { es: 'Paneles Tridimensionales 3D', en: '3D Panels' },
          medidas: { es: '500 x 500 mm (varía por modelo).', en: '500 x 500 mm (varies by model).' },
          agua: { es: 'Los de PVC son resistentes al agua. Los de fibra de bambú requieren protección en zonas húmedas.', en: 'PVC ones are water resistant. Bamboo fiber ones require protection in humid areas.' },
          exterior: { es: 'Solo los modelos de PVC específicos para exterior. Consultar ficha técnica.', en: 'Only PVC models specific for outdoor use. Check technical sheet.' },
          material: { es: 'PVC o fibra de bambú natural. Texturas en relieve con diseños geométricos y orgánicos.', en: 'PVC or natural bamboo fiber. Embossed textures with geometric and organic designs.' },
          instalacion: { es: 'Adhesión con silicona o pegamento de contacto sobre muro limpio y nivelado.', en: 'Adhesion with silicone or contact glue on clean and level wall.' },
          colores: { es: 'Blanco, grises, madera, negro, dorado. Algunos modelos se pueden pintar.', en: 'White, grays, wood, black, gold. Some models can be painted.' },
          precio: { es: '$280 - $550 MXN por pieza.', en: '$280 - $550 MXN per piece.' },
          mantenimiento: { es: 'Limpieza con paño seco o aspiradora de baja potencia. Para PVC: paño húmedo.', en: 'Clean with dry cloth or low-power vacuum. For PVC: damp cloth.' },
          usos: { es: 'Muros de acento, fondos de TV, cabeceras de cama, recepciones, salas, recámaras, locales comerciales.', en: 'Accent walls, TV backdrops, bed headboards, receptions, living rooms, bedrooms, commercial spaces.' },
          garantia: { es: '10 años.', en: '10 years.' },
          diferencias: { es: 'Agrega profundidad y relieve que las placas lisas no logran. Más decorativo que funcional.', en: 'Adds depth and relief that flat panels cannot achieve. More decorative than functional.' },
        },
        vigas: {
          name: { es: 'Vigas PVC/WPC/PU', en: 'PVC/WPC/PU Beams' },
          medidas: { es: 'Varían desde 70x50 mm hasta 120x80 mm según modelo.', en: 'Vary from 70x50 mm to 120x80 mm depending on model.' },
          agua: { es: 'Las de PVC y WPC son resistentes al agua. Las de PU requieren protección en exteriores.', en: 'PVC and WPC ones are water resistant. PU ones require protection outdoors.' },
          exterior: { es: 'Vigas PVC y WPC: sí. Vigas PU: solo interiores o exteriores protegidos.', en: 'PVC and WPC beams: yes. PU beams: indoors only or protected outdoors.' },
          material: { es: 'PVC ligero, WPC (aspecto madera real) o PU (poliuretano, muy ligero y detallado).', en: 'Lightweight PVC, WPC (real wood look) or PU (polyurethane, very light and detailed).' },
          instalacion: { es: 'Instalación con tornillos, soportes metálicos o adhesivo de construcción según el peso y ubicación.', en: 'Installation with screws, metal supports or construction adhesive depending on weight and location.' },
          colores: { es: 'Madera clara, madera oscura, nogal, caoba, blanco, gris.', en: 'Light wood, dark wood, walnut, mahogany, white, gray.' },
          precio: { es: '$450 - $1,200 MXN por pieza.', en: '$450 - $1,200 MXN per piece.' },
          mantenimiento: { es: 'Limpieza con paño seco. No requiere barnizado ni sellado (PVC/WPC).', en: 'Clean with dry cloth. Does not require varnishing or sealing (PVC/WPC).' },
          usos: { es: 'Decoración de techos, pérgolas, porches, vigas falsas, marcos de puertas y ventanas.', en: 'Ceiling decoration, pergolas, porches, false beams, door and window frames.' },
          garantia: { es: '15 años (PVC/WPC).', en: '15 years (PVC/WPC).' },
          diferencias: { es: 'PVC: más ligero y económico. WPC: aspecto madera real. PU: máximo detalle decorativo.', en: 'PVC: lighter and more economical. WPC: real wood look. PU: maximum decorative detail.' },
        },
        pisos: {
          name: { es: 'Pisos', en: 'Flooring' },
          medidas: { es: 'SPC: 1220 x 180 x 4-5.5 mm. WPC: 1220 x 180 x 5.5-8 mm. Laminado: 1215 x 195 x 8-12 mm.', en: 'SPC: 1220 x 180 x 4-5.5 mm. WPC: 1220 x 180 x 5.5-8 mm. Laminate: 1215 x 195 x 8-12 mm.' },
          agua: { es: 'SPC: 100% impermeable. WPC: muy resistente al agua. Laminado: resistente a salpicaduras, no sumergible.', en: 'SPC: 100% waterproof. WPC: very water resistant. Laminate: resistant to splashes, not submersible.' },
          exterior: { es: 'Deck sintético: sí, diseñado para exteriores. SPC/WPC/Laminado: solo interiores.', en: 'Synthetic deck: yes, designed for outdoors. SPC/WPC/Laminate: indoors only.' },
          material: { es: 'SPC: piedra + plástico. WPC: madera + plástico. Laminado: fibra de alta densidad (HDF). Deck: WPC exterior.', en: 'SPC: stone + plastic. WPC: wood + plastic. Laminate: high-density fiber (HDF). Deck: outdoor WPC.' },
          instalacion: { es: 'Sistema click (encaje tipo puzzle). No requiere pegamento. Superficie nivelada y limpia. Dejar junta de dilatación perimetral.', en: 'Click system (puzzle-type fitting). No glue required. Level and clean surface. Leave perimeter expansion joint.' },
          colores: { es: 'Maderas claras, medias y oscuras. Cements, grises, blancos. Imitaciones de mármol y piedra.', en: 'Light, medium and dark woods. Cements, grays, whites. Marble and stone imitations.' },
          precio: { es: '$900 - $2,500 MXN por caja. SPC más económico, WPC más cálido.', en: '$900 - $2,500 MXN per box. SPC more economical, WPC warmer.' },
          mantenimiento: { es: 'Barrido regular y trapeado húmedo con jabón neutro. Evitar abrasivos y exceso de agua en laminado.', en: 'Regular sweeping and damp mopping with neutral soap. Avoid abrasives and excess water on laminate.' },
          usos: { es: 'Interiores residenciales y comerciales: recámaras, salas, cocinas, baños (SPC), oficinas, tiendas. Deck para terrazas y albercas.', en: 'Residential and commercial interiors: bedrooms, living rooms, kitchens, bathrooms (SPC), offices, shops. Deck for terraces and pools.' },
          garantia: { es: 'SPC: 12 años residencial. WPC: 15 años. Laminado: 10-15 años.', en: 'SPC: 12 years residential. WPC: 15 years. Laminate: 10-15 years.' },
          diferencias: { es: 'SPC: más duro y resistente al agua. WPC: más cálido al tacto y confortable. Laminado: más económico pero sensible al agua.', en: 'SPC: harder and more water resistant. WPC: warmer to the touch and more comfortable. Laminate: more economical but sensitive to water.' },
        },
        zacate: {
          name: { es: 'Zacate Sintético', en: 'Synthetic Grass' },
          medidas: { es: 'Rollos de 2m o 4m de ancho. Altura: 20-40 mm.', en: 'Rolls 2m or 4m wide. Height: 20-40 mm.' },
          agua: { es: 'Drenaje integrado. No se encharca. Resistente a lluvia y rocío.', en: 'Integrated drainage. Does not puddle. Resistant to rain and dew.' },
          exterior: { es: 'Sí, es exclusivamente para exteriores. Resistente a rayos UV.', en: 'Yes, it is exclusively for outdoors. Resistant to UV rays.' },
          material: { es: 'Polietileno UV de alta densidad. Hilos texturizados que imitan pasto natural.', en: 'High-density UV polyethylene. Textured threads that imitate natural grass.' },
          instalacion: { es: 'Colocación sobre terreno nivelado con base de grava o cemento. Se fija con clavos en U o adhesivo.', en: 'Placement on level ground with gravel or cement base. Fixed with U-nails or adhesive.' },
          colores: { es: 'Verde natural, verde oscuro, verde-amarillo, mixtos.', en: 'Natural green, dark green, green-yellow, mixed.' },
          precio: { es: '$220 - $480 MXN por m².', en: '$220 - $480 MXN per m².' },
          mantenimiento: { es: 'Barrido de hojas y residuos. Lavado ocasional con manguera. No requiere riego, poda ni fertilizantes.', en: 'Sweep leaves and debris. Occasional washing with hose. Does not require irrigation, pruning or fertilizers.' },
          usos: { es: 'Jardines, terrazas, balcones, albercas, áreas de juego, rooftops, eventos, decoración de interiores (follaje).', en: 'Gardens, terraces, balconies, pools, play areas, rooftops, events, indoor decoration (foliage).' },
          garantia: { es: '5 años contra decoloración por UV.', en: '5 years against UV discoloration.' },
          diferencias: { es: 'No requiere riego, poda ni mantenimiento como el pasto natural. Más higiénico para mascotas y niños.', en: 'Does not require irrigation, pruning or maintenance like natural grass. More hygienic for pets and children.' },
        },
        cladding: {
          name: { es: 'Cladding (Placas tipo piedra)', en: 'Cladding (Stone-look Panels)' },
          medidas: { es: '1200 x 600 x 30-50 mm.', en: '1200 x 600 x 30-50 mm.' },
          agua: { es: 'Resistente al agua y a la intemperie. No absorbe humedad.', en: 'Resistant to water and weather. Does not absorb moisture.' },
          exterior: { es: 'Sí, diseñado específicamente para exteriores. Resiste lluvia, viento, UV y cambios de temperatura.', en: 'Yes, designed specifically for outdoors. Resists rain, wind, UV and temperature changes.' },
          material: { es: 'Poliuretano o compuesto mineral de alta densidad. Imitación de piedra real con textura y color naturales.', en: 'Polyurethane or high-density mineral composite. Real stone imitation with natural texture and color.' },
          instalacion: { es: 'Adhesión con mortero especial o tornillos en estructura. Requiere nivelación previa y sellado de juntas.', en: 'Adhesion with special mortar or screws on structure. Requires prior leveling and joint sealing.' },
          colores: { es: 'BLACK, WHITE, GRAY, BEIGE, BROWN, RUSTIC, CEMENT.', en: 'BLACK, WHITE, GRAY, BEIGE, BROWN, RUSTIC, CEMENT.' },
          precio: { es: '$550 - $1,050 MXN por pieza.', en: '$550 - $1,050 MXN per piece.' },
          mantenimiento: { es: 'Limpieza con manguera o cepillo suave. No requiere tratamientos químicos.', en: 'Clean with hose or soft brush. Does not require chemical treatments.' },
          usos: { es: 'Fachadas residenciales y comerciales, muros de contención decorativos, columnas, chimeneas, detalles arquitectónicos.', en: 'Residential and commercial facades, decorative retaining walls, columns, chimneys, architectural details.' },
          garantia: { es: '10 años.', en: '10 years.' },
          diferencias: { es: 'Pesa 8-12 veces menos que la piedra real. Instalación más rápida y económica. No requiere cimentación especial.', en: 'Weighs 8-12 times less than real stone. Faster and more economical installation. Does not require special foundation.' },
        },
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
          medidas: ct('label_measures'), agua: ct('label_water'), exterior: ct('label_exterior'),
          material: ct('label_material'), instalacion: ct('label_install'), colores: ct('label_colors'),
          precio: ct('label_price'), mantenimiento: ct('label_maintenance'), usos: ct('label_uses'),
          garantia: ct('label_warranty'), comparar: ct('label_compare')
        };
        return ct('kb_answer_header', {label: labels[questionType], name: kbval(kb, 'name'), value: kbval(kb, questionType)});
      }
      
      function getKBOverview(catName) {
        const kb = PRODUCT_KB[catName];
        if (!kb) return null;
        const name = kbval(kb, 'name');
        return ct('overview_header', {name: name}) +
          '📐 <strong>' + ct('label_measures') + ':</strong> ' + kbval(kb, 'medidas') + '<br>' +
          '💧 <strong>' + ct('label_water') + ':</strong> ' + kbval(kb, 'agua') + '<br>' +
          '🌤️ <strong>' + ct('label_exterior') + ':</strong> ' + kbval(kb, 'exterior') + '<br>' +
          '🧱 <strong>' + ct('label_material') + ':</strong> ' + kbval(kb, 'material') + '<br>' +
          '💰 <strong>' + ct('label_price') + ':</strong> ' + kbval(kb, 'precio') + '<br>' +
          '✅ <strong>' + ct('label_warranty') + ':</strong> ' + kbval(kb, 'garantia') + '<br><br>' +
          ct('overview_ask_more');
      }
      
      const WELCOME_VARIANTS = [
        ct('welcome_1'), ct('welcome_2')
      
      ];
      
      let kb = {
        horarios: {
          lunes: ct('hours_monday'),
          martes: ct('hours_tuesday'),
          miercoles: ct('hours_wednesday'),
          jueves: ct('hours_thursday'),
          viernes: ct('hours_friday'),
          sabado: ct('hours_saturday'),
          domingo: ct('hours_sunday'),
          whatsapp: ct('hours_whatsapp_note')
        },
        contacto: {
          whatsapp: '+1 (520) 839-2877',
          tel_showroom: '+52 631-120-4943',
          email: 'adis.remodelacion@gmail.com',
          ubicacion: 'Nogales, Sonora y Rio Rico, AZ',
          direccion: 'C. Alfonso Acosta 16 Local 3, Col. 5 de Mayo, 84000 Heroica Nogales, Sonora'
        },
        envios: {
          gratis: ct('kb_shipping_free'),
          nacional: ct('kb_shipping_national'),
          tiempo_grandes: ct('kb_shipping_time')
        },
        pagos: {
          metodos: [ct('payment_credit_card'), ct('payment_debit_card'), ct('payment_transfer'), ct('payment_cash')],
          anticipo: ct('payment_advance')
        },
        instalacion: {
          disponible: true,
          costo: ct('install_cost_note'),
          proceso: ct('install_process')
        },
        proyectos: {
          tipos: ct('kb_projects_types')
        },
        cotizacion: {
          tiempo: ct('kb_quote_time'),
          incluye: ct('kb_quote_includes'),
          sin_stock: ct('kb_quote_no_stock')
        },
        precios: {
          iva: ct('price_includes_iva'),
          mayorista: ct('price_wholesale')
        },
        garantia: {
          validacion: ct('warranty_validation'),
          pvc: '15 años',
          wpc: '15 años',
          spc: '12 años (residencial)',
          zacate: '5 años'
        },
        definiciones: {
          pvc: ct('def_pvc_text'),
          wpc: ct('def_wpc_text'),
          spc: 'Stone Plastic Composite. Material de piso compuesto de piedra caliza y PVC. Muy resistente al agua, ideal para cocinas y baños. Instalación tipo click.',
          laminado: 'Piso laminado de alta densidad (HDF) con capa decorativa impresa. Económico y fácil de instalar. Recomendado para interiores de bajo tráfico.',
          cladding: 'Revestimiento de fachada que imita piedra natural. Pesa 8-12 veces menos que la piedra real, es más fácil de instalar y no requiere mantenimiento.'
        },
        especificaciones: {
          placas_pvc: ct('specs_placas_pvc'),
          lambrin_wpc: ct('specs_lambrin_wpc'),
          paneles_3d: ct('specs_paneles_3d'),
          pisos_spc: ct('specs_pisos_spc'),
          plafon_pvc: ct('specs_plafon_pvc'),
          vigas_pvc: ct('specs_vigas_pvc'),
          zacate: ct('specs_zacate'),
          cladding: ct('specs_cladding')
        },
        venta: {
          unidad: ct('kb_venta_unidad')
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
        const displayText = isUser ? text : translateResponse(text);
        msg.innerHTML = displayText + '<div class="chat-time">' + formatTime(Date.now()) + '</div>';
        chatBody.appendChild(msg);
        chatBody.scrollTop = chatBody.scrollHeight;
      }
      
      function renderHistory() {
        const h = getHistory();
        if (h.length === 0) return false;
        h.forEach(item => {
          const msg = document.createElement('div');
          msg.className = 'chat-message ' + (item.isUser ? 'user' : 'bot');
          msg.innerHTML = (item.isUser ? item.text : translateResponse(item.text)) + '<div class="chat-time">' + formatTime(item.time) + '</div>';
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
        if (!replies || replies.length === 0) replies = [ct('view_products'), ct('hours'), ct('quotation'), ct('location')];
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
        wrap.innerHTML = `<input type="text" id="chatTextInput" placeholder="${ct('input_placeholder')}" autocomplete="off" style="flex:1;padding:0.6rem 1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(197,160,89,0.25);border-radius:20px;color:var(--light);font-family:'Montserrat',sans-serif;font-size:1rem;" onkeydown="if(event.key==='Enter'){chatBotProcess(this.value);this.value='';}"><button onclick="chatBotProcess(document.getElementById('chatTextInput').value);document.getElementById('chatTextInput').value='';" style="background:var(--gold);border:none;border-radius:50%;width:34px;height:34px;cursor:pointer;color:var(--black);font-size:0.9rem;flex-shrink:0;">➤</button>`;
        chatBody.appendChild(wrap);
        chatBody.scrollTop = chatBody.scrollHeight;
        setTimeout(() => { const inp = document.getElementById('chatTextInput'); if (inp) inp.focus(); }, 100);
      }
      
      // === TARJETAS DE PRODUCTO ===
      function formatProductCard(m) {
        const waText = encodeURIComponent(ct('wa_product_interest', {name: m.name}));
        const priceTag = m.price ? `<div style="color:var(--gold);font-size:0.75rem;font-weight:600;margin-top:0.25rem;">💰 ${m.price} <span style="opacity:0.7;font-weight:400;">${ct('product_price_label')} ${m.price_unit || 'pieza'}</span></div>` : '';
        return `<div class="chat-product-card">
          <img src="${ADIS_PREFIX + m.thumb}" alt="${(getLang()==='en' && m.name_en) ? m.name_en : m.name}" loading="lazy">
          <div class="chat-product-info">
            <a href="${m.url}" target="_blank">${(getLang()==='en' && m.name_en) ? m.name_en : m.name}</a>
            <div class="chat-product-cat">${m.category}${m.subcategory ? ' / ' + m.subcategory : ''}</div>
            ${priceTag}
            <div class="chat-product-actions">
              <a href="${m.url}" class="primary" target="_blank">${ct('view_product')}</a>
              <a href="https://wa.me/15208392877?text=${waText}" class="secondary" target="_blank">${ct('quote')}</a>
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
          const text = normalizeQuery(p.name + ' ' + p.category + ' ' + (p.subcategory || '') + ' ' + (p.name_en || '') + ' ' + (p.category_en || '') + ' ' + (p.subcategory_en || ''));
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
        const label = item.type === 'faq' ? ct('label_faq') : ct('label_curiosity');
        return ct('research_answer', {icon: icon, label: label, category: item.category, title: item.title, content: item.content});
      }
      
      // === SUGERENCIAS CONTEXTUALES ===
      // === SUGERENCIAS CONTEXTUALES ===
      function getSuggestions(intent, category, products) {
        if (products && products.length > 0) {
          return [ct('view_datasheet'), ct('quote_this_product'), ct('view_more_products'), ct('talk_to_advisor')];
        }
        if (category) {
          const catName = category.labels.short;
          const base = [ct('suggest_view_of', {cat: catName}), ct('suggest_quote_of', {cat: catName}), ct('talk_to_advisor')];
          if (intent === 'medidas') return [ct('suggest_prices_of', {cat: catName}), ct('suggest_can_get_wet'), ct('suggest_colors_of', {cat: catName})].concat(base);
          if (intent === 'precio') return [ct('suggest_measures_of', {cat: catName}), ct('suggest_colors_of', {cat: catName}), ct('suggest_exterior')].concat(base);
          if (intent === 'agua') return [ct('suggest_measures_of', {cat: catName}), ct('suggest_maintenance'), ct('suggest_colors_of', {cat: catName})].concat(base);
          if (intent === 'exterior') return [ct('suggest_measures_of', {cat: catName}), ct('suggest_material'), ct('suggest_installation')].concat(base);
          if (intent === 'material') return [ct('label_measures'), ct('label_colors'), ct('label_price')].concat(base);
          if (intent === 'instalacion') return [ct('label_measures'), ct('label_material'), ct('label_price')].concat(base);
          if (intent === 'colores') return [ct('suggest_view_of', {cat: catName}), ct('label_price'), ct('label_measures')].concat(base);
          if (intent === 'mantenimiento') return [ct('label_material'), ct('label_price'), ct('label_warranty')].concat(base);
          if (intent === 'usos') return [ct('label_measures'), ct('label_price'), ct('label_colors')].concat(base);
          if (intent === 'garantia') return [ct('label_measures'), ct('label_price'), ct('label_maintenance')].concat(base);
          if (intent === 'comparar') return [ct('suggest_view_of', {cat: catName}), ct('label_price'), ct('label_measures')].concat(base);
          return [ct('suggest_measures_of', {cat: catName}), ct('suggest_prices_of', {cat: catName}), ct('suggest_colors_of', {cat: catName}), ct('talk_to_advisor')];
        }
        if (intent === 'precio') return [ct('suggest_request_quote'), ct('view_products'), ct('hours'), ct('talk_to_advisor')];
        if (intent === 'medidas') return [ct('view_products'), ct('quotation'), ct('hours'), ct('talk_to_advisor')];
        if (intent === 'horario') return [ct('location'), ct('view_products'), ct('quotation'), ct('talk_to_advisor')];
        if (intent === 'ubicacion') return [ct('hours'), ct('view_products'), ct('quotation'), ct('talk_to_advisor')];
        if (intent === 'envio') return [ct('suggest_quote_shipping'), ct('view_products'), ct('location'), ct('talk_to_advisor')];
        if (intent === 'instalacion') return [ct('suggest_quote_install'), ct('view_products'), ct('label_price'), ct('talk_to_advisor')];
        return [ct('view_products'), ct('hours'), ct('quotation'), ct('location'), ct('talk_to_advisor')];
      }
      
      // === RESPUESTAS POR INTENCIÓN ===
      function handleSpecs(category, q) {
        const specsMap = {
          placas_pvc: { text: ct('specs_placas_pvc') + '<br><br>' + ct('specs_placas_extra'), url: '1-placas-pvc.html' },
          lambrin_wpc: { text: ct('specs_lambrin_wpc') + '<br><br>' + ct('specs_lambrin_extra'), url: '2-lambrin-wpc.html' },
          paneles_3d: { text: ct('specs_paneles_3d'), url: '5-paneles-tridimensionales.html' },
          pisos: { text: ct('specs_pisos_spc') + '<br><br>' + ct('specs_pisos_extra'), url: '7-pisos.html' },
          plafon: { text: ct('specs_plafon_pvc'), url: '4-plafon-pvc.html' },
          vigas: { text: ct('specs_vigas_pvc'), url: '6-vigas-pvc.html' },
          zacate: { text: ct('specs_zacate'), url: '8-zacate.html' },
          cladding: { text: ct('specs_cladding'), url: '9-cladding.html' },
          revestimiento: { text: ct('specs_revestimiento'), url: '3-revestimiento-flexible.html' }
        };
        function specLabel(key) { return kbval(PRODUCT_KB[key], 'name') || key; }
        if (category && specsMap[category.name]) {
          const s = specsMap[category.name];
          return '📐 <strong>' + ct('label_measures') + ' — ' + specLabel(category.name) + ':</strong><br><br>' + s.text;
        }
        let r = ct('specs_all_intro');
        for (let key in specsMap) {
          const s = specsMap[key];
          r += '📋 <strong>' + specLabel(key) + ':</strong><br>' + s.text + '<br><br>';
        }
        r += ct('specs_all_outro');
        return r;
      }
      
      function respond(intent, category, q, original) {
        let r = '', suggestions = [];

        switch(intent) {
          case 'saludo':
            r = WELCOME_VARIANTS[Math.floor(Math.random() * WELCOME_VARIANTS.length)];
            suggestions = [ct('view_products'), ct('hours'), ct('quotation'), ct('location'), ct('do_you_ship')];
            break;
          case 'horario':
            r = ct('hours_title') + '<br><br>• <strong>' + ct('hours_monday_label') + '</strong> ' + kb.horarios.lunes +
              '<br>• <strong>' + ct('hours_tuesday_label') + '</strong> ' + kb.horarios.martes +
              '<br>• <strong>' + ct('hours_wednesday_label') + '</strong> ' + kb.horarios.miercoles +
              '<br>• <strong>' + ct('hours_thursday_label') + '</strong> ' + kb.horarios.jueves +
              '<br>• <strong>' + ct('hours_friday_label') + '</strong> ' + kb.horarios.viernes +
              '<br>• <strong>' + ct('hours_saturday_label') + '</strong> ' + kb.horarios.sabado +
              '<br>• <strong>' + ct('hours_sunday_label') + '</strong> ' + kb.horarios.domingo +
              '<br><br>&#128172; ' + kb.horarios.whatsapp;
            break;
          case 'contacto':
            r = ct('contact_title') + '<br><br>• <strong>' + ct('contact_whatsapp_label') + '</strong> ' + kb.contacto.whatsapp +
              '<br>• <strong>' + ct('contact_showroom_label') + '</strong> ' + kb.contacto.tel_showroom +
              '<br>• <strong>' + ct('contact_email_label') + '</strong> ' + kb.contacto.email +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_general')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('contact_open_whatsapp') + '</a>';
            break;
          case 'ubicacion':
            r = ct('location_title') + '<br><br>' + ct('location_address_label') + '<br>' + kb.contacto.direccion +
              '<br><br>📱 <strong>' + ct('contact_whatsapp_label') + '</strong> ' + kb.contacto.whatsapp +
              '<br>☎️ <strong>' + ct('contact_showroom_label') + '</strong> ' + kb.contacto.tel_showroom +
              '<br>✉️ <strong>' + ct('contact_email_label') + '</strong> ' + kb.contacto.email +
              '<br><br>🕐 ' + ct('location_hours_note') + '<br>' + ct('location_also_serves') +
              '<br><br><a href="https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8" target="_blank" style="color:#C5A059">' + ct('location_view_map') + '</a>';
            break;
          case 'precio':
            r = ct('price_title') + '<br><br>• ' + kb.precios.iva + '<br>• ' + kb.precios.mayorista +
              '<br>• ' + ct('price_material_only') + '<br><br>' + ct('price_quote_detail') + ' ' + kb.cotizacion.tiempo +
              '<br>' + ct('price_quote_includes') + ' ' + kb.cotizacion.incluye +
              '<br>' + ct('price_quote_no_stock') + ' ' + kb.cotizacion.sin_stock + '<br><br>' + ct('price_install_question') +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_quote')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('price_request_quote') + '</a>';
            break;
          case 'envio':
            r = ct('shipping_title') + '<br><br>' + ct('shipping_free', {zonas: kb.envios.gratis}) +
              '<br><br>📦 ' + kb.envios.nacional + '<br><br>⏱️ ' + ct('shipping_large_orders', {tiempo: kb.envios.tiempo_grandes}) +
              '<br><br>' + ct('shipping_quote_address') +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_shipping')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('shipping_quote_button') + '</a>';
            break;
          case 'instalacion':
            r = ct('install_title') + '<br><br>' + kb.instalacion.costo + '<br><br>' + kb.instalacion.proceso +
              '<br><br>' + ct('install_tips_title') + '<br>' + ct('install_tips') + '<br><br>' + ct('install_also_sell_materials') +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_install')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('install_quote_button') + '</a>';
            break;
          case 'pago':
            r = ct('payment_title') + '<br><br>';
            kb.pagos.metodos.forEach(m => { r += '• ' + m + '<br>'; });
            r += '<br>⚠️ <strong>' + kb.pagos.anticipo + '</strong><br><br>' + ct('payment_write_us') +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_payments')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('payment_ask_button') + '</a>';
            break;
          case 'garantia':
            r = ct('warranty_title') + '<br><br>🛡️ ' + kb.garantia.validacion +
              '<br><br>• ' + ct('warranty_pvc_label') + ' ' + kb.garantia.pvc +
              '<br>• ' + ct('warranty_wpc_label') + ' ' + kb.garantia.wpc +
              '<br>• ' + ct('warranty_spc_label') + ' ' + kb.garantia.spc +
              '<br>• ' + ct('warranty_zacate_label') + ' ' + kb.garantia.zacate +
              '<br><br>' + ct('warranty_keep_ticket');
            break;
          case 'producto':
            r = ct('catalog_title') + '<br><br>' + ct('catalog_list') + '<br><br>&#127968; ' + ct('kb_projects_types') + '<br><br>' + ct('catalog_hint');
            break;
          case 'mantenimiento':
            r = ct('maintenance_title') + '<br><br>' + ct('maintenance_regular') + '<br>' + ct('maintenance_stains') +
              '<br>' + ct('maintenance_avoid') + '<br>' + ct('maintenance_frequency') + '<br>' + ct('maintenance_annual') +
              '<br><br>' + ct('maintenance_no_seal') +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_maintenance')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('maintenance_ask_button') + '</a>';
            break;
          case 'proyecto':
            r = ct('projects_title') + '<br><br>' + kb.proyectos.tipos + '<br><br>' + ct('projects_description') +
              '<br><br>' + ct('projects_tip_title') + ' ' + ct('projects_tip') +
              '<br><br><a href="https://wa.me/15208392877?text=' + encodeURIComponent(ct('wa_project')) + '" target="_blank" class="chat-whatsapp-btn">' + ct('projects_share_button') + '</a>';
            break;
          case 'agradecimiento':
            r = ct('response_thanks_subject', {whatsapp: kb.contacto.whatsapp});
            break;
          case 'despedida':
            r = ct('bye');
            break;
          case 'negacion':
            r = ct('negation');
            suggestions = [ct('view_products'), ct('hours'), ct('quotation'), ct('location')];
            break;
          case 'ayuda':
            r = ct('help');
            break;
          case 'medidas':
            r = handleSpecs(category, q);
            break;
          case 'definicion':
            if (q.includes('pvc')) r = ct('def_pvc_title') + '<br><br>' + kb.definiciones.pvc + '<br><br>' + ct('def_pvc_usage');
            else if (q.includes('wpc')) r = ct('def_wpc_title') + '<br><br>' + kb.definiciones.wpc + '<br><br>' + ct('def_wpc_usage');
            else r = ct('def_ask');
            break;
          case 'resistencia':
            if (category) {
              const catName = category.labels.short;
              if (catName.includes('PVC')) r = ct('water_pvc_title', {name: catName}) + '<br><br>' + ct('water_pvc_points') + '<br><br>' + ct('water_pvc_tip');
              else if (catName.includes('WPC')) r = ct('water_wpc_title', {name: catName}) + '<br><br>' + ct('water_wpc_points') + '<br><br>' + ct('water_wpc_tip');
              else if (catName.includes('Piso')) r = ct('water_floor_title', {name: catName}) + '<br><br>' + ct('water_floor_points') + '<br><br>' + ct('water_floor_tip');
              else r = ct('water_generic_title', {name: catName}) + '<br><br>' + ct('water_generic_text');
            } else {
              r = ct('water_overview_title') + '<br><br>' + ct('water_overview_points') + '<br><br>' + ct('water_overview_tip');
            }
            break;
          case 'usos':
            if (category) {
              r = ct('uses_title', {name: category.labels.short}) + '<br><br>' + handleSpecs(category, q);
            } else {
              r = ct('uses_overview_title') + '<br><br>' + ct('uses_overview_points') + '<br><br>' + ct('uses_tip');
            }
            break;
          default:
            r = ct('fallback');
        }

        if (!suggestions.length) suggestions = getSuggestions(intent, category, []);
        chatContext.lastTopic = category || chatContext.lastTopic;
        chatContext.lastIntent = intent;
        chatContext.lastResponseType = 'info';
        saveContext();

        return { text: r, suggestions };
      }
      function translateResponse(text) {
        if (getLang() !== 'en') return text;
        const map = {
          'Aquí tienes más información de': 'Here is more information about',
          'Cotizar este producto': 'Quote this product',
          'Ver productos similares': 'View similar products',
          'Hablar con asesor': 'Talk to advisor',
          'Ver en Google Maps': 'View on Google Maps',
          'Enviar cotización por WhatsApp': 'Send quote via WhatsApp',
          'Hacer otra cotización': 'Make another quote',
          'Se abrió WhatsApp con tu cotización. Envía el mensaje y un asesor te atenderá pronto. ¡Gracias por contactarnos! 🙌': 'WhatsApp opened with your quote. Send the message and an advisor will attend you soon. Thank you for contacting us! 🙌',
          'Se abrió Google Maps con la ubicación de nuestro showroom.': 'Google Maps opened with the location of our showroom.',
          'Para darte la información correcta, ¿sobre qué producto necesitas saber?': 'To give you the correct information, which product do you need to know about?',
          'Los precios varían por material y modelo.': 'Prices vary by material and model.',
          'Cotización gratis por WhatsApp con respuesta en menos de 24 horas.': 'Free quote via WhatsApp with response in less than 24 hours.',
          'Envío GRATIS en Nogales y Rio Rico. A otras ciudades cotizamos por WhatsApp.': 'FREE shipping in Nogales and Rio Rico. To other cities we quote via WhatsApp.',
          'Horario showroom: Martes a Domingo 10:00-19:00. Lunes cerrado.': 'Showroom hours: Tuesday to Sunday 10:00 AM-7:00 PM. Monday closed.',
          '¿Necesitas algo más?': 'Do you need anything else?',
          'WhatsApp:': 'WhatsApp:',
          'Showroom:': 'Showroom:',
          'Martes a domingo 10:00-19:00': 'Tuesday to Sunday 10:00 AM-7:00 PM',
          'WPC vs PVC:': 'WPC vs PVC:',
          'Hoja de PVC tipo Mármol': 'Marble-look PVC Sheet',
          'Es una solución decorativa perfecta para cualquier espacio interior. Añade un toque de elegancia a tu hogar, oficina o espacio comercial.': 'It is a perfect decorative solution for any indoor space. It adds a touch of elegance to your home, office or commercial space.',
          'Características:': 'Features:',
          'Fabricada con PVC rígido de alta calidad': 'Made with high-quality rigid PVC',
          'Dimensiones: 2440 x 1220 x 5 mm (2.977 m² por pieza)': 'Dimensions: 2440 x 1220 x 5 mm (2.977 m² per piece)',
          'Duradera y ligera, fácil de instalar y mantener': 'Durable and lightweight, easy to install and maintain',
          '100% resistente al agua, manchas y arañazos': '100% resistant to water, stains and scratches',
          'No requiere sellado ni barnizado': 'Does not require sealing or varnishing',
          'Garantía: 15 años': 'Warranty: 15 years',
          'Aplicaciones:': 'Applications:',
          'Cocinas, baños, salas de estar, recepciones, muros de acento y más.': 'Kitchens, bathrooms, living rooms, receptions, accent walls and more.',
          'Diseños disponibles:': 'Available designs:',
          'Carrara, Carrara Oscuro, Aurora Dorada, Onix, Cuarzo, Opalo, Perla, Topacio, Grafito, Jaspe, Agata, Arena, Obsidiana y más.': 'Carrara, Dark Carrara, Golden Aurora, Onyx, Quartz, Opal, Pearl, Topaz, Graphite, Jasper, Agate, Sand, Obsidian and more.',
          'Consejo: Para instalación en espejos se requiere perfil de aluminio obligatoriamente.': 'Tip: Aluminum profiles are mandatory for mirror installation.',
          'Cotizar mármol PVC': 'Quote marble PVC',
          'Ver Placas PVC': 'View PVC Panels',
          'Cotizar para baño/cocina': 'Quote for bathroom/kitchen',
          'Ver Lambrín WPC exterior': 'View exterior WPC Slats',
          'Cotizar fachada': 'Quote facade',
          'Ver Pisos SPC': 'View SPC Flooring',
          'Ver Pisos WPC': 'View WPC Flooring',
          'Ver Laminado': 'View Laminate',
          'Cotizar pisos': 'Quote flooring',
          'Ver Plafón PVC': 'View PVC Ceiling',
          'Cotizar plafón': 'Quote ceiling',
          'Ver Paneles 3D': 'View 3D Panels',
          'Cotizar paneles 3D': 'Quote 3D panels',
          'Ver Zacate': 'View Synthetic Grass',
          'Cotizar zacate': 'Quote synthetic grass',
          'Ver Vigas': 'View Beams',
          'Cotizar vigas': 'Quote beams',
          'Placas PVC': 'PVC Panels',
          'Lambrín WPC': 'WPC Slats',
          'Paneles 3D': '3D Panels',
          'Plafón PVC': 'PVC Ceiling',
          'Vigas': 'Beams',
          'Zacate': 'Synthetic Grass',
          'Revestimiento Flexible': 'Flexible Cladding',
          'Para baños y cocinas te recomendamos:': 'For bathrooms and kitchens we recommend:',
          'Para exteriores y fachadas te recomendamos:': 'For outdoors and facades we recommend:',
          'Para pisos te recomendamos:': 'For flooring we recommend:',
          'Para plafones y cielos falsos te recomendamos:': 'For ceilings and drop ceilings we recommend:',
          'Para muros decorativos te recomendamos:': 'For decorative walls we recommend:',
          'Para jardines y exteriores verdes te recomendamos:': 'For green gardens and outdoors we recommend:',
          'Para vigas decorativas te recomendamos:': 'For decorative beams we recommend:',
          'Lambrín WPC exterior': 'Exterior WPC Slats',
          'No se deforma con la humedad ni el sol.': 'Does not deform with moisture or sun.',
          'Imitación de piedra real, pesa 8-12 veces menos.': 'Real stone imitation, weighs 8-12 times less.',
          'Zacate sintético': 'Synthetic Grass',
          'Para jardines, verde todo el año sin mantenimiento.': 'For gardens, green all year without maintenance.',
          'Estos materiales están diseñados para resistir intemperie.': 'These materials are designed to withstand the weather.',
          'Muy resistente al agua, ideal cocinas y baños.': 'Very water resistant, ideal for kitchens and bathrooms.',
          'Más cálido y confortable, ideal recámaras.': 'Warmer and more comfortable, ideal for bedrooms.',
          'Más económico, para interiores de bajo tráfico.': 'More economical, for low-traffic interiors.',
          'Deck sintético': 'Synthetic Deck',
          'Para exteriores y terrazas.': 'For outdoors and terraces.',
          'Plafón PVC laminado': 'Laminated PVC Ceiling',
          'Imitación madera, inmune a humedad y moho.': 'Wood imitation, immune to moisture and mold.',
          'Plafón PVC ranurado': 'Grooved PVC Ceiling',
          'Diseño moderno, fácil instalación.': 'Modern design, easy installation.',
          'No se cuartea, no absorbe humedad y no requiere mantenimiento.': 'Does not crack, does not absorb moisture and requires no maintenance.',
          'Transforman cualquier muro en una obra de arte. Disponibles en blanco, grises, madera, negro y dorado.': 'Transform any wall into a work of art. Available in white, gray, wood, black and gold.',
          'Ideales para recámaras, salas, recepciones y fondos de TV.': 'Ideal for bedrooms, living rooms, receptions and TV backdrops.',
          'Follaje sintético': 'Synthetic Foliage',
          'Para muros verdes y jardineras.': 'For green walls and planters.',
          'Resistente a rayos UV, con garantía de 5 años.': 'UV resistant, with 5-year warranty.',
          'Vigas PVC': 'PVC Beams',
          'Más ligeras, fáciles de instalar, gran variedad de diseños.': 'Lighter, easy to install, wide variety of designs.',
          'Vigas WPC': 'WPC Beams',
          'Aspecto de madera real sin mantenimiento.': 'Real wood look without maintenance.',
          'Ideales para interior y exterior.': 'Ideal for indoors and outdoors.'
        };
        let t = text;
        for (let es in map) {
          t = t.split(es).join(map[es]);
        }
        return t;
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
              text: (getLang()==='en' ? 'Here is more information about <strong>' : 'Aquí tienes más información de <strong>') + ((getLang()==='en' && p.name_en) ? p.name_en : p.name) + '</strong>:<br><br>' + formatProductCard(p),
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
            return { text: ct('hours_short'), suggestions: [ct('location'), ct('view_products'), ct('quotation')] };
          }
          if (intent.name === 'contacto') {
            return { text: ct('contact_short', {whatsapp: kb.contacto.whatsapp, tel_showroom: kb.contacto.tel_showroom}), suggestions: [ct('open_whatsapp'), ct('location'), ct('hours')] };
          }
          if (intent.name === 'ubicacion') {
            return { text: ct('location_short', {direccion: kb.contacto.direccion}), suggestions: [ct('view_on_google_maps'), ct('whatsapp'), ct('hours')] };
          }
          if (intent.name === 'precio' && !questionType) {
            return { text: ct('price_short'), suggestions: [ct('suggest_request_quote'), ct('view_products'), ct('talk_to_advisor')] };
          }
          if (intent.name === 'envio') {
            return { text: ct('shipping_short'), suggestions: [ct('suggest_quote_shipping'), ct('location'), ct('whatsapp')] };
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
            text: ct('which_product'),
            suggestions: [ct('menu_placas_pvc'), ct('menu_lambrin_wpc'), ct('menu_pisos'), ct('menu_plafon'), ct('menu_paneles_3d'), ct('menu_cladding'), ct('talk_to_advisor')]
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
              text: ct('compare_pvc_wpc_title') + '<br><br>' + ct('compare_pvc_wpc_wpc') + '<br><br>' + ct('compare_pvc_wpc_pvc') + '<br><br>' + ct('compare_pvc_wpc_tip'),
              suggestions: [ct('menu_lambrin_wpc'), ct('menu_placas_pvc'), ct('suggest_request_quote'), ct('talk_to_advisor')]
            };
          }
          if (activeProduct) {
            const kb = PRODUCT_KB[activeProduct.name];
            if (kb && kb.diferencias) {
              return {
                text: ct('compare_diff_title', {name: kbval(kb, 'name')}) + '<br><br>' + kbval(kb, 'diferencias'),
                suggestions: getSuggestions('comparar', activeProduct, [])
              };
            }
          }
        }
        
        // === 9. Mármol específico (solo si no hay producto activo o si el usuario lo menciona explícitamente) ===
        if (!activeProduct && (normalized.includes('marmol') || normalized.includes('marble'))) {
          return { 
            text: ct('marble_title') + '<br><br>' + ct('marble_intro') + '<br><br>' + ct('marble_features_title') + '<br>' + ct('marble_features') + '<br><br>' + ct('marble_apps_title') + ' ' + ct('marble_apps') + '<br><br>' + ct('marble_designs_title') + '<br>' + ct('marble_designs') + '<br><br>' + ct('marble_tip'),
            suggestions: [ct('menu_placas_pvc'), ct('suggest_request_quote'), ct('label_measures'), ct('talk_to_advisor')]
          };
        }
        
        // === 10. Clarificación inteligente para términos ambiguos (solo si NO hay producto activo) ===
        const ambiguousTerms = ['pvc','wpc','piso','pisos','placa','placas','viga','vigas','panel','paneles'];
        const isAmbiguous = ambiguousTerms.includes(normalized.trim()) || (normalized.trim().length < 5 && !category);
        if (isAmbiguous && !activeProduct) {
          const clarifications = {
            'pvc': ct('clarify_pvc_title') + '<br><br>' + ct('clarify_pvc_text'),
            'wpc': ct('clarify_wpc_title') + '<br><br>' + ct('clarify_wpc_text'),
            'piso': ct('clarify_floor_title') + '<br><br>' + ct('clarify_floor_text'),
            'pisos': ct('clarify_floor_title') + '<br><br>' + ct('clarify_floor_text'),
            'placa': ct('clarify_plate_title') + '<br><br>' + ct('clarify_plate_text'),
            'placas': ct('clarify_plate_title') + '<br><br>' + ct('clarify_plate_text'),
            'viga': ct('clarify_beam_title') + '<br><br>' + ct('clarify_beam_text'),
            'vigas': ct('clarify_beam_title') + '<br><br>' + ct('clarify_beam_text'),
            'panel': ct('clarify_panel_title') + '<br><br>' + ct('clarify_panel_text'),
            'paneles': ct('clarify_panel_title') + '<br><br>' + ct('clarify_panel_text')
          };
          const term = normalized.trim();
          if (clarifications[term]) {
            return { text: clarifications[term], suggestions: [ct('view_full_catalog'), ct('talk_to_advisor'), ct('suggest_request_quote')] };
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
              text: ct('other_options', {cards: related.map(formatProductCard).join('')}),
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
              text: ct('rejection'),
              suggestions: [ct('suggest_view_of', {cat: ct('menu_placas_pvc')}), ct('suggest_view_of', {cat: ct('menu_lambrin_wpc')}), ct('talk_to_advisor')]
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
              text: ct('price_context', {price_info: priceInfo}),
              suggestions: [ct('suggest_quote_of', {cat: activeProduct.labels.short}), ct('view_more_products'), ct('talk_to_advisor')]
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
            urgencyMsg = ct('urgent_msg');
          }
          return {
            text: ct('found_products', {cards: products.map(formatProductCard).join(''), urgency: urgencyMsg}),
            suggestions: getSuggestions('producto', chatContext.lastTopic, products)
          };
        }
        
        // === 16. respond() con intents generales ===
        const respondResult = respond(intent.name, category, normalized, original);
        if (respondResult.text && !respondResult.text.includes('no entendí')) {
          if (isUrgent && respondResult.text) {
            respondResult.text += ct('urgent_add');
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
            text: formatResearchAnswer(researchMatch) + '<br><br>' + ct('research_source'),
            suggestions: (activeProduct || category) ? [ct('suggest_view_of', {cat: (activeProduct || category).labels.short}), ct('suggest_quote_of', {cat: (activeProduct || category).labels.short}), ct('more_curiosities'), ct('talk_to_advisor')] : [ct('curious_facts'), ct('view_products'), ct('quotation'), ct('talk_to_advisor')]
          };
        }
        
        // === 18. FALLBACK SEGURO: Si hay producto activo pero no sabemos responder ===
        if (activeProduct) {
          return {
            text: ct('no_data_for_product', {name: activeProduct.labels.short, whatsapp: kb.contacto.whatsapp}),
            suggestions: [ct('talk_to_advisor'), ct('suggest_view_of', {cat: activeProduct.labels.short}), ct('suggest_quote_of', {cat: activeProduct.labels.short})]
          };
        }
        
        // === 19. Urgencia sin resultado ===
        if (isUrgent) {
          return {
            text: ct('urgent_fallback', {whatsapp: kb.contacto.whatsapp}),
            suggestions: [ct('wa_urgent_quote'), ct('whatsapp'), ct('view_products')]
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
          text: ct('quote_flow_start'),
          suggestions: [ct('menu_placas_pvc'), ct('menu_lambrin_wpc'), ct('menu_pisos'), ct('menu_paneles_3d'), ct('menu_plafon'), ct('menu_cladding'), ct('menu_zacate')]
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
            text: ct('quote_step', {field: ct('quote_field_product'), value: text, step: ct('quote_step_2'), question: ct('quote_question_space')}),
            suggestions: [ct('suggest_bathroom'), ct('suggest_kitchen'), ct('suggest_living'), ct('suggest_bedroom'), ct('suggest_facade'), ct('suggest_garden'), ct('suggest_office')]
          };
        }
        if (state === 'space') {
          data.space = text;
          chatContext.quoteState = 'm2';
          saveContext();
          return {
            text: ct('quote_step', {field: ct('quote_field_space'), value: text, step: ct('quote_step_3'), question: ct('quote_question_m2')}),
            suggestions: [ct('suggest_5m2'), ct('suggest_10m2'), ct('suggest_20m2'), ct('suggest_30m2'), ct('suggest_50m2'), ct('suggest_dont_know')]
          };
        }
        if (state === 'm2') {
          data.m2 = text;
          chatContext.quoteState = 'install';
          saveContext();
          return {
            text: ct('quote_step', {field: ct('quote_field_m2'), value: text, step: ct('quote_step_4'), question: ct('quote_question_install')}),
            suggestions: [ct('suggest_with_install'), ct('suggest_only_material'), ct('suggest_advice')]
          };
        }
        if (state === 'install') {
          data.install = text;
          chatContext.quoteState = 'location';
          saveContext();
          return {
            text: ct('quote_step', {field: ct('quote_field_install'), value: text, step: ct('quote_step_5'), question: ct('quote_question_location')}),
            suggestions: [ct('suggest_nogales_son'), ct('suggest_nogales_az'), ct('suggest_tucson'), ct('suggest_other_city')]
          };
        }
        if (state === 'location') {
          data.location = text;
          chatContext.quoteState = 'contact';
          saveContext();
          return {
            text: ct('quote_step', {field: ct('quote_field_location'), value: text, step: ct('quote_step_6'), question: ct('quote_question_contact')}),
            suggestions: [ct('quote_prefers_not'), ct('quote_whatsapp_only')]
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
        const contactStr = (data.contact && data.contact !== ct('quote_prefers_not') && data.contact !== ct('quote_whatsapp_only')) ? ct('quote_summary_contact', {contact: data.contact}) : '';
        return {
          text: ct('quote_summary', {category: data.category, space: data.space, m2: data.m2, install: data.install, location: data.location, contact: contactStr}),
          suggestions: [ct('send_quote_whatsapp'), ct('make_another_quote'), ct('talk_to_advisor')]
        };
      }
      
      function sendQuoteToWhatsApp() {
        const data = chatContext.quoteData;
        if (!data || !data.category) return;
        const contactStr = (data.contact && data.contact !== ct('quote_prefers_not') && data.contact !== ct('quote_whatsapp_only')) ? '• Contacto: ' + data.contact + '\\n' : '';
        const msg = ct('wa_quote_summary', {category: data.category, space: data.space, m2: data.m2, install: data.install, location: data.location, contact: contactStr});
        window.open('https://wa.me/15208392877?text=' + encodeURIComponent(msg), '_blank');
      }
      
      // === RECOMENDADOR INTELIGENTE ===
      function getRecommendation(q, category) {
        const recoMap = [
          {
            words: ['bano','regadera','ducha','humedad','moho','cocina','salpicaduras'],
            text: ct('reco_bath_title') + '<br><br>' + ct('reco_bath_text'),
            suggestions: [ct('menu_placas_pvc'), ct('menu_pisos'), ct('suggest_request_quote'), ct('talk_to_advisor')]
          },
          {
            words: ['fachada','exterior','sol','lluvia','uv','exterior casa','pared exterior'],
            text: ct('reco_exterior_title') + '<br><br>' + ct('reco_exterior_text'),
            suggestions: [ct('menu_lambrin_wpc'), ct('menu_cladding'), ct('menu_zacate'), ct('suggest_request_quote')]
          },
          {
            words: ['piso','pisos','suelo','piso para','baldosa'],
            text: ct('reco_floor_title') + '<br><br>' + ct('reco_floor_text'),
            suggestions: [ct('menu_pisos'), ct('menu_pisos'), ct('menu_pisos'), ct('suggest_request_quote')]
          },
          {
            words: ['techo','cielo','plafon','plafond','cielo falso'],
            text: ct('reco_ceiling_title') + '<br><br>' + ct('reco_ceiling_text'),
            suggestions: [ct('menu_plafon'), ct('suggest_request_quote'), ct('talk_to_advisor')]
          },
          {
            words: ['muro 3d','panel decorativo','pared decorativa','relieve','textura pared'],
            text: ct('reco_wall_title') + '<br><br>' + ct('reco_wall_text'),
            suggestions: [ct('menu_paneles_3d'), ct('suggest_request_quote'), ct('talk_to_advisor')]
          },
          {
            words: ['jardin','pasto','cesped','follaje','terraza verde','jardinera'],
            text: ct('reco_garden_title') + '<br><br>' + ct('reco_garden_text'),
            suggestions: [ct('menu_zacate'), ct('suggest_request_quote'), ct('talk_to_advisor')]
          },
          {
            words: ['viga','vigas','viga decorativa','trabe','cubierta madera'],
            text: ct('reco_beam_title') + '<br><br>' + ct('reco_beam_text'),
            suggestions: [ct('menu_vigas'), ct('suggest_request_quote'), ct('talk_to_advisor')]
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
        if (text === ct('send_quote_whatsapp')) {
          sendQuoteToWhatsApp();
          setTimeout(() => {
            addMessage(ct('quote_sent'), false);
            saveHistory(ct('quote_sent'), false);
            showQuickReplies([ct('view_products'), ct('make_another_quote'), ct('talk_to_advisor')]);
            addInputField();
          }, 600);
          return;
        }
        if (text === ct('make_another_quote')) {
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
        if (text === ct('view_on_google_maps')) {
          window.open('https://maps.app.goo.gl/Q3raWUzhCj2rvhjm8', '_blank');
          setTimeout(() => {
            addMessage(ct('maps_opened'), false);
            saveHistory(ct('maps_opened'), false);
            showQuickReplies([ct('view_products'), ct('hours'), ct('quotation'), ct('whatsapp')]);
            addInputField();
          }, 600);
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
      fetch(ADIS_PREFIX + 'products.json')
        .then(r => r.json())
        .then(data => { 
          allProducts = data.products || [];
          researchData = (getLang() === 'en' && data.research_en && Object.keys(data.research_en).length) ? data.research_en : (data.research || {});
          // Compartir productos con el buscador global
          window.__adisProducts = allProducts;
          if (typeof window.__initAdisSearch === 'function') window.__initAdisSearch();
        })
        .catch(() => { 
          allProducts = [];
          researchData = {};
        });
    })();

    // === BÚSQUEDA GLOBAL (Spotlight + móvil) ===
    (function() {
      let searchProducts = [];
      let searchTimeout = null;
      
      function getLang() { return localStorage.getItem('adis_lang') || ADIS_DEFAULT_LANG; }
      function t(key) {
        const dict = {
          search_start_typing: { es: 'Escribe para buscar productos...', en: 'Type to search products...' },
          search_no_results: { es: 'No se encontraron productos', en: 'No products found' },
          search_results_count: { es: '{count} resultados', en: '{count} results' },
          search_view_product: { es: 'Ver producto', en: 'View product' },
          search_quote: { es: 'Cotizar', en: 'Quote' },
          search_all_results: { es: 'Ver todos los resultados', en: 'See all results' }
        };
        const txt = (dict[key] && dict[key][getLang()]) || (dict[key] && dict[key].es) || key;
        return txt;
      }
      
      function normalize(str) {
        return (str || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      }
      
      function highlight(text, term) {
        if (!term) return text;
        const safe = term.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
        return text.replace(new RegExp('(' + safe + ')', 'gi'), '<mark>$1</mark>');
      }
      
      function scoreProducts(term, limit) {
        if (!term || term.length < 2 || !searchProducts.length) return [];
        const normTerm = normalize(term);
        const terms = normTerm.split(/\\s+/).filter(Boolean);
        return searchProducts.map(p => {
          const text = normalize(p.name + ' ' + p.category + ' ' + (p.subcategory || '') + ' ' + (p.name_en || '') + ' ' + (p.category_en || '') + ' ' + (p.subcategory_en || ''));
          let score = 0;
          for (let t of terms) {
            if (text.includes(t)) score += 1;
            if (normalize(p.name).includes(t)) score += 3;
            if (normalize(p.name).startsWith(t)) score += 5;
          }
          return { p, score };
        }).filter(x => x.score > 0).sort((a,b) => b.score - a.score).slice(0, limit);
      }
      
      function productItem(p, term) {
        const dName = (getLang() === 'en' && p.name_en) ? p.name_en : p.name;
        const dCat = (getLang() === 'en' && p.category_en) ? p.category_en : p.category;
        const dSub = (getLang() === 'en' && p.subcategory_en) ? p.subcategory_en : p.subcategory;
        const waText = encodeURIComponent((getLang() === 'en' ? 'Hello ADIS, I saw the ' : 'Hola ADIS, vi el ') + dName + (getLang() === 'en' ? ' in the catalog and I am interested in a quote' : ' en el catálogo y me interesa cotizar'));
        return `<a href="${p.url}" class="search-item" onclick="closeSpotlight && closeSpotlight();">
          <img src="${ADIS_PREFIX + p.thumb}" alt="${dName}" loading="lazy" onerror="this.style.display='none'">
          <div class="search-item-info">
            <span class="search-item-name">${highlight(dName, term)}</span>
            <span class="search-item-cat">${dCat}${dSub ? ' / ' + dSub : ''}</span>
          </div>
        </a>`;
      }
      
      // Desktop header search dropdown
      function renderSearchDropdown(term) {
        const dropdown = document.getElementById('searchDropdown');
        if (!dropdown) return;
        const scored = scoreProducts(term, 6);
        if (scored.length === 0) {
          dropdown.innerHTML = term.length < 2 ? '' : `<div class="search-empty">${t('search_no_results')}</div>`;
          dropdown.style.display = term.length < 2 ? 'none' : 'block';
          return;
        }
        dropdown.innerHTML = scored.map(({p}) => productItem(p, term)).join('');
        dropdown.style.display = 'block';
      }
      
      // Mobile search dropdown
      function renderMobileSearch(term) {
        const dropdown = document.getElementById('searchDropdownMobile');
        if (!dropdown) return;
        const scored = scoreProducts(term, 5);
        if (scored.length === 0) {
          dropdown.innerHTML = term.length < 2 ? '' : `<div class="search-empty">${t('search_no_results')}</div>`;
          dropdown.style.display = term.length < 2 ? 'none' : 'block';
          return;
        }
        dropdown.innerHTML = scored.map(({p}) => productItem(p, term)).join('');
        dropdown.style.display = 'block';
      }
      window.performSearchMobile = function() {
        const input = document.getElementById('searchInputMobile');
        if (input) renderMobileSearch(input.value.trim());
      };
      
      // Spotlight overlay
      window.openSpotlight = function() {
        const overlay = document.getElementById('spotlightOverlay');
        if (overlay) {
          overlay.classList.add('active');
          setTimeout(() => {
            const input = document.getElementById('spotlightInput');
            if (input) { input.value = ''; input.focus(); renderSpotlight(''); }
          }, 50);
        }
      };
      window.closeSpotlight = function(e) {
        if (e && e.target !== e.currentTarget && !e.target.classList.contains('spotlight-close')) return;
        const overlay = document.getElementById('spotlightOverlay');
        if (overlay) overlay.classList.remove('active');
      };
      
      function renderSpotlight(term) {
        const container = document.getElementById('spotlightResults');
        if (!container) return;
        const scored = scoreProducts(term, 8);
        if (!term || term.length < 2) {
          container.innerHTML = `<div class="search-empty">${t('search_start_typing')}</div>`;
          return;
        }
        if (scored.length === 0) {
          container.innerHTML = `<div class="search-empty">${t('search_no_results')}</div>`;
          return;
        }
        container.innerHTML = scored.map(({p}) => productItem(p, term)).join('');
      }
      
      function initSearchListeners() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
          searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const term = searchInput.value.trim();
            searchTimeout = setTimeout(() => renderSearchDropdown(term), 150);
          });
          searchInput.addEventListener('focus', function() { renderSearchDropdown(searchInput.value.trim()); });
          searchInput.addEventListener('keydown', function(e) { if (e.key === 'Escape') { document.getElementById('searchDropdown').style.display='none'; } });
        }
        
        const spotlightInput = document.getElementById('spotlightInput');
        if (spotlightInput) {
          spotlightInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const term = spotlightInput.value.trim();
            searchTimeout = setTimeout(() => renderSpotlight(term), 150);
          });
        }
        
        const searchHeroInput = document.getElementById('searchHeroInput');
        if (searchHeroInput) {
          searchHeroInput.addEventListener('focus', openSpotlight);
        }
        
        const mobileInput = document.getElementById('searchInputMobile');
        if (mobileInput) {
          mobileInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const term = mobileInput.value.trim();
            searchTimeout = setTimeout(() => renderMobileSearch(term), 150);
          });
        }
        
        document.addEventListener('keydown', function(e) {
          if (e.key === '/' && document.activeElement && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            openSpotlight();
          }
          if (e.key === 'Escape') {
            closeSpotlight();
            const dd = document.getElementById('searchDropdown');
            if (dd) dd.style.display = 'none';
            const ddm = document.getElementById('searchDropdownMobile');
            if (ddm) ddm.style.display = 'none';
          }
        });
        
        document.addEventListener('click', function(e) {
          const searchBox = document.querySelector('.search-box');
          const dropdown = document.getElementById('searchDropdown');
          const mobileBox = document.querySelector('#mobileMenu .search-box');
          const mobileDropdown = document.getElementById('searchDropdownMobile');
          if (dropdown && searchBox && !searchBox.contains(e.target)) dropdown.style.display = 'none';
          if (mobileDropdown && mobileBox && !mobileBox.contains(e.target)) mobileDropdown.style.display = 'none';
        });
      }
      
      window.__initAdisSearch = function() {
        searchProducts = window.__adisProducts || [];
        initSearchListeners();
      };
      
      // Si los productos ya cargaron, inicializar ahora
      if (window.__adisProducts) __initAdisSearch();
      // Si no, intentar cargar directamente
      else if (!window.__adisProductsLoading) {
        window.__adisProductsLoading = true;
        fetch(ADIS_PREFIX + 'products.json')
          .then(r => r.json())
          .then(data => { window.__adisProducts = data.products || []; __initAdisSearch(); })
          .catch(() => { window.__adisProducts = []; __initAdisSearch(); });
      }
    })();

  </script>
'''
    return f"""  <footer>
    <div class="footer-logo">{logo_tag()}</div>
    <div class="footer-info">
      <strong>ADI&#39;S DISEÑO & REMODELACIÓN</strong><br>
      {i18n('footer_slogan')}<br>
      {CONTACTO['ubicacion']}<br>
      <a href="tel:{CONTACTO['tel_mx_link']}">Tel. MX: {CONTACTO['tel_mx']}</a> · <a href="tel:{CONTACTO['tel_usa_link']}">Tel. USA: {CONTACTO['tel_usa']}</a><br>
      <a href="mailto:{CONTACTO['email']}">{CONTACTO['email']}</a>
    </div>
    <div class="footer-social">
      <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO["whatsapp_msg"].replace(' ', '%20')}" target="_blank" title="{t('footer_whatsapp')}">{svg_icon('whatsapp', size=22, color='currentColor')}</a>
      <a href="{CONTACTO['facebook']}" target="_blank" title="{t('footer_facebook')}">{svg_icon('facebook', size=22, color='currentColor')}</a>
    </div>
    <div class="footer-links">
      <span>{i18n('footer_links_legal')}:</span>
      <a href="{p('nosotros.html')}">{i18n('footer_links_about')}</a>
      <a href="{p('aviso-de-privacidad.html')}">{i18n('footer_links_privacy')}</a>
    </div>
    <div class="copyright">© <span id="footer-year"></span> {i18n('footer_copyright_suffix')}</div>
  </footer>
  <script>
    (function(){{
      var y = new Date().getFullYear();
      var el = document.getElementById('footer-year');
      if (el) el.textContent = y;
    }})();
  </script>

  <!-- MOBILE BOTTOM NAV -->
  <nav class="mobile-bottom-nav">
    <a href="{p('index.html')}"><span>{svg_icon('home', size=22, color='currentColor')}</span><span>{i18n('mobile_nav_home')}</span></a>
    <a href="{p('index.html#categorias')}"><span>{svg_icon('grid', size=22, color='currentColor')}</span><span>{i18n('mobile_nav_catalog')}</span></a>
    <a href="{p('proyectos.html')}"><span>{svg_icon('image', size=22, color='currentColor')}</span><span>{i18n('mobile_nav_projects')}</span></a>
    <a href="{p('contacto.html')}"><span>{svg_icon('phone', size=22, color='currentColor')}</span><span>{i18n('mobile_nav_contact')}</span></a>
  </nav>

  <a href="https://wa.me/{CONTACTO['whatsapp']}?text={CONTACTO["whatsapp_msg"].replace(' ', '%20')}" class="whatsapp-float" target="_blank" title="{t('wa_tooltip')}" aria-label="WhatsApp">
    <svg viewBox="0 0 24 24" width="32" height="32" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.008-.57-.008-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
    <span class="wa-tooltip">{i18n('wa_tooltip')}</span>
  </a>

  <button class="chatbot-float" onclick="toggleChat()" title="{t('chatbot_title')}">{svg_icon('robot', size=28, color='#0F0F0F')}<span class="chatbot-badge" id="chatBadge">{t('chatbot_badge')}</span></button>
  <div class="chatbot-window" id="chatbotWindow">
    <div class="chatbot-header">
      <h4>{svg_icon('robot', size=20, color='#C5A059')} {i18n('chatbot_title')}</h4>
      <div class="chat-header-actions">
        <button class="chat-clear" onclick="clearAllChat()" title="{t('chatbot_new_chat')}">{svg_icon('trash', size=18, color='#E8D5A3')}</button>
        <button class="chatbot-close" onclick="toggleChat()" title="{t('chatbot_close')}">{svg_icon('x', size=18, color='#E8D5A3')}</button>
      </div>
    </div>
    <div class="chatbot-body" id="chatbotBody"></div>
  </div>


{chatbot_js.replace('__ADIS_PREFIX__', CUR_PREFIX).replace('__ADIS_LANG__', CUR_LANG).replace('__ADIS_LEADS_URL__', LEADS_URL).replace('__ADIS_REVIEWS_URL__', REVIEWS_URL)}"""


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
  <meta name="description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="{meta_keywords}">
  <meta name="geo.region" content="MX-SON">
  <meta name="geo.placename" content="Heroica Nogales, Sonora, México">
  <meta name="geo.position" content="31.3014;-110.9386">
  <meta name="ICBM" content="31.3014, -110.9386">
  <meta property="og:title" content="{t('title_index')}">
  <meta property="og:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{page_url('index.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t('title_index')}">
  <meta name="twitter:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
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
  <meta name="description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="cotizar recubrimientos Nogales, contacto ADIS, paneles PVC Sonora, wall panels Nogales AZ, remodeling materials Arizona, WhatsApp ADIS">
  <meta name="geo.region" content="MX-SON">
  <meta name="geo.placename" content="Heroica Nogales, Sonora, México">
  <meta name="geo.position" content="31.3014;-110.9386">
  <meta name="ICBM" content="31.3014, -110.9386">
  <meta property="og:title" content="Cotizar Recubrimientos Nogales Sonora · Arizona | Contacto ADIS">
  <meta property="og:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  <meta property="og:image" content="{SITE_URL}LOGO%20ADIS.png">
  <meta property="og:url" content="{page_url('contacto.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Cotizar Recubrimientos Nogales Sonora · Arizona | Contacto ADIS">
  <meta name="twitter:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
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
  <meta name="description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="ADIS Diseño Remodelación, nosotros ADIS, recubrimientos Nogales, paneles PVC Sonora, remodeling Arizona">
  <meta property="og:title" content="{t('title_nosotros')}">
  <meta property="og:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  {og_image_tags(f'{SITE_URL}LOGO%20ADIS.png')}
  <meta property="og:url" content="{page_url('nosotros.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:title" content="{t('title_nosotros')}">
  <meta name="twitter:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
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
  <meta name="description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  <meta name="keywords" content="aviso de privacidad ADIS, proteccion de datos, privacidad Nogales, privacy notice">
  <meta property="og:title" content="{t('title_privacidad')}">
  <meta property="og:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
  {og_image_tags(f'{SITE_URL}LOGO%20ADIS.png')}
  <meta property="og:url" content="{page_url('aviso-de-privacidad.html')}">
  <meta property="og:type" content="website">
  <meta name="twitter:title" content="{t('title_privacidad')}">
  <meta name="twitter:description" content="{(meta_desc_en if CUR_LANG == 'en' else meta_desc_es)}">
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

    if CUR_LANG == 'en':
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
    seo_entry = CAT_SEO.get(cat['name'], {}).get(CUR_LANG) or CAT_SEO.get(cat['name'], {}).get('es')
    if seo_entry:
        cat_title, cat_desc_template = seo_entry
    elif CUR_LANG == 'en':
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


def video_caption(vid):
    """Devuelve un título legible para un video; hace fallback al nombre de archivo."""
    return VIDEO_CAPTIONS.get(vid, Path(vid).stem.replace('-', ' ').replace('_', ' ').title())


def video_mime_type(vid):
    """Devuelve el MIME type correcto según la extensión del video."""
    ext = Path(vid).suffix.lower()
    return {'mp4': 'video/mp4', 'mov': 'video/quicktime', 'webm': 'video/webm'}.get(ext, 'video/mp4')


def sync_media():
    """Copia TODAS las fotos y videos de Material de Facebock a media/ con nombres limpios (sync incremental)."""
    src_dir = BASE_DIR / 'Material de Facebock'
    media_dir = OUTPUT_DIR / 'media'
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
        elif re.match(r'^(antes|despues)(\s+\d+)?\.(jpg|jpeg|png)$', fname, re.IGNORECASE):
            # Conservar nombres de pares antes/después para que generate_proyectos() los detecte
            dst_name = fname
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
        if HAS_PIL and dst_name.lower().endswith(img_exts):
            p = Path(dst_name)
            expected_names.add(p.with_suffix('.webp').name.lower())
            expected_names.add((p.parent / (p.stem + '-600w.webp')).name.lower())
    
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
    webp_total = 0
    errors = []
    for src_path, dst_name in mapping.items():
        if not src_path.exists():
            errors.append(f"  [ERROR] No existe: {src_path}")
            continue
        dst = media_dir / dst_name
        if dst_name.lower().endswith(img_exts):
            file_copied = _generate_image_variants(src_path, dst)
            if webp_path_for := _webp_path_for(dst):
                if webp_path_for[0].exists():
                    webp_total += 1
        else:
            file_copied = _copy_if_needed(src_path, dst)
        if file_copied:
            copied += 1
    if errors:
        print(f"ADVERTENCIA: {len(errors)} archivos de media no se pudieron copiar:")
        for e in errors[:10]:
            print(e)
    print(f"Media sincronizada: {copied} copiados, {removed} huérfanos eliminados ({auto_img} imgs + {auto_pvc} pvc + {auto_vid} vids)")
    print(f"Media WebP listas: {webp_total}")


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


def generate_lead_banner():
    """Genera banner de captacion de leads que envia a WhatsApp."""
    return f'''
  <!-- LEAD CAPTURE -->
  <section class="lead-section reveal" id="cotizar">
    <div class="lead-container">
      <h2>{i18n('lead_title')}</h2>
      <p>{i18n('lead_subtitle')}</p>
      <form class="lead-form" onsubmit="sendLead(event)">
        <input type="text" id="leadName" placeholder="{t('lead_name')}" required>
        <input type="tel" id="leadPhone" placeholder="{t('lead_phone')}" required>
        <textarea id="leadProject" rows="3" placeholder="{t('lead_project_placeholder')}" required></textarea>
        <button type="submit" class="btn-primary btn-wa">{svg_icon('whatsapp', size=18, color='currentColor')} {i18n('lead_button')}</button>
      </form>
      <p class="lead-note">{i18n('lead_note')}</p>
    </div>
  </section>
  <script>
    function sendLead(e) {{
      e.preventDefault();
      const name = document.getElementById('leadName').value.trim();
      const phone = document.getElementById('leadPhone').value.trim();
      const project = document.getElementById('leadProject').value.trim();
      const msg = 'Hola ADIS, mi nombre es ' + name + ' y mi telefono es ' + phone + '. Tengo un proyecto de: ' + project + '. Me gustaria recibir asesoria.';
      window.open('https://wa.me/{CONTACTO['whatsapp']}?text=' + encodeURIComponent(msg), '_blank');
      if (typeof gtag !== 'undefined') gtag('event','lead_whatsapp',{{'location':'lead_banner'}});
      e.target.reset();
    }}
  </script>
'''


def generate_testimonios():
    """Genera formulario de testimonios que envía a WhatsApp para revisión manual."""
    return f'''
  <!-- TESTIMONIOS -->
  <section class="section-wrap reveal" style="padding-top: 2rem;">
    <div class="section-header">
      <h2>{i18n('testimonials_title')}</h2>
      <div class="divider"></div>
      <p>{i18n('testimonials_subtitle', html=True)}</p>
    </div>
    <div id="reviewsGrid" style="max-width: 1100px; margin: 0 auto; padding: 0 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <span class="review-badge">{i18n('reviews_badge')}</span>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">{i18n('testimonial_maria_text', html=True)}</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">MG</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">{i18n('testimonial_maria_name')}</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — {i18n('testimonial_maria_meta')}</div>
          </div>
        </div>
      </div>
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <span class="review-badge">{i18n('reviews_badge')}</span>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">{i18n('testimonial_carlos_text', html=True)}</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">CR</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">{i18n('testimonial_carlos_name')}</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — {i18n('testimonial_carlos_meta')}</div>
          </div>
        </div>
      </div>
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <span class="review-badge">{i18n('reviews_badge')}</span>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">{i18n('testimonial_lopez_text', html=True)}</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">FL</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">{i18n('testimonial_lopez_name')}</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — {i18n('testimonial_lopez_meta')}</div>
          </div>
        </div>
      </div>
      <div style="background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;">
        <div style="font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;">"</div>
        <span class="review-badge">{i18n('reviews_badge')}</span>
        <p style="font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;">{i18n('testimonial_roberto_text', html=True)}</p>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;">RM</div>
          <div>
            <div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">{i18n('testimonial_roberto_name')}</div>
            <div style="font-size: 0.75rem; color: var(--gold);">&#11088;&#11088;&#11088;&#11088;&#11088; — {i18n('testimonial_roberto_meta')}</div>
          </div>
        </div>
      </div>
    </div>
    <div style="max-width: 600px; margin: 0 auto; padding: 0 1rem;">
      <form id="testimonioForm" onsubmit="enviarTestimonio(event)" style="display: flex; flex-direction: column; gap: 1rem;">
        <input type="text" id="tNombre" placeholder="{t('testimonials_name')}" required
          style="padding: 0.9rem 1.2rem; background: rgba(42,42,42,0.8); border: 1px solid rgba(197,160,89,0.3); border-radius: 8px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 0.9rem; backdrop-filter: blur(8px); transition: all 0.3s;"
          onfocus="this.style.borderColor='var(--gold)';this.style.boxShadow='0 0 15px rgba(197,160,89,0.15)'" onblur="this.style.borderColor='rgba(197,160,89,0.3)';this.style.boxShadow='none'">
        <textarea id="tComentario" placeholder="{t('testimonials_comment')}" required rows="4"
          style="padding: 0.9rem 1.2rem; background: rgba(42,42,42,0.8); border: 1px solid rgba(197,160,89,0.3); border-radius: 8px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 0.9rem; backdrop-filter: blur(8px); resize: vertical; transition: all 0.3s;"
          onfocus="this.style.borderColor='var(--gold)';this.style.boxShadow='0 0 15px rgba(197,160,89,0.15)'" onblur="this.style.borderColor='rgba(197,160,89,0.3)';this.style.boxShadow='none'"></textarea>
        <input type="text" id="tProducto" placeholder="{t('testimonials_product')}"
          style="padding: 0.9rem 1.2rem; background: rgba(42,42,42,0.8); border: 1px solid rgba(197,160,89,0.3); border-radius: 8px; color: var(--white); font-family: 'Montserrat', sans-serif; font-size: 0.9rem; backdrop-filter: blur(8px); transition: all 0.3s;"
          onfocus="this.style.borderColor='var(--gold)';this.style.boxShadow='0 0 15px rgba(197,160,89,0.15)'" onblur="this.style.borderColor='rgba(197,160,89,0.3)';this.style.boxShadow='none'">
        <button type="submit" class="btn-primary" style="align-self: center; margin-top: 0.5rem; display:inline-flex; align-items:center; gap:0.5rem;">{svg_icon('send', size=18, color='currentColor')} {i18n('testimonials_send')}</button>
      </form>
      <div style="text-align: center; margin-top: 1.2rem; font-size: 0.8rem; color: rgba(245,245,245,0.5); line-height: 1.6;">
        {i18n('testimonials_review', html=True)}<br>
        {i18n('testimonials_whatsapp', html=True)}
        <a href="https://wa.me/15208392877?text=Hola%20ADIS,%20quiero%20dejar%20un%20testimonio" target="_blank" style="color: var(--gold); text-decoration: none; font-weight: 600; display:inline-flex; align-items:center; gap:0.3rem;">{svg_icon('chat', size=14)} WhatsApp</a>
      </div>
    </div>
    <div class="reviews-cta">
      <a href="{CONTACTO.get('google_business_url') or 'https://www.google.com/search?q=ADIS+Dise%C3%B1o+y+Remodelaci%C3%B3n+Nogales+rese%C3%B1as'}" target="_blank" class="btn-outline" onclick="gtag('event','google_reviews_click',{{'location':'testimonials'}})">{i18n('reviews_google_cta')}</a>
    </div>
  </section>
  <script>
    function enviarTestimonio(e) {{
      e.preventDefault();
      const nombre = document.getElementById('tNombre').value.trim();
      const comentario = document.getElementById('tComentario').value.trim();
      const producto = document.getElementById('tProducto').value.trim();
      let msg = 'Hola ADIS, soy ' + nombre + '. Quiero dejar un testimonio:';
      msg += '%0A%0A' + comentario;
      msg += '%0A%0AProducto/Categoría: ' + (producto || 'No especificado');
      msg += '%0A%0APágina: ' + window.location.href;
      window.open('https://wa.me/15208392877?text=' + encodeURIComponent(msg.replace(/%0A/g, '\\n')), '_blank');
      alert('{t("testimonial_thanks")}' + nombre + '{t("testimonial_thanks_end")}');
      e.target.reset();
    }}

    // Resenas en vivo desde Google Sheets (via Apps Script). Si falla o no hay URL
    // configurada, se conservan las tarjetas estaticas generadas.
    (function() {{
      var grid = document.getElementById('reviewsGrid');
      if (!grid || typeof ADIS_REVIEWS_URL !== 'string' || !ADIS_REVIEWS_URL) return;
      var CARD = 'background: rgba(42,42,42,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(197,160,89,0.2); border-radius: 12px; padding: 1.8rem; position: relative;';
      var QUOTE = 'font-size: 3rem; color: var(--gold); opacity: 0.3; position: absolute; top: 0.5rem; right: 1rem; font-family: Georgia, serif;';
      var TEXT = 'font-size: 0.9rem; color: rgba(245,245,245,0.8); line-height: 1.7; margin-bottom: 1rem; font-style: italic;';
      var AVATAR = 'width: 40px; height: 40px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; color: var(--black); font-weight: 700; font-size: 0.9rem;';
      var tried = false;
      function esc(s) {{ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {{ return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]; }}); }}
      function cardHtml(r) {{
        var words = String(r.nombre || '?').trim().split(/\\s+/);
        var initials = words.map(function(w) {{ return w.charAt(0); }}).join('').substring(0, 2).toUpperCase();
        var n = Math.max(1, Math.min(5, parseInt(r.estrellas, 10) || 5));
        var stars = '';
        for (var i = 0; i < n; i++) stars += '\u2B50';
        return '<div style="' + CARD + '">' +
          '<div style="' + QUOTE + '">"</div>' +
          '<span class="review-badge">Google</span>' +
          '<p style="' + TEXT + '">' + esc(r.texto) + '</p>' +
          '<div style="display: flex; align-items: center; gap: 0.8rem;">' +
            '<div style="' + AVATAR + '">' + esc(initials) + '</div>' +
            '<div><div style="font-size: 0.85rem; color: var(--white); font-weight: 600;">' + esc(r.nombre) + '</div>' +
            '<div style="font-size: 0.75rem; color: var(--gold);">' + stars + (r.fecha ? ' — ' + esc(r.fecha) : '') + '</div></div>' +
          '</div></div>';
      }}
      function load() {{
        if (tried) return; tried = true;
        fetch(ADIS_REVIEWS_URL + '?action=reviews').then(function(res) {{ return res.json(); }}).then(function(data) {{
          if (data && data.ok && data.reviews && data.reviews.length) {{
            grid.innerHTML = data.reviews.map(cardHtml).join('');
          }}
        }}).catch(function() {{}});
      }}
      if ('IntersectionObserver' in window) {{
        var io = new IntersectionObserver(function(entries) {{
          entries.forEach(function(en) {{ if (en.isIntersecting) {{ load(); io.disconnect(); }} }});
        }}, {{ rootMargin: '300px' }});
        io.observe(grid);
      }} else {{ load(); }}
    }})();
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
        if len(desc) > 130:
            desc_trunc = desc[:127] + '...'
            card_p = f'''<p class="sq-card-text">
      <span class="sq-short">{desc_trunc}</span>
      <span class="sq-full" style="display:none">{desc}</span>
      <span class="sq-card-readmore" onclick="sqToggle(this)">{t('sq_card_readmore')}</span>
    </p>'''
        else:
            card_p = f'<p class="sq-card-text">{desc}</p>'
        cards += f'''      <div class="sq-card">
        <span class="sq-card-number">{item_count:02d}</span>
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
        print(f"✅ sabias-que-{slug}.html generado ({cat_name_disp}) [{CUR_LANG}]")
    
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
        shutil.copy2(admin_src, OUTPUT_DIR / 'admin.html')
        print("admin.html copiado al sitio")

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
