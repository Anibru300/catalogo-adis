// Harness Node.js — ejecuta el core.gs REAL de Etapa 1 contra un emulador de
// Google Sheets cargado con el snapshot de produccion (60_DATA/auditoria_2026-11-06).
// SOLO LECTURA del snapshot: el "libro" es una estructura en memoria.
// Valida: control_ie (conciliacion oct-2026), creacion de columna naturaleza,
// P&L provisional + fix ultimo dia del mes, flujo por_actividad, retiros,
// filtros generales vs filtrados, proteccion delete_row, preservacion de TC
// historico en ediciones, y reclasificacion de prueba (solo en memoria).
//
// Uso:  node scripts/auditoria/harness_node/run_etapa1.js
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const SNAP = path.join(ROOT, '60_DATA', 'auditoria_2026-11-06');
const load = f => JSON.parse(fs.readFileSync(path.join(SNAP, f), 'utf8'));

/* ---------------- Emulador de Google Sheets ---------------- */
function makeSheet(nombre, headers, rows) {
  const grid = [headers.slice()];
  (rows || []).forEach(r => grid.push(headers.map(h => (r[h] !== undefined && r[h] !== null) ? r[h] : '')));
  const norm = (v) => (v === undefined || v === null) ? '' : v;
  const cell = (r, c) => ({
    getValue: () => grid[r - 1][c - 1],
    setValue: (v) => {
      while (grid[r - 1].length < c) grid[r - 1].push('');
      grid[r - 1][c - 1] = v;
    },
    setNumberFormat: () => cell(r, c),
  });
  return {
    nombre,
    getLastRow: () => grid.length,
    getLastColumn: () => grid[0].length,
    getRange: (r, c, nr, nc) => {
      if (nr === undefined) return cell(r, c);
      return {
        getValues: () => {
          const out = [];
          for (let i = r - 1; i < r - 1 + nr; i++) {
            const row = [];
            for (let j = c - 1; j < c - 1 + nc; j++) row.push(norm(grid[i] ? grid[i][j] : ''));
            out.push(row);
          }
          return out;
        },
        setValues: (m) => m.forEach((row, i) => row.forEach((v, j) => cell(r + i, c + j).setValue(v))),
        setNumberFormat: () => ({}),
      };
    },
    getDataRange: () => ({ getValues: () => grid.map(r => r.slice()) }),
    appendRow: (arr) => { grid.push(arr.map(norm)); },
    setFrozenRows: () => {},
    _grid: grid,
  };
}

const ENC = {
  Gastos: ['fecha','categoria','descripcion','monto','moneda','tipo_cambio','monto_base','id','usuario','folio','estado','pagado'],
  Pagos: ['id','folio','gasto_id','gasto_folio','categoria','fecha','monto','moneda','monto_base','metodo','notas','usuario'],
  Cobros: ['id','folio','venta_id','venta_folio','cliente','proyecto_id','fecha','monto','moneda','monto_base','metodo','notas','usuario','tipo'],
  Ventas: ['fecha','cliente','almacen','items','total','moneda','tipo_cambio','total_base','costo_total_base','utilidad_base','notas','id','folio','usuario','cliente_id','proyecto_id','estado_pago','almacen_id','items_json'],
  Proyectos_Movs: ['id','proyecto_id','tipo','monto','moneda','tipo_cambio','monto_base','fecha','descripcion','usuario'],
  Config: ['clave','valor'],
  Log: ['fecha','usuario','accion','detalle'],
  Stock: ['producto_id','almacen_id','cantidad'],
  Productos: ['id','codigo','nombre','costo','precio','moneda','estado'],
  Cotizaciones: ['folio','id'],
  Proyectos: ['id','folio'],
  Proveedores: ['id','nombre'],
  Clientes: ['id','nombre'],
  OrdenesCompra: ['id','folio'],
  Recepciones: ['id','oc_id'],
  Almacenes: ['id','nombre'],
  Leads: ['fecha'], Resenas: ['id'], Visitas: ['fecha'], Visitas_Archivo: ['fecha'],
  GastosFijos: ['id','concepto'],
};

const gastos = load('gastos.json').gastos;
const pagos = load('pagos.json').pagos;
const cobros = load('cxc.json').cobros;
const libro = {
  getSheetByName: (n) => sheets[n] || null,
  insertSheet: (n) => { sheets[n] = makeSheet(n, ENC[n] || ['id']); return sheets[n]; },
  getSpreadsheetTimeZone: () => 'America/Hermosillo',
};
const sheets = {
  Gastos: makeSheet('Gastos', ENC.Gastos, gastos),        // SIN columna naturaleza (pre-migracion)
  Pagos: makeSheet('Pagos', ENC.Pagos, pagos),
  Cobros: makeSheet('Cobros', ENC.Cobros, cobros),
  Ventas: makeSheet('Ventas', ENC.Ventas, []),
  Proyectos_Movs: makeSheet('Proyectos_Movs', ENC.Proyectos_Movs, []),
  Config: makeSheet('Config', ENC.Config, [
    { clave: 'moneda_base', valor: 'MXN' }, { clave: 'tipo_cambio', valor: '18.5' },
    { clave: 'folio_gasto', valor: '56' }, { clave: 'folio_pago', valor: '49' },
    { clave: 'folio_ingreso', valor: '12' },
  ]),
  Log: makeSheet('Log', ENC.Log, []),
};
Object.keys(ENC).forEach(n => { if (!sheets[n]) sheets[n] = makeSheet(n, ENC[n], []); });

/* ---------------- Stubs de servicios de Apps Script ---------------- */
const cacheStore = {};
const pad = n => String(n).padStart(2, '0');
global.SpreadsheetApp = { getActiveSpreadsheet: () => libro };
global.Utilities = {
  formatDate: (d, tz, fmt) => {
    const s = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    if (fmt === 'yyyy') return String(d.getFullYear());
    return fmt === 'yyyy-MM-dd HH:mm' ? `${s} ${pad(d.getHours())}:${pad(d.getMinutes())}` : s;
  },
  getUuid: () => Math.random().toString(16).slice(2) + Date.now().toString(16),
  base64Decode: () => { throw new Error('no usado en harness'); },
};
global.CacheService = { getScriptCache: () => ({
  get: k => (k in cacheStore ? cacheStore[k] : null),
  put: (k, v) => { cacheStore[k] = v; },
  remove: (k) => { delete cacheStore[k]; },
}) };
global.LockService = { getScriptLock: () => ({ waitLock: () => {}, releaseLock: () => {} }) };
global.PropertiesService = { getScriptProperties: () => ({ getProperty: () => null, setProperty: () => {}, deleteProperty: () => {} }) };
global.ContentService = { MimeType: { JSON: 'application/json' }, createTextOutput: (s) => ({ setMimeType: () => ({ getContent: () => s }), payload: JSON.parse(s), getContent: () => s }) };
global.MailApp = { sendEmail: () => { throw new Error('MailApp no permitido en harness'); } };
global.DriveApp = { getFolderById: () => { throw new Error('DriveApp no permitido en harness'); } };
cacheStore['adis_token_test'] = '1';
const TOKEN = 'test';

/* ---------------- Cargar el backend REAL ---------------- */
const vm = require('vm');
// El desplegable es core.gs + analitica.gs (ver 50_BUILD/concat_backend.py):
// parseF y otras helpers viven en analitica.gs.
const code = fs.readFileSync(path.join(ROOT, '00_CORE', 'backend', 'core.gs'), 'utf8') + '\n' +
             fs.readFileSync(path.join(ROOT, '09_MARKETING', 'backend', 'analitica.gs'), 'utf8');
vm.runInThisContext(code, { filename: 'apps-script.gs' });

/* ---------------- Utilidades de chequeo ---------------- */
let pass = 0, fail = 0;
function check(nombre, ok, detalle) {
  if (ok) { pass++; console.log('PASS ' + nombre + (detalle ? ' · ' + detalle : '')); }
  else { fail++; console.log('FAIL ' + nombre + (detalle ? ' · ' + detalle : '')); }
}
function unwrap(out) { return out.payload !== undefined ? out.payload : JSON.parse(out.getContent()); }
function apiGet(qs) {
  const params = { token: TOKEN };
  qs.split('&').forEach(p => { const [k, v] = p.split('='); params[k] = decodeURIComponent(v); });
  return unwrap(doGet({ parameter: params }));
}
function apiPost(obj) {
  return unwrap(doPost({ postData: { contents: JSON.stringify(Object.assign({ token: TOKEN }, obj)) } }));
}

/* ---------------- Validaciones ---------------- */
const OCT = '2026-10-01', OCTF = '2026-10-31';
const _h = new Date();
const HOY = `${_h.getFullYear()}-${String(_h.getMonth() + 1).padStart(2, '0')}-${String(_h.getDate()).padStart(2, '0')}`;

// 0. pre-migracion: sin columna naturaleza
const g0 = apiGet('action=gastos');
check('PRE: hoja Gastos sin columna naturaleza', !('naturaleza' in g0.gastos[0]));

// 1. control_ie oct-2026 (conciliacion)
const ci = apiGet(`action=control_ie&desde=${OCT}&hasta=${OCTF}`);
check('control_ie ok', ci.ok === true);
check('V3 ingresos oct = 42,490.00', Math.abs(ci.ingresos.total_base - 42490) < 0.01, Number(ci.ingresos.total_base).toFixed(2));
check('V3 egresos oct = 69,231.04', Math.abs(ci.egresos.total_base - 69231.04) < 0.01, Number(ci.egresos.total_base).toFixed(2));
check('V3 variacion neta oct = -26,741.04', Math.abs(ci.variacion_neta - (-26741.04)) < 0.01, Number(ci.variacion_neta).toFixed(2));
check('V1 sin doble conteo: detalle suma = total', Math.abs(ci.egresos.detalle.reduce((s, m) => s + m.monto_base, 0) - ci.egresos.total_base) < 0.01);
check('V5 pendientes incluidos en egresos (todo por_clasificar)', Math.abs(ci.pendientes_clasificar.total_base - 69231.04) < 0.01 && ci.egresos.por_naturaleza.por_clasificar === ci.egresos.total_base);
check('V6 retiros oct = 0 (sin reclasificar)', ci.retiros.total_base === 0);
check('mensual trae 12 meses', ci.mensual.length === 12);
const mOct = ci.mensual.find(m => m.mes === '2026-10');
check('mensual oct coincide (ingresos/egresos/neto)',
  Math.abs(mOct.ingresos - 42490) < 0.01 && Math.abs(mOct.egresos - 69231.04) < 0.01 && Math.abs(mOct.neto + 26741.04) < 0.01);

// 2. igualdad con flujo_caja (mismo rango)
const fl = apiGet(`action=flujo_caja&desde=${OCT}&hasta=${OCTF}`);
check('V2 control_ie == flujo_caja (entradas)', Math.abs(fl.entradas - ci.ingresos.total_base) < 0.01);
check('V2 control_ie == flujo_caja (salidas)', Math.abs(fl.salidas - ci.egresos.total_base) < 0.01);
check('V2 neto igual', Math.abs(fl.neto - ci.variacion_neta) < 0.01);
check('por_actividad: todo operacion (aun no hay retiros)', Math.abs(fl.por_actividad.operacion.salidas - 69231.04) < 0.01 && fl.por_actividad.financiamiento.salidas === 0);

// 3. migracion de columna + P&L provisional + fix ultimo dia del mes
const g1 = apiGet('action=gastos');
check('POST-GET: columna naturaleza migrada (todas vacias/por_clasificar)', g1.gastos.every(g => !g.naturaleza || g.naturaleza === ''));
check('POST-GET: datos historicos intactos (56 folios, suma base)', g1.gastos.length === 56 && Math.abs(g1.gastos.reduce((s, g) => s + Number(g.monto_base || 0), 0) - 97378.04) < 0.01);
const er = apiGet('action=estado_resultados&mes=2026-10');
check('V3 P&L oct ingresos = 42,490 (fix ultimo dia del mes: incluye ING-0009 del 31)', Math.abs(er.ingresos - 42490) < 0.01, Number(er.ingresos).toFixed(2));
check('P&L provisional: flags presentes', er.provisional === true && 'resultado_provisional' in er && /NO es utilidad neta/i.test(er.motivo_provisional || ''));
check('P&L: sin clasificar oct = 77,781.04 (por fecha de GASTO, devengado); gastos operativos = 0', Math.abs(er.sin_clasificar - 77781.04) < 0.01 && er.total_gastos === 0, Number(er.sin_clasificar).toFixed(2));
check('P&L: costos = 0 y advertencia de utilidad provisional', er.costos === 0 && /provisional/i.test(er.advertencia || ''));

// 4. retiros endpoint
const ret = apiGet(`action=retiros&desde=${OCT}&hasta=${OCTF}`);
check('retiros oct = 0 pre-reclasificacion', ret.ok && ret.total_base === 0);

// 5. reclasificacion de PRUEBA en memoria (GAS-2026-0004 -> retiro)
const gasto4 = g1.gastos.find(g => g.folio === 'GAS-2026-0004');
const cl = apiPost({ tipo: 'gasto_clasificar', id: gasto4.id, naturaleza: 'retiro' });
check('gasto_clasificar ok', cl.ok === true, JSON.stringify(cl));
const ci2 = apiGet(`action=control_ie&desde=${OCT}&hasta=${OCTF}`);
check('V6 retiro EN egresos de efectivo (total general no cambia)', Math.abs(ci2.egresos.total_base - 69231.04) < 0.01);
check('V6 retiro identificado: 1,353.72', Math.abs(ci2.retiros.total_base - 1353.72) < 0.01 && ci2.retiros.movimientos === 1);
check('V5 pendientes bajan a 67,877.32', Math.abs(ci2.pendientes_clasificar.total_base - 67877.32) < 0.01);
const fl2 = apiGet(`action=flujo_caja&desde=${OCT}&hasta=${OCTF}`);
check('V6 retiro en flujo como FINANCIAMIENTO (salida)', Math.abs(fl2.por_actividad.financiamiento.salidas - 1353.72) < 0.01 && Math.abs(fl2.por_actividad.operacion.salidas - 67877.32) < 0.01);
const er2 = apiGet('action=estado_resultados&mes=2026-10');
check('V6 retiro NO es gasto operativo del P&L (total_gastos sigue 0; retiros aparte)', er2.total_gastos === 0 && Math.abs(er2.retiros - 1353.72) < 0.01);
const ret2 = apiGet(`action=retiros&desde=${OCT}&hasta=${OCTF}&agrupar=mes`);
check('reporte retiros: 1 movimiento, total 1,353.72, grupo 2026-10', ret2.total_movimientos === 1 && Math.abs(ret2.total_base - 1353.72) < 0.01 && ret2.grupos.length === 1 && ret2.grupos[0].periodo === '2026-10');

// 6. filtros: totales generales vs filtrados
const ci3 = apiGet(`action=control_ie&desde=${OCT}&hasta=${OCTF}&naturaleza=retiro`);
check('V4 filtro naturaleza: total GENERAL intacto (69,231.04)', Math.abs(ci3.egresos.total_base - 69231.04) < 0.01);
check('V4 filtro naturaleza: detalle filtrado aparte (1,353.72)', ci3.egresos.filtrado.activo === true && Math.abs(ci3.egresos.filtrado.total_base - 1353.72) < 0.01 && ci3.variacion_neta === ci2.variacion_neta);
const ci4 = apiGet(`action=control_ie&desde=${OCT}&hasta=${OCTF}&moneda=USD`);
check('V4 filtro moneda consistente ambos lados (ingresos 8,140 / egresos 7,400)', Math.abs(ci4.ingresos.total_base - 8140) < 0.01 && Math.abs(ci4.egresos.total_base - 7400) < 0.01);

// 7. protecciones y fixes Fase 0
const dr = apiPost({ tipo: 'delete_row', sheet: 'Gastos', row: 999999 });
check('F0 delete_row bloqueado en Gastos (NO_PERMITIDO)', dr.ok === false && dr.error && dr.error.code === 'NO_PERMITIDO', JSON.stringify(dr).slice(0, 120));
const g11 = g1.gastos.find(g => g.folio === 'GAS-2026-0011'); // 200 USD, tc 18.5, base 3700
apiPost({ tipo: 'gasto_editar', id: g11.id, fecha: '2026-10-15', categoria: 'Equipos', descripcion: 'edicion de prueba solo descripcion', monto: 200, moneda: 'USD' });
const g11d = apiGet('action=gastos').gastos.find(g => g.folio === 'GAS-2026-0011');
check('F0 gasto_editar conserva monto_base (3,700) y TC (18.5) sin cambio monetario', Math.abs(Number(g11d.monto_base) - 3700) < 0.01 && Number(g11d.tipo_cambio) === 18.5);
const cob8 = apiGet('action=cxc').cobros.find(c => c.folio === 'ING-2026-0008'); // 240 USD base 4440
apiPost({ tipo: 'ingreso_editar', id: cob8.id, fecha: '2026-10-22', concepto: 'edicion prueba', monto: 240, moneda: 'USD', metodo: 'Efectivo', notas: '', tipo_ingreso: 'otro' });
const cob8b = apiGet('action=cxc').cobros.find(c => c.folio === 'ING-2026-0008');
check('F0 ingreso_editar conserva monto_base (4,440) al editar solo concepto', Math.abs(Number(cob8b.monto_base) - 4440) < 0.01);

// 8. config con mapa_naturalezas
const cfgR = apiGet('action=config');
check('F1 config: mapa_naturalezas presente', 'mapa_naturalezas' in cfgR && typeof cfgR.mapa_naturalezas === 'object');

// 9. ETAPA 1: categoria de ingreso (col 15 de Cobros) + por_categoria en control_ie
const cfgCats = cfgR.categorias_ingresos || [];
check('E2 config: nuevas categorias de ingreso por defecto', cfgCats.includes('Venta de mercancía') && cfgCats.includes('Aportación del propietario'));
const ingN = apiPost({ tipo: 'ingreso', fecha: HOY, concepto: 'prueba categoria', monto: 100,
  moneda: 'MXN', metodo: 'Efectivo', tipo_ingreso: 'venta', categoria: 'Venta de mercancía' });
check('E2 alta ingreso con categoria', ingN.ok === true, ingN.folio);
const cobN = apiGet('action=cxc').cobros.find(c => String(c.folio) === String(ingN.folio));
check('E2 categoria persistida en Cobros', cobN && cobN.categoria === 'Venta de mercancía');
const ciN = apiGet(`action=control_ie&desde=${HOY}&hasta=${HOY}`);
check('E3 control_ie ingresos.por_categoria refleja la categoria',
  ((ciN.ingresos || {}).por_categoria || {})['Venta de mercancía'] >= 100,
  JSON.stringify((ciN.ingresos || {}).por_categoria || {}).slice(0, 80));
apiPost({ tipo: 'ingreso_editar', id: cobN.id, fecha: HOY, concepto: 'prueba categoria', monto: 100,
  moneda: 'MXN', metodo: 'Efectivo', tipo_ingreso: 'venta', categoria: 'Otros' });
const cobN2 = apiGet('action=cxc').cobros.find(c => String(c.folio) === String(ingN.folio));
check('E2 ingreso_editar actualiza categoria', cobN2 && cobN2.categoria === 'Otros');

console.log(`\n${pass}/${pass + fail} PASS` + (fail ? ` — FALLOS: ${fail}` : ''));
process.exit(fail ? 1 : 0);
