#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Concatena los .gs modulares en admin/apps-script.gs (artefacto de despliegue).

El orden del MANIFIESTO es funcional: las asignaciones var de nivel superior en
core.gs deben ejecutarse antes que cualquier llamada en tiempo de carga.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFIESTO = [
    '00_CORE/backend/core.gs',
    '09_MARKETING/backend/analitica.gs',
]

parts = [(ROOT / rel).read_bytes().decode('utf-8') for rel in MANIFIESTO]
out = ''.join(parts)
if not out.endswith('\n'):
    out += '\n'
(ROOT / 'admin' / 'apps-script.gs').write_bytes(out.encode('utf-8'))
print(f'admin/apps-script.gs regenerado ({len(MANIFIESTO)} partes, {len(out.splitlines())} lineas)')
