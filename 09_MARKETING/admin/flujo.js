/* ---------- flujo (visitas del sitio) ---------- */
function fLocal(d){ d=d||new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function contarPor(arr, fn){
  const m = {};
  arr.forEach(x => { const k = fn(x) || '—'; m[k] = (m[k]||0)+1; });
  return Object.keys(m).map(k => [k, m[k]]).sort((a,b)=>b[1]-a[1]);
}
function flowBarras(contados, max){
  if (!contados.length) return '<p class="muted">Sin datos todavía.</p>';
  const top = contados.slice(0, max||8);
  const mx = top[0][1] || 1;
  return top.map(r =>
    '<div class="flow-row"><span class="lbl" title="'+esc(r[0])+'">'+esc(r[0])+'</span>' +
    '<span class="bar"><i style="width:'+Math.max(3,Math.round(r[1]/mx*100))+'%"></i></span>' +
    '<span class="n">'+r[1]+'</span></div>').join('');
}
function loadFlow(){
  $('flowKpis').innerHTML = '<p class="muted">Cargando…</p>';
  apiGet('visitas').then(d=>{
    if (!d || !d.ok) { $('flowKpis').innerHTML='<p class="muted">Sin acceso o error de conexión. Si acabas de actualizar el script, despliega una <b>nueva versión</b> en Apps Script.</p>'; return; }
    const v = (d.visitas || []).filter(x => !x.pagina || String(x.pagina).indexOf('admin') === -1);
    if (!v.length) {
      $('flowKpis').innerHTML = '<p class="muted">Aún no hay visitas registradas. El tracker se activa al regenerar y publicar el sitio; entra tú mismo a la página para generar los primeros datos.</p>';
      ['flowDiario','flowOrigen','flowDisp','flowNav','flowLang','flowPaginas','flowSecciones'].forEach(id=>$(id).innerHTML='');
      $('flowTabla').innerHTML = ''; $('flowRango').textContent = '';
      return;
    }
    const hoy = fLocal();
    const hace7 = fLocal(new Date(Date.now()-6*864e5));
    const hace30 = fLocal(new Date(Date.now()-29*864e5));
    const vistas = v.filter(x => !x.seccion);            // vistas de página completa
    const apartados = v.filter(x => x.seccion);          // apartados vistos
    $('flowRango').textContent = v.length + ' registro(s) en la hoja';
    const topPag = contarPor(vistas, x=>String(x.pagina).replace(/^\/+/, ''))[0] || ['—', 0];
    $('flowKpis').innerHTML = [
      ['Visitas a páginas', vistas.length],
      ['Hoy', vistas.filter(x=>String(x.fecha)===hoy).length],
      ['Últimos 7 días', vistas.filter(x=>String(x.fecha)>=hace7).length],
      ['Apartados vistos', apartados.length],
      ['Página más vista', topPag[0] + ' (' + topPag[1] + ')']
    ].map(k=>'<div class="pnl-card"><div class="k">'+k[0]+'</div><div class="v" style="font-size:0.95rem;">'+esc(String(k[1]))+'</div></div>').join('');
    // Diario (30 días)
    const porDia = {};
    vistas.forEach(x => { const f = String(x.fecha).slice(0,10); if (f >= hace30) porDia[f] = (porDia[f]||0)+1; });
    const dias = [];
    for (let i=29; i>=0; i--) { const f = fLocal(new Date(Date.now()-i*864e5)); dias.push([f, porDia[f]||0]); }
    const mxD = Math.max(1, ...dias.map(x=>x[1]));
    $('flowDiario').innerHTML = dias.map(x=>'<div class="flow-bar" style="height:'+Math.max(3,Math.round(x[1]/mxD*100))+'%;"><span class="tip">'+x[0]+' · '+x[1]+' visita(s)</span></div>').join('');
    // Origen, dispositivo, navegador, idioma
    $('flowOrigen').innerHTML = flowBarras(contarPor(vistas, x=>x.origen), 10);
    $('flowDisp').innerHTML = flowBarras(contarPor(vistas, x=>x.dispositivo), 5);
    $('flowNav').innerHTML = flowBarras(contarPor(vistas, x=>x.navegador), 6);
    $('flowLang').innerHTML = flowBarras(contarPor(vistas, x=>x.idioma==='en'?'Inglés':'Español'), 3);
    // Páginas y apartados
    $('flowPaginas').innerHTML = flowBarras(contarPor(vistas, x=>String(x.pagina).replace(/^\/+/, '')), 10);
    $('flowSecciones').innerHTML = flowBarras(contarPor(apartados, x=>x.seccion), 10);
    // Tabla reciente
    $('flowTabla').innerHTML = v.slice(-25).reverse().map(x=>
      '<tr><td>'+esc(x.fecha)+'</td><td>'+esc(x.hora)+'</td><td>'+esc(x.pagina)+'</td><td>'+esc(x.seccion||'—')+'</td>' +
      '<td>'+esc(x.origen||'—')+'</td><td>'+esc(x.dispositivo||'—')+'</td><td>'+esc(x.navegador||'—')+'</td></tr>').join('');
  }).catch(()=>{ $('flowKpis').innerHTML='<p class="muted">Error de conexión.</p>'; });
}

