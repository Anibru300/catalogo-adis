# Backend modular (Apps Script) — estado M5

## Archivos fuente
| Archivo | Contenido |
|---|---|
| `00_CORE/backend/core.gs` | Constantes (SHEET_*, ENC_*, credenciales, HOJAS_BORRABLES), helpers (json, conErrores, conLock, hoja, cfg, folios, aBase, snapStock, **aplicarMovimiento**, filaPorId, log_), auth (tokens) y los dispatchers `doGetInterno`/`doPostInterno` con los handlers inline. |
| `09_MARKETING/backend/analitica.gs` | `trackProtegido` (rate-limit, dedup, archivo) + clasificadores `origenDe_`/`dispositivoDe_`/`navegadorDe_`. |

## Por qué los handlers siguen en core.gs
Los handlers están **inline** dentro de los dispatchers. Moverlos exige refactor
de lógica (prohibido en la fase M: solo extracción). Se hará junto con la
migración al envelope `{ok,data,error}` (rediseño de API), no antes.

## Mapa de handlers inline por módulo (líneas de core.gs)
| Módulo | Handlers (tipo POST) / actions (GET) |
|---|---|
| 01_EXISTENCIAS | save_product, update_precios, delete_product, restore_product, import_productos, save_almacen, delete_almacen, movimiento · GET productos/almacenes/stock/movimientos |
| 02_COMPRAS | save_proveedor, delete_proveedor, save_oc, cambiar_estado_oc, recibir_oc · GET proveedores/oc |
| 03_COMERCIAL | lead (público), save_cliente, delete_cliente · GET leads/clientes |
| 04_COTIZADOR | quote, set_estado_quote, crear_proyecto_desde_cotizacion · GET quotes |
| 05_PROYECTOS | save_proyecto, proyecto_mov, cambiar_estado_proyecto · GET proyectos |
| 06_VENTAS_COBROS | venta, registrar_cobro, anular_venta · GET ventas/cxc |
| 07_GASTOS_PAGOS | gasto, gasto_pago/registrar_pago, gasto_cancelar, delete_gasto · GET gastos/pagos/cxp |
| 08_RESULTADOS | (solo lectura) · GET estado_resultados/flujo_caja/alertas |
| 09_MARKETING | review, delete_review · GET reviews/reviews_admin/visitas · track (público, en analitica.gs) |
| 11_SISTEMA | config, delete_row, admin_purge |
| 00_CORE | login, logout, me |

## Despliegue (sin cambios)
`python 50_BUILD/concat_backend.py` regenera `admin/apps-script.gs` (concatenación
en orden). El dueño sigue pegando **ese archivo** en Apps Script e implementando
✏️ Nueva versión. Validar sintaxis: `node --check admin/apps-script.gs`.
