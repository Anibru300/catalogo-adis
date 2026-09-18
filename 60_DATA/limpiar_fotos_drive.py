# -*- coding: utf-8 -*-
"""Limpia fotos huérfanas de la carpeta Drive 'ADIS FOTOS PRODUCTOS'.

Una foto es huérfana cuando ningún producto la referencia en foto..foto_4
(las de prueba/diagnóstico). El backend las manda a la papelera de Drive
(se pueden recuperar desde drive.google.com/drive/trash durante 30 días).

Requiere backend con el endpoint 'limpiar_fotos_drive' (redeploy del script).

Uso:
    python 60_DATA/limpiar_fotos_drive.py             -> solo SIMULA (lista candidatas)
    python 60_DATA/limpiar_fotos_drive.py --ejecutar  -> realmente las borra
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
EJECUTAR = '--ejecutar' in sys.argv


def _cfg():
    cfg = json.loads((BASE / '00_CORE' / 'config' / 'plataforma.json').read_text(encoding='utf-8'))
    return cfg['url_backend']


def main():
    url_backend = _cfg()
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

        payload = {'tipo': 'limpiar_fotos_drive', 'token': token}
        if EJECUTAR:
            payload['ejecutar'] = True
        d = post(payload)
        if not d.get('ok'):
            sys.exit(f'ERROR: {d}')

        print('SIMULACIÓN (sin borrar):' if d.get('dry_run') else 'EJECUTADO:')
        print(f"  Candidatas: {d.get('total', 0)}")
        for c in d.get('candidatos', [])[:50]:
            print('   -', c)
        if d.get('total', 0) > len(d.get('candidatos', [])):
            print(f"   … y {d['total'] - len(d['candidatos'])} más")
        if d.get('dry_run') and d.get('total'):
            print()
            print('Para borrarlas de verdad: python 60_DATA/limpiar_fotos_drive.py --ejecutar')
        br.close()


if __name__ == '__main__':
    main()
