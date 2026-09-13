/* ----- gastos ----- */
function addExpense(){
  const cat=$('gCategoria').value.trim(), monto=parseFloat($('gMonto').value)||0;
  if (!cat || !monto) { notice('Falta la categoría o el monto.', false); return; }
  apiPost({tipo:'gasto', fecha:$('gFecha').value, categoria:cat, descripcion:$('gDesc').value.trim(),
    monto, moneda:$('gMoneda').value}).then(d=>{
    notice(d&&d.ok?('Gasto '+(d.folio||'')+' guardado.'):errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
    if(d&&d.ok){ $('gMonto').value=''; $('gDesc').value=''; loadBiz(); }
  });
}
// FASE 5: gasto != pago. Cada gasto lleva folio GAS-, estado (ACTIVA/CANCELADA) y pagos parciales.
function renderExpenses(list){
  if (!list.length) { $('expTable').innerHTML='<tr><td colspan="9" class="muted">Sin gastos registrados.</td></tr>'; return; }
  $('expTable').innerHTML = list.slice().reverse().map(g=>{
    const est = g.estado || 'ACTIVA';
    const cancelada = est==='CANCELADA';
    const pagado = Number(g.pagado)||0;
    const saldo = Math.max(0, (Number(g.monto)||0) - pagado);
    const colE = cancelada ? '#9a9a9a' : '#e8b96a';
    const acciones = g.id && !cancelada
      ? (saldo>0.001 ? '<button class="btn btn-sm" onclick="showPagoForm(\''+g.id+'\')">Pagar</button> ' : '') +
        '<button class="btn btn-danger btn-sm" onclick="cancelarGasto(\''+g.id+'\', this)">Cancelar</button>'
      : (cancelada ? '<span class="muted">cancelado</span>' : '');
    return '<tr><td class="gold">'+esc(g.folio||'—')+'</td><td>'+esc(g.fecha)+'</td><td>'+esc(g.categoria)+'</td><td>'+esc(g.descripcion)+'</td>' +
      '<td class="gold">'+fmtMoney(g.monto)+' '+esc(g.moneda)+'</td>' +
      '<td style="color:#7ce3a1;">'+fmtMoney(pagado)+'</td>' +
      '<td>'+(saldo>0.001&&!cancelada?'<span class="gold">'+fmtMoney(saldo)+'</span>':'—')+'</td>' +
      '<td><span style="color:'+colE+';font-weight:600;font-size:0.72rem;">'+esc(est)+'</span></td>' +
      '<td style="white-space:nowrap;">'+acciones+'</td></tr>';}).join('');
}
function renderCXP(d){
  const porPagar = Number(d && d.por_pagar_base)||0;
  const conSaldo = cxpCache.filter(x=>x.saldo_base>0.001).length;
  const pagadas = cxpCache.filter(x=>x.estado_pago==='PAGADA').length;
  if ($('cxpDash')) $('cxpDash').innerHTML =
    '<div class="pnl-card '+(porPagar?'bad':'good')+'"><div class="k">Por pagar ('+esc((d&&d.moneda_base)||'MXN')+')</div><div class="v">'+fmtMoney(porPagar)+'</div></div>' +
    '<div class="pnl-card"><div class="k">Gastos con saldo</div><div class="v">'+conSaldo+'</div></div>' +
    '<div class="pnl-card good"><div class="k">Gastos pagados</div><div class="v">'+pagadas+'</div></div>';
  if (!$('cxpTable')) return;
  const orden = cxpCache.slice().sort((a,b)=>(Number(b.saldo_base>0.001))-(Number(a.saldo_base>0.001)));
  $('cxpTable').innerHTML = orden.length ? orden.map(x=>{
    const col = x.estado_pago==='PAGADA'?'#7ce3a1':(x.estado_pago==='PARCIAL'?'#e8b96a':'#e37c7c');
    return '<tr><td class="gold">'+esc(x.folio||'—')+'</td><td>'+esc(x.fecha)+'</td><td>'+esc(x.categoria)+'</td>' +
      '<td>'+fmtMoney(x.total)+' '+esc(x.moneda)+'</td><td style="color:#7ce3a1;">'+fmtMoney(x.pagado)+'</td>' +
      '<td class="gold">'+fmtMoney(x.saldo)+'</td>' +
      '<td><span style="color:'+col+';font-weight:600;font-size:0.72rem;">'+esc(x.estado_pago)+'</span></td>' +
      '<td style="white-space:nowrap;">'+(x.saldo>0.001?'<button class="btn btn-sm" onclick="showPagoForm(\''+x.gasto_id+'\')">Pagar</button>':'')+'</td></tr>';
  }).join('') : '<tr><td colspan="8" class="muted">Sin gastos pendientes de pago.</td></tr>';
  $('pagosTable').innerHTML = pagosCache.length ? pagosCache.map(p=>
    '<tr><td class="gold">'+esc(p.folio||'—')+'</td><td>'+esc(p.fecha)+'</td><td>'+esc(p.gasto_folio||'—')+'</td>' +
    '<td>'+esc(p.categoria||'—')+'</td><td class="gold">'+fmtMoney(p.monto)+' '+esc(p.moneda)+'</td><td>'+esc(p.metodo||'—')+'</td></tr>').join('')
    : '<tr><td colspan="6" class="muted">Sin pagos registrados.</td></tr>';
}
function showPagoForm(gastoId){
  const x = cxpCache.filter(g=>String(g.gasto_id)===String(gastoId))[0];
  if (!x) { notice('Recarga la pestaña para ver el saldo actualizado.', false); return; }
  $('pagoForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>Registrar pago — '+esc(x.folio)+'</strong> <span class="muted">'+esc(x.categoria)+' · saldo '+fmtMoney(x.saldo)+' '+esc(x.moneda)+'</span></p><div class="row">' +
    '<div><label>Fecha</label><input type="date" id="pgFecha" value="'+fLocal()+'"></div>' +
    '<div><label>Monto *</label><input type="number" id="pgMonto" min="0" step="0.01" value="'+x.saldo+'"></div>' +
    '<div><label>Moneda</label><select id="pgMoneda"><option value="'+esc(x.moneda)+'">'+esc(x.moneda)+'</option><option value="MXN">MXN</option><option value="USD">USD</option></select></div>' +
    '<div><label>Método</label><select id="pgMetodo"><option>Efectivo</option><option>Transferencia</option><option>Tarjeta</option><option>Depósito</option><option>Otro</option></select></div>' +
    '</div><label>Notas</label><input id="pgNotas">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="savePago(\''+x.gasto_id+'\')">Guardar pago</button> ' +
    '<button class="btn btn-sm" onclick="$(\'pagoForms\').innerHTML=\'\'">Cerrar</button></div></div>';
  $('pagoForms').scrollIntoView({behavior:'smooth', block:'nearest'});
}
function savePago(gastoId){
  const monto = parseFloat($('pgMonto').value)||0;
  if (monto <= 0) { notice('El monto debe ser mayor que cero.', false); return; }
  apiPost({tipo:'gasto_pago', gasto_id:gastoId, fecha:$('pgFecha').value, monto,
    moneda:$('pgMoneda').value, metodo:$('pgMetodo').value, notas:$('pgNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?('Pago '+(d.folio||'')+' registrado. Gasto ahora: '+d.estado_pago+'.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ $('pagoForms').innerHTML=''; loadBiz(); }
  }).catch(()=>notice('Error de conexión.', false));
}
// doble paso sin confirm(): el boton pide confirmacion a si mismo
function cancelarGasto(id, btn){
  if (btn.dataset.confirm !== '1') {
    btn.dataset.confirm = '1'; btn.textContent = '¿Seguro?';
    setTimeout(()=>{ if (btn.isConnected){ btn.dataset.confirm=''; btn.textContent='Cancelar'; } }, 3000);
    return;
  }
  apiPost({tipo:'gasto_cancelar', id}).then(d=>{
    notice(d&&d.ok?'Gasto cancelado (baja lógica; queda en el historial).':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadBiz();
  });
}

