# Resumen de sesión — 2026-09-07

## Contexto

Mejoras al apartado de **Inventario** del panel admin (`admin/index.html` → `public/admin.html`),
centradas en la **entrada y salida de material**, con 4 pedidos del usuario: formulario más
completo, salida por proyecto/obra, multi-producto por operación y mejor historial.

## Cambios en backend (`admin/apps-script.gs`)

- **`ENC_MOV`** crece 2 columnas al final (migración aditiva automática): `proveedor` y `lote`.
- **Handler `tipo:'movimiento'`** reescrito (retrocompatible con el payload simple anterior):
  - Acepta `fecha` (AAAA-MM-DD, validada con `validarFecha`, no futura), `referencia`,
    `proveedor`, `moneda`, `costo_unit` y `proyecto_id`.
  - **Lote multi-producto**: `items:[{producto_id, cantidad, costo_unit?}]` (máx. 100, no en
    ajuste). Pre-validación completa antes de escribir; para salidas verifica el stock TOTAL
    por producto+almacén → el lote es **todo-o-nada** (STOCK_INSUFICIENTE sin mover nada).
    Folio `LOTE-AAAA-NNNN` (nuevo contador `folio_lote`, incluido en la purga).
  - **Documento origen con prioridad**: `PROYECTO` (si viene `proyecto_id`, validado con
    `filaPorId`) > `LOTE` > `AJUSTE`. El folio de lote siempre va en la columna `lote` de cada
    movimiento, así un lote ligado a proyecto agrupa igual.
  - **Entrada con costo actualiza el último costo del producto** (columna 8 + fecha col 16,
    igual que la recepción de OC).
  - Devuelve `{ok, stock_nuevo:{producto_id:cant}, lote}`.
- **`doGet action='movimientos'`**: filtros opcionales `desde`, `hasta`, `tipo`, `almacen_id`
  (con cualquier filtro devuelve hasta 500; sin filtros sigue últimos 100).
- Sintaxis GS validada con `node --check`.

## Cambios en frontend (`admin/index.html`)

- **Formulario unificado `showMovForm(tipo)`** para Entrada/Salida (menú lateral):
  fecha (default hoy, max hoy), almacén, **proveedor + factura/remisión** (solo entrada),
  **proyecto/obra** (solo salida, proyectos ACTIVOS), moneda, notas y **tabla de items
  multi-producto** (buscador con stock visible, cantidad, costo unitario en entrada, quitar
  fila, totales de piezas y costo). El **ajuste** conserva el formulario simple de 1 producto.
- **Movimientos recientes**: barra de filtros (desde/hasta/tipo/almacén/buscar texto),
  columnas nuevas (Documento resuelve LOTE/Proyecto/OC, Ref/Proveedor), botones **⬇ CSV**
  (BOM UTF-8, abre en Excel) y **🖨 Imprimir** (ventana limpia).
- `renderMovs` ahora filtra en cliente sobre `movsCache`; `loadProductHistory` muestra
  referencia y documento.

## Pruebas

- **Nuevo** `scripts/auditoria/test_movimientos_ui.py` (Playwright + backend simulado):
  **21/21 PASS, 0 errores JS** — entrada lote 2 items con costo/proveedor/referencia/fecha,
  salida con proyecto, filtros, CSV e impresión; valida los payloads enviados.
- **Nuevo** `scripts/auditoria/test_movimientos_lote_api.py` (API en vivo, auto-detecta
  backend nuevo; hoy omite con mensaje porque aún no se redepliega).
- Regresión `test_fase0_regresion.py` contra backend vivo: **19/19 PASS, 0 errores JS**
  (frontend retrocompatible).
- Verificación visual: `screenshots/check_mov_form_entrada.png`, `check_mov_historial.png`.

## Verificación EN VIVO (backend redeployado el 2026-09-07 noche)

- `scripts/auditoria/test_movimientos_lote_api.py` contra el backend real: **19/19 PASS**
  - Entrada lote 2 items → folio `LOTE-2026-0001`, stock correcto, costos actualizados (11 y 6)
  - Movimientos del lote traen lote/proveedor/referencia/fecha pasada y existencia anterior→posterior
  - Filtros del historial (tipo / desde-hasta / almacén) funcionan
  - Validaciones: fecha futura, ajuste con items, proyecto inexistente, salida que excede (stock intacto, todo-o-nada)
  - Salida vinculada a proyecto → `documento_tipo=PROYECTO`; lote parcial OK
  - Limpieza: stock de prueba retirado y productos TEST-LOTE-A/B eliminados (quedan inactivos).
    Sus filas de movimiento quedan en la bitácora por diseño (los movimientos jamás se borran).
- Nota: hay huecos en la numeración de lotes (0001 → 0004): el folio se reserva antes de la
  pre-validación de stock (decisión documentada: huecos aceptables, duplicados imposibles).
- Regresión `test_fase0_regresion.py` contra backend viejo: **19/19 PASS, 0 errores JS**
  (el frontend retrocompatible funcionó todo el día hasta el redeploy).
- Verificación visual: `screenshots/check_mov_form_entrada.png`, `check_mov_historial.png`.

## ✅ Hecho por el dueño (2026-09-07 noche)

1. ✅ Backend redeplegado con **✅ Nueva versión** (misma URL `/exec`).
2. ✅ Suite API en vivo corrida y aprobada (19/19).
3. **Pendiente**: `git add -A && git commit && git push origin main` para publicar
   `public/admin.html` con el panel nuevo (el admin en línea sigue siendo el viejo hasta el push).

## Lecciones técnicas (no repetir)

1. OJO con búsquedas en tests: `lambrin` no coincide con `Lambrín` (acentos); y `pvc` coincide
   con TODOS los códigos `HJPVC-*`. Usar términos sin acento y únicos (`wpc`, `placa`).
2. Los `<details class="mgroup">` del menú se cierran durante la navegación del test: reabrir
   con evaluate antes de cada click a pestañas del menú lateral.
3. Al esperar options de un `<select>` cerrado usar `state='attached'` (visible da timeout).
4. Un mock de backend por rutas debe devolver las claves exactas que el frontend espera
   (`ventas`, no `ventass`) o `renderSales`/`renderExpenses` explotan en el navegador.

## Pendientes para próximas sesiones

- Probar entrada/salida de material real en vivo tras el redeploy (folio LOTE-2026-0001)
- Logo roto en login/PDF (`LOGO%20AD.webp/.png`) — pendiente menor heredado
- Otras fases del Plan Maestro pendientes según auditoría
