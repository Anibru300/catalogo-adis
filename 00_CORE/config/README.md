# 00_CORE/config — Configuración global de plataforma

**Estado: pendiente (Fase M1).** Hoy la configuración está dispersa:

- URL del backend Apps Script: hardcodeada x4 (`generar_web.py` L33-34, `admin/index.html` L950, `60_DATA/importar_maestro.py` L13, `scripts/auditoria/test_fase0_api.py` L21)
- `SITE_URL` (punycode): `generar_web.py` L602
- `WHATSAPP` / `LOOKER_STUDIO_URL`: `admin/index.html` CONFIG L947-951
- Credenciales admin: constantes `apps-script.gs` L42-43

**Plan M1**: `plataforma.json` como fuente unica (url_backend, site_url, whatsapp),
leido por generador, panel (en build) y scripts.

---

## ✅ Estado M1 (2026-09-13)

`plataforma.json` creado y **activo**. Consume:
- `generar_web.py`: `url_backend` (LEADS_URL/REVIEWS_URL), `site_url`, `catalog_dir`,
  `material_media_dir`; e inyecta `url_backend` + `whatsapp` en `public/admin.html` al copiar.
- `60_DATA/importar_maestro.py` y `scripts/auditoria/test_fase0_api.py`: leen `url_backend` (fallback documentado).

Duplicidad residual documentada: `admin/index.html` (fuente del panel) conserva la URL en su
`CONFIG` — se inyecta desde aqui en el build; desaparece como duplicidad efectiva en M4.
