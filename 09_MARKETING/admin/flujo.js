/* ---------- sitio web (analítica del sitio, alimentada por el tracker) ----------
   Todo lo que es tráfico web vive aquí: KPIs de visitas, gráfica diaria
   (Chart.js), orígenes, dispositivos, navegadores, páginas y tabla reciente.
   Si se configura CONFIG.LOOKER_STUDIO_URL, muestra ese iframe en su lugar.
   Los helpers de Chart.js (_estChart, cargarChartJS, _estUltimos30Dias) viven
   en estadisticas.js, que se carga en el mismo bundle. */
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
  // Looker Studio configurado → iframe (comportamiento clásico)
  if (CONFIG.LOOKER_STUDIO_URL) {
    $('flowNativo').style.display = 'none';
    $('analyticsBox').innerHTML = '<iframe id="analyticsFrame" src="' + esc(CONFIG.LOOKER_STUDIO_URL) + '" frameborder="0" allowfullscreen></iframe>';
    return;
  }
  $('analyticsBox').innerHTML = '';
  $('flowNativo').style.display = '';
  $('flowKpis').innerHTML = '<p class="muted">Cargando…</p>';
  apiGet('visitas').then(d=>{
    if (!d || !d.ok) { $('flowKpis').innerHTML='<p class="muted">Sin acceso o error de conexión. Si acabas de actualizar el script, despliega una <b>nueva versión</b> en Apps Script.</p>'; return; }
    const v = (d.visitas || []).filter(x => !x.pagina || String(x.pagina).indexOf('admin') === -1);
    // Limpia gráficas previas (por si se reentra al tab)
    ['flowChartDiario','flowChartOrigen'].forEach(id => { if (_estCharts[id]) { try { _estCharts[id].destroy(); } catch(e) {} delete _estCharts[id]; } });
    if (!v.length) {
      $('flowKpis').innerHTML = '<p class="muted">Aún no hay visitas registradas. El tracker se activa al regenerar y publicar el sitio; entra tú mismo a la página para generar los primeros datos.</p>';
      $('flowChartDiarioBox').innerHTML = '<p class="muted">Sin datos todavía.</p>';
      $('flowChartOrigenBox').innerHTML = '<p class="muted">Sin datos todavía.</p>';
      ['flowDisp','flowNav','flowLang','flowPaginas','flowSecciones'].forEach(id=>$(id).innerHTML='');
      $('flowTabla').innerHTML = ''; $('flowRango').textContent = '';
      return;
    }
    const hoy = fLocal();
    const hace7 = fLocal(new Date(Date.now()-6*864e5));
    const hace30 = fLocal(new Date(Date.now()-29*864e5));
    const vistas = v.filter(x => !x.seccion);            // vistas de página completa
    const apartados = v.filter(x => x.seccion);          // apartados vistos
    $('flowRango').textContent = v.length + ' registro(s) en la hoja';
    const nomPag = x => { const p = String(x.pagina || '').replace(/^\/+/, '').replace(/^index\.html$/, ''); return p || 'Inicio'; };
    const topPag = contarPor(vistas, nomPag)[0] || ['—', 0];
    $('flowKpis').innerHTML = [
      ['Visitas a páginas', vistas.length],
      ['Hoy', vistas.filter(x=>String(x.fecha)===hoy).length],
      ['Últimos 7 días', vistas.filter(x=>String(x.fecha)>=hace7).length],
      ['Últimos 30 días', vistas.filter(x=>String(x.fecha)>=hace30).length],
      ['Apartados vistos', apartados.length],
      ['Página más vista', topPag[0] + ' (' + topPag[1] + ')']
    ].map(k=>'<div class="pnl-card"><div class="k">'+k[0]+'</div><div class="v" style="font-size:0.95rem;">'+esc(String(k[1]))+'</div></div>').join('');
    // Gráficas principales con Chart.js (fallback a barras CSS si el CDN falla)
    cargarChartJS().then(function () {
      _flowPintarDiario(vistas, hace30);
      _flowPintarOrigen(vistas);
    }).catch(function () {
      $('flowChartDiarioBox').innerHTML = flowBarras(contarPor(vistas, x=>String(x.fecha).slice(0,10)), 10);
      $('flowChartOrigenBox').innerHTML = flowBarras(contarPor(vistas, x=>x.origen), 10);
    });
    // Origen, dispositivo, navegador, idioma
    $('flowDisp').innerHTML = flowBarras(contarPor(vistas, x=>x.dispositivo), 5);
    $('flowNav').innerHTML = flowBarras(contarPor(vistas, x=>x.navegador), 6);
    $('flowLang').innerHTML = flowBarras(contarPor(vistas, x=>x.idioma==='en'?'Inglés':'Español'), 3);
    // Páginas y apartados
    $('flowPaginas').innerHTML = flowBarras(contarPor(vistas, nomPag), 10);
    $('flowSecciones').innerHTML = flowBarras(contarPor(apartados, x=>x.seccion), 10);
    // Tabla reciente
    $('flowTabla').innerHTML = v.slice(-25).reverse().map(x=>
      '<tr><td>'+esc(x.fecha)+'</td><td>'+esc(x.hora)+'</td><td>'+esc(x.pagina)+'</td><td>'+esc(x.seccion||'—')+'</td>' +
      '<td>'+esc(x.origen||'—')+'</td><td>'+esc(x.dispositivo||'—')+'</td><td>'+esc(x.navegador||'—')+'</td></tr>').join('');
  }).catch(()=>{ $('flowKpis').innerHTML='<p class="muted">Error de conexión.</p>'; });
}

function _flowPintarDiario(vistas, hace30) {
  const porDia = {};
  vistas.forEach(x => {
    if (String(x.fecha) < hace30) return;
    const f = String(x.fecha).slice(0, 10); // fecha trae hora (yyyy-MM-dd HH:mm)
    porDia[f] = (porDia[f] || 0) + 1;
  });
  const datos = _estUltimos30Dias(f => porDia[f] || 0);
  const ctx = $('flowChartDiario').getContext('2d');
  const grad = ctx.createLinearGradient(0, 0, 0, 240);
  grad.addColorStop(0, 'rgba(176,140,61,0.45)');
  grad.addColorStop(1, 'rgba(176,140,61,0.02)');
  _estChart('flowChartDiario', {
    type: 'line',
    data: {
      labels: datos.map(d => d[0].slice(5)),
      datasets: [{
        label: 'Visitas', data: datos.map(d => d[1]),
        borderColor: '#B08C3D', backgroundColor: grad, fill: true,
        tension: 0.35, pointRadius: 2, pointBackgroundColor: '#8A6D2F', borderWidth: 2
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

function _flowPintarOrigen(vistas) {
  const c = contarPor(vistas, x => x.origen || 'Directo').slice(0, 7);
  const items = c.length ? c : [['Sin datos', 0]];
  _estChart('flowChartOrigen', {
    type: 'doughnut',
    data: {
      labels: items.map(i => i[0]),
      datasets: [{
        data: items.map(i => i[1]),
        backgroundColor: c.length ? EST_COLORS.slice(0, items.length) : ['#E5DDCC'],
        borderColor: '#F6F3EC', borderWidth: 2
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true, cutout: '58%',
      plugins: { legend: { position: 'right', labels: { boxWidth: 12, padding: 10 } } }
    }
  });
}
