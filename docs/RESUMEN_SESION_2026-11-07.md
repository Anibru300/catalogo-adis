# RESUMEN DE SESIÓN — 2026-11-07

> Etapa 2 (Compras/Inventario) **DESPLEGADA EN PRODUCCIÓN y verificada**:
> el gasto de mercancía ya puede entrar al stock ligado a su folio GAS-.
> Decisión del dueño: sin carga retroactiva de los 9 gastos de octubre;
> la disciplina ahora es capturar bien las compras futuras.

---

## 1. LO QUE SE DESPLEGÓ (commit `d62a47d`, autorizado)

### Backend (Apps Script — redeploy hecho por el dueño el 2026-11-07)
- **Nuevo endpoint `gasto_inventario`**: entrada a stock de un gasto EXISTENTE
  con `naturaleza=inventario`. Un `MOV-` de entrada por partida con
  `documento_tipo=GASTO`, `documento_id=<folio GAS->` y la **fecha original**
  del gasto (carga retroactiva posible). Idempotente: un folio solo admite una
  entrada. Actualiza el último costo del producto (col 8) y marca el gasto en
  las **cols 14/15 nuevas** (`entrada_inventario`, `items_json`).
- **`gasto` extendido**: acepta `items_inventario` + `almacen_id` (mismo lock,
  pre-validación todo-o-nada para no dejar gastos huérfanos).
- `aplicarMovimiento()` NO se tocó. Migración aditiva (cols al final).

### Panel admin (`public/admin.html` en línea)
- **Registrar gasto**: al elegir tipo "Compra de inventario" aparece la sección
  opcional **"📦 Entrar esta mercancía al inventario"** (almacén destino +
  filas producto/cantidad/costo con el selector de productos). El aviso de
  éxito indica "📦 mercancía en inventario".
- **Inventario → Movimientos**: origen "🧾 Gasto GAS-…" (tabla y CSV).
- Cuadro de ayuda del formulario actualizado.
- Ojo: los cambios viven en los **módulos fuente** (`07_GASTOS_PAGOS/admin/gastos.js`,
  `admin/plantilla.html`, `01_EXISTENCIAS/admin/existencias.js`); `admin/index.html`
  es artefacto ensamblado (`python 50_BUILD/build_admin.py`).

## 2. VERIFICACIÓN EN PRODUCCIÓN (2026-11-07, tras redeploy)
- `test_control_ie.py --api` → **9/9 PASS**; conciliación oct-2026 exacta:
  ingresos 42,490.00 · egresos 69,231.04 · neto −26,741.04.
- `test_fase01_api.py --post` → **20/24**; los 4 "fallos" son comparación contra
  snapshot viejo: el dueño ya había capturado 3 gastos reales (GAS-0057
  Compra de material $800 → inventario, GAS-0058 gasolina, GAS-0059 alimentos).
  Mismo patrón aceptado en el despliegue de Etapa 1. Ninguna regresión real.
- Endpoint `gasto_inventario` en vivo: id falso → NO_ENCONTRADO; gasto
  operativo → NO_PERMITIDO (guard correcto, sin escribir nada).
- Columnas 14/15 migradas aditivamente en la hoja Gastos de producción.
- Los 10 gastos con naturaleza=inventario siguen SIN entrada (limpio).
- Sandbox Node: **28/28 PASS** (Etapa 2) + **40/40 PASS** (regresión Etapa 1).
  La entrada de stock no mueve dinero (control_ie intacto).

## 3. DECISIÓN DEL DUEÑO — sin carga retroactiva
- Los 9 gastos de oct-2026 (~$40k de mercancía) **NO** entrarán al stock de
  forma retroactiva. De hoy en adelante las compras se capturan bien
  (producto/piezas/costo) con el nuevo flujo.
- Plan y script quedan como referencia: `60_DATA/plan_entrada_inventario_fase2.json`
  + `scripts/auditoria/entrada_inventario_fase2.py` (dry-run; bloqueado en
  producción sin `ADIS_ENTRADA_INV_PROD=si`).

## 4. RESPALDOS Y REVERSIÓN
- `backups/apps_script_pre_etapa2_20261107.gs` · `backups/admin_index_pre_etapa2_20261107.html`
  · `backups/admin_public_pre_etapa2_20261107.html`.
- Reversión: repegar el .gs → Nueva versión; resubir el HTML respaldado.

## 5. PENDIENTES MENORES (heredados)
1. Rotar `ADMIN_CLAVE` (expuesta en el repo).
2. Catálogo duplicado (`public/catalogos/` vs hoja Productos).
3. Retirar viejas categorías de transición (flag `--quitar-viejas`).
4. GAS-2026-0025 ($1, clasificado retiro) — sin impacto.

## Commits de la jornada
`d62a47d` Etapa 2 completa: backend + panel + sandbox 28/28 + respaldos + docs.
`fc13d89` Fix cotizador (IVA con/sin, fotos 1→3 proyecto / 12 producto, re-guardar
edita en vez de duplicar) + PDF revisado visualmente.
`8df02b0` Paginación PDF: cada foto viaja con su leyenda (nada partido/encimado).
`daf8877` Auditoría minuciosa: fix placeholders de fotos (B1), utilidad sin IVA (B2),
validación imprimir/WhatsApp (B3) + limpieza de 7 duplicados históricos en
producción (respaldo 60_DATA/respaldo_cotizaciones_duplicadas_2026-11-07.json).
`10d72cb` Cierre de auditoría BAJA (B4-B10): colspan, 404 login, debounce cliente,
waNum, paginación/logo PDF, impresión foto-a-foto. Suite 24/24 PASS.

## 6. CIERRE DE JORNADA (verificación final 2026-11-07)
- Sandbox: Etapa 1 **40/40** · Etapa 2 **28/28** · cotizador **11/11** PASS.
- Producción: `control_ie` **9/9** (conciliación oct-2026 exacta) · suite panel
  Playwright **24/24 PASS, 0 errores JS** · PDF verificado visualmente.
- Repo: sin cambios pendientes, todo commiteado y pusheado a `main`.
- Historial de cotizaciones: 5 folios únicos, 0 duplicados, estados correctos.
