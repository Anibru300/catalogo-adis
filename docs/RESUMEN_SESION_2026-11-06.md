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

## 3. DESARROLLADO Y VALIDADO — PENDIENTE DE AUTORIZACIÓN PARA DESPLEGAR (commit `55dc8ce`)
**Actividades 2–3** (formularios con listas desplegables + reportes):
- Dropdown de **categorías de gasto** organizadas según la operación real (20),
  con sugerencia automática de naturaleza (siempre editable).
- Dropdown de **categoría de ingreso** (7) que se guarda y aparece en reportes;
  sugiere tipo de ingreso (aportación/anticipo nunca se asumen como venta).
- **Ingresos por categoría** en Control I/E (doughnut + tabla).
- Backend: columna `categoria` al final de Cobros (aditiva) +
  `control_ie.ingresos.por_categoria`.
- Script de sincronización de catálogos listo (dry-run aprobado: +16 categorías
  gasto, +7 ingreso, mapeo de 20 sugerencias). **Sandbox: 40/40 PASS.**
- Despliegue sugerido: nuevo backend → sincronizar catálogos → publicar panel.

## 4. LA PLATAFORMA HOY (forma actual del ERP ADIS)
- **12 módulos operativos** (existencias, compras, comercial, cotizador, proyectos,
  ventas/cobros, gastos/pagos, resultados, marketing, sitio público, sistema) con
  backend modular (core.gs + analítica), panel por build y folios bajo LockService.
- **Finanzas Etapa 1 COMPLETA**: captura simple (ingreso/egreso en segundos),
  clasificación por naturaleza, retiros separados, efectivo real visible con
  simulador, P&L honesto (provisional) y 100% de los históricos clasificados.
- Infraestructura de calidad: respaldos (git + JSON + copias físicas), sandbox en
  Node que ejecuta el código real contra snapshots (40 pruebas), suites de
  regresión de solo lectura, procedimiento de despliegue/reversión documentado
  (`99_DOCUMENTACION/PROCEDIMIENTO_DESPLIEGUE_ETAPA1.md`).

## 5. PENDIENTES Y PRÓXIMOS PASOS (requieren decisión del propietario)
1. **Autorizar despliegue de Actividades 2–3** (listas desplegables y reportes).
2. Decidir si se retiran las categorías viejas del catálogo (`--quitar-viejas`).
3. Observación para Etapa 2: las compras de mercancía de oct (~$40,139) no
   entraron como movimientos de inventario — si la mercancía está en almacén,
   el stock no la refleja (se resuelve con el módulo Compras/Inventario).
4. Rotación de credenciales (pendiente desde sep-2026; procedimiento seguro listo).
5. Etapas futuras (congeladas hasta autorización): 2 = integración operativa
   (ventas con productos/clientes, compras→inventario, CxP de OC);
   3 = rentabilidad (costos de venta, utilidad real por producto/proyecto);
   4 = análisis avanzado (balance, presupuestos, proyecciones).

## Commits de la jornada
`a11c8cc` Fase 0/1 → `598ef4d` control_ie + simulador → `2f44d59` validación final →
`96a25cb` procedimiento seguro → `3d70be4` sandbox Node + 2 bugs críticos →
`25b929a` panel en producción → `d6ca0fa` respaldo + conciliación posterior →
`0a097af` conciliación definitiva → `55dc8ce` Actividades 2–3 (sin desplegar).
