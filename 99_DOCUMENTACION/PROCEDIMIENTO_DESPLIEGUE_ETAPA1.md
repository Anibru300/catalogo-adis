# PROCEDIMIENTO SEGURO — DESPLIEGUE ETAPA 1 FINANCIERA

> Fecha: 2026-11-06 · Estado: **PREPARADO — esperando autorización expresa del propietario**
> Alcance: Fase 0 + Fase 1 + ajustes Etapa 1 (commits `a11c8cc`, `598ef4d`, `2f44d59`)
> Regla de oro: **ningún paso de prueba escribe en producción.**

---

## 1. Estado de respaldos (verificado 2026-11-06)

| Respaldo | Ubicación | Estado |
|---|---|---|
| Código fuente completo | git (commits `47ce9fa`→`2f44d59`) | ✅ recuperable (`git revert` / `git checkout`) |
| Script de producción previo | `backups/apps_script_pre_fase01_20261106.gs` (129,620 B) | ✅ copia física del desplegado |
| Panel admin previo | `backups/admin_index_pre_fase01_20261106.html` (306,744 B) | ✅ copia física |
| Datos: 17 JSON (gastos, pagos, cobros, cxc/cxp, stock, productos, config, proyectos, ventas, oc, P&L, flujo, finanzas mensual) | `60_DATA/auditoria_2026-11-06/` (commit `47ce9fa`) | ✅ verificados, parsean OK |
| Conciliación oct-2026 por folio | impresa en sesión + reproducible con `test_control_ie.py` | ✅ |

**Limitación honesta**: los JSON son referencia de auditoría/restauración parcial
(no vuelcan datos de regreso a Sheets por sí solos). El respaldo integral de la
hoja lo da el paso 2 (la copia de prueba **es** un respaldo completo de la
hoja) y el historial de versiones nativo de Google Sheets (Archivo → Historial
de versiones).

---

## 2. ENTORNO AISLADO (viable — recomendado antes de tocar producción)

La copia de Google Sheets incluye el proyecto de Apps Script ligado, así que el
entorno de prueba es una réplica total y **la prueba de escritura es segura**.

### 2.1 Crear la copia (5 min, sin riesgo)
1. Abre la hoja de producción en Google Sheets.
2. **Archivo → Hacer una copia** (queda en tu Drive, p. ej. `ADIS PRUEBA Etapa1`).
   - La copia trae todas las hojas (21) **y el script ligado**.
3. Abre la copia → **Extensiones → Apps Script**. Verás el código anterior.
4. Pega el contenido de `admin/apps-script.gs` (regenerado, 2 702 líneas) sobre
   el código del editor de la **copia**.
5. **Implementar → Nueva implementación** → tipo **Aplicación web**:
   - Ejecutar como: *Yo* · Quién tiene acceso: *Cualquier persona* (igual que prod).
6. Copia la URL `/exec` nueva (es distinta a la de producción).

### 2.2 Probar contra la copia (todo automatizado, solo escritura en la copia)
```bash
export ADIS_API_URL="https://script.google.com/macros/s/<ID_DE_LA_COPIA>/exec"

# A) Escritura (ciclo completo: gasto+pago, clasificar, ingreso+edicion)
python scripts/auditoria/test_escritura_aislada.py

# B) control_ie vs conciliacion oct-2026 (42,490 / 69,231.04 / -26,741.04)
python scripts/auditoria/test_control_ie.py --api

# C) Regresion completa (campos nuevos, protecciones, sin doble conteo)
python scripts/auditoria/test_fase01_api.py --post
```
Resultado esperado: **A) 10/10 · B) 9/9 · C) ~20/20 PASS.**
La columna `naturaleza` se crea sola (al final de la hoja Gastos) en el primer
`GET gastos` de la copia. Verifícalo visualmente en la copia.

### 2.3 Limpieza (opcional)
La copia puede conservarse como respaldo en frío o eliminarse tras el despliegue
exitoso. Producción jamás se tocó en estos pasos.

---

## 3. DESPLIEGUE A PRODUCCIÓN (solo tras autorización expresa)

1. **Ventana corta** (el panel sigue usable; el único cambio inmediato es la
   columna nueva al primer acceso post-redeploy).
2. Apps Script de **producción**: reemplazar todo el código por
   `admin/apps-script.gs` → **Implementar → Administrar implementaciones →
   editar → Nueva versión** (mismo URL `/exec`, sin cambiar nada más).
3. Subir `admin/index.html` (regenerado) a `public/admin.html` (flujo habitual).
4. **No reclasificar nada.** Los 31 folios siguen sin autorización.

### Cambio estructural que ocurrirá (el único, aditivo y reversible)
- Al primer `GET/POST` que toque la hoja Gastos, el guard `hoja()` agrega la
  columna `naturaleza` **al final, vacía**. No renombra, no reordena, no toca
  filas ni folios. Todos los históricos quedan `por_clasificar` (default seguro).

---

## 4. REVERSIÓN (si algo falla)

| Síntoma | Acción |
|---|---|
| Error de sintaxis/no responde el API | Repegar `backups/apps_script_pre_fase01_20261106.gs` → nueva versión. Panel: resubir `backups/admin_index_pre_fase01_20261106.html`. Vuelve todo al estado previo. |
| La columna `naturaleza` ya fue creada | **No requiere acción**: es inofensiva vacía; el código viejo la ignora. Si se desea, bórrala manualmente de la hoja. |
| Datos históricos alterados (no esperado) | Los JSON de `60_DATA/auditoria_2026-11-06/` + historial de versiones de Sheets permiten restaurar/auditar fila por fila. El código nuevo no modifica filas históricas por sí solo (solo lectura en reportes; escritura solo en altas/edición explícitas y en `gasto_clasificar`, que está bloqueado). |
| Reversión de código local | `git revert 2f44d59 598ef4d a11c8cc` |

---

## 5. LISTA DE VERIFICACIÓN POST-DESPLIEGUE

### Automática (ejecutar inmediatamente tras el redeploy)
- [ ] `python scripts/auditoria/test_fase01_api.py --post` → 0 fallos
- [ ] `python scripts/auditoria/test_control_ie.py --api` → conciliación oct-2026 exacta
- [ ] **Fix último día del mes**: `estado_resultados&mes=2026-10` → ingresos **42,490.00** (antes 38,790)

### Visual (panel admin, 5 min)
- [ ] Tab **Control de Ingresos y Egresos** visible en menú Dinero; KPIs cargan
- [ ] **Simulador**: modificar un importe recalcula neto en vivo; nota "No representa la utilidad contable" visible
- [ ] Filtros: poner naturaleza="Retiros" → KPIs/generales **no cambian**; la nota indica "Detalle filtrado"
- [ ] P&L: título "PROVISIONAL", sin margen 100%, "Resultado provisional del periodo"
- [ ] Flujo de caja: por actividad (Operación/Inversión/Financiamiento) presente
- [ ] **Formularios**: registrar UN ingreso y UN gasto reales del día (operación normal, no prueba) y verlos reflejados en Control I/E
- [ ] **Retiros**: vacío hasta reclasificar (correcto); la sección no rompe
- [ ] Inventario, cotizador, ventas, proyectos: sin cambios (smoke visual rápido)

### Seguridad
- [ ] Bitácora (`logs`) sin errores nuevos; doble log de ingreso eliminado
- [ ] `delete_row` sobre Gastos responde NO_PERMITIDO
- [ ] `reclasificar_fase1.py` (sin --aplicar) sigue en dry-run → **no ejecutar --aplicar sin autorización**

---

## 6. RESTRICCIONES VIGENTES

- ❌ Prohibido generar gastos/ingresos de prueba **en producción** (los $1 de
  prueba existentes son históricos de oct-2025). Toda escritura de prueba: copia.
- ❌ Reclasificación de los 31 folios: **sin autorizar**. El script exige
  `ADIS_RECLASIFICAR_PROD=si` en producción aunque se fuerce.
- ❌ Sin avances de Etapas 2–4 hasta nueva autorización.
- ⚠️ Entorno aislado: no es viable crearlo 100% programáticamente (la copia de
  Sheets exige acción manual en la UI de Google); el procedimiento 2.1 es el
  camino más seguro y tarda ~5 minutos.
