/*************************************************************************
 * ADIS — Backend de leads, cotizaciones y reseñas (Google Apps Script)
 *
 * INSTRUCCIONES (resumen; la guia completa esta en admin/GUIA_CONFIGURACION.md):
 *  1. Crea una hoja de Google nueva (da igual el nombre).
 *  2. Extensiones > Apps Script, borra el contenido y pega TODO este archivo.
 *  3. Cambia ADMIN_USUARIO y ADMIN_CLAVE abajo.
 *  4. Despliega: Implementar > Nueva implementacion > Tipo: Aplicacion web
 *     - Ejecutar como: Yo
 *     - Quien tiene acceso: Cualquier persona
 *  5. Copia la URL de la app web y pegala en:
 *     - generar_web.py  -> LEADS_URL y REVIEWS_URL
 *     - admin/index.html -> CONFIG.API_URL
 *  6. La primera vez que se reciba un lead/cotizacion/reseña se crean las
 *     pestañas Leads, Cotizaciones y Reseñas automaticamente.
 *************************************************************************/

// ======= CREDENCIALES DEL ADMINISTRADOR (CAMBIA ESTOS DOS VALORES) =======
var ADMIN_USUARIO = 'Adis';
var ADMIN_CLAVE   = 'Adisdiseño2026';
// ========================================================================

var SHEET_LEADS   = 'Leads';
var SHEET_QUOTES  = 'Cotizaciones';
var SHEET_REVIEWS = 'Reseñas';
var TOKEN_MINUTOS = 8 * 60; // duracion de la sesion del panel

/* ============================ UTILIDADES ============================ */

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ss() {
  return SpreadsheetApp.getActiveSpreadsheet();
}

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

// Devuelve los datos de una pestaña como arreglo de objetos {columna: valor}
function filasComoObjetos(nombre) {
  var h = ss().getSheetByName(nombre);
  if (!h) return [];
  var valores = h.getDataRange().getValues();
  if (valores.length < 2) return [];
  var encabezados = valores[0].map(function (e) { return String(e); });
  var filas = [];
  for (var i = 1; i < valores.length; i++) {
    var obj = {};
    for (var c = 0; c < encabezados.length; c++) obj[encabezados[c]] = valores[i][c];
    filas.push(obj);
  }
  return filas;
}

function esTokenValido(token) {
  if (!token) return false;
  var cache = CacheService.getScriptCache();
  return cache.get('adis_token_' + token) === '1';
}

function crearToken() {
  var token = Utilities.getUuid();
  CacheService.getScriptCache().put('adis_token_' + token, '1', TOKEN_MINUTOS * 60);
  return token;
}

/* ============================ GET (lectura) ============================ */

function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || '';
  var token = e && e.parameter && e.parameter.token;

  // Reseñas publicas para el sitio web (solo las activas)
  if (action === 'reviews') {
    var resenias = filasComoObjetos(SHEET_REVIEWS)
      .filter(function (r) { return String(r.activa).toLowerCase() !== 'no'; })
      .map(function (r) {
        return { nombre: r.nombre, estrellas: r.estrellas, texto: r.texto, fecha: r.fecha };
      });
    return json({ ok: true, reviews: resenias });
  }

  // Todo lo demas requiere sesion de administrador
  if (!esTokenValido(token)) return json({ ok: false, error: 'Sesion no valida. Vuelve a entrar.' });
  if (action === 'me') return json({ ok: true, usuario: ADMIN_USUARIO });
  if (action === 'leads') return json({ ok: true, leads: filasComoObjetos(SHEET_LEADS) });
  if (action === 'quotes') return json({ ok: true, quotes: filasComoObjetos(SHEET_QUOTES) });
  if (action === 'reviews_admin') return json({ ok: true, reviews: filasComoObjetos(SHEET_REVIEWS) });
  return json({ ok: false, error: 'Accion desconocida' });
}

/* ============================ POST (escritura) ============================ */

function doPost(e) {
  var data = {};
  try { data = JSON.parse(e.postData.contents); } catch (err) { return json({ ok: false, error: 'JSON invalido' }); }
  var tipo = data.tipo || data.type || '';

  // ---- Login del administrador ----
  if (tipo === 'login') {
    if (data.usuario === ADMIN_USUARIO && data.clave === ADMIN_CLAVE) {
      return json({ ok: true, token: crearToken() });
    }
    return json({ ok: false, error: 'Usuario o contraseña incorrectos.' });
  }

  // ---- Lead del formulario de contacto (publico, con honeypot anti-spam) ----
  if (tipo === 'lead') {
    if (data.empresa) return json({ ok: true }); // campo oculto: es spam, se ignora
    hoja(SHEET_LEADS, ['fecha', 'nombre', 'telefono', 'email', 'ciudad', 'metros', 'producto', 'mensaje', 'pagina', 'idioma'])
      .appendRow([ahora_(), data.nombre || '', data.telefono || '', data.email || '', data.ciudad || '',
        data.metros || '', data.producto || '', data.mensaje || '', data.pagina || '', data.idioma || '']);
    return json({ ok: true });
  }

  // ---- A partir de aqui todo requiere sesion ----
  if (!esTokenValido(data.token)) return json({ ok: false, error: 'Sesion no valida. Vuelve a entrar.' });

  if (tipo === 'quote') {
    var items = (data.items || []).map(function (it) {
      return (it.nombre || '') + ' x' + (it.cantidad || 1) + ' @' + (it.precio || 0);
    }).join(' | ');
    hoja(SHEET_QUOTES, ['fecha', 'cliente', 'telefono', 'ciudad', 'items', 'total', 'notas'])
      .appendRow([ahora_(), data.cliente || '', data.telefono || '', data.ciudad || '',
        items, data.total || 0, data.notas || '']);
    return json({ ok: true });
  }

  if (tipo === 'review') {
    hoja(SHEET_REVIEWS, ['fecha', 'nombre', 'estrellas', 'texto', 'activa'])
      .appendRow([ahora_(), data.nombre || '', data.estrellas || 5, data.texto || '', 'si']);
    return json({ ok: true });
  }

  if (tipo === 'delete_review') {
    var h = ss().getSheetByName(SHEET_REVIEWS);
    if (h && data.row > 1 && data.row <= h.getLastRow()) {
      h.getRange(data.row, 1, 1, h.getLastColumn()).setValue(''); // marca activa vacia
      h.getRange(data.row, 5).setValue('no'); // columna "activa"
      return json({ ok: true });
    }
    return json({ ok: false, error: 'Fila no encontrada' });
  }

  return json({ ok: false, error: 'Tipo desconocido' });
}
