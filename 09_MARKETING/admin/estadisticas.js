/* ---------- estadísticas del sitio (dashboard nativo, sin Looker Studio) ----------
   Consume los mismos endpoints que ya alimentan el negocio (visitas, ventas,
   estado de resultados y flujo de caja) y los dibuja con Chart.js (lazy-load
   vía cargarScriptCDN, tema marfil+oro del panel). Si se configura
   CONFIG.LOOKER_STUDIO_URL, muestra ese iframe en su lugar. */
const EST_COLORS = ['#B08C3D', '#8A6D2F', '#E4D2A8', '#1e7a46', '#c0392b', '#8ab4e8', '#6b5b3e', '#d9a441', '#7a6a4f', '#3e7a5b'];
const _estCharts = {};

function _estChart(id, cfg) {
  if (_estCharts[id]) { try { _estCharts[id].destroy(); } catch (e) {} }
  _estCharts[id] = new Chart($(id), cfg);
}

function cargarChartJS() {
  if (window.Chart) return Promise.resolve();
  return cargarScriptCDN('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js');
}

function loadEstadisticas() {
  // Looker Studio configurado → iframe (comportamiento clásico)
  if (CONFIG.LOOKER_STUDIO_URL) {
    $('estNativo').style.display = 'none';
    $('analyticsBox').innerHTML = '<iframe id="analyticsFrame" src="' + esc(CONFIG.LOOKER_STUDIO_URL) + '" frameborder="0" allowfullscreen></iframe>';
    return;
  }
  $('analyticsBox').innerHTML = '';
  $('estNativo').style.display = '';
  $('estKpis').innerHTML = '<p class="muted">Cargando…</p>';

  cargarChartJS().then(function () {
    Chart.defaults.font.family = 'Montserrat, sans-serif';
    Chart.defaults.color = '#29241A';
    Chart.defaults.borderColor = '#E5DDCC';

    const hoy = fLocal();
    const mes = hoy.slice(0, 7);
    const hace29 = fLocal(new Date(Date.now() - 29 * 864e5));
    const base = CONFIG.API_URL + '?token=' + encodeURIComponent(token);
    const getj = url => fetch(url).then(r => r.json()).catch(() => null);

    Promise.all([
      apiGet('visitas'),
      getj(base + '&action=estado_resultados&mes=' + mes),
      apiGet('ventas'),
      getj(base + '&action=flujo_caja&desde=' + hace29 + '&hasta=' + hoy),
      apiGet('quotes'),
    ]).then(function ([vis, pnl, ventas, flujo, quotes]) {
      const sinConexion = !vis && !pnl && !ventas && !flujo && !quotes;
      if (sinConexion) {
        $('estKpis').innerHTML = '<p class="muted">Sin acceso o error de conexión. Si acabas de actualizar el script, despliega una <b>nueva versión</b> en Apps Script.</p>';
        return;
      }
      _estPintarKpis(vis, pnl, ventas, flujo, quotes, hoy, mes);
      _estPintarVisitas(vis, hace29);
      _estPintarOrigen(vis);
      _estPintarVentas(ventas);
      _estPintarGastos(pnl);
      _estPintarFlujo(flujo);
    });
  }).catch(function () {
    $('estKpis').innerHTML = '<p class="muted">No se pudo cargar la librería de gráficas (sin conexión al CDN). Revisa tu internet y vuelve a intentar.</p>';
  });
}

function _estPintarKpis(vis, pnl, ventas, flujo, quotes, hoy, mes) {
  const moneda = (pnl && pnl.moneda_base) || 'MXN';
  const v = ((vis && vis.visitas) || []).filter(x => !x.pagina || String(x.pagina).indexOf('admin') === -1);
  const vistas = v.filter(x => !x.seccion);
  const hace7 = fLocal(new Date(Date.now() - 6 * 864e5));
  const hace30 = fLocal(new Date(Date.now() - 29 * 864e5));
  const num = (n, suf) => '<div class="v">' + (Number(n) || 0).toLocaleString('es-MX') + (suf || '') + '</div>';
  $('estRango').textContent = v.length ? v.length + ' visita(s) registrada(s)' : '';
  let html = '';
  html += '<div class="pnl-card"><div class="k">Visitas últimos 30 días</div>' + num(vistas.filter(x => String(x.fecha) >= hace30).length) + '</div>';
  html += '<div class="pnl-card"><div class="k">Visitas últimos 7 días</div>' + num(vistas.filter(x => String(x.fecha) >= hace7).length) + '</div>';
  if (pnl && pnl.ok) {
    html += '<div class="pnl-card"><div class="k">Ventas del mes (' + (pnl.num_ventas || 0) + ')</div><div class="v">' + fmtMoney(pnl.ingresos) + ' ' + moneda + '</div></div>';
    html += '<div class="pnl-card ' + ((Number(pnl.utilidad_neta) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Utilidad neta del mes</div><div class="v">' + fmtMoney(pnl.utilidad_neta) + ' ' + moneda + '</div></div>';
  }
  if (flujo && flujo.ok) {
    html += '<div class="pnl-card ' + ((Number(flujo.neto) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Flujo neto 30 días</div><div class="v">' + fmtMoney(flujo.neto) + ' ' + (flujo.moneda_base || moneda) + '</div></div>';
  }
  const cotMes = ((quotes && quotes.quotes) || []).filter(q => String(q.fecha || '').indexOf(mes) === 0).length;
  html += '<div class="pnl-card"><div class="k">Cotizaciones del mes</div>' + num(cotMes) + '</div>';
  $('estKpis').innerHTML = html;
}

function _estUltimos30Dias(contarFn) {
  const out = [];
  for (let i = 29; i >= 0; i--) {
    const f = fLocal(new Date(Date.now() - i * 864e5));
    out.push([f, contarFn(f)]);
  }
  return out;
}

function _estPintarVisitas(vis, hace30) {
  let datos = [];
  if (vis && vis.ok) {
    const vistas = (vis.visitas || []).filter(x => (!x.pagina || String(x.pagina).indexOf('admin') === -1) && !x.seccion);
    const porDia = {};
    vistas.forEach(x => {
      if (String(x.fecha) < hace30) return;
      const f = String(x.fecha).slice(0, 10); // fecha trae hora (yyyy-MM-dd HH:mm)
      porDia[f] = (porDia[f] || 0) + 1;
    });
    datos = _estUltimos30Dias(f => porDia[f] || 0);
  } else {
    datos = _estUltimos30Dias(() => 0);
  }
  const ctx = $('estVisitasLine').getContext('2d');
  const grad = ctx.createLinearGradient(0, 0, 0, 240);
  grad.addColorStop(0, 'rgba(176,140,61,0.45)');
  grad.addColorStop(1, 'rgba(176,140,61,0.02)');
  _estChart('estVisitasLine', {
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
      scales: { y: { beginAtZero: true, suggestedMax: 5, ticks: { precision: 0 } } }
    }
  });
}

function _estPintarOrigen(vis) {
  let items = [['Sin datos', 1]];
  if (vis && vis.ok) {
    const vistas = (vis.visitas || []).filter(x => !x.pagina || String(x.pagina).indexOf('admin') === -1);
    const c = contarPor(vistas, x => x.origen || 'Directo');
    if (c.length) items = c.slice(0, 7);
  }
  _estChart('estOrigenDough', {
    type: 'doughnut',
    data: {
      labels: items.map(i => i[0]),
      datasets: [{
        data: items.map(i => i[1]),
        backgroundColor: EST_COLORS.slice(0, items.length),
        borderColor: '#F6F3EC', borderWidth: 2
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true, cutout: '58%',
      plugins: { legend: { position: 'right', labels: { boxWidth: 12, padding: 10 } } }
    }
  });
}

function _estPintarVentas(ventas) {
  const porMes = {};
  let hay = false;
  ((ventas && ventas.ventas) || []).forEach(function (v) {
    const m = String(v.fecha || '').slice(0, 7);
    if (!m || m.length !== 7) return;
    porMes[m] = (porMes[m] || 0) + (Number(v.total) || 0);
    hay = true;
  });
  const meses = Object.keys(porMes).sort().slice(-6);
  const labels = hay ? meses : ['Sin datos'];
  const data = hay ? meses.map(m => porMes[m]) : [0];
  _estChart('estVentasBar', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Ventas', data: data,
        backgroundColor: 'rgba(176,140,61,0.75)', borderColor: '#8A6D2F', borderWidth: 1,
        borderRadius: 6, maxBarThickness: 46
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtMoney(c.parsed.y) } } },
      scales: { y: { beginAtZero: true, suggestedMax: 10, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
}

function _estPintarGastos(pnl) {
  const g = (pnl && pnl.ok && pnl.gastos) ? Object.keys(pnl.gastos).map(k => [k, Number(pnl.gastos[k]) || 0]).sort((a, b) => b[1] - a[1]).slice(0, 8) : [];
  _estChart('estGastosBar', {
    type: 'bar',
    data: {
      labels: g.length ? g.map(x => x[0]) : ['Sin datos'],
      datasets: [{
        label: 'Gastos', data: g.length ? g.map(x => x[1]) : [0],
        backgroundColor: 'rgba(192,57,43,0.65)', borderColor: '#c0392b', borderWidth: 1,
        borderRadius: 5, maxBarThickness: 22
      }]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtMoney(c.parsed.x) } } },
      scales: { x: { beginAtZero: true, suggestedMax: 10, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
}

function _estPintarFlujo(flujo) {
  const dias = (flujo && flujo.ok && flujo.dias && flujo.dias.length) ? flujo.dias : [];
  const labels = dias.length ? dias.map(d => String(d.fecha).slice(5)) : ['Sin datos'];
  _estChart('estFlujoBar', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'Entradas', data: dias.length ? dias.map(d => Number(d.entradas) || 0) : [0], backgroundColor: 'rgba(30,122,70,0.75)', borderRadius: 4, maxBarThickness: 14 },
        { label: 'Salidas', data: dias.length ? dias.map(d => Number(d.salidas) || 0) : [0], backgroundColor: 'rgba(192,57,43,0.7)', borderRadius: 4, maxBarThickness: 14 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12 } }, tooltip: { callbacks: { label: c => c.dataset.label + ': ' + fmtMoney(c.parsed.y) } } },
      scales: { y: { beginAtZero: true, suggestedMax: 10, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
}
