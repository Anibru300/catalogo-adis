# Handoff — ADIS Catálogo Web

> Documento para la siguiente sesión. Última actualización: 2026-07-24.

## Estado general

- **Proyecto**: Catálogo web estático para ADIS Diseño & Remodelación (Nogales, Sonora · Arizona).
- **Repo**: `https://github.com/Anibru300/catalogo-adis.git`
- **Sitio en vivo**: `https://anibru300.github.io/catalogo-adis/`
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
