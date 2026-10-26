/* ---------- mi negocio (ingresos, utilidad y flujo de efectivo) ----------
   Dashboard financiero: consume los endpoints del negocio (estado de
   resultados, ventas, flujo de caja y cotizaciones) y los dibuja con
   Chart.js (lazy-load vía cargarScriptCDN, tema marfil+oro del panel).
   Filtros interactivos: rango de meses, mes del desglose, top de categorías
   y días del flujo. Lo de tráfico web vive en flujo.js (tab "Sitio web"). */
const EST_COLORS = ['#B08C3D', '#8A6D2F', '#E4D2A8', '#1e7a46', '#c0392b', '#8ab4e8', '#6b5b3e', '#d9a441', '#7a6a4f', '#3e7a5b', '#a86a6a', '#5b7a8a', '#8a7ab0', '#b0863d'];
const _estCharts = {};

/* Estado compartido: los datos se descargan UNA vez y los filtros solo
   re-pintan (slicing local). Solo 'mes' del desglose y rango del flujo
   piden datos nuevos al servidor (y quedan en caché). */
const EST = { finanzas: null, ventas: null, flujo: null, quotes: null, pnlActual: null, pnlPorMes: {}, flujoCache: {} };
const EST_F = { meses: 12, mes: null, top: 8, flujoDias: 30 };

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
// tick de eje: compacto ($38.8k) para vistas largas, completo para cortas
function _estTick(v, compacto) {
  const n = Number(v) || 0;
  if (compacto && Math.abs(n) >= 1000) return '$' + (n / 1000).toLocaleString('es-MX', { maximumFractionDigits: 1 }) + 'k';
  return '$' + n.toLocaleString('es-MX');
}
// estilo visual compartido: tooltips oscuros elegantes, rejilla suave
function _estTooltip() {
  return { backgroundColor: '#29241A', titleColor: '#E4D2A8', bodyColor: '#F5EFE2',
    padding: 10, cornerRadius: 8, boxPadding: 4, titleFont: { weight: '700' } };
}
function _estLegend() {
  return { position: 'top', labels: { usePointStyle: true, boxWidth: 8, boxHeight: 8, font: { size: 11 } } };
}
function _estEjeY(compacto) {
  return { beginAtZero: true, grid: { color: '#EAE2D0' }, border: { display: false },
    ticks: { callback: v => _estTick(v, compacto), font: { size: 11 } } };
}
function _estEjeX() {
  return { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } };
}

function _estUltimos30Dias(contarFn) {
  const out = [];
  for (let i = 29; i >= 0; i--) {
    const f = fLocal(new Date(Date.now() - i * 864e5));
    out.push([f, contarFn(f)]);
  }
  return out;
}

function _estLabelMes(m) {
  const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  const p = String(m || '').split('-');
  return MESES[(Number(p[1]) || 1) - 1] + ' ' + String(p[0] || '').slice(2);
}

function loadEstadisticas() {
  $('estKpis').innerHTML = '<p class="muted">Cargando…</p>';

  cargarChartJS().then(function () {
    Chart.defaults.font.family = 'Montserrat, sans-serif';
    Chart.defaults.color = '#29241A';
    Chart.defaults.borderColor = '#E5DDCC';

    const hoy = fLocal();
    const mes = hoy.slice(0, 7);
    if (!EST_F.mes) EST_F.mes = mes;
    if ($('estFMes') && !$('estFMes').value) $('estFMes').value = EST_F.mes;
    const hace29 = fLocal(new Date(Date.now() - 29 * 864e5));
    const base = CONFIG.API_URL + '?token=' + encodeURIComponent(token);
    const getj = url => fetch(url).then(r => r.json()).catch(() => null);

    Promise.all([
      getj(base + '&action=estado_resultados&mes=' + EST_F.mes),
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
      EST.pnlActual = pnl; EST.pnlPorMes[EST_F.mes] = pnl;
      EST.ventas = ventas; EST.flujo = flujo; EST.quotes = quotes; EST.finanzas = finanzas;
      EST.flujoCache[30] = flujo;
      pintarTodoEst();
    });
  }).catch(function () {
    $('estKpis').innerHTML = '<p class="muted">No se pudo cargar la librería de gráficas (sin conexión al CDN). Revisa tu internet y vuelve a intentar.</p>';
  });
}

/* Llamado por cada filtro. Solo 'mes' y 'flujoDias' necesitan datos nuevos;
   el resto re-pinta con lo ya descargado. */
function estFiltroCambiado(clave) {
  if (!EST.finanzas) return;
  if ($('estFMeses')) EST_F.meses = Number($('estFMeses').value) || 12;
  if ($('estFTop')) EST_F.top = Number($('estFTop').value) || 8;
  if (clave === 'mes' && $('estFMes') && $('estFMes').value) {
    EST_F.mes = $('estFMes').value;
    const cacheado = EST.pnlPorMes[EST_F.mes];
    if (cacheado) { EST.pnlActual = cacheado; pintarTodoEst(); return; }
    apiGet('estado_resultados&mes=' + EST_F.mes).then(function (p) {
      EST.pnlActual = p; EST.pnlPorMes[EST_F.mes] = p;
      pintarTodoEst();
    });
    return;
  }
  if (clave === 'flujoDias' && $('estFFlujo')) {
    EST_F.flujoDias = Number($('estFFlujo').value) || 30;
    const cacheado = EST.flujoCache[EST_F.flujoDias];
    if (cacheado) { EST.flujo = cacheado; pintarTodoEst(); return; }
    const hoy = fLocal();
    const desde = fLocal(new Date(Date.now() - (EST_F.flujoDias - 1) * 864e5));
    fetch(CONFIG.API_URL + '?token=' + encodeURIComponent(token) + '&action=flujo_caja&desde=' + desde + '&hasta=' + hoy)
      .then(r => r.json()).catch(() => null).then(function (f) {
        EST.flujo = f; EST.flujoCache[EST_F.flujoDias] = f;
        pintarTodoEst();
      });
    return;
  }
  pintarTodoEst();
}

function pintarTodoEst() {
  if (!EST.finanzas) return;
  _estPintarKpis(EST.pnlActual, EST.ventas, EST.flujo, EST.quotes, EST_F.mes);
  _estPintarResumen(EST.finanzas, EST_F.meses);
  _estPintarVentas(EST.ventas, EST.finanzas, EST_F.meses);
  _estPintarGastos(EST.pnlActual, EST_F.top);
  _estPintarFinanzas(EST.finanzas, EST_F.meses);
  _estPintarGastosMes(EST.finanzas, EST_F.meses, EST_F.top);
  _estPintarFlujo(EST.flujo, EST_F.flujoDias);
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
    html += '<div class="pnl-card ' + ((Number(flujo.neto) || 0) >= 0 ? 'good' : 'bad') + '"><div class="k">Flujo neto ' + (EST_F.flujoDias || 30) + ' días</div><div class="v">' + _estMoney(flujo.neto) + ' ' + (flujo.moneda_base || moneda) + '</div></div>';
  }
  const cotMes = ((quotes && quotes.quotes) || []).filter(q => String(q.fecha || '').indexOf(mes) === 0).length;
  html += '<div class="pnl-card"><div class="k">Cotizaciones del mes</div><div class="v">' + cotMes.toLocaleString('es-MX') + '</div></div>';
  $('estKpis').innerHTML = html || '<p class="muted">Sin datos todavía.</p>';
}

function _estPintarResumen(finanzas, nMeses) {
  const todos = (finanzas && finanzas.ok && finanzas.meses) ? finanzas.meses : [];
  const conDatos = todos.filter(m => Number(m.ingresos) > 0 || Number(m.gastos) > 0).slice(-(nMeses || 12));
  const labels = conDatos.map(m => _estLabelMes(m.mes));
  const hay = labels.length > 0;
  _estChart('estResumenBar', {
    type: 'bar',
    data: {
      labels: hay ? labels : ['Sin datos'],
      datasets: [
        { type: 'bar', label: 'Ingresos', data: hay ? conDatos.map(m => Number(m.ingresos) || 0) : [0],
          backgroundColor: 'rgba(30,122,70,0.8)', borderColor: '#1e7a46', borderWidth: 1,
          borderRadius: 6, maxBarThickness: 44, categoryPercentage: 0.72, barPercentage: 0.86 },
        { type: 'bar', label: 'Gastos', data: hay ? conDatos.map(m => Number(m.gastos) || 0) : [0],
          backgroundColor: 'rgba(192,57,43,0.75)', borderColor: '#c0392b', borderWidth: 1,
          borderRadius: 6, maxBarThickness: 44, categoryPercentage: 0.72, barPercentage: 0.86 },
        { type: 'line', label: 'Utilidad', data: hay ? conDatos.map(m => (Number(m.ingresos) || 0) - (Number(m.gastos) || 0)) : [0],
          borderColor: '#B08C3D', backgroundColor: '#B08C3D', borderWidth: 2.5,
          tension: 0.3, pointRadius: 4, pointHoverRadius: 6, pointStyle: 'circle' }
      ]
    },
    options: {
      responsive: true,
      animation: { duration: 600 },
      plugins: {
        legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' ' + c.dataset.label + ': ' + _estMoney(c.parsed.y) } })
      },
      scales: { x: _estEjeX(), y: _estEjeY((nMeses || 12) > 6) }
    }
  });
  // Explicacion con las cifras del MES SELECCIONADO en el filtro
  const sel = conDatos.filter(m => m.mes === EST_F.mes)[0] || conDatos[conDatos.length - 1];
  if (sel && $('estResumenTxt')) {
    const ing = Number(sel.ingresos) || 0, gas = Number(sel.gastos) || 0, util = ing - gas;
    $('estResumenTxt').innerHTML =
      '<b>¿De dónde salen estos números?</b> Los <b style="color:#1e7a46;">Ingresos</b> (verde) son todo el dinero que entró en el mes: las ventas más los ingresos que registraste en "Registrar ingreso". ' +
      'Los <b style="color:#c0392b;">Gastos</b> (rojo) son todo lo que salió: la suma de cada gasto que capturaste. ' +
      'La <b style="color:#8A6D2F;">Utilidad</b> (línea dorada) = Ingresos − Gastos. ' +
      '<br>Mes <b>' + sel.mes + '</b>: $' + ing.toLocaleString('es-MX') + ' − $' + gas.toLocaleString('es-MX') + ' = <b>' +
      (util < 0 ? '−$' + Math.abs(util).toLocaleString('es-MX') : '$' + util.toLocaleString('es-MX')) + '</b>. ' +
      '<i>Ojo: si el mes incluye compras de material o inventario, ese dinero no se perdió — se recupera cuando vendas esa mercancía.</i>';
  }
}

function _estPintarVentas(ventas, finanzas, nMeses) {
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
  const meses = Object.keys(porMes).sort().slice(-(nMeses || 12));
  const hay = meses.length > 0;
  _estChart('estVentasBar', {
    type: 'bar',
    data: {
      labels: hay ? meses.map(_estLabelMes) : ['Sin datos'],
      datasets: [{
        label: 'Ventas', data: hay ? meses.map(m => porMes[m]) : [0],
        backgroundColor: 'rgba(176,140,61,0.85)', borderColor: '#8A6D2F', borderWidth: 1,
        borderRadius: 7, maxBarThickness: 52, categoryPercentage: 0.7, barPercentage: 0.88
      }]
    },
    options: {
      responsive: true, animation: { duration: 600 },
      plugins: { legend: { display: false },
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' Ventas: ' + _estMoney(c.parsed.y) } }) },
      scales: { x: _estEjeX(), y: _estEjeY((nMeses || 12) > 6) }
    }
  });
}

function _estPintarGastos(pnl, topN) {
  const todos = (pnl && pnl.ok && pnl.gastos) ? Object.keys(pnl.gastos).map(k => [k, Number(pnl.gastos[k]) || 0]).sort((a, b) => b[1] - a[1]) : [];
  const g = topN >= 999 ? todos : todos.slice(0, topN || 8);
  const hay = g.length > 0;
  _estChart('estGastosBar', {
    type: 'bar',
    data: {
      labels: hay ? g.map(x => x[0]) : ['Sin datos'],
      datasets: [{
        label: 'Gastos', data: hay ? g.map(x => x[1]) : [0],
        backgroundColor: hay ? g.map((_, i) => 'rgba(192,57,43,' + (0.85 - i * 0.05) + ')') : 'rgba(192,57,43,0.65)',
        borderColor: '#c0392b', borderWidth: 1, borderRadius: 5, maxBarThickness: 24,
        categoryPercentage: 0.75, barPercentage: 0.9
      }]
    },
    options: {
      indexAxis: 'y', responsive: true, animation: { duration: 600 },
      plugins: { legend: { display: false },
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' ' + _estMoney(c.parsed.x) } }) },
      scales: { x: _estEjeY(false), y: _estEjeX() }
    }
  });
}

// Ingresos (ventas + otros ingresos) vs egresos (gastos)
function _estPintarFinanzas(fm, nMeses) {
  const datos = (fm.meses || []).slice(-(nMeses || 12));
  const hay = datos.length > 0;
  _estChart('estFinanzasBar', {
    type: 'bar',
    data: {
      labels: hay ? datos.map(x => _estLabelMes(x.mes)) : ['Sin datos'],
      datasets: [
        { label: 'Ingresos', data: hay ? datos.map(x => Number(x.ingresos) || 0) : [0],
          backgroundColor: 'rgba(30,122,70,0.8)', borderColor: '#1e7a46', borderWidth: 1,
          borderRadius: 5, maxBarThickness: 28, categoryPercentage: 0.68, barPercentage: 0.88 },
        { label: 'Egresos', data: hay ? datos.map(x => Number(x.gastos) || 0) : [0],
          backgroundColor: 'rgba(192,57,43,0.75)', borderColor: '#c0392b', borderWidth: 1,
          borderRadius: 5, maxBarThickness: 28, categoryPercentage: 0.68, barPercentage: 0.88 }
      ]
    },
    options: {
      responsive: true, animation: { duration: 600 },
      plugins: { legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' ' + c.dataset.label + ': ' + _estMoney(c.parsed.y) } }) },
      scales: { x: _estEjeX(), y: _estEjeY((nMeses || 12) > 6) }
    }
  });
}

// Gastos apilados por categoría (top N + Otro)
function _estPintarGastosMes(fm, nMeses, topN) {
  const datos = (fm.meses || []).slice(-(nMeses || 12));
  const meses = datos.map(x => x.mes);
  const totales = {};
  datos.forEach(x => {
    Object.keys(x.por_categoria || {}).forEach(k => {
      totales[k] = (totales[k] || 0) + (Number(x.por_categoria[k]) || 0);
    });
  });
  const limite = topN >= 999 ? 99 : (topN || 8);
  const top = Object.keys(totales).sort((a, b) => totales[b] - totales[a]).slice(0, limite);
  const cats = top.length ? top.concat(['Otro']) : [];
  const series = cats.map((cat, i) => ({
    label: cat,
    data: meses.map(m => {
      const x = datos.filter(y => y.mes === m)[0];
      if (!x) return 0;
      if (cat === 'Otro') {
        return Object.keys(x.por_categoria || {})
          .filter(k => top.indexOf(k) === -1)
          .reduce((s, k) => s + (Number(x.por_categoria[k]) || 0), 0);
      }
      return Number((x.por_categoria || {})[cat]) || 0;
    }),
    backgroundColor: cat === 'Otro' ? '#CFC5AE' : EST_COLORS[i % EST_COLORS.length],
    borderRadius: 3, maxBarThickness: 40
  }));
  const hay = meses.length > 0 && cats.length > 0;
  _estChart('estGastosMesBar', {
    type: 'bar',
    data: {
      labels: hay ? meses.map(_estLabelMes) : ['Sin datos'],
      datasets: hay ? series : [{ label: 'Gastos', data: [0], backgroundColor: EST_COLORS[0] }]
    },
    options: {
      responsive: true, animation: { duration: 600 },
      scales: { x: Object.assign(_estEjeX(), { stacked: true }),
        y: Object.assign(_estEjeY((nMeses || 12) > 6), { stacked: true }) },
      plugins: { legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' ' + c.dataset.label + ': ' + _estMoney(c.parsed.y) } }) }
    }
  });
}

function _estPintarFlujo(flujo, nDias) {
  // El backend solo devuelve días con movimientos; rellenamos los huecos con 0
  let dias = [];
  nDias = nDias || 30;
  if (flujo && flujo.ok && flujo.dias && flujo.dias.length) {
    const mapa = {};
    flujo.dias.forEach(d => { mapa[String(d.fecha).slice(0, 10)] = d; });
    for (let i = nDias - 1; i >= 0; i--) {
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
        { label: 'Entradas', data: dias.length ? dias.map(d => d.entradas) : [0],
          backgroundColor: 'rgba(30,122,70,0.8)', borderColor: '#1e7a46', borderWidth: 1,
          borderRadius: 4, maxBarThickness: nDias > 30 ? 8 : 16, categoryPercentage: 0.7, barPercentage: 0.9 },
        { label: 'Salidas', data: dias.length ? dias.map(d => d.salidas) : [0],
          backgroundColor: 'rgba(192,57,43,0.75)', borderColor: '#c0392b', borderWidth: 1,
          borderRadius: 4, maxBarThickness: nDias > 30 ? 8 : 16, categoryPercentage: 0.7, barPercentage: 0.9 }
      ]
    },
    options: {
      responsive: true, animation: { duration: 600 },
      plugins: { legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' ' + c.dataset.label + ': ' + _estMoney(c.parsed.y) } }) },
      scales: { x: _estEjeX(), y: _estEjeY(true) }
    }
  });
}
