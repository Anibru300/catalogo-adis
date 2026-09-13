# 📊 08_RESULTADOS — P&L, Flujo de Caja, Alertas y Dashboard

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§3 regla 6, §8 moneda).
> **Solo lectura** sobre los demás módulos: no escribe hojas de negocio.
> Fuente: `admin/index.html`, `admin/apps-script.gs`,
> `scripts/auditoria/test_fase5_api.py` (flujo), `test_fase6_api.py`.

## IDENTIDAD

- **Objetivo**: dar la foto financiera del negocio: utilidad del mes (P&L),
  efectivo real entrado/salido (flujo de caja), problemas que requieren atención
  (alertas) y un tablero resumen al entrar (dashboard).
- **Responsabilidad**: endpoints de agregación; tabs `pnl`, `flujocaja`, `dash`
  (Resumen, con cmdk).
- **Problema que resuelve**: el dueño responde en segundos "¿gané o perdí?",
  "¿cuánto efectivo tengo?" y "¿qué urge?".

## ALCANCE

- **Hace**: estado de resultados mensual (ingresos − costos − gastos, márgenes,
  imprimible, filtrable por proyecto), flujo de efectivo por rango (cobros −
  pagos, día/semana/mes/año), alertas priorizadas (CRÍTICA>ALTA>MEDIA), dashboard
  con KPIs + gráficas CSS + buscador de módulos (Ctrl+K).
- **NO hace**: registrar ventas/gastos (06/07), mover dinero, editar datos —
  es lectura agregada pura.
- **Pertenecen aquí**: los 3 endpoints de agregación + las 3 vistas.

## DATOS

- **Hojas** (lectura, sin escritura): Ventas, Gastos, Cobros, Pagos, Stock,
  Productos, Cotizaciones, Proyectos.
- **Consume**: utilidad_base/costo de Ventas (06), monto_base de Gastos (07),
  Cobros (06) y Pagos (07) para efectivo real, stock/precios para alertas.
- **Genera**: respuestas agregadas (ninguna persistida); las alertas se calculan
  en vivo en cada llamada.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE`; `06_VENTAS_COBROS`; `07_GASTOS_PAGOS`;
  `01_EXISTENCIAS` (valor de inventario, stock para alertas); `05_PROYECTOS`
  (P&L por proyecto); `04_COTIZADOR` (cotizaciones viejas en alertas).
- **ALIMENTA A**: el dashboard (mismo módulo) es la primera pantalla del panel.
- **COMPARTE CON**: todos (solo lectura).

## REGLAS DE NEGOCIO

1. **P&L contable, caja efectiva**: el P&L cuenta ventas/gastos por fecha de
   registro; el flujo de caja cuenta cobros/pagos por fecha real — fuente
   oficial: CONTEXTO_GLOBAL §3.6.
2. **Ventas CANCELADAS excluidas** del ingreso; gastos CANCELADOS excluidos.
3. Fechas comparadas como strings YYYY-MM-DD validadas al escribir (06/07) —
   registros con formato raro quedan fuera silenciosamente (deuda conocida).
4. Alertas priorizadas CRÍTICA > ALTA > MEDIA: stock negativo/bajo/cero, productos
   sin precio/costo, CxC/CxP > 30 días, cotizaciones pendientes viejas, OCs por
   recibir.

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `estado_resultados&mes=YYYY-MM` | GET | `{ingresos, costos, utilidad_bruta, gastos:{cat}, total_gastos, utilidad_neta, num_ventas, margen_bruto, margen_neto, moneda_base}`; fase 6: filtro `proyecto_id`, niveles bruta/operativa/neta |
| `flujo_caja?desde=&hasta=` | GET | `{cobros, pagos, neto}` por fecha real (Cobros−Pagos) |
| `alertas` | GET | Lista priorizada con tipo y detalle |

- Handlers: `apps-script.gs` L500–607 (P&L), L722–760 (flujo), L556–607
  (alertas). Errores: `VALIDACION` (mes/rango mal formado).

## FRONTEND (tabs `pnl`, `flujocaja`, `dash`)

- **Dashboard** (`dash`): KPIs, top alertas (enlace a pnl), accesos rápidos;
  `loadDash` L1052; buscador Ctrl+K `abrirCmdk/pintarCmdk/irCmdk` L1106–1131.
- **P&L**: `generarPNL` L3039 (selectores mes/proyecto, tabla niveles,
  márgenes), `printPNL` L3069, `fillPnlProyectos` L2990, `loadAlertas` L2972.
- **Flujo de caja**: `loadFlujoCaja` L2937 (rango, barras CSS, totales).
- **Ficha de proyecto**: `fichaProyecto` L2999 y `saveProyectoMov` L3028
  (documentadas en 05; la rentabilidad por proyecto se visualiza aquí).

## PERMISOS

Token admin (solo lectura). Sin endpoints públicos.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L1052–1131 (dash), L2937–3069 | vistas del módulo |
| `admin/apps-script.gs` L500–607, L722–760 | handlers de agregación |
| `scripts/auditoria/test_fase5_api.py` | flujo de caja + P&L excluye cancelados |
| `scripts/auditoria/test_fase6_api.py` | P&L por proyecto, anuladas excluidas, alertas priorizadas |

## INTEGRACIONES

- Sheets (lectura multi-hoja) · Apps Script · consume de 01/04/05/06/07.

## QUÉ NO MODIFICAR

- Las definiciones de utilidad/margen (impactan decisiones del negocio; un
  cambio aquí es de producto, no de implementación).
- La exclusión de CANCELADAS (regla acordada fase 5/6).
- No agregar escrituras: este módulo es de solo lectura por diseño.

## PRUEBAS

- `python scripts/auditoria/test_fase5_api.py` y `test_fase6_api.py` (tras redeploy).
- Casos críticos: venta anulada no suma ingreso; gasto cancelado no suma gasto;
  flujo neto = cobros − pagos (no ventas − gastos); alertas ordenadas por
  severidad.
- Tras modificar: fase5 + fase6 + regresión fase0.

## EJEMPLOS DE INTERACCIÓN

1. **Cierre de mes**: `estado_resultados?mes=2026-09` → ingresos de Ventas,
   costos desde movimientos de venta, gastos por categoría, utilidad neta y
   márgenes.
2. **¿Cuánto efectivo moví?**: `flujo_caja?desde=2026-09-01&hasta=2026-09-30` →
   cobros reales (06) menos pagos reales (07).
3. **Dashboard al entrar**: `loadDash` consume `alertas` y muestra las 8 primeras
   con enlace al P&L completo.
