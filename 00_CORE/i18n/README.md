# 00_CORE/i18n — Internacionalizacion del sitio publico

**Estado: parcial (datos en raiz, pendiente M1).** Hoy:

- Infraestructura dentro de `generar_web.py`: TRANSLATIONS (L59), t(), i18n(), p(), set_lang().
- Datos: `traducciones_productos.json`, `investigacion_data.json`, `investigacion_data_en.json`
  (raiz del repo; los lee el generador en runtime — NO mover hasta M1).

**Nota**: el panel admin es solo ES; no hay i18n en admin.

---

## ✅ Estado M1 (2026-09-13)

- `translations.py`: dict `TRANSLATIONS` extraido de `generar_web.py` (importado por el generador).
- Los 3 JSON (`traducciones_productos`, `investigacion_data`, `investigacion_data_en`) movidos
  aqui desde la raiz; `generar_web.py` actualizo sus rutas.
- Las funciones `t()/i18n()/p()/set_lang()` siguen en el generador (M3 -> `10_SITIO_PUBLICO/sitio/infra.py`).
