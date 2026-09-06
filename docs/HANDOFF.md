# Handoff — ADIS Catálogo Web

> Documento para la siguiente sesión. Última actualización: 2026-09-06 (FASE 0 completada).

## Novedades 2026-09-06 — FASE 0: cimientos del sistema administrativo

- Se aprobó el Plan Maestro (8 fases, ver `docs/AUDITORIA_SISTEMA_2026-09-06.md` + `docs/ADMIN_ARCHITECTURE.md` nuevo).
- **Backend reescrito** (`admin/apps-script.gs`): LockService en operaciones críticas (folios/stock/ventas — imposible duplicar folios o perder stock por concurrencia), errores JSON consistentes `{ok:false,error:{code,message}}` vía `conErrores`, Config con caché por ejecución, stock con snapshot (adiós N+1), movimientos trazables (id MOV-AAAA-NNNNN, usuario, existencia anterior/posterior, documento origen — la existencia SOLO cambia por `aplicarMovimiento`), stock negativo bloqueado (STOCK_INSUFICIENTE), folios VEN-0000/MOV-00000 nuevos, borrado por ID estable (filaPorId), venta con compensación best-effort, track con rate-limit+dedup+archivo (Visitas_Archivo, ya no se borra historial), login con límite de intentos + logout que revoca token, usuario admin fuera del Log, HOJAS_BORRABLES sin Ventas/Movimientos.
- **Contrato de éxito**: sigue plano (compatibilidad); errores ya son `{code,message}`. Migración a envelope en Fase 7.
- **Frontend**: 10 parches mínimos en `admin/index.html` (errMsg para ambos formatos de error, sesión expirada → re-login automático, logout revoca token, reseñas/gastos envían ID estable + fila como respaldo). Sin cambios visuales. Copiado a `public/admin.html`.
- **Pruebas**: `scripts/auditoria/test_fase0_api.py` (suite API+concurrencia, auto-detecta backend viejo/nuevo — correr tras redeploy) y `test_fase0_regresion.py` (Playwright 13/13 PASS, 0 errores JS contra backend viejo). Sintaxis GS+JS validada con node.
- ⚠️ **PENDIENTE DEL DUEÑO**: (1) rotar ADMIN_CLAVE en Apps Script, (2) redeploy con **✏️ Nueva versión** (la URL no debe cambiar), (3) avisar para correr la suite completa en vivo. Luego empezar Fase 1 (inventario transaccional: historial por producto, indicadores, márgenes).

## Novedades 2026-09-05

### Cotizador — sección 03 solo inversión total (según el Word)
- El PDF de la cotización **ya no muestra el desglose de partidas**: la sección 03 ahora es "INVERSIÓN TOTAL DEL PROYECTO" con USD/MXN, fiel a `Formato de Cotizacion nuevo.docx`.
- Las partidas siguen en el editor (uso interno para calcular el total; van etiquetadas como tal). WhatsApp ya no menciona el desglose.
- Cambio en `admin/index.html` (`buildProposalHTML`). Verificado con Playwright: 2 placas × $850 + IVA = $1,972.00 MXN, sin tabla de partidas.

### 🌊 Pestaña Flujo (panel admin) — requiere REDEPLOY del script
- Nueva pestaña **Flujo** en `admin/index.html`: KPIs (visitas, hoy, 7 días, apartados vistos, página más vista), gráfica de barras de visitas por día (30 días), "¿De dónde nos visitan?" (Google/Facebook/Instagram/WhatsApp/directo…), "¿Quién nos visita?" (dispositivo/navegador/idioma), páginas y apartados más vistos, tabla de últimas visitas. Gráficas en CSS puro (sin librerías).
- **Tracker**: snippet en `generate_footer()` (dentro de `chatbot_js`) que envía `tipo:'track'` a Apps Script (sendBeacon/fetch, dedup por sesión) con página, apartados vistos (IntersectionObserver), referrer, idioma, UA y ancho. No trackea `admin.html`.
- **Backend (`admin/apps-script.gs`)**: sheet `Visitas` (auto-creada, tope 5000 filas), `doPost tipo='track'` (público, con clasificadores `origenDe_`/`dispositivoDe_`/`navegadorDe_`) y `doGet action='visitas'` (con token; devuelve filas como objetos, se agregan en el cliente).
- ⚠️ **PENDIENTE PUBLICAR**: (1) usuario redeploya Apps Script con **nueva versión** (rutina: Implementar → Administrar implementaciones → ✏️ → Nueva versión) para activar `track`/`visitas`; (2) `git add -A && git commit && git push origin main` para publicar el sitio con el tracker. Prueba: entrar a la web y ver la pestaña Flujo.
- Test de verificación: `scripts/auditoria/test_flujo_cotizador.py` (Playwright, backend simulado).

## Novedades de esta sesión

### ✅ Fase 0 y 1 del Plan Maestro — COMPLETAS
- Base maestra importada en Google Sheets con integridad 100%: **261 productos** (251 web + 10 solo-Excel), 0 duplicados, **20 existencias** en 3 almacenes (Nogales 14, Decosonora 3, Rio Rico 3), costos 261/261. Esquema: ID/Código/Producto/Descripción/Categoría/Subcategoría/Proveedor/Costo/Precio/Unidad/Foto/Estado/Fecha. Pestañas auto-creadas: Productos, Almacenes, Stock, Movimientos, Ventas, Gastos, Config, **Log** (bitácora).
- Panel admin → pestaña **Inventario**: CRUD completo con validación, buscador/filtros, foto lateral al seleccionar, dashboard (total/activos/sin foto/revisión), soft-delete (Activo/Inactivo).
- Backend `admin/apps-script.gs`: `importDataset`, CRUD productos, movimientos, ventas con descuento de stock, gastos, estadoResultados (fix fechas Date), config, getLog.
- **Pendiente usuario**: capturar precios de venta (los 261 tienen costo pero precio vacío) y revisar los 10 productos marcados REVISAR (HJPVC2/3/12/13/14/15/16, KL8276, KL8055, KL8267, ISA).

### 🆕 Cotizador profesional (nueva pestaña 📝 Cotizador en admin/index.html)
- Replica el formato de `Formato de Cotizacion nuevo.docx` (secciones 01–09: datos, alcance con foto/render + casillas de tipo de proyecto, desglose con IVA, fotos de productos, especificaciones, condiciones, garantía 7 meses, logística premium, firmas, footer).
- Partidas con **lista desplegable del catálogo** (biz.productos, OJO: el API devuelve llaves en **minúsculas**: id/codigo/nombre/categoria/precio/unidad — NO las cabeceras del sheet). Autollenado código/desc/unidad/precio.
- Fotos (proyecto + hasta 6 productos) comprimidas a canvas JPEG 0.82 ≤1280px → dataURL; van incrustadas en el PDF pero **NO** se persisten en Sheets (celda 50k chars) — van al borrador localStorage (`adis_prop_draft`).
- **Folio consecutivo ADIS-AAAA-NNN** vía `cfg('folio_cotizacion')` en el backend; el handler `quote` extendido guarda columnas extra (folio/proyecto/ubicacion/moneda/subtotal/iva/estado/datosJSON) y devuelve `{ok, folio}`. Botón 📂 Cargar reabre cotizaciones guardadas en el editor (parsea `datos`).
- PDF multipágina validado con Playwright (page.pdf): fiel al DOCX, paginación por secciones.
- **✅ REDEPLOY HECHO el 2026-09-04 noche** (el usuario creó implementación nueva → **cambió la URL**). URL vigente: `https://script.google.com/macros/s/AKfycbyb5ij67ky7BYlmi76Zg_CPDy44i0HwB-z3bwGp_umHb0rL_0Jl3ClvorquDVN0SD09/exec` — ya replicada en generar_web.py (×2), admin/index.html, scripts/auditoria/importar_maestro.py y todo public/. Prueba en vivo OK: login + guardar quote devolvió folio `ADIS-2026-001`; fila de prueba borrada (cotizaciones en 0). Contador folio quedó en 2 (próxima real: 002; se puede resetear a 1 editando la pestaña Config en Sheets). NOTA: apps-script.gs local tiene además un micro-cambio sin desplegar (handler config acepta `folio_cotizacion`) — se despliega junto con la próxima actualización (Fase 2), no urge.
- Rutina para el usuario al actualizar el script: **Nueva versión** (✏️ sobre la implementación existente) para que la URL NO cambie; si crea "Nueva implementación", la URL cambia (pasó hoy) y hay que avisarla para replicarla en los 4 archivos.

## Estado general

- **Proyecto**: Catálogo web estático para ADIS Diseño & Remodelación (Nogales, Sonora · Arizona).
- **Repo**: `https://github.com/Anibru300/catalogo-adis.git`
- **Sitio en vivo**: `https://anibru300.github.io/catalogo-adis/` → dominio propio `https://xn--adis-diseo-19a.com/`
- **⚠️ MIGRACIÓN 2026-09-04**: el proyecto salió de Google Drive (Drive corrompía `.git` con `desktop.ini` y destruyó objetos del repo). Nueva ubicación: **`C:\Users\Carlos\Desktop\Pagina`**. `BASE_DIR` en `generar_web.py` ahora se deriva de `Path(__file__).resolve().parent`. `CATALOG_DIR` sigue en Drive (solo lectura). La carpeta vieja en Drive queda intacta como respaldo — NO trabajar ahí.
- **Generador principal**: `generar_web.py` (Python 3.13 en `C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python`).
- **Salida**: carpeta `public/` (GitHub Pages sirve desde `public/`).
- **Último commit local**: `741fe36` — "fix: corrige JS roto en modal de cotizacion WhatsApp (escapes \n)".
- **Push pendiente**: No (al día con `main`).
- **Kimi CLI**: actualizado a `v1.49.0` (el ejecutable en uso se reemplazará al reiniciar la terminal).
- **Modelo por defecto de Kimi**: cambiado a `kimi-code/k3` (1,048,576 tokens de contexto) en `C:\Users\Carlos\.kimi\config.toml`.
- **Dominio canonical**: `SITE_URL` corregido a punycode `https://xn--adis-diseo-19a.com/` (antes tenía ñ literal, inválida en URLs).

## Versión /en/ con hreflang (2026-07-24) ✅

El sitio se genera **dos veces** desde `main()` en `generar_web.py`:
- `set_lang('es')` → `public/` (raíz)
- `set_lang('en')` → `public/en/` (24 páginas espejo en inglés)

Infraestructura clave:
- `CUR_LANG` / `CUR_PREFIX` globales; `set_lang()`, `p(path)` (prefijo `../`), `out_dir()`, `page_url()`, `hreflang_tags()`, `html_lang()`, `og_locale()`.
- `t(key)` usa `CUR_LANG` por defecto; `i18n()`/`i18n_fmt()` emiten el texto default según idioma (mantienen `data-es`/`data-en` para el swap JS) y `_prefix_links()` arregla links `.html` dentro de traducciones.
- Toggle ES/EN ahora es un `<a>` que navega a la página contraparte real (`en/xxx.html` ↔ `../xxx.html`); el swap JS queda como respaldo vía `adisSetLang()`.
- Cada página tiene canonical por idioma + 3 `link rel="alternate" hreflang` (es, en, x-default) + `og:locale` es_MX/en_US con alternate.
- `sitemap.xml`: 48 URLs con `xhtml:link` alternates bidireccionales.
- Archivos de traducción nuevos en raíz del proyecto:
  - `traducciones_productos.json` — categories/subcategories/names (237 productos) ES→EN.
  - `investigacion_data_en.json` — FAQs/curiosos/comparativas/ventas de las 9 categorías en inglés.
- `products.json` ahora incluye `name_en`, `category_en`, `subcategory_en` y bloque `research_en`; el chatbot/buscador los usan según idioma (`ADIS_PREFIX` y `ADIS_DEFAULT_LANG` se inyectan en build).
- `CAT_SEO` es bilingüe; `RESEARCH_CAT_EN` traduce nombres de categorías de investigación.

Al modificar plantillas: mantener `p()` en toda ruta relativa (href/src/fetch/background-image) y `t()`/`i18n()` en todo texto visible.

## Qué se arregló en la sesión anterior

### 1. Buscador global ✅
- Script JS propio (`__initAdisSearch`) que consume `products.json`.
- Soporte para tecla `/`, `Esc`, cierre al clic fuera, debounce 150 ms.
- Dropdown en header, dropdown móvil y spotlight overlay.

### 2. Chatbot bilingüe ES/EN ✅
- Se agregó el diccionario `CHATBOT_I18N` dentro del JS del chatbot (`generar_web.py`).
- Se tradujeron:
  - UI del chatbot (título, placeholder, botones, quick replies).
  - Mensajes de bienvenida y despedida.
  - Respuestas de horarios, contacto, ubicación, precios, envíos, instalación, pagos, garantía, mantenimiento, proyectos.
  - Base de conocimiento de productos (`PRODUCT_KB`) completamente bilingüe.
  - Cotización guiada paso a paso.
  - Recomendador inteligente.
  - Respuestas de "Sabías que" / FAQs.
- Se corrigieron errores de sintaxis graves dejados por intentos previos (funciones duplicadas).
- Se validó la sintaxis JS con Node: OK.

### 3. Nombres de categorías del menú ✅
- Se agregaron claves `menu_xxx` en `TRANSLATIONS`.
- `generate_header()` usa `i18n()` para los textos visibles del mega-menú y el dropdown "¿Sabías que?".
- Los atributos `alt` de las imágenes del mega-menú usan `t()` (texto plano).

### 4. Limpieza
- Se eliminaron scripts residuales: `build_chatbot_new.py`, `chatbot_js_original.js`, `traducir_chatbot.py`, `scripts/finalizar_chatbot_i18n.py`.
- Backup del intento previo movido a `backups/generar_web_pre_chatbot_i18n_20260724.bak`.

## Novedades 2026-09-04 — Leads, reseñas y panel admin

1. **Captación de leads**: el formulario de contacto ahora envía cada lead a Google Sheets (Apps Script) además de abrir WhatsApp. Config: `LEADS_URL` arriba en `generar_web.py`. Honeypot anti-spam (`cfEmpresa`). Si `LEADS_URL` está vacío, todo funciona como antes.
2. **Reseñas en vivo**: `generate_testimonios()` mantiene las 4 tarjetas estáticas (fallback/SEO) y, si `REVIEWS_URL` está configurado, carga reseñas de la pestaña Reseñas al hacer scroll (IntersectionObserver). Endpoint público: `?action=reviews`.
3. **Panel de administración** (`admin/index.html` → se copia a `public/admin.html` en `main()`): login con **usuario/contraseña propios** (validado en Apps Script, token de sesión 8h en CacheService; sin Google). Pestañas: Leads, Cotizaciones (cotizador con productos reales de products.json, imprimir/PDF, WhatsApp), Reseñas (publicar/eliminar), Estadísticas (iframe Looker Studio). Oculto: noindex, `Disallow: /admin.html` en robots.txt, sin enlaces en el sitio.
4. **Backend**: `admin/apps-script.gs` (pegar en Apps Script de la hoja de Google). Credenciales `ADMIN_USUARIO`/`ADMIN_CLAVE` dentro del script. Pestañas Leads/Cotizaciones/Reseñas se crean solas.
5. **Guía de configuración**: `admin/GUIA_CONFIGURACION.md` (pasos Google Sheet → deploy → conectar URL). Falta que el usuario la siga y pase la URL `/exec`.

## Mini-ERP (2026-09-04)

El panel (`admin/index.html` + `admin/apps-script.gs`) ahora incluye gestión del negocio:
- **Productos** (costo/precio/unidad/stock mínimo/moneda), **Almacenes**, **Stock** por almacén, **Movimientos** (entrada/salida/ajuste).
- **Ventas**: registran salidas de stock y calculan utilidad (costo vs precio) en moneda base.
- **Gastos** por categoría. **Estado de resultados** mensual (`?action=estado_resultados&mes=YYYY-MM`): ingresos, costos, utilidad bruta, gastos por categoría, utilidad neta, márgenes; imprimible.
- **Moneda dual**: Config (`moneda_base`, `tipo_cambio` = MXN por 1 USD); conversión server-side en `aBase()`.
- Endpoint `import_productos` para migrar el Excel de precios/costos del usuario (PENDIENTE: usuario pasa el archivo + la URL /exec tras crear la hoja y el deploy).

## Qué falta por hacer (prioridad sugerida)

1. **Push del commit actual**
   - El commit `8425e96` está solo en local. Ejecutar:
     ```bash
     git push origin main
     ```

2. **Reseñas reales de Google**
   - Actualmente la sección de testimonios es manual.
   - Integrar widget de Google Reviews o Google Places API.

3. **Captación de leads**
   - El formulario pide correo pero no almacena nada.
   - Opciones: guardar en Google Sheets, Airtable, Supabase, o al menos enviar por email/WhatsApp con los datos.

4. **Página de garantías**
   - No existe `garantia.html`.
   - Se puede generar desde `generar_web.py` con la información de garantías que ya está en `PRODUCT_KB`.

5. **Hreflang real**
   - El sitio es bilingüe por JS toggle, no por URLs `/en/`.
   - Para SEO internacional debería existir `/en/` o al menos `hreflang` dinámico.

6. **Posters de video**
   - Los videos en home no tienen imagen de portada (`poster`).

7. **Fotografía profesional**
   - Falta sesión de showroom / equipo / instalación.

8. **Precios por modelo**
   - Pendiente a que el usuario proporcione precios reales.
   - Actualmente todos los productos muestran "Consultar".

## Problemas técnicos recurrentes

### `desktop.ini` de Windows dentro de `.git/refs/`
- Windows crea `desktop.ini` en carpetas. Si entra en `.git/refs/`, git falla con:
  ```
  fatal: bad object refs/desktop.ini
  ```
- **Solución rápida**:
  ```bash
  find .git/refs -name "desktop.ini" -type f -delete
  ```
- Considerar agregar `.git/refs/**/desktop.ini` o `desktop.ini` global al `.gitignore` ya existente.

### Entorno virtual anterior
- El entorno `C:\temp\kimi_venv\` ya no existe.
- Usar Python 3.13 directamente:
  ```bash
  "C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python" generar_web.py
  ```

## Comandos útiles

```bash
# Generar todo el sitio
"C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python" generar_web.py

# Validar sintaxis JS del chatbot/buscador
node --check "C:\Users\Carlos\AppData\Local\Temp\adis_chatbot_check.js"

# Limpiar desktop.ini de git
find .git/refs -name "desktop.ini" -type f -delete

# Git
git status
git add -A
git commit -m "..."
git push origin main
```

## Notas para la siguiente sesión

- **2026-07-25 — 9 mejoras visuales:** (1) slider Antes/Después arrastrable en Proyectos (`.ba-slider`, pointer events, reemplaza carruseles ba); (2) calculadora de m² `calculator_html(categories, preselect)` en index + categorías, CTA WhatsApp prellenado (claves `calc_*`); (3) video de fondo en hero (`.hero-video`, z-index: video 0, overlay ::before 1, content 2); (4) sección Transformaciones reales `transformations_html()` (fotos `media/proyecto-*.jpeg`); (5) topbar dorada en el header (`topbar_text`) — **ojos con los paddings-top de heroes/breadcrumbs, ajustados +2rem**; (6) shine en `.btn-primary::after` (`btnShine`); (7) badges: `featured_star_badge` = 'Más vendido', `new-badge` verde en 9-cladding; (8) iconos benefit con pop escalonado vía `.reveal.active`; (9) trust-banner con iconos SVG. `picture_tag()` ahora acepta `cls=''`. Auditoría: 0 problemas en 192 pruebas. Respaldo: `backups/generar_web_pre_visual9_*.py`. PENDIENTE: agregar Misión a Nosotros (usuario eligiendo entre opciones A/B/C propuestas).

- **2026-07-25 — Optimización integral UX móvil (Fases 1-4):** corrección de bugs (llaves del `@media 480px` que aplicaban reglas móviles en desktop; grids `minmax()` desbordando a 320px → patrón `minmax(min(Xpx,100%),1fr)`; flotantes WA/chatbot a `bottom:108px` sobre la bottom-nav; lightbox renderizaba `{svg_icon...}` literal por string sin `f`), interacción táctil (tap targets ≥44px, swipe en lightbox con flechas/teclado, swipe+sin autoplay móvil en carrusel, inputs a 16px anti-zoom iOS, `@media (hover:none)` anti sticky-hover, menú móvil con 9 categorías + toggle idioma), rendimiento (`picture_tag()` en cat-cards/featured/mega-menu — **srcset requiere URL-encoding de espacios** (`webp_srcset` ya lo hace), logo webp 8.6KB vía `ensure_logo_webp()`, webp full max 1600w q82 / 600w q78, canvas de partículas pausa con `visibilitychange` y respeta `prefers-reduced-motion`). Verificación: Playwright 320/390/768px sin overflow ni errores JS en 12 páginas. Respaldo: `backups/generar_web_pre_mobileux_*.py`.

- **2026-07-25 — Botón de idioma movido al header (mobile-first):** el toggle ES/EN ya no es flotante abajo a la derecha; ahora es una píldora dorada `🌐 EN/ES` dentro del header (`.header-actions`, junto a la hamburguesa), generada por `translate_toggle(page_file)` e insertada por `generate_header(current_page, page_file)`. `translate_script()` ya solo inyecta el JS + prefetch. Se corrigieron dos bugs móviles preexistentes: `.desktop-nav` nunca se ocultaba en móvil por especificidad (`nav.desktop-nav` > `.desktop-nav`) y el `::before` de `.featured-product-section` (`right: -20%`) expandía el viewport móvil a 469px (ahora `right: 0`).

- Antes de tocar `generar_web.py`, revisar que no haya `desktop.ini` en `.git/refs/`.
- Si se va a seguir traduciendo, el patrón es:
  1. Agregar clave en `TRANSLATIONS` (Python) o `CHATBOT_I18N` (JS dentro de `generar_web.py`).
  2. Usar `i18n('clave')` / `t('clave')` en Python o `ct('clave')` en JS.
- El buscador y el chatbot comparten `window.__adisProducts` desde `products.json`.
- Si se agrega una nueva página, no olvidar agregarla al sitemap en `generar_web.py`.

## Decisiones pendientes del usuario

- ¿Hacemos push de los cambios actuales?
- ¿Continuamos con reseñas de Google, captación de leads, página de garantías, o hreflang?
- ¿Nos proporciona precios reales por modelo?
