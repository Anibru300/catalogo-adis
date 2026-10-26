window.addEventListener('load', ()=>{
  if (CONFIG.API_URL.indexOf('PEGAR') === 0) {
    $('loginStatus').innerHTML = 'Falta configurar API_URL. Sigue admin/GUIA_CONFIGURACION.md.';
    return;
  }
  if (token) {
    $('loginUser').value = usuario;
    apiGet('me').then(d=>{ if (d && d.ok) enterApp(usuario); else logout(); }).catch(()=>logout());
  }
});

/* ---------- bitacora del sistema: ver errores y saber que pasó ---------- */
let logsCache = [];
function loadLogs(){
  if (!$('logsTable')) return;
  apiGet('logs').then(d=>{
    logsCache = (d && d.logs) || [];
    renderLogs();
  }).catch(()=>{ $('logsTable').innerHTML='<tr><td colspan="4" class="muted">No se pudo cargar la bitácora. Intenta de nuevo.</td></tr>'; });
}
function esErrorLog_(accion){
  const a = String(accion||'').toLowerCase();
  return a.indexOf('error')!==-1 || a.indexOf('cliente_')!==-1 || a.indexOf('invalido')!==-1 || a.indexOf('divergente')!==-1;
}
function renderLogs(){
  if (!$('logsTable')) return;
  const filtro = ($('logFiltro') ? $('logFiltro').value : '').trim().toLowerCase();
  const tipo = $('logTipo') ? $('logTipo').value : '';
  const errs = logsCache.filter(l=>esErrorLog_(l.accion)).length;
  if ($('logsDash')) $('logsDash').innerHTML =
    '<div class="pnl-card '+(errs?'bad':'good')+'"><div class="k">Errores / avisos (últimos 300)</div><div class="v">'+errs+'</div></div>' +
    '<div class="pnl-card"><div class="k">Total de registros</div><div class="v">'+logsCache.length+'</div></div>';
  let lista = logsCache;
  if (tipo) lista = lista.filter(l=>String(l.accion||'').indexOf(tipo)!==-1 || (tipo==='error'&&esErrorLog_(l.accion)));
  if (filtro) lista = lista.filter(l=>
    String(l.accion||'').toLowerCase().indexOf(filtro)!==-1 ||
    String(l.detalle||'').toLowerCase().indexOf(filtro)!==-1 ||
    String(l.usuario||'').toLowerCase().indexOf(filtro)!==-1);
  if (!lista.length) { $('logsTable').innerHTML='<tr><td colspan="4" class="muted">Sin registros que coincidan.</td></tr>'; return; }
  $('logsTable').innerHTML = lista.slice(0, 300).map(l=>{
    const err = esErrorLog_(l.accion);
    return '<tr'+(err?' style="background:rgba(192,57,43,0.06);"':'')+'><td style="white-space:nowrap;">'+esc(l.fecha)+'</td>' +
      '<td>'+esc(l.usuario)+'</td>' +
      '<td style="font-weight:600;color:'+(err?'#c0392b':'inherit')+';white-space:nowrap;">'+esc(l.accion)+'</td>' +
      '<td>'+esc(l.detalle)+'</td></tr>';
  }).join('');
}
