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
var SHEET_PROVIDERS  = 'Proveedores';
var SHEET_CLIENTS    = 'Clientes';
var SHEET_PROJECTS   = 'Proyectos';
var SHEET_COBROS     = 'Cobros';
var SHEET_PAGOS      = 'Pagos';
var SHEET_PROY_MOVS  = 'Proyectos_Movs';
var SHEET_PO         = 'OrdenesCompra';
var SHEET_RECEP      = 'Recepciones';
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
  'folio', 'proyecto', 'ubicacion', 'moneda', 'subtotal', 'iva', 'estado', 'datos', 'id', 'usuario', 'cliente_id'];
var ENC_PROD = ['id', 'codigo', 'nombre', 'descripcion', 'categoria', 'subcategoria', 'proveedor',
  'costo', 'precio', 'unidad', 'stock_minimo', 'moneda', 'foto', 'estado', 'notas', 'fecha_actualizacion'];
var ENC_MOV = ['fecha', 'tipo', 'producto_id', 'producto', 'almacen_id', 'almacen', 'cantidad',
  'costo_unit', 'moneda', 'referencia', 'notas',
  'id', 'usuario', 'existencia_anterior', 'existencia_posterior', 'documento_tipo', 'documento_id'];
var ENC_VENTAS = ['fecha', 'cliente', 'almacen', 'items', 'total', 'moneda', 'tipo_cambio',
  'total_base', 'costo_total_base', 'utilidad_base', 'notas', 'id', 'folio', 'usuario',
  'cliente_id', 'proyecto_id', 'estado_pago', 'almacen_id', 'items_json'];
var ENC_GASTOS = ['fecha', 'categoria', 'descripcion', 'monto', 'moneda', 'tipo_cambio', 'monto_base',
  'id', 'usuario', 'folio', 'estado', 'pagado'];
var ENC_PAGOS = ['id', 'folio', 'gasto_id', 'gasto_folio', 'categoria', 'fecha', 'monto', 'moneda',
  'monto_base', 'metodo', 'notas', 'usuario'];
var ENC_PROY_MOVS = ['id', 'proyecto_id', 'tipo', 'monto', 'moneda', 'tipo_cambio', 'monto_base',
  'fecha', 'descripcion', 'usuario'];
var ENC_RESENAS = ['fecha', 'nombre', 'estrellas', 'texto', 'activa', 'id', 'usuario'];
var ENC_PROV = ['id', 'nombre', 'contacto', 'telefono', 'email', 'direccion', 'notas', 'activo', 'fecha'];
var ENC_CLIENTES = ['id', 'nombre', 'telefono', 'email', 'ciudad', 'direccion', 'notas', 'origen', 'fecha', 'activo'];
var ENC_PROY = ['id', 'folio', 'nombre', 'cliente_id', 'cliente', 'cotizacion_id', 'cotizacion_folio',
  'ubicacion', 'fecha_inicio', 'fecha_fin', 'presupuesto', 'moneda', 'estado', 'notas', 'usuario', 'fecha_actualizacion'];
var ENC_COBROS = ['id', 'folio', 'venta_id', 'venta_folio', 'cliente', 'proyecto_id', 'fecha', 'monto',
  'moneda', 'monto_base', 'metodo', 'notas', 'usuario'];
var ENC_OC = ['id', 'folio', 'proveedor_id', 'proveedor', 'fecha', 'fecha_esperada', 'almacen_id', 'almacen',
  'moneda', 'subtotal', 'iva', 'descuento', 'total', 'estado', 'notas', 'usuario', 'fecha_actualizacion', 'partidas'];
var ENC_RECEP = ['id', 'oc_id', 'oc_folio', 'fecha', 'items', 'usuario'];
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
    var proyFiltro = String(e.parameter.proyecto_id || '');
    var ventas = filasComoObjetos(SHEET_SALES).filter(function (v) {
      if (String(v.estado_pago) === 'CANCELADA') return false; // FASE 6: las anuladas no son ingreso
      if (proyFiltro && String(v.proyecto_id) !== proyFiltro) return false;
      return enRango(v.fecha);
    });
    var gastos;
    if (proyFiltro) { // FASE 6: en vista por proyecto, los gastos son los movimientos tipo 'gasto' del proyecto
      gastos = filasComoObjetos('Proyectos_Movs').filter(function (m) {
        return String(m.proyecto_id) === proyFiltro && String(m.tipo) === 'gasto' && enRango(m.fecha);
      }).map(function (m) {
        return { categoria: String(m.descripcion || 'Gasto de proyecto').slice(0, 40), monto_base: Number(m.monto_base) || 0, estado: 'ACTIVA' };
      });
    } else {
      gastos = filasComoObjetos(SHEET_EXPENSES).filter(function (g) {
        return enRango(g.fecha) && String(g.estado) !== 'CANCELADA';
      });
    }
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
      proyecto_id: proyFiltro || '',
      ingresos: ingresos, costos: costos, utilidad_bruta: utilBruta,
      gastos: porCategoria, total_gastos: totalGastos, utilidad_neta: utilNeta,
      utilidad_operativa: utilNeta, // FASE 6: gastos operativos ya descontados
      num_ventas: ventas.length,
      margen_bruto: ingresos ? (utilBruta / ingresos * 100) : 0,
      margen_neto: ingresos ? (utilNeta / ingresos * 100) : 0,
      margen_operativo: ingresos ? (utilNeta / ingresos * 100) : 0 });
  }

  // FASE 6: alertas priorizadas del negocio (stock, cobros, pagos, cotizaciones, compras)
  if (action === 'alertas') {
    var alertas = [];
    var stockA = filasComoObjetos(SHEET_STOCK);
    var productosA = filasComoObjetos(SHEET_PRODUCTS);
    var existencias = {};
    stockA.forEach(function (s) {
      var k = String(s.producto_id);
      existencias[k] = (existencias[k] || 0) + (Number(s.cantidad) || 0);
    });
    productosA.forEach(function (p) {
      if (String(p.estado) === 'inactivo') return;
      var ex = existencias[String(p.id)] || 0;
      var min = Number(p.stock_minimo) || 0;
      if (ex < 0) alertas.push({ prioridad: 'CRITICA', tipo: 'stock_negativo', detalle: p.nombre + ': existencia ' + ex + ' (revisar movimientos)' });
      else if (min > 0 && ex <= min) alertas.push({ prioridad: 'ALTA', tipo: 'stock_bajo', detalle: p.nombre + ': ' + ex + ' en existencia (mínimo ' + min + ')' });
      else if (ex === 0) alertas.push({ prioridad: 'ALTA', tipo: 'stock_cero', detalle: p.nombre + ': sin existencia' });
      if (!(Number(p.precio) > 0)) alertas.push({ prioridad: 'ALTA', tipo: 'sin_precio', detalle: p.nombre + ': sin precio de venta' });
      if (!(Number(p.costo) > 0)) alertas.push({ prioridad: 'MEDIA', tipo: 'sin_costo', detalle: p.nombre + ': sin costo (la utilidad no se calcula bien)' });
    });
    var hace30 = Utilities.formatDate(new Date(Date.now() - 30 * 864e5), 'America/Hermosillo', 'yyyy-MM-dd');
    var cobrosA = filasComoObjetos(SHEET_COBROS);
    filasComoObjetos(SHEET_SALES).forEach(function (v) {
      if (String(v.estado_pago) === 'CANCELADA' || !v.id) return;
      var cobrado = 0;
      cobrosA.forEach(function (c) { if (String(c.venta_id) === String(v.id)) cobrado += Number(c.monto_base) || 0; });
      var totalV = Number(v.total_base) || 0;
      if (totalV - cobrado > 0.001 && String(v.fecha).slice(0, 10) < hace30)
        alertas.push({ prioridad: 'ALTA', tipo: 'cxc_vencida', detalle: 'Venta ' + (v.folio || '') + ' · ' + (v.cliente || '') + ': saldo ' + (totalV - cobrado).toFixed(2) + ' desde ' + String(v.fecha).slice(0, 10) });
    });
    var pagosA = filasComoObjetos(SHEET_PAGOS);
    filasComoObjetos(SHEET_EXPENSES).forEach(function (g) {
      if (String(g.estado) === 'CANCELADA' || !g.id) return;
      var pagado = 0;
      pagosA.forEach(function (p) { if (String(p.gasto_id) === String(g.id)) pagado += Number(p.monto_base) || 0; });
      var totalG = Number(g.monto_base) || 0;
      if (totalG - pagado > 0.001 && String(g.fecha).slice(0, 10) < hace30)
        alertas.push({ prioridad: 'MEDIA', tipo: 'cxp_vencida', detalle: 'Gasto ' + (g.folio || '') + ' · ' + (g.categoria || '') + ': saldo ' + (totalG - pagado).toFixed(2) + ' desde ' + String(g.fecha).slice(0, 10) });
    });
    filasComoObjetos(SHEET_QUOTES).forEach(function (q) {
      if (String(q.estado) === 'Pendiente' && String(q.fecha).slice(0, 10) < hace30)
        alertas.push({ prioridad: 'MEDIA', tipo: 'quote_vieja', detalle: 'Cotización ' + (q.folio || '') + ' · ' + (q.cliente || '') + ' sigue Pendiente desde ' + String(q.fecha).slice(0, 10) });
    });
    filasComoObjetos(SHEET_PO).forEach(function (oc) {
      var stOC = String(oc.estado);
      if (stOC === 'ENVIADA' || stOC === 'AUTORIZADA' || stOC === 'PARCIAL')
        alertas.push({ prioridad: 'MEDIA', tipo: 'oc_por_recibir', detalle: 'OC ' + (oc.folio || '') + ' · ' + (oc.proveedor || '') + ': estado ' + stOC });
    });
    var pesoAlerta = { CRITICA: 0, ALTA: 1, MEDIA: 2 };
    alertas.sort(function (a, b) { return pesoAlerta[a.prioridad] - pesoAlerta[b.prioridad]; });
    return json({ ok: true, alertas: alertas, hoy: hoy_() });
  }

  if (action === 'clientes') {
    return json({ ok: true, clientes: filasComoObjetos(SHEET_CLIENTS).filter(function (c) { return String(c.activo) !== 'no'; }) });
  }
  if (action === 'proveedores') {
    return json({ ok: true, proveedores: filasComoObjetos(SHEET_PROVIDERS).filter(function (p) { return String(p.activo) !== 'no'; }) });
  }
  if (action === 'oc') {
    var listaOC = filasComoObjetos(SHEET_PO);
    var receps = filasComoObjetos(SHEET_RECEP);
    var recibidoPorOC = {};
    receps.forEach(function (r) {
      var its = [];
      try { its = JSON.parse(r.items || '[]'); } catch (e) {}
      its.forEach(function (it) {
        var k = String(r.oc_id) + '|' + String(it.producto_id);
        recibidoPorOC[k] = (recibidoPorOC[k] || 0) + (Number(it.cantidad) || 0);
      });
    });
    listaOC = listaOC.map(function (oc) {
      var partidas = [];
      try { partidas = JSON.parse(oc.partidas || '[]'); } catch (e) {}
      partidas = partidas.map(function (pt) {
        var rec = recibidoPorOC[String(oc.id) + '|' + String(pt.producto_id)] || 0;
        return { producto_id: pt.producto_id, producto: pt.producto, cantidad: pt.cantidad,
          costo_unit: pt.costo_unit, recibido: rec, pendiente: Math.max(0, (Number(pt.cantidad) || 0) - rec) };
      });
      return { id: oc.id, folio: oc.folio, proveedor_id: oc.proveedor_id, proveedor: oc.proveedor,
        fecha: oc.fecha, fecha_esperada: oc.fecha_esperada, almacen_id: oc.almacen_id, almacen: oc.almacen,
        moneda: oc.moneda, subtotal: Number(oc.subtotal) || 0, iva: Number(oc.iva) || 0,
        descuento: Number(oc.descuento) || 0, total: Number(oc.total) || 0, estado: oc.estado,
        notas: oc.notas, partidas: partidas };
    });
    return json({ ok: true, oc: listaOC });
  }

  if (action === 'proyectos') {
    var movsProyectos = filasComoObjetos(SHEET_PROY_MOVS);
    var listaProy = filasComoObjetos(SHEET_PROJECTS).map(function (p) {
      // cobrado del proyecto = cobros de ventas vinculadas
      var cobrado = 0, cobradoBase = 0;
      var ventasProy = filasComoObjetos(SHEET_SALES).filter(function (v) { return String(v.proyecto_id) === String(p.id) && String(v.estado_pago) !== 'CANCELADA'; });
      var cobros = filasComoObjetos(SHEET_COBROS);
      ventasProy.forEach(function (v) {
        cobros.forEach(function (c) {
          if (String(c.venta_id) === String(v.id)) { cobrado += Number(c.monto) || 0; cobradoBase += Number(c.monto_base) || 0; }
        });
      });
      // FASE 6: gastos/ingresos directos del proyecto (Proyectos_Movs)
      var gastosProy = 0, ingresosProy = 0;
      movsProyectos.forEach(function (m) {
        if (String(m.proyecto_id) !== String(p.id)) return;
        if (String(m.tipo) === 'gasto') gastosProy += Number(m.monto_base) || 0;
        if (String(m.tipo) === 'ingreso') ingresosProy += Number(m.monto_base) || 0;
      });
      return { id: p.id, folio: p.folio, nombre: p.nombre, cliente_id: p.cliente_id, cliente: p.cliente,
        cotizacion_id: p.cotizacion_id, cotizacion_folio: p.cotizacion_folio, ubicacion: p.ubicacion,
        fecha_inicio: p.fecha_inicio, fecha_fin: p.fecha_fin, presupuesto: Number(p.presupuesto) || 0,
        moneda: p.moneda, estado: p.estado, notas: p.notas, ventas_count: ventasProy.length,
        cobrado: cobrado, cobrado_base: cobradoBase,
        gastos_real: gastosProy, ingresos_extra: ingresosProy,
        utilidad_real: cobradoBase + ingresosProy - gastosProy };
    });
    return json({ ok: true, proyectos: listaProy });
  }
  if (action === 'cxc') { // cuentas por cobrar: ventas (no canceladas) vs cobros reales
    var ventasCx = filasComoObjetos(SHEET_SALES).filter(function (v) { return String(v.estado_pago) !== 'CANCELADA' && v.id; });
    var cobrosCx = filasComoObjetos(SHEET_COBROS);
    var cxc = ventasCx.map(function (v) {
      var cobrado = 0, cobradoBase = 0, ultimoCobro = '';
      cobrosCx.forEach(function (c) {
        if (String(c.venta_id) === String(v.id)) {
          cobrado += Number(c.monto) || 0; cobradoBase += Number(c.monto_base) || 0;
          if (String(c.fecha) > ultimoCobro) ultimoCobro = String(c.fecha);
        }
      });
      var total = Number(v.total) || 0, totalBase = Number(v.total_base) || 0;
      return { venta_id: v.id, folio: v.folio, fecha: v.fecha, cliente: v.cliente, moneda: v.moneda,
        total: total, cobrado: cobrado, saldo: Math.max(0, total - cobrado),
        total_base: totalBase, cobrado_base: cobradoBase, saldo_base: Math.max(0, totalBase - cobradoBase),
        estado_pago: v.estado_pago || (cobrado >= total && total > 0 ? 'PAGADA' : (cobrado > 0 ? 'PARCIAL' : 'PENDIENTE')),
        ultimo_cobro: ultimoCobro, proyecto_id: v.proyecto_id || '' };
    });
    var porCobrar = cxc.reduce(function (s, x) { return s + x.saldo_base; }, 0);
    return json({ ok: true, cxc: cxc, por_cobrar_base: porCobrar, moneda_base: cfg('moneda_base', 'MXN'),
      cobros: cobrosCx.slice(-100).reverse() });
  }

  if (action === 'pagos') {
    return json({ ok: true, pagos: filasComoObjetos(SHEET_PAGOS).slice(-200).reverse(),
      moneda_base: cfg('moneda_base', 'MXN') });
  }
  if (action === 'cxp') { // cuentas por pagar: gastos (no cancelados) vs pagos reales
    var gastosCp = filasComoObjetos(SHEET_EXPENSES).filter(function (g) { return g.id && String(g.estado) !== 'CANCELADA'; });
    var pagosCp = filasComoObjetos(SHEET_PAGOS);
    var cxp = gastosCp.map(function (g) {
      var pagadoP = 0, pagadoBaseP = 0, ultimoPago = '';
      pagosCp.forEach(function (p) {
        if (String(p.gasto_id) === String(g.id)) {
          pagadoP += Number(p.monto) || 0; pagadoBaseP += Number(p.monto_base) || 0;
          if (String(p.fecha) > ultimoPago) ultimoPago = String(p.fecha);
        }
      });
      var totalCp = Number(g.monto) || 0, totalBaseCp = Number(g.monto_base) || 0;
      return { gasto_id: g.id, folio: g.folio, fecha: g.fecha, categoria: g.categoria,
        descripcion: g.descripcion || '', moneda: g.moneda, total: totalCp, pagado: pagadoP,
        saldo: Math.max(0, totalCp - pagadoP), total_base: totalBaseCp, pagado_base: pagadoBaseP,
        saldo_base: Math.max(0, totalBaseCp - pagadoBaseP), estado: g.estado || 'ACTIVA',
        estado_pago: (pagadoBaseP >= totalBaseCp - 0.001 && totalBaseCp > 0) ? 'PAGADA' : (pagadoBaseP > 0 ? 'PARCIAL' : 'PENDIENTE'),
        ultimo_pago: ultimoPago };
    });
    var porPagar = cxp.reduce(function (s, x) { return s + x.saldo_base; }, 0);
    return json({ ok: true, cxp: cxp, por_pagar_base: porPagar, moneda_base: cfg('moneda_base', 'MXN'),
      pagos: pagosCp.slice(-100).reverse() });
  }
  if (action === 'flujo_caja') { // FASE 5: efectivo REAL = cobros entrados - pagos salidos
    var desdeFc = String(params.desde || ''), hastaFc = String(params.hasta || '');
    if (!desdeFc || !hastaFc) {
      var ahoraFc = new Date();
      var yFc = ahoraFc.getFullYear(), mFc = ahoraFc.getMonth() + 1;
      desdeFc = yFc + '-' + (mFc < 10 ? '0' : '') + mFc + '-01';
      hastaFc = Utilities.formatDate(ahoraFc, 'America/Hermosillo', 'yyyy-MM-dd');
    }
    var enRangoFc = function (fecha) { var f = String(fecha).slice(0, 10); return f >= desdeFc && f <= hastaFc; };
    var cobrosFc = filasComoObjetos(SHEET_COBROS).filter(function (c) { return enRangoFc(c.fecha); });
    var pagosFc = filasComoObjetos(SHEET_PAGOS).filter(function (p) { return enRangoFc(p.fecha); });
    var porDiaFc = {};
    cobrosFc.forEach(function (c) {
      var f = String(c.fecha).slice(0, 10);
      porDiaFc[f] = porDiaFc[f] || { fecha: f, entradas: 0, salidas: 0 };
      porDiaFc[f].entradas += Number(c.monto_base) || 0;
    });
    pagosFc.forEach(function (p) {
      var f = String(p.fecha).slice(0, 10);
      porDiaFc[f] = porDiaFc[f] || { fecha: f, entradas: 0, salidas: 0 };
      porDiaFc[f].salidas += Number(p.monto_base) || 0;
    });
    var diasFc = Object.keys(porDiaFc).sort().map(function (k) { return porDiaFc[k]; });
    var entradasFc = cobrosFc.reduce(function (s, c) { return s + (Number(c.monto_base) || 0); }, 0);
    var salidasFc = pagosFc.reduce(function (s, p) { return s + (Number(p.monto_base) || 0); }, 0);
    var movsFc = cobrosFc.map(function (c) {
      return { tipo: 'entrada', fecha: c.fecha, folio: c.folio || '',
        concepto: (c.cliente || '') + (c.venta_folio ? ' · ' + c.venta_folio : ''),
        monto_base: Number(c.monto_base) || 0, metodo: c.metodo || '' };
    }).concat(pagosFc.map(function (p) {
      return { tipo: 'salida', fecha: p.fecha, folio: p.folio || '',
        concepto: (p.categoria || '') + (p.gasto_folio ? ' · ' + p.gasto_folio : ''),
        monto_base: Number(p.monto_base) || 0, metodo: p.metodo || '' };
    })).sort(function (a, b) { return String(a.fecha) < String(b.fecha) ? 1 : -1; }).slice(0, 100);
    return json({ ok: true, desde: desdeFc, hasta: hastaFc, moneda_base: cfg('moneda_base', 'MXN'),
      entradas: entradasFc, salidas: salidasFc, neto: entradasFc - salidasFc,
      num_cobros: cobrosFc.length, num_pagos: pagosFc.length, dias: diasFc, movimientos: movsFc });
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
      JSON.stringify(data.datos || {}), nuevoId(), USUARIO_ACTUAL, data.cliente_id || '']);
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
    // FASE 4: vinculos opcionales con cliente y proyecto (validados)
    var clienteIdV = data.cliente_id ? String(data.cliente_id) : '';
    if (clienteIdV && !filaPorId(SHEET_CLIENTS, clienteIdV)) throw AdisError('NO_ENCONTRADO', 'Cliente no encontrado.');
    var proyectoIdV = data.proyecto_id ? String(data.proyecto_id) : '';
    if (proyectoIdV && !filaPorId(SHEET_PROJECTS, proyectoIdV)) throw AdisError('NO_ENCONTRADO', 'Proyecto no encontrado.');
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
        ventaId, folioV, USUARIO_ACTUAL, clienteIdV, proyectoIdV, 'PENDIENTE', String(data.almacen_id),
        JSON.stringify(items.map(function (it2) {
          var p2 = mapaProd[String(it2.producto_id)] || {};
          return { producto_id: p2.id || it2.producto_id, producto: p2.nombre || '', cantidad: Number(it2.cantidad) || 0 };
        }))]);
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
    var folioG = siguienteFolio('GAS', 'folio_gasto', 4);
    hoja(SHEET_EXPENSES, ENC_GASTOS).appendRow([fechaG, categoria, data.descripcion || '',
      monto, monedaG, tcg, aBase(monto, monedaG, tcg), nuevoId(), USUARIO_ACTUAL, folioG, 'ACTIVA', 0]);
    log_('gasto_registrado', folioG + ' · ' + categoria + ' - ' + monto + ' ' + monedaG);
    return json({ ok: true, folio: folioG });
  });

  // FASE 5: pago parcial/total de un gasto (gasto != pago; flujo de efectivo real)
  if (tipo === 'gasto_pago' || tipo === 'registrar_pago') return conLock(function () {
    var filaGP = filaPorId(SHEET_EXPENSES, data.gasto_id);
    if (!filaGP) throw AdisError('NO_ENCONTRADO', 'Gasto no encontrado.');
    var hGP = ss().getSheetByName(SHEET_EXPENSES);
    var estadoGP = String(hGP.getRange(filaGP, 11).getValue()) || 'ACTIVA';
    if (estadoGP === 'CANCELADA') throw AdisError('NO_PERMITIDO', 'El gasto está cancelado; no admite pagos.');
    var folioGP = String(hGP.getRange(filaGP, 10).getValue()) || '';
    var monedaGP = String(hGP.getRange(filaGP, 5).getValue()) || 'MXN';
    var tcgGP = Number(hGP.getRange(filaGP, 6).getValue()) || 1;
    var montoP = Number(data.monto);
    if (!isFinite(montoP) || montoP <= 0) throw AdisError('VALIDACION', 'El monto del pago debe ser mayor que cero.');
    var monedaP = validarMoneda(data.moneda || monedaGP);
    var tcP = Number(data.tipo_cambio) || Number(cfg('tipo_cambio', '18.5')) || 1;
    var pagadoPrev = 0, pagadoPrevBase = 0;
    filasComoObjetos(SHEET_PAGOS).forEach(function (p) {
      if (String(p.gasto_id) === String(data.gasto_id)) {
        pagadoPrevBase += Number(p.monto_base) || 0;
        if (String(p.moneda) === monedaGP) pagadoPrev += Number(p.monto) || 0;
      }
    });
    var totalBaseGP = Number(hGP.getRange(filaGP, 7).getValue()) || 0;
    var montoBaseP = aBase(montoP, monedaP, tcP);
    if (pagadoPrevBase + montoBaseP > totalBaseGP + 0.001) {
      throw AdisError('VALIDACION', 'El pago excede el saldo pendiente del gasto ' + folioGP + '.');
    }
    var folioP = siguienteFolio('PAG', 'folio_pago', 4);
    hoja(SHEET_PAGOS, ENC_PAGOS).appendRow([nuevoId(), folioP, String(data.gasto_id), folioGP,
      String(hGP.getRange(filaGP, 2).getValue()), validarFecha(data.fecha) || hoy_(),
      montoP, monedaP, montoBaseP, data.metodo || '', data.notas || '', USUARIO_ACTUAL]);
    // columna pagado en la moneda del gasto (si el pago es en otra moneda, equivalente aproximado)
    var sumaPagado = pagadoPrev + (String(monedaP) === monedaGP ? montoP : (tcgGP ? montoBaseP / tcgGP : montoBaseP));
    hGP.getRange(filaGP, 12).setValue(Math.round(sumaPagado * 100) / 100);
    var estadoPagoGP = (pagadoPrevBase + montoBaseP >= totalBaseGP - 0.001 && totalBaseGP > 0) ? 'PAGADA' : 'PARCIAL';
    log_('pago_registrado', folioP + ' · ' + folioGP + ' · ' + montoP + ' ' + monedaP + ' · ' + estadoPagoGP);
    return json({ ok: true, folio: folioP, estado_pago: estadoPagoGP });
  });

  // FASE 5: cancelar gasto (baja logica; nunca borrado fisico ni con pagos)
  if (tipo === 'gasto_cancelar') return conLock(function () {
    var filaGC = filaPorId(SHEET_EXPENSES, data.id);
    if (!filaGC) throw AdisError('NO_ENCONTRADO', 'Gasto no encontrado.');
    var hGC = ss().getSheetByName(SHEET_EXPENSES);
    if (String(hGC.getRange(filaGC, 11).getValue()) === 'CANCELADA') return json({ ok: true, ya_cancelada: true });
    var pagadoGC = 0;
    filasComoObjetos(SHEET_PAGOS).forEach(function (p) {
      if (String(p.gasto_id) === String(data.id)) pagadoGC += Number(p.monto_base) || 0;
    });
    if (pagadoGC > 0.001) throw AdisError('NO_PERMITIDO', 'El gasto tiene pagos registrados; no puede cancelarse (los pagos son efectivo ya salido).');
    hGC.getRange(filaGC, 11).setValue('CANCELADA');
    log_('gasto_cancelado', 'id=' + (data.id || ''));
    return json({ ok: true });
  });

  // FASE 5: delete_gasto queda como alias de CANCELAR (baja logica trazable, no fisica)
  if (tipo === 'delete_gasto') return conLock(function () {
    var filaG = filaPorId(SHEET_EXPENSES, data.id);
    if (!filaG && Number(data.row) > 1) { // compatibilidad temporal con frontend viejo
      var hg0 = ss().getSheetByName(SHEET_EXPENSES);
      if (hg0 && Number(data.row) <= hg0.getLastRow()) {
        // validar que la fila legacy corresponde al id enviado (o no hay id)
        var idFila = String(hg0.getRange(Number(data.row), 8).getValue() || '');
        if (!data.id || idFila === String(data.id)) filaG = Number(data.row);
      }
    }
    if (!filaG) throw AdisError('NO_ENCONTRADO', 'Gasto no encontrado.');
    var hGx = ss().getSheetByName(SHEET_EXPENSES);
    if (String(hGx.getRange(filaG, 11).getValue()) === 'CANCELADA') return json({ ok: true, ya_cancelada: true });
    var pagadoG = 0;
    filasComoObjetos(SHEET_PAGOS).forEach(function (p) {
      if (String(p.gasto_id) === String(data.id)) pagadoG += Number(p.monto_base) || 0;
    });
    if (pagadoG > 0.001) throw AdisError('NO_PERMITIDO', 'El gasto tiene pagos registrados; no puede cancelarse.');
    hGx.getRange(filaG, 11).setValue('CANCELADA');
    log_('gasto_cancelado', 'id=' + (data.id || '') + ' (via delete_gasto)');
    return json({ ok: true, cancelada: true });
  });

  /* ---------- Clientes (FASE 3) ---------- */
  if (tipo === 'save_cliente') return conLock(function () {
    var nombreC = String(data.nombre || '').trim();
    if (!nombreC) throw AdisError('VALIDACION', 'El cliente necesita nombre.');
    var telC = String(data.telefono || '').trim();
    var hc = hoja(SHEET_CLIENTS, ENC_CLIENTES);
    if (data.id) {
      var filaC = filaPorId(SHEET_CLIENTS, data.id);
      if (!filaC) throw AdisError('NO_ENCONTRADO', 'Cliente no encontrado.');
      hc.getRange(filaC, 1, 1, ENC_CLIENTES.length).setValues([[data.id, nombreC, telC, data.email || '',
        data.ciudad || '', data.direccion || '', data.notas || '', 'manual', ahora_(), 'si']]);
      log_('cliente_editado', nombreC);
      return json({ ok: true, id: data.id });
    }
    // dedup por telefono entre clientes activos (mismo telefono = mismo cliente)
    if (telC) {
      var existentes = filasComoObjetos(SHEET_CLIENTS);
      for (var ic = 0; ic < existentes.length; ic++) {
        if (String(existentes[ic].activo) !== 'no' && String(existentes[ic].telefono) === telC) {
          throw AdisError('CLIENTE_DUPLICADO', 'Ya existe un cliente con ese teléfono: ' + existentes[ic].nombre);
        }
      }
    }
    var idC = nuevoId();
    hc.appendRow([idC, nombreC, telC, data.email || '', data.ciudad || '', data.direccion || '',
      data.notas || '', data.origen === 'lead' ? 'lead' : 'manual', ahora_(), 'si']);
    log_('cliente_creado', nombreC + (telC ? ' · ' + telC : ''));
    return json({ ok: true, id: idC });
  });

  if (tipo === 'delete_cliente') return conLock(function () {
    var filaDC = filaPorId(SHEET_CLIENTS, data.id);
    if (!filaDC) throw AdisError('NO_ENCONTRADO', 'Cliente no encontrado.');
    ss().getSheetByName(SHEET_CLIENTS).getRange(filaDC, 10).setValue('no');
    log_('cliente_desactivado', String(data.id));
    return json({ ok: true });
  });

  // Estados de cotizacion: Activa -> Aprobada/Vencida/Cancelada; Aprobada -> Vencida
  if (tipo === 'set_estado_quote') return conLock(function () {
    var transQ = { Activa: ['Aprobada', 'Vencida', 'Cancelada'], Aprobada: ['Vencida'], Vencida: [], Cancelada: [] };
    var filaQ = filaPorId(SHEET_QUOTES, data.id);
    if (!filaQ) throw AdisError('NO_ENCONTRADO', 'Cotización no encontrada (solo las nuevas tienen ID estable).');
    var hQ = ss().getSheetByName(SHEET_QUOTES);
    var encQ = hQ.getRange(1, 1, 1, hQ.getLastColumn()).getValues()[0].map(String);
    var colEstado = encQ.indexOf('estado');
    var estadoQ = String(hQ.getRange(filaQ, colEstado + 1).getValue()) || 'Activa';
    var nuevoQ = String(data.estado || '');
    if ((transQ[estadoQ] || []).indexOf(nuevoQ) === -1) {
      throw AdisError('NO_PERMITIDO', 'No se puede pasar de ' + estadoQ + ' a ' + nuevoQ + '.');
    }
    hQ.getRange(filaQ, colEstado + 1).setValue(nuevoQ);
    log_('cotizacion_estado', String(hQ.getRange(filaQ, 8).getValue()) + ': ' + estadoQ + ' -> ' + nuevoQ);
    return json({ ok: true, estado: nuevoQ });
  });

  /* ================= PROYECTOS + COBROS (FASE 4) ================= */

  // FASE 6: movimiento financiero directo de un proyecto (gasto/ingreso/presupuesto)
  if (tipo === 'proyecto_mov') return conLock(function () {
    var filaPM = filaPorId(SHEET_PROJECTS, data.proyecto_id);
    if (!filaPM) throw AdisError('NO_ENCONTRADO', 'Proyecto no encontrado.');
    var tipoPM = String(data.tipo || '').toLowerCase();
    if (['gasto', 'ingreso', 'presupuesto'].indexOf(tipoPM) === -1) {
      throw AdisError('VALIDACION', 'Tipo de movimiento inválido (gasto/ingreso/presupuesto).');
    }
    var montoPM = Number(data.monto);
    if (!isFinite(montoPM) || montoPM <= 0) throw AdisError('VALIDACION', 'El monto debe ser mayor que cero.');
    var monedaPM = validarMoneda(data.moneda || cfg('moneda_base', 'MXN'));
    var tcPM = Number(data.tipo_cambio) || Number(cfg('tipo_cambio', '18.5')) || 1;
    hoja(SHEET_PROY_MOVS, ENC_PROY_MOVS).appendRow([nuevoId(), String(data.proyecto_id), tipoPM, montoPM,
      monedaPM, tcPM, aBase(montoPM, monedaPM, tcPM), validarFecha(data.fecha) || hoy_(),
      data.descripcion || '', USUARIO_ACTUAL]);
    // 'presupuesto' ajusta el presupuesto base del proyecto (columna 11)
    if (tipoPM === 'presupuesto') {
      var hPM = ss().getSheetByName(SHEET_PROJECTS);
      var previoPM = Number(hPM.getRange(filaPM, 11).getValue()) || 0;
      hPM.getRange(filaPM, 11).setValue(previoPM + montoPM);
    }
    log_('proyecto_mov', tipoPM + ' · ' + montoPM + ' ' + monedaPM + ' · proyecto ' + String(data.proyecto_id));
    return json({ ok: true });
  });

  // Crea un proyecto desde una cotizacion Aprobada (sin recapturar datos)
  if (tipo === 'crear_proyecto_desde_cotizacion') return conLock(function () {
    var filaCot = filaPorId(SHEET_QUOTES, data.quote_id);
    if (!filaCot) throw AdisError('NO_ENCONTRADO', 'Cotización no encontrada.');
    var hCot2 = ss().getSheetByName(SHEET_QUOTES);
    var encCot2 = hCot2.getRange(1, 1, 1, hCot2.getLastColumn()).getValues()[0].map(String);
    var vCot = {};
    hCot2.getRange(filaCot, 1, 1, encCot2.length).getValues()[0].forEach(function (val, ic2) { vCot[encCot2[ic2]] = val; });
    var estadoCot = String(vCot.estado || 'Activa');
    if (estadoCot !== 'Aprobada') throw AdisError('NO_PERMITIDO', 'La cotización debe estar APROBADA para crear el proyecto (está: ' + estadoCot + ').');
    // idempotencia: si ya tiene proyecto, se devuelve el existente
    var existentes = filasComoObjetos(SHEET_PROJECTS);
    for (var ip = 0; ip < existentes.length; ip++) {
      if (String(existentes[ip].cotizacion_id) === String(data.quote_id)) {
        return json({ ok: true, id: existentes[ip].id, folio: existentes[ip].folio, ya_existia: true });
      }
    }
    var datosCot = {};
    try { datosCot = JSON.parse(String(vCot.datos || '{}')); } catch (e) {}
    var nombreProy = String(datosCot.proyecto || '').trim() || ('Proyecto ' + String(vCot.folio));
    var folioProy = siguienteFolio('PRY', 'folio_proyecto', 4);
    var idProy = nuevoId();
    hoja(SHEET_PROJECTS, ENC_PROY).appendRow([idProy, folioProy, nombreProy, String(vCot.cliente_id || ''),
      String(vCot.cliente || ''), String(data.quote_id), String(vCot.folio || ''),
      String(datosCot.ubicacion || vCot.ubicacion || ''), hoy_(), '', Number(vCot.total) || 0,
      String(vCot.moneda || 'MXN'), 'ACTIVO', data.notas || '', USUARIO_ACTUAL, ahora_()]);
    log_('proyecto_creado', folioProy + ' · ' + nombreProy + ' · desde ' + vCot.folio);
    return json({ ok: true, id: idProy, folio: folioProy });
  });

  if (tipo === 'save_proyecto') return conLock(function () {
    var nombreP2 = String(data.nombre || '').trim();
    if (!nombreP2) throw AdisError('VALIDACION', 'El proyecto necesita nombre.');
    var hPr = hoja(SHEET_PROJECTS, ENC_PROY);
    if (data.id) {
      var filaPr = filaPorId(SHEET_PROJECTS, data.id);
      if (!filaPr) throw AdisError('NO_ENCONTRADO', 'Proyecto no encontrado.');
      hPr.getRange(filaPr, 1, 1, ENC_PROY.length).setValues([[data.id, String(hPr.getRange(filaPr, 2).getValue()),
        nombreP2, data.cliente_id || '', data.cliente || '', data.cotizacion_id || '', data.cotizacion_folio || '',
        data.ubicacion || '', validarFecha(data.fecha_inicio) || hoy_(), validarFecha(data.fecha_fin) || '',
        Number(data.presupuesto) || 0, validarMoneda(data.moneda || 'MXN'), data.estado || 'ACTIVO',
        data.notas || '', USUARIO_ACTUAL, ahora_()]]);
      log_('proyecto_editado', nombreP2);
      return json({ ok: true, id: data.id });
    }
    var folioP2 = siguienteFolio('PRY', 'folio_proyecto', 4);
    var idP2 = nuevoId();
    hPr.appendRow([idP2, folioP2, nombreP2, data.cliente_id || '', data.cliente || '', data.cotizacion_id || '',
      data.cotizacion_folio || '', data.ubicacion || '', validarFecha(data.fecha_inicio) || hoy_(),
      validarFecha(data.fecha_fin) || '', Number(data.presupuesto) || 0, validarMoneda(data.moneda || 'MXN'),
      'ACTIVO', data.notas || '', USUARIO_ACTUAL, ahora_()]);
    log_('proyecto_creado', folioP2 + ' · ' + nombreP2);
    return json({ ok: true, id: idP2, folio: folioP2 });
  });

  if (tipo === 'cambiar_estado_proyecto') return conLock(function () {
    var transP = { ACTIVO: ['TERMINADO', 'CANCELADO'], TERMINADO: [], CANCELADO: [] };
    var filaPE = filaPorId(SHEET_PROJECTS, data.id);
    if (!filaPE) throw AdisError('NO_ENCONTRADO', 'Proyecto no encontrado.');
    var hPE = ss().getSheetByName(SHEET_PROJECTS);
    var estadoPE = String(hPE.getRange(filaPE, 12).getValue()) || 'ACTIVO';
    var nuevoPE = String(data.estado || '').toUpperCase();
    if ((transP[estadoPE] || []).indexOf(nuevoPE) === -1) {
      throw AdisError('NO_PERMITIDO', 'No se puede pasar de ' + estadoPE + ' a ' + nuevoPE + '.');
    }
    hPE.getRange(filaPE, 12).setValue(nuevoPE);
    if (nuevoPE === 'TERMINADO') hPE.getRange(filaPE, 10).setValue(hoy_());
    hPE.getRange(filaPE, 16).setValue(ahora_());
    log_('proyecto_estado', String(hPE.getRange(filaPE, 2).getValue()) + ': ' + estadoPE + ' -> ' + nuevoPE);
    return json({ ok: true, estado: nuevoPE });
  });

  // Cobro: dinero REAL recibido contra una venta. Diferencia venta (contable)
  // de cobro (efectivo). Actualiza estado_pago PENDIENTE/PARCIAL/PAGADA.
  if (tipo === 'registrar_cobro') return conLock(function () {
    var filaV = filaPorId(SHEET_SALES, data.venta_id);
    if (!filaV) throw AdisError('NO_ENCONTRADO', 'Venta no encontrada (solo ventas nuevas con ID admiten cobros).');
    var hV2 = ss().getSheetByName(SHEET_SALES);
    var estadoV = String(hV2.getRange(filaV, 17).getValue()) || 'PENDIENTE';
    if (estadoV === 'CANCELADA') throw AdisError('NO_PERMITIDO', 'La venta está cancelada; no admite cobros.');
    var folioV2 = String(hV2.getRange(filaV, 13).getValue());
    var totalV = Number(hV2.getRange(filaV, 5).getValue()) || 0;
    var monedaV2 = String(hV2.getRange(filaV, 6).getValue()) || 'MXN';
    var tc2 = Number(hV2.getRange(filaV, 7).getValue()) || Number(cfg('tipo_cambio', '18.5')) || 1;
    var montoC = Number(data.monto);
    if (!isFinite(montoC) || montoC <= 0) throw AdisError('VALIDACION', 'El monto del cobro debe ser mayor que cero.');
    var monedaC = validarMoneda(data.moneda || monedaV2);
    // cobrado previo en la moneda de la venta (aproximacion via monto_base si moneda distinta)
    var cobradoPrev = 0, cobradoPrevBase = 0;
    filasComoObjetos(SHEET_COBROS).forEach(function (c) {
      if (String(c.venta_id) === String(data.venta_id)) {
        cobradoPrevBase += Number(c.monto_base) || 0;
        if (String(c.moneda) === monedaV2) cobradoPrev += Number(c.monto) || 0;
      }
    });
    var totalBaseV = Number(hV2.getRange(filaV, 8).getValue()) || 0;
    var montoBaseC = aBase(montoC, monedaC, tc2);
    if (cobradoPrevBase + montoBaseC > totalBaseV + 0.001) {
      throw AdisError('VALIDACION', 'El cobro excede el saldo pendiente de la venta ' + folioV2 + '.');
    }
    var folioCob = siguienteFolio('COB', 'folio_cobro', 4);
    hoja(SHEET_COBROS, ENC_COBROS).appendRow([nuevoId(), folioCob, String(data.venta_id), folioV2,
      String(hV2.getRange(filaV, 2).getValue()), String(hV2.getRange(filaV, 15).getValue()) || '',
      validarFecha(data.fecha) || hoy_(), montoC, monedaC, montoBaseC,
      data.metodo || '', data.notas || '', USUARIO_ACTUAL]);
    var nuevoEstadoV = (cobradoPrevBase + montoBaseC >= totalBaseV - 0.001 && totalBaseV > 0) ? 'PAGADA' : 'PARCIAL';
    hV2.getRange(filaV, 17).setValue(nuevoEstadoV);
    log_('cobro_registrado', folioCob + ' · ' + folioV2 + ' · ' + montoC + ' ' + monedaC + ' · ' + nuevoEstadoV);
    return json({ ok: true, folio: folioCob, estado_pago: nuevoEstadoV });
  });

  // Anulacion de venta: cancela y REGRESA la mercancia al almacen (trazable)
  if (tipo === 'anular_venta') return conLock(function () {
    var filaAV = filaPorId(SHEET_SALES, data.id);
    if (!filaAV) throw AdisError('NO_ENCONTRADO', 'Venta no encontrada.');
    var hAV = ss().getSheetByName(SHEET_SALES);
    var estadoAV = String(hAV.getRange(filaAV, 17).getValue()) || 'PENDIENTE';
    if (estadoAV === 'CANCELADA') return json({ ok: true, ya_cancelada: true });
    var almacenIdAV = String(hAV.getRange(filaAV, 18).getValue());
    if (!almacenIdAV) throw AdisError('NO_PERMITIDO', 'Esta venta es antigua (sin almacén registrado) y no puede anularse automáticamente.');
    var folioAV = String(hAV.getRange(filaAV, 13).getValue());
    var almacenAV = filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.id) === almacenIdAV; })[0] || {};
    // reingresar mercancia: los items se guardan como texto "Nombre xN"; sin
    // producto_id no es posible revertir automaticamente -> se exige venta nueva
    var itemsTxt = String(hAV.getRange(filaAV, 4).getValue() || '');
    if (!itemsTxt) throw AdisError('NO_PERMITIDO', 'Venta sin partidas; no se puede anular automáticamente.');
    // Las ventas nuevas guardan items_json (columna 19) para anulacion con reversa
    var itemsJsonAV = String(hAV.getRange(filaAV, 19).getValue());
    var partidasAV = [];
    try { partidasAV = JSON.parse(itemsJsonAV); } catch (e) {}
    if (!partidasAV.length || !partidasAV[0].producto_id) {
      throw AdisError('NO_PERMITIDO', 'Esta venta fue registrada sin partidas estructuradas; revierte el stock manualmente con un movimiento de entrada documentado.');
    }
    partidasAV.forEach(function (it) {
      aplicarMovimiento({ tipo: 'entrada', producto_id: it.producto_id, producto: it.producto || it.nombre || '',
        almacen_id: almacenIdAV, almacen: almacenAV.nombre || '', cantidad: Number(it.cantidad) || 0,
        moneda: String(hAV.getRange(filaAV, 6).getValue()) || 'MXN',
        referencia: 'Anulación ' + folioAV, notas: data.motivo || 'Venta anulada',
        doc_tipo: 'DEVOLUCION', doc_id: folioAV });
    });
    hAV.getRange(filaAV, 17).setValue('CANCELADA');
    log_('venta_anulada', folioAV + (data.motivo ? ' · ' + data.motivo : ''));
    return json({ ok: true, estado: 'CANCELADA' });
  });

  /* ================= COMPRAS (FASE 2) ================= */

  if (tipo === 'save_proveedor') return conLock(function () {
    var nombreP = String(data.nombre || '').trim();
    if (!nombreP) throw AdisError('VALIDACION', 'El proveedor necesita nombre.');
    var hpr2 = hoja(SHEET_PROVIDERS, ENC_PROV);
    if (data.id) {
      var filaProv = filaPorId(SHEET_PROVIDERS, data.id);
      if (!filaProv) throw AdisError('NO_ENCONTRADO', 'Proveedor no encontrado.');
      hpr2.getRange(filaProv, 1, 1, ENC_PROV.length).setValues([[data.id, nombreP, data.contacto || '',
        data.telefono || '', data.email || '', data.direccion || '', data.notas || '', 'si', ahora_()]]);
      log_('proveedor_editado', nombreP);
      return json({ ok: true, id: data.id });
    }
    var idProv = nuevoId();
    hpr2.appendRow([idProv, nombreP, data.contacto || '', data.telefono || '', data.email || '',
      data.direccion || '', data.notas || '', 'si', ahora_()]);
    log_('proveedor_creado', nombreP);
    return json({ ok: true, id: idProv });
  });

  if (tipo === 'delete_proveedor') return conLock(function () {
    var filaDP = filaPorId(SHEET_PROVIDERS, data.id);
    if (!filaDP) throw AdisError('NO_ENCONTRADO', 'Proveedor no encontrado.');
    ss().getSheetByName(SHEET_PROVIDERS).getRange(filaDP, 8).setValue('no');
    log_('proveedor_desactivado', String(data.id));
    return json({ ok: true });
  });

  // Validacion comun de partidas de una OC (usada por save_oc)
  function validarPartidasOC(itemsIn, mapaProd) {
    if (!itemsIn || !itemsIn.length) throw AdisError('VALIDACION', 'La orden de compra necesita al menos un producto.');
    if (itemsIn.length > 100) throw AdisError('VALIDACION', 'Máximo 100 partidas por orden de compra.');
    var vistos = {};
    return itemsIn.map(function (it) {
      var p = mapaProd[String(it.producto_id)];
      if (!p) throw AdisError('NO_ENCONTRADO', 'Producto no encontrado: ' + it.producto_id);
      var cant = Number(it.cantidad), costo = Number(it.costo_unit);
      if (!isFinite(cant) || cant <= 0) throw AdisError('VALIDACION', 'Cantidad inválida para ' + p.nombre + '.');
      if (!isFinite(costo) || costo < 0) throw AdisError('VALIDACION', 'Costo inválido para ' + p.nombre + '.');
      if (vistos[String(p.id)]) throw AdisError('VALIDACION', 'Producto repetido en la orden: ' + p.nombre + '.');
      vistos[String(p.id)] = true;
      return { producto_id: p.id, producto: p.nombre, cantidad: cant, costo_unit: costo };
    });
  }
  function totalesOC(partidas, ivaPct, descuento) {
    var subtotal = partidas.reduce(function (s, p) { return s + p.cantidad * p.costo_unit; }, 0);
    var iva = subtotal * (Number(ivaPct) || 0) / 100;
    var total = subtotal + iva - (Number(descuento) || 0);
    if (total < 0) throw AdisError('VALIDACION', 'El total de la orden no puede ser negativo.');
    return { subtotal: subtotal, iva: iva, total: total };
  }

  if (tipo === 'save_oc') return conLock(function () {
    var prodsOC = filasComoObjetos(SHEET_PRODUCTS);
    var mapaProdOC = {};
    prodsOC.forEach(function (p) { mapaProdOC[String(p.id)] = p; });
    var partidas = validarPartidasOC(data.items, mapaProdOC);
    var prov = filasComoObjetos(SHEET_PROVIDERS).filter(function (p) { return String(p.id) === String(data.proveedor_id) && String(p.activo) !== 'no'; })[0] || {};
    if (!prov.id) throw AdisError('NO_ENCONTRADO', 'Selecciona un proveedor válido.');
    var almOC = filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.id) === String(data.almacen_id); })[0] || {};
    if (!almOC.id) throw AdisError('NO_ENCONTRADO', 'Selecciona un almacén destino válido.');
    var monedaOC = validarMoneda(data.moneda || cfg('moneda_base', 'MXN'));
    var t = totalesOC(partidas, data.iva_pct, data.descuento);
    var fechaOC = validarFecha(data.fecha) || hoy_();
    var esperada = validarFecha(data.fecha_esperada);
    var hOC = hoja(SHEET_PO, ENC_OC);
    if (data.id) { // solo se puede editar en BORRADOR
      var filaOC = filaPorId(SHEET_PO, data.id);
      if (!filaOC) throw AdisError('NO_ENCONTRADO', 'Orden de compra no encontrada.');
      var hojaOC = ss().getSheetByName(SHEET_PO);
      var estadoActual = String(hojaOC.getRange(filaOC, 14).getValue());
      if (estadoActual !== 'BORRADOR') throw AdisError('NO_PERMITIDO', 'Solo se pueden editar órdenes en BORRADOR.');
      hojaOC.getRange(filaOC, 1, 1, ENC_OC.length).setValues([[data.id, hojaOC.getRange(filaOC, 2).getValue(),
        prov.id, prov.nombre, fechaOC, esperada || '', almOC.id, almOC.nombre, monedaOC,
        t.subtotal, t.iva, Number(data.descuento) || 0, t.total, 'BORRADOR', data.notas || '',
        USUARIO_ACTUAL, ahora_(), JSON.stringify(partidas)]]);
      log_('oc_editada', hojaOC.getRange(filaOC, 2).getValue());
      return json({ ok: true, id: data.id });
    }
    var folioOC = siguienteFolio('OC', 'folio_oc', 4);
    var idOC = nuevoId();
    hOC.appendRow([idOC, folioOC, prov.id, prov.nombre, fechaOC, esperada || '', almOC.id, almOC.nombre,
      monedaOC, t.subtotal, t.iva, Number(data.descuento) || 0, t.total, 'BORRADOR', data.notas || '',
      USUARIO_ACTUAL, ahora_(), JSON.stringify(partidas)]);
    log_('oc_creada', folioOC + ' · ' + prov.nombre + ' · ' + monedaOC + ' ' + t.total);
    return json({ ok: true, id: idOC, folio: folioOC });
  });

  if (tipo === 'cambiar_estado_oc') return conLock(function () {
    var filaE = filaPorId(SHEET_PO, data.id);
    if (!filaE) throw AdisError('NO_ENCONTRADO', 'Orden de compra no encontrada.');
    var hE = ss().getSheetByName(SHEET_PO);
    var estadoE = String(hE.getRange(filaE, 14).getValue());
    var nuevoE = String(data.estado || '').toUpperCase();
    var transiciones = { BORRADOR: ['AUTORIZADA', 'CANCELADA'], AUTORIZADA: ['ENVIADA', 'CANCELADA'],
      ENVIADA: ['CANCELADA'], PARCIAL: ['CANCELADA'], RECIBIDA: [], CANCELADA: [] };
    if ((transiciones[estadoE] || []).indexOf(nuevoE) === -1) {
      throw AdisError('NO_PERMITIDO', 'No se puede pasar de ' + estadoE + ' a ' + nuevoE + '.');
    }
    hE.getRange(filaE, 14).setValue(nuevoE);
    hE.getRange(filaE, 17).setValue(ahora_());
    log_('oc_estado', hE.getRange(filaE, 2).getValue() + ': ' + estadoE + ' -> ' + nuevoE);
    return json({ ok: true, estado: nuevoE });
  });

  // Recepcion de mercancia: NO modifica stock a mano; genera una ENTRADA por
  // partida vinculada a la OC (doc_tipo ORDEN_COMPRA). Recepcion parcial: el
  // estado pasa a PARCIAL hasta completar, luego RECIBIDA.
  if (tipo === 'recibir_oc') return conLock(function () {
    var filaR = filaPorId(SHEET_PO, data.oc_id);
    if (!filaR) throw AdisError('NO_ENCONTRADO', 'Orden de compra no encontrada.');
    var hR = ss().getSheetByName(SHEET_PO);
    var estadoR = String(hR.getRange(filaR, 14).getValue());
    if (['AUTORIZADA', 'ENVIADA', 'PARCIAL'].indexOf(estadoR) === -1) {
      throw AdisError('NO_PERMITIDO', 'La orden ' + estadoR + ' no admite recepciones.');
    }
    var folioR = String(hR.getRange(filaR, 2).getValue());
    var almacenIdR = String(hR.getRange(filaR, 7).getValue());
    var almacenNomR = String(hR.getRange(filaR, 8).getValue());
    var partidasR = [];
    try { partidasR = JSON.parse(String(hR.getRange(filaR, 18).getValue()) || '[]'); } catch (e) {}
    var itemsIn = data.items || [];
    if (!itemsIn.length) throw AdisError('VALIDACION', 'Indica qué productos estás recibiendo.');
    // recepciones previas para calcular pendiente real
    var recibidoPrev = {};
    filasComoObjetos(SHEET_RECEP).forEach(function (r) {
      if (String(r.oc_id) !== String(data.oc_id)) return;
      var its = [];
      try { its = JSON.parse(r.items || '[]'); } catch (e) {}
      its.forEach(function (it) {
        recibidoPrev[String(it.producto_id)] = (recibidoPrev[String(it.producto_id)] || 0) + (Number(it.cantidad) || 0);
      });
    });
    var mapaPartidas = {};
    partidasR.forEach(function (pt) { mapaPartidas[String(pt.producto_id)] = pt; });
    var recibidosAhora = [];
    itemsIn.forEach(function (it) {
      var pt = mapaPartidas[String(it.producto_id)];
      if (!pt) throw AdisError('VALIDACION', 'El producto no pertenece a esta orden de compra.');
      var cant = Number(it.cantidad);
      if (!isFinite(cant) || cant <= 0) throw AdisError('VALIDACION', 'Cantidad inválida para ' + pt.producto + '.');
      var yaRec = recibidoPrev[String(pt.producto_id)] || 0;
      if (yaRec + cant > Number(pt.cantidad)) {
        throw AdisError('VALIDACION', 'Excede lo pendiente de ' + pt.producto + ': pidió ' + pt.cantidad +
          ', ya recibió ' + yaRec + ', intenta recibir ' + cant + '.');
      }
      recibidosAhora.push({ producto_id: pt.producto_id, producto: pt.producto, cantidad: cant, costo_unit: pt.costo_unit });
    });
    // aplicar entradas trazables + actualizar ultimo costo
    recibidosAhora.forEach(function (rc) {
      aplicarMovimiento({ tipo: 'entrada', producto_id: rc.producto_id, producto: rc.producto,
        almacen_id: almacenIdR, almacen: almacenNomR, cantidad: rc.cantidad, costo_unit: rc.costo_unit,
        moneda: String(hR.getRange(filaR, 9).getValue()) || 'MXN',
        referencia: 'OC ' + folioR, notas: 'Recepción de compra',
        doc_tipo: 'ORDEN_COMPRA', doc_id: folioR });
      var filaProd = filaPorId(SHEET_PRODUCTS, rc.producto_id);
      if (filaProd) {
        var hp2 = ss().getSheetByName(SHEET_PRODUCTS);
        hp2.getRange(filaProd, 8).setValue(rc.costo_unit); // ultimo costo
        hp2.getRange(filaProd, 16).setValue(ahora_());
      }
    });
    hoja(SHEET_RECEP, ENC_RECEP).appendRow([nuevoId(), data.oc_id, folioR, ahora_(),
      JSON.stringify(recibidosAhora), USUARIO_ACTUAL]);
    // nuevo estado
    var completo = partidasR.every(function (pt) {
      var ya = (recibidoPrev[String(pt.producto_id)] || 0) +
        recibidosAhora.filter(function (r) { return String(r.producto_id) === String(pt.producto_id); })
          .reduce(function (s, r) { return s + r.cantidad; }, 0);
      return ya >= Number(pt.cantidad);
    });
    var nuevoEstado = completo ? 'RECIBIDA' : 'PARCIAL';
    hR.getRange(filaR, 14).setValue(nuevoEstado);
    hR.getRange(filaR, 17).setValue(ahora_());
    log_('oc_recepcion', folioR + ': ' + recibidosAhora.length + ' partidas, estado ' + nuevoEstado);
    return json({ ok: true, estado: nuevoEstado, folio: folioR });
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
