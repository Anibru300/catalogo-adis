# -*- coding: utf-8 -*-
"""P8 - Sincroniza fotos subidas al panel (URLs de Drive) hacia el catalogo local.

Flujo:
  1. (Previo)  60_DATA/exportar_productos.py  -> dataset_maestro.json actualizado
  2. (Este)    baja cada foto Drive a la carpeta del catalogo local (CATALOG_DIR,
               espejando la ruta img/<categoria>/<subcategoria>/...) y le pide al
               backend reescribir la hoja con la ruta local (localizar_fotos).
  3. (Despues) python generar_web.py && git push  -> la foto sale en el sitio web.

Asi una foto subida desde cualquier computadora termina en la pagina publica.

Uso:
    "C:\\...\\Python313\\python" 60_DATA/sync_fotos_drive.py
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
DATASET = BASE / '60_DATA' / 'dataset_maestro.json'
CAMPOS = [('foto', ''), ('foto_2', '_2'), ('foto_3', '_3'), ('foto_4', '_4')]


def _cfg():
    cfg = json.loads((BASE / '00_CORE' / 'config' / 'plataforma.json').read_text(encoding='utf-8'))
    return cfg['url_backend'], Path(cfg['catalog_dir'])


def _es_drive(url):
    return isinstance(url, str) and url.startswith('https://drive.google.com/')


def _id_drive(url):
    m = re.search(r'[?&]id=([\w-]+)', url)
    return m.group(1) if m else None


def _safe(nombre):
    return re.sub(r'[^\w\-]+', '_', str(nombre))[:50] or 'producto'


def main():
    if not DATASET.exists():
        sys.exit('ERROR: no existe 60_DATA/dataset_maestro.json. Corre primero 60_DATA/exportar_productos.py')
    url_backend, catalog_dir = _cfg()
    if not catalog_dir.exists():
        sys.exit(f'ERROR: no existe la carpeta del catalogo: {catalog_dir}')

    dataset = json.loads(DATASET.read_text(encoding='utf-8'))
    productos = dataset['productos']

    bajadas, saltados, errores = 0, 0, []

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        pg.goto('about:blank')

        def post(payload):
            r = pg.evaluate("""async ({URL, payload}) => {
              const res = await fetch(URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON.stringify(payload)});
              return await res.text();
            }""", {'URL': url_backend, 'payload': payload})
            return json.loads(r)

        login = post({'tipo': 'login', 'usuario': 'Adis', 'clave': 'Adisdiseño2026'})
        if not login.get('ok'):
            sys.exit(f'ERROR login: {login}')
        token = login['token']

        for p in productos:
            valores = {c: str(p.get(c, '') or '').strip() for c, _ in CAMPOS}
            if not any(_es_drive(v) for v in valores.values()):
                continue
            # Carpeta destino REAL: se localiza el archivo de una foto LOCAL del
            # producto (busqueda por nombre en CATALOGO FINAL; las carpetas reales
            # son p. ej. "1. Placas PVC", no los slugs web img/1-placas-pvc/...).
            locales = [v for v in valores.values() if v and not _es_drive(v)]
            if not locales:
                saltados += 1
                print(f"  SALTADO {p.get('codigo')}: sin foto local de referencia (¿producto nuevo? "
                      f"ponle la primera foto en el panel o en el catalogo).")
                continue
            base = next(catalog_dir.rglob(Path(locales[0].replace('\\', '/')).name), None)
            if base is None:
                saltados += 1
                print(f"  SALTADO {p.get('codigo')}: no se encontro {Path(locales[0]).name} en el catalogo local.")
                continue
            dir_destino = base.parent
            ruta_local = Path(locales[0].replace('\\', '/'))
            dir_rel = ruta_local.parent                      # img/<cat>/<sub> (para reescribir la hoja)
            stem_base = base.stem                            # p. ej. 'Adler' -> extras 'Adler-2.jpg'

            cambios = {}
            for campo, sufijo in CAMPOS:
                val = valores[campo]
                if not _es_drive(val):
                    continue
                fid = _id_drive(val)
                if not fid:
                    errores.append(f"{p.get('codigo')} {campo}: URL sin id: {val}")
                    continue
                # Convencion de galeria del sitio: 'Adler-2.jpg' (sufijo '_2' -> '-2').
                # La foto principal conserva su nombre de catalogo existente.
                if campo == 'foto':
                    nombre_arch = base.name
                else:
                    nombre_arch = f"{stem_base}{sufijo.replace('_', '-')}.jpg"
                destino = dir_destino / nombre_arch
                try:
                    resp = pg.request.get(f'https://drive.google.com/thumbnail?id={fid}&sz=w2000')
                    if resp.status != 200 or len(resp.body()) < 500:
                        errores.append(f"{p.get('codigo')} {campo}: Drive respondio {resp.status}")
                        continue
                    destino.write_bytes(resp.body())
                    cambios[campo] = (dir_rel / nombre_arch).as_posix()
                    bajadas += 1
                    print(f"  OK {p.get('codigo')} {campo} -> {cambios[campo]} ({len(resp.body())//1024} KB)")
                except Exception as e:
                    errores.append(f"{p.get('codigo')} {campo}: {e}")

            if cambios:
                r = post({'tipo': 'localizar_fotos', 'token': token, 'id': p['id'], **cambios})
                if not r.get('ok'):
                    errores.append(f"{p.get('codigo')} localizar_fotos: {r}")
                else:
                    print(f"  HOJA actualizada: {p.get('codigo')} ({len(cambios)} campo(s))")
        br.close()

    print()
    print(f'Fotos bajadas: {bajadas} | productos saltados: {saltados} | errores: {len(errores)}')
    for e in errores:
        print('  ERROR:', e)
    if bajadas:
        print()
        print('Siguiente paso: python generar_web.py && git push (la foto sale en el sitio web).')
    sys.exit(1 if errores else 0)


if __name__ == '__main__':
    main()
