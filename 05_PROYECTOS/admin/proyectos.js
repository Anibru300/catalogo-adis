/* =====================================================================
   FASE 4 — PROYECTOS + COBROS (cuentas por cobrar)
   ===================================================================== */
let proyCache = [], cxcCache = [], cobrosCache = [], cxpCache = [], pagosCache = [];

function loadProyectos(){
  apiGet('proyectos').then(d=>{
    if (!d || !d.ok) { $('proyTable').innerHTML='<tr><td colspan="7" class="muted">Sin acceso.</td></tr>'; return; }
    proyCache = d.proyectos || [];
    renderProyectos();
    fillSaleLinks();
    fillPnlProyectos();
  }).catch(()=>{});
}
function renderProyectos(){
  const activos = proyCache.filter(p=>p.estado==='ACTIVO').length;
  const presup = proyCache.filter(p=>p.estado==='ACTIVO').reduce((s,p)=>s+(Number(p.presupuesto)||0),0);
  const cobr = proyCache.reduce((s,p)=>s+(Number(p.cobrado)||0),0);
  $('proyDash').innerHTML =
    '<div class="pnl-card"><div class="k">Proyectos activos</div><div class="v">'+activos+'</div></div>' +
    '<div class="pnl-card"><div class="k">Total proyectos</div><div class="v">'+proyCache.length+'</div></div>' +
    '<div class="pnl-card"><div class="k">Presupuesto activo</div><div class="v" style="font-size:0.95rem;">'+fmtMoney(presup)+'</div></div>' +
    '<div class="pnl-card good"><div class="k">Cobrado (proyectos)</div><div class="v" style="font-size:0.95rem;">'+fmtMoney(cobr)+'</div></div>';
  if (!proyCache.length) { $('proyTable').innerHTML='<tr><td colspan="7" class="muted">Sin proyectos. Crea uno desde una cotización aprobada.</td></tr>'; }
  else $('proyTable').innerHTML = proyCache.slice().reverse().map(p=>
    '<tr><td class="gold" style="white-space:nowrap;">'+esc(p.folio||'—')+'</td><td>'+esc(p.nombre)+(p.cotizacion_folio?' <span class="muted">('+esc(p.cotizacion_folio)+')</span>':'')+'</td>' +
    '<td>'+esc(p.cliente||'—')+'</td><td>'+fmtMoney(p.presupuesto)+' '+esc(p.moneda||'')+'</td>' +
    '<td style="color:#7ce3a1;">'+fmtMoney(p.cobrado)+'</td><td>'+ocEstadoBadge(p.estado)+'</td>' +
    '<td style="white-space:nowrap;">'+(p.estado==='ACTIVO'
      ? '<button class="btn btn-sm" onclick="fichaProyecto(\''+p.id+'\')">Ficha</button> ' +
        '<button class="btn btn-sm" onclick="cambiarEstadoProyecto(\''+p.id+'\',\'TERMINADO\')">✔ Terminar</button> ' +
        '<button class="btn btn-danger btn-sm" onclick="cambiarEstadoProyecto(\''+p.id+'\',\'CANCELADO\')">✕</button>'
      : '<button class="btn btn-sm" onclick="fichaProyecto(\''+p.id+'\')">Ficha</button>')+'</td></tr>').join('');
  // selector "desde cotización" se llena desde quotesCache (cotizaciones aprobadas sin proyecto)
  const usadas = proyCache.map(p=>String(p.cotizacion_id));
  const aptas = quotesCache.filter(q=>q.estado==='Aprobada' && q.id && usadas.indexOf(String(q.id))<0);
  $('proyDesdeCot').innerHTML = '<option value="">— Cotización aprobada —</option>' +
    aptas.map(q=>'<option value="'+esc(q.id)+'">'+esc(q.folio||'')+' · '+esc(q.cliente||'')+'</option>').join('');
}
function crearProyectoDesdeSelect(){
  const qid = $('proyDesdeCot').value;
  if (!qid) { notice('Selecciona una cotización aprobada.', false); return; }
  crearProyectoDesdeQuote(qid);
}
function crearProyectoDesdeQuote(qid){
  if (!confirma('proycot-'+qid, 'Crear el proyecto desde esta cotización (se vinculan cliente, folio y presupuesto).')) return;
  apiPost({tipo:'crear_proyecto_desde_cotizacion', quote_id:qid}).then(d=>{
    notice(d&&d.ok?('Proyecto '+(d.folio||'')+(d.ya_existia?' (ya existía)':'')+' creado.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ loadProyectos(); loadQuotes(); }
  });
}
function showProyectoForm(){
  const cliOpts = '<option value="">— Sin cliente —</option>' + clientesCache.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.nombre)+'</option>').join('');
  $('proyForms').innerHTML = '<div class="card-box"><div class="row">' +
    '<div><label>Nombre del proyecto *</label><input id="prNombre" placeholder="Remodelación cocina Pérez"></div>' +
    '<div><label>Cliente</label><select id="prCliente">'+cliOpts+'</select></div>' +
    '<div><label>Ubicación</label><input id="prUbi"></div>' +
    '<div><label>Presupuesto</label><input type="number" id="prPresupuesto" min="0" step="0.01" value="0"></div>' +
    '<div><label>Moneda</label><select id="prMoneda"><option value="MXN">MXN</option><option value="USD">USD</option></select></div>' +
    '<div><label>Fecha inicio</label><input type="date" id="prInicio" value="'+fLocal()+'"></div>' +
    '</div><label>Notas</label><input id="prNotas">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="saveProyecto()">💾 Guardar proyecto</button> ' +
    '<button class="btn btn-sm" onclick="$(\'proyForms\').innerHTML=\'\'">Cancelar</button></div></div>';
}
function saveProyecto(){
  const nombre = $('prNombre').value.trim();
  if (!nombre) { notice('El proyecto necesita nombre.', false); return; }
  const cid = $('prCliente').value;
  const cliente = cid ? clientesCache.filter(c=>String(c.id)===String(cid))[0] : null;
  apiPost({tipo:'save_proyecto', nombre, cliente_id:cid, cliente:cliente?cliente.nombre:'',
    ubicacion:$('prUbi').value.trim(), presupuesto:parseFloat($('prPresupuesto').value)||0,
    moneda:$('prMoneda').value, fecha_inicio:$('prInicio').value, notas:$('prNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?('Proyecto '+(d.folio||'')+' creado.'):errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
    if(d&&d.ok){ $('proyForms').innerHTML=''; loadProyectos(); }
  }).catch(()=>notice('Error de conexión.', false));
}
function cambiarEstadoProyecto(id, estado){
  if (!confirma('proy-'+id+'-'+estado, estado==='TERMINADO'?'Marcar proyecto como TERMINADO.':'CANCELAR este proyecto.')) return;
  apiPost({tipo:'cambiar_estado_proyecto', id, estado}).then(d=>{
    notice(d&&d.ok?('Proyecto ahora está '+estado+'.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadProyectos();
  });
}

function loadCXC(){
  apiGet('cxc').then(d=>{
    if (!d || !d.ok) { $('cxcTable').innerHTML='<tr><td colspan="8" class="muted">Sin acceso.</td></tr>'; return; }
    cxcCache = d.cxc || [];
    cobrosCache = d.cobros || [];
    const porCobrar = Number(d.por_cobrar_base)||0;
    const pendientes = cxcCache.filter(x=>x.saldo_base>0.001).length;
    const pagadas = cxcCache.filter(x=>x.estado_pago==='PAGADA').length;
    $('cxcDash').innerHTML =
      '<div class="pnl-card '+(porCobrar?'bad':'good')+'"><div class="k">Por cobrar ('+esc(d.moneda_base||'MXN')+')</div><div class="v">'+fmtMoney(porCobrar)+'</div></div>' +
      '<div class="pnl-card"><div class="k">Ventas con saldo</div><div class="v">'+pendientes+'</div></div>' +
      '<div class="pnl-card good"><div class="k">Ventas pagadas</div><div class="v">'+pagadas+'</div></div>';
    if (!cxcCache.length) { $('cxcTable').innerHTML='<tr><td colspan="8" class="muted">Sin ventas con ID (las ventas nuevas aparecen aquí).</td></tr>'; }
    else $('cxcTable').innerHTML = cxcCache.slice().reverse().map(x=>{
      const col = x.estado_pago==='PAGADA'?'#7ce3a1':(x.estado_pago==='PARCIAL'?'#e8b96a':'#e37c7c');
      return '<tr><td class="gold">'+esc(x.folio||'—')+'</td><td>'+esc(x.fecha)+'</td><td>'+esc(x.cliente||'—')+'</td>' +
        '<td>'+fmtMoney(x.total)+' '+esc(x.moneda)+'</td><td style="color:#7ce3a1;">'+fmtMoney(x.cobrado)+'</td>' +
        '<td class="gold">'+fmtMoney(x.saldo)+'</td>' +
        '<td><span style="color:'+col+';font-weight:600;font-size:0.75rem;">'+esc(x.estado_pago)+'</span></td>' +
        '<td style="white-space:nowrap;">'+(x.saldo>0.001?'<button class="btn btn-sm" onclick="showCobroForm(\''+x.venta_id+'\')">💰 Cobrar</button> ':'')+'</td></tr>';
    }).join('');
    $('cobrosTable').innerHTML = cobrosCache.length ? cobrosCache.map(c=>
      '<tr><td class="gold">'+esc(c.folio||'—')+'</td><td>'+esc(c.fecha)+'</td><td>'+esc(c.venta_folio||'—')+'</td>' +
      '<td>'+esc(c.cliente||'—')+'</td><td class="gold">'+fmtMoney(c.monto)+' '+esc(c.moneda)+'</td><td>'+esc(c.metodo||'—')+'</td></tr>').join('')
      : '<tr><td colspan="6" class="muted">Sin cobros registrados.</td></tr>';
  }).catch(()=>{});
}
function showCobroForm(ventaId){
  const x = cxcCache.filter(v=>String(v.venta_id)===String(ventaId))[0];
  if (!x) return;
  $('cobForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>Registrar cobro — '+esc(x.folio)+'</strong> <span class="muted">'+esc(x.cliente||'')+' · saldo '+fmtMoney(x.saldo)+' '+esc(x.moneda)+'</span></p><div class="row">' +
    '<div><label>Fecha</label><input type="date" id="cbFecha" value="'+fLocal()+'"></div>' +
    '<div><label>Monto *</label><input type="number" id="cbMonto" min="0" step="0.01" value="'+x.saldo+'"></div>' +
    '<div><label>Moneda</label><select id="cbMoneda"><option value="'+esc(x.moneda)+'">'+esc(x.moneda)+'</option><option value="MXN">MXN</option><option value="USD">USD</option></select></div>' +
    '<div><label>Método</label><select id="cbMetodo"><option>Efectivo</option><option>Transferencia</option><option>Tarjeta</option><option>Depósito</option><option>Otro</option></select></div>' +
    '</div><label>Notas</label><input id="cbNotas">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="saveCobro(\''+x.venta_id+'\')">💾 Guardar cobro</button> ' +
    '<button class="btn btn-sm" onclick="$(\'cobForms\').innerHTML=\'\'">Cancelar</button></div></div>';
}
function saveCobro(ventaId){
  const monto = parseFloat($('cbMonto').value)||0;
  if (monto <= 0) { notice('El monto debe ser mayor que cero.', false); return; }
  apiPost({tipo:'registrar_cobro', venta_id:ventaId, fecha:$('cbFecha').value, monto,
    moneda:$('cbMoneda').value, metodo:$('cbMetodo').value, notas:$('cbNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?('Cobro '+(d.folio||'')+' registrado. Venta ahora: '+d.estado_pago+'.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ $('cobForms').innerHTML=''; loadCXC(); loadBiz(); }
  }).catch(()=>notice('Error de conexión.', false));
}

// Rellena los selects de cliente/proyecto del formulario de venta
function fillSaleLinks(){
  if ($('sClienteSel')) $('sClienteSel').innerHTML = '<option value="">— Mostrador —</option>' +
    clientesCache.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.nombre)+'</option>').join('');
  if ($('sProyectoSel')) $('sProyectoSel').innerHTML = '<option value="">— Ninguno —</option>' +
    proyCache.filter(p=>p.estado==='ACTIVO').map(p=>'<option value="'+esc(p.id)+'">'+esc(p.folio)+' · '+esc(p.nombre)+'</option>').join('');
}
function anularVenta(id){
  if (!confirma('anula-'+id, 'ANULAR esta venta: la mercancía REGRESA al almacén con movimiento trazable y la venta queda CANCELADA.')) return;
  apiPost({tipo:'anular_venta', id}).then(d=>{
    notice(d&&d.ok?'Venta anulada y stock repuesto.':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ loadBiz(); loadCXC(); }
  });
}

