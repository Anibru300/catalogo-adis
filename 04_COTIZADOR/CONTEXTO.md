# 📝 04_COTIZADOR — Cotizaciones

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§7 folios).
> **Deuda reconocida**: coexisten DOS cotizadores en el panel (simple y
> profesional). Este módulo documenta ambos tal cual existen hoy.
> Fuente: `admin/index.html`, `admin/apps-script.gs`,
> `scripts/auditoria/test_fase3_api.py` (quote), `test_cotizador_precio_final.py`,
> `test_flujo_cotizador.py`. Formato visual: `Formato de Cotizacion nuevo.docx`
> (archivado en `C:\Users\Carlos\Desktop\ARCHIVO_ADIS\documentos\`).

## IDENTIDAD

- **Objetivo**: crear cotizaciones profesionales con folio consecutivo
  (ADIS-AAAA-NNN), formato fiel al documento comercial de la empresa (secciones
  01–09), exportables a PDF y WhatsApp, y convertibles en proyecto al aprobarse.
- **Responsabilidad**: hoja Cotizaciones; tabs `proposal` (editor) y `quotes`
  (historial); el endpoint público no existe — todo con token.
- **Problema que resuelve**: cotizar con imagen profesional, numeración
  oficial y trazabilidad de estados (borrador → enviada → aprobada).

## ALCANCE

- **Hace**: editor con datos del cliente/obra, casillas de tipo de proyecto,
  partidas con autollenado del catálogo, **precio final único** (sin desglose
  en el PDF; las partidas son uso interno), foto del proyecto + hasta 6 fotos de
  producto (canvas JPEG 0.82 ≤1280px), IVA opcional, folio, guardar/cargar
  borradores, PDF multipágina real (html2canvas+jsPDF con cortes limpios),
  imprimir, WhatsApp (móvil: share con PDF / escritorio: descarga + chat),
  historial con estados y aprobación.
- **NO hace**: persistir fotos en Sheets (viven en localStorage del navegador
  que creó la cotización — deuda), facturar (06), gestionar el proyecto (05).
- **Pertenecen aquí**: hoja Cotizaciones, editor, historial, PDF.

## DATOS

- **Hojas**: `Cotizaciones` (ENC_COTIZ: fecha, cliente, telefono, ciudad, items,
  total, notas, folio, proyecto, ubicacion, moneda, subtotal, iva, estado,
  datos, id, usuario). Esquema: `apps-script.gs` L79.
- **Campos importantes**: `datos` = JSON string con el estado completo del
  cotizador (secciones 01–09); `estado` (borrador/enviada/aprobada…);
  `folio` ADIS-AAAA-NNN.
- **Consume**: Productos del ERP (para partidas/autollenado), Clientes/Leads (03),
  Config (`folio_cotizacion`).
- **Genera**: filas Cotizaciones; folios; al aprobar → proyecto (05).

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE`; `01_EXISTENCIAS` (productos/precios para partidas);
  `03_COMERCIAL` (cliente/lead — `matchLead` L1460 relaciona el lead con el
  cliente del directorio).
- **ALIMENTA A**: `05_PROYECTOS` (`crear_proyecto_desde_cotizacion` crea el
  proyecto al aprobar, sin recapturar datos).
- **COMPARTE CON**: 03 (cliente/lead), 08 (cotizaciones viejas pendientes
  aparecen en alertas).

## REGLAS DE NEGOCIO

1. Folio consecutivo bajo LockService; **re-guardar no consume folio nuevo** (se
   respeta el folio existente).
2. La sección 03 del documento es **"INVERSIÓN TOTAL DEL PROYECTO"** — el PDF no
   muestra desglose de partidas (decisión del dueño, 2026-09-05); las partidas
   son uso interno para calcular el total.
3. Las fotos **no viajan a Sheets** (límite 50k chars/celda): van a localStorage
   (`adis_prop_draft`). Cargar una cotización guardada en otro equipo no recupera fotos.
4. El handler `quote` es **retrocompatible**: acepta el payload simple (tab quotes)
   y el profesional (tab proposal). No romper el formato simple hasta unificar.
5. Cotizaciones ∈ HOJAS_BORRABLES (se pueden borrar filas desde el panel).

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `quotes` | GET | Historial completo |
| `quote` | POST | Guardar cotización (ambos formatos); devuelve `{ok, folio}` |
| `set_estado_quote` | POST | Cambiar estado (borrador/enviada/aprobada/vencida) |
| `crear_proyecto_desde_cotizacion` | POST | `{quote_id}` → crea proyecto ligado (05) |

- Handlers: `apps-script.gs` L812–835, L1399–1419, L1446–1473.
- Errores: `VALIDACION` ("necesita al menos un cliente o un producto"),
  `NO_ENCONTRADO`.

## FRONTEND (tabs `proposal` y `quotes`)

- **Editor profesional**: estado `prop` (global); `defaultProp` L1419,
  `initProposal` L1433, borrador localStorage `schedulePropDraft` L1441,
  `renderItemRows` L1561, `calcTotals` L1588, `buildProposalHTML` L1616
  (documento secciones 01–09), `renderProposal` L1695, `saveProposal` L1698,
  `syncFormToProp` L1723, `descargarPDF` L1744 + `buildProposalPDF` L1842
  (html2canvas + jsPDF, cortes keep-together), `printProposal` L1756,
  `sendProposalWhatsApp` L1886, `loadProposalFromQuote` L1921, `newProposal` L1935.
- **Cotizador simple** (historial): `quoteData` L1354, `saveQuote` L1358,
  `quoteText` L1363, `sendQuoteWhatsApp` L1372, `printQuote` L1373, `loadQuotes`
  L1386, `aprobarQuote` L1405.
- **Fotos**: `fileToDataURL` L1498, `setFotoProyecto` L1513, `setFotoProducto`
  L1527, `renderFotosGrid` L1533.

## PERMISOS

Token admin para todo. Sin endpoints públicos. El PDF/documento puede compartirse
por WhatsApp a terceros (es el propósito).

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L1354–1430 (simple), L1419–1941 (profesional) | ambos cotizadores |
| `admin/apps-script.gs` L79, L812–835, L1399–1473 | esquema + handlers |
| `scripts/auditoria/test_cotizador_precio_final.py` | precio final único + IVA |
| `scripts/auditoria/test_flujo_cotizador.py` | flujo del cotizador (backend simulado) |
| `scripts/auditoria/test_fase3_api.py` | `quote`/`set_estado_quote` en vivo |
| `ARCHIVO_ADIS\documentos\Formato de Cotizacion nuevo.docx` | referencia de diseño (fuente) |

## INTEGRACIONES

- Sheets (Cotizaciones) · Apps Script · CDN jsPDF/html2canvas (`cargarScriptCDN`
  L1778) · WhatsApp (`waNum` +52/+1 L1767) · productos del ERP · localStorage.

## QUÉ NO MODIFICAR

- El formato plano de éxito de `quote` (`{ok, folio}`) y la retrocompatibilidad
  del payload.
- La regla "precio final único en el PDF" (decisión del dueño).
- El algoritmo de folios (Core) y la no-consumición de folio al re-guardar.
- ENC_COTIZ: columnas nuevas solo al final.

## PRUEBAS

- `python scripts/auditoria/test_cotizador_precio_final.py`
- `python scripts/auditoria/test_flujo_cotizador.py`
- `python scripts/auditoria/test_fase3_api.py` (quote en vivo; tras redeploy).
- Casos críticos: folio consecutivo sin duplicar, re-guardar conserva folio,
  PDF sin hojas en blanco ni fotos partidas, IVA correcto (2 placas × $850 + IVA
  = $1,972.00 MXN), WhatsApp con número +52/+1.
- Tras modificar: las 3 suites + regresión fase0.

## EJEMPLOS DE INTERACCIÓN

1. **Aprobación (04→05)**: historial → `aprobarQuote`/`set_estado_quote`
  (aprobada) → `crear_proyecto_desde_cotizacion` → proyecto con cliente,
  cotizacion_id y folio PRY- nuevo, sin recapturar.
2. **Alerta (08←04)**: `alertas` detecta cotizaciones pendientes viejas y las
   muestra en el dashboard y en Resultados.
3. **Lead → cotización (03→04)**: `matchLead` pre-llena datos del cliente desde
   el lead convertido.
