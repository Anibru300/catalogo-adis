# PLAN DIFERIDO — Rediseño de API con envelope `{ok, data, error}`

**Estado: DIFERIDO (decisión 2026-09-13).** No se implementa en esta fase.

## Por qué se difiere

El sitio (`public/`) se despliega automáticamente a producción con cada push a
`main` (GitHub Pages, ver `.github/workflows/deploy.yml`). El backend (Apps
Script) solo se actualiza con pegado manual en la consola (ver
`00_CORE/backend/GUIA_DESPLIEGUE.md`). Si el envelope se subiera al repo antes
de que el backend lo soporte, **el panel admin y el chatbot/tracker público
quedarían rotos en producción** entre el push y el redeploy manual.

Prerequisito duro: poder desplegar backend y frontend en la misma ventana.

## Objetivo del rediseño

1. Normalizar TODAS las respuestas del backend a `{ok, data, error}`:
   - éxito: `{ok: true, data: <payload>}`
   - error controlado: `{ok: false, error: {codigo, mensaje}}`
2. Con el contrato explícito, los handlers **inline** de `doGetInterno`/`doPostInterno`
   (`00_CORE/backend/core.gs`) se podrán extraer a módulos por dominio
   (`01_EXISTENCIAS/backend/*.gs`, etc.) sin ambigüedad de interfaz.

## Impacto estimado

| Capa | Archivos | Cambio |
|---|---|---|
| Backend | `core.gs` (dispatchers + ~40 handlers inline), `analitica.gs` | Envolver respuestas; extraer handlers a archivos por módulo |
| Admin JS | `00_CORE/shared_js/admin_core.js` (`apiGet/apiPost`), 15 JS de módulos | Leer `ok/data/error` en vez del contrato plano |
| Sitio público | `componentes.py` (tracker tipo `track`, chatbot, leads, reseñas) | Mismo parseo nuevo |
| Tests | `scripts/auditoria/test_fase*.py` (19 pruebas) | Actualizar asserts al envelope |

## Secuencia segura propuesta (cuando se apruebe)

1. **Paso 0 — Coordinación**: elegir ventana de despliegue; tener a mano el
   acceso a Apps Script y a GitHub.
2. Backend dual (opcional pero recomendado): aceptar `envelope: 1` en el
   request y devolver el formato nuevo solo cuando se pida. El frontend viejo
   sigue funcionando mientras tanto.
3. Commit del backend dual → desplegar manualmente → verificar
   `test_fase0_regresion.py` (19/19) contra el backend ya desplegado.
4. Commit del frontend con el nuevo parseo (activa el flag `envelope: 1`) →
   push → Pages despliega. Verificar 19/19 de nuevo.
5. Quitar el formato plano del backend (segundo deploy manual) y el flag.

## Riesgos

- Doble formato temporal = doble superficie de bugs (mitigar con pruebas de
  ambos formatos en `test_fase0_api.py`).
- Endpoints públicos (`lead`, `track`, `reviews`) los consume el sitio estático:
  cualquier desfase rompe captación de leads y analítica.
- CacheService de tokens: el envelope no afecta auth, pero validar `login/logout/me`.

## Qué SÍ quedó hecho en M5 (base de este plan)

- Backend modular en 2 archivos con concatenación (`50_BUILD/concat_backend.py`).
- Mapa de handlers inline por módulo documentado en `00_CORE/backend/README.md`.
- El mecanismo de credenciales (P4) es independiente del envelope.
