/*************************************************************************
 * ADIS — Backend integral (FASE 0: cimientos de arquitectura)
 *
 * Cambios de la Fase 0 respecto a la version anterior:
 *  - LockService en TODAS las operaciones criticas (folios, stock, ventas,
 *    importaciones, borrados): imposible folios duplicados o stock perdido
 *    por concurrencia.
 *  - Manejo global de errores: cualquier excepcion devuelve JSON consistente
 *    {ok:false, error:{code, message}}. Nunca HTML de Google.
 *  - Config con cache por ejecucion (una sola lectura de la hoja por
 *    request; invalidacion inmediata al escribir).
 *  - Inventario transaccional: cada movimiento registra id MOV-AAAA-NNNNN,
 *    usuario, existencia anterior/posterior y documento origen. La
 *    existencia SIEMPRE es consecuencia de movimientos trazables.
 *  - Stock negativo bloqueado (salida > existencia = error STOCK_INSUFICIENTE).
 *  - Folios imposibles de duplicar: VEN-AAAA-NNNN (ventas), MOV (movimientos),
 *    ADIS-AAAA-NNN (cotizaciones, igual que antes).
 *  - Borrado por ID estable (ya no por indice de fila) en reseñas y gastos;
 *    compatibilidad temporal con el parametro viejo `row`.
 *  - Venta multi-hoja con compensacion best-effort (Sheets no tiene ACID):
 *    si falla tras mover stock, se revierten los movimientos y se registra.
 *  - Track protegido: rate-limit por huella (120 eventos/10 min),
 *    deduplicacion (45 s) y archivo de retencion (Visitas_Archivo) en vez
 *    de borrar historial.
 *  - Login con limite de intentos (5 / 10 min) y cierre de sesion real
 *    (tipo 'logout' revoca el token).
 *  - El usuario admin ya NO se escribe en el Log (trazabilidad sin exponer
 *    credenciales).
 *  - HOJAS_BORRABLES ya no incluye Ventas ni Movimientos (historico
 *    financiero/inventario protegido).
 *
 * INSTRUCCIONES (resumen; guia completa en admin/GUIA_CONFIGURACION.md):
 *  1. Extensiones > Apps Script, borra el contenido y pega TODO este archivo.
 *  2. Cambia ADMIN_USUARIO y ADMIN_CLAVE abajo (y ROTA la clave: la actual
 *     estuvo expuesta en el repositorio; instrucciones en el reporte Fase 0).
 *  3. Despliega: Implementar > Administrar implementaciones > (✏️) > Nueva
 *     VERSION > Implementar. ASI LA URL NO CAMBIA. Si creas "nueva
 *     implementacion", la URL cambia y hay que replicarla en 4 archivos.
 *************************************************************************/

// ======= CREDENCIALES DEL ADMINISTRADOR (CAMBIA Y ROTA ESTOS DOS VALORES) =======
var ADMIN_USUARIO = 'Adis';
var ADMIN_CLAVE   = 'Adisdiseño2026';
// ================================================================================

var SHEET_LEADS    = 'Leads';
var SHEET_QUOTES   = 'Cotizaciones';
var SHEET_REVIEWS  = 'Reseñas';
var SHEET_PRODUCTS = 'Productos';
var SHEET_WAREHOUSES = 'Almacenes';
var SHEET_STOCK    = 'Stock';
var SHEET_MOVES    = 'Movimientos';
var SHEET_SALES    = 'Ventas';
var SHEET_EXPENSES = 'Gastos';
var SHEET_CONFIG   = 'Config';
var SHEET_LOG      = 'Log';
var SHEET_VISITS   = 'Visitas';
var SHEET_VISITS_ARCHIVE = 'Visitas_Archivo';
var VISITS_MAX_FILAS = 5000;   // activas; el excedente se ARCHIVA (no se borra)
var TOKEN_MINUTOS  = 8 * 60;

// Limpieza administrativa permitida. Ventas/Movimientos NO se pueden borrar:
// son historico financiero e inventario (usar compensaciones, no deleciones).
var HOJAS_BORRABLES = [SHEET_LEADS, SHEET_QUOTES, SHEET_REVIEWS, SHEET_EXPENSES, SHEET_STOCK, SHEET_VISITS];

var MONEDAS = ['MXN', 'USD'];
var TIPOS_MOVIMIENTO = ['entrada', 'salida', 'ajuste'];

/* ----- Esquemas (columnas NUEVAS siempre se agregan al final; nunca se
   renombran ni reordenan las existentes para no romper datos vivos) ----- */
var ENC_COTIZ = ['fecha', 'cliente', 'telefono', 'ciudad', 'items', 'total', 'notas',
  'folio', 'proyecto', 'ubicacion', 'moneda', 'subtotal', 'iva', 'estado', 'datos', 'id', 'usuario'];
var ENC_PROD = ['id', 'codigo', 'nombre', 'descripcion', 'categoria', 'subcategoria', 'proveedor',
  'costo', 'precio', 'unidad', 'stock_minimo', 'moneda', 'foto', 'estado', 'notas', 'fecha_actualizacion'];
var ENC_MOV = ['fecha', 'tipo', 'producto_id', 'producto', 'almacen_id', 'almacen', 'cantidad',
  'costo_unit', 'moneda', 'referencia', 'notas',
  'id', 'usuario', 'existencia_anterior', 'existencia_posterior', 'documento_tipo', 'documento_id'];
var ENC_VENTAS = ['fecha', 'cliente', 'almacen', 'items', 'total', 'moneda', 'tipo_cambio',
  'total_base', 'costo_total_base', 'utilidad_base', 'notas', 'id', 'folio', 'usuario'];
var ENC_GASTOS = ['fecha', 'categoria', 'descripcion', 'monto', 'moneda', 'tipo_cambio', 'monto_base',
  'id', 'usuario'];
var ENC_RESENAS = ['fecha', 'nombre', 'estrellas', 'texto', 'activa', 'id', 'usuario'];
var ENC_VISITS = ['fecha', 'hora', 'pagina', 'seccion', 'origen', 'referrer', 'idioma',
  'dispositivo', 'navegador', 'ancho', 'ua'];

/* ============================ UTILIDADES ============================ */

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// Error de negocio: se convierte en {ok:false, error:{code, message}}.
// Todo error LANZADO dentro de handlers debe ser AdisError o sera ERROR_INTERNO.
function AdisError(code, message) {
  var e = new Error(message);
  e.adis = true;
  e.code = code;
  return e;
}
function err_(code, message) { return { ok: false, error: { code: code, message: message } }; }

// Todo endpoint pasa por aqui: errores SIEMPRE como JSON consistente,
// nunca stack traces ni HTML de Google al frontend.
function conErrores(fn) {
  try { return fn(); }
  catch (err) {
    try { log_('error_interno', String((err && err.message) || err).slice(0, 300)); } catch (e) {}
    if (err && err.adis) return json(err_(err.code, err.message));
    return json(err_('ERROR_INTERNO', 'Error interno del servidor. Intenta de nuevo.'));
  }
}

// Lock para operaciones criticas. El lock cubre la operacion completa
// (validar + escribir) para que dos ejecuciones concurrentes no interfieran.
function conLock(fn) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try { return fn(); }
  finally { lock.releaseLock(); }
}

function ss() { return SpreadsheetApp.getActiveSpreadsheet(); }

// Obtiene la hoja y garantiza el esquema: si falta, crea; si existen
// columnas nuevas al final, las agrega (migracion aditiva, sin tocar las
// existentes). Corrige el bug de la extension condicional de Cotizaciones.
function hoja(nombre, encabezados) {
  var libro = ss();
  var h = libro.getSheetByName(nombre);
  if (!h) {
    h = libro.insertSheet(nombre);
    h.appendRow(encabezados);
    h.setFrozenRows(1);
    return h;
  }
  var ultima = h.getLastColumn();
  var fila1 = ultima ? h.getRange(1, 1, 1, ultima).getValues()[0] : [];
  for (var i = 0; i < encabezados.length; i++) {
    var actual = i < fila1.length ? String(fila1[i]) : '';
    if (actual === '') h.getRange(1, i + 1).setValue(encabezados[i]);
    else if (actual !== encabezados[i]) {
      // Esquema divergente en posicion existente: NO se sobreescribe (protege datos).
      // Se registra en Log para revision manual.
      try { log_('esquema_divergente', nombre + ' col ' + (i + 1) + ': "' + actual + '" vs "' + encabezados[i] + '"'); } catch (e) {}
    }
  }
  return h;
}

function ahora_() {
  return Utilities.formatDate(new Date(), 'America/Hermosillo', 'yyyy-MM-dd HH:mm');
}
function hoy_() {
  return Utilities.formatDate(new Date(), 'America/Hermosillo', 'yyyy-MM-dd');
}
// Fecha YYYY-MM-DD valida o null (nunca aceptar formatos sueltos del cliente:
// rompian los filtros por rango del estado de resultados).
function validarFecha(f) {
  f = String(f || '').trim();
  return /^\d{4}-\d{2}-\d{2}$/.test(f) ? f : null;
}
function validarMoneda(m) {
  m = String(m || '').trim().toUpperCase();
  if (!m) return cfg('moneda_base', 'MXN');
  if (MONEDAS.indexOf(m) === -1) throw AdisError('VALIDACION', 'Moneda no soportada: ' + m);
  return m;
}
function padN(n, d) { var s = String(n); while (s.length < d) s = '0' + s; return s; }

function filasComoObjetos(nombre) {
  var h = ss().getSheetByName(nombre);
  if (!h) return [];
  var valores = h.getDataRange().getValues();
  if (valores.length < 2) return [];
  var encabezados = valores[0].map(function (e) { return String(e); });
  var filas = [];
  for (var i = 1; i < valores.length; i++) {
    var obj = {};
    for (var c = 0; c < encabezados.length; c++) {
      var v = valores[i][c];
      if (v instanceof Date) v = Utilities.formatDate(v, 'America/Hermosillo', 'yyyy-MM-dd HH:mm');
      obj[encabezados[c]] = v;
    }
    filas.push(obj);
  }
  return filas;
}

function nuevoId() { return Utilities.getUuid().slice(0, 8); }

function digestHex(str) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, String(str), Utilities.Charset.UTF_8);
  return bytes.map(function (b) {
    var v = (b < 0 ? b + 256 : b).toString(16);
    return v.length === 1 ? '0' + v : v;
  }).join('');
}

/* --- Clasificadores para el tracker de visitas (pestaña Flujo) --- */
function origenDe_(ref) {
  var r = String(ref || '').toLowerCase();
  if (!r) return 'Directo / sin dato';
  if (r.indexOf('google.') !== -1) return 'Google';
  if (r.indexOf('facebook.') !== -1 || r.indexOf('fb.') !== -1 || r.indexOf('fbwatch') !== -1) return 'Facebook';
  if (r.indexOf('instagram.') !== -1) return 'Instagram';
  if (r.indexOf('whatsapp') !== -1) return 'WhatsApp';
  if (r.indexOf('youtube.') !== -1) return 'YouTube';
  if (r.indexOf('tiktok.') !== -1) return 'TikTok';
  if (r.indexOf('bing.') !== -1) return 'Bing';
  return 'Otro sitio';
}
function dispositivoDe_(ua) {
  var u = String(ua || '').toLowerCase();
  if (!u) return 'Sin dato';
  if (u.indexOf('ipad') !== -1 || u.indexOf('tablet') !== -1) return 'Tableta';
  if (u.indexOf('mobi') !== -1 || u.indexOf('iphone') !== -1 || u.indexOf('android') !== -1) return 'Móvil';
  return 'Escritorio';
}
function navegadorDe_(ua) {
  var u = String(ua || '').toLowerCase();
  if (!u) return 'Sin dato';
  if (u.indexOf('edg') !== -1) return 'Edge';
  if (u.indexOf('opr') !== -1 || u.indexOf('opera') !== -1) return 'Opera';
  if (u.indexOf('crios') !== -1) return 'Chrome (iOS)';
  if (u.indexOf('chrome') !== -1) return 'Chrome';
  if (u.indexOf('firefox') !== -1) return 'Firefox';
  if (u.indexOf('safari') !== -1) return 'Safari';
  if (u.indexOf('trident') !== -1 || u.indexOf('msie') !== -1) return 'Internet Explorer';
  return 'Otro';
}

// Bitacora: quien (sin credenciales), que, cuando. Best-effort: si el Log
// falla no se rompe la operacion principal, pero queda registrado en Log.
var USUARIO_ACTUAL = 'sistema';
function log_(accion, detalle) {
  try {
    hoja(SHEET_LOG, ['fecha', 'usuario', 'accion', 'detalle'])
      .appendRow([ahora_(), USUARIO_ACTUAL, accion, String(detalle || '').slice(0, 500)]);
  } catch (err) {}
}

function esTokenValido(token) {
  if (!token) return false;
  return CacheService.getScriptCache().get('adis_token_' + token) === '1';
}
function crearToken() {
  var token = Utilities.getUuid();
  CacheService.getScriptCache().put('adis_token_' + token, '1', TOKEN_MINUTOS * 60);
  return token;
}
function revocarToken(token) {
  if (token) CacheService.getScriptCache().remove('adis_token_' + token);
}
function exigirToken(data) {
  if (!esTokenValido(data && data.token)) {
    throw AdisError('TOKEN_INVALIDO', 'Sesión no válida o expirada. Vuelve a entrar.');
  }
  USUARIO_ACTUAL = ADMIN_USUARIO;
}

/* ---------- Config con cache por ejecucion ----------
   Una sola lectura de la hoja por request. Invalidacion: inmediata al
   escribir con cfgSet (actualiza cache + hoja). Entre requests siempre se
   relee: no hay configuracion obsoleta mas alla de la vida de un request. */
var CONFIG_MEMO = null;
function cfgMemo() {
  if (!CONFIG_MEMO) {
    CONFIG_MEMO = {};
    filasComoObjetos(SHEET_CONFIG).forEach(function (f) { CONFIG_MEMO[String(f.clave)] = String(f.valor); });
  }
  return CONFIG_MEMO;
}
function cfg(clave, defecto) {
  var m = cfgMemo();
  return m[clave] !== undefined ? m[clave] : defecto;
}
// Precondicion: llamar dentro de conLock (el handler publico 'config' lo hace).
function cfgSet(clave, valor) {
  var h = hoja(SHEET_CONFIG, ['clave', 'valor']);
  var datos = h.getDataRange().getValues();
  for (var i = 1; i < datos.length; i++) {
    if (String(datos[i][0]) === clave) {
      h.getRange(i + 1, 2).setValue(valor);
      cfgMemo()[clave] = String(valor);
      return;
    }
  }
  h.appendRow([clave, valor]);
  cfgMemo()[clave] = String(valor);
}

/* ---------- Folios consecutivos (imposibles de duplicar) ----------
   Precondicion: llamar DENTRO de conLock. Reserva el numero incrementando
   el contador ANTES de usarlo: si la escritura posterior falla queda un
   hueco en la numeracion (aceptable) pero JAMAS un duplicado. */
function siguienteFolio(prefijo, claveCfg, digitos) {
  var n = Math.round(Number(cfg(claveCfg, '1'))) || 1;
  if (n < 1) n = 1;
  cfgSet(claveCfg, String(n + 1));
  return prefijo + '-' + Utilities.formatDate(new Date(), 'America/Hermosillo', 'yyyy') + '-' + padN(n, digitos);
}

// Convierte un monto a la moneda base. tc = unidades de moneda base por 1 USD
function aBase(monto, moneda, tc) {
  monto = Number(monto) || 0;
  moneda = moneda || cfg('moneda_base', 'MXN');
  var base = cfg('moneda_base', 'MXN');
  tc = Number(tc) || Number(cfg('tipo_cambio', '18.5')) || 1;
  if (moneda === base) return monto;
  if (moneda === 'USD' && base === 'MXN') return monto * tc;
  if (moneda === 'MXN' && base === 'USD') return monto / tc;
  return monto;
}

/* ---------- Stock: snapshot por ejecucion ----------
   Una sola lectura de la hoja Stock por request; los movimientos sucesivos
   (p.ej. una venta de 10 items) se calculan sobre el snapshot y persiste
   cada escritura. Esto elimina el N+1 de lecturas y garantiza que dentro
   de una misma operacion cada movimiento vea el anterior. */
var STOCK_SNAP = null;
function snapStock() {
  if (!STOCK_SNAP) {
    STOCK_SNAP = { map: {}, filas: {} };
    filasComoObjetos(SHEET_STOCK).forEach(function (s, i) {
      var k = String(s.producto_id) + '|' + String(s.almacen_id);
      STOCK_SNAP.map[k] = Number(s.cantidad) || 0;
      STOCK_SNAP.filas[k] = i + 2;
    });
  }
  return STOCK_SNAP;
}
function stockSnapDe(productoId, almacenId) {
  var k = String(productoId) + '|' + String(almacenId);
  var s = snapStock();
  return { cantidad: s.map[k] || 0, fila: s.filas[k] || null };
}
function ponerStockSnap(productoId, almacenId, cantidad) {
  var k = String(productoId) + '|' + String(almacenId);
  var s = snapStock();
  s.map[k] = cantidad;
  var h = hoja(SHEET_STOCK, ['producto_id', 'almacen_id', 'cantidad']);
  if (s.filas[k]) h.getRange(s.filas[k], 3).setValue(cantidad);
  else { h.appendRow([productoId, almacenId, cantidad]); s.filas[k] = h.getLastRow(); }
}

/* ---------- Movimiento de inventario trazable (REGLA CENTRAL DEL SISTEMA) ----------
   La existencia SOLO cambia mediante esta funcion. Registra:
   id MOV-AAAA-NNNNN, usuario, tipo, existencia anterior/posterior y
   documento origen (doc_tipo/doc_id). Stock negativo = excepcion.
   Precondicion: llamar dentro de conLock. */
function aplicarMovimiento(m) {
  var anterior = stockSnapDe(m.producto_id, m.almacen_id).cantidad;
  var posterior;
  if (m.tipo === 'entrada') {
    posterior = anterior + m.cantidad;
  } else if (m.tipo === 'salida') {
    posterior = anterior - m.cantidad;
    if (posterior < 0) {
      throw AdisError('STOCK_INSUFICIENTE',
        'Existencia insuficiente de "' + (m.producto || m.producto_id) + '": hay ' + anterior +
        ', se piden ' + m.cantidad + '.');
    }
  } else if (m.tipo === 'ajuste') {
    if (m.cantidad < 0) throw AdisError('VALIDACION', 'El ajuste no puede fijar una cantidad negativa.');
    posterior = m.cantidad;
  } else {
    throw AdisError('TIPO_MOVIMIENTO_INVALIDO', 'Tipo de movimiento no permitido: ' + m.tipo);
  }
  ponerStockSnap(m.producto_id, m.almacen_id, posterior);
  var movId = siguienteFolio('MOV', 'folio_movimiento', 5);
  hoja(SHEET_MOVES, ENC_MOV).appendRow([
    m.fecha || ahora_(), m.tipo, m.producto_id, m.producto || '', m.almacen_id, m.almacen || '',
    m.cantidad, m.costo_unit || '', m.moneda || cfg('moneda_base', 'MXN'), m.referencia || '', m.notas || '',
    movId, USUARIO_ACTUAL, anterior, posterior, m.doc_tipo || 'AJUSTE', m.doc_id || ''
  ]);
  return posterior;
}

// Localiza la fila de un registro por su ID estable (columna 'id').
// Devuelve el numero de fila de la hoja o null. Nunca confia en indices del cliente.
function filaPorId(nombreHoja, id) {
  if (!id) return null;
  var h = ss().getSheetByName(nombreHoja);
  if (!h) return null;
  var valores = h.getDataRange().getValues();
  if (valores.length < 2) return null;
  var enc = valores[0].map(String);
  var colId = enc.indexOf('id');
  if (colId === -1) return null;
  for (var i = 1; i < valores.length; i++) {
    if (String(valores[i][colId]) === String(id)) return i + 1;
  }
  return null;
}

/* ============================ GET (lectura) ============================ */

function doGet(e) {
  return conErrores(function () { return doGetInterno(e); });
}

function doGetInterno(e) {
  var action = (e && e.parameter && e.parameter.action) || '';
  var token = e && e.parameter && e.parameter.token;

  if (action === 'reviews') { // publico: solo lo que se publica en el sitio
    var resenias = filasComoObjetos(SHEET_REVIEWS)
      .filter(function (r) { return String(r.activa).toLowerCase() !== 'no'; })
      .map(function (r) { return { nombre: r.nombre, estrellas: r.estrellas, texto: r.texto, fecha: r.fecha }; });
    return json({ ok: true, reviews: resenias });
  }

  exigirToken({ token: token });

  if (action === 'visitas') {
    var hV = ss().getSheetByName(SHEET_VISITS);
    if (!hV) return json({ ok: true, visitas: [] });
    return json({ ok: true, visitas: filasComoObjetos(SHEET_VISITS) });
  }

  if (action === 'me') return json({ ok: true, usuario: ADMIN_USUARIO });
  if (action === 'leads') return json({ ok: true, leads: filasComoObjetos(SHEET_LEADS) });
  if (action === 'quotes') return json({ ok: true, quotes: filasComoObjetos(SHEET_QUOTES) });
  if (action === 'reviews_admin') return json({ ok: true, reviews: filasComoObjetos(SHEET_REVIEWS) });

  if (action === 'config') {
    return json({ ok: true, moneda_base: cfg('moneda_base', 'MXN'), tipo_cambio: cfg('tipo_cambio', '18.5') });
  }
  if (action === 'productos') {
    return json({ ok: true, productos: filasComoObjetos(SHEET_PRODUCTS) }); // activos e inactivos
  }
  if (action === 'almacenes') {
    return json({ ok: true, almacenes: filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.activo) !== 'no'; }) });
  }
  if (action === 'stock') {
    var productos = filasComoObjetos(SHEET_PRODUCTS);
    var almacenes = filasComoObjetos(SHEET_WAREHOUSES);
    var mapaP = {}, mapaA = {};
    productos.forEach(function (p) { mapaP[String(p.id)] = p.nombre || ''; });
    almacenes.forEach(function (a) { mapaA[String(a.id)] = a.nombre || ''; });
    var detalle = filasComoObjetos(SHEET_STOCK).map(function (s) {
      return { producto_id: s.producto_id, producto: mapaP[String(s.producto_id)] || '',
        almacen_id: s.almacen_id, almacen: mapaA[String(s.almacen_id)] || '',
        cantidad: Number(s.cantidad) || 0 };
    });
    return json({ ok: true, stock: detalle });
  }
  if (action === 'movimientos') {
    // FASE 1: filtro opcional por producto (historial completo hasta 500);
    // sin filtro, ultimos 100 como antes.
    var filtroPid = e.parameter.producto_id;
    var todosMovs = filasComoObjetos(SHEET_MOVES);
    if (filtroPid) {
      var filtrados = todosMovs.filter(function (m) { return String(m.producto_id) === String(filtroPid); });
      return json({ ok: true, movimientos: filtrados.slice(-500) });
    }
    return json({ ok: true, movimientos: todosMovs.slice(-100) });
  }
  if (action === 'ventas') return json({ ok: true, ventas: filasComoObjetos(SHEET_SALES).slice(-100) });
  if (action === 'gastos') return json({ ok: true, gastos: filasComoObjetos(SHEET_EXPENSES) });

  if (action === 'estado_resultados') {
    var mes = e.parameter.mes; // formato YYYY-MM
    var desde = mes ? mes + '-01' : null;
    var hasta = null;
    if (mes && /^\d{4}-\d{2}$/.test(mes)) {
      var partes = mes.split('-');
      var fin = new Date(Number(partes[0]), Number(partes[1]), 0);
      hasta = Utilities.formatDate(fin, 'America/Hermosillo', 'yyyy-MM-dd');
    }
    var enRango = function (fecha) {
      if (!desde || !hasta) return true;
      var f = String(fecha).slice(0, 10);
      return f >= desde && f <= hasta;
    };
    var ventas = filasComoObjetos(SHEET_SALES).filter(function (v) { return enRango(v.fecha); });
    var gastos = filasComoObjetos(SHEET_EXPENSES).filter(function (g) { return enRango(g.fecha); });
    var ingresos = 0, costos = 0;
    ventas.forEach(function (v) { ingresos += Number(v.total_base) || 0; costos += Number(v.costo_total_base) || 0; });
    var porCategoria = {};
    var totalGastos = 0;
    gastos.forEach(function (g) {
      var m = Number(g.monto_base) || 0;
      totalGastos += m;
      var cat = g.categoria || 'Otro';
      porCategoria[cat] = (porCategoria[cat] || 0) + m;
    });
    var utilBruta = ingresos - costos;
    var utilNeta = utilBruta - totalGastos;
    return json({ ok: true, mes: mes || 'Todos', moneda_base: cfg('moneda_base', 'MXN'),
      ingresos: ingresos, costos: costos, utilidad_bruta: utilBruta,
      gastos: porCategoria, total_gastos: totalGastos, utilidad_neta: utilNeta,
      num_ventas: ventas.length,
      margen_bruto: ingresos ? (utilBruta / ingresos * 100) : 0,
      margen_neto: ingresos ? (utilNeta / ingresos * 100) : 0 });
  }

  throw AdisError('ACCION_DESCONOCIDA', 'Acción desconocida: ' + action);
}

/* ============================ POST (escritura) ============================ */

function doPost(e) {
  return conErrores(function () {
    var data = {};
    try { data = JSON.parse(e.postData.contents); }
    catch (err) { throw AdisError('JSON_INVALIDO', 'El cuerpo de la petición no es JSON válido.'); }
    return doPostInterno(data);
  });
}

function doPostInterno(data) {
  var tipo = data.tipo || data.type || '';

  /* ----- publicos (sin token) ----- */

  if (tipo === 'login') {
    var cacheL = CacheService.getScriptCache();
    var intentos = Number(cacheL.get('login_fail_' + data.usuario)) || 0;
    if (intentos >= 5) {
      throw AdisError('DEMASIADOS_INTENTOS', 'Demasiados intentos fallidos. Espera 10 minutos e intenta de nuevo.');
    }
    if (data.usuario === ADMIN_USUARIO && data.clave === ADMIN_CLAVE) {
      cacheL.remove('login_fail_' + data.usuario);
      return json({ ok: true, token: crearToken() });
    }
    cacheL.put('login_fail_' + data.usuario, String(intentos + 1), 600);
    throw AdisError('CREDENCIALES_INVALIDAS', 'Usuario o contraseña incorrectos.');
  }

  if (tipo === 'logout') { // revoca el token propio; siempre responde ok
    revocarToken(data.token);
    return json({ ok: true });
  }

  if (tipo === 'lead') {
    if (data.empresa) return json({ ok: true }); // honeypot: spam, se ignora
    hoja(SHEET_LEADS, ['fecha', 'nombre', 'telefono', 'email', 'ciudad', 'metros', 'producto', 'mensaje', 'pagina', 'idioma'])
      .appendRow([ahora_(), data.nombre || '', data.telefono || '', data.email || '', data.ciudad || '',
        data.metros || '', data.producto || '', data.mensaje || '', data.pagina || '', data.idioma || '']);
    return json({ ok: true });
  }

  if (tipo === 'track') return trackProtegido(data);

  /* ----- a partir de aqui se exige token valido ----- */
  exigirToken(data);

  if (tipo === 'quote') return conLock(function () {
    var hCot = hoja(SHEET_QUOTES, ENC_COTIZ); // esquema garantizado (corrige extension condicional)
    var cliente = String(data.cliente || '').trim();
    if (!cliente && !(data.items || []).length) {
      throw AdisError('VALIDACION', 'La cotización necesita al menos un cliente o un producto.');
    }
    // Folio ADIS-AAAA-NNN bajo lock: imposible duplicar por concurrencia.
    // Se respeta si se re-guarda una cotizacion cargada (placeholder '___').
    var folio = data.folio ? String(data.folio) : '';
    if (!folio || folio.indexOf('___') !== -1) {
      folio = siguienteFolio('ADIS', 'folio_cotizacion', 3);
    }
    var items = (data.items || []).map(function (it) {
      return (it.codigo ? it.codigo + ' ' : '') + (it.descripcion || it.nombre || '') +
        ' x' + (it.cantidad || 1) + ' ' + (it.unidad || '') + ' @' + (it.precio || 0);
    }).join(' | ');
    hCot.appendRow([ahora_(), cliente, data.telefono || '', data.ciudad || data.ubicacion || '',
      items, data.total || 0, data.notas || '', folio, data.proyecto || '', data.ubicacion || '',
      validarMoneda(data.moneda || 'MXN'), data.subtotal || 0, data.iva || 0, data.estado || 'Activa',
      JSON.stringify(data.datos || {}), nuevoId(), USUARIO_ACTUAL]);
    log_('cotizacion', folio + ' · ' + cliente + ' · ' + (data.moneda || '') + ' ' + (data.total || 0));
    return json({ ok: true, folio: folio });
  });

  if (tipo === 'review') return conLock(function () {
    var nombre = String(data.nombre || '').trim(), texto = String(data.texto || '').trim();
    if (!nombre || !texto) throw AdisError('VALIDACION', 'La reseña necesita nombre y texto.');
    var estrellas = Math.round(Number(data.estrellas));
    if (!isFinite(estrellas) || estrellas < 1 || estrellas > 5) {
      throw AdisError('VALIDACION', 'Las estrellas deben ser un número de 1 a 5.');
    }
    hoja(SHEET_REVIEWS, ENC_RESENAS)
      .appendRow([ahora_(), nombre, estrellas, texto, 'si', nuevoId(), USUARIO_ACTUAL]);
    return json({ ok: true });
  });

  if (tipo === 'delete_review') return conLock(function () {
    var fila = filaPorId(SHEET_REVIEWS, data.id);
    if (!fila && Number(data.row) > 1) { // compatibilidad temporal con frontend viejo
      var hr = ss().getSheetByName(SHEET_REVIEWS);
      if (hr && Number(data.row) <= hr.getLastRow()) fila = Number(data.row);
    }
    if (!fila) throw AdisError('NO_ENCONTRADO', 'Reseña no encontrada.');
    var h = ss().getSheetByName(SHEET_REVIEWS);
    var enc = h.getRange(1, 1, 1, h.getLastColumn()).getValues()[0].map(String);
    var colActiva = enc.indexOf('activa');
    if (colActiva === -1) throw AdisError('ERROR_INTERNO', 'Esquema de reseñas sin columna activa.');
    h.getRange(fila, colActiva + 1).setValue('no'); // baja logica, historico preservado
    log_('resena_eliminada', 'id=' + (data.id || '') + ' fila=' + fila);
    return json({ ok: true });
  });

  /* ---------- Config ---------- */
  if (tipo === 'config') return conLock(function () {
    if (data.moneda_base) cfgSet('moneda_base', validarMoneda(data.moneda_base));
    if (data.tipo_cambio) {
      var tc = Number(data.tipo_cambio);
      if (!isFinite(tc) || tc <= 0) throw AdisError('VALIDACION', 'El tipo de cambio debe ser mayor que cero.');
      cfgSet('tipo_cambio', String(tc));
    }
    if (data.folio_cotizacion) {
      var fc = Math.round(Number(data.folio_cotizacion));
      if (!isFinite(fc) || fc < 1) throw AdisError('VALIDACION', 'El folio debe ser un entero mayor o igual a 1.');
      cfgSet('folio_cotizacion', String(fc));
    }
    return json({ ok: true, moneda_base: cfg('moneda_base', 'MXN'), tipo_cambio: cfg('tipo_cambio', '18.5') });
  });

  /* ---------- Productos ---------- */
  if (tipo === 'save_product') return conLock(function () {
    var hp = hoja(SHEET_PRODUCTS, ENC_PROD);
    var codigo = String(data.codigo || '').trim();
    if (!String(data.nombre || '').trim()) throw AdisError('VALIDACION', 'El producto necesita nombre.');
    if (!codigo) throw AdisError('VALIDACION', 'El código no puede estar vacío.');
    var monedaP = validarMoneda(data.moneda || 'MXN');
    var vals = hp.getDataRange().getValues();
    var filaExistente = null;
    for (var i = 1; i < vals.length; i++) {
      if (data.id && String(vals[i][0]) === String(data.id)) filaExistente = i + 1;
      else if (String(vals[i][1]).toLowerCase() === codigo.toLowerCase()) {
        throw AdisError('CODIGO_DUPLICADO', 'El código ' + codigo + ' ya existe en otro producto.');
      }
    }
    var fila = [data.id || nuevoId(), codigo, String(data.nombre).trim(), data.descripcion || '',
      data.categoria || '', data.subcategoria || '', data.proveedor || '',
      Number(data.costo) || 0, Number(data.precio) || 0, data.unidad || 'pieza',
      Number(data.stock_minimo) || 0, monedaP, data.foto || '',
      data.estado === 'inactivo' ? 'inactivo' : 'activo', data.notas || '', ahora_()];
    if (filaExistente) hp.getRange(filaExistente, 1, 1, ENC_PROD.length).setValues([fila]);
    else hp.appendRow(fila);
    log_(filaExistente ? 'producto_editado' : 'producto_creado', codigo + ' - ' + data.nombre);
    return json({ ok: true, id: fila[0] });
  });

  /* ---------- Actualizacion de precios/costos por lote (FASE 1) ----------
     Dos pasadas: primero se valida TODO, despues se escribe (si un precio
     es invalido no se actualiza nada). Columnas resueltas por nombre de
     encabezado, no por posicion. */
  if (tipo === 'update_precios') return conLock(function () {
    var itemsP = data.items || [];
    if (!itemsP.length) throw AdisError('VALIDACION', 'No hay precios para actualizar.');
    if (itemsP.length > 200) throw AdisError('VALIDACION', 'Máximo 200 productos por actualización.');
    var hp = hoja(SHEET_PRODUCTS, ENC_PROD);
    var valores = hp.getDataRange().getValues();
    var enc = valores[0].map(String);
    var colId = enc.indexOf('id'), colPrecio = enc.indexOf('precio'),
        colCosto = enc.indexOf('costo'), colFecha = enc.indexOf('fecha_actualizacion');
    // pasada 1: validar y localizar filas
    var plan = [];
    itemsP.forEach(function (it) {
      var filaP = null;
      for (var i = 1; i < valores.length; i++) {
        if (String(valores[i][colId]) === String(it.id)) { filaP = i + 1; break; }
      }
      if (!filaP) return; // producto inexistente: se omite (se reporta en actualizados)
      if (it.precio !== undefined && it.precio !== null && it.precio !== '') {
        var pr = Number(it.precio);
        if (!isFinite(pr) || pr < 0) throw AdisError('VALIDACION', 'Precio inválido (debe ser >= 0).');
      }
      if (it.costo !== undefined && it.costo !== null && it.costo !== '') {
        var co = Number(it.costo);
        if (!isFinite(co) || co < 0) throw AdisError('VALIDACION', 'Costo inválido (debe ser >= 0).');
      }
      plan.push({ fila: filaP, precio: it.precio, costo: it.costo });
    });
    // pasada 2: escribir
    plan.forEach(function (paso) {
      if (paso.precio !== undefined && paso.precio !== null && paso.precio !== '')
        hp.getRange(paso.fila, colPrecio + 1).setValue(Number(paso.precio));
      if (paso.costo !== undefined && paso.costo !== null && paso.costo !== '')
        hp.getRange(paso.fila, colCosto + 1).setValue(Number(paso.costo));
      hp.getRange(paso.fila, colFecha + 1).setValue(ahora_());
    });
    log_('precios_actualizados', plan.length + ' productos');
    return json({ ok: true, actualizados: plan.length });
  });

  if (tipo === 'delete_product') return conLock(function () {
    var fila = filaPorId(SHEET_PRODUCTS, data.id);
    if (!fila) throw AdisError('NO_ENCONTRADO', 'Producto no encontrado.');
    var hp = ss().getSheetByName(SHEET_PRODUCTS);
    hp.getRange(fila, 14).setValue('inactivo'); // baja logica, nunca se borra
    hp.getRange(fila, 16).setValue(ahora_());
    log_('producto_desactivado', String(data.id));
    return json({ ok: true });
  });

  if (tipo === 'restore_product') return conLock(function () {
    var filaR = filaPorId(SHEET_PRODUCTS, data.id);
    if (!filaR) throw AdisError('NO_ENCONTRADO', 'Producto no encontrado.');
    var hpr = ss().getSheetByName(SHEET_PRODUCTS);
    hpr.getRange(filaR, 14).setValue('activo');
    hpr.getRange(filaR, 16).setValue(ahora_());
    log_('producto_recuperado', String(data.id));
    return json({ ok: true });
  });

  /* ---------- Importacion masiva (una sola ejecucion bajo lock) ---------- */
  if (tipo === 'import_productos') return conLock(function () {
    if (data.reset) {
      [SHEET_PRODUCTS, SHEET_STOCK, SHEET_MOVES].forEach(function (n) {
        var h = ss().getSheetByName(n);
        if (h) h.clearContents();
      });
      STOCK_SNAP = null;
      hoja(SHEET_PRODUCTS, ENC_PROD);
      hoja(SHEET_STOCK, ['producto_id', 'almacen_id', 'cantidad']);
      hoja(SHEET_MOVES, ENC_MOV);
      log_('reset_base', 'Pestañas de productos/stock/movimientos reiniciadas');
    }
    var himp = hoja(SHEET_PRODUCTS, ENC_PROD);
    var codigosVistos = {};
    var count = 0, errores = [];
    (data.rows || []).forEach(function (r) {
      if (!r.nombre) return;
      var cod = String(r.codigo || '').trim();
      if (!cod) { errores.push('Sin codigo: ' + r.nombre); return; }
      if (codigosVistos[cod.toLowerCase()]) { errores.push('Duplicado en import: ' + cod); return; }
      codigosVistos[cod.toLowerCase()] = true;
      himp.appendRow([nuevoId(), cod, r.nombre, r.descripcion || '', r.categoria || '', r.subcategoria || '',
        r.proveedor || '', Number(r.costo) || 0, Number(r.precio) || 0, r.unidad || 'pieza',
        Number(r.stock_minimo) || 0, r.moneda || 'MXN', r.foto || '', r.estado || 'activo',
        r.notas || '', ahora_()]);
      count++;
    });
    // Stock por almacen: cada existencia inicial es un MOVIMIENTO trazable (doc IMPORTACION)
    var mapaCodigoId = {}, mapaCodigoNom = {};
    himp.getDataRange().getValues().forEach(function (f, i) {
      if (i === 0) return;
      mapaCodigoId[String(f[1]).toLowerCase()] = String(f[0]);
      mapaCodigoNom[String(f[1]).toLowerCase()] = String(f[2]);
    });
    var stockCount = 0;
    (data.stock || []).forEach(function (s) {
      if (!s.codigo || !s.almacen) return;
      var halm = hoja(SHEET_WAREHOUSES, ['id', 'nombre', 'ubicacion', 'activo']);
      var almRows = halm.getDataRange().getValues();
      var almId = null;
      for (var a = 1; a < almRows.length; a++) {
        if (String(almRows[a][1]).toLowerCase() === String(s.almacen).toLowerCase() && String(almRows[a][3]) !== 'no') {
          almId = String(almRows[a][0]); break;
        }
      }
      if (!almId) { almId = nuevoId(); halm.appendRow([almId, s.almacen, '', 'si']); }
      var clave = String(s.codigo).toLowerCase();
      var prodId = mapaCodigoId[clave];
      if (!prodId) { errores.push('Stock sin producto: ' + s.codigo); return; }
      aplicarMovimiento({ tipo: 'ajuste', producto_id: prodId, producto: mapaCodigoNom[clave],
        almacen_id: almId, almacen: s.almacen, cantidad: Number(s.cantidad) || 0,
        moneda: 'MXN', referencia: 'Importación inicial', notas: 'Carga desde Excel',
        doc_tipo: 'IMPORTACION', doc_id: 'INICIAL' });
      stockCount++;
    });
    log_('importacion_masiva', count + ' productos, ' + stockCount + ' existencias');
    return json({ ok: true, importados: count, stock: stockCount, errores: errores });
  });

  /* ---------- Borrado administrativo de una fila (protegido) ---------- */
  if (tipo === 'delete_row') return conLock(function () {
    var nombreHoja = String(data.sheet || '');
    if (HOJAS_BORRABLES.indexOf(nombreHoja) === -1) {
      throw AdisError('NO_PERMITIDO', 'Esta hoja no admite borrado (histórico protegido).');
    }
    var hb = ss().getSheetByName(nombreHoja);
    var filaB = Number(data.row);
    if (!hb || !isFinite(filaB) || filaB <= 1 || filaB > hb.getLastRow()) {
      throw AdisError('NO_ENCONTRADO', 'Fila no encontrada.');
    }
    hb.deleteRow(filaB);
    log_('fila_eliminada', nombreHoja + ' fila ' + filaB);
    return json({ ok: true });
  });

  /* ---------- Almacenes ---------- */
  if (tipo === 'save_almacen') return conLock(function () {
    if (!String(data.nombre || '').trim()) throw AdisError('VALIDACION', 'El almacén necesita nombre.');
    var ha = hoja(SHEET_WAREHOUSES, ['id', 'nombre', 'ubicacion', 'activo']);
    if (data.id) {
      var va = ha.getDataRange().getValues();
      for (var k = 1; k < va.length; k++) {
        if (String(va[k][0]) === String(data.id)) {
          ha.getRange(k + 1, 1, 1, 4).setValues([[data.id, String(data.nombre).trim(), data.ubicacion || '', 'si']]);
          return json({ ok: true, id: data.id });
        }
      }
      throw AdisError('NO_ENCONTRADO', 'Almacén no encontrado.');
    }
    var ida = nuevoId();
    ha.appendRow([ida, String(data.nombre).trim(), data.ubicacion || '', 'si']);
    return json({ ok: true, id: ida });
  });

  if (tipo === 'delete_almacen') return conLock(function () {
    var filaA = filaPorId(SHEET_WAREHOUSES, data.id);
    if (!filaA) throw AdisError('NO_ENCONTRADO', 'Almacén no encontrado.');
    ss().getSheetByName(SHEET_WAREHOUSES).getRange(filaA, 4).setValue('no');
    return json({ ok: true });
  });

  /* ---------- Entrada / salida / ajuste de inventario ---------- */
  if (tipo === 'movimiento') return conLock(function () {
    if (TIPOS_MOVIMIENTO.indexOf(data.tipo_mov) === -1) {
      throw AdisError('TIPO_MOVIMIENTO_INVALIDO', 'Tipo de movimiento no permitido: ' + data.tipo_mov);
    }
    var alm = filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.id) === String(data.almacen_id); })[0] || {};
    if (!alm.id) throw AdisError('NO_ENCONTRADO', 'Almacén no encontrado.');
    var prod = filasComoObjetos(SHEET_PRODUCTS).filter(function (p) { return String(p.id) === String(data.producto_id); })[0] || {};
    if (!prod.id) throw AdisError('NO_ENCONTRADO', 'Producto no encontrado.');
    var cant = Math.abs(Number(data.cantidad));
    if (!isFinite(cant) || cant <= 0) throw AdisError('VALIDACION', 'La cantidad debe ser mayor que cero.');
    var nueva = aplicarMovimiento({
      tipo: data.tipo_mov, producto_id: data.producto_id, producto: prod.nombre,
      almacen_id: data.almacen_id, almacen: alm.nombre, cantidad: cant,
      costo_unit: data.costo_unit || prod.costo || '',
      moneda: validarMoneda(data.moneda || prod.moneda), notas: data.notas || '',
      doc_tipo: 'AJUSTE', doc_id: ''
    });
    log_('movimiento_' + data.tipo_mov, prod.nombre + ' x' + cant + ' en ' + alm.nombre);
    return json({ ok: true, stock_nuevo: nueva });
  });

  /* ---------- Venta (atomica bajo lock + compensacion best-effort) ----------
     Sheets no tiene transacciones ACID: la estrategia es (1) hacer TODA la
     validacion antes de escribir, (2) aplicar movimientos + venta dentro de
     un solo lock, y (3) si algo falla despues de mover stock, revertir cada
     movimiento aplicado (COMPENSACION) y registrarlo en el Log. Limite
     documentado: si la compensacion tambien falla (causa externa, p.ej.
     cuota de Google), el Log queda con 'error_compensacion' para correccion
     manual. */
  if (tipo === 'venta') return conLock(function () {
    var almacenV = filasComoObjetos(SHEET_WAREHOUSES)
      .filter(function (a) { return String(a.id) === String(data.almacen_id); })[0] || {};
    if (!almacenV.id) throw AdisError('VALIDACION', 'Selecciona un almacén válido.');
    var items = data.items || [];
    if (!items.length) throw AdisError('VALIDACION', 'La venta necesita al menos un producto.');

    var prods = filasComoObjetos(SHEET_PRODUCTS);
    var mapaProd = {};
    prods.forEach(function (p) { mapaProd[String(p.id)] = p; });

    // Validacion completa ANTES de tocar nada (incluye agregacion por producto)
    var agregados = {};
    items.forEach(function (it) {
      var p = mapaProd[String(it.producto_id)];
      if (!p) throw AdisError('NO_ENCONTRADO', 'Producto no encontrado: ' + it.producto_id);
      var cant = Number(it.cantidad);
      if (!isFinite(cant) || cant <= 0) throw AdisError('VALIDACION', 'Cantidad inválida para ' + p.nombre + '.');
      agregados[String(p.id)] = (agregados[String(p.id)] || 0) + cant;
    });
    Object.keys(agregados).forEach(function (pid) {
      var disponible = stockSnapDe(pid, data.almacen_id).cantidad;
      if (disponible < agregados[pid]) {
        var nom = (mapaProd[pid] || {}).nombre || pid;
        throw AdisError('STOCK_INSUFICIENTE',
          'Stock insuficiente de "' + nom + '": hay ' + disponible + ', se piden ' + agregados[pid] + '.');
      }
    });

    var fechaV = validarFecha(data.fecha) || hoy_();
    var folioV = siguienteFolio('VEN', 'folio_venta', 4);
    var ventaId = nuevoId();
    var aplicados = [];
    try {
      var total = 0, costoTotal = 0, nombres = [];
      items.forEach(function (it) {
        var p = mapaProd[String(it.producto_id)];
        var precio = Number(it.precio);
        if (!isFinite(precio) || precio < 0) precio = Number(p.precio) || 0;
        var costo = Number(p.costo) || 0;
        var cant = Number(it.cantidad);
        total += precio * cant;
        costoTotal += costo * cant;
        nombres.push(p.nombre + ' x' + cant);
        aplicarMovimiento({ tipo: 'salida', producto_id: p.id, producto: p.nombre,
          almacen_id: data.almacen_id, almacen: almacenV.nombre, cantidad: cant,
          costo_unit: costo, moneda: validarMoneda(data.moneda || 'MXN'),
          referencia: 'Venta ' + folioV, notas: data.cliente || '',
          doc_tipo: 'VENTA', doc_id: folioV });
        aplicados.push({ p: p, cant: cant, costo: costo });
      });
      var tc = Number(data.tipo_cambio) || Number(cfg('tipo_cambio', '18.5')) || 1;
      var monedaV = validarMoneda(data.moneda || cfg('moneda_base', 'MXN'));
      var totalBase = aBase(total, monedaV, tc);
      var costoBase = aBase(costoTotal, monedaV, tc);
      hoja(SHEET_SALES, ENC_VENTAS).appendRow([fechaV, data.cliente || '', almacenV.nombre, nombres.join(' | '),
        total, monedaV, tc, totalBase, costoBase, totalBase - costoBase, data.notas || '',
        ventaId, folioV, USUARIO_ACTUAL]);
      log_('venta_registrada', folioV + ' · ' + (data.cliente || 'mostrador') + ' · ' + items.length + ' items');
      return json({ ok: true, id: ventaId, folio: folioV, total: total, utilidad: totalBase - costoBase });
    } catch (errV) {
      // Compensacion: revertir el stock movido para no dejar venta a medias.
      aplicados.forEach(function (a) {
        try {
          aplicarMovimiento({ tipo: 'entrada', producto_id: a.p.id, producto: a.p.nombre,
            almacen_id: data.almacen_id, almacen: almacenV.nombre, cantidad: a.cant,
            costo_unit: a.costo, moneda: validarMoneda(data.moneda || 'MXN'),
            referencia: 'Reversión ' + folioV, notas: 'Compensación por error al registrar la venta',
            doc_tipo: 'COMPENSACION', doc_id: folioV });
        } catch (eC) {
          log_('error_compensacion', folioV + ' · ' + String((eC && eC.message) || eC).slice(0, 200));
        }
      });
      throw errV;
    }
  });

  /* ---------- Gasto ---------- */
  if (tipo === 'gasto') return conLock(function () {
    var categoria = String(data.categoria || '').trim();
    if (!categoria) throw AdisError('VALIDACION', 'El gasto necesita una categoría.');
    var monto = Number(data.monto);
    if (!isFinite(monto) || monto <= 0) throw AdisError('VALIDACION', 'El monto debe ser mayor que cero.');
    var monedaG = validarMoneda(data.moneda || cfg('moneda_base', 'MXN'));
    var tcg = Number(data.tipo_cambio) || Number(cfg('tipo_cambio', '18.5')) || 1;
    var fechaG = validarFecha(data.fecha) || hoy_();
    hoja(SHEET_EXPENSES, ENC_GASTOS).appendRow([fechaG, categoria, data.descripcion || '',
      monto, monedaG, tcg, aBase(monto, monedaG, tcg), nuevoId(), USUARIO_ACTUAL]);
    log_('gasto_registrado', categoria + ' - ' + monto + ' ' + monedaG);
    return json({ ok: true });
  });

  if (tipo === 'delete_gasto') return conLock(function () {
    var filaG = filaPorId(SHEET_EXPENSES, data.id);
    if (!filaG && Number(data.row) > 1) { // compatibilidad temporal con frontend viejo
      var hg0 = ss().getSheetByName(SHEET_EXPENSES);
      if (hg0 && Number(data.row) <= hg0.getLastRow()) filaG = Number(data.row);
    }
    if (!filaG) throw AdisError('NO_ENCONTRADO', 'Gasto no encontrado.');
    ss().getSheetByName(SHEET_EXPENSES).deleteRow(filaG);
    log_('gasto_eliminado', 'id=' + (data.id || '') + ' fila=' + filaG);
    return json({ ok: true });
  });

  throw AdisError('TIPO_DESCONOCIDO', 'Tipo desconocido: ' + tipo);
}

/* ---------- Tracking protegido (anti-abuso + retencion con archivo) ----------
   Defensas: rate-limit por huella (120 eventos / 10 min), deduplicacion de
   eventos repetidos (45 s) y, al superar el tope de filas activas, el
   excedente se MUEVE a Visitas_Archivo (historial preservado, nunca borrado). */
function trackProtegido(data) {
  var cache = CacheService.getScriptCache();
  var fp = digestHex(String(data.ua || '') + '|' + String(data.idioma || '') + '|' + String(data.ancho || ''));

  var rl = Number(cache.get('trk_rl_' + fp)) || 0;
  if (rl >= 120) return { ok: true }; // se descarta silenciosamente (anti-abuso)
  cache.put('trk_rl_' + fp, String(rl + 1), 600);

  var dedup = 'trk_dp_' + digestHex(String(data.pagina || '') + '|' + String(data.seccion || '') + '|' + fp);
  if (cache.get(dedup)) return { ok: true };
  cache.put(dedup, '1', 45);

  var pagina = String(data.pagina || '').slice(0, 180);
  var seccion = String(data.seccion || '').slice(0, 120);
  if (!pagina && !seccion) return { ok: true }; // evento vacio, no ocupa fila

  return conLock(function () {
    hoja(SHEET_VISITS, ENC_VISITS).appendRow([
      hoy_(),
      Utilities.formatDate(new Date(), 'America/Hermosillo', 'HH:mm'),
      pagina,
      seccion,
      origenDe_(data.referrer),
      String(data.referrer || '').slice(0, 180),
      String(data.idioma || '').slice(0, 20),
      dispositivoDe_(data.ua),
      navegadorDe_(data.ua),
      Number(data.ancho) || 0,
      String(data.ua || '').slice(0, 200)
    ]);
    // Retencion: el excedente se ARCHIVA (no se borra historial)
    var hV = ss().getSheetByName(SHEET_VISITS);
    var last = hV ? hV.getLastRow() : 0;
    if (last > VISITS_MAX_FILAS + 1) {
      var excedente = last - VISITS_MAX_FILAS - 1;
      var valores = hV.getRange(2, 1, excedente, hV.getLastColumn()).getValues();
      var arch = hoja(SHEET_VISITS_ARCHIVE, ENC_VISITS);
      arch.getRange(arch.getLastRow() + 1, 1, valores.length, valores[0].length).setValues(valores);
      hV.deleteRows(2, excedente);
      log_('visitas_archivadas', excedente + ' filas movidas a ' + SHEET_VISITS_ARCHIVE);
    }
    return { ok: true };
  });
}
