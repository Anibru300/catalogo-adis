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
