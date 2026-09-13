# 00_CORE/shared — Codigo compartido (JS del cliente / helpers Python)

**Estado: pendiente (Fase M4/M3).** Hoy todo vive dentro de los monolitos:

- JS compartido del panel: apiGet/apiPost, errMsg, $, esc, fmtMoney, notice, confirma
  (`admin/index.html` L962-1050).
- Helpers del generador: minify_css/html, picture_tag, webp_srcset, schemas SEO
  (`generar_web.py`).

**Plan**: extraer a modulos importados por el build (build_admin.py / build_sitio.py).

---

## ✅ Estado M1 (2026-09-13)

`web_utils.py` creado: helpers puros extraidos de `generar_web.py` (ICONS_SVG, svg_icon,
minify_css, minify_html, json_ld, whatsapp_url, build_whatsapp_message, md_to_html, clean_name, slugify).
El generador los importa con `from web_utils import *`.
