/* ---------- mi negocio (ingresos, utilidad y flujo de efectivo) ----------
   Dashboard financiero: consume los endpoints del negocio (estado de
   resultados, ventas, flujo de caja y cotizaciones) y los dibuja con
   Chart.js (lazy-load vía cargarScriptCDN, tema marfil+oro del panel).
   Lo de tráfico web vive en flujo.js (tab "Sitio web"). */
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

// dinero en formato mexicano consistente dentro de este tab
function _estMoney(n) {
  return '$' + (Number(n) || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function _estUltimos30Dias(contarFn) {
  const out = [];
  for (let i = 29; i >= 0; i--) {
    const f = fLocal(new Date(Date.now() - i * 864e5));
    out.push([f, contarFn(f)]);
  }
  return out;
}

function loadEstadisticas() {
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
      getj(base + '&action=estado_resultados&mes=' + mes),
      apiGet('ventas'),
      getj(base + '&action=flujo_caja&desde=' + hace29 + '&hasta=' + hoy),
      apiGet('quotes'),
    ]).then(function ([pnl, ventas, flujo, quotes]) {
      const sinConexion = !pnl && !ventas && !flujo && !quotes;
      if (sinConexion) {
        $('estKpis').innerHTML = '<p class="muted">Sin acceso o error de conexión. Si acabas de actualizar el script, despliega una <b>nueva versión</b> en Apps Script.</p>';
        return;
      }
      _estPintarKpis(pnl, ventas, flujo, quotes, mes);
      _estPintarVentas(ventas);
      _estPintarGastos(pnl);
      _estPintarFlujo(flujo, hace29, hoy);
    });
  }).catch(function () {
    $('estKpis').innerHTML = '<p class="muted">No se pudo cargar la librería de gráficas (sin conexión al CDN). Revisa tu internet y vuelve a intentar.</p>';
  });
}

function _estPintarKpis(pnl, ventas, flujo, quotes, mes) {
  const moneda = (pnl && pnl.moneda_base) || 'MXN';
  let html = '';
  if (pnl && pnl.ok) {
    html += '<div class="pnl-card"><div class="k">Ventas del mes (' + (pnl.num_ventas || 0) + ')</div><div class="v">' + _estMoney(pnl.ingresos) + ' ' + moneda + '</div></div>';
    html += '<div class="pnl-card ' + ((Number(pnl.utilidad_neta) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Utilidad neta del mes</div><div class="v">' + _estMoney(pnl.utilidad_neta) + ' ' + moneda + '</div></div>';
  }
  if (flujo && flujo.ok) {
    html += '<div class="pnl-card ' + ((Number(flujo.neto) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Flujo neto 30 días</div><div class="v">' + _estMoney(flujo.neto) + ' ' + (flujo.moneda_base || moneda) + '</div></div>';
  }
  const cotMes = ((quotes && quotes.quotes) || []).filter(q => String(q.fecha || '').indexOf(mes) === 0).length;
  html += '<div class="pnl-card"><div class="k">Cotizaciones del mes</div><div class="v">' + cotMes.toLocaleString('es-MX') + '</div></div>';
  $('estKpis').innerHTML = html || '<p class="muted">Sin datos todavía.</p>';
}

function _estPintarVentas(ventas) {
  // Preferimos el agregado por mes del backend (exacto, sin límite de filas);
  // si aún no está desplegado, caemos a calcularlo desde las últimas ventas.
  let porMes = (ventas && ventas.porMes) || null;
  if (!porMes) {
    porMes = {};
    ((ventas && ventas.ventas) || []).forEach(function (v) {
      const m = String(v.fecha || '').slice(0, 7);
      if (!m || m.length !== 7) return;
      porMes[m] = (porMes[m] || 0) + (Number(v.total) || 0);
    });
  }
  const meses = Object.keys(porMes).sort().slice(-6);
  const hay = meses.length > 0;
  _estChart('estVentasBar', {
    type: 'bar',
    data: {
      labels: hay ? meses : ['Sin datos'],
      datasets: [{
        label: 'Ventas', data: hay ? meses.map(m => porMes[m]) : [0],
        backgroundColor: 'rgba(176,140,61,0.75)', borderColor: '#8A6D2F', borderWidth: 1,
        borderRadius: 6, maxBarThickness: 46
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => _estMoney(c.parsed.y) } } },
      scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
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
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => _estMoney(c.parsed.x) } } },
      scales: { x: { beginAtZero: true, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
}

function _estPintarFlujo(flujo, desde, hasta) {
  // El backend solo devuelve días con movimientos; rellenamos los huecos con 0
  let dias = [];
  if (flujo && flujo.ok && flujo.dias && flujo.dias.length) {
    const mapa = {};
    flujo.dias.forEach(d => { mapa[String(d.fecha).slice(0, 10)] = d; });
    for (let i = 29; i >= 0; i--) {
      const f = fLocal(new Date(Date.now() - i * 864e5));
      const d = mapa[f];
      dias.push({ fecha: f, entradas: d ? Number(d.entradas) || 0 : 0, salidas: d ? Number(d.salidas) || 0 : 0 });
    }
  }
  const labels = dias.length ? dias.map(d => String(d.fecha).slice(5)) : ['Sin datos'];
  _estChart('estFlujoBar', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'Entradas', data: dias.length ? dias.map(d => d.entradas) : [0], backgroundColor: 'rgba(30,122,70,0.75)', borderRadius: 4, maxBarThickness: 14 },
        { label: 'Salidas', data: dias.length ? dias.map(d => d.salidas) : [0], backgroundColor: 'rgba(192,57,43,0.7)', borderRadius: 4, maxBarThickness: 14 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12 } }, tooltip: { callbacks: { label: c => c.dataset.label + ': ' + _estMoney(c.parsed.y) } } },
      scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
}
