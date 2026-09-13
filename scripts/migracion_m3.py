#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración M3 (one-off): divide generar_web.py en el paquete 10_SITIO_PUBLICO/sitio/.

Usa AST para obtener rangos exactos de cada statement de nivel superior
(inmune a comentarios dentro de strings). Verifica cobertura total y emite
generar_web.py como orquestador fino. La salida del build debe ser byte-identica.
"""
import ast, pathlib, sys

ROOT = pathlib.Path(r'C:\Users\Carlos\Desktop\Pagina')
GW = ROOT / 'generar_web.py'
PKG = ROOT / '10_SITIO_PUBLICO' / 'sitio'
PKG.mkdir(parents=True, exist_ok=True)

source = GW.read_text(encoding='utf-8')
lines = source.splitlines(keepends=True)
tree = ast.parse(source)

FUNC_MAP = {
    # infra
    't': 'infra', '_prefix_links': 'infra', 'i18n': 'infra', 'i18n_fmt': 'infra',
    'set_lang': 'infra', 'p': 'infra', 'hreflang_tags': 'infra', 'out_dir': 'infra',
    'page_url': 'infra', 'html_lang': 'infra', 'cat_display': 'infra',
    'subcat_display': 'infra', 'product_display': 'infra', 'og_locale': 'infra',
    # datos
    'research_cat_display': 'datos', 'research_data': 'datos', 'is_image': 'datos',
    'is_ficha': 'datos', 'scan_catalog': 'datos', 'get_products': 'datos',
    'get_ficha': 'datos', 'sync_images': 'datos', '_copy_if_needed': 'datos',
    '_webp_path_for': 'datos', '_ensure_webp': 'datos', '_generate_image_variants': 'datos',
    'video_caption': 'datos', 'video_mime_type': 'datos', 'sync_media': 'datos',
    'mailto_link': 'datos', 'generate_specs_table': 'datos',
    # seo
    'ga_script': 'seo', 'fb_pixel_script': 'seo', 'head_common': 'seo',
    'og_image_tags': 'seo', 'breadcrumb_html': 'seo', 'organization_schema': 'seo',
    'website_schema': 'seo', 'breadcrumb_schema': 'seo', 'product_schema': 'seo',
    'faqpage_schema': 'seo', 'generate_sitemap': 'seo', 'generate_robots': 'seo',
    # componentes
    'generate_style': 'componentes', 'translate_script': 'componentes',
    'translate_toggle': 'componentes', 'tracking_script': 'componentes',
    'generate_research_html': 'componentes', 'transformations_html': 'componentes',
    'calculator_html': 'componentes', 'modal_cotizar_html': 'componentes',
    '_extract_keywords': 'componentes', 'category_filters_html': 'componentes',
    'category_filters_js': 'componentes', 'webp_srcset': 'componentes',
    'ensure_logo_webp': 'componentes', 'logo_tag': 'componentes', 'picture_tag': 'componentes',
    'product_card_html': 'componentes', 'generate_header': 'componentes',
    'generate_footer': 'componentes', 'generate_lead_banner': 'componentes',
    'generate_testimonios': 'componentes', '_extract_curiosos_cards': 'componentes',
    '_extract_faqs_html': 'componentes', '_extract_curiosos_data': 'componentes',
    '_extract_faqs_data': 'componentes',
    # paginas
    'generate_index': 'paginas', 'generate_contacto': 'paginas',
    'generate_nosotros': 'paginas', 'generate_privacy': 'paginas',
    'generate_category_page': 'paginas', 'generate_sabias_que': 'paginas',
    'generate_proyectos': 'paginas',
    # build
    'main': 'build',
}

ASSIGN_MAP = {
    'OUTPUT_DIR': 'infra', 'CUR_LANG': 'infra', 'CUR_PREFIX': 'infra',
    'PRICE_DATA': 'infra', 'CSS': 'componentes', 'PARTICLES_JS': 'componentes',
    '_CAT_TR': 'infra', 'RESEARCH_DATA': 'infra', 'RESEARCH_DATA_EN': 'infra',
    'BASE_DIR': 'infra', 'CORE_DIR': 'infra', 'PLATAFORMA': 'infra',
    'CATALOG_DIR': 'infra', 'LEADS_URL': 'infra', 'REVIEWS_URL': 'infra', 'SITE_URL': 'infra',
}

segments = []  # (module, lineno_start, lineno_end, descr)
top = [n for n in tree.body]
for node in top:
    name = None
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        mod = FUNC_MAP.get(node.name)
        assert mod, f'funcion sin asignar de modulo: {node.name}'
        segments.append((mod, node.lineno, node.end_lineno, f'def {node.name}'))
    elif isinstance(node, ast.Assign):
        tgt = node.targets[0]
        var = getattr(tgt, 'id', None) or getattr(getattr(tgt, 'value', None), 'id', None)
        mod = ASSIGN_MAP.get(var, 'infra')  # assigns no mapeados: config global -> infra
        segments.append((mod, node.lineno, node.end_lineno, var))
    elif isinstance(node, ast.Try):
        names = set()
        for h in node.body:
            for t in ast.walk(h):
                if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store):
                    names.add(t.id)
        if 'HAS_PIL' in names:
            segments.append(('infra', node.lineno, node.end_lineno, 'HAS_PIL'))
        elif '_CAT_TR' in names:
            segments.append(('infra', node.lineno, node.end_lineno, '_CAT_TR load'))
        elif any(n.startswith('RESEARCH_DATA') for n in names):
            segments.append(('infra', node.lineno, node.end_lineno, 'RESEARCH load'))
        else:
            raise AssertionError(f'Try sin clasificar linea {node.lineno}')
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        segments.append(('infra', node.lineno, node.end_lineno, 'import'))
    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
        segments.append(('infra', node.lineno, node.end_lineno, 'docstring'))
    elif isinstance(node, ast.Expr):
        # llamadas de nivel superior: sys.path.insert(...) tras la config
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        assert names == {'sys', 'path'} or 'sys' in names, f'Expr call sin clasificar linea {node.lineno}: {names}'
        segments.append(('infra', node.lineno, node.end_lineno, 'sys.path.insert'))
    elif isinstance(node, ast.If):
        if isinstance(node.test, ast.Call) and getattr(node.test.func, 'id', '') == 'hasattr':
            segments.append(('infra', node.lineno, node.end_lineno, 'stdout reconfigure'))
            continue
        assert any(isinstance(t, ast.Compare) and getattr(t.left, 'id', '') == '__name__'
                   for t in ast.walk(node.test)), f'If sin clasificar linea {node.lineno}'
        segments.append(('build', node.lineno, node.end_lineno, '__main__'))
    else:
        raise AssertionError(f'nodo sin clasificar: {type(node).__name__} linea {node.lineno}')

# Gaps entre statements (comentarios de seccion sueltos): se adjuntan al statement SIGUIENTE
by_start = sorted(segments, key=lambda s: s[1])
chunks = {}  # module -> list of (start,end) line ranges incluidos gaps previos
covered = set()
for i, (mod, s, e, d) in enumerate(by_start):
    gs = s
    if i > 0:
        prev_end = by_start[i - 1][2]
        if prev_end + 1 < s:
            gs = prev_end + 1  # gap de comentarios va con este statement
    chunks.setdefault(mod, []).append((gs, e))
    covered.update(range(gs, e + 1))

# El espacio entre statements consecutivos (lineas en blanco) se pierde: irrelevante.
HEADERS = {
    'infra': ('infra', ['from .infra import *  # noqa  (base; sin imports relativos)']),
    'datos': ('datos', ['from .infra import *  # noqa']),
    'seo': ('seo', ['from .infra import *  # noqa']),
    'componentes': ('componentes', ['from .infra import *  # noqa', 'from .datos import *  # noqa', 'from .seo import *  # noqa']),
    'paginas': ('paginas', ['from .infra import *  # noqa', 'from .datos import *  # noqa', 'from .seo import *  # noqa', 'from .componentes import *  # noqa']),
    'build': ('build', ['from .infra import *  # noqa', 'from .infra import _CAT_TR  # nombre con guion bajo: no sale en import *',
                        'from .datos import *  # noqa', 'from .seo import *  # noqa',
                        'from .componentes import *  # noqa', 'from .paginas import *  # noqa']),
}
MODULE_DOC = {
    'infra': 'Infraestructura del generador: config, estado de idioma, datos maestros.',
    'datos': 'Datos: catalogo (Drive), imagenes, media, investigacion.',
    'seo': 'SEO: schemas, sitemap, robots, analytics.',
    'componentes': 'Componentes: estilos, header/footer, chatbot, buscador, tarjetas, modales.',
    'paginas': 'Paginas: index, categorias, contacto, nosotros, proyectos, sabias-que, privacidad.',
    'build': 'Orquestacion del build (main).',
}
for mod, ranges in chunks.items():
    parts = [f'# -*- coding: utf-8 -*-\n"""{MODULE_DOC[mod]} Extraido de generar_web.py en M3 (salida byte-identica)."""\n']
    _, imps = HEADERS[mod]
    if mod != 'infra':
        parts.append('\n'.join(imps) + '\n')
    for (s, e) in ranges:
        parts.append(''.join(lines[s - 1:e]))
        parts.append('\n\n')
    (PKG / f'{mod}.py').write_text(''.join(parts), encoding='utf-8')
    print(f'OK  {mod}.py  ({sum(e - s + 1 for s, e in ranges)} lineas)')

(PKG / '__init__.py').write_text('# Paquete del generador del sitio (M3).\n', encoding='utf-8')

orq = '''# -*- coding: utf-8 -*-
"""Generador del sitio ADIS — ORQUESTADOR (M3).

Toda la logica vive en 10_SITIO_PUBLICO/sitio/ (infra, datos, seo, componentes,
paginas, build). Este archivo solo arranca el build para no romper el habito de
ejecutar `python generar_web.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / '10_SITIO_PUBLICO'))

from sitio.build import main

if __name__ == '__main__':
    main()
'''
GW.write_text(orq, encoding='utf-8')
print('OK  generar_web.py -> orquestador')
print(f'TOTAL funciones extraidas: {len([s for s in segments if s[3].startswith("def")])}')
