# Resumen de sesión — 2026-10-18

## Contexto / dinámica acordada

El dueño pasa sus movimientos en crudo → se **capturan en la plataforma** (ingresos
y egresos con folio), se **catalogan** (categorías configurables) y se **presentan
en el dashboard**. Todo queda en la hoja ERP (fuente maestra). Reglas de captura:
**todo es MXN salvo indicación de USD; todo gasto ya está pagado salvo indicación
de "por pagar"** (entonces el pago se registra después).

---

## ➡️ PRÓXIMOS PASOS (continuar aquí)

1. **REDEPLOY pendiente del dueño** (el único). Activar dos cosas que ya están
   en el código (commit `e46658a`, archivo `admin/apps-script.gs`, 2209 líneas):
   - Fix del endpoint de categorías (campo `clase`; sin esto el gestor de
     INVENTARIO → Configuración falla).
   - Los ingresos sin venta pasan a contar como **Ventas del mes** (campo
     `tipo=venta|otro` en Cobros; sin redeploy siguen apareciendo como "Otros
     ingresos").
   Pasos: Hoja ERP → Extensiones > Apps Script → borrar todo, pegar el archivo
   fresco del disco → Implementar > Administrar implementaciones > ✏️ >
   **Nueva versión** > Implementar (NUNCA "Nueva implementación") → esperar
   2-5 min → avisar para verificación en vivo.
2. **Tras ese redeploy**: (a) agregar al catálogo las categorías usadas:
   Honorarios, Gastos personales, Compra de inventario, Alimentos, Materiales,
   Equipos, Muestrario; (b) verificar que el dashboard muestre Ventas (5)
   $24,775 y Otros ingresos $0; (c) capturar un gasto/ingreso de prueba.
3. **Papel tapiz** — siguiente tanda del catálogo SENZ (avisó el dueño: "pa no
   atacarlo le mando eso primero"). Mismo procedimiento que persianas.
4. **Fichas técnicas SENZ** — no son públicas (su "CATÁLOGO PDF" lleva al portal
   de distribuidores con login). El dueño debe pedir a SENZ: catálogos PDF por
   línea, fichas técnicas y kit de marca. La web ya tiene el slot listo:
   soltar el PDF en `public/catalogos/pdf/catalogo_persianas-y-cortinas.pdf`
   y la tarjeta de descarga funciona sola.
5. Días **09–14 y 16–18 oct sin datos** — cargar con su fecha real si el dueño
   los pasa.
6. Decisión pendiente: **"Gastos personales"** ($3,303.72 acumulados) bajan la
   utilidad del negocio en el P&L. Si el dueño prefiere llevarlos aparte, se
   cancelan (baja lógica, no se borran).

---

## 1. Finanzas — backend (`00_CORE/backend/core.gs`)

- Drift con el desplegado resuelto (`ventas.porMes` portado al canónico).
- Nuevo helper `calcularEstadoResultados(mes, proyFiltro)` usado por
  `estado_resultados` y `finanzas_mensual`.
- Endpoints: `POST ingreso` (folio ING-, escribe en Cobros sin venta_id),
  `POST categoria` (catálogo configurable en Config; campo `clase`),
  `GET finanzas_mensual` (12 meses en un request), `GET config` ahora devuelve
  `categorias_gastos/ingresos`.
- Cobros sin venta: campo `tipo` (`venta` default | `otro`). Los ingresos del
  dueño son ventas → cuentan en Ventas del mes, no en Otros ingresos.
- `verificar_fuentes.py` FUENTES CONSISTENTES; drift 0 core↔deploy.

## 2. Finanzas — panel

- DINERO → Cobros: formulario "Registrar ingreso" con selector Tipo
  (Venta / Otro ingreso) → `addIngreso()`.
- INVENTARIO → ⚙️ Configuración: gestor de categorías (chips con ✕ doble-clic,
  alta por tipo) — **activo tras el redeploy**.
- Tab Gastos: datalist de categorías se llena desde config (`poblarCategorias`).
- SITIO WEB → Negocio: 2 gráficas Chart.js de 12 meses (`finanzas_mensual`):
  Ingresos vs Egresos y Gastos por categoría apilados. Dashboard (Resumen)
  separa Ventas de Otros ingresos.
- ⚠️ El panel en vivo es `public/admin.html` (copia de `admin/index.html` en el
  build del sitio) — cualquier cambio al panel exige regenerar o se ve viejo.

## 3. Finanzas — carga real del dueño (VERIFICADO EN PRODUCCIÓN)

06→15 oct: **18 gastos (GAS-0001..0018) + 5 ingresos (ING-0001..0005) + 18
pagos (PAG-0001..0018)**. Octubre: ingresos $24,775 · gastos $44,179.82 ·
flujo neto **−$19,404.82** (el día 15 concentró $21k de materiales/inventario) ·
por pagar $0.

Herramienta: `60_DATA/capturar_movimiento.py` (gasto/ingreso/pago, batch JSON;
`pago` liquida por `gasto_folio`). Archivos: `movimientos_2026-10-*.json`,
`pagos_2026-10-*.json`, `pendientes_ingresos_2026-10-06.json` (ya subidos).

## 4. Web — categoría 10 "Persianas y Cortinas" (proveedor SENZ)

- **EN VIVO**: `adis-diseño.com/10-persianas-y-cortinas.html` (+ `/en/`).
  6 persianas (Enrollables, Duo Sheer Elegance, Romana, Panel Japonés, Vienna,
  Cellular) + Cortinas Personalizadas. 28 fotos oficiales de senz.com.mx,
  galería por producto, botón Cotizar→WhatsApp, sin precios (a medida, por m²).
- Fotos: `60_DATA/importar_persianas_senz.py` → `CATALOGO FINAL\10. Persianas y
  Cortinas\` (Drive). Slugs: cat `10-persianas-y-cortinas`, subs `101-persianas`,
  `102-cortinas`.
- ERP: productos SENZ-ENR-01..SENZ-COR-07 (precio/costo 0, proveedor SENZ).
- Generador: MEGA_ITEMS + `menu_persianas` + icono `blinds` (web_utils.py) +
  traducciones ES→EN. Lección anotada en `10_SITIO_PUBLICO/CONTEXTO.md`: qué
  tocar para agregar una categoría nueva.
- Verificación: smoke `cap_persianas.py` 10/10 PASS; página 200 en producción;
  home y mega-menú la muestran; 0 errores JS.

## 5. Proveedores

- **SENZ (Persianas y Cortinas)** registrado (COMPRAS → Proveedores, id
  479c6c63): qué surte, sitio, productos ligados, pendientes (ventas/precios/kit).
- Los 7 productos SENZ llevan `proveedor='SENZ'` en la hoja — base del catálogo
  de proveedores (info + productos que surte).

## Verificación del día

node --check ✅ · builds ✅ · regresión fase0 19/19 ✅ · smoke estadísticas
11/11 ✅ · smoke tabs finanzas ✅ · smoke persianas 10/10 ✅ · verificar_fuentes
✅ · producción (página viva, home, panel) 4/4 ✅ · 0 errores JS en todo.

## Archivos tocados (todos commiteados, rama main)

`00_CORE/backend/core.gs`, `admin/apps-script.gs`, `admin/index.html`,
`public/admin.html`, `admin/plantilla.html`, `07_GASTOS_PAGOS/admin/gastos.js`,
`01_EXISTENCIAS/admin/existencias.js`, `08_RESULTADOS/admin/dashboard.js`,
`09_MARKETING/admin/estadisticas.js`, `00_CORE/shared/web_utils.py`,
`00_CORE/i18n/translations.py`, `00_CORE/i18n/traducciones_productos.json`,
`10_SITIO_PUBLICO/sitio/{componentes,paginas}.py`, `public/` completo,
`60_DATA/` (capturar_movimiento, importar_persianas_senz, dataset, lotes),
`scripts/auditoria/` (cap_estadisticas, cap_tabs_finanzas, cap_persianas),
docs: este resumen, `07_GASTOS_PAGOS/CONTEXTO.md`, `08_RESULTADOS/CONTEXTO.md`,
`10_SITIO_PUBLICO/CONTEXTO.md`, `docs/ADMIN_ARCHITECTURE.md`,
`00_CORE/CONTEXTO_GLOBAL.md`.

## Pendientes de fondo (sin cambio)

Escáner de código de barras, conteo físico asistido, historial de precios,
exportar movimientos a Excel, GA4, compras de mercancía por flujo COMPRAS
(para que también suba inventario — hoy solo se registran como gasto).
