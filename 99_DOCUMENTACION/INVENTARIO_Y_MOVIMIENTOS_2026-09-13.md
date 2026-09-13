# 📦 Inventario y registro de movimientos — Limpieza de repo (2026-09-13)

> Autorizado por el dueño con la condición de no perder información útil.
> Todo lo movido queda registrado aquí. El repo Git conserva el historial
> completo de estos archivos en commits anteriores (recuperables con `git`).

## Clasificación aplicada

| Categoría | Criterio |
|---|---|
| **Producción** | Necesario para que el sitio/ERP funcionen o se regeneren |
| **Desarrollo** | Herramientas de trabajo activas (tests, importadores) |
| **Documentación** | Docs vivos de la plataforma |
| **Archivo histórico** | Conservar por trazabilidad, fuera de Git |
| **Generado** | Salida de build (`public/`), se regenera, no se edita a mano |
| **Basura** | Regenerable o sin valor, eliminable |

## Movimientos realizados

### → Archivo externo `C:\Users\Carlos\Desktop\ARCHIVO_ADIS\` (fuera del repo, NO en Git)

| Origen | Destino | Clasificación | Motivo |
|---|---|---|---|
| `Formato de Cotizacion nuevo.docx` | `ARCHIVO_ADIS\documentos\` | Histórico (referencia de diseño del cotizador) | DOCX pesado; el formato ya está implementado en código |
| `Informe_Consultoria_UXUI_ADIS_vs_TeknoStep.docx` (12,7 MB) | `ARCHIVO_ADIS\documentos\` | Histórico | Pesado, no se lee en runtime |
| `informe_docx_extraido.txt` | `ARCHIVO_ADIS\documentos\` | Histórico | Extracción derivada del docx |
| `informe_webux.agent.final.md` | `ARCHIVO_ADIS\documentos\` | Histórico | Informe de consultoría ya aplicado |
| `investigacion\` (md 191 KB + docx 110 KB) | `ARCHIVO_ADIS\investigacion_fuentes\` | Histórico | Fuentes de `investigacion_data*.json` (ya procesadas); nada las lee en runtime |
| `scripts\legacy\` (7 generadores) | `ARCHIVO_ADIS\scripts_legacy\` | Histórico | Obsoletos, sustituidos por `generar_web.py` |
| 21 scripts one-off de `scripts\auditoria\` (fixes, comparadores, detectores, `parse_investigacion.py`, reporte json) | `ARCHIVO_ADIS\scripts_oneoff\` | Histórico | Ya ejecutados; no volverán a correr |

### → Dentro del repo, reubicado

| Origen | Destino | Clasificación | Motivo |
|---|---|---|---|
| `scripts\auditoria\importar_maestro.py`, `generar_dataset_maestro.py`, `dataset_maestro.json` | `60_DATA\` | Desarrollo | Herramienta de migración Excel→Sheets viva; trazabilidad del dataset maestro (261 productos) |

### → Sin tracking en Git, permanece físicamente en el repo (hasta M3)

| Elemento | Estado | Motivo |
|---|---|---|
| `Material de Facebock\` (39 MB, 33 archivos) | `git rm --cached` + `.gitignore` | **`sync_media()` en `generar_web.py` lo lee en cada build**. En M3 su ruta pasará a configuración y podrá salir del repo. NO renombrar ni mover sin actualizar `sync_media()`. |

### Eliminado (regenerable)

| Elemento | Motivo |
|---|---|
| `__pycache__\` (raíz y `scripts\auditoria\`) | Bytecode regenerable; ya estaba en `.gitignore` |

## Lo que SE QUEDÓ en el repo (y por qué)

| Elemento | Clasificación | Nota |
|---|---|---|
| `public/` (187 MB, con media e imágenes) | Generado versionado | **GitHub Pages despliega desde `public/`** — debe seguir en Git hasta que el deploy cambie |
| `investigacion_data.json`, `investigacion_data_en.json`, `traducciones_productos.json` (raíz) | Producción | Los lee `generar_web.py` en runtime. **Pendiente M1 → `00_CORE/i18n/`** |
| `docs/` | Documentación | Se depura en esta fase (ver `ANALISIS_DOCS_LEGACY.md`) |
| `backups/`, `screenshots/` | Desarrollo | Ya ignorados por Git (correcto) |
| `assets/` (logo, QR) | Producción | Fuentes de marca |
| 12 suites de pruebas en `scripts/auditoria/` | Desarrollo | Vivas; se reubicarán a sus módulos en M6 |

## Estado Git tras la limpieza

- `Material de Facebock/` eliminado del índice (staged).
- Resto de movimientos aparecen como deletions sin stagear.
- **Commit NO realizado** — pendiente aprobación del dueño.
- El historial Git conserva todo lo movido (recuperable).

## Reglas que nacen de esta limpieza

1. `Material de Facebock/` y `public/media/` son la misma información en fuente y destino: la fuente manda; `media/` se regenera con `sync_media()`.
2. Nada nuevo de más de ~1 MB entra al repo sin decisión explícita.
3. Los DOCX/imágenes fuente viven fuera del repo (`ARCHIVO_ADIS\`) o en `assets/` (marca).
