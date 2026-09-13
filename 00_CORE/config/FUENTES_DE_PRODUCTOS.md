# Fuentes de datos de productos — RESUELTO (P1, 2026-09-13)

## Decisión vigente

**La hoja `Productos` (Sheets, ERP) es la fuente única de verdad.** El sitio web
es una *vista* de esa hoja: las imágenes viven en el catálogo de Drive y cada
fila de la hoja referencia su foto con la ruta `foto` (== `thumb` en products.json).

## Mecanismo (implementado en P1)

1. **`60_DATA/exportar_productos.py`** — exporta la hoja completa (con costos,
   uso interno) a `60_DATA/dataset_maestro.json`, versionado en el repo.
   Dirección oficial: **hoja → repo** (el flujo histórico inverso,
   `importar_maestro.py`, queda obsoleto; se conserva solo como referencia).
2. **`60_DATA/verificar_fuentes.py`** — puerta de drift: cruza `foto`==`thumb`
   entre la hoja exportada y `public/products.json` + existencia de archivos en
   `public/img`. Exit 1 si hay drift duro (producto web sin hoja, foto perdida).
   Correr después de cada build y antes de pushear.
3. El build del sitio sigue leyendo el catálogo de Drive (`scan_catalog`) —
   opción deliberada para preservar byte-identidad; migrar el build a consumir
   la hoja directamente (Opción A) queda ligada al rediseño de API (ver
   `99_DOCUMENTACION/PLAN_ENVELOPE_API.md`).

## Estado real (2026-09-13)

| Métrica | Valor |
|---|---|
| Productos en hoja (ERP) | 263 |
| Productos publicados en web | 251 |
| Cruce foto==thumb | 251/251 OK |
| Solo-Excel (sin foto / REVISAR) | 12 — conocidos, no son drift |

## Reglas de seguridad (sin cambio)

- `products.json` público **nunca** lleva costos (regla intacta: el build no
  toca la hoja; el export con costos vive solo en el repo privado, 60_DATA).
- Claves de la API `productos` en MINÚSCULAS (id/codigo/nombre/...).

## Diferencias históricas (resueltas o aceptadas)

- ~~Dos capturas por producto (Drive + Sheets)~~ → hoy la captura es una sola
  (hoja); Drive solo aporta imágenes/fichas. El drift gate avisa si divergen.
- 10 productos "solo-Excel" → hoy 12; se revisan en el ERP, no bloquean.
