# 🌐 10_SITIO_PUBLICO — Sitio Web, Chatbot, Buscador y Tracker

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§10 diseño, §11 i18n,
> §12 conexiones, §13 build). Es el módulo **más grande en líneas** (todo vive
> hoy dentro de `generar_web.py`, 8 944 líneas) y el único que despliega al
> dominio público. Fuente: `generar_web.py`, `public/` (salida), `.github/
> workflows/deploy.yml`.

## IDENTIDAD

- **Objetivo**: la cara pública de ADIS: catálogo de productos bilingüe
  ES/EN con SEO, chatbot de ventas, buscador global, calculadora de m²,
  captación de leads y reseñas — todo estático, rápido y desplegable en Pages.
- **Responsabilidad**: generar `public/` completo (48 páginas, style.css,
  products.json, sitemap, robots, imágenes webp, media).
- **Problema que resuelve**: vender sin dependencia de marketplaces: el sitio
  atrae, informa, cotiza vía WhatsApp y empuja leads al ERP.

## ALCANCE

- **Hace**: páginas (index, 9 categorías con subcategorías y fichas, contacto,
  nosotros, proyectos, privacidad, 10 páginas "¿Sabías que?"), versión EN
  completa con hreflang, SEO (schema.org, OpenGraph, sitemap, canonical),
  chatbot bilingüe con base de conocimiento y cotización guiada, buscador
  global (`/` y spotlight), calculadora de m² con CTA a WhatsApp, slider
  antes/después, tracker de visitas, formulario de contacto (lead + WhatsApp),
  carga de reseñas activas, imágenes responsive (webp + srcset), i18n ES/EN.
- **NO hace**: gestionar el negocio (es el ERP, módulos 01–09), servir API
  (solo consume los 3 endpoints públicos), almacenar datos.
- **Pertenecen aquí**: el generador, sus componentes y la salida `public/`.

## DATOS

- **Fuentes**: catálogo en Drive (`G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL` —
  solo lectura), `Material de Facebock/` (media, desde P2 dentro de CATALOG_DIR en Drive),
  `investigacion_data.json`/`_en.json` (FAQs y curiosos por categoría),
  `traducciones_productos.json` (nombres ES→EN), `assets/` (logo, QR).
- **Genera**: `public/` (HTML, `style.css` 75 KB minificado, `products.json`,
  `sitemap.xml` 48 URLs, `robots.txt`, img webp, media, `en/` espejo 24
  páginas, `admin.html` copiado del panel).
- **products.json**: productos (name/name_en, category, url, thumb, price
  "Consultar") + research/research_en (FAQs/curiosos). **Sin costos** —
  regla de seguridad: los costos viven solo en la hoja Productos (01).

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE` (design system, i18n — hoy incrustados en el
  generador); endpoints públicos de `03_COMERCIAL` (`lead`), `09_MARKETING`
  (`track`, `reviews`); catálogo Drive (incl. media desde P2); `assets/`.
- **ALIMENTA A**: `03_COMERCIAL` (leads), `09_MARKETING` (visitas).
- **COMPARTE CON**: 09 (reseñas y tracker); `products.json` +
  `window.__adisProducts` consumidos por buscador y chatbot del propio sitio.

## REGLAS DE NEGOCIO

1. **Nunca exponer costos** en products.json ni en el HTML público.
2. Toda ruta relativa con `p()` y todo texto visible con `t()`/`i18n()` (i18n).
3. El chatbot y el buscador comparten `window.__adisProducts` (desde
   products.json) — no duplicar la carga.
4. El tracker no rastrea `admin.html`.
5. Cada página nueva debe agregarse al sitemap y (si aplica) a hreflang.
6. `public/` se regenera siempre; **no editar a mano** (se pierde en el
   próximo build).
7. Los nombres de imagen con espacios requieren URL-encoding en srcset.

## API / BACKEND (solo consume 3 endpoints públicos)

| Uso | Endpoint | Dónde |
|---|---|---|
| Formulario de contacto | POST `lead` | `generate_contacto()` → `LEADS_URL` |
| Tracker | POST `track` | snippet en `generate_footer()` L4424–4532 |
| Reseñas | GET `reviews` | `generate_testimonios()` L8091 |

- Constantes: `LEADS_URL`, `REVIEWS_URL` (`generar_web.py` L33–34 — misma URL,
  el backend; **pendiente M1** a `00_CORE/config/`).

## FRONTEND (estructura del generador)

- **Infra**: `TRANSLATIONS` L59, `t/i18n/i18n_fmt` L564–601, `set_lang/p/
  out_dir/hreflang_tags` L602–660, `svg_icon` L556, `ga_script` L753,
  `fb_pixel` L767, `translate_script/toggle` L792–848.
- **Datos**: `scan_catalog` L1326, `sync_images` L1251, `sync_media` L7726,
  `research_data` L976, carga de JSON L656–660, L940–950.
- **SEO**: schemas L3726–3878, `generate_sitemap` L3879, `generate_robots` L3920.
- **Componentes**: `generate_style` L3573 (CSS completo L1396–3555),
  `generate_header` L4311 (mega-menú, topbar, toggle idioma, buscador),
  `generate_footer` L4424 (contiene tracker L4424–4532, chatbot con
  `CHATBOT_I18N` L4534 y `PRODUCT_KB` L4871, buscador `__initAdisSearch` L6438).
- **Páginas**: `generate_index` L6514, `generate_contacto` L6935,
  `generate_nosotros` L7137, `generate_privacy` L7276,
  `generate_category_page` L7356, `generate_sabias_que` L8360,
  `generate_proyectos` L8543, helpers (calculadora L3953, modal cotizar L4007,
  testimonios L8091, lead banner L8059).
- **Build**: `main()` L8807 — escanea catálogo, sincroniza img/media, genera
  style/sitemap/robots, copia admin, genera ES+EN, escribe products.json.

## PERMISOS

n/a (estático). Los endpoints que consume son públicos por diseño.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `generar_web.py` | TODO el módulo hoy (pendiente M3: dividir en `generador/` + `componentes/`) |
| `investigacion_data.json`, `_en.json`, `traducciones_productos.json` (raíz) | datos i18n/investigación (pendiente M1 → `00_CORE/i18n/`) |
| `public/` | salida generada (despliegue GitHub Pages) |
| `assets/` | logo, QR |
| `.github/workflows/deploy.yml` | publica `public/` en Pages al push a main |
| `Material de Facebock/` (en CATALOG_DIR, Drive, desde P2) | fuente de media (ver 00_CORE/CONTEXTO_GLOBAL.md) |

## INTEGRACIONES

- Google Drive (catálogo, solo lectura) · Apps Script (3 endpoints públicos) ·
  GitHub Pages (deploy) · Google Analytics + Facebook Pixel (scripts L753–790) ·
  WhatsApp (CTAs) · jsDelivr/CDN (jsPDF solo en admin).

## QUÉ NO MODIFICAR

- `sync_media()` depende de la ruta en `plataforma.json` (`material_media_dir`, absoluta
  desde P2 hacia CATALOG_DIR en Drive) — no renombrar la carpeta sin actualizarla.
- El contrato de products.json (lo consumen buscador y chatbot en producción).
- Los 3 endpoints públicos que consume (son de otros módulos).
- El dominio canonical (punycode `xn--adis-diseo-19a.com`).

## PRUEBAS

- No hay suite automatizada del sitio completo (deuda). Verificación manual
  estándar tras cambios: regenerar, abrir index + 1 categoría + contacto en
  320/390/768px, probar buscador/chatbot/toggle ES-EN, validar `node --check`
  del JS extraído, y diff de `public/` contra el build anterior.
- Playwright móvil/desktop se usó en sesiones 2026-07-25 (referencia en
  CONTEXTO_GLOBAL §15).

## EJEMPLOS DE INTERACCIÓN

1. **Lead (10→03)**: formulario → POST `lead` (honeypot) → fila en Leads →
   aparece en el tab Leads del panel.
2. **Reseñas (09→10)**: testimonios cargan `?action=reviews` al hacer scroll;
   las 4 tarjetas estáticas quedan como fallback/SEO.
3. **Tracker (10→09)**: cada vista de página envía `track` con secciones vistas
   → alimenta el tab Flujo del panel.
