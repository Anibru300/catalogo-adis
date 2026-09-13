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
    $('flujoKpis').innerHTML =
      '<div class="pnl-card good"><div class="k">Entradas ('+d.num_cobros+' cobro(s))</div><div class="v">'+f(d.entradas)+'</div></div>' +
      '<div class="pnl-card bad"><div class="k">Salidas ('+d.num_pagos+' pago(s))</div><div class="v">'+f(d.salidas)+'</div></div>' +
      '<div class="pnl-card '+clsN+'"><div class="k">Flujo neto</div><div class="v">'+f(d.neto)+'</div></div>';
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
      const clsBruta = d.utilidad_bruta>=0?'good':'bad', clsNeta = d.utilidad_neta>=0?'good':'bad';
      const tituloProy = d.proyecto_id ? ' <span class="muted" style="font-size:0.75rem;">(proyecto)</span>' : '';
      $('pnlCards').innerHTML = '<div class="pnl-cards">' +
        '<div class="pnl-card"><div class="k">Ventas ('+d.num_ventas+')'+tituloProy+'</div><div class="v">'+f(d.ingresos)+'</div></div>' +
        '<div class="pnl-card"><div class="k">Costo mercancía</div><div class="v">'+f(d.costos)+'</div></div>' +
        '<div class="pnl-card '+clsBruta+'"><div class="k">Utilidad bruta</div><div class="v">'+f(d.utilidad_bruta)+' <small style="font-size:0.7rem;">'+d.margen_bruto.toFixed(1)+'%</small></div></div>' +
        '<div class="pnl-card"><div class="k">Gastos operativos</div><div class="v">'+f(d.total_gastos)+'</div></div>' +
        '<div class="pnl-card '+clsNeta+'"><div class="k">Utilidad operativa</div><div class="v">'+f(d.utilidad_operativa!=null?d.utilidad_operativa:d.utilidad_neta)+' <small style="font-size:0.7rem;">'+(d.margen_operativo!=null?d.margen_operativo:d.margen_neto).toFixed(1)+'%</small></div></div>' +
        '</div>';
      const cats = Object.keys(d.gastos).sort();
      $('pnlBox').style.display='block';
      $('pnlTable').innerHTML =
        '<tr><td>Ventas</td><td style="text-align:right;">'+f(d.ingresos)+'</td></tr>' +
        '<tr><td>(−) Costo de la mercancía vendida</td><td style="text-align:right;">'+f(d.costos)+'</td></tr>' +
        '<tr><td><strong>= Utilidad bruta</strong></td><td style="text-align:right;"><strong>'+f(d.utilidad_bruta)+'</strong></td></tr>' +
        '<tr><td colspan="2" style="color:var(--gold);">Gastos por categoría</td></tr>' +
        (cats.length ? cats.map(c=>'<tr><td>&nbsp;&nbsp;'+esc(c)+'</td><td style="text-align:right;">'+f(d.gastos[c])+'</td></tr>').join('') : '<tr><td colspan="2" class="muted">Sin gastos este mes.</td></tr>') +
        '<tr><td>(−) Total gastos</td><td style="text-align:right;">'+f(d.total_gastos)+'</td></tr>' +
        '<tr><td><strong>= Utilidad operativa del mes</strong></td><td style="text-align:right;"><strong>'+f(d.utilidad_neta)+'</strong></td></tr>';
    }).catch(()=>{ $('pnlCards').innerHTML='<p class="muted">Error de conexion.</p>'; });
}
function printPNL(){
  if (!pnlData) { notice('Primero genera el resultado.', false); return; }
  const d = pnlData, f = n => fmtMoney(n)+' '+d.moneda_base;
  const mesTxt = $('pnlMes').value;
  $('printArea').innerHTML =
    '<h1>ADIS Diseño & Remodelación</h1><div class="pq-meta">Estado de resultados · ' + mesTxt + ' · Moneda: ' + d.moneda_base + '</div>' +
    '<table><tbody>' + $('pnlTable').innerHTML + '</tbody></table>' +
    '<p style="margin-top:1rem;font-size:0.85rem;">Ventas: '+d.num_ventas+' · Margen bruto: '+d.margen_bruto.toFixed(1)+'% · Margen neto: '+d.margen_neto.toFixed(1)+'%</p>' +
    '<div class="pq-foot">Generado desde el panel administrativo ADIS</div>';
  window.print();
}

