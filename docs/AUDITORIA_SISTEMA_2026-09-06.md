# 🔍 Auditoría del Sistema Administrativo ADIS — 6 de septiembre de 2026

> Diagnóstico completo previo a la evolución del panel hacia un sistema integral.
> Alcance: `admin/index.html` (1,565 líneas), `admin/apps-script.gs` (639 líneas),
> `generar_web.py` (puntos de integración), `scripts/auditoria/importar_maestro.py`, `docs/`.
> NO se modificó código en esta fase.

---

## A. ESTADO ACTUAL — Módulos que existen realmente

| Módulo | Estado | Notas |
|---|---|---|
| Login / sesión | ✅ Funcional | Usuario+clave → token UUID 8h en CacheService. sessionStorage en frontend. |
| Leads | ✅ Funcional | Alta pública (formulario web), lectura en panel. Sin gestión (no hay convertir a cliente, estados, seguimiento). |
| Cotización simple | ⚠️ A medio camino | Sin folio, sin IVA, sin editar/borrar. Duplicada con el cotizador profesional. |
| Cotizador profesional | ✅ Funcional | Formato Word secciones 01–09, folio ADIS-AAAA-NNN, PDF vía window.print(), fotos en localStorage (NO persisten en Sheets). |
| Inventario (productos) | ✅ Funcional | CRUD, soft-delete, foto por ruta de texto (sin upload real — Fase 2 pendiente). |
| Almacenes + Stock | ✅ Funcional | Hoja Stock (producto_id + almacen_id + cantidad). |
| Movimientos | ✅ Funcional | Entrada/salida/ajuste con bitácora, pero sin existencia anterior/posterior ni documento origen. |
| Ventas | ✅ Funcional | Descuenta stock, calcula utilidad. Sin estados de pago, sin anulación, sin folio. |
| Gastos | ✅ Funcional | Alta/baja. Sin editar, sin proveedor, sin proyecto, sin estados (registrado vs pagado). |
| Estado de resultados | ✅ Funcional | Mensual simple: ingresos − costos − gastos. No separa ventas de cobros. |
| Reseñas | ✅ Funcional | Alta/baja, filtro `activa`. Públicas vía `?action=reviews`. |
| Flujo (analítica web) | ✅ Funcional | Tracker en sitio público (sendBeacon, dedup por sesión), panel con KPIs/agregados. |
| Estadísticas | ⛔ Placeholder | Solo iframe de Looker Studio si se configura URL a mano. |
| Configuración | ✅ Mínima | Solo moneda_base, tipo_cambio, folio_cotizacion. |
| **NO existen** | ⛔ | Clientes, Prospectos, Proyectos, Órdenes de compra, Proveedores, Cuentas por cobrar, Cuentas por pagar, Flujo de efectivo, Pagos, Usuarios/roles, Dashboard ejecutivo, Alertas, Buscador global. |

## B. MAPA DE ARQUITECTURA

```
SITIO PÚBLICO (public/, generado por generar_web.py)
  ├─ Formulario contacto ──POST tipo:'lead'─────┐
  ├─ Testimonios ─────GET ?action=reviews ──────┤  (públicos, sin token)
  └─ Tracker visitas ──POST tipo:'track'────────┘
                                                 ▼
PANEL ADMIN (admin/index.html → public/admin.html, monolito HTML+CSS+JS)
  └─ apiGet/apiPost ──text/plain JSON──► GOOGLE APPS SCRIPT (admin/apps-script.gs)
                                          ├─ doGet: me, leads, quotes, reviews, reviews_admin,
                                          │   visitas, config, productos, almacenes, stock,
                                          │   movimientos, ventas, gastos, estado_resultados
                                          └─ doPost: login, lead*, track*, quote, review,
                                              delete_review, config, save_product, delete_product,
                                              restore_product, import_productos, delete_row,
                                              save_almacen, delete_almacen, movimiento, venta,
                                              gasto, delete_gasto
                                                 ▼
                              GOOGLE SHEETS (13 pestañas: Leads, Cotizaciones, Reseñas,
                              Productos, Almacenes, Stock, Movimientos, Ventas, Gastos,
                              Config, Log, Visitas + auto-creadas)
```

**Flujo de datos clave:** la cotización guarda `datos` (JSON string) en Sheets; al re-cargar, las fotos NO se recuperan (viven en localStorage del navegador que la creó). Los productos del ERP (hoja Productos) y los del cotizador simple (products.json público) son **dos fuentes distintas**.

## C. PROBLEMAS DETECTADOS

### Arquitectura
1. **Cero locking (LockService no se usa)**: folios (carrera clásica read-modify-write sobre Config), stock (salidas concurrentes pierden existencia), ventas (TOCTOU: valida stock y luego descuenta sin lock). Folios duplicados y stock incorrecto son probables bajo concurrencia real.
2. **Cero transaccionalidad**: una venta toca 4–5 hojas (validación → N movimientos → Ventas → Log). Si falla a mitad, queda stock descontado sin fila de venta. Sin rollback posible.
3. **Rendimiento N+1**: `venta` re-lee la hoja Productos completa por cada item; `cfg()` re-lee Config completa en cada llamada (decenas de veces por request). Riesgo de timeout de Apps Script con catálogo creciente.
4. **Borrados por índice de fila** (delete_review/delete_gasto/delete_row con `i+2`): si el orden en la UI no coincide con el de la hoja, se borra la fila equivocada.
5. **Esquema de Cotizaciones extendido condicionalmente** (cols 8–15 solo si col 8 está vacía): si la hoja ya tenía datos con otro esquema, la extensión nunca se aplica.
6. **Dos sistemas de productos** (products.json público vs hoja Productos) y **dos cotizadores** superpuestos.

### Datos
7. Movimientos sin existencia anterior/posterior, sin usuario, sin documento origen → la existencia NO es consecuencia trazable de movimientos (contradice la regla del negocio).
8. Fechas inconsistentes: `filasComoObjetos` normaliza a `yyyy-MM-dd HH:mm`, pero Ventas/Gastos aceptan fecha del cliente sin validar formato; el rango del estado de resultados compara strings lexicográficos → registros con formato distinto quedan fuera silenciosamente.
9. Flag "REVISAR" = substring `REVISION` en `notas` (frágil). Stock negativo permitido sin aviso.
10. Folio desborda formato NNN tras 999 (`ADIS-2026-1000`).
11. Sin IDs únicos estables para clientes, ventas, gastos (todo por fila). Los IDs de producto existen.

### Seguridad
12. **Credenciales en claro en el repo** (apps-script.gs L20-21, importar_maestro.py L14) y el usuario admin queda persistido en cada fila del Log.
13. Token 8h: sin rotación, sin revocación, sin límite de sesiones activas (cada login acumula una sesión viva). En GET viaja como query param (queda en logs).
14. Endpoint público `track` sin rate-limit: un atacante puede saturar las 5000 filas y provocar el borrado del historial real (poda automática).
15. Autorización plana: un solo rol; cualquier token puede `import_productos` con reset:true (borra Productos/Stock/Movimientos) y `delete_row` sobre Ventas/Movimientos (manipulación de resultados).
16. Sin try/catch fuera del parseo JSON → un error de Sheets devuelve HTML de error de Google, rompiendo el contrato `{ok, error}` que el frontend espera.
17. admin.html sin `noindex` (solo robots.txt, que es orientativo).

### UX / Frontend
18. **Emojis como iconos en toda la UI** (tabs, botones, KPIs; 📊 duplicado en dos tabs).
19. **window.confirm() en 5 operaciones** (newProposal, deleteReview, deleteProduct, deleteWarehouse, deleteExpense).
20. Tablas sin paginación/ordenamiento/filtros por columna; la mayoría sin buscador.
21. Sin feedback de operaciones (no hay "Guardando…", botones no se deshabilitan → doble POST posible). apiPost sin `.catch` en la mayoría de llamados.
22. Sin manejo de expiración de token en frontend (no redirige al login).
23. Navegación: 10 tabs horizontales con wrap — límite alcanzado, no escala.
24. Logo roto en login/PDF (`LOGO%20ADIS.webp` no existe en admin/).
25. CSS inline abundante junto a un bloque `<style>` con variables (mezcla de convenciones).
26. Monolingüe (solo ES), fechas UTC (`toISOString`) puede dar día anterior en MX.

### Mantenibilidad
27. Monolito: 930 líneas de JS global con onclick inline; funciones largas (buildProposalHTML ~80 líneas de strings); HTML por concatenación con interpolación de IDs sin escapar.
28. Encabezados de hojas duplicados literalmente (Movimientos ×3, Productos ×2); índices de columna hardcodeados por posición (col 5, 14, 16, 4, 3…).
29. Código muerto: constante MONEDAS sin uso, condición `indexOf('PEGAR')===0` imposible, clase `qp-qp-4` inexistente.
30. URL del backend hardcodeada en 4 archivos (generar_web.py ×2, admin/index.html, importar_maestro.py).

## D. FUNCIONES FALTANTES

### CRÍTICAS (bloquean la confiabilidad del sistema)
1. LockService + try/catch global en backend (folios, stock, ventas).
2. Movimientos de inventario completos (existencia anterior/posterior, tipo real, referencia a documento, usuario) — base de toda trazabilidad.
3. IDs únicos estables + eliminación por ID (no por índice de fila).
4. Módulo de Clientes/Prospectos (unificar leads → clientes).
5. Órdenes de compra con recepción parcial → entrada automática de inventario.
6. Ventas 2.0: estados de pago (pendiente/parcial/pagada), cobros parciales, folio, anulación con reverso.
7. Cuentas por cobrar y por pagar.
8. Separación venta↔cobro y gasto↔pago + Flujo de efectivo real.
9. Dashboard ejecutivo (la primera pantalla).
10. Rediseño visual del panel (sidebar, iconos SVG profesionales, sin emojis).

### IMPORTANTES
11. Proyectos (ficha financiera, presupuesto vs real, rentabilidad).
12. Proveedores (catálogo propio, no texto libre).
13. Gastos 2.0: editar, proveedor, proyecto, estado pagado/pendiente.
14. Sistema de alertas (stock bajo, sin precio, sin foto, saldos vencidos, OC atrasada…).
15. Modales propios (reemplazar confirm()).
16. Tablas profesionales (paginación, ordenamiento, filtros, menú ⋮ contextual).
17. Manejo de expiración de sesión + re-login automático.
18. Fotos de producto con upload real (Fase 2 original).
19. Subida de cotizaciones a Drive para recuperarlas con fotos en cualquier equipo.

### DESEABLES
20. Buscador global Ctrl+K, breadcrumbs, acciones rápidas.
21. Multi-usuario con roles (dueño / operador / solo lectura).
22. Configuración de negocio completa (empresa, IVA, vigencia, prefijos de folio).
23. Exportación CSV/Excel de tablas.
24. Estadísticas reales (reemplazar Looker Studio o conectarlo bien).
25. Versión EN del panel.
26. Sincronización hoja→web (GitHub Actions).

## E. PLAN MAESTRO (fases propuestas)

| Fase | Nombre | Contenido | Entregable verificable |
|---|---|---|---|
| **0** | Cimientos del backend | LockService en folios/stock/ventas; try/catch global con `{ok,error}`; caché de Config; eliminación por ID; esquemas unificados; noindex admin; quitar credenciales del Log. Sin cambios visibles de UI. | Mismo panel, mismos datos, backend blindado. Playwright: regresión de login/cotizar/inventario/venta. |
| **1** | Inventario transaccional | Movimientos con anterior/posterior/tipo/documento/usuario; validaciones (no negativos); historial por producto; indicadores nuevos (sin precio/costo/foto, stock bajo, valor de inventario). | Recibir/ajustar material y ver el historial completo con existencias calculadas. |
| **2** | Compras | Proveedores + Órdenes de compra (estados BORRADOR→RECIBIDA, parciales) + PDF de OC + recepción que genera ENTRADA_COMPRA automática. | Crear OC 100 u → recibir 40 → recibir 60 → stock correcto y trazado a la OC. |
| **3** | Clientes + Cotizaciones conectadas | Módulo Clientes; lead→prospecto→cliente; unificar los 2 cotizadores en 1; estados de cotización (borrador/enviada/aprobada/vencida); cotización aprobada → crear proyecto. | Flujo completo: lead entra → cotizo → aprueban → proyecto creado sin recapturar datos. |
| **4** | Proyectos + Ventas 2.0 + Cobros | Proyectos con ficha financiera; ventas con folio VEN-AAAA-NNN, estados de pago, cobros parciales; cuentas por cobrar (cartera, vencida, próximos cobros). | Venta $100k → anticipo $30k → segundo $40k → saldo $30k visible en CXC. |
| **5** | Gastos 2.0 + Cuentas por pagar + Flujo de efectivo | Gasto vs pago; proveedor/proyecto/OC en gastos; CXP; flujo de efectivo día/semana/mes/año (cobros/pagos reales, no contables). | Responder "¿cuánto dinero REALMENTE entró y salió este mes?" |
| **6** | Finanzas completas | Estado de resultados real (bruta→operativa→neta, márgenes, filtros proyecto/rango), rentabilidad por proyecto (presupuesto vs real), alertas priorizadas. | P&L con márgenes y proyecto más rentable identificado. |
| **7** | Dashboard ejecutivo + rediseño visual | Sidebar agrupada (Resumen/Comercial/Operaciones/Finanzas/Marketing/Sistema), iconos Lucide SVG, sin emojis, modales propios, tablas profesionales, feedback de operaciones, formatos consistentes, responsive, Ctrl+K. | Panel con apariencia de software empresarial; todas las preguntas del punto 35 respondibles desde el inicio. |
| **8** | Cierre | ADMIN_ARCHITECTURE.md, pruebas integrales end-to-end, limpieza de código muerto, commit final. | Documentación + suite de pruebas. |

## F. PROPUESTA VISUAL (qué conservar / cambiar / simplificar / reorganizar)

**Conservar:** paleta negro grafito `#0d0d0d` + dorado `#C5A059` (identidad ADIS), tipografía Montserrat, variables CSS en `:root`, tarjetas `.card-box` con esquinas suaves, el papel blanco del preview del cotizador (contraste profesional ya probado).

**Cambiar:**
- Dorado de decoración → dorado de acento (botones primarios, selección, estados activos, detalles de borde). Superficies neutras grises; el 90% de la UI en blanco cálido/gris sobre oscuro, 10% dorado.
- Emojis → iconos **Lucide** (SVG inline, stroke 2, 24px base) con la misma familia en toda la UI.
- Tabs horizontales → **sidebar fija** (240px desktop, colapsable a 64px, drawer en tablet; bottom-nav simple en móvil con 5 destinos).
- `window.confirm` → modal de confirmación con icono de advertencia, texto de consecuencia ("Se desactivará el producto HJPVC-I01") y botones descriptivos (Desactivar / Conservar).
- Buscadores sueltos → tablas con toolbar (buscar + filtro + orden + paginación) y menú de acciones `⋮` por fila.

**Simplificar:**
- Unificar los **dos cotizadores** en uno solo (el profesional; el simple se elimina o queda como "cotización rápida" dentro del mismo flujo).
- Unificar las 3 implementaciones de "items de documento" (quoteItems/prop.items/saleItems) en un solo componente JS reutilizable.
- Reducir tabs de 10 a 6 grupos en sidebar; Estadísticas se absorbe en Flujo.

**Reorganizar:**
```
RESUMEN      → Dashboard ejecutivo
COMERCIAL    → Prospectos · Clientes · Cotizaciones · Proyectos · Ventas
OPERACIONES  → Inventario · Movimientos · Órdenes de compra · Proveedores
FINANZAS     → Cobros · Pagos · Flujo de efectivo · Resultados
MARKETING    → Reseñas · Analítica web
SISTEMA      → Configuración · Bitácora
```

## G. RIESGOS (qué podría afectar información existente)

| Cambio | Riesgo | Mitigación |
|---|---|---|
| LockService + rewrite de folios | Folio salta un número si el append falla tras incrementar | Incrementar el contador SOLO después de escribir la cotización (o reintentar). Aceptable un hueco; inaceptable un duplicado. |
| Movimientos con anterior/posterior | Los ~20 movimientos históricos no tienen anterior/posterior | Migración: recalcular existencia actual por producto/almacén y usarla como cierre de la era previa; nueva era trazada desde el deploy. |
| Eliminar por ID en vez de fila | Filas viejas sin ID | Migración asigna ID a filas existentes (una vez, con lock). |
| Unificar cotizadores | Cotizaciones "simple" guardadas no cargables en el nuevo | Mantener lectura legacy en el cargador durante 1 fase; luego congelar. |
| Nueva hoja Clientes/Proveedores | Duplicar leads existentes | Migración: leads actuales pasan a Prospectos con fecha; no se borra nada. |
| Re-deploy del script | URL cambia si se crea "nueva implementación" en vez de "nueva versión" | Rutina documentada: siempre ✏️ Nueva versión. URL está en 4 archivos → centralizar en 1 constante por archivo con comentario. |
| Cambio de encabezados de hojas | Romper importador y datos vivos | Nunca renombrar columnas existentes; solo agregar al final. Validación de esquema al inicio de cada handler. |
| products.json público | Exponer costos si se unifican fuentes | Mantener products.json SIN costos (público) y hoja Productos (privada). El cotizador consume la privada. |
| Pruebas Playwright | Contaminar datos reales | Backend simulado (como test_flujo_cotizador.py) o prefijo TEST- + limpieza posterior. |

## H. PRIMERA IMPLEMENTACIÓN RECOMENDADA

**Fase 0 — Cimientos del backend** (sin cambios visibles de interfaz), en este orden:

1. **`conLock()` helper** con `LockService.getScriptLock()` (wait 30s) envolviendo: folios, `aplicarMovimiento`, `venta` completa, `import_productos`, `cfgSet`.
2. **Try/catch global** en doGet/doPost: cualquier excepción → `{ok:false, error:'Error interno'}` JSON válido siempre.
3. **Caché de Config** por request (una sola lectura) + validación de `tipo_mov` contra lista blanca (ahora cualquier string raro actúa como "ajuste absoluto").
4. **Borrado por ID** en reseñas/gastos (el handler busca la fila por contenido, no confía en el índice del cliente).
5. **No stock negativo** sin confirmación explícita; movimientos guardan existencia anterior/posterior (columnas nuevas al final de Movimientos — no rompe esquema).
6. **noindex** en admin.html + quitar `ADMIN_USUARIO` del Log + validación de esquema de Cotizaciones en cada arranque.
7. Playwright de regresión: login → cotizar (folio) → inventario → venta con descuento de stock.

Por qué primero esto: todas las fases siguientes (OC, cobros, flujo) **dependen** de folios correctos, stock confiable y errores JSON predecibles. Construir finanzas sobre un backend sin locking sería deuda garantizada.

---

*Auditoría realizada sin modificar código. Próximo paso: aprobación del plan maestro → inicio de Fase 0.*


---

# ✅ RESULTADO DE IMPLEMENTACIÓN — FASE 0 (6 de septiembre de 2026)

> Aprobada por el dueño el mismo día. Se implementó exactamente el alcance aprobado.

## Cambios realizados

### Backend (`admin/apps-script.gs` — reescritura completa, 639 → ~780 líneas)

| # | Cambio | Causa arquitectónica corregida |
|---|---|---|
| 1 | `conLock()` con LockService en folios, stock, venta, movimiento, import, borrados | Concurrencia: folios duplicados, stock perdido, TOCTOU en ventas |
| 2 | `conErrores()` global en doGet/doPost + `AdisError` | Errores de Sheets devolvían HTML de Google, rompiendo el contrato JSON |
| 3 | Errores `{ok:false, error:{code,message}}` con códigos útiles (TOKEN_INVALIDO, STOCK_INSUFICIENTE, VALIDACION, NO_ENCONTRADO…) | Frontend no podía reaccionar a errores específicos |
| 4 | Config con caché por ejecución (`cfgMemo`), invalidación inmediata al escribir | N+1: Config se re-leía completa decenas de veces por request |
| 5 | `snapStock()` snapshot por ejecución; venta valida con snapshot agregado | N+1 en ventas (hoja Productos re-leída por item) y carreras entre items de la misma venta |
| 6 | `aplicarMovimiento()` única vía de cambio de existencia: id MOV-AAAA-NNNNN, usuario, existencia anterior/posterior, documento_tipo/documento_id | La existencia no era consecuencia de movimientos trazables (regla central) |
| 7 | Stock negativo = excepción STOCK_INSUFICIENTE (jamás persiste) | Existencias negativas sin aviso |
| 8 | `siguienteFolio()` bajo lock para ADIS (cotiz), VEN-0000 (ventas, nuevo), MOV-00000 (movimientos, nuevo); IDs UUID en Ventas/Gastos/Reseñas/Cotizaciones | Folios duplicados bajo concurrencia; dependencia de índices de fila |
| 9 | `filaPorId()` + borrado por ID estable en reseñas/gastos (respaldo temporal `row` para compatibilidad) | Borrados por `i+2` podían borrar la fila equivocada |
| 10 | Venta: validación completa pre-escritura + **compensación best-effort** (reversión COMPENSACION documentada) | Operación multi-hoja sin atomicidad dejaba stock descontado sin venta |
| 11 | Track: rate-limit 120/10min por huella + dedup 45s + **archivo** Visitas_Archivo en vez de borrar | Bots podían destruir el historial saturando las 5000 filas |
| 12 | Login: 5 intentos/10min; `logout` revoca token; usuario admin fuera del Log | Sin brute-force protection, sesiones acumuladas, credenciales en bitácora |
| 13 | `hoja()` garantiza esquema (corrige extensión condicional de Cotizaciones); HOJAS_BORRABLES sin Ventas/Movimientos | Esquema silenciosamente desalineado; historico financiero borrable |
| 14 | Validaciones: tipo_mov lista blanca, moneda contra MONEDAS, fechas YYYY-MM-DD, cantidades > 0, review 1–5 estrellas, gasto > 0 | Strings arbitrarios actuaban como "ajuste absoluto"; NaN silencioso a 0; fechas sueltas rompían filtros |

**Decisión documentada**: el contrato de éxito sigue plano (`{ok, ...campos}`)
por compatibilidad con las 17 integraciones del frontend; la migración al
envelope `{ok, data, error}` se hace en la Fase 7 (rediseño). Los errores ya
llevan `{code, message}`.

### Frontend (`admin/index.html`, 10 parches mínimos — sin cambios visuales)

1. `errMsg()` — interpreta error string (backend viejo) u objeto `{code,message}` (nuevo).
2. `manejarSesion()` — token inválido/expirado → aviso y regreso a login automático.
3. `logout()` revoca el token en el servidor (best-effort).
4. Login, cotizador, ajuste de inventario, venta y P&L muestran el mensaje de error real del backend.
5. Reseñas y gastos envían **ID estable + fila** (el nuevo backend usa ID; el viejo sigue usando fila — funciona con ambos durante la ventana de transición).
6. Mensaje de venta exitosa muestra el folio VEN- cuando el backend nuevo lo devuelve.

`noindex` ya existía (verificado en admin y en public/admin.html).

## Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| `node --check` backend (.gs) | ✅ Sintaxis OK |
| `node --check` frontend (949 líneas JS extraídas) | ✅ Sintaxis OK |
| `test_fase0_api.py` contra backend vivo | ✅ 5/5 conectividad/auth; detector confirma "backend viejo" y omite pruebas nuevas correctamente |
| `test_fase0_regresion.py` (Playwright, HTTP local) | ✅ 13/13 PASS, 0 errores JS — login, 10 pestañas, logout |

**Pendiente (requiere redeploy del script por el dueño)**: suite completa
Fase 0 — concurrencia de ventas (2×7 sobre stock 10 ⇒ 1 ok + 1 STOCK_INSUFICIENTE,
stock final 3), folios concurrentes distintos, trazabilidad de movimientos,
13 códigos de error. El suite (`scripts/auditoria/test_fase0_api.py`) está listo
y auto-detecta cuándo el backend nuevo está vivo.

## Riesgos residuales (documentados, aceptados o diferidos)

- Hueco en numeración de folio si falla la escritura tras reservar (aceptado: mejor que duplicado).
- Compensación de venta es best-effort; si también falla queda marca en Log (límite real de Sheets, documentado en ADMIN_ARCHITECTURE.md §7).
- Rate-limit del track es por huella UA|idioma|ancho (Apps Script no expone IP); un atacante distribuido con UAs distintos no se bloquea por completo (mitigado por dedup + archivo).
- Credenciales siguen en constantes del script y en el repo (rotación pendiente del dueño; instrucciones abajo).
- Movimientos históricos (era pre-Fase-0) no tienen anterior/posterior/id: cierre de era, nueva era trazada desde el deploy.
- `delete_gasto` sigue siendo borrado físico (se evalúa CANCELAR en Fase 5 — gasto vs pago).

## Qué debe hacer el administrador (manual, en este orden)

1. **Rotar credenciales**: en Apps Script cambia `ADMIN_CLAVE` (y opcionalmente `ADMIN_USUARIO`) por una clave nueva y fuerte; Guardar. La clave actual estuvo expuesta en el repositorio. Avisar para actualizar la copia local en el mismo commit del redeploy.
2. **Redeploy**: Implementar → Administrar implementaciones → ✏️ (lápiz) → **Nueva versión** → Implementar. Verificar que la URL `/exec` **no cambió**.
3. **Avisarme** para ejecutar `python scripts/auditoria/test_fase0_api.py` y verificar la suite completa en vivo.
4. No es necesario tocar la hoja: el esquema se migra solo (columnas nuevas al final) en el primer uso de cada pestaña.

## Recomendación para Fase 1 (inventario transaccional — ya con base sólida)

- Historial por producto en el frontend (filtrar Movimientos por producto_id).
- Indicadores nuevos: sin precio, sin costo, sin fotografía, stock bajo, valor de inventario.
- Edición en lote de precios/márgenes y cálculo de margen sugerido.
- Subida real de fotos (Fase 2 original) puede adelantarse aquí si se desea.
