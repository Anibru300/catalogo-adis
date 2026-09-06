# Resumen de sesión — 2026-09-06 (Plan Maestro 8 fases)

## Estado: Fases 0–7 COMPLETAS y pusheadas. Fase 8 (cierre) = este documento + pruebas.

| Fase | Commit | Contenido |
|---|---|---|
| 0 | e45c834 | Cimientos backend: lock, errores JSON con códigos, inventario transaccional, folios concurrentes, compensación, login 5 intentos, logout revoca |
| 1 | a3c8f6b | Inventario: movimientos filtrables, update_precios por lote, dashboard de salud, panel ±Movimiento |
| 2 | 036c37a | Compras: Proveedores + OC con estados y recepción parcial trazable (ENTRADA_COMPRA) |
| 3 | c662cf5 | Clientes + Cotizaciones: directorio, convertir lead, estados de cotización |
| 4 | 2174cba | Proyectos + Cobros/CxC + anulación de venta con repuesto de stock |
| 5 | 5918a45 | Gastos 2.0: gasto≠pago, hoja Pagos, folios GAS-/PAG-, cancelar en vez de borrar, CxP, flujo de efectivo real |
| 6 | 199617d | Finanzas: P&L por proyecto, utilidad operativa, alertas priorizadas, proyecto_mov (Proyectos_Movs) |
| 7 | b1af7aa | Rediseño: sidebar, dashboard Resumen, Ctrl+K, fin de confirm() |
| 8 | (este) | Cierre: docs, regresión 19/19, suite de tests API Fase 0–6 |

## Verificación
- `node --check` GS y JS extraído: OK tras cada fase.
- Regresión Playwright `test_fase0_regresion.py`: **19/19 PASS, 0 errores JS** (sirve `public/` en :8788).
- Tests API `scripts/auditoria/test_fase{0..6}_api.py`: escritos; auto-omiten comportamiento con el backend viejo hasta el redeploy.

## ⚠️ ÚNICO paso manual pendiente (el usuario): redeploy de Apps Script
1. script.google.com → abrir el proyecto del backend.
2. **Implementar → Administrar implementaciones → ✏️ (editar) → Nueva versión → Implementar.** NUNCA "nueva implementación" (cambiaría la URL).
3. Verificar que la URL `/exec` sigue igual.
4. Avisar para correr en vivo: `test_fase0_api.py` … `test_fase6_api.py` (concurrencia de ventas, folios, todos los códigos de error por fase).

## Notas operativas
- `folio_cotizacion` en Config quedó en 2 → la primera cotización real será ADIS-2026-003 (o resetear a 1 si se prefiere).
- Los datos de prueba de las suites API usan fechas 2020-0x y prefijo TEST: no contaminan reportes reales y son borrables por fecha si se desea.
- Lucide (iconos) quedó diferido por decisión documentada (Fase 7).
- Logo roto en login/PDF (`LOGO%20ADIS.webp` no existe en admin/): pendiente menor, no bloquea.
