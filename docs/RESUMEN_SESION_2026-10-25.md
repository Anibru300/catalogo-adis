# Resumen de sesión — 2026-10-25

## ➡️ PRÓXIMOS PASOS (continuar aquí)

1. ~~REDEPLOY del Apps Script~~ ✅ **HECHO el 2026-10-25** (cuenta
   `ing.carlosurbona300@gmail.com`, proyecto con código, vía ✏️ Nueva versión).
   Verificado en vivo: bitácora, 18 categorías, gastos fijos (fechas exactas,
   sin corrimiento de día), "Ya lo pagué" (gasto+pago en un paso), log_cliente.
2. **Pendiente del dueño (uso real)**: probar en producción un gasto con
   "Sí, ya lo pagué" y programar sus gastos fijos reales (renta, internet...).
   La Bitácora (Sistema → Bitácora) ya registra errores si algo falla.
3. Días **09–14 y 16–18 oct siguen sin datos** — cargarlos con el dueño usando
   los formularios del panel.

## Hecho hoy (commit `40e15b5`, en producción tras deploy de Pages)

**Regla acordada con el dueño: todo cambio debe ser fácil, intuitivo, amigable
y lo más automatizado posible (listas desplegables + guía en cada apartado).**

- **Cuadro de ayuda en cada sección** del panel (componente `details.helpbox`
  en `00_CORE/design-system/admin.css`): 17 secciones explican "¿para qué sirve
  y cómo lo uso?"; la pestaña Ayuda sigue como guía completa.
- **"¿Ya lo pagaste?"** en Registrar gasto: registra gasto Y pago en un solo
  paso (antes eran dos). Backend `gasto` devuelve `id` para encadenar el pago.
- **Avisos flotantes** (`#notice` fixed): antes el mensaje de confirmación
  quedaba arriba de todo y el dueño no lo veía (creyó que no se había
  guardado el ingreso de $25,000). Mensajes explícitos: "✅ Ingreso correcto —
  folio ING-XXXX · $…".
- **Gastos fijos (programados)**: pestaña nueva Dinero → Gastos fijos.
  Frecuencia semanal/quincenal/mensual/anual, alertas 🔴 vencido / 🟠 por
  vencer (≤3 días), aviso global al entrar al panel, "Generar gasto" crea el
  GAS- y programa la siguiente fecha solo.
- **Menús renombrados** a pedido del dueño: "Cobros / cuentas por cobrar" →
  "Registrar ingreso"; "Gastos / cuentas por pagar" → "Registrar gasto".
- `ingFecha` ahora se pre-llena con hoy (`fLocal`; antes quedaba vacío y
  `gFecha` se adelantaba un día por UTC).
- URL correcta del panel: **https://adis-diseño.com/admin.html** (Pages sirve
  la carpeta `public/` como raíz; `/public/admin.html` NO existe — se dijo mal
  el 18-oct).

## Verificación del día

regresión fase0 19/19 ✅ · smoke tabs finanzas ✅ 0 errores JS · backend
sintaxis ✅ · deploy Pages verificado en vivo (helpbox + menú nuevos presentes)
✅.

## Archivos tocados (commit `40e15b5`, rama main)

`00_CORE/backend/core.gs`, `00_CORE/design-system/admin.css`,
`00_CORE/shared_js/admin_core.js`, `00_CORE/shared_js/admin_nav.js`,
`07_GASTOS_PAGOS/admin/gastos.js`, `07_GASTOS_PAGOS/CONTEXTO.md`,
`admin/plantilla.html`, `admin/index.html`, `admin/apps-script.gs`,
`public/admin.html`.

## Pendientes de fondo (sin cambio)

Escáner de código de barras, conteo físico asistido, historial de precios,
exportar movimientos a Excel, GA4, compras de mercancía por flujo COMPRAS,
fichas técnicas SENZ (pendientes del proveedor; regla: nunca publicar marca
del proveedor), papel tapiz SENZ (siguiente tanda del catálogo), decisión
sobre "Gastos personales" en el P&L ($3,303.72 acumulados).
