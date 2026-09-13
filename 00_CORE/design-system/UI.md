# UI — Guia del sistema de diseno (estado M1)

## Archivos
- `sitio-publico.css` (89 KB): CSS completo del sitio, extraido VERBATIM de `generar_web.py` en M1.
  El generador lo lee y minifica a `public/style.css`. NO editar a mano `public/style.css`.

## Mapa de contenidos (indices aproximados dentro del archivo)
- Tokens `:root` (linea 1): `--gold #C5A059`, `--gold-light #E8D5A3`, `--black #0F0F0F`,
  `--dark #1A1A1A`, `--gray #2A2A2A`, `--light #F5F5F5`, `--white #FFFFFF`. Tipografia: Montserrat.
- Base y reset (inicio) · header/topbar/mega-menu · heroes y breadcrumbs · tarjetas de
  producto/categoria · carruseles y lightbox · calculadora · modales (cotizar) · chatbot y
  buscador · tablas · formularios · badges · footer y bottom-nav · responsive (media queries).

## Segundo tema: panel admin
- CSS propio embebido en `admin/index.html` L10-293 (mismas variables base, superficie oscura).
- NO extraido en M1 (M4 lo modulariza sin cambios visuales). Unificacion visual: fase posterior.

## Reglas de uso
1. Dorado = acento (~10%); superficies neutras el resto.
2. Componentes nuevos del sitio: agregarlos en este archivo (el generador lo minifica).
3. No duplicar reglas entre modulos: todo estilo del sitio publico vive aqui.
