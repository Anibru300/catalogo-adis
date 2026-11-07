# RESUMEN DE SESIÓN — 2026-11-06

> Jornada completa: **Etapa 1 financiera DESPLEGADA EN PRODUCCIÓN** y 49 gastos
> históricos clasificados con autorización del propietario. La plataforma ya
> "dice a dónde se va el dinero de ADIS".

---

## 1. LO QUE SE DESPLEGÓ A PRODUCCIÓN (hoy, autorizado)

### Etapa 1 — Control de Ingresos y Egresos (commit `25b929a` + backend en Apps Script)
- **Nuevo reporte principal**: tab **Control de Ingresos y Egresos** (Dinero):
  ingresos recibidos, egresos pagados, variación neta (incluye retiros,
  inventario e inversiones), desgloses por naturaleza y categoría con %,
  comparativo 12 meses, principales conceptos, pendientes de clasificar y
  **simulador de escenarios** (hipotético, sin tocar datos).
- **Clasificación financiera**: columna `naturaleza` en Gastos
  (operativo / costo_directo / inventario / inversion / retiro / por_clasificar).
- **Retiros del propietario**: salen del efectivo como financiamiento, NO son
  gasto del negocio; reporte propio por día/mes/año/periodo.
- **Tipos de ingreso** ampliados (venta/otro/reembolso/aportacion/prestamo/anticipo);
  aportaciones y préstamos jamás entran al P&L.
- **P&L rotulado PROVISIONAL**: sin "utilidad neta" ficticia ni margen 100%;
  "Resultado provisional del periodo".
- **Flujo de caja por actividad** (operación/inversión/financiamiento).
- **Correcciones Fase 0**: TC histórico preservado en ediciones · Gastos/Stock
  protegidos de borrado físico · bitácora sin duplicados · ventas porMes sin
  canceladas · fechas normalizadas (fix: los filtros mensuales ya incluyen el
  último día del mes) · flags de sobrepago en CxC/CxP.
- **2 bugs críticos detectados en sandbox y corregidos antes de desplegar**:
  `parseF` fuera de alcance (rompería `control_ie`) y columna `naturaleza` sin
  garantía de encabezado (clasificación temprana quedaría invisible).

### Verificación posterior al despliegue
- Suites automáticas: **24/24 y 9/9 PASS** en producción real.
- Conciliación oct-2026 exacta: ingresos **$42,490.00** · egresos **$69,231.04** ·
  neto **−$26,741.04**. Fix de último día del mes confirmado en vivo.

## 2. RECLASIFICACIÓN DE LOS 49 GASTOS HISTÓRICOS (autorizada y aplicada)
- Proceso: propuesta → tu revisión → conciliación definitiva → **aplicación 49/49,
  0 fallos** (solo columna naturaleza; integridad 100% verificada; respaldo en
  `60_DATA/respaldo_pre_reclasificacion_2026-11-06.json`).
- **Distribución real del dinero de ADIS (oct–nov 2026)**:
  - 📦 Inventario (mercancía): **$40,139.32** (41.2%) — 9 movimientos
  - 🏢 Operativo: **$26,227.00** (26.9%) — 21 movimientos
  - 🔴 Retiro del propietario: **$24,804.72** (25.5%) — 17 movimientos
  - 🔧 Inversión (teléfono + muestrario): **$6,200.00** (6.4%) — 2 movimientos
- Los 7 registros de prueba cancelados quedaron intactos; bitácora con 49 eventos.

## 3. DESPLEGADO TAMBIÉN HOY (autorizado) — Actividades 2–3 COMPLETAS EN PRODUCCIÓN
- **Backend**: nueva versión de Apps Script (columna `categoria` al final de Cobros,
  `control_ie.ingresos.por_categoria`, guard de esquema en Cobros, nuevas categorías
  por defecto). Verificado en vivo: 9/9 y 20/24 (los 4 restantes eran comparación
  contra snapshot viejo: el dueño ya había capturado 3 gastos reales nuevos,
  todos bien clasificados: GAS-0057 inventario, GAS-0058/0059 operativo).
- **Catálogos sincronizados**: 20 categorías de gasto + 7 de ingreso + mapeo de
  20 sugerencias categoria→naturaleza en Config (`mapa_naturalezas`). Las viejas
  se conservan en transición (retirables con `--quitar-viejas`).
- **Panel publicado** (push `25b929a..786f8d2`): botones "Página pública" y
  "Salir" en el login; Resumen con la distribución Etapa 1 del mes (gastos
  operativos, compra de mercancía, retiros, inversiones, pendientes); dropdowns
  de categorías con sugerencia de naturaleza/tipo; "Ingresos por categoría".
- Uso real inmediato: 3 gastos capturados por el dueño con clasificación correcta.

## Commits de la jornada
`a11c8cc` Fase 0/1 → `598ef4d` control_ie + simulador → `2f44d59` validación final →
`96a25cb` procedimiento seguro → `3d70be4` sandbox Node + 2 bugs críticos →
`25b929a` panel Etapa 1 en producción → `d6ca0fa` respaldo + conciliación posterior →
`0a097af` conciliación definitiva → `55dc8ce` Actividades 2–3 → `d9eeaac` resumen sesión →
`c4619a2` botones login → `786f8d2` Resumen con distribución Etapa 1.
