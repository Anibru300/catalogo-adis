# -*- coding: utf-8 -*-
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
