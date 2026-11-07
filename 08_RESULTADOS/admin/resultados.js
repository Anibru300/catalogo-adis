/* ----- FASE 5: flujo de efectivo real (cobros vs pagos) ----- */
function loadFlujoCaja(){
  const hoy = fLocal();
  const rango = ($('flujoRango') && $('flujoRango').value) || 'mes';
  let desde;
  if (rango === 'hoy') desde = hoy;
  else if (rango === 'semana') desde = fLocal(new Date(Date.now() - 6 * 864e5));
  else desde = hoy.slice(0, 8) + '01';
  apiGet('flujo_caja&desde=' + desde + '&hasta=' + hoy).then(d=>{
    if (!d || !d.ok) { $('flujoKpis').innerHTML = '<p class="muted">'+esc(errMsg(d,'Sin acceso.'))+'</p>'; return; }
    const f = n => fmtMoney(n) + ' ' + d.moneda_base;
    const clsN = d.neto >= 0 ? 'good' : 'bad';
    let kpis =
      '<div class="pnl-card good"><div class="k">Entradas ('+d.num_cobros+' cobro(s))</div><div class="v">'+f(d.entradas)+'</div></div>' +
      '<div class="pnl-card bad"><div class="k">Salidas ('+d.num_pagos+' pago(s))</div><div class="v">'+f(d.salidas)+'</div></div>' +
      '<div class="pnl-card '+clsN+'"><div class="k">Flujo neto</div><div class="v">'+f(d.neto)+'</div></div>';
    // FASE 0-1: desglose por actividad (solo si el backend ya lo devuelve)
    const pa = d.por_actividad;
    if (pa) {
      const acts = [['operacion','Operación'],['inversion','Inversión'],['financiamiento','Financiamiento']];
      kpis += acts.map(a=>{
        const x = pa[a[0]] || {entradas:0, salidas:0};
        const n = (Number(x.entradas)||0) - (Number(x.salidas)||0);
        return '<div class="pnl-card '+(n>=0?'good':'bad')+'"><div class="k">'+a[1]+' <span style="font-size:0.68rem;">(E '+f(x.entradas)+' · S '+f(x.salidas)+')</span></div><div class="v">'+f(n)+'</div></div>';
      }).join('');
    }
    $('flujoKpis').innerHTML = kpis;
    const dias = d.dias || [];
    const mx = Math.max(1, ...dias.map(x => Math.max(x.entradas, x.salidas)));
    $('flujoDiario').innerHTML = dias.length ? dias.map(x => {
      const hE = Math.max(2, Math.round(x.entradas / mx * 100));
      const hS = Math.max(2, Math.round(x.salidas / mx * 100));
      return '<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:1px;min-width:8px;">' +
        '<div class="flow-bar" style="height:'+hE+'px;background:#3fae6a;" title="'+x.fecha+' entradas '+f(x.entradas)+'"></div>' +
        '<div class="flow-bar" style="height:'+hS+'px;background:#c05a5a;" title="'+x.fecha+' salidas '+f(x.salidas)+'"></div></div>';
    }).join('') : '<p class="muted">Sin movimientos en el rango.</p>';
    $('flujoDiarioLeyenda').textContent = dias.length ? 'Verde = entradas · Rojo = salidas · ' + dias.length + ' día(s) con movimiento' : '';
    $('flujoMovs').innerHTML = (d.movimientos || []).length ? d.movimientos.map(m=>
      '<tr><td>'+esc(m.fecha)+'</td><td class="gold">'+esc(m.folio||'—')+'</td><td>'+esc(m.concepto||'—')+'</td>' +
      '<td><span style="color:'+(m.tipo==='entrada'?'#7ce3a1':'#e37c7c')+';font-weight:600;font-size:0.75rem;">'+(m.tipo==='entrada'?'ENTRADA':'SALIDA')+'</span></td>' +
      '<td style="color:'+(m.tipo==='entrada'?'#7ce3a1':'#e37c7c')+';font-weight:600;">'+(m.tipo==='entrada'?'+':'−')+fmtMoney(m.monto_base)+'</td>' +
      '<td>'+esc(m.metodo||'—')+'</td></tr>').join('')
      : '<tr><td colspan="6" class="muted">Sin movimientos en el rango.</td></tr>';
  }).catch(()=>{});
}

/* ----- FASE 6: alertas priorizadas + ficha financiera de proyecto ----- */
function loadAlertas(){
  apiGet('alertas').then(d=>{
    const box = $('alertasBox');
    if (!box) return;
    if (!d || !d.ok) { box.innerHTML=''; return; }
    const als = d.alertas || [];
    if (!als.length) { box.innerHTML = '<div class="card-box" style="border-left:3px solid #3fae6a;"><strong style="color:#7ce3a1;">Sin alertas.</strong> <span class="muted">Inventario, cobros, pagos, cotizaciones y compras bajo control.</span></div>'; return; }
    const colorP = { CRITICA: '#e37c7c', ALTA: '#e8b96a', MEDIA: '#8ab4e8' };
    box.innerHTML = '<div class="card-box" style="border-left:3px solid #e37c7c;"><strong>'+als.length+' alerta(s):</strong> <span class="muted">' +
      als.length + ' pendiente(s) — ' + als.filter(a=>a.prioridad==='CRITICA').length + ' crítica(s), ' +
      als.filter(a=>a.prioridad==='ALTA').length + ' alta(s), ' + als.filter(a=>a.prioridad==='MEDIA').length + ' media(s).</span>' +
      '<table style="margin-top:0.6rem;"><tbody>' + als.slice(0, 15).map(a=>
        '<tr><td style="white-space:nowrap;"><span style="color:'+(colorP[a.prioridad]||'#e8b96a')+';font-weight:700;font-size:0.7rem;">'+esc(a.prioridad)+'</span></td>' +
        '<td style="font-size:0.85rem;">'+esc(a.detalle)+'</td></tr>').join('') +
      (als.length > 15 ? '<tr><td colspan="2" class="muted">… y '+(als.length-15)+' más (revísalas en su módulo).</td></tr>' : '') +
      '</tbody></table></div>';
  }).catch(()=>{});
}
function fillPnlProyectos(){
  const sel = $('pnlProyecto');
  if (!sel) return;
  const val = sel.value;
  sel.innerHTML = '<option value="">Todo el negocio</option>' +
    proyCache.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.folio||'')+' · '+esc(p.nombre)+'</option>').join('');
  sel.value = val;
}
// Ficha PRESUPUESTO VS REAL del proyecto + movimientos directos (gasto/ingreso)
function fichaProyecto(id){
  const p = proyCache.filter(x=>String(x.id)===String(id))[0];
  if (!p) return;
  const base = biz.config && biz.config.moneda_base || 'MXN';
  const presup = Number(p.presupuesto)||0, cobr = Number(p.cobrado_base)||0;
  const gastos = Number(p.gastos_real)||0, ingExt = Number(p.ingresos_extra)||0;
  const ingresosTot = cobr + ingExt;
  const util = Number(p.utilidad_real)||0;
  const pct = presup > 0 ? Math.round(gastos / presup * 100) : null;
  $('proyForms').innerHTML = '<div class="card-box" style="border-left:3px solid var(--gold);">' +
    '<div class="toolbar" style="margin-bottom:0.5rem;"><strong>'+esc(p.folio||'')+' · '+esc(p.nombre)+'</strong> <span class="muted">'+esc(p.cliente||'')+'</span>' +
    '<button class="btn btn-sm" onclick="$(\'proyForms\').innerHTML=\'\'" style="margin-left:auto;">Cerrar</button></div>' +
    '<div class="pnl-cards">' +
    '<div class="pnl-card"><div class="k">Presupuesto</div><div class="v">'+fmtMoney(presup)+' '+esc(p.moneda||'')+'</div></div>' +
    '<div class="pnl-card"><div class="k">Cobrado (ventas)</div><div class="v" style="font-size:0.95rem;">'+fmtMoney(cobr)+' '+base+'</div></div>' +
    '<div class="pnl-card bad"><div class="k">Gastos reales</div><div class="v" style="font-size:0.95rem;">'+fmtMoney(gastos)+' '+base+(pct!=null?' <small style="font-size:0.7rem;">'+pct+'% del presupuesto</small>':'')+'</div></div>' +
    '<div class="pnl-card '+(util>=0?'good':'bad')+'"><div class="k">Utilidad real</div><div class="v" style="font-size:0.95rem;">'+fmtMoney(util)+' '+base+'</div></div>' +
    '</div>' +
    '<div class="row" style="margin-top:0.8rem;">' +
    '<div><label>Tipo</label><select id="pmTipo"><option value="gasto">Gasto</option><option value="ingreso">Ingreso</option><option value="presupuesto">Ajuste presupuesto (+)</option></select></div>' +
    '<div><label>Monto *</label><input type="number" id="pmMonto" min="0" step="0.01" placeholder="0.00"></div>' +
    '<div><label>Moneda</label><select id="pmMoneda"><option value="MXN">MXN</option><option value="USD">USD</option></select></div>' +
    '<div><label>Fecha</label><input type="date" id="pmFecha" value="'+fLocal()+'"></div>' +
    '</div>' +
    '<label>Descripción</label><input id="pmDesc" placeholder="Ej. Mano de obra, compra de material...">' +
    '<div class="toolbar" style="margin-top:0.8rem;"><button class="btn btn-solid btn-sm" onclick="saveProyectoMov(\''+p.id+'\')">Guardar movimiento</button></div>' +
    '</div>';
  $('proyForms').scrollIntoView({behavior:'smooth', block:'nearest'});
}
function saveProyectoMov(id){
  const monto = parseFloat($('pmMonto').value)||0;
  if (monto <= 0) { notice('El monto debe ser mayor que cero.', false); return; }
  apiPost({tipo:'proyecto_mov', proyecto_id:id, mov_tipo:$('pmTipo').value, monto,
    moneda:$('pmMoneda').value, fecha:$('pmFecha').value, descripcion:$('pmDesc').value.trim()}).then(d=>{
    notice(d&&d.ok?'Movimiento guardado.':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadProyectos();
  }).catch(()=>notice('Error de conexión.', false));
}

/* ----- estado de resultados ----- */
function generarPNL(){
  const mes = $('pnlMes').value;
  if (!mes) { notice('Selecciona un mes.', false); return; }
  const proy = $('pnlProyecto') ? $('pnlProyecto').value : '';
  fetch(CONFIG.API_URL + '?action=estado_resultados&mes=' + mes + (proy ? '&proyecto_id=' + encodeURIComponent(proy) : '') + '&token=' + encodeURIComponent(token))
    .then(r=>r.json()).then(d=>{
      if (!d || !d.ok) { $('pnlCards').innerHTML='<p class="muted">'+esc(errMsg(d,'Error'))+'</p>'; return; }
      pnlData = d;
      const f = n => fmtMoney(n)+' '+d.moneda_base;
      const n = v => Number(v)||0; // FASE 0-1: compatibilidad — campos nuevos pueden venir undefined (backend sin redeploy)
      const tituloProy = d.proyecto_id ? ' <span class="muted" style="font-size:0.75rem;">(proyecto)</span>' : '';
      // niveles del estado de resultados (retrocompatible con backend viejo)
      const ventas = n(d.ingresos);
      const costos = n(d.costos);
      const uBruta = n(d.utilidad_bruta);
      const gOp = n(d.total_gastos);
      const uOp = d.utilidad_operativa!=null ? n(d.utilidad_operativa) : uBruta - gOp;
      const otros = n(d.otros_resultados);
      const uNeta = d.utilidad_neta!=null ? n(d.utilidad_neta) : uOp + otros;
      const margenBruto = n(d.margen_bruto), margenOp = n(d.margen_operativo), margenNeto = n(d.margen_neto);
      const vExtra = n(d.ventas_extra);
      // ETAPA 1: sin costos registrados la utilidad bruta no es calculable (no mostrar 100%)
      const sinCostos = costos === 0 && ventas > 0;
      const txtBruta = sinCostos ? 'No calculable (sin costos registrados)' : f(uBruta);
      const txtMargenBruto = sinCostos ? '—' : margenBruto.toFixed(1) + '%';
      const txtMargenOp = '—', txtMargenNeto = '—'; // Etapa 1: márgenes op/neto engañosos sin costos
      const rProv = d.resultado_provisional != null ? n(d.resultado_provisional) : uNeta;
      $('pnlCards').innerHTML = '<div class="pnl-cards">' +
        '<div class="pnl-card"><div class="k">Ventas netas ('+n(d.num_ventas)+')'+tituloProy+'</div><div class="v">'+f(ventas)+'</div></div>' +
        '<div class="pnl-card"><div class="k">Costo de ventas</div><div class="v">'+f(costos)+'</div></div>' +
        '<div class="pnl-card '+(uBruta>=0?'good':'bad')+'"><div class="k">Utilidad bruta</div><div class="v"'+(sinCostos?' style="font-size:0.85rem;"':'')+'>'+txtBruta+' <small style="font-size:0.7rem;">'+txtMargenBruto+'</small></div></div>' +
        '<div class="pnl-card"><div class="k">Gastos operativos</div><div class="v">'+f(gOp)+'</div></div>' +
        '<div class="pnl-card '+(uOp>=0?'good':'bad')+'"><div class="k">Utilidad operativa</div><div class="v">'+f(uOp)+' <small style="font-size:0.7rem;">'+txtMargenOp+'</small></div></div>' +
        '<div class="pnl-card '+(otros>=0?'good':'bad')+'"><div class="k">Otros resultados ('+n(d.num_otros_resultados)+')</div><div class="v">'+f(otros)+'</div></div>' +
        '<div class="pnl-card '+(rProv>=0?'good':'bad')+'"><div class="k">Resultado provisional del periodo</div><div class="v">'+f(rProv)+' <small style="font-size:0.7rem;">'+txtMargenNeto+'</small></div></div>' +
        '</div>';
      const cats = Object.keys(d.gastos||{}).sort();
      const finIn = n(d.financiamiento_entrante);
      const excluidos = [
        ['Retiros del propietario', n(d.retiros)],
        ['Compras de inventario', n(d.inventario)],
        ['Inversiones', n(d.inversiones)],
        ['Sin clasificar', n(d.sin_clasificar)]
      ].filter(x=>x[1]>0);
      $('pnlBox').style.display='block';
      $('pnlTable').innerHTML =
        '<tr><td><strong>VENTAS NETAS</strong> <span class="muted">('+n(d.num_ventas)+' ventas'+(vExtra>0?' + '+f(vExtra)+' en ventas extra':'')+')</span></td><td style="text-align:right;"><strong>'+f(ventas)+'</strong></td></tr>' +
        '<tr><td>(−) COSTO DE VENTAS</td><td style="text-align:right;">'+f(costos)+'</td></tr>' +
        '<tr><td><strong>= UTILIDAD BRUTA</strong></td><td style="text-align:right;"><strong>'+txtBruta+'</strong> <span class="muted" style="font-size:0.72rem;">'+txtMargenBruto+'</span></td></tr>' +
        '<tr><td colspan="2" style="color:var(--gold);">Gastos operativos por categoría</td></tr>' +
        (cats.length ? cats.map(c=>'<tr><td>&nbsp;&nbsp;'+esc(c)+'</td><td style="text-align:right;">'+f(d.gastos[c])+'</td></tr>').join('') : '<tr><td colspan="2" class="muted">Sin gastos operativos este mes.</td></tr>') +
        '<tr><td>(−) TOTAL GASTOS OPERATIVOS</td><td style="text-align:right;">'+f(gOp)+'</td></tr>' +
        '<tr><td><strong>= UTILIDAD OPERATIVA</strong></td><td style="text-align:right;"><strong>'+f(uOp)+'</strong> <span class="muted" style="font-size:0.72rem;">'+txtMargenOp+'</span></td></tr>' +
        '<tr><td>(+/−) OTROS RESULTADOS <span class="muted">('+n(d.num_otros_resultados)+' mov.)</span></td><td style="text-align:right;">'+f(otros)+'</td></tr>' +
        (finIn>0 ? '<tr><td colspan="2" class="muted" style="font-size:0.78rem;">Entradas de financiamiento (no son ingreso): '+f(finIn)+'</td></tr>' : '') +
        '<tr><td>(−) IMPUESTOS</td><td style="text-align:right;">'+f(n(d.impuestos))+'</td></tr>' +
        '<tr><td><strong>= RESULTADO PROVISIONAL DEL PERIODO</strong></td><td style="text-align:right;"><strong>'+f(rProv)+'</strong> <span class="muted" style="font-size:0.72rem;">'+txtMargenNeto+'</span></td></tr>' +
        (excluidos.length ? '<tr><td colspan="2" class="muted" style="font-size:0.78rem;padding-top:0.8rem;">Movimientos excluidos del resultado: ' + excluidos.map(x=>x[0]+' '+f(x[1])).join(' · ') + '</td></tr>' : '');
      const adv = $('pnlAdvertencia');
      if (adv) {
        const notas = [];
        if (d.motivo_provisional) notas.push('<strong>ℹ️ Resultado provisional (Etapa 1):</strong> <span class="muted">'+esc(d.motivo_provisional)+'</span>');
        if (d.advertencia) notas.push('<strong>⚠️ Revisar clasificación:</strong> <span class="muted">'+esc(d.advertencia)+'</span>');
        adv.innerHTML = notas.length ? '<div class="card-box" style="border-left:3px solid #e8b96a;margin-bottom:1rem;">' + notas.join('<br>') + '</div>' : '';
      }
    }).catch(()=>{ $('pnlCards').innerHTML='<p class="muted">Error de conexion.</p>'; });
}
function printPNL(){
  if (!pnlData) { notice('Primero genera el resultado.', false); return; }
  const d = pnlData, f = n => fmtMoney(n)+' '+d.moneda_base;
  const mesTxt = $('pnlMes').value;
  const sinCostos = (Number(d.costos)||0) === 0 && (Number(d.ingresos)||0) > 0;
  $('printArea').innerHTML =
    '<h1>ADIS Diseño & Remodelación</h1><div class="pq-meta">Estado de resultados — PROVISIONAL (Etapa 1) · ' + mesTxt + ' · Moneda: ' + d.moneda_base + '</div>' +
    '<table><tbody>' + $('pnlTable').innerHTML + '</tbody></table>' +
    '<p style="margin-top:1rem;font-size:0.85rem;">Ventas: '+(Number(d.num_ventas)||0)+' · Margen bruto: '+(sinCostos?'—':(Number(d.margen_bruto)||0).toFixed(1)+'%')+' · Margen operativo y neto: — (Etapa 1)</p>' +
    (d.motivo_provisional ? '<p style="font-size:0.8rem;">ℹ️ ' + esc(d.motivo_provisional) + '</p>' : '') +
    (d.advertencia ? '<p style="font-size:0.8rem;">⚠️ ' + esc(d.advertencia) + '</p>' : '') +
    '<div class="pq-foot">Generado desde el panel administrativo ADIS</div>';
  window.print();
}



/* ----- ETAPA 1: control de ingresos y egresos (a dónde se va el efectivo; no es utilidad contable) ----- */
const CIE_NAT = { operativo:'Gastos operativos', costo_directo:'Costos directos', inventario:'Compra de mercancía',
  inversion:'Inversiones', retiro:'Retiros del propietario', por_clasificar:'Pendientes de clasificar' };
let cieData = null;

function ciePeriodoRapido(tipo){
  const hoy = fLocal();
  if (tipo === 'mes') { $('cieDesde').value = hoy.slice(0,8)+'01'; $('cieHasta').value = hoy; }
  else if (tipo === 'anterior') {
    const ini = new Date(); ini.setDate(1); ini.setMonth(ini.getMonth()-1);
    const fin = new Date(); fin.setDate(0);
    $('cieDesde').value = fLocal(ini); $('cieHasta').value = fLocal(fin);
  } else if (tipo === 'anio') { $('cieDesde').value = hoy.slice(0,4)+'-01-01'; $('cieHasta').value = hoy; }
  loadControlIE();
}

function loadControlIE(){
  const hoy = fLocal();
  if ($('cieDesde') && !$('cieDesde').value) $('cieDesde').value = hoy.slice(0,8)+'01';
  if ($('cieHasta') && !$('cieHasta').value) $('cieHasta').value = hoy;
  // categorías configurables (mismo catálogo del negocio)
  const selCat = $('cieCategoria');
  if (selCat && selCat.options.length <= 1) {
    const cats = (biz.config && biz.config.categorias_gastos) || [];
    selCat.innerHTML = '<option value="">Todas</option>' + cats.map(c=>'<option value="'+esc(c)+'">'+esc(c)+'</option>').join('');
  }
  const params = [];
  if ($('cieDesde').value) params.push('desde='+$('cieDesde').value);
  if ($('cieHasta').value) params.push('hasta='+$('cieHasta').value);
  const nat = $('cieNaturaleza').value, cat = selCat.value, mon = $('cieMoneda').value;
  if (nat) params.push('naturaleza='+encodeURIComponent(nat));
  if (cat) params.push('categoria='+encodeURIComponent(cat));
  if (mon) params.push('moneda='+encodeURIComponent(mon));
  $('cieKpis').innerHTML = '<div class="pnl-card"><div class="k">Cargando…</div><div class="v">—</div></div>';
  cargarChartJS().then(()=>{
    apiGet('control_ie&'+params.join('&')).then(d=>{
      if (!d || !d.ok) { $('cieKpis').innerHTML = '<p class="muted">'+esc(errMsg(d,'Sin acceso.'))+'</p>'; return; }
      cieData = d;
      ciePintar(d);
    }).catch(()=>{ $('cieKpis').innerHTML = '<p class="muted">Error de conexión.</p>'; });
  }).catch(()=>{ $('cieKpis').innerHTML = '<p class="muted">No se pudo cargar la librería de gráficas (sin conexión al CDN).</p>'; });
}

// simulador: recalcula en vivo (Egresos totales = suma de los 5 rubros; Variación = Ingresos − Egresos)
function cieSimular(){
  const g = id => parseFloat($(id).value)||0;
  const ing = g('cieSimIngresos');
  const eg = g('cieSimOperativo') + g('cieSimMercancia') + g('cieSimRetiros') + g('cieSimInversiones') + g('cieSimCostos');
  const neto = ing - eg;
  const base = (cieData && cieData.moneda_base) || 'MXN';
  $('cieSimEgresos').value = fmtMoney(eg)+' '+base;
  const ne = $('cieSimNeto');
  ne.value = (neto>=0?'+':'−')+fmtMoney(Math.abs(neto))+' '+base;
  ne.style.color = neto>=0 ? '#1e7a46' : '#c0392b';
}

function ciePintar(d){
  const base = d.moneda_base || 'MXN';
  const f = n => fmtMoney(n)+' '+base;
  const pn = (d.egresos && d.egresos.por_naturaleza) || {};
  const nPn = (d.egresos && d.egresos.num_por_naturaleza) || {};
  const num = (v)=>Number(v)||0;
  const neto = num(d.variacion_neta);

  // --- indicadores (6 cards)
  $('cieKpis').innerHTML =
    '<div class="pnl-card good"><div class="k">Ingresos recibidos</div><div class="v">'+f(d.ingresos.total_base)+'</div></div>' +
    '<div class="pnl-card bad"><div class="k">Egresos pagados</div><div class="v">'+f(d.egresos.total_base)+'</div></div>' +
    '<div class="pnl-card '+(neto>=0?'good':'bad')+'"><div class="k">Flujo neto</div><div class="v">'+f(neto)+'</div></div>' +
    '<div class="pnl-card"><div class="k">Retiros del propietario</div><div class="v">'+f(num(pn.retiro))+'</div></div>' +
    '<div class="pnl-card"><div class="k">Compra de mercancía</div><div class="v">'+f(num(pn.inventario))+'</div></div>' +
    '<div class="pnl-card"><div class="k">Gastos operativos</div><div class="v">'+f(num(pn.operativo))+'</div></div>';

  // --- simulador: precargar con los valores reales del periodo
  $('cieSimIngresos').value = num(d.ingresos.total_base).toFixed(2);
  $('cieSimOperativo').value = num(pn.operativo).toFixed(2);
  $('cieSimMercancia').value = num(pn.inventario).toFixed(2);
  $('cieSimRetiros').value = num(pn.retiro).toFixed(2);
  $('cieSimInversiones').value = num(pn.inversion).toFixed(2);
  $('cieSimCostos').value = num(pn.costo_directo).toFixed(2);
  cieSimular();

  // --- (a) barras comparativas ingresos vs egresos por mes
  const mensual = ((d.mensual)||[]).filter(m=>num(m.ingresos)>0 || num(m.egresos)>0);
  const hayMes = mensual.length > 0;
  _estChart('cieMensualBar', {
    type: 'bar',
    data: {
      labels: hayMes ? mensual.map(m=>_estLabelMes(m.mes)) : ['Sin datos'],
      datasets: [
        { label: 'Ingresos', data: hayMes ? mensual.map(m=>num(m.ingresos)) : [0],
          backgroundColor: 'rgba(30,122,70,0.8)', borderColor: '#1e7a46', borderWidth: 1,
          borderRadius: 6, maxBarThickness: 44, categoryPercentage: 0.72, barPercentage: 0.86 },
        { label: 'Egresos', data: hayMes ? mensual.map(m=>num(m.egresos)) : [0],
          backgroundColor: 'rgba(192,57,43,0.75)', borderColor: '#c0392b', borderWidth: 1,
          borderRadius: 6, maxBarThickness: 44, categoryPercentage: 0.72, barPercentage: 0.86 }
      ]
    },
    options: { responsive: true, animation: { duration: 600 },
      plugins: { legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' '+c.dataset.label+': '+_estMoney(c.parsed.y) } }) },
      scales: { x: _estEjeX(), y: _estEjeY(true) } }
  });

  // --- (b) doughnut: distribución de las salidas por naturaleza
  const natKeys = Object.keys(pn).filter(k=>num(pn[k])>0);
  _estChart('cieNaturalezaDough', {
    type: 'doughnut',
    data: {
      labels: natKeys.length ? natKeys.map(k=>CIE_NAT[k]||k) : ['Sin egresos'],
      datasets: [{ data: natKeys.length ? natKeys.map(k=>num(pn[k])) : [1],
        backgroundColor: natKeys.length ? natKeys.map((_,i)=>EST_COLORS[i%EST_COLORS.length]) : ['#EAE2D0'],
        borderColor: '#fff', borderWidth: 2 }]
    },
    options: { responsive: true, cutout: '58%',
      plugins: { legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c=>' '+c.label+': '+_estMoney(c.parsed)+(natKeys.length?' ('+(num(d.egresos.total_base)>0?(num(c.parsed)/num(d.egresos.total_base)*100).toFixed(1):'0.0')+'%)':'') } }) } }
  });

  // --- (c) barras horizontales: egresos por categoría (monto y %)
  const porCat = (d.egresos && d.egresos.por_categoria) || {};
  const pctCat = (d.egresos && d.egresos.porcentaje_categoria) || {};
  const cats = Object.keys(porCat).map(k=>[k, num(porCat[k])]).sort((a,b)=>b[1]-a[1]);
  const hayCat = cats.length > 0;
  _estChart('cieCategoriaBar', {
    type: 'bar',
    data: {
      labels: hayCat ? cats.map(x=>x[0]) : ['Sin datos'],
      datasets: [{ label: 'Egresos', data: hayCat ? cats.map(x=>x[1]) : [0],
        backgroundColor: hayCat ? cats.map((_,i)=>'rgba(176,140,61,'+(0.85-i*0.04)+')') : 'rgba(176,140,61,0.5)',
        borderColor: '#8A6D2F', borderWidth: 1, borderRadius: 5, maxBarThickness: 24,
        categoryPercentage: 0.75, barPercentage: 0.9 }]
    },
    options: { indexAxis: 'y', responsive: true, animation: { duration: 600 },
      plugins: { legend: { display: false },
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => {
          const pct = pctCat[c.label] != null ? num(pctCat[c.label]).toFixed(1)+'%' : '—';
          return ' '+_estMoney(c.parsed.x)+' ('+pct+')';
        } } }) },
      scales: { x: _estEjeY(false), y: _estEjeX() } }
  });

  // --- (d) línea: tendencia del flujo neto (puntos negativos en rojo)
  const netos = hayMes ? mensual.map(m=>num(m.neto)) : [0];
  _estChart('cieNetoLine', {
    type: 'line',
    data: {
      labels: hayMes ? mensual.map(m=>_estLabelMes(m.mes)) : ['Sin datos'],
      datasets: [{ label: 'Flujo neto', data: netos,
        borderColor: '#B08C3D', backgroundColor: 'rgba(176,140,61,0.15)', borderWidth: 2.5,
        fill: true, tension: 0.3, pointRadius: 4, pointHoverRadius: 6, pointStyle: 'circle',
        pointBackgroundColor: netos.map(v=>v<0?'#c0392b':'#1e7a46'),
        pointBorderColor: netos.map(v=>v<0?'#c0392b':'#1e7a46') }]
    },
    options: { responsive: true, animation: { duration: 600 },
      plugins: { legend: { display: false },
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' Flujo neto: '+_estMoney(c.parsed.y) } }) },
      scales: { x: _estEjeX(), y: { grid: { color: '#EAE2D0' }, border: { display: false },
        ticks: { callback: v => _estTick(v, true), font: { size: 11 } } } } }
  });

  // --- (e) barras horizontales: principales conceptos de gasto (top 10)
  const conceptos = ((d.egresos && d.egresos.principales_conceptos)||[]).slice(0,10);
  const hayCon = conceptos.length > 0;
  _estChart('cieConceptosBar', {
    type: 'bar',
    data: {
      labels: hayCon ? conceptos.map(c=>c.concepto) : ['Sin datos'],
      datasets: [{ label: 'Gasto', data: hayCon ? conceptos.map(c=>num(c.monto_base)) : [0],
        backgroundColor: hayCon ? conceptos.map((_,i)=>'rgba(192,57,43,'+(0.85-i*0.05)+')') : 'rgba(192,57,43,0.65)',
        borderColor: '#c0392b', borderWidth: 1, borderRadius: 5, maxBarThickness: 22,
        categoryPercentage: 0.75, barPercentage: 0.9 }]
    },
    options: { indexAxis: 'y', responsive: true, animation: { duration: 600 },
      plugins: { legend: { display: false },
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c => ' '+_estMoney(c.parsed.x) } }) },
      scales: { x: _estEjeY(false), y: _estEjeX() } }
  });

  // --- (f2) doughnut: ingresos por categoría + mini-tabla (monto y % sobre ingresos totales)
  const porCatIng = (d.ingresos && d.ingresos.por_categoria) || {};
  const catIng = Object.keys(porCatIng).map(k=>[k || 'Sin categoría', num(porCatIng[k])]).sort((a,b)=>b[1]-a[1]);
  const hayCatIng = catIng.length > 0;
  const totalIng = num(d.ingresos.total_base);
  _estChart('cieIngCatDough', {
    type: 'doughnut',
    data: {
      labels: hayCatIng ? catIng.map(x=>x[0]) : ['Sin ingresos'],
      datasets: [{ data: hayCatIng ? catIng.map(x=>x[1]) : [1],
        backgroundColor: hayCatIng ? catIng.map((_,i)=>EST_COLORS[(i+3)%EST_COLORS.length]) : ['#EAE2D0'],
        borderColor: '#fff', borderWidth: 2 }]
    },
    options: { responsive: true, cutout: '58%',
      plugins: { legend: _estLegend(),
        tooltip: Object.assign(_estTooltip(), { callbacks: { label: c=>' '+c.label+': '+_estMoney(c.parsed)+(hayCatIng&&totalIng>0?' ('+(num(c.parsed)/totalIng*100).toFixed(1)+'%)':'') } }) } }
  });
  if ($('cieIngCatTable')) $('cieIngCatTable').innerHTML = hayCatIng ? catIng.map(x=>{
    const pct = totalIng > 0 ? (x[1]/totalIng*100).toFixed(1)+'%' : '—';
    return '<tr><td>'+esc(x[0])+'</td><td style="text-align:right;">'+f(x[1])+'</td><td style="text-align:right;">'+pct+'</td></tr>';
  }).join('') : '<tr><td colspan="3" class="muted">Sin ingresos en el periodo.</td></tr>';

  // --- (f) tabla: desglose por naturaleza
  const totalEg = num(d.egresos.total_base);
  $('cieNatTable').innerHTML = natKeys.length ? natKeys.map(k=>{
    const monto = num(pn[k]);
    const pct = totalEg > 0 ? (monto/totalEg*100).toFixed(1)+'%' : '—';
    return '<tr><td>'+esc(CIE_NAT[k]||k)+'</td><td>'+(num(nPn[k]))+'</td>' +
      '<td style="text-align:right;">'+f(monto)+'</td><td style="text-align:right;">'+pct+'</td></tr>';
  }).join('') : '<tr><td colspan="4" class="muted">Sin egresos en el periodo.</td></tr>';

  // --- (g) pendientes de clasificar (solo si hay movimientos)
  const pc = d.pendientes_clasificar || { total_base: 0, movimientos: 0 };
  const boxP = $('ciePendBox');
  if (num(pc.movimientos) > 0) {
    boxP.style.display = 'block';
    $('ciePendTotal').textContent = f(pc.total_base);
    const det = (pc.detalle && pc.detalle.length ? pc.detalle :
      ((d.egresos.detalle)||[]).filter(x=>x.naturaleza==='por_clasificar')).slice(0, 20);
    $('ciePendTable').innerHTML = det.length ? det.map(x=>
      '<tr><td class="gold">'+esc(x.gasto_folio||x.folio||'—')+'</td><td>'+esc(x.fecha||'—')+'</td>' +
      '<td>'+esc(x.categoria||'—')+'</td><td>'+esc(x.descripcion||'—')+'</td>' +
      '<td style="text-align:right;">'+f(x.monto_base)+'</td></tr>').join('')
      : '<tr><td colspan="5" class="muted">'+num(pc.movimientos)+' movimiento(s) sin detalle disponible.</td></tr>';
  } else {
    boxP.style.display = 'none';
  }

  // --- nota del reporte + aviso de filtrado (totales generales vs filtrados)
  var fil = d.egresos && d.egresos.filtrado;
  var avisoFiltro = '';
  if (fil && fil.activo) {
    var descF = [];
    if (fil.naturaleza) descF.push('naturaleza=' + (CIE_NAT[fil.naturaleza] || fil.naturaleza));
    if (fil.categoria) descF.push('categoría=' + fil.categoria);
    avisoFiltro = '⚠ Detalle filtrado (' + descF.join(' · ') + '): ' + num(fil.movimientos) +
      ' egreso(s) por ' + f(fil.total_base) + '. Los indicadores, gráficas y la variación neta ' +
      'muestran el TOTAL GENERAL del periodo. — ';
  }
  $('cieNota').textContent = avisoFiltro + (d.nota || '');
}
