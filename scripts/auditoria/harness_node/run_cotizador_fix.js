// Harness Node.js — FIX COTIZADOR 2026-11-07 (re-guardar no duplica).
// Ejecuta el core.gs REAL contra un emulador de Google Sheets en memoria.
// Valida: quote nuevo crea fila con folio ADIS-, re-guardar con folio existente
// ACTUALIZA la fila (sin duplicar), conserva id/fecha/estado, respeta folio,
// placeholder '___' genera folio nuevo, y el resto del backend sigue intacto.
//
// Uso:  node scripts/auditoria/harness_node/run_cotizador_fix.js
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..', '..');

function makeSheet(nombre, headers, rows) {
  const grid = [headers.slice()];
  (rows || []).forEach(r => grid.push(headers.map(h => (r[h] !== undefined && r[h] !== null) ? r[h] : '')));
  const norm = v => (v === undefined || v === null) ? '' : v;
  const cell = (r, c) => ({
    getValue: () => grid[r - 1][c - 1],
    setValue: v => { while (grid[r - 1].length < c) grid[r - 1].push(''); grid[r - 1][c - 1] = v; },
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
        setValues: m => m.forEach((row, i) => row.forEach((v, j) => cell(r + i, c + j).setValue(v))),
        setNumberFormat: () => ({}),
      };
    },
    getDataRange: () => ({ getValues: () => grid.map(r => r.slice()) }),
    appendRow: arr => { grid.push(arr.map(norm)); },
    setFrozenRows: () => {},
    _grid: grid,
  };
}

const ENC_COTIZ = ['fecha','cliente','telefono','ciudad','items','total','notas','folio','proyecto','ubicacion','moneda','subtotal','iva','estado','datos','id','usuario','cliente_id'];
const ENC = {
  Cotizaciones: ENC_COTIZ,
  Config: ['clave','valor'],
  Log: ['fecha','usuario','accion','detalle'],
  Gastos: ['fecha','categoria','descripcion','monto','moneda','tipo_cambio','monto_base','id','usuario','folio','estado','pagado','naturaleza'],
  Pagos: ['id','folio','gasto_id'], Cobros: ['id','folio'], Ventas: ['id','folio'],
  Proyectos_Movs: ['id'], Productos: ['id','nombre'], Movimientos: ['id'],
  Stock: ['producto_id','almacen_id','cantidad'], Almacenes: ['id','nombre'],
  Proyectos: ['id','folio'], Proveedores: ['id'], Clientes: ['id'],
  OrdenesCompra: ['id','folio'], Recepciones: ['id','oc_id'],
  Leads: ['fecha'], Resenas: ['id'], Visitas: ['fecha'], Visitas_Archivo: ['fecha'],
  GastosFijos: ['id','concepto'],
};
const libro = {
  getSheetByName: n => sheets[n] || null,
  insertSheet: n => { sheets[n] = makeSheet(n, ENC[n] || ['id']); return sheets[n]; },
  getSpreadsheetTimeZone: () => 'America/Hermosillo',
};
const sheets = {
  Cotizaciones: makeSheet('Cotizaciones', ENC.Cotizaciones, [{
    fecha: '2026-10-01 10:00', cliente: 'Cliente Viejo', telefono: '', ciudad: 'Nogales',
    items: 'X y y x1 PZS @100', total: 100, notas: '', folio: 'ADIS-2026-001', proyecto: '',
    ubicacion: 'Nogales', moneda: 'MXN', subtotal: 100, iva: 0, estado: 'Activa',
    datos: '{}', id: 'cot1vieja', usuario: 'Adis', cliente_id: '',
  }]),
  Config: makeSheet('Config', ENC.Config, [
    { clave: 'moneda_base', valor: 'MXN' }, { clave: 'tipo_cambio', valor: '18.5' },
    { clave: 'folio_cotizacion', valor: '2' },
  ]),
  Log: makeSheet('Log', ENC.Log, []),
};
Object.keys(ENC).forEach(n => { if (!sheets[n]) sheets[n] = makeSheet(n, ENC[n], []); });

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
  base64Decode: () => { throw new Error('no usado'); },
};
global.CacheService = { getScriptCache: () => ({ get: k => cacheStore[k] ?? null, put: (k, v) => { cacheStore[k] = v; }, remove: k => { delete cacheStore[k]; } }) };
global.LockService = { getScriptLock: () => ({ waitLock: () => {}, releaseLock: () => {} }) };
global.PropertiesService = { getScriptProperties: () => ({ getProperty: () => null, setProperty: () => {}, deleteProperty: () => {} }) };
global.ContentService = { MimeType: { JSON: 'application/json' }, createTextOutput: s => ({ setMimeType: () => ({ getContent: () => s }), payload: JSON.parse(s), getContent: () => s }) };
global.MailApp = { sendEmail: () => {} };
global.DriveApp = { getFolderById: () => { throw new Error('no'); } };
cacheStore['adis_token_test'] = '1';
const TOKEN = 'test';

const vm = require('vm');
const code = fs.readFileSync(path.join(ROOT, '00_CORE', 'backend', 'core.gs'), 'utf8') + '\n' +
             fs.readFileSync(path.join(ROOT, '09_MARKETING', 'backend', 'analitica.gs'), 'utf8');
vm.runInThisContext(code, { filename: 'apps-script.gs' });

let pass = 0, fail = 0;
const check = (n, ok, d) => { ok ? pass++ : fail++; console.log((ok ? 'PASS ' : 'FAIL ') + n + (d ? ' · ' + d : '')); };
const unwrap = out => out.payload !== undefined ? out.payload : JSON.parse(out.getContent());
const apiGet = qs => {
  const params = { token: TOKEN };
  qs.split('&').forEach(p => { const [k, v] = p.split('='); params[k] = decodeURIComponent(v); });
  return unwrap(doGet({ parameter: params }));
};
const apiPost = o => unwrap(doPost({ postData: { contents: JSON.stringify(Object.assign({ token: TOKEN }, o)) } }));
const filas = () => sheets.Cotizaciones.getLastRow() - 1;

// 1. quote NUEVO: crea fila con folio consecutivo
const n0 = filas();
const q1 = apiPost({ tipo: 'quote', cliente: 'Nuevo Cliente', telefono: '631', ciudad: 'Nogales',
  items: [{ codigo: 'ABC', descripcion: 'Placa', cantidad: 2, unidad: 'PZS', precio: 850 }],
  subtotal: 1700, iva: 272, total: 1972, moneda: 'MXN', datos: { proyecto: 'X' } });
check('COT nuevo: ok y folio ADIS-2026-002', q1.ok === true && String(q1.folio) === 'ADIS-2026-002', JSON.stringify(q1));
check('COT nuevo: 1 fila agregada', filas() === n0 + 1, String(filas()));

// 2. re-guardar con folio existente: ACTUALIZA, no duplica
const quotes = apiGet('action=quotes').quotes;
const laNueva = quotes.find(x => String(x.folio) === 'ADIS-2026-002');
const n1 = filas();
const q2 = apiPost({ tipo: 'quote', folio: 'ADIS-2026-002', cliente: 'Nuevo Cliente',
  total: 2100, subtotal: 1800, iva: 300, moneda: 'MXN', datos: { proyecto: 'X v2' } });
check('COT re-guardar: ok, mismo folio', q2.ok === true && String(q2.folio) === 'ADIS-2026-002');
check('COT re-guardar: SIN fila duplicada', filas() === n1, String(filas()));
const quotes2 = apiGet('action=quotes').quotes;
const actualizada = quotes2.find(x => String(x.folio) === 'ADIS-2026-002');
check('COT re-guardar: total/iva actualizados (2100/300)', Number(actualizada.total) === 2100 && Number(actualizada.iva) === 300);
check('COT re-guardar: id y fecha originales conservados', String(actualizada.id) === String(laNueva.id) && String(actualizada.fecha) === String(laNueva.fecha));

// 3. estado no se resetea al re-guardar
apiPost({ tipo: 'set_estado_quote', id: laNueva.id, estado: 'Aprobada' });
apiPost({ tipo: 'quote', folio: 'ADIS-2026-002', cliente: 'Nuevo Cliente', total: 2200, subtotal: 1896.55, iva: 303.45, moneda: 'MXN', datos: {} });
const st = apiGet('action=quotes').quotes.find(x => String(x.folio) === 'ADIS-2026-002');
check('COT re-guardar: estado Aprobada conservado', String(st.estado) === 'Aprobada', String(st.estado));
check('COT re-guardar: sigue sin duplicar', apiGet('action=quotes').quotes.filter(x => String(x.folio) === 'ADIS-2026-002').length === 1);

// 4. placeholder '___' genera folio nuevo
const q3 = apiPost({ tipo: 'quote', folio: 'ADIS-2026-___', cliente: 'Otro', total: 500, moneda: 'MXN', datos: {} });
check('COT placeholder ___: folio nuevo generado', q3.ok === true && String(q3.folio).indexOf('___') === -1, q3.folio);

// 5. sin folio: crea nuevo; folio viejo no reutilizable en append
const q4 = apiPost({ tipo: 'quote', cliente: 'Sin folio', total: 1, moneda: 'MXN', datos: {} });
check('COT sin folio: folio nuevo', q4.ok === true && q4.folio !== q1.folio, q4.folio);

// 6. bitácora registra alta y actualización
const logsTxt = JSON.stringify(apiGet('action=logs'));
check('COT bitacora: cotizacion y cotizacion_actualizada', logsTxt.indexOf('cotizacion_actualizada') !== -1);

console.log(`\n${pass}/${pass + fail} PASS` + (fail ? ` — FALLOS: ${fail}` : ''));
process.exit(fail ? 1 : 0);
