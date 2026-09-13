# 00_CORE/auth — Autenticacion y autorizacion

**Estado: documentado (implementacion en los monolitos).**

- Backend: `apps-script.gs` login/logout/me (L780-797); token UUID 8h CacheService;
  limite 5 intentos/10 min.
- Frontend: sessionStorage `adis_admin_token`/`adis_admin_user`; manejarSesion()
  re-login automatico (`admin/index.html` L979).
- Rol unico (admin plano). Endpoints publicos: login, logout, lead, track, reviews.

**Pendiente del dueno**: rotar ADMIN_CLAVE (expuesta en repo). Ver CONTEXTO_GLOBAL.md §4.
