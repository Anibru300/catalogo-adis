// Harness Node.js — ETAPA 2: gasto-mercancia <-> stock. Ejecuta el core.gs REAL
// contra un emulador de Google Sheets cargado con el snapshot de produccion
// (60_DATA/auditoria_2026-11-06 + revision_gastos_2026-11-06).
// SOLO LECTURA del snapshot: el "libro" es una estructura en memoria.
// Valida: gasto nuevo con entrada a inventario, camino retroactivo
// (gasto_inventario), idempotencia, validaciones todo-o-nada, costo por
// defecto, marcado cols 14/15, trazabilidad MOV (doc_tipo GASTO) y que la
// conciliacion financiera oct-2026 NO se altera (el stock no mueve dinero).
//
// Uso:  node scripts/auditoria/harness_node/run_etapa2.js
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const SNAP = path.join(ROOT, '60_DATA', 'auditoria_2026-11-06');
const load = f => JSON.parse(fs.readFileSync(path.join(SNAP, f), 'utf8'));
const movsSnap = JSON.parse(fs.readFileSync(path.join(ROOT, '60_DATA', 'revision_gastos_2026-11-06.json'), 'utf8')).movimientos;

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
  Movimientos: ['fecha','tipo','producto_id','producto','almacen_id','almacen','cantidad','costo_unit','moneda','referencia','notas','id','usuario','existencia_anterior','existencia_posterior','documento_tipo','documento_id','proveedor','lote'],
  Stock: ['producto_id','almacen_id','cantidad'],
  Productos: ['id','codigo','nombre','descripcion','categoria','subcategoria','proveedor','costo','precio','unidad','stock_minimo','moneda','foto','estado','notas','fecha_actualizacion','foto_2','foto_3','foto_4'],
  Almacenes: ['id','nombre'],
  Config: ['clave','valor'],
  Log: ['fecha','usuario','accion','detalle'],
  Pagos: ['id','folio','gasto_id','gasto_folio','categoria','fecha','monto','moneda','monto_base','metodo','notas','usuario'],
  Cobros: ['id','folio','venta_id','venta_folio','cliente','proyecto_id','fecha','monto','moneda','monto_base','metodo','notas','usuario','tipo','categoria'],
  Ventas: ['fecha','cliente','almacen','items','total','moneda','tipo_cambio','total_base','costo_total_base','utilidad_base','notas','id','folio','usuario','cliente_id','proyecto_id','estado_pago','almacen_id','items_json'],
  Proyectos_Movs: ['id','proyecto_id','tipo','monto','moneda','tipo_cambio','monto_base','fecha','descripcion','usuario'],
  Cotizaciones: ['folio','id'],
  Proyectos: ['id','folio'],
  Proveedores: ['id','nombre'],
  Clientes: ['id','nombre'],
  OrdenesCompra: ['id','folio'],
  Recepciones: ['id','oc_id'],
  Leads: ['fecha'], Resenas: ['id'], Visitas: ['fecha'], Visitas_Archivo: ['fecha'],
  GastosFijos: ['id','concepto'],
};

const gastos = load('gastos.json').gastos;
const pagos = load('pagos.json').pagos;
const cobros = load('cxc.json').cobros;
const productos = load('productos.json').productos;
const stockRows = load('stock.json').stock;
const libro = {
  getSheetByName: (n) => sheets[n] || null,
  insertSheet: (n) => { sheets[n] = makeSheet(n, ENC[n] || ['id']); return sheets[n]; },
  getSpreadsheetTimeZone: () => 'America/Hermosillo',
};
const sheets = {
  Gastos: makeSheet('Gastos', ENC.Gastos, gastos),        // SIN cols 14/15 (pre-migracion)
  Movimientos: makeSheet('Movimientos', ENC.Movimientos, movsSnap),
  Stock: makeSheet('Stock', ENC.Stock, stockRows),
  Productos: makeSheet('Productos', ENC.Productos, productos),
  Almacenes: makeSheet('Almacenes', ENC.Almacenes, [
    { id: 'e6a5e282', nombre: 'Nogales' },
    { id: '369dc79a', nombre: 'Decosonora' },
    { id: '07d53c1e', nombre: 'Rio rico' },
  ]),
  Pagos: makeSheet('Pagos', ENC.Pagos, pagos),
  Cobros: makeSheet('Cobros', ENC.Cobros, cobros),
  Config: makeSheet('Config', ENC.Config, [
    { clave: 'moneda_base', valor: 'MXN' }, { clave: 'tipo_cambio', valor: '18.5' },
    { clave: 'folio_gasto', valor: '57' }, { clave: 'folio_pago', valor: '49' },
    { clave: 'folio_movimiento', valor: '7' }, { clave: 'folio_ingreso', valor: '12' },
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
const stockDe = (pid, aid) => {
  const f = sheets.Stock._grid.find((r, i) => i > 0 && String(r[0]) === String(pid) && String(r[1]) === String(aid));
  return f ? Number(f[2]) : 0;
};
const movsGASTO = (folio) => sheets.Movimientos._grid.filter((r, i) => i > 0 && String(r[15]) === 'GASTO' && String(r[16]) === String(folio));

const _h = new Date();
const HOY = `${_h.getFullYear()}-${String(_h.getMonth() + 1).padStart(2, '0')}-${String(_h.getDate()).padStart(2, '0')}`;
const NOG = 'e6a5e282';
const N_MOV_INI = sheets.Movimientos.getLastRow() - 1;
const N_GAST_INI = sheets.Gastos.getLastRow() - 1;
const N_STOCK_INI = sheets.Stock.getLastRow() - 1;

// productos de prueba: uno con stock real en Nogales (AGATA x5) y uno sin stock
const conStock = stockRows.find(s => s.almacen_id === NOG && Number(s.cantidad) > 0);
const prodCon = productos.find(p => p.id === conStock.producto_id);
const prodSin = productos.find(p => !stockRows.some(s => s.producto_id === p.id));

/* 1. gasto nuevo con entrada a inventario (2 partidas, costo explicito) */
const g1 = apiPost({ tipo: 'gasto', fecha: HOY, categoria: 'Mercancía', descripcion: 'prueba etapa2 entrada',
  monto: 350, moneda: 'MXN', naturaleza: 'inventario', almacen_id: NOG,
  items_inventario: [
    { producto_id: prodCon.id, cantidad: 2, costo_unit: 100 },
    { producto_id: prodSin.id, cantidad: 3, costo_unit: 50 },
  ] });
check('E2 gasto con entrada: ok y folio nuevo', g1.ok === true && String(g1.folio) === 'GAS-2026-0057', JSON.stringify(g1).slice(0, 100));
check('E2 stock_nuevo devuelto para ambos', g1.stock_nuevo && g1.stock_nuevo[prodCon.id] === Number(conStock.cantidad) + 2 && g1.stock_nuevo[prodSin.id] === 3,
  JSON.stringify(g1.stock_nuevo));
check('E2 stock persistido: AGATA +2 y producto nuevo creado con 3',
  stockDe(prodCon.id, NOG) === Number(conStock.cantidad) + 2 && stockDe(prodSin.id, NOG) === 3);
const movs1 = movsGASTO(g1.folio);
check('E2 dos MOV- de entrada con doc_tipo=GASTO y doc_id=folio', movs1.length === 2 && movs1.every(m => m[1] === 'entrada' && String(m[16]) === String(g1.folio)));
check('E2 fecha del movimiento = fecha del gasto', movs1.every(m => String(m[0]).indexOf(HOY) === 0), movs1[0] && movs1[0][0]);
check('E2 trazabilidad: referencia y existencia anterior/posterior correctas',
  movs1.every(m => String(m[9]) === 'Gasto ' + g1.folio) &&
  Number(movs1.find(m => String(m[2]) === prodCon.id)[13]) === Number(conStock.cantidad) &&
  Number(movs1.find(m => String(m[2]) === prodCon.id)[14]) === Number(conStock.cantidad) + 2);
const prodConUpd = apiGet('action=productos').productos.find(p => String(p.id) === prodCon.id);
const prodSinUpd = apiGet('action=productos').productos.find(p => String(p.id) === prodSin.id);
check('E2 ultimo costo actualizado en Productos (100 / 50)', Number(prodConUpd.costo) === 100 && Number(prodSinUpd.costo) === 50);
const gasto1 = apiGet('action=gastos').gastos.find(g => String(g.folio) === String(g1.folio));
check('E2 cols 14/15: entrada_inventario=SI e items_json con 2 partidas',
  gasto1 && gasto1.entrada_inventario === 'SI' && JSON.parse(gasto1.items_json || '[]').length === 2);
check('E2 gasto sin pagos ni cambios monetarios (monto 350, pagado 0)', Number(gasto1.monto) === 350 && Number(gasto1.pagado) === 0);

/* 2. idempotencia: un gasto solo admite UNA entrada de inventario */
const again = apiPost({ tipo: 'gasto_inventario', id: gasto1.id, almacen_id: NOG, items: [{ producto_id: prodCon.id, cantidad: 1, costo_unit: 1 }] });
check('E2 idempotencia: segunda entrada rechazada (NO_PERMITIDO)',
  again.ok === false && again.error && again.error.code === 'NO_PERMITIDO', JSON.stringify(again).slice(0, 120));
check('E2 idempotencia: stock y movimientos sin cambios',
  stockDe(prodCon.id, NOG) === Number(conStock.cantidad) + 2 && movsGASTO(g1.folio).length === 2);

/* 3. camino retroactivo: gasto EXISTENTE (GAS-2026-0005, 2026-10-07) */
const gas5 = apiGet('action=gastos').gastos.find(g => g.folio === 'GAS-2026-0005');
const retro0 = apiPost({ tipo: 'gasto_inventario', id: gas5.id, almacen_id: NOG, items: [{ producto_id: prodCon.id, cantidad: 1, costo_unit: 10 }] });
check('E2 retro: gasto por_clasificar rechazado hasta reclasificar',
  retro0.ok === false && retro0.error && retro0.error.code === 'NO_PERMITIDO');
apiPost({ tipo: 'gasto_clasificar', id: gas5.id, naturaleza: 'inventario' });
const retro1 = apiPost({ tipo: 'gasto_inventario', id: gas5.id, almacen_id: NOG, items: [{ producto_id: prodCon.id, cantidad: 4, costo_unit: 260 }] });
check('E2 retro: entrada aplicada a gasto de oct-2026', retro1.ok === true, JSON.stringify(retro1).slice(0, 120));
const movs5 = movsGASTO('GAS-2026-0005');
check('E2 retro: MOV- con FECHA DEL GASTO (2026-10-07, retroactiva)', movs5.length === 1 && String(movs5[0][0]).indexOf('2026-10-07') === 0, movs5[0] && movs5[0][0]);
const gas5b = apiGet('action=gastos').gastos.find(g => g.folio === 'GAS-2026-0005');
check('E2 retro: cols 14/15 marcadas; naturaleza intacta; monto intacto',
  gas5b.entrada_inventario === 'SI' && gas5b.naturaleza === 'inventario' && Number(gas5b.monto) === 1055.47);

/* 4. validaciones todo-o-nada (nada se escribe si algo esta mal) */
const nGasAntes = sheets.Gastos.getLastRow() - 1;
const nMovAntes = sheets.Movimientos.getLastRow() - 1;
const v1 = apiPost({ tipo: 'gasto', categoria: 'Mercancía', monto: 100, naturaleza: 'operativo', almacen_id: NOG, items_inventario: [{ producto_id: prodCon.id, cantidad: 1, costo_unit: 1 }] });
check('E2 val: naturaleza no inventario + items -> VALIDACION', v1.ok === false && v1.error && v1.error.code === 'VALIDACION');
const v2 = apiPost({ tipo: 'gasto', categoria: 'Mercancía', monto: 100, naturaleza: 'inventario', almacen_id: NOG, items_inventario: [{ producto_id: prodCon.id, cantidad: 0, costo_unit: 1 }] });
check('E2 val: cantidad 0 -> VALIDACION', v2.ok === false && v2.error && v2.error.code === 'VALIDACION');
const v3 = apiPost({ tipo: 'gasto', categoria: 'Mercancía', monto: 100, naturaleza: 'inventario', almacen_id: 'xxxx', items_inventario: [{ producto_id: prodCon.id, cantidad: 1, costo_unit: 1 }] });
check('E2 val: almacen inexistente -> NO_ENCONTRADO y sin gasto huérfano', v3.ok === false && v3.error && v3.error.code === 'NO_ENCONTRADO');
const v4 = apiPost({ tipo: 'gasto', categoria: 'Mercancía', monto: 100, naturaleza: 'inventario', almacen_id: NOG, items_inventario: [{ producto_id: prodCon.id, cantidad: 1, costo_unit: 1 }, { producto_id: prodCon.id, cantidad: 2, costo_unit: 1 }] });
check('E2 val: producto repetido -> VALIDACION', v4.ok === false && v4.error && /repetido/i.test(v4.error.message || ''));
const v5 = apiPost({ tipo: 'gasto', categoria: 'Mercancía', monto: 100, naturaleza: 'inventario', almacen_id: NOG, items_inventario: [{ producto_id: 'zzzz', cantidad: 1, costo_unit: 1 }] });
check('E2 val: producto inexistente -> NO_ENCONTRADO', v5.ok === false && v5.error && v5.error.code === 'NO_ENCONTRADO');
check('E2 todo-o-nada: ningun gasto/movimiento huérfano tras validaciones',
  sheets.Gastos.getLastRow() - 1 === nGasAntes && sheets.Movimientos.getLastRow() - 1 === nMovAntes);

/* 5. costo_unit omitido: toma el ultimo costo del producto (retrocompatible) */
const g2 = apiPost({ tipo: 'gasto', fecha: HOY, categoria: 'Mercancía', monto: 999, naturaleza: 'inventario', almacen_id: NOG,
  items_inventario: [{ producto_id: prodSin.id, cantidad: 1 }] });
const movs2 = movsGASTO(g2.folio);
check('E2 costo omitido: aplica con costo_unit=50 (ultimo costo del producto)', g2.ok === true && Number(movs2[0][7]) === 50, 'costo=' + (movs2[0] && movs2[0][7]));

/* 6. gasto SIN items: comportamiento Etapa 1 intacto */
const g3 = apiPost({ tipo: 'gasto', fecha: HOY, categoria: 'Gasolina', monto: 500, naturaleza: 'operativo' });
check('E2 gasto sin items: ok, stock_nuevo null, sin movimientos',
  g3.ok === true && g3.stock_nuevo === null && movsGASTO(g3.folio).length === 0);

/* 7. integridad e inmutabilidad del historial */
const gastosAhora = apiGet('action=gastos').gastos;
const idsOrig = new Set(gastos.map(g => String(g.id)));
const orig56 = gastosAhora.filter(g => idsOrig.has(String(g.id)));
check('E2 inmutabilidad: 56 gastos originales intactos (suma monto_base)',
  orig56.length === 56 && Math.abs(orig56.reduce((s, g) => s + Number(g.monto_base || 0), 0) - 97378.04) < 0.01);
check('E2 inmutabilidad: movimientos originales (66) y stock original (23 filas) preservados',
  sheets.Movimientos.getLastRow() - 1 >= 66 + 4 && sheets.Stock.getLastRow() - 1 >= N_STOCK_INI);
const primeros66 = sheets.Movimientos._grid.slice(1, 67);
check('E2 inmutabilidad: los 66 MOV- originales byte a byte iguales',
  primeros66.every((r, i) => r.every((c, j) => String(c) === String(movsSnap[i][ENC.Movimientos[j]]))));

/* 8. la entrada de stock NO mueve dinero (conciliacion oct-2026 intacta) */
const ci = apiGet('action=control_ie&desde=2026-10-01&hasta=2026-10-31');
check('E2 control_ie oct: egresos siguen 69,231.04 pese a entradas de stock',
  ci.ok === true && Math.abs(ci.egresos.total_base - 69231.04) < 0.01);

/* 9. bitacora */
const logs = apiGet('action=logs');
const logTxt = JSON.stringify(logs);
check('E2 bitacora: eventos gasto_inventario y gasto_registrado presentes',
  logTxt.indexOf('gasto_inventario') !== -1 && logTxt.indexOf('gasto_registrado') !== -1);

console.log(`\n${pass}/${pass + fail} PASS` + (fail ? ` — FALLOS: ${fail}` : ''));
process.exit(fail ? 1 : 0);
