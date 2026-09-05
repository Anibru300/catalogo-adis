/*************************************************************************
 * ADIS — Backend: leads, cotizaciones, reseñas + mini-ERP
 * (productos, almacenes, stock, movimientos, ventas, gastos, resultado)
 *
 * INSTRUCCIONES (resumen; guia completa en admin/GUIA_CONFIGURACION.md):
 *  1. Crea una hoja de Google nueva (da igual el nombre).
 *  2. Extensiones > Apps Script, borra el contenido y pega TODO este archivo.
 *  3. Cambia ADMIN_USUARIO y ADMIN_CLAVE abajo.
 *  4. Despliega: Implementar > Nueva implementacion > Tipo: Aplicacion web
 *     - Ejecutar como: Yo
 *     - Quien tiene acceso: Cualquier persona
 *  5. Copia la URL de la app web (/exec) y pegala en:
 *     - generar_web.py  -> LEADS_URL y REVIEWS_URL
 *     - admin/index.html -> CONFIG.API_URL
 *  Las pestañas (Leads, Cotizaciones, Reseñas, Productos, Almacenes,
 *  Stock, Movimientos, Ventas, Gastos, Config) se crean solas.
 *************************************************************************/

// ======= CREDENCIALES DEL ADMINISTRADOR (CAMBIA ESTOS DOS VALORES) =======
var ADMIN_USUARIO = 'Adis';
var ADMIN_CLAVE   = 'Adisdiseño2026';
// ========================================================================

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
var TOKEN_MINUTOS  = 8 * 60;

// Hojas desde las que el panel puede borrar filas (limpieza / correccion)
var HOJAS_BORRABLES = [SHEET_LEADS, SHEET_QUOTES, SHEET_REVIEWS, SHEET_MOVES, SHEET_SALES, SHEET_EXPENSES, SHEET_STOCK];

var MONEDAS = ['MXN', 'USD'];

/* ============================ UTILIDADES ============================ */

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ss() { return SpreadsheetApp.getActiveSpreadsheet(); }

function hoja(nombre, encabezados) {
  var libro = ss();
  var h = libro.getSheetByName(nombre);
  if (!h) {
    h = libro.insertSheet(nombre);
    h.appendRow(encabezados);
    h.setFrozenRows(1);
  }
  return h;
}

function ahora_() {
  return Utilities.formatDate(new Date(), 'America/Hermosillo', 'yyyy-MM-dd HH:mm');
}

function hoy_() {
  return Utilities.formatDate(new Date(), 'America/Hermosillo', 'yyyy-MM-dd');
}

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
      // Sheets convierte fechas a objetos Date: normalizar a texto ISO
      if (v instanceof Date) v = Utilities.formatDate(v, 'America/Hermosillo', 'yyyy-MM-dd HH:mm');
      obj[encabezados[c]] = v;
    }
    filas.push(obj);
  }
  return filas;
}

function nuevoId() { return Utilities.getUuid().slice(0, 8); }

// Bitacora de cambios (Fase 4 del plan): quien, que, cuando
function log_(accion, detalle) {
  try {
    hoja(SHEET_LOG, ['fecha', 'usuario', 'accion', 'detalle'])
      .appendRow([ahora_(), ADMIN_USUARIO, accion, String(detalle || '').slice(0, 500)]);
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

/* ---------- Config (moneda base / tipo de cambio) ---------- */

function cfg(clave, defecto) {
  var filas = filasComoObjetos(SHEET_CONFIG);
  for (var i = 0; i < filas.length; i++) {
    if (filas[i].clave === clave) return String(filas[i].valor);
  }
  return defecto;
}

function cfgSet(clave, valor) {
  var h = hoja(SHEET_CONFIG, ['clave', 'valor']);
  var datos = h.getDataRange().getValues();
  for (var i = 1; i < datos.length; i++) {
    if (datos[i][0] === clave) { h.getRange(i + 1, 2).setValue(valor); return; }
  }
  h.appendRow([clave, valor]);
}

// Convierte un monto a la moneda base. tc = unidades de moneda base por 1 USD
// (ej. moneda base MXN y tc=18.5  =>  1 USD = 18.5 MXN)
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

/* ---------- Stock ---------- */

function stockDe(productoId, almacenId) {
  var filas = filasComoObjetos(SHEET_STOCK);
  for (var i = 0; i < filas.length; i++) {
    if (String(filas[i].producto_id) === String(productoId) && String(filas[i].almacen_id) === String(almacenId)) {
      return { cantidad: Number(filas[i].cantidad) || 0, fila: i + 2 };
    }
  }
  return { cantidad: 0, fila: null };
}

function ponerStock(productoId, almacenId, cantidad) {
  var h = hoja(SHEET_STOCK, ['producto_id', 'almacen_id', 'cantidad']);
  var actual = stockDe(productoId, almacenId);
  if (actual.fila) {
    h.getRange(actual.fila, 3).setValue(cantidad);
  } else {
    h.appendRow([productoId, almacenId, cantidad]);
  }
}

// tipo: 'entrada' | 'salida' | 'ajuste'  (ajuste fija la cantidad absoluta)
function aplicarMovimiento(m) {
  var actual = stockDe(m.producto_id, m.almacen_id).cantidad;
  var nueva;
  if (m.tipo === 'entrada') nueva = actual + m.cantidad;
  else if (m.tipo === 'salida') nueva = actual - m.cantidad;
  else nueva = m.cantidad; // ajuste absoluto
  ponerStock(m.producto_id, m.almacen_id, nueva);
  hoja(SHEET_MOVES, ['fecha', 'tipo', 'producto_id', 'producto', 'almacen_id', 'almacen', 'cantidad', 'costo_unit', 'moneda', 'referencia', 'notas'])
    .appendRow([m.fecha || ahora_(), m.tipo, m.producto_id, m.producto || '', m.almacen_id, m.almacen || '',
      m.cantidad, m.costo_unit || '', m.moneda || cfg('moneda_base', 'MXN'), m.referencia || '', m.notas || '']);
  return nueva;
}

/* ============================ GET (lectura) ============================ */

function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || '';
  var token = e && e.parameter && e.parameter.token;

  if (action === 'reviews') {
    var resenias = filasComoObjetos(SHEET_REVIEWS)
      .filter(function (r) { return String(r.activa).toLowerCase() !== 'no'; })
      .map(function (r) { return { nombre: r.nombre, estrellas: r.estrellas, texto: r.texto, fecha: r.fecha }; });
    return json({ ok: true, reviews: resenias });
  }

  if (!esTokenValido(token)) return json({ ok: false, error: 'Sesion no valida. Vuelve a entrar.' });

  if (action === 'me') return json({ ok: true, usuario: ADMIN_USUARIO });
  if (action === 'leads') return json({ ok: true, leads: filasComoObjetos(SHEET_LEADS) });
  if (action === 'quotes') return json({ ok: true, quotes: filasComoObjetos(SHEET_QUOTES) });
  if (action === 'reviews_admin') return json({ ok: true, reviews: filasComoObjetos(SHEET_REVIEWS) });

  if (action === 'config') {
    return json({ ok: true, moneda_base: cfg('moneda_base', 'MXN'), tipo_cambio: cfg('tipo_cambio', '18.5') });
  }
  if (action === 'productos') {
    // Incluye activos e inactivos: el panel filtra y permite recuperar
    return json({ ok: true, productos: filasComoObjetos(SHEET_PRODUCTS) });
  }
  if (action === 'almacenes') {
    return json({ ok: true, almacenes: filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.activo) !== 'no'; }) });
  }
  if (action === 'stock') {
    var productos = filasComoObjetos(SHEET_PRODUCTS);
    var almacenes = filasComoObjetos(SHEET_WAREHOUSES);
    var stock = filasComoObjetos(SHEET_STOCK);
    var detalle = stock.map(function (s) {
      var p = productos.filter(function (x) { return String(x.id) === String(s.producto_id); })[0] || {};
      var a = almacenes.filter(function (x) { return String(x.id) === String(s.almacen_id); })[0] || {};
      return { producto_id: s.producto_id, producto: p.nombre || '', almacen_id: s.almacen_id,
        almacen: a.nombre || '', cantidad: Number(s.cantidad) || 0 };
    });
    return json({ ok: true, stock: detalle });
  }
  if (action === 'movimientos') return json({ ok: true, movimientos: filasComoObjetos(SHEET_MOVES).slice(-100) });
  if (action === 'ventas') return json({ ok: true, ventas: filasComoObjetos(SHEET_SALES).slice(-100) });
  if (action === 'gastos') return json({ ok: true, gastos: filasComoObjetos(SHEET_EXPENSES) });

  if (action === 'estado_resultados') {
    var mes = e.parameter.mes; // formato YYYY-MM
    var desde = mes ? mes + '-01' : null;
    var hasta = null;
    if (mes) {
      var partes = mes.split('-');
      var fin = new Date(Number(partes[0]), Number(partes[1]), 0);
      hasta = Utilities.formatDate(fin, 'America/Hermosillo', 'yyyy-MM-dd');
    }
    var enRango = function (fecha) {
      if (!desde) return true;
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
    // mes anterior para comparativa
    var utilBruta = ingresos - costos;
    var utilNeta = utilBruta - totalGastos;
    return json({ ok: true, mes: mes || 'Todos', moneda_base: cfg('moneda_base', 'MXN'),
      ingresos: ingresos, costos: costos, utilidad_bruta: utilBruta,
      gastos: porCategoria, total_gastos: totalGastos, utilidad_neta: utilNeta,
      num_ventas: ventas.length,
      margen_bruto: ingresos ? (utilBruta / ingresos * 100) : 0,
      margen_neto: ingresos ? (utilNeta / ingresos * 100) : 0 });
  }

  return json({ ok: false, error: 'Accion desconocida' });
}

/* ============================ POST (escritura) ============================ */

function doPost(e) {
  var data = {};
  try { data = JSON.parse(e.postData.contents); } catch (err) { return json({ ok: false, error: 'JSON invalido' }); }
  var tipo = data.tipo || data.type || '';

  if (tipo === 'login') {
    if (data.usuario === ADMIN_USUARIO && data.clave === ADMIN_CLAVE) {
      return json({ ok: true, token: crearToken() });
    }
    return json({ ok: false, error: 'Usuario o contraseña incorrectos.' });
  }

  if (tipo === 'lead') {
    if (data.empresa) return json({ ok: true }); // honeypot: spam, se ignora
    hoja(SHEET_LEADS, ['fecha', 'nombre', 'telefono', 'email', 'ciudad', 'metros', 'producto', 'mensaje', 'pagina', 'idioma'])
      .appendRow([ahora_(), data.nombre || '', data.telefono || '', data.email || '', data.ciudad || '',
        data.metros || '', data.producto || '', data.mensaje || '', data.pagina || '', data.idioma || '']);
    return json({ ok: true });
  }

  if (!esTokenValido(data.token)) return json({ ok: false, error: 'Sesion no valida. Vuelve a entrar.' });

  if (tipo === 'quote') {
    var items = (data.items || []).map(function (it) {
      return (it.nombre || '') + ' x' + (it.cantidad || 1) + ' @' + (it.precio || 0);
    }).join(' | ');
    hoja(SHEET_QUOTES, ['fecha', 'cliente', 'telefono', 'ciudad', 'items', 'total', 'notas'])
      .appendRow([ahora_(), data.cliente || '', data.telefono || '', data.ciudad || '', items, data.total || 0, data.notas || '']);
    return json({ ok: true });
  }

  if (tipo === 'review') {
    hoja(SHEET_REVIEWS, ['fecha', 'nombre', 'estrellas', 'texto', 'activa'])
      .appendRow([ahora_(), data.nombre || '', data.estrellas || 5, data.texto || '', 'si']);
    return json({ ok: true });
  }

  if (tipo === 'delete_review') {
    var hr = ss().getSheetByName(SHEET_REVIEWS);
    if (hr && data.row > 1 && data.row <= hr.getLastRow()) {
      hr.getRange(data.row, 5).setValue('no');
      return json({ ok: true });
    }
    return json({ ok: false, error: 'Fila no encontrada' });
  }

  /* ---------- Config ---------- */
  if (tipo === 'config') {
    if (data.moneda_base) cfgSet('moneda_base', data.moneda_base);
    if (data.tipo_cambio) cfgSet('tipo_cambio', String(data.tipo_cambio));
    return json({ ok: true, moneda_base: cfg('moneda_base', 'MXN'), tipo_cambio: cfg('tipo_cambio', '18.5') });
  }

  /* ---------- Productos (esquema maestro) ---------- */
  if (tipo === 'save_product') {
    var ENC_PROD = ['id', 'codigo', 'nombre', 'descripcion', 'categoria', 'subcategoria', 'proveedor',
      'costo', 'precio', 'unidad', 'stock_minimo', 'moneda', 'foto', 'estado', 'notas', 'fecha_actualizacion'];
    var hp = hoja(SHEET_PRODUCTS, ENC_PROD);
    var codigo = String(data.codigo || '').trim();
    if (!String(data.nombre || '').trim()) return json({ ok: false, error: 'El producto necesita nombre.' });
    if (!codigo) return json({ ok: false, error: 'El codigo no puede estar vacio.' });
    // validar codigo unico (excepto el propio producto al editar)
    var vals = hp.getDataRange().getValues();
    var filaExistente = null;
    for (var i = 1; i < vals.length; i++) {
      if (data.id && String(vals[i][0]) === String(data.id)) filaExistente = i + 1;
      else if (String(vals[i][1]).toLowerCase() === codigo.toLowerCase()) {
        return json({ ok: false, error: 'El codigo ' + codigo + ' ya existe en otro producto.' });
      }
    }
    var fila = [data.id || nuevoId(), codigo, String(data.nombre).trim(), data.descripcion || '',
      data.categoria || '', data.subcategoria || '', data.proveedor || '',
      Number(data.costo) || 0, Number(data.precio) || 0, data.unidad || 'pieza',
      Number(data.stock_minimo) || 0, data.moneda || 'MXN', data.foto || '',
      data.estado === 'inactivo' ? 'inactivo' : 'activo', data.notas || '', ahora_()];
    if (filaExistente) hp.getRange(filaExistente, 1, 1, ENC_PROD.length).setValues([fila]);
    else hp.appendRow(fila);
    log_(filaExistente ? 'producto_editado' : 'producto_creado', codigo + ' - ' + data.nombre);
    return json({ ok: true, id: fila[0] });
  }

  // Desactivar = borrado logico (recuperable). Nunca se borra fisicamente.
  if (tipo === 'delete_product') {
    var hpd = ss().getSheetByName(SHEET_PRODUCTS);
    if (hpd) {
      var vd = hpd.getDataRange().getValues();
      for (var j = 1; j < vd.length; j++) {
        if (String(vd[j][0]) === String(data.id)) {
          hpd.getRange(j + 1, 14).setValue('inactivo');
          hpd.getRange(j + 1, 16).setValue(ahora_());
          log_('producto_desactivado', String(vd[j][1]) + ' - ' + String(vd[j][2]));
          return json({ ok: true });
        }
      }
    }
    return json({ ok: false, error: 'Producto no encontrado' });
  }

  // Recuperar producto desactivado
  if (tipo === 'restore_product') {
    var hpr = ss().getSheetByName(SHEET_PRODUCTS);
    if (hpr) {
      var vr = hpr.getDataRange().getValues();
      for (var q = 1; q < vr.length; q++) {
        if (String(vr[q][0]) === String(data.id)) {
          hpr.getRange(q + 1, 14).setValue('activo');
          hpr.getRange(q + 1, 16).setValue(ahora_());
          log_('producto_recuperado', String(vr[q][1]) + ' - ' + String(vr[q][2]));
          return json({ ok: true });
        }
      }
    }
    return json({ ok: false, error: 'Producto no encontrado' });
  }

  // Importacion masiva (dataset maestro): productos + stock por almacen
  if (tipo === 'import_productos') {
    var ENC_IMP = ['id', 'codigo', 'nombre', 'descripcion', 'categoria', 'subcategoria', 'proveedor',
      'costo', 'precio', 'unidad', 'stock_minimo', 'moneda', 'foto', 'estado', 'notas', 'fecha_actualizacion'];
    // reset: limpia las pestañas de productos/stock/movimientos y pone encabezados nuevos
    if (data.reset) {
      [SHEET_PRODUCTS, SHEET_STOCK, SHEET_MOVES].forEach(function (n) {
        var h = ss().getSheetByName(n);
        if (h) h.clearContents();
      });
      hoja(SHEET_PRODUCTS, ENC_IMP);
      hoja(SHEET_STOCK, ['producto_id', 'almacen_id', 'cantidad']);
      hoja(SHEET_MOVES, ['fecha', 'tipo', 'producto_id', 'producto', 'almacen_id', 'almacen', 'cantidad', 'costo_unit', 'moneda', 'referencia', 'notas']);
      log_('reset_base', 'Pestanas de productos/stock/movimientos reiniciadas');
    }
    var himp = hoja(SHEET_PRODUCTS, ENC_IMP);
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
    // stock por almacen (crea almacenes que no existan)
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
      // resolver producto por codigo
      var prodRows = himp.getDataRange().getValues();
      var prodId = null, prodNom = '';
      for (var b = 1; b < prodRows.length; b++) {
        if (String(prodRows[b][1]).toLowerCase() === String(s.codigo).toLowerCase()) {
          prodId = String(prodRows[b][0]); prodNom = String(prodRows[b][2]); break;
        }
      }
      if (!prodId) { errores.push('Stock sin producto: ' + s.codigo); return; }
      ponerStock(prodId, almId, Number(s.cantidad) || 0);
      hoja(SHEET_MOVES, ['fecha', 'tipo', 'producto_id', 'producto', 'almacen_id', 'almacen', 'cantidad', 'costo_unit', 'moneda', 'referencia', 'notas'])
        .appendRow([ahora_(), 'ajuste', prodId, prodNom, almId, s.almacen, Number(s.cantidad) || 0, '', 'MXN', 'Importacion inicial', 'Carga desde Excel']);
      stockCount++;
    });
    log_('importacion_masiva', count + ' productos, ' + stockCount + ' existencias');
    return json({ ok: true, importados: count, stock: stockCount, errores: errores });
  }

  // Borrado de una fila concreta (limpieza de datos de prueba / correcciones)
  if (tipo === 'delete_row') {
    var nombreHoja = String(data.sheet || '');
    if (HOJAS_BORRABLES.indexOf(nombreHoja) === -1) return json({ ok: false, error: 'Hoja no permitida' });
    var hb = ss().getSheetByName(nombreHoja);
    if (hb && data.row > 1 && data.row <= hb.getLastRow()) {
      hb.deleteRow(data.row);
      log_('fila_eliminada', nombreHoja + ' fila ' + data.row);
      return json({ ok: true });
    }
    return json({ ok: false, error: 'Fila no encontrada' });
  }

  /* ---------- Almacenes ---------- */
  if (tipo === 'save_almacen') {
    var ha = hoja(SHEET_WAREHOUSES, ['id', 'nombre', 'ubicacion', 'activo']);
    if (data.id) {
      var va = ha.getDataRange().getValues();
      for (var k = 1; k < va.length; k++) {
        if (String(va[k][0]) === String(data.id)) {
          ha.getRange(k + 1, 1, 1, 4).setValues([[data.id, data.nombre, data.ubicacion || '', 'si']]);
          return json({ ok: true, id: data.id });
        }
      }
    }
    var ida = nuevoId();
    ha.appendRow([ida, data.nombre, data.ubicacion || '', 'si']);
    return json({ ok: true, id: ida });
  }

  if (tipo === 'delete_almacen') {
    var had = ss().getSheetByName(SHEET_WAREHOUSES);
    if (had) {
      var vad = had.getDataRange().getValues();
      for (var m = 1; m < vad.length; m++) {
        if (String(vad[m][0]) === String(data.id)) { had.getRange(m + 1, 4).setValue('no'); return json({ ok: true }); }
      }
    }
    return json({ ok: false, error: 'Almacen no encontrado' });
  }

  /* ---------- Entrada / salida / ajuste de inventario ---------- */
  if (tipo === 'movimiento') {
    var alm = filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.id) === String(data.almacen_id); })[0] || {};
    var prod = filasComoObjetos(SHEET_PRODUCTS).filter(function (p) { return String(p.id) === String(data.producto_id); })[0] || {};
    if (!prod.id) return json({ ok: false, error: 'Producto no encontrado' });
    if (data.tipo_mov !== 'ajuste' && !alm.id) return json({ ok: false, error: 'Almacen no encontrado' });
    var nuevaCant = aplicarMovimiento({
      tipo: data.tipo_mov, producto_id: data.producto_id, producto: prod.nombre,
      almacen_id: data.almacen_id || '', almacen: alm.nombre || '',
      cantidad: Math.abs(Number(data.cantidad) || 0), costo_unit: data.costo_unit || prod.costo || '',
      moneda: data.moneda || prod.moneda || 'MXN', notas: data.notas || ''
    });
    log_('movimiento_' + data.tipo_mov, prod.nombre + ' x' + data.cantidad + ' en ' + (alm.nombre || ''));
    return json({ ok: true, stock_nuevo: nuevaCant });
  }

  /* ---------- Venta (descuenta stock y calcula utilidad) ---------- */
  if (tipo === 'venta') {
    var almacenV = filasComoObjetos(SHEET_WAREHOUSES).filter(function (a) { return String(a.id) === String(data.almacen_id); })[0] || {};
    if (!almacenV.id) return json({ ok: false, error: 'Selecciona un almacen' });
    // validar stock suficiente
    var faltantes = [];
    (data.items || []).forEach(function (it) {
      var s = stockDe(it.producto_id, data.almacen_id).cantidad;
      if (s < it.cantidad) {
        var pv = filasComoObjetos(SHEET_PRODUCTS).filter(function (p) { return String(p.id) === String(it.producto_id); })[0] || {};
        faltantes.push(pv.nombre + ' (hay ' + s + ', pides ' + it.cantidad + ')');
      }
    });
    if (faltantes.length) return json({ ok: false, error: 'Stock insuficiente: ' + faltantes.join(', ') });
    log_('venta_registrada', (data.cliente || 'mostrador') + ' - ' + (data.items || []).length + ' items');

    var total = 0, costoTotal = 0;
    var nombres = [];
    (data.items || []).forEach(function (it) {
      var prodV = filasComoObjetos(SHEET_PRODUCTS).filter(function (p) { return String(p.id) === String(it.producto_id); })[0] || {};
      var precio = Number(it.precio) || Number(prodV.precio) || 0;
      var costo = Number(prodV.costo) || 0;
      total += precio * it.cantidad;
      costoTotal += costo * it.cantidad;
      nombres.push(prodV.nombre + ' x' + it.cantidad);
      aplicarMovimiento({ tipo: 'salida', producto_id: it.producto_id, producto: prodV.nombre,
        almacen_id: data.almacen_id, almacen: almacenV.nombre, cantidad: it.cantidad,
        costo_unit: costo, moneda: data.moneda || 'MXN', referencia: 'Venta', notas: data.cliente || '' });
    });
    var tc = Number(data.tipo_cambio) || Number(cfg('tipo_cambio', '18.5')) || 1;
    var monedaV = data.moneda || cfg('moneda_base', 'MXN');
    var totalBase = aBase(total, monedaV, tc);
    var costoBase = aBase(costoTotal, monedaV, tc);
    hoja(SHEET_SALES, ['fecha', 'cliente', 'almacen', 'items', 'total', 'moneda', 'tipo_cambio', 'total_base', 'costo_total_base', 'utilidad_base', 'notas'])
      .appendRow([data.fecha || hoy_(), data.cliente || '', almacenV.nombre, nombres.join(' | '),
        total, monedaV, tc, totalBase, costoBase, totalBase - costoBase, data.notas || '']);
    return json({ ok: true, total: total, utilidad: totalBase - costoBase });
  }

  /* ---------- Gasto ---------- */
  if (tipo === 'gasto') {
    var tcg = Number(data.tipo_cambio) || Number(cfg('tipo_cambio', '18.5')) || 1;
    var monedaG = data.moneda || cfg('moneda_base', 'MXN');
    hoja(SHEET_EXPENSES, ['fecha', 'categoria', 'descripcion', 'monto', 'moneda', 'tipo_cambio', 'monto_base'])
      .appendRow([data.fecha || hoy_(), data.categoria || 'Otro', data.descripcion || '',
        Number(data.monto) || 0, monedaG, tcg, aBase(Number(data.monto) || 0, monedaG, tcg)]);
    log_('gasto_registrado', (data.categoria || 'Otro') + ' - ' + (data.monto || 0) + ' ' + monedaG);
    return json({ ok: true });
  }

  if (tipo === 'delete_gasto') {
    var hg = ss().getSheetByName(SHEET_EXPENSES);
    if (hg && data.row > 1 && data.row <= hg.getLastRow()) {
      hg.deleteRow(data.row);
      return json({ ok: true });
    }
    return json({ ok: false, error: 'Fila no encontrada' });
  }

  return json({ ok: false, error: 'Tipo desconocido' });
}
