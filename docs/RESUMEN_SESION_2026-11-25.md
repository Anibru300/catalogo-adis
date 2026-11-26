# RESUMEN DE SESIÓN — 2026-11-25

> Jornada triple: **compra Teknostep registrada (factura 28024799)**,
> **módulo de Traspasos entre almacenes desplegado** (multi-producto, atómico,
> folio TRA-) y **Kardex por producto** con proveedor en movimientos.
> Todo commiteado y pusheado (`e2a1cb0` traspasos + `eff2c3a` reintento
> deploy Pages + cierre del día con kardex).

---

## 1. COMPRA TEKNOSTEP — FACTURA 28024799 (commit `e2a1cb0`)

- **Registrada vía script one-off** `60_DATA/registrar_compra_teknostep_28024799.py`
  (dry-run + `--aplicar`, con pre-chequeo anti-duplicados por factura).
- **Gasto `GAS-2026-0060`** — categoría "Compra de mercancía", naturaleza
  inventario, **$3,460.88 MXN** (subtotal $2,983.52 + IVA $477.36), descripción
  con factura. **Pago `PAG-2026-0053`** total, tarjeta de débito (PUE).
- **Entradas a Nogales** (doc GASTO trazado): LAM-015 Río +14 @ $99.57 (c/IVA),
  LAM-005 Brasilia +14 @ $99.57, y productos nuevos **LAM-040 Ángulo Río** y
  **LAM-041 Ángulo Brasilia** (5 pzas c/u @ $67.28, claves prov. en notas).
- Corrección del dueño aplicada: las 2 cajas de lambrín "1 caja = 14 pzas"
  (6.496 m² caja); ángulos 5 pzas c/u (14.5 m.l.). Verificado contra el PDF.
- Stock resultante Nogales: Río 14, Brasilia 14, ángulos 5+5. Costos con IVA
  (IVA no acreditable RESICO ⇒ costo real). Factura PDF en
  `Archivos de Inventario/FACTURA No. 28024799.pdf`.

## 2. MÓDULO DE TRASPASOS ENTRE ALMACENES (commit `e2a1cb0`)

### Backend (`00_CORE/backend/core.gs`)
- Nuevo endpoint **`traspaso`**: `{almacen_origen_id, almacen_destino_id,
  fecha?, notas?, items:[{producto_id, cantidad}]}`. Bajo UN `conLock`:
  pre-validación todo-o-nada en origen (STOCK_INSUFICIENTE antes de escribir
  nada), folio **`TRA-AAAA-NNNN`** (`folio_traspaso`, se autocrea en Config),
  par salida+entrada por partida con `doc_tipo=TRASPASO` y doc_id compartido,
  **compensación inversa** si falla a mitad (patrón VENTA), alertas de stock
  bajo. NO cambia costos. Respuesta `{ok, folio, stock_nuevo, alertas}`.
- `folio_traspaso` agregado a la lista del purge. `admin/apps-script.gs`
  regenerado con `50_BUILD/concat_backend.py`. Sin cambios de esquema.

### Frontend (`01_EXISTENCIAS/admin/existencias.js` + `plantilla.html`)
- Botón **"⇄ Traspaso"** en toolbar de Inventario → formulario multi-producto:
  origen/destino (auto-distintos), fecha (retroactiva OK, futura no), buscador
  que solo lista productos **con existencia en el origen** (muestra
  disponible), validación por fila (borde rojo + "insuficiente"), 1 solo POST.
- Traslado rápido por **chip de almacén** re-enrutado al endpoint nuevo
  (antes: 2 POSTs no atómicos).
- Historial/CSV/imprimir: `doc_tipo=TRASPASO` se muestra **🔀 TRA-…**
  (`movDocTxt`/`movCSV`).

### Pruebas (todas en verde)
- `test_traspaso_api.py` **22/22 en producción** (TRA-2026-0002/0003 reales,
  todo-o-nada verificado, limpieza total con almacenes TEST aislados).
- `test_traspaso_ui.py` **20/20** (backend simulado).
- Regresión: `test_movimientos_ui.py` **21/21** (reparada: selectores del
  renombrado de menús 2026-10-25 — estaba rota desde entonces),
  `test_movimientos_lote_api.py` **19/19**, `test_fase1_api.py` **11/11**,
  `test_fase0_regresion.py` **19/19**.

## 3. KARDEX POR PRODUCTO + PROVEEDOR EN MOVIMIENTOS (cierre del día)

### Qué pidió el dueño
Ver el kardex de un producto con entradas tipo **"+14 por compra de material,
factura tal, del proveedor tal"**. El historial por producto existía pero era
pobre (5 columnas, últimos 30, sin proveedor propio, a 300px de ancho).

### Backend (`core.gs`)
- `aplicarEntradaInvGasto` acepta **5to param `proveedor`** (desde `gasto` y
  `gasto_inventario`) que queda en la **columna proveedor de cada MOVIMIENTO
  de entrada** (ENC_MOV ya tenía la columna — cero migración).
- ⚠️ **FALTA REDEPLOY del backend con este cambio** (ver pendientes).

### Frontend
- **Kardex a ancho completo** (nuevo `#invKardex` entre la tabla y
  "Movimientos recientes"; se libera la barra lateral que queda compacta con
  foto/datos/editar). Título "📒 Kardex: código · nombre", filtros
  **desde/hasta/tipo**, contador "N de M movimiento(s)", botones **⬇ CSV** y
  **🖨 Imprimir** del kardex filtrado.
- Cantidades **con signo coloreado**: **+14** 🟢 entrada, **−2** 🔴 salida,
  `=N` ajuste. Columnas: Fecha, Tipo, Almacén, Cant., Existencia (ant→post),
  Documento (🧾/🔀/OC/Lote/🏗), **Proveedor**, Notas (completa en tooltip).
- **Campo "Proveedor (opcional)"** en Registrar gasto (`gProveedor`) → se
  envía con el POST y cae al kardex. Limpieza del formulario incluida.

### Pruebas
- `test_kardex_ui.py` **12/12** (signos, proveedor Teknostep, filtros, CSV,
  payload del gasto). `test_traspaso_ui.py` 20/20, `test_movimientos_ui.py`
  21/21, `test_fase0_regresion.py` 19/19 tras el rediseño.
- `test_gasto_proveedor_api.py` lista; **queda correrla en vivo tras el
  redeploy** (hoy dio 6/7 con el único FAIL = proveedor vacío por backend
  viejo; limpieza OK).

### Diseño verificado con capturas (`screenshots/kardex_check_*.png`)
Kardex full-width bien distribuido (el sidebar de 300px cortaba las 8
columnas — por eso se movió). Form de traspaso y de gasto revisados.

## 4. INFRA / COMMITS
- `e2a1cb0` — traspasos + compra Teknostep + tests + docs.
- `eff2c3a` — commit vacío: reintento de deploy Pages (el step deploy-pages
  falló transitorio 2 veces; el reintento pasó). **Ojo: si vuelve a fallar,
  Re-run failed jobs en la pestaña Actions.**
- Docs actualizados: `01_EXISTENCIAS/CONTEXTO.md` (traspaso API/regla/UI,
  kardex, pruebas), `07_GASTOS_PAGOS/CONTEXTO.md` (gasto.proveedor),
  `00_CORE/CONTEXTO_GLOBAL.md` §7 (folio TRA-).

## 5. PENDIENTES PARA MAÑANA (2026-11-26)
1. **Redeploy backend** en Apps Script con el `admin/apps-script.gs` actual
   (2,923 líneas — incluye proveedor en movimientos). 2 min. Luego correr
   `python scripts/auditoria/test_gasto_proveedor_api.py` → debe dar 7/7.
2. **Backfill opcional**: las 4 entradas de hoy (GAS-2026-0060) tienen la
   columna proveedor vacía (Teknostep va en notas). Si se quiere la columna
   llena, script one-off en Apps Script; pedirlo y se genera.
3. Heredados de ayer: rotar `ADMIN_CLAVE` 🔴 (sigue expuesta en el repo),
   catálogo duplicado (public/catalogos vs hoja Productos), retirar viejas
   categorías de transición (--quitar-viejas), fotos de cotizaciones solo en
   navegador creador.
4. Idea anotada por el dueño: datalist de proveedores en el campo Proveedor
   (sugerir los del directorio) — el campo es texto libre por ahora.

## Commits de la jornada
`e2a1cb0` Inventario: modulo de traspasos entre almacenes (+ compra Teknostep)
`eff2c3a` ci: reintento de deploy Pages
(+ commit de cierre: kardex + proveedor + tests + resumen)
