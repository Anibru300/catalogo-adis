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
      getj(base + '&action=finanzas_mensual'),
    ]).then(function ([pnl, ventas, flujo, quotes, finanzas]) {
      const sinConexion = !pnl && !ventas && !flujo && !quotes;
      if (sinConexion) {
        $('estKpis').innerHTML = '<p class="muted">Sin acceso o error de conexión. Si acabas de actualizar el script, despliega una <b>nueva versión</b> en Apps Script.</p>';
        return;
      }
      _estPintarKpis(pnl, ventas, flujo, quotes, mes);
      _estPintarVentas(ventas, finanzas);
      _estPintarGastos(pnl);
      _estPintarFlujo(flujo, hace29, hoy);
      // Evolución 12 meses: solo si el backend ya tiene el endpoint (redeploy)
      if (finanzas && finanzas.ok && finanzas.meses) {
        _estPintarResumen(finanzas);
        _estPintarFinanzas(finanzas);
        _estPintarGastosMes(finanzas);
      }
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
    html += '<div class="pnl-card"><div class="k">Gastos del mes</div><div class="v">' + _estMoney(pnl.total_gastos) + ' ' + moneda + '</div></div>';
    html += '<div class="pnl-card ' + ((Number(pnl.utilidad_neta) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Utilidad neta del mes</div><div class="v">' + _estMoney(pnl.utilidad_neta) + ' ' + moneda + '</div></div>';
  }
  if (flujo && flujo.ok) {
    html += '<div class="pnl-card ' + ((Number(flujo.neto) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Flujo neto 30 días</div><div class="v">' + _estMoney(flujo.neto) + ' ' + (flujo.moneda_base || moneda) + '</div></div>';
  }
  const cotMes = ((quotes && quotes.quotes) || []).filter(q => String(q.fecha || '').indexOf(mes) === 0).length;
  html += '<div class="pnl-card"><div class="k">Cotizaciones del mes</div><div class="v">' + cotMes.toLocaleString('es-MX') + '</div></div>';
  $('estKpis').innerHTML = html || '<p class="muted">Sin datos todavía.</p>';
}

function _estPintarVentas(ventas, finanzas) {
  // Fuente principal: finanzas_mensual (sus 'ingresos' = ventas de la hoja +
  // cobros tipo venta; es la misma cifra del KPI y no deja huecos). Si no hay,
  // caemos al agregado por mes de la hoja Ventas y luego al calculo local.
  let porMes = null;
  if (finanzas && finanzas.ok && finanzas.meses) {
    porMes = {};
    finanzas.meses.forEach(function (f) { if (Number(f.ingresos) > 0) porMes[f.mes] = Number(f.ingresos) || 0; });
  }
  if (!porMes) porMes = (ventas && ventas.porMes) || null;
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

function _estPintarResumen(finanzas) {
  const meses = (finanzas && finanzas.ok && finanzas.meses) ? finanzas.meses : [];
  const conDatos = meses.filter(m => Number(m.ingresos) > 0 || Number(m.gastos) > 0);
  const labels = conDatos.map(m => m.mes);
  const hay = labels.length > 0;
  _estChart('estResumenBar', {
    type: 'bar',
    data: {
      labels: hay ? labels : ['Sin datos'],
      datasets: [
        { type: 'bar', label: 'Ingresos', data: hay ? conDatos.map(m => Number(m.ingresos) || 0) : [0],
          backgroundColor: 'rgba(30,122,70,0.75)', borderColor: '#1e7a46', borderWidth: 1,
          borderRadius: 6, maxBarThickness: 42 },
        { type: 'bar', label: 'Gastos', data: hay ? conDatos.map(m => Number(m.gastos) || 0) : [0],
          backgroundColor: 'rgba(192,57,43,0.7)', borderColor: '#c0392b', borderWidth: 1,
          borderRadius: 6, maxBarThickness: 42 },
        { type: 'line', label: 'Utilidad', data: hay ? conDatos.map(m => (Number(m.ingresos) || 0) - (Number(m.gastos) || 0)) : [0],
          borderColor: '#B08C3D', backgroundColor: '#B08C3D', borderWidth: 2,
          tension: 0.25, pointRadius: 4, pointStyle: 'circle' }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        tooltip: { callbacks: { label: c => ' ' + c.dataset.label + ': ' + _estMoney(c.parsed.y) } }
      },
      scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
  // Explicacion en lenguaje del dueno, con las cifras reales del ultimo mes con datos
  const ult = conDatos[conDatos.length - 1];
  if (ult && $('estResumenTxt')) {
    const ing = Number(ult.ingresos) || 0, gas = Number(ult.gastos) || 0, util = ing - gas;
    $('estResumenTxt').innerHTML =
      '<b>¿De dónde salen estos números?</b> Los <b style="color:#1e7a46;">Ingresos</b> (verde) son todo el dinero que entró en el mes: las ventas más los ingresos que registraste en "Registrar ingreso". ' +
      'Los <b style="color:#c0392b;">Gastos</b> (rojo) son todo lo que salió: la suma de cada gasto que capturaste. ' +
      'La <b style="color:#8A6D2F;">Utilidad</b> (línea dorada) = Ingresos − Gastos. ' +
      '<br>Mes <b>' + ult.mes + '</b>: $' + ing.toLocaleString('es-MX') + ' − $' + gas.toLocaleString('es-MX') + ' = <b>' +
      (util < 0 ? '−$' + Math.abs(util).toLocaleString('es-MX') : '$' + util.toLocaleString('es-MX')) + '</b>. ' +
      '<i>Ojo: si el mes incluye compras de material o inventario, ese dinero no se perdió — se recupera cuando vendas esa mercancía.</i>';
  }
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

function _estLabelMes(m) {
  const MESES_CORTOS = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  const p = String(m || '').split('-');
  return MESES_CORTOS[(Number(p[1]) || 1) - 1] + ' ' + String(p[0] || '').slice(2);
}

// Ingresos (ventas + otros ingresos) vs egresos (gastos), últimos 12 meses
function _estPintarFinanzas(fm) {
  const meses = (fm.meses || []).map(x => x.mes);
  const hay = meses.length > 0;
  _estChart('estFinanzasBar', {
    type: 'bar',
    data: {
      labels: hay ? meses.map(_estLabelMes) : ['Sin datos'],
      datasets: [
        { label: 'Ingresos', data: hay ? fm.meses.map(x => Number(x.ingresos) || 0) : [0],
          backgroundColor: 'rgba(30,122,70,0.75)', borderRadius: 5, maxBarThickness: 26 },
        { label: 'Egresos', data: hay ? fm.meses.map(x => Number(x.gastos) || 0) : [0],
          backgroundColor: 'rgba(192,57,43,0.7)', borderRadius: 5, maxBarThickness: 26 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12 } },
        tooltip: { callbacks: { label: c => c.dataset.label + ': ' + _estMoney(c.parsed.y) } } },
      scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } }
    }
  });
}

// Gastos apilados por categoría (top 5 + Otro), últimos 12 meses
function _estPintarGastosMes(fm) {
  const meses = (fm.meses || []).map(x => x.mes);
  // categorías ordenadas por total acumulado del año
  const totales = {};
  (fm.meses || []).forEach(x => {
    Object.keys(x.por_categoria || {}).forEach(k => {
      totales[k] = (totales[k] || 0) + (Number(x.por_categoria[k]) || 0);
    });
  });
  const top = Object.keys(totales).sort((a, b) => totales[b] - totales[a]).slice(0, 5);
  const cats = top.length ? top.concat(['Otro']) : [];
  const series = cats.map(cat => ({
    label: cat,
    data: meses.map(m => {
      const x = fm.meses.filter(y => y.mes === m)[0];
      if (!x) return 0;
      if (cat === 'Otro') {
        return Object.keys(x.por_categoria || {})
          .filter(k => top.indexOf(k) === -1)
          .reduce((s, k) => s + (Number(x.por_categoria[k]) || 0), 0);
      }
      return Number((x.por_categoria || {})[cat]) || 0;
    }),
    backgroundColor: EST_COLORS[cats.indexOf(cat) % EST_COLORS.length]
  }));
  const hay = meses.length > 0 && cats.length > 0;
  _estChart('estGastosMesBar', {
    type: 'bar',
    data: {
      labels: hay ? meses.map(_estLabelMes) : ['Sin datos'],
      datasets: hay ? series : [{ label: 'Gastos', data: [0], backgroundColor: EST_COLORS[0] }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true,
        ticks: { callback: v => '$' + Number(v).toLocaleString('es-MX') } } },
      plugins: { legend: { position: 'top', labels: { boxWidth: 12 } },
        tooltip: { callbacks: { label: c => c.dataset.label + ': ' + _estMoney(c.parsed.y) } } }
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
