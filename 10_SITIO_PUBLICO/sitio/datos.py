# -*- coding: utf-8 -*-
"""Datos: catalogo (Drive), imagenes, media, investigacion. Extraido de generar_web.py en M3 (salida byte-identica)."""
from . import infra
from .infra import *  # noqa


def research_cat_display(cat_key):
    """Nombre visible de una categoría de investigación según idioma."""
    if infra.CUR_LANG == 'en':
        return RESEARCH_CAT_EN.get(cat_key, cat_key.title())
    return cat_key.title()




def research_data(cat_key):
    """Datos de investigación de una categoría según idioma de generación."""
    if infra.CUR_LANG == 'en':
        return RESEARCH_DATA_EN.get(cat_key) or RESEARCH_DATA.get(cat_key, {})
    return RESEARCH_DATA.get(cat_key, {})



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




def is_image(filename):
    return filename.lower().endswith(IMG_EXTS)




def is_ficha(filename):
    """Detecta si un archivo es ficha técnica."""
    return 'ficha' in filename.lower() and is_image(filename)






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




def video_caption(vid):
    """Devuelve un título legible para un video; hace fallback al nombre de archivo."""
    return VIDEO_CAPTIONS.get(vid, Path(vid).stem.replace('-', ' ').replace('_', ' ').title())




def video_mime_type(vid):
    """Devuelve el MIME type correcto según la extensión del video."""
    ext = Path(vid).suffix.lower()
    return {'mp4': 'video/mp4', 'mov': 'video/quicktime', 'webm': 'video/webm'}.get(ext, 'video/mp4')




def sync_media():
    """Copia TODAS las fotos y videos de Material de Facebock a media/ con nombres limpios (sync incremental)."""
    src_cfg = Path(PLATAFORMA['material_media_dir'])
    src_dir = src_cfg if src_cfg.is_absolute() else BASE_DIR / src_cfg
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


